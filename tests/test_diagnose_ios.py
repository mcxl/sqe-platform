import os
import json
from pathlib import Path
from unittest.mock import patch

import pytest

from tools import diagnose_ios as diagnostic


def test_redaction_keeps_error_but_removes_private_values():
    with patch.dict(os.environ, {"PRIVATE_TEST_VALUE": "hidden-token-123"}):
        text = diagnostic.redact('error: hidden-token-123 /Users/builder/project/file.swift:18 user@host.invalid https://private.invalid token=secret')
    assert "error:" in text
    assert "hidden-token-123" not in text
    assert "/Users/" not in text
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


def test_exact_scope_and_retention_contract():
    source = Path(diagnostic.__file__).read_text(encoding="utf-8")
    yaml = (diagnostic.rt.ROOT / "codemagic.yaml").read_text(encoding="utf-8")
    section = yaml.split("  ace-ios-diagnostic-manual:", 1)[1].split("  ace-ios-core:", 1)[0]
    assert "max_build_duration: 15" in section
    assert "triggering:" not in section
    assert "- mcx19_diagnostic" in section
    assert "mcx19_live_evidence" not in section
    assert "/private/tmp/mcx-19-diagnostic-safe/diagnostic.json" in section
    assert "live-evidence --" not in section
    assert "ios_release_ui_matrix" not in source
    assert diagnostic.METHODS == (
        "testSignInPasswordFieldIsSecure",
        "testFictionalReleaseHasApprovedCopyControls",
        "testAllControlledScenariosShowExpectedStateAndAudit",
    )
    assert "ui_log, 360" in source


def test_diagnostic_runs_only_three_functional_methods_and_retains_failure(tmp_path, monkeypatch):
    """Catch an extra build, wrong selector/appearance, or lost assertion details."""
    root = tmp_path / "raw"
    safe = tmp_path / "safe"
    root.mkdir()
    safe.mkdir()
    monkeypatch.setattr(diagnostic, "ROOT", root)
    monkeypatch.setattr(diagnostic, "SAFE_ROOT", safe)
    monkeypatch.setattr(diagnostic, "context", lambda: "a" * 40)
    monkeypatch.setattr(diagnostic.rt, "_live_artifact_root", lambda path: path)
    monkeypatch.setattr(diagnostic.rt, "resolve_ios_destinations", lambda devices: {devices[0]: "platform=iOS Simulator,id=fixture"})
    commands = []

    def run(command, environment, log, timeout):
        commands.append(command)
        if command[:2] == ["xcodebuild", "test"]:
            assert [arg for arg in command if arg.startswith("-only-testing:")] == [
                f"-only-testing:ACEClientAppUITests/ACEClientAppUITests/{method}" for method in diagnostic.METHODS
            ]
            assert "ACE_UI_TEST_APPEARANCE=light" in command
            assert environment["TEST_RUNNER_ACE_UI_TEST_APPEARANCE"] == "light"
            assert timeout == 360
            (root / "ui.xcresult").mkdir()
            log.write_text(
                'error: XCTAssertEqual failed: light is not dark\n'
                'ACE_A11Y_ISSUE {"scenario":"signIn","auditType":"contrast",'
                '"compactDescription":"Contrast failed","detailedDescription":"Text contrast failed",'
                '"element":{"identifier":"Password","label":"Password","type":"SecureTextField",'
                '"frame":{"x":1,"y":2,"width":3,"height":4}}}\n',
                encoding="utf-8",
            )
            return {"processExit": 65}
        assert command[:4] == ["xcrun", "xcresulttool", "get", "test-results"]
        log.write_text(json.dumps({"passedTests": 0, "failedTests": 1, "skippedTests": 0,
            "testFailures": [{"failureText": "XCTAssertEqual failed: light is not dark"}]}))
        return {"processExit": 0}

    monkeypatch.setattr(diagnostic, "run", run)
    assert diagnostic.main() == 1
    report = json.loads((safe / "diagnostic.json").read_text())
    assert len(commands) == 2
    assert set(report["results"]) == {"ui"}
    assert report["releaseEvidence"] is False
    assert report["results"]["ui"]["selectors"] == list(diagnostic.METHODS)
    assert "light is not dark" in report["results"]["ui"]["testFailureDetails"]
    assert report["results"]["ui"]["accessibilityIssues"] == [{
        "scenario": "signIn", "auditType": "contrast", "compactDescription": "Contrast failed",
        "detailedDescription": "Text contrast failed", "element": {
            "identifier": "Password", "label": "Password", "type": "SecureTextField",
            "frame": {"x": 1, "y": 2, "width": 3, "height": 4},
        },
    }]
