#!/usr/bin/env python3
"""One manual G0 diagnostic: one UI selector and one negative build. Not evidence."""
from __future__ import annotations

import json
import os
from pathlib import Path
import re
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
METHOD = "testLaunchShowsSafeConfigurationState"


def redact(text: str) -> str:
    # These subprocesses receive only operating values and fictional test inputs.
    # Still remove host environment values, paths, addresses and credential forms.
    for value in sorted(set(os.environ.values()), key=len, reverse=True):
        if len(value) >= 8:
            text = text.replace(value, "[redacted]")
    text = re.sub(r"(?i)(?:https?|ssh)://\S+", "[url]", text)
    text = re.sub(r"\b[^\s@]+@[^\s@]+\b", "[address]", text)
    text = re.sub(r"/(?:Users|private|var|Volumes|Applications)/[^\s:]+", "[path]", text)
    text = re.sub(r"(?i)(password|token|authorization|credential|secret)\s*[:=].*", r"\1=[redacted]", text)
    text = re.sub(r"\b(?:gh[pousr]_[A-Za-z0-9_]+|github_pat_[A-Za-z0-9_]+|sk-[A-Za-z0-9_-]+)\b", "[redacted]", text)
    return "".join(c for c in text if c.isprintable() or c == "\n")[:2000]


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
        if len(selected) == 30:
            break
    return selected or ["no matching error lines; cause unknown"]


def run(command: list[str], environment: dict[str, str], log: Path, timeout: int) -> dict:
    with log.open("w", encoding="utf-8") as stream:
        try:
            process = subprocess.Popen(command, cwd=rt.ROOT / "ios/ACEClientApp",
                env=rt._live_command_environment(environment), stdout=stream,
                stderr=subprocess.STDOUT, start_new_session=True)
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
    if (sys.platform != "darwin"
        or os.environ.get(rt.LIVE_WORKFLOW_ENVIRONMENT_KEY) != WORKFLOW
        or os.environ.get("CM_COMMIT") != expected
        or os.environ.get("CM_BRANCH") != rt.LIVE_BRANCH
        or os.environ.get("CM_TRIGGER_SOURCE") != "api"
        or not os.environ.get("CM_BUILD_ID")
        or not os.environ.get("CM_BUILD_STARTED_BY")
        or Path(os.environ.get("CM_BUILD_DIR", "")).resolve() != rt.ROOT.resolve()):
        raise ValueError("diagnostic context rejected")
    rt._live_repository_metadata(expected)
    return expected


def publish(report: dict) -> None:
    content = json.dumps(report, indent=2, sort_keys=True)
    (SAFE_ROOT / "diagnostic.json").write_text(content + "\n", encoding="utf-8")
    print(content, flush=True)


def main() -> int:
    # Do not publish exception values, environment values, or raw result bundles.
    try:
        commit = context()
        rt._live_artifact_root(ROOT)
        rt._live_artifact_root(SAFE_ROOT)
    except (OSError, ValueError):
        print("diagnostic setup rejected; no test started", flush=True)
        return 1
    report = {"scope": "one-ui-and-negative-diagnostic", "releaseEvidence": False,
              "commit": commit, "results": {}}
    publish(report)
    # Negative first: retain its error even if simulator setup or UI execution fails.
    negative_log = ROOT / "negative.log"
    negative = run(["xcodebuild", "build", "-project", "ACEClientApp.xcodeproj",
        "-scheme", "ACEClientApp", *(f"{k}={v}" for k, v in rt.NEGATIVE_CONFIG_ENVIRONMENT.items())],
        rt.NEGATIVE_CONFIG_ENVIRONMENT, negative_log, 120)
    negative["errors"] = errors(negative_log)
    negative["requiredRejectionFound"] = (
        negative_log.is_file() and negative_log.stat().st_size <= 16 * 1024 * 1024
        and rt.NEGATIVE_CONFIG_REJECTION in negative_log.read_text(encoding="utf-8", errors="replace"))
    report["results"]["negative"] = negative
    publish(report)
    try:
        destination = rt.resolve_ios_destinations((rt.IOS_CORE_DEVICE,))[rt.IOS_CORE_DEVICE]
    except (OSError, ValueError, rt.SimulatorResolutionError):
        report["results"]["ui"] = {"status": "simulator-resolution-failed"}
        publish(report)
        return 1
    bundle = ROOT / "ui.xcresult"
    ui_log = ROOT / "ui.log"
    ui = run(["xcodebuild", "test", "-project", "ACEClientApp.xcodeproj",
        "-scheme", "ACEClientAppUITests", "-configuration", "Debug",
        "-destination", destination,
        f"-only-testing:ACEClientAppUITests/ACEClientAppUITests/{METHOD}",
        "-resultBundlePath", str(bundle), "ACE_UI_TEST_APPEARANCE=light"],
        rt.ios_test_environment("light"), ui_log, 360)
    ui["selector"] = METHOD
    ui["errors"] = errors(ui_log)
    report["results"]["ui"] = ui
    publish(report)
    # Save test failure messages as well as console error lines, without raw JSON.
    if bundle.is_dir():
        summary = ROOT / "summary.json"
        summary_run = run(["xcrun", "xcresulttool", "get", "test-results", "summary",
            "--path", str(bundle)], {}, summary, 30)
        if summary_run.get("processExit") == 0 and summary.stat().st_size <= 1024 * 1024:
            try:
                payload = json.loads(summary.read_text(encoding="utf-8"))
                ui["counts"] = rt._xcresult_counts(payload)
                # The summary's failure records contain the assertion/launch text.
                failures = payload.get("testFailures", []) if isinstance(payload, dict) else []
                ui["testFailureDetails"] = redact(json.dumps(failures)[:16000])
            except (ValueError, RecursionError):
                ui["summary"] = "unreadable"
        else:
            ui["summary"] = "unavailable"
    publish(report)
    # This diagnostic must never be mistaken for successful release evidence.
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
