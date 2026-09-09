import os
import json
import struct
import tarfile
import zlib
from pathlib import Path
from unittest.mock import patch

import pytest

from tools import diagnose_ios as diagnostic


def _png() -> bytes:
    def chunk(kind: bytes, content: bytes) -> bytes:
        return struct.pack(">I", len(content)) + kind + content + struct.pack(">I", zlib.crc32(kind + content) & 0xFFFFFFFF)

    return (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", struct.pack(">IIBBBBB", 1, 1, 8, 2, 0, 0, 0))
        + chunk(b"IDAT", zlib.compress(b"\0\0\0\0"))
        + chunk(b"IEND", b"")
    )


def test_redaction_keeps_error_but_removes_private_values(monkeypatch):
    root = type("Root", (), {"resolve": lambda self: "/Users/builder/project"})()
    monkeypatch.setattr(diagnostic.rt, "ROOT", root)
    with patch.dict(os.environ, {"PRIVATE_TEST_VALUE": "hidden-token-123"}):
        text = diagnostic.redact("error: hidden-token-123 /Users/builder/project/ios/ACEClientApp/ACEClientAppUITests.swift:92 /Users/person/private/src/customer.swift user@host.invalid https://private.invalid token=secret")
    assert "error:" in text
    assert "ios/ACEClientApp/ACEClientAppUITests.swift:92" in text
    assert "hidden-token-123" not in text
    assert "/Users/" not in text
    assert "customer.swift" not in text
    assert "user@" not in text
    assert "https://" not in text
    assert "token=secret" not in text


def test_error_selection_retains_actual_failure(tmp_path):
    log = tmp_path / "ui.log"
    log.write_text('normal build output\nerror: XCTAssertEqual failed: light expected\n', encoding="utf-8")
    assert diagnostic.errors(log) == ["error: XCTAssertEqual failed: light expected"]


def test_missing_log_is_unknown(tmp_path):
    assert diagnostic.errors(tmp_path / "absent") == ["error log unavailable"]


def test_error_limit(tmp_path):
    log = tmp_path / "negative.log"
    log.write_text("\n".join(f"error: failure {n}" for n in range(100)), encoding="utf-8")
    assert len(diagnostic.errors(log)) == 30


def test_accessibility_issue_retention_is_bounded_redacted_and_separate_from_errors(tmp_path):
    log = tmp_path / "ui.log"
    issue = {
        "scenario": "signIn",
        "auditType": "contrast",
        "compactDescription": "Contrast failed",
        "detailedDescription": "secret=hidden-token-123 " + "x" * 400,
        "element": {
            "identifier": "Password",
            "label": "Password",
            "type": "SecureTextField",
            "frame": {"x": 1, "y": 2, "width": 3, "height": 4},
            "value": "must-not-retain",
        },
    }
    lines = [f"error: unrelated {index}" for index in range(35)]
    lines += ["ACE_A11Y_ISSUE " + json.dumps(issue) for _ in range(31)]
    log.write_text("\n".join(lines), encoding="utf-8")

    assert len(diagnostic.errors(log)) == 30
    retained, status = diagnostic.accessibility_issues(log)
    assert status == "truncated"
    assert len(retained) == diagnostic.A11Y_ISSUE_LIMIT
    assert retained[0]["scenario"] == "signIn"
    assert retained[0]["element"] == {
        "identifier": "Password", "label": "Password", "type": "SecureTextField",
        "frame": {"x": 1, "y": 2, "width": 3, "height": 4},
    }
    assert "hidden-token-123" not in retained[0]["detailedDescription"]
    assert len(retained[0]["detailedDescription"]) <= diagnostic.A11Y_ISSUE_TEXT_LIMIT
    assert "must-not-retain" not in json.dumps(retained)


def test_accessibility_issue_rejects_invalid_or_oversized_records(tmp_path):
    log = tmp_path / "ui.log"
    log.write_text(
        "ACE_A11Y_ISSUE not-json\n"
        "ACE_A11Y_ISSUE {\"scenario\": \"missing fields\"}\n"
        + "ACE_A11Y_ISSUE " + "x" * (diagnostic.A11Y_ISSUE_LINE_LIMIT + 1),
        encoding="utf-8",
    )
    assert diagnostic.accessibility_issues(log) == ([], "truncated")


def test_accessibility_issue_retains_maximum_escaped_producer_record(tmp_path):
    log = tmp_path / "ui.log"
    escaped = ('"\\' * 128)
    issue = {
        "scenario": escaped,
        "auditType": escaped,
        "compactDescription": escaped,
        "detailedDescription": escaped,
        "element": {"identifier": escaped, "label": escaped, "type": escaped},
    }
    line = "ACE_A11Y_ISSUE " + json.dumps(issue)
    assert len(line) > 2 * 1024
    assert len(line) <= diagnostic.A11Y_ISSUE_LINE_LIMIT
    log.write_text(line, encoding="utf-8")

    retained, status = diagnostic.accessibility_issues(log)
    assert status is None
    assert retained[0]["scenario"] == escaped


def test_accessibility_issue_reports_truncation_and_unavailable_input(tmp_path):
    oversized = tmp_path / "oversized.log"
    oversized.write_text("ACE_A11Y_ISSUE " + "x" * (diagnostic.A11Y_ISSUE_LINE_LIMIT + 1), encoding="utf-8")
    assert diagnostic.accessibility_issues(oversized) == ([], "truncated")
    assert diagnostic.accessibility_issues(tmp_path / "missing.log") == ([], "unavailable")


def test_accessibility_issue_rejects_deep_or_nonfinite_or_boolean_frames(tmp_path):
    log = tmp_path / "ui.log"
    valid = {
        "scenario": "signIn", "auditType": "contrast", "compactDescription": "Contrast failed",
        "detailedDescription": "Text contrast failed", "element": {
            "identifier": "Password", "label": "Password", "type": "SecureTextField",
        },
    }
    boolean_frame = valid | {"element": valid["element"] | {"frame": {"x": True, "y": 2, "width": 3, "height": 4}}}
    nonfinite_frame = valid | {"element": valid["element"] | {"frame": {"x": float("nan"), "y": 2, "width": 3, "height": 4}}}
    deep_json = "[" * 1500 + "]" * 1500
    log.write_text(
        "\n".join((
            "ACE_A11Y_ISSUE " + json.dumps(boolean_frame),
            "ACE_A11Y_ISSUE " + json.dumps(nonfinite_frame),
            "ACE_A11Y_ISSUE " + deep_json,
        )),
        encoding="utf-8",
    )
    assert diagnostic.accessibility_issues(log) == ([], None)


def test_context_rejects_local_execution():
    with patch.dict(os.environ, {}, clear=True):
        with pytest.raises(ValueError):
            diagnostic.context()


def test_diagnostic_environment_transports_only_approved_screenshot_flag(tmp_path, monkeypatch):
    captured = []

    class Process:
        pid = 1

        def wait(self, timeout):
            return 0

    def popen(command, cwd, env, stdout, stderr, start_new_session):
        captured.append(env)
        return Process()

    monkeypatch.setattr(diagnostic.subprocess, "Popen", popen)
    monkeypatch.setattr(diagnostic.rt, "ROOT", tmp_path)

    assert diagnostic.run(["xcodebuild"], diagnostic.DIAGNOSTIC_TEST_ENVIRONMENT, tmp_path / "ui.log", 1) == {"processExit": 0}
    assert captured[0][diagnostic.INITIAL_AUDIT_SCREENSHOT_ENVIRONMENT_KEY] == "1"

    assert diagnostic.run(["xcrun"], {}, tmp_path / "probe.log", 1) == {"processExit": 0}
    assert diagnostic.INITIAL_AUDIT_SCREENSHOT_ENVIRONMENT_KEY not in captured[1]


def test_diagnostic_environment_rejects_unapproved_flag_values_and_keys(tmp_path):
    with pytest.raises(ValueError):
        diagnostic.run(
            ["xcodebuild"],
            {**diagnostic.DIAGNOSTIC_TEST_ENVIRONMENT, diagnostic.INITIAL_AUDIT_SCREENSHOT_ENVIRONMENT_KEY: "0"},
            tmp_path / "invalid-flag.log",
            1,
        )
    with pytest.raises(ValueError):
        diagnostic.run(
            ["xcodebuild"],
            {diagnostic.INITIAL_AUDIT_SCREENSHOT_ENVIRONMENT_KEY: None},
            tmp_path / "missing-flag-value.log",
            1,
        )
    with pytest.raises(ValueError):
        diagnostic.run(["xcodebuild"], {"UNRELATED_ENVIRONMENT_KEY": "1"}, tmp_path / "unknown-key.log", 1)


def test_exact_scope_and_retention_contract():
    source = Path(diagnostic.__file__).read_text(encoding="utf-8")
    yaml = (diagnostic.rt.ROOT / "codemagic.yaml").read_text(encoding="utf-8")
    section = yaml.split("  ace-ios-diagnostic-manual:", 1)[1].split("  ace-ios-core:", 1)[0]
    assert "max_build_duration: 5" in section
    assert "ACE_IOS_DIAGNOSTIC_MODE: unit-settings" in section
    assert "triggering:" not in section
    assert "- mcx19_diagnostic" in section
    assert "mcx19_live_evidence" not in section
    assert "/private/tmp/mcx-19-diagnostic-safe/diagnostic.json" in section
    assert "/private/tmp/mcx-19-diagnostic-safe/screenshots/**/*.png" in section
    assert "live-evidence --" not in section
    assert "ios_release_ui_matrix" not in source
    assert diagnostic.METHOD == "testFictionalReleaseHasApprovedCopyControls"
    expected_runner_names = diagnostic.rt._expected_logical_screenshot_names(
        f"ios-release-{diagnostic.rt.IOS_CORE_DEVICE}-light-{diagnostic.METHOD}"
    )
    assert len(expected_runner_names) == 13
    assert diagnostic.SCREENSHOT_NAMES == (*expected_runner_names, diagnostic.INITIAL_AUDIT_SCREENSHOT_NAME)
    assert diagnostic.DIAGNOSTIC_TEST_ENVIRONMENT == {
        **diagnostic.rt.ios_test_environment("light"),
        diagnostic.INITIAL_AUDIT_SCREENSHOT_ENVIRONMENT_KEY: "1",
    }
    assert "DIAGNOSTIC_TEST_ENVIRONMENT, ui_log, 420" in source
    assert diagnostic.rt.SIMULATOR_VERIFICATION_SECONDS == 180
    native = yaml.split("  ace-ios-native-cycle-manual:", 1)[1].split("  ace-ios-core:", 1)[0]
    assert "max_build_duration: 8" in native
    assert "instance_type: mac_mini_m4" in native
    assert "xcode: 26.4.1" in native
    assert "ACE_LIVE_EVIDENCE_WORKFLOW: ace-ios-native-cycle-manual" in native
    assert "ACE_IOS_DIAGNOSTIC_MODE: native-cycle" in native
    assert "triggering:" not in native
    assert diagnostic.PRIVATE_ARCHIVE_NAME in native
    assert "**" not in native


def test_diagnostic_runs_one_functional_method_and_retains_failure(tmp_path, monkeypatch):
    """Catch an extra build, wrong selector or appearance, and lost failure data."""
    root = tmp_path / "raw"
    safe = tmp_path / "safe"
    root.mkdir()
    safe.mkdir()
    root_marker = type("Root", (), {"resolve": lambda self: "/Users/builder/project"})()
    monkeypatch.setattr(diagnostic, "ROOT", root)
    monkeypatch.setattr(diagnostic, "SAFE_ROOT", safe)
    monkeypatch.setattr(diagnostic.rt, "ROOT", root_marker)
    monkeypatch.setattr(diagnostic, "context", lambda: "a" * 40)
    monkeypatch.setattr(diagnostic.rt, "_live_artifact_root", lambda path: path)
    monkeypatch.setattr(diagnostic.rt, "resolve_ios_destinations", lambda devices: {devices[0]: "platform=iOS Simulator,id=fixture"})
    commands = []

    def run(command, environment, log, timeout):
        commands.append(command)
        if command[:3] == ["xcrun", "simctl", "ui"]:
            assert len(command) == 5
            assert timeout == 10
            log.write_text("light" if command[-1] == "appearance" else "medium", encoding="utf-8")
            return {"processExit": 0}
        if command[:2] == ["xcodebuild", "test"]:
            assert [arg for arg in command if arg.startswith("-only-testing:")] == [f"-only-testing:{diagnostic.METHOD_PATH}"]
            assert command[command.index("-parallel-testing-enabled") + 1] == "NO"
            assert "ACE_UI_TEST_APPEARANCE=light" in command
            assert environment["TEST_RUNNER_ACE_UI_TEST_APPEARANCE"] == "light"
            assert environment["TEST_RUNNER_ACE_UI_TEST_RETAIN_INITIAL_AUDIT_SCREENSHOT"] == "1"
            assert timeout == 420
            (root / "ui.xcresult").mkdir()
            log.write_text("error: XCTAssertEqual failed at /Users/builder/project/ios/ACEClientApp/ACEClientAppUITests.swift:92\n", encoding="utf-8")
            return {"processExit": 65}
        if command[2] == "get":
            log.write_text(json.dumps({"passedTests": 0, "failedTests": 1, "skippedTests": 0, "testFailures": [{"testCaseName": diagnostic.METHOD, "failureText": "XCTAssertEqual failed", "fileName": "/Users/builder/project/ios/ACEClientApp/ACEClientAppUITests.swift", "lineNumber": 92}]}), encoding="utf-8")
            return {"processExit": 0}
        log.write_text("export failed", encoding="utf-8")
        return {"processExit": 1}

    monkeypatch.setattr(diagnostic, "run", run)
    assert diagnostic.main() == 1
    report = json.loads((safe / "diagnostic.json").read_text())
    assert [command[:3] for command in commands[:5]] == [
        ["xcrun", "simctl", "ui"],
        ["xcrun", "simctl", "ui"],
        ["xcodebuild", "test", "-project"],
        ["xcrun", "simctl", "ui"],
        ["xcrun", "simctl", "ui"],
    ]
    assert [probe["phase"] for probe in report["results"]["simulatorProbes"]["beforeTest"]] == ["beforeTest", "beforeTest"]
    assert [probe["setting"] for probe in report["results"]["simulatorProbes"]["beforeTest"]] == ["appearance", "content_size"]
    assert [probe["phase"] for probe in report["results"]["simulatorProbes"]["afterTest"]] == ["afterTest", "afterTest"]
    assert [probe["setting"] for probe in report["results"]["simulatorProbes"]["afterTest"]] == ["appearance", "content_size"]
    assert report["releaseEvidence"] is False
    assert report["diagnosticStatus"] == "completed-not-release-evidence"
    assert report["results"]["ui"]["counts"] == {"passed": 0, "failed": 1, "skipped": 0}
    assert report["results"]["ui"]["testFailureDetails"][0]["sourceLocation"] == "ios/ACEClientApp/ACEClientAppUITests.swift:92"
    assert report["results"]["ui"]["screenshotStatus"] == "attachment-export-failed"


def test_diagnostic_publishes_test_failure_before_post_test_probe(tmp_path, monkeypatch):
    root = tmp_path / "raw"
    safe = tmp_path / "safe"
    root.mkdir()
    safe.mkdir()
    root_marker = type("Root", (), {"resolve": lambda self: "/Users/builder/project"})()
    monkeypatch.setattr(diagnostic, "ROOT", root)
    monkeypatch.setattr(diagnostic, "SAFE_ROOT", safe)
    monkeypatch.setattr(diagnostic.rt, "ROOT", root_marker)
    monkeypatch.setattr(diagnostic, "context", lambda: "a" * 40)
    monkeypatch.setattr(diagnostic.rt, "_live_artifact_root", lambda path: path)
    monkeypatch.setattr(diagnostic.rt, "resolve_ios_destinations", lambda devices: {devices[0]: "platform=iOS Simulator,id=fixture"})
    simctl_calls = 0

    def run(command, environment, log, timeout):
        nonlocal simctl_calls
        if command[:3] == ["xcrun", "simctl", "ui"]:
            simctl_calls += 1
            if simctl_calls == 3:
                raise KeyboardInterrupt
            log.write_text("light", encoding="utf-8")
            return {"processExit": 0}
        if command[:2] == ["xcodebuild", "test"]:
            log.write_text("error: XCTest failure evidence\n", encoding="utf-8")
            return {"processExit": 65}
        raise AssertionError(f"unexpected command: {command}")

    monkeypatch.setattr(diagnostic, "run", run)
    with pytest.raises(KeyboardInterrupt):
        diagnostic.main()

    report = json.loads((safe / "diagnostic.json").read_text())
    assert report["diagnosticStatus"] == "started"
    assert report["results"]["ui"]["processExit"] == 65
    assert report["results"]["ui"]["errors"] == ["error: XCTest failure evidence"]
    assert [probe["phase"] for probe in report["results"]["simulatorProbes"]["beforeTest"]] == ["beforeTest", "beforeTest"]
    assert "afterTest" not in report["results"]["simulatorProbes"]


def test_large_private_summary_retains_only_redacted_failure_fields(tmp_path, monkeypatch):
    root = tmp_path / "raw"
    root.mkdir()
    bundle = root / "ui.xcresult"
    bundle.mkdir()
    monkeypatch.setattr(diagnostic, "ROOT", root)
    with patch.dict(os.environ, {"PRIVATE_TEST_VALUE": "hidden-token-123"}):
        def run(command, environment, log, timeout):
            log.write_text(json.dumps({"padding": "x" * 3000, "passedTests": 0, "failedTests": 1, "testFailures": [{"failureText": "hidden-token-123"}]}), encoding="utf-8")
            return {"processExit": 0}
        monkeypatch.setattr(diagnostic, "run", run)
        ui = {}
        diagnostic.collect_summary(ui, bundle)
    assert ui["counts"] == {"passed": 0, "failed": 1, "skipped": 0}
    assert ui["testFailureDetails"][0]["failureText"] == "[redacted]"
    assert ui["summaryCommand"] == {"commandKind": "xcresult-summary", "processExit": 0, "responseStatus": "not-published"}


def test_missing_attachments_do_not_erase_failure_details(tmp_path, monkeypatch):
    root = tmp_path / "raw"
    safe = tmp_path / "safe"
    root.mkdir()
    safe.mkdir()
    bundle = root / "ui.xcresult"
    bundle.mkdir()
    ui = {"testFailureDetails": [{"failureText": "retained failure"}]}

    def run(command, environment, log, timeout):
        log.write_text("no attachments", encoding="utf-8")
        export = root / "attachment-export"
        export.mkdir()
        (export / "manifest.json").write_text("[]", encoding="utf-8")
        return {"processExit": 0}

    monkeypatch.setattr(diagnostic, "ROOT", root)
    monkeypatch.setattr(diagnostic, "SAFE_ROOT", safe)
    monkeypatch.setattr(diagnostic, "run", run)
    diagnostic.retain_screenshots(ui, bundle)
    assert ui["testFailureDetails"] == [{"failureText": "retained failure"}]
    assert ui["screenshots"] == []
    assert ui["screenshotStatus"] == "attachment-missing"


def test_partial_valid_attachments_are_retained_with_a_clear_gap(tmp_path, monkeypatch):
    root = tmp_path / "raw"
    safe = tmp_path / "safe"
    root.mkdir()
    safe.mkdir()
    bundle = root / "ui.xcresult"
    bundle.mkdir()

    def run(command, environment, log, timeout):
        export = root / "attachment-export"
        export.mkdir()
        (export / "01.png").write_bytes(_png())
        (export / "manifest.json").write_text(json.dumps([{"attachments": [{"suggestedHumanReadableName": diagnostic.SCREENSHOT_NAMES[0], "exportedFileName": "01.png"}]}]), encoding="utf-8")
        log.write_text("exported", encoding="utf-8")
        return {"processExit": 0}

    monkeypatch.setattr(diagnostic, "ROOT", root)
    monkeypatch.setattr(diagnostic, "SAFE_ROOT", safe)
    monkeypatch.setattr(diagnostic, "run", run)
    ui = {}
    diagnostic.retain_screenshots(ui, bundle)
    assert ui["screenshotStatus"] == "partial"
    assert ui["screenshots"] == [f"screenshots/{diagnostic.METHOD}/01.png"]
    assert ui["missingScreenshotNames"] == list(diagnostic.SCREENSHOT_NAMES[1:])


def test_valid_selector_attachments_are_copied_to_safe_root(tmp_path, monkeypatch):
    root = tmp_path / "raw"
    safe = tmp_path / "safe"
    root.mkdir()
    safe.mkdir()
    bundle = root / "ui.xcresult"
    bundle.mkdir()

    def run(command, environment, log, timeout):
        export = root / "attachment-export"
        export.mkdir()
        attachments = []
        for number, name in enumerate(diagnostic.SCREENSHOT_NAMES, 1):
            exported = f"{number}.png"
            (export / exported).write_bytes(_png())
            attachments.append({"suggestedHumanReadableName": name, "exportedFileName": exported})
        (export / "manifest.json").write_text(json.dumps([{"attachments": attachments}]), encoding="utf-8")
        log.write_text("exported", encoding="utf-8")
        return {"processExit": 0}

    monkeypatch.setattr(diagnostic, "ROOT", root)
    monkeypatch.setattr(diagnostic, "SAFE_ROOT", safe)
    monkeypatch.setattr(diagnostic, "run", run)
    ui = {}
    diagnostic.retain_screenshots(ui, bundle)
    assert ui["screenshotStatus"] == "available"
    assert ui["screenshots"] == [
        f"screenshots/{diagnostic.METHOD}/{number:02d}.png"
        for number in range(1, len(diagnostic.SCREENSHOT_NAMES) + 1)
    ]
    assert all((safe / path).is_file() for path in ui["screenshots"])


def test_unit_settings_mode_runs_one_target_and_never_accepts(tmp_path, monkeypatch):
    root = tmp_path / "raw"
    safe = tmp_path / "safe"
    root.mkdir()
    safe.mkdir()
    monkeypatch.setattr(diagnostic, "ROOT", root)
    monkeypatch.setattr(diagnostic, "SAFE_ROOT", safe)
    monkeypatch.setattr(diagnostic, "context", lambda: "a" * 40)
    monkeypatch.setattr(diagnostic.rt, "_live_artifact_root", lambda path: path)
    monkeypatch.setattr(diagnostic, "_existing_core_destination", lambda: "platform=iOS Simulator,id=fixture")
    monkeypatch.setenv(diagnostic.DIAGNOSTIC_MODE_ENVIRONMENT_KEY, diagnostic.UNIT_SETTINGS_MODE)
    commands = []
    timeouts = []

    def run(command, environment, log, timeout):
        commands.append(command)
        timeouts.append(timeout)
        if command[:4] == ["xcrun", "simctl", "help", "ui"]:
            log.write_text("appearance\ncontent_size\nprivate-token=value", encoding="utf-8")
            return {"processExit": 0}
        if command[:3] == ["xcrun", "simctl", "ui"]:
            log.write_text("unknown\n", encoding="utf-8")
            return {"processExit": 0}
        if command[:2] == ["xcodebuild", "test"]:
            assert [arg for arg in command if arg.startswith("-only-testing:")] == ["-only-testing:ACEClientAppTests"]
            assert command[command.index("-parallel-testing-enabled") + 1] == "NO"
            assert timeout == diagnostic.UNIT_XCODEBUILD_SECONDS
            assert diagnostic.INITIAL_AUDIT_SCREENSHOT_ENVIRONMENT_KEY not in environment
            (root / "unit.xcresult").mkdir()
            log.write_text(
                f"error: XCTest failed at {diagnostic.rt.ROOT}/ios/ACEClientApp/ACEClientAppTests.swift:92\n",
                encoding="utf-8",
            )
            return {"processExit": 65}
        assert command[:5] == ["xcrun", "xcresulttool", "get", "test-results", "summary"]
        log.write_text(json.dumps({
            "passedTests": 64, "failedTests": 1, "skippedTests": 0,
                "testFailures": [{
                    "testCaseName": "ACEClientAppTests.testUnit", "expected": "A", "actual": "B",
                    "failureText": "ghp_abcdefghi /Users/client/ios/Customer.swift",
                }],
        }), encoding="utf-8")
        return {"processExit": 0}

    monkeypatch.setattr(diagnostic, "run", run)
    assert diagnostic.main() == 1
    report = json.loads((safe / "diagnostic.json").read_text(encoding="utf-8"))
    assert report["releaseEvidence"] is False
    assert report["diagnosticStatus"] == "completed-not-release-evidence"
    assert report["results"]["unit"]["expectedTestCount"] == 65
    assert report["results"]["unit"]["actualCounts"] == {"passed": 64, "failed": 1, "skipped": 0}
    assert report["results"]["unit"]["testFailures"][0]["expected"] == "A"
    assert report["results"]["unit"]["testFailures"][0]["sourceFileStatus"] == "absent"
    assert report["results"]["unit"]["testFailures"][0]["sourceLineStatus"] == "absent"
    assert report["results"]["unit"]["logErrorLines"] == [
        "error: XCTest failed at ios/ACEClientApp/ACEClientAppTests.swift:92"
    ]
    assert report["results"]["simulatorProbes"]["settings"][0]["response"] == "unknown"
    assert "private-token=value" not in json.dumps(report)
    assert "ghp_abcdefghi" not in json.dumps(report)
    assert "/Users/client/ios/Customer.swift" not in json.dumps(report)
    assert len(commands) == 5
    assert timeouts == [
        diagnostic.UNIT_UI_SYNTAX_SECONDS,
        diagnostic.UNIT_SETTINGS_QUERY_SECONDS,
        diagnostic.UNIT_SETTINGS_QUERY_SECONDS,
        diagnostic.UNIT_XCODEBUILD_SECONDS,
        diagnostic.UNIT_SUMMARY_SECONDS,
    ]
    assert diagnostic.UNIT_SETUP_SECONDS == 90
    assert diagnostic.UNIT_XCODEBUILD_SECONDS == 120
    assert diagnostic.UNIT_ALLOCATED_SECONDS == 266
    assert diagnostic.UNIT_ALLOCATED_SECONDS < 270
    assert diagnostic.UNIT_WORKFLOW_SECONDS == 300
    assert diagnostic.rt.SIMULATOR_VERIFICATION_SECONDS == 180


def test_native_cycle_runs_one_selector_and_archives_original_failure_records(tmp_path, monkeypatch):
    root = tmp_path / "raw"
    safe = tmp_path / "safe"
    private = tmp_path / "private"
    root.mkdir()
    safe.mkdir()
    monkeypatch.setattr(diagnostic, "ROOT", root)
    monkeypatch.setattr(diagnostic, "SAFE_ROOT", safe)
    monkeypatch.setattr(diagnostic, "PRIVATE_ROOT", private)
    monkeypatch.setattr(diagnostic, "context", lambda workflow=diagnostic.WORKFLOW: "a" * 40)
    monkeypatch.setattr(diagnostic.rt, "_live_artifact_root", lambda path: path)
    monkeypatch.setattr(diagnostic, "_existing_core_destination", lambda: "platform=iOS Simulator,id=fixture")
    monkeypatch.setenv(diagnostic.DIAGNOSTIC_MODE_ENVIRONMENT_KEY, diagnostic.NATIVE_CYCLE_MODE)
    original = b"original-result-byte"
    commands = []

    def run(command, _environment, log, _timeout):
        commands.append(command)
        if command[:4] == ["xcrun", "simctl", "help", "ui"]:
            log.write_text("appearance\ncontent_size\n", encoding="utf-8")
            return {"processExit": 0}
        if command[:3] == ["xcrun", "simctl", "ui"]:
            log.write_text("medium\n", encoding="utf-8")
            return {"processExit": 0}
        if command[:2] == ["xcodebuild", "test"]:
            assert [item for item in command if item.startswith("-only-testing:")] == [
                f"-only-testing:{diagnostic.NATIVE_CYCLE_TEST_SELECTOR}"
            ]
            bundle = root / "unit.xcresult"
            bundle.mkdir()
            (bundle / "Info.plist").write_bytes(original)
            log.write_text(
                "error: XCTAssertEqual failed: (\"MCX19-B intentional fail\") is not equal to (\"Second\")\n",
                encoding="utf-8",
            )
            return {"processExit": 65}
        if command[:5] == ["xcrun", "xcresulttool", "get", "test-results", "summary"]:
            log.write_text(json.dumps({
                "passedTests": 0, "failedTests": 1, "skippedTests": 0,
                "testFailures": [{
                    "testCaseName": "ACEClientAppTests.testActionOrderAndUnknownFieldsRemainSafe",
                    "expected": "Second", "actual": "MCX19-B intentional fail",
                }],
            }), encoding="utf-8")
            return {"processExit": 0}
        assert command[:4] == ["xcrun", "xcresulttool", "export", "attachments"]
        Path(command[-1]).mkdir()
        log.write_text("no attachments\n", encoding="utf-8")
        return {"processExit": 0}

    monkeypatch.setattr(diagnostic, "run", run)
    assert diagnostic.main() == 1
    report = json.loads((safe / "diagnostic.json").read_text(encoding="utf-8"))
    unit = report["results"]["unit"]
    assert unit["status"] == "failed"
    assert unit["actualCounts"] == {"passed": 0, "failed": 1, "skipped": 0}
    assert unit["resolvedDestination"] == "platform=iOS Simulator,id=fixture"
    assert unit["executedCommand"][-3:] == [
        f"-only-testing:{diagnostic.NATIVE_CYCLE_TEST_SELECTOR}",
        "-resultBundlePath", str(root / "unit.xcresult"),
    ]
    assert unit["summaryCommand"]["executedCommand"][:5] == [
        "xcrun", "xcresulttool", "get", "test-results", "summary",
    ]
    assert unit["attachmentExportCommand"]["executedCommand"][:4] == [
        "xcrun", "xcresulttool", "export", "attachments",
    ]
    assert unit["privateRecordCollection"] == "complete"
    archive = private / diagnostic.PRIVATE_ARCHIVE_NAME
    with tarfile.open(archive, "r:gz") as records:
        names = records.getnames()
        assert "records/unit.xcresult/Info.plist" in names
        assert records.extractfile("records/unit.xcresult/Info.plist").read() == original
        inventory = json.load(records.extractfile("records/collection-inventory.json"))
    assert inventory["candidateCommit"] == "a" * 40
    assert inventory["collectionState"] == "complete"
    assert inventory["testSelector"] == diagnostic.NATIVE_CYCLE_TEST_SELECTOR
    assert inventory["processExit"] == 65
    assert inventory["actualCounts"] == {"passed": 0, "failed": 1, "skipped": 0}
    assert inventory["failureStatus"] == "available"
    assert inventory["commands"]["xcodebuild-test"] == unit["executedCommand"]
    assert inventory["commands"]["xcresult-summary"] == unit["summaryCommand"]
    assert inventory["commands"]["xcresult-attachment-export"] == unit["attachmentExportCommand"]
    assert any(entry["relativePath"] == "records/unit.log" for entry in inventory["records"])
    assert len([item for item in commands if item[:2] == ["xcodebuild", "test"]]) == 1


def test_native_cycle_context_requires_its_workflow_and_api_trigger(tmp_path, monkeypatch):
    monkeypatch.setattr(diagnostic.sys, "platform", "darwin")
    monkeypatch.setattr(diagnostic.rt, "ROOT", tmp_path)
    monkeypatch.setattr(diagnostic.rt, "_live_repository_metadata", lambda commit: {"commit": commit})
    environment = {
        "ACE_LIVE_EVIDENCE_APPROVED_COMMIT": "a" * 40,
        diagnostic.rt.LIVE_WORKFLOW_ENVIRONMENT_KEY: diagnostic.NATIVE_CYCLE_WORKFLOW,
        "CM_COMMIT": "a" * 40,
        "CM_BRANCH": diagnostic.rt.LIVE_BRANCH,
        "CM_TRIGGER_SOURCE": "api",
        "CM_BUILD_ID": "build-1",
        "CM_BUILD_STARTED_BY": "operator",
        "CM_BUILD_DIR": str(tmp_path),
    }
    with patch.dict(os.environ, environment, clear=True):
        assert diagnostic.context(diagnostic.NATIVE_CYCLE_WORKFLOW) == "a" * 40
    environment["CM_TRIGGER_SOURCE"] = "webhook"
    with patch.dict(os.environ, environment, clear=True), pytest.raises(ValueError):
        diagnostic.context(diagnostic.NATIVE_CYCLE_WORKFLOW)


def test_native_cycle_returns_zero_only_after_pass_collection_and_final_publication(tmp_path, monkeypatch):
    def run_case(name, collection, final_publication, expected_exit):
        root = tmp_path / name / "raw"
        safe = tmp_path / name / "safe"
        root.mkdir(parents=True)
        safe.mkdir()
        with monkeypatch.context() as local:
            local.setattr(diagnostic, "ROOT", root)
            local.setattr(diagnostic, "SAFE_ROOT", safe)
            local.setattr(diagnostic, "PRIVATE_ROOT", tmp_path / name / "private")
            local.setattr(diagnostic, "context", lambda workflow=diagnostic.WORKFLOW: "a" * 40)
            local.setattr(diagnostic.rt, "_live_artifact_root", lambda path: path)
            local.setattr(diagnostic, "_existing_core_destination", lambda: "platform=iOS Simulator,id=fixture")
            local.setenv(diagnostic.DIAGNOSTIC_MODE_ENVIRONMENT_KEY, diagnostic.NATIVE_CYCLE_MODE)
            local.setattr(diagnostic, "_collect_native_cycle_records", lambda *_args: collection)
            publication_calls = []
            publication_reports = []

            def publish_unit(report, _deadline):
                publication_calls.append(True)
                publication_reports.append(report)
                return final_publication or len(publication_calls) < 3

            def run(command, _environment, log, _timeout):
                if command[:4] == ["xcrun", "simctl", "help", "ui"]:
                    log.write_text("appearance\ncontent_size\n", encoding="utf-8")
                    return {"processExit": 0}
                if command[:3] == ["xcrun", "simctl", "ui"]:
                    log.write_text("medium\n", encoding="utf-8")
                    return {"processExit": 0}
                if command[:2] == ["xcodebuild", "test"]:
                    bundle = root / "unit.xcresult"
                    bundle.mkdir()
                    (bundle / "Info.plist").write_bytes(b"original-pass-result")
                    log.write_text("Test Suite passed\n", encoding="utf-8")
                    return {"processExit": 0}
                assert command[:5] == ["xcrun", "xcresulttool", "get", "test-results", "summary"]
                log.write_text(json.dumps({
                    "passedTests": 1, "failedTests": 0, "skippedTests": 0,
                    "testFailures": [],
                }), encoding="utf-8")
                return {"processExit": 0}

            local.setattr(diagnostic, "run", run)
            local.setattr(diagnostic, "_publish_unit_report", publish_unit)
            assert diagnostic.main() == expected_exit
            report = publication_reports[-1]
            assert report["results"]["unit"]["status"] == "passed"
            assert report["results"]["unit"]["privateRecordCollection"] == collection
            assert "intentionalNonZeroExit" not in report

    run_case("pass", "complete", True, 0)
    run_case("collection-failure", "sensitive-record", True, 1)
    run_case("publication-failure", "complete", False, 1)


def test_native_collection_stops_for_missing_bundle_or_sensitive_record(tmp_path, monkeypatch):
    root = tmp_path / "raw"
    private = tmp_path / "private"
    root.mkdir()
    monkeypatch.setattr(diagnostic, "ROOT", root)
    monkeypatch.setattr(diagnostic, "PRIVATE_ROOT", private)
    unit = {"summaryStatus": "available", "processExit": 65}
    assert diagnostic._collect_native_cycle_records("a" * 40, unit, root / "missing.xcresult") == "result-bundle-unavailable"
    assert not private.exists()

    bundle = root / "unit.xcresult"
    bundle.mkdir()
    (bundle / "Info.plist").write_text('{"token":"blocked"}', encoding="utf-8")
    for name in (
        "unit.log", "unit-summary.json", "simctl-help-ui.log",
        "unit-simctl-appearance-query.log", "unit-simctl-content_size-query.log",
    ):
        (root / name).write_text("controlled", encoding="utf-8")
    (root / "unit-summary.json").write_text("{}", encoding="utf-8")

    def run(command, _environment, log, _timeout):
        assert command[:4] == ["xcrun", "xcresulttool", "export", "attachments"]
        Path(command[-1]).mkdir()
        log.write_text("controlled", encoding="utf-8")
        return {"processExit": 0}

    monkeypatch.setattr(diagnostic, "run", run)
    assert diagnostic._collect_native_cycle_records("a" * 40, unit, bundle) == "sensitive-record"
    assert not (private / diagnostic.PRIVATE_ARCHIVE_NAME).exists()


def test_native_collection_rejects_an_empty_result_bundle(tmp_path, monkeypatch):
    root = tmp_path / "raw"
    private = tmp_path / "private"
    root.mkdir()
    (root / "unit.xcresult").mkdir()
    for name in (
        "unit.log", "unit-summary.json", "simctl-help-ui.log",
        "unit-simctl-appearance-query.log", "unit-simctl-content_size-query.log",
    ):
        (root / name).write_text("{}", encoding="utf-8")
    monkeypatch.setattr(diagnostic, "ROOT", root)
    monkeypatch.setattr(diagnostic, "PRIVATE_ROOT", private)

    def run(command, _environment, log, _timeout):
        assert command[:4] == ["xcrun", "xcresulttool", "export", "attachments"]
        Path(command[-1]).mkdir()
        log.write_text("controlled", encoding="utf-8")
        return {"processExit": 0}

    monkeypatch.setattr(diagnostic, "run", run)
    unit = {"summaryStatus": "available", "processExit": 65}
    assert diagnostic._collect_native_cycle_records(
        "a" * 40, unit, root / "unit.xcresult"
    ) == "result-bundle-empty"
    assert not (private / diagnostic.PRIVATE_ARCHIVE_NAME).exists()


def test_private_collection_rejects_symlink_and_invalid_archive_path(tmp_path, monkeypatch):
    root = tmp_path / "records"
    root.mkdir()
    target = root / "file"
    target.write_text("controlled", encoding="utf-8")
    safe = root / "safe"
    safe.write_text("controlled", encoding="utf-8")
    original_is_symlink = Path.is_symlink
    monkeypatch.setattr(
        Path, "is_symlink", lambda path: path == target or original_is_symlink(path)
    )
    with pytest.raises(diagnostic.PrivateRecordCollectionError, match="symlink-record"):
        diagnostic._private_regular_files(root)
    with pytest.raises(diagnostic.PrivateRecordCollectionError, match="archive-path-invalid"):
        diagnostic._private_record_entries([(safe, "unexpected/file", "test")], "complete")
    for unsafe_path in ("records/../outside", "records/./same", "records//same"):
        with pytest.raises(diagnostic.PrivateRecordCollectionError, match="archive-path-invalid"):
            diagnostic._private_record_entries([(safe, unsafe_path, "test")], "complete")
    with pytest.raises(diagnostic.PrivateRecordCollectionError, match="archive-path-duplicate"):
        diagnostic._private_record_entries([
            (safe, "records/duplicate", "test"),
            (safe, "records/duplicate", "test"),
        ], "complete")
    with pytest.raises(diagnostic.PrivateRecordCollectionError, match="record-count-exceeded"):
        diagnostic._private_record_entries([
            (safe, f"records/{number}", "test")
            for number in range(diagnostic.PRIVATE_RECORD_MAX_FILES + 1)
        ], "complete")


def test_unit_destination_uses_bounded_ready_core_resolver(monkeypatch):
    calls = []

    def resolve(names, recorder=None, verification_seconds=None, require_ready=False):
        calls.append((names, recorder, verification_seconds, require_ready))
        return {diagnostic.rt.IOS_CORE_DEVICE: "platform=iOS Simulator,id=fixture"}

    monkeypatch.setattr(diagnostic.rt, "resolve_ios_destinations", resolve)
    assert diagnostic._existing_core_destination() == "platform=iOS Simulator,id=fixture"
    assert calls == [((diagnostic.rt.IOS_CORE_DEVICE,), None, diagnostic.UNIT_SETUP_SECONDS, True)]


def test_unit_readiness_failure_publishes_safe_fixed_result_before_probes(tmp_path, monkeypatch):
    root = tmp_path / "raw"
    safe = tmp_path / "safe"
    root.mkdir()
    safe.mkdir()
    monkeypatch.setattr(diagnostic, "ROOT", root)
    monkeypatch.setattr(diagnostic, "SAFE_ROOT", safe)
    monkeypatch.setattr(diagnostic, "context", lambda: "a" * 40)
    monkeypatch.setattr(diagnostic.rt, "_live_artifact_root", lambda path: path)
    private_error = "private readiness token=secret"
    monkeypatch.setattr(
        diagnostic.rt, "resolve_ios_destinations",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            diagnostic.rt.SimulatorResolutionError(private_error)
        ),
    )
    calls = []
    monkeypatch.setattr(diagnostic, "run", lambda *args: calls.append(args) or {"processExit": 0})
    published = []
    original_publish = diagnostic.publish

    def capture_publish(report, deadline=None):
        published.append(json.loads(json.dumps(report)))
        original_publish(report, deadline)

    monkeypatch.setattr(diagnostic, "publish", capture_publish)
    monkeypatch.setenv(diagnostic.DIAGNOSTIC_MODE_ENVIRONMENT_KEY, diagnostic.UNIT_SETTINGS_MODE)
    assert diagnostic.main() == 1
    assert calls == []
    assert published[0]["diagnosticStatus"] == "started"
    assert published[0]["releaseEvidence"] is False
    assert published[0]["results"] == {}
    report = json.loads((safe / "diagnostic.json").read_text(encoding="utf-8"))
    assert report["releaseEvidence"] is False
    assert report["diagnosticStatus"] == "setup-failed"
    assert report["results"] == {"setup": {
        "phase": "simulator-readiness", "reason": "resolution-failed",
    }}
    assert private_error not in json.dumps(report)


@pytest.mark.parametrize("error_type", [OSError, ValueError])
def test_unit_readiness_resolver_error_publishes_safe_fixed_result_before_probes(
    tmp_path, monkeypatch, capsys, error_type
):
    root = tmp_path / "raw"
    safe = tmp_path / "safe"
    root.mkdir()
    safe.mkdir()
    monkeypatch.setattr(diagnostic, "ROOT", root)
    monkeypatch.setattr(diagnostic, "SAFE_ROOT", safe)
    monkeypatch.setattr(diagnostic, "context", lambda: "a" * 40)
    monkeypatch.setattr(diagnostic.rt, "_live_artifact_root", lambda path: path)
    private_error = "private simctl output=secret /Users/client/ios/Secret.swift"
    monkeypatch.setattr(
        diagnostic.rt, "resolve_ios_destinations",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(error_type(private_error)),
    )
    calls = []
    monkeypatch.setattr(diagnostic, "run", lambda *args: calls.append(args) or {"processExit": 0})
    monkeypatch.setenv(diagnostic.DIAGNOSTIC_MODE_ENVIRONMENT_KEY, diagnostic.UNIT_SETTINGS_MODE)

    assert diagnostic.main() == 1
    captured = capsys.readouterr()
    assert '"diagnosticStatus": "started"' in captured.out
    assert '"diagnosticStatus": "setup-failed"' in captured.out
    assert '"reason": "resolution-failed"' in captured.out
    assert captured.out.endswith("diagnostic setup rejected; no test started\n")
    assert captured.err == ""
    assert private_error not in captured.out
    assert private_error not in captured.err
    assert calls == []
    report = json.loads((safe / "diagnostic.json").read_text(encoding="utf-8"))
    assert report["releaseEvidence"] is False
    assert report["diagnosticStatus"] == "setup-failed"
    assert report["results"] == {"setup": {
        "phase": "simulator-readiness", "reason": "resolution-failed",
    }}
    assert private_error not in json.dumps(report)


def test_unit_readiness_timeout_publishes_safe_fixed_result_before_probes(tmp_path, monkeypatch):
    root = tmp_path / "raw"
    safe = tmp_path / "safe"
    root.mkdir()
    safe.mkdir()
    monkeypatch.setattr(diagnostic, "ROOT", root)
    monkeypatch.setattr(diagnostic, "SAFE_ROOT", safe)
    monkeypatch.setattr(diagnostic, "context", lambda: "a" * 40)
    monkeypatch.setattr(diagnostic.rt, "_live_artifact_root", lambda path: path)
    monkeypatch.setattr(
        diagnostic.rt, "resolve_ios_destinations",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            diagnostic.rt.SimulatorResolutionError(
                "private timeout output", diagnostic.rt.SIMULATOR_RESOLUTION_TIMEOUT_REASON
            )
        ),
    )
    calls = []
    monkeypatch.setattr(diagnostic, "run", lambda *args: calls.append(args) or {"processExit": 0})
    monkeypatch.setenv(diagnostic.DIAGNOSTIC_MODE_ENVIRONMENT_KEY, diagnostic.UNIT_SETTINGS_MODE)
    assert diagnostic.main() == 1
    assert calls == []
    report = json.loads((safe / "diagnostic.json").read_text(encoding="utf-8"))
    assert report["releaseEvidence"] is False
    assert report["diagnosticStatus"] == "setup-failed"
    assert report["results"] == {"setup": {
        "phase": "simulator-readiness", "reason": "timeout",
    }}
    assert "private timeout output" not in json.dumps(report)


def test_unit_publication_deadline_retains_previous_report(tmp_path, monkeypatch):
    safe = tmp_path / "safe"
    safe.mkdir()
    target = safe / "diagnostic.json"
    target.write_text('{"diagnosticStatus":"started"}\n', encoding="utf-8")
    monkeypatch.setattr(diagnostic, "SAFE_ROOT", safe)
    monkeypatch.setattr(diagnostic.time, "monotonic", lambda: 100.0)
    assert diagnostic._publish_unit_report({"diagnosticStatus": "later"}, 100.0) is False
    assert target.read_text(encoding="utf-8") == '{"diagnosticStatus":"started"}\n'
    assert not (safe / ".diagnostic.json.tmp").exists()


def test_copy_controls_mode_remains_the_default(monkeypatch):
    monkeypatch.delenv(diagnostic.DIAGNOSTIC_MODE_ENVIRONMENT_KEY, raising=False)
    assert diagnostic.diagnostic_mode() == diagnostic.COPY_CONTROLS_MODE
