#!/usr/bin/env python3
"""One manual G0 iOS diagnostic. It is never release evidence."""
from __future__ import annotations

import json
import math
import os
from pathlib import Path
import re
import shutil
import signal
import subprocess
import sys

try:
    from tools import run_tests as rt
except ModuleNotFoundError:
    import run_tests as rt

WORKFLOW = "ace-ios-diagnostic-manual"
ROOT = Path("/private/tmp/mcx-19-diagnostic")
SAFE_ROOT = Path("/private/tmp/mcx-19-diagnostic-safe")
METHOD = "testFictionalReleaseHasApprovedCopyControls"
METHOD_PATH = f"ACEClientAppUITests/ACEClientAppUITests/{METHOD}"
RUNNER_SCREENSHOT_NAMES = rt._expected_logical_screenshot_names(f"ios-release-{rt.IOS_CORE_DEVICE}-light-{METHOD}")
INITIAL_AUDIT_SCREENSHOT_NAME = "Fictional release — initial-audit — light"
SCREENSHOT_NAMES = (*RUNNER_SCREENSHOT_NAMES, INITIAL_AUDIT_SCREENSHOT_NAME)
INITIAL_AUDIT_SCREENSHOT_ENVIRONMENT_KEY = "TEST_RUNNER_ACE_UI_TEST_RETAIN_INITIAL_AUDIT_SCREENSHOT"
DIAGNOSTIC_TEST_ENVIRONMENT = {
    **rt.ios_test_environment("light"),
    # xcodebuild forwards this TEST_RUNNER_ value to XCTest without the prefix.
    INITIAL_AUDIT_SCREENSHOT_ENVIRONMENT_KEY: "1",
}
A11Y_ISSUE_TAG = "ACE_A11Y_ISSUE "
A11Y_ISSUE_LIMIT = 30
A11Y_ISSUE_LINE_LIMIT = 16 * 1024
A11Y_ISSUE_TEXT_LIMIT = 256
LOG_RESPONSE_LIMIT = 2 * 1024
FAILURE_DETAIL_LIMIT = 30
FAILURE_TEXT_LIMIT = 2 * 1024


def redact(text: str) -> str:
    """Remove private data, while retaining allowlisted repository locations."""
    repository_root = re.escape(str(rt.ROOT.resolve()).replace("\\", "/"))
    text = re.sub(
        rf"{repository_root}[\\/](?P<path>"
        r"(?:apps|ios|quality|security|src|tests|tools|workflows)[\\/][^\s:]+"
        r"(?::\d+(?::\d+)?)?)",
        lambda match: match.group("path").replace("\\", "/"),
        text,
    )
    for value in sorted(set(os.environ.values()), key=len, reverse=True):
        if len(value) >= 8:
            text = text.replace(value, "[redacted]")
    text = re.sub(r"(?i)(?:https?|ssh)://\S+", "[url]", text)
    text = re.sub(r"\b[^\s@]+@[^\s@]+\b", "[address]", text)
    text = re.sub(
        r"(?:(?:[A-Za-z]:)?[\\/](?:Users|private|var|Volumes|Applications)[\\/][^\s:]+)",
        "[path]",
        text,
    )
    text = re.sub(r"(?i)(password|token|authorization|credential|secret)\s*[:=].*", r"\1=[redacted]", text)
    text = re.sub(r"\b(?:gh[pousr]_[A-Za-z0-9_]+|github_pat_[A-Za-z0-9_]+|sk-[A-Za-z0-9_-]+)\b", "[redacted]", text)
    return "".join(char for char in text if char.isprintable() or char == "\n")[:FAILURE_TEXT_LIMIT]


def errors(path: Path) -> list[str]:
    if not path.is_file() or path.is_symlink():
        return ["error log unavailable"]
    if path.stat().st_size > 16 * 1024 * 1024:
        return ["error log exceeds diagnostic limit"]
    selected = []
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if re.search(r"error:|failed|XCTAssert|requires a development team|provisioning profile", line, re.I):
            safe = redact(line)
            if safe not in selected:
                selected.append(safe)
        if len(selected) == FAILURE_DETAIL_LIMIT:
            break
    return selected or ["no matching error lines; cause unknown"]


def accessibility_issues(path: Path) -> tuple[list[dict[str, object]], str | None]:
    """Retain bounded, redacted fault locations without a UI hierarchy or values."""
    if not path.is_file() or path.is_symlink() or path.stat().st_size > 16 * 1024 * 1024:
        return [], "unavailable"
    selected = []
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        _, tag, payload = line.partition(A11Y_ISSUE_TAG)
        if not tag or len(payload) > A11Y_ISSUE_LINE_LIMIT:
            if tag:
                return selected, "truncated"
            continue
        try:
            parsed = json.loads(payload)
        except (json.JSONDecodeError, RecursionError):
            continue
        issue = _normalise_accessibility_issue(parsed)
        if issue is not None:
            selected.append(issue)
        if len(selected) > A11Y_ISSUE_LIMIT:
            return selected[:A11Y_ISSUE_LIMIT], "truncated"
    return selected, None


def _normalise_accessibility_issue(payload: object) -> dict[str, object] | None:
    if not isinstance(payload, dict):
        return None
    element = payload.get("element")
    if not isinstance(element, dict):
        return None
    fields = ("scenario", "auditType", "compactDescription", "detailedDescription")
    if not all(isinstance(payload.get(field), str) for field in fields):
        return None
    result: dict[str, object] = {field: _bounded_a11y_text(payload[field]) for field in fields}
    result["element"] = {
        "identifier": _bounded_a11y_text(element.get("identifier", "")),
        "label": _bounded_a11y_text(element.get("label", "")),
        "type": _bounded_a11y_text(element.get("type", "")),
    }
    if "frame" in element:
        frame = element["frame"]
        if not isinstance(frame, dict) or not all(_finite_frame_value(frame.get(field)) for field in ("x", "y", "width", "height")):
            return None
        result["element"]["frame"] = {field: frame[field] for field in ("x", "y", "width", "height")}
    return result


def _bounded_a11y_text(value: object) -> str:
    return redact(value)[:A11Y_ISSUE_TEXT_LIMIT] if isinstance(value, str) else ""


def _finite_frame_value(value: object) -> bool:
    return type(value) in (int, float) and math.isfinite(value)


def _safe_text(path: Path, maximum_bytes: int) -> tuple[str, str | None]:
    """Read a regular file and return a redacted bounded excerpt."""
    try:
        if path.is_symlink() or not path.is_file():
            return "unavailable", None
        if path.stat().st_size > maximum_bytes:
            return "oversized", None
        content = path.read_bytes()
    except OSError:
        return "unavailable", None
    return "available", redact(content.decode("utf-8", errors="replace"))[:LOG_RESPONSE_LIMIT]


def _command_record(kind: str, result: dict, log: Path) -> dict[str, object]:
    state, response = _safe_text(log, LOG_RESPONSE_LIMIT)
    record: dict[str, object] = {"commandKind": kind, **result, "responseStatus": state}
    if response is not None:
        record["response"] = response
    return record


def diagnostic_command_environment(environment: dict[str, str]) -> dict[str, str]:
    """Add the approved diagnostic screenshot flag after shared environment validation."""
    screenshot_flag = None
    if INITIAL_AUDIT_SCREENSHOT_ENVIRONMENT_KEY in environment:
        screenshot_flag = environment[INITIAL_AUDIT_SCREENSHOT_ENVIRONMENT_KEY]
        if screenshot_flag != "1":
            raise ValueError("diagnostic screenshot flag is invalid")
    shared_environment = {
        key: value for key, value in environment.items()
        if key != INITIAL_AUDIT_SCREENSHOT_ENVIRONMENT_KEY
    }
    command_environment = rt._live_command_environment(shared_environment)
    if screenshot_flag == "1":
        command_environment[INITIAL_AUDIT_SCREENSHOT_ENVIRONMENT_KEY] = screenshot_flag
    return command_environment


def run(command: list[str], environment: dict[str, str], log: Path, timeout: int) -> dict:
    with log.open("w", encoding="utf-8") as stream:
        try:
            process = subprocess.Popen(
                command, cwd=rt.ROOT / "ios/ACEClientApp", env=diagnostic_command_environment(environment),
                stdout=stream, stderr=subprocess.STDOUT, start_new_session=True,
            )
            try:
                return {"processExit": process.wait(timeout=timeout)}
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGKILL)
                process.wait()
                return {"status": "timeout"}
        except OSError:
            return {"status": "start-failed"}


def context() -> str:
    expected = os.environ.get("ACE_LIVE_EVIDENCE_APPROVED_COMMIT", "")
    if (
        sys.platform != "darwin"
        or os.environ.get(rt.LIVE_WORKFLOW_ENVIRONMENT_KEY) != WORKFLOW
        or os.environ.get("CM_COMMIT") != expected
        or os.environ.get("CM_BRANCH") != rt.LIVE_BRANCH
        or os.environ.get("CM_TRIGGER_SOURCE") != "api"
        or not os.environ.get("CM_BUILD_ID")
        or not os.environ.get("CM_BUILD_STARTED_BY")
        or Path(os.environ.get("CM_BUILD_DIR", "")).resolve() != rt.ROOT.resolve()
    ):
        raise ValueError("diagnostic context rejected")
    rt._live_repository_metadata(expected)
    return expected


def _build_id() -> str | None:
    value = os.environ.get("CM_BUILD_ID", "")
    return value if re.fullmatch(r"[A-Za-z0-9_-]{1,128}", value) else None


def _simulator_identifier(destination: str) -> str | None:
    for part in destination.split(","):
        key, separator, value = part.partition("=")
        if separator and key.strip() == "id" and value:
            return value
    return None


def settings_probes(identifier: str, phase: str) -> list[dict[str, object]]:
    """Read simulator settings only. This helper never changes simulator settings."""
    probes = []
    for setting in ("appearance", "content_size"):
        log = ROOT / f"simctl-{phase}-{setting}-query.log"
        result = run(["xcrun", "simctl", "ui", identifier, setting], {}, log, 10)
        record = _command_record("simctl-ui-query", result, log)
        if isinstance(record.get("response"), str):
            record["response"] = record["response"].replace(identifier, "[simulator]")
        probes.append(record | {"phase": phase, "setting": setting})
    return probes


def failure_details(payload: object) -> tuple[list[dict[str, object]], str]:
    """Retain allowlisted XCTest failure fields. Do not infer assertion values."""
    selected: list[dict[str, object]] = []
    pending = [payload]
    visited = 0
    found = False
    while pending:
        value = pending.pop()
        visited += 1
        if visited > rt.LIVE_RESULT_SUMMARY_MAX_NODES:
            return selected, "truncated"
        if isinstance(value, dict):
            failures = value.get("testFailures")
            if isinstance(failures, list):
                found = True
                for failure in failures:
                    if not isinstance(failure, dict):
                        continue
                    detail = _failure_detail(failure)
                    if detail:
                        selected.append(detail)
                    if len(selected) >= FAILURE_DETAIL_LIMIT:
                        return selected, "truncated"
            pending.extend(value.values())
        elif isinstance(value, list):
            pending.extend(value)
    return selected, "available" if found else "not-recorded"


def _failure_detail(failure: dict[str, object]) -> dict[str, object]:
    detail: dict[str, object] = {"expectedActual": None, "sourceLocation": None}
    for field in ("testCaseName", "failureText", "message", "description"):
        value = failure.get(field)
        if isinstance(value, str):
            detail[field] = redact(value)[:FAILURE_TEXT_LIMIT]
    locations = []
    for field in ("file", "fileName", "location", "sourceCodeLocation"):
        value = failure.get(field)
        if isinstance(value, str):
            safe = redact(value)[:FAILURE_TEXT_LIMIT]
            detail[field] = safe
            locations.append(safe)
    for field in ("line", "lineNumber", "column", "columnNumber"):
        value = failure.get(field)
        if type(value) is int and value >= 0:
            detail[field] = value
    expected_actual = {}
    for field in ("expected", "expectedValue", "actual", "actualValue"):
        value = failure.get(field)
        if isinstance(value, str):
            expected_actual[field] = redact(value)[:FAILURE_TEXT_LIMIT]
        elif type(value) in (int, float, bool):
            expected_actual[field] = value
    if expected_actual:
        detail["expectedActual"] = expected_actual
    if locations:
        line = detail.get("lineNumber", detail.get("line"))
        detail["sourceLocation"] = f"{locations[0]}:{line}" if isinstance(line, int) else locations[0]
    return detail if len(detail) > 2 else {}


def collect_summary(ui: dict[str, object], bundle: Path) -> None:
    """Add bounded failure data without replacing existing diagnostics."""
    if not bundle.is_dir() or bundle.is_symlink():
        ui["summary"] = "result-bundle-unavailable"
        ui["testFailureDetails"] = []
        ui["testFailureDetailStatus"] = "not-recorded"
        return
    summary = ROOT / "summary.json"
    result = run(["xcrun", "xcresulttool", "get", "test-results", "summary", "--path", str(bundle)], {}, summary, 30)
    summary_record = _command_record("xcresult-summary", result, summary)
    if result.get("processExit") == 0:
        summary_record.pop("response", None)
        summary_record["responseStatus"] = "not-published"
    ui["summaryCommand"] = summary_record
    if result.get("processExit") != 0:
        ui["summary"] = "command-failed"
        ui["testFailureDetails"] = []
        ui["testFailureDetailStatus"] = "unavailable"
        return
    state, content = rt._bounded_live_file_text(ROOT, summary, rt.LIVE_RESULT_SUMMARY_MAX_BYTES)
    if state != "available" or content is None:
        ui["summary"] = "unavailable"
        ui["testFailureDetails"] = []
        ui["testFailureDetailStatus"] = "unavailable"
        return
    try:
        payload = json.loads(content)
    except (ValueError, RecursionError):
        ui["summary"] = "unreadable"
        ui["testFailureDetails"] = []
        ui["testFailureDetailStatus"] = "unavailable"
        return
    counts = rt._xcresult_counts(payload)
    if counts is not None:
        ui["counts"] = {"passed": counts[0], "failed": counts[1], "skipped": counts[2]}
    details, status = failure_details(payload)
    ui["testFailureDetails"] = details
    ui["testFailureDetailStatus"] = status
    ui["summary"] = "available"


def retain_screenshots(ui: dict[str, object], bundle: Path) -> None:
    """Publish only verified PNG attachments for the approved fictional selector."""
    ui["screenshots"] = []
    if not bundle.is_dir() or bundle.is_symlink():
        ui["screenshotStatus"] = "result-bundle-unavailable"
        return
    export_directory = ROOT / "attachment-export"
    export_log = ROOT / "attachment-export.log"
    if export_directory.exists() or export_directory.is_symlink():
        ui["screenshotStatus"] = "attachment-export-unavailable"
        return
    result = run(["xcrun", "xcresulttool", "export", "attachments", "--path", str(bundle), "--output-path", str(export_directory)], {}, export_log, 30)
    ui["attachmentExport"] = _command_record("xcresult-attachment-export", result, export_log)
    if result.get("processExit") != 0:
        ui["screenshotStatus"] = "attachment-export-failed"
        return
    if export_directory.is_symlink() or not export_directory.is_dir() or not export_directory.resolve().is_relative_to(ROOT.resolve()):
        ui["screenshotStatus"] = "attachment-invalid"
        return
    entries = rt._attachment_export_entries(ROOT, export_directory)
    if entries is None:
        ui["screenshotStatus"] = "attachment-invalid"
        return
    by_name: dict[str, Path] = {}
    rejected = 0
    for logical, source in entries:
        matched = next((name for name in SCREENSHOT_NAMES if logical == name or re.fullmatch(rf"{re.escape(name)}_[0-9]+_[0-9A-Fa-f-]+(?:\.png)?", logical)), None)
        if matched is None or matched in by_name:
            rejected += 1
            continue
        by_name[matched] = source
    missing = [name for name in SCREENSHOT_NAMES if name not in by_name]
    if missing:
        ui["missingScreenshotNames"] = missing
    if rejected:
        ui["rejectedAttachmentCount"] = rejected
    target_directory = SAFE_ROOT / "screenshots" / METHOD
    stage_directory = SAFE_ROOT / ".screenshot-stage"
    try:
        sources: list[tuple[int, Path]] = []
        for number, logical in enumerate(SCREENSHOT_NAMES, 1):
            source = by_name.get(logical)
            if source is None:
                continue
            if (source.is_symlink() or not source.is_file() or not source.resolve().is_relative_to(export_directory.resolve()) or source.stat().st_size > rt.LIVE_ARTIFACT_MAX_BYTES or not rt._valid_png(source)):
                missing.append(logical)
                ui["missingScreenshotNames"] = missing
                rejected += 1
                ui["rejectedAttachmentCount"] = rejected
                continue
            sources.append((number, source))
        if not sources:
            ui["screenshotStatus"] = "attachment-missing"
            return
        if target_directory.exists() or target_directory.is_symlink() or stage_directory.exists() or stage_directory.is_symlink():
            ui["screenshotStatus"] = "attachment-invalid"
            return
        target_directory.parent.mkdir(parents=True, exist_ok=False)
        stage_directory.mkdir(parents=True, exist_ok=False)
        for number, source in sources:
            shutil.copyfile(source, stage_directory / f"{number:02d}.png")
        os.replace(stage_directory, target_directory)
        ui["screenshots"] = [
            (target_directory / f"{number:02d}.png").relative_to(SAFE_ROOT).as_posix()
            for number, _ in sources
        ]
    except OSError:
        ui["screenshotStatus"] = "attachment-invalid"
        return
    ui["screenshotStatus"] = "available" if not missing and not rejected else "partial"


def publish(report: dict) -> None:
    content = json.dumps(report, indent=2, sort_keys=True)
    (SAFE_ROOT / "diagnostic.json").write_text(content + "\n", encoding="utf-8")
    print(content, flush=True)


def main() -> int:
    # Do not publish exception values, environment values, raw bundles, or raw logs.
    try:
        commit = context()
        rt._live_artifact_root(ROOT)
        rt._live_artifact_root(SAFE_ROOT)
    except (OSError, ValueError):
        print("diagnostic setup rejected; no test started", flush=True)
        return 1
    report: dict[str, object] = {
        "scope": "one-light-release-copy-control-diagnostic",
        "workflow": WORKFLOW,
        "device": rt.IOS_CORE_DEVICE,
        "appearance": "light",
        "releaseEvidence": False,
        "diagnosticStatus": "started",
        "intentionalNonZeroExit": True,
        "commit": commit,
        "results": {},
    }
    build_id = _build_id()
    if build_id is not None:
        report["buildId"] = build_id
    publish(report)
    try:
        destination = rt.resolve_ios_destinations((rt.IOS_CORE_DEVICE,))[rt.IOS_CORE_DEVICE]
    except (OSError, ValueError, rt.SimulatorResolutionError):
        report["diagnosticStatus"] = "setup-failed"
        report["results"] = {"ui": {"status": "simulator-resolution-failed"}}
        publish(report)
        return 1
    identifier = _simulator_identifier(destination)
    if identifier is None:
        report["diagnosticStatus"] = "setup-failed"
        report["results"] = {"ui": {"status": "simulator-identifier-unavailable"}}
        publish(report)
        return 1
    simulator_probes = {"beforeTest": settings_probes(identifier, "beforeTest")}
    report["results"] = {"simulatorProbes": simulator_probes}
    publish(report)
    bundle = ROOT / "ui.xcresult"
    ui_log = ROOT / "ui.log"
    ui: dict[str, object] = run(
        ["xcodebuild", "test", "-project", "ACEClientApp.xcodeproj", "-scheme", "ACEClientAppUITests", "-configuration", "Debug", "-destination", destination, f"-only-testing:{METHOD_PATH}", "-resultBundlePath", str(bundle), "ACE_UI_TEST_APPEARANCE=light"],
        DIAGNOSTIC_TEST_ENVIRONMENT, ui_log, 420,
    )
    ui.update({"commandKind": "xcodebuild-test", "selector": METHOD, "device": rt.IOS_CORE_DEVICE, "appearance": "light", "errors": errors(ui_log)})
    issues, issue_status = accessibility_issues(ui_log)
    ui["accessibilityIssues"] = issues
    if issue_status is not None:
        ui["accessibilityIssueStatus"] = issue_status
    report["results"] = {"simulatorProbes": simulator_probes, "ui": ui}
    # Publish the test result before post-test probes, summary, or attachment export starts.
    publish(report)
    simulator_probes["afterTest"] = settings_probes(identifier, "afterTest")
    report["results"] = {"simulatorProbes": simulator_probes, "ui": ui}
    publish(report)
    collect_summary(ui, bundle)
    publish(report)
    retain_screenshots(ui, bundle)
    report["diagnosticStatus"] = "completed-not-release-evidence"
    publish(report)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
