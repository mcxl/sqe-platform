#!/Library/Frameworks/Python.framework/Versions/3.14/bin/python3
"""Bounded external launcher for the approved D2 Copy reflow diagnostic."""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import importlib.util
import json
import os
import plistlib
import re
import signal
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

ROOT = Path("LOCAL_HOME/ace-private/mcx19b-orientation-repair-20260915/14-copy-reflow-check-20260917")
TARGET = "2EB0863C-470E-467D-A0C6-CD216DA70C67"
METHOD = "ACEClientAppUITests/testCopyReflowCheck()"
SELECTOR = "ACEClientAppUITests/ACEClientAppUITests/testCopyReflowCheck"
NAMES = ("01-harness-failure", "02-harness-pass", "03-arm-X", "04-arm-Y")
MARKERS = ("ACE_D2_CALL_STARTED", "ACE_D2_CALL", "ACE_D2_STOP", "ACE_A11Y_ISSUE")


def now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def die(message: str) -> None:
    raise SystemExit(message)


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def load_runner(record: dict[str, Any]) -> Any:
    candidates = [record.get("runnerPath"), record.get("aceIosLocalPath")]
    root = record.get("worktree") or record.get("candidateRoot") or record.get("repository")
    if isinstance(root, str):
        candidates.append(str(Path(root) / "tools/ace_ios_local.py"))
    candidates.append("LOCAL_HOME/Developer/sqe-platform-r5-diagnostic/tools/ace_ios_local.py")
    path = next((Path(value) for value in candidates if isinstance(value, str) and Path(value).is_file()), None)
    if path is None:
        die("build record does not identify an existing ace_ios_local.py")
    spec = importlib.util.spec_from_file_location("ace_ios_local_d2", path)
    if spec is None or spec.loader is None:
        die("cannot import ace_ios_local.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def directory_hash(runner: Any, path: Path) -> str:
    return str(runner.directory_hash(path))


def path_hash(runner: Any, path: Path) -> str:
    return directory_hash(runner, path) if path.is_dir() else sha256(path)


def check_build(record_path: Path, runner: Any) -> dict[str, Any]:
    record = read_json(record_path)
    if not isinstance(record, dict):
        die("build record must be a JSON object")
    template_value = record.get("template") or record.get("xctestrun") or record.get("templatePath")
    app_value = record.get("applicationBundle") or record.get("app") or record.get("appBundle")
    if not isinstance(template_value, str) or not isinstance(app_value, str):
        die("build record needs template and applicationBundle")
    template, app = Path(template_value), Path(app_value)
    if not template.is_file() or not app.is_dir():
        die("build record template or app bundle is missing")
    expected_template = record.get("templateSha256") or record.get("xctestrunSha256") or record.get("identity")
    expected_app = record.get("applicationBundleSha256") or record.get("appBundleSha256") or record.get("appSha256")
    if isinstance(expected_template, str) and path_hash(runner, template) != expected_template:
        die("xctestrun hash differs from build record")
    if isinstance(expected_app, str) and path_hash(runner, app) != expected_app:
        die("application bundle hash differs from build record")
    source_hashes = record.get("sourceHashes")
    if not isinstance(source_hashes, dict) and isinstance(record.get("candidate"), dict):
        source_hashes = record["candidate"].get("sourceHashes")
    checked_sources: dict[str, str] = {}
    if isinstance(source_hashes, dict):
        for value, expected in source_hashes.items():
            if not isinstance(value, str) or not isinstance(expected, str):
                die("invalid source hash record")
            path = Path(value)
            if not path.is_absolute():
                root = record.get("worktree") or record.get("candidateRoot") or record.get("repository")
                if not isinstance(root, str):
                    die("relative source hash has no worktree")
                path = Path(root) / value
            if not path.is_file() or sha256(path) != expected:
                die(f"source hash differs: {value}")
            checked_sources[value] = expected
    target = record.get("testSourceSha256")
    if isinstance(target, str):
        target_paths = [Path(value) for value in record.get("testSourcePaths", []) if isinstance(value, str)]
        if not target_paths and isinstance(record.get("worktree"), str):
            target_paths = [Path(record["worktree"]) / "ios/ACEClientApp/ACEClientAppUITests/ACEClientAppUITests.swift"]
        if target_paths and (not target_paths[0].is_file() or sha256(target_paths[0]) != target):
            die("temporary test source hash differs from build record")
    return {
        "recordPath": str(record_path),
        "template": str(template),
        "templateSha256": path_hash(runner, template),
        "applicationBundle": str(app),
        "applicationBundleSha256": path_hash(runner, app),
        "sourceHashes": checked_sources,
        "patchSha256": record.get("patchSha256"),
        "candidate": record.get("candidate") or record.get("commit"),
        "runnerPath": str(Path(runner.__file__).resolve()),
    }


def run_command(command: list[str], log: Path | None = None, timeout: int = 60) -> dict[str, Any]:
    started = time.monotonic()
    started_at = now()
    try:
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                   text=True, start_new_session=True)
    except OSError as error:
        result = {"command": command, "start": started_at, "end": now(), "exit": None,
                  "timedOut": False, "error": str(error)}
        if log is not None:
            log.write_text(str(error) + "\n", encoding="utf-8")
        return result
    output = ""
    timed_out = False
    try:
        output, _ = process.communicate(timeout=timeout)
    except subprocess.TimeoutExpired as error:
        timed_out = True
        try:
            os.killpg(process.pid, signal.SIGKILL)
        finally:
            output, _ = process.communicate()
    result = {"command": command, "start": started_at, "end": now(), "output": output,
              "exit": None if timed_out else process.returncode, "timedOut": timed_out,
              "seconds": round(time.monotonic() - started, 3)}
    if log is not None:
        log.write_text(output, encoding="utf-8", errors="replace")
    return result


def command_json(command: list[str], timeout: int = 60) -> tuple[dict[str, Any], Any]:
    result = run_command(command, timeout=timeout)
    if result.get("exit") != 0 or result.get("timedOut"):
        return result, None
    try:
        return result, json.loads(str(result.get("output", "")))
    except json.JSONDecodeError:
        return result, None


def devices() -> dict[str, str]:
    result = run_command(["xcrun", "simctl", "list", "devices", "--json"], timeout=30)
    if result.get("exit") != 0:
        die("simctl device listing failed")
    try:
        payload = json.loads(result.get("output", ""))
    except json.JSONDecodeError:
        die("simctl device listing was not JSON")
    return {item["udid"]: item["state"] for group in payload.get("devices", {}).values()
            for item in group if isinstance(item, dict) and "udid" in item and "state" in item}


def setting(identifier: str, name: str) -> str:
    result = run_command(["xcrun", "simctl", "ui", identifier, name], timeout=30)
    if result.get("exit") != 0:
        die(f"simctl setting query failed: {name}")
    value = str(result.get("output", "")).strip().lower()
    if not value:
        die(f"simctl setting query was empty: {name}")
    return value


def json_markers(log: Path) -> tuple[list[dict[str, Any]], list[str]]:
    calls: list[dict[str, Any]] = []
    raw: list[str] = []
    current: dict[str, Any] | None = None
    for line in log.read_text(encoding="utf-8", errors="replace").splitlines():
        for marker in MARKERS:
            prefix = marker + " "
            if prefix not in line:
                continue
            text = line.split(prefix, 1)[1]
            raw.append(line)
            try:
                value = json.loads(text)
            except json.JSONDecodeError:
                continue
            if not isinstance(value, dict):
                continue
            if marker == "ACE_D2_CALL_STARTED":
                current = {"callNumber": value.get("callNumber", value.get("call", value.get("n"))),
                           "issues": [], "rawIssueLines": []}
            elif marker == "ACE_A11Y_ISSUE" and current is not None:
                current["issues"].append(value)
                current["rawIssueLines"].append(line)
            elif marker == "ACE_D2_CALL":
                item = dict(value)
                number = item.get("callNumber", item.get("call", item.get("n")))
                if number == 0 or str(number) == "0":
                    item.setdefault("issues", None)
                    item.setdefault("issueCount", None)
                    item["issueSourceMarker"] = "ACE_A11Y_ISSUE"
                    item["resolvedIssues"] = list(current["issues"] if current and str(current.get("callNumber")) == "0" else [])
                    item["resolvedIssueCount"] = len(item["resolvedIssues"])
                    item.setdefault("helperReturned", value.get("helperReturned"))
                    item.setdefault("nativeFailureCountDelta", value.get("nativeFailureCountDelta"))
                    item["rawIssueLines"] = list(current.get("rawIssueLines", []) if current else [])
                else:
                    item["resolvedIssues"] = item.get("issues") if isinstance(item.get("issues"), list) else []
                calls.append(item)
                current = None
            break
    return calls, raw


def run_capture(command: list[str], timeout: int = 300) -> tuple[dict[str, Any], str]:
    started = time.monotonic(); started_at = now()
    try:
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                   text=True, start_new_session=True)
        try:
            output, _ = process.communicate(timeout=timeout)
            timed = False
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGKILL); output, _ = process.communicate(); timed = True
        return ({"command": command, "start": started_at, "end": now(), "exit": None if timed else process.returncode,
                 "timedOut": timed, "seconds": round(time.monotonic() - started, 3)}, output)
    except OSError as error:
        return ({"command": command, "start": started_at, "end": now(), "exit": None, "timedOut": False,
                 "error": str(error)}, "")


def gate_file(previous: str) -> Path | None:
    names = (f"gate-{previous}.json", f"{previous}-gate.json", f"{previous}.gate.json",
             f"{previous}-manual-gate.json")
    for base in (ROOT, ROOT / "gates"):
        for name in names:
            candidate = base / name
            if candidate.is_file():
                try:
                    value = read_json(candidate)
                except (OSError, json.JSONDecodeError):
                    continue
                execution = ROOT / previous / "execution.json"
                expected_hash = sha256(execution) if execution.is_file() else None
                bound_hash = value.get("executionJsonSha256") or value.get("executionSha256")
                if (isinstance(value, dict) and value.get("execution") == previous
                        and value.get("approved") is True
                        and value.get("mechanicalGateSuccess") is True
                        and bound_hash == expected_hash):
                    return candidate
    return None


def require_ledger(name: str) -> None:
    index = NAMES.index(name)
    for prior in NAMES[:index]:
        path = ROOT / prior
        if not path.is_dir() or not (path / "execution.json").is_file():
            die(f"previous execution is incomplete: {prior}")
        record = read_json(path / "execution.json")
        if record.get("status") != "completed" or record.get("mechanicalGateSuccess") is not True:
            die(f"previous execution is not completed: {prior}")
        if prior == NAMES[0]:
            _require_harness_record(record, "FAIL")
        if prior == NAMES[1]:
            _require_harness_record(record, "PASS")
        if index >= 2 and prior == NAMES[index - 1] and gate_file(prior) is None:
            die(f"manual gate approval is missing for {prior}")


def _failure_texts(value: Any) -> list[str]:
    found: list[str] = []
    if isinstance(value, dict):
        if isinstance(value.get("failureText"), str):
            found.append(value["failureText"])
        for child in value.values():
            found.extend(_failure_texts(child))
    elif isinstance(value, list):
        for child in value:
            found.extend(_failure_texts(child))
    return found


def _require_harness_record(record: dict[str, Any], expected: str) -> None:
    if record.get("nativeOutcome") != expected or record.get("callCount") != 3:
        die(f"{record.get('execution')} does not satisfy the {expected} harness gate")
    payload = (record.get("summary") or {}).get("payload")
    if not isinstance(payload, dict):
        die("harness summary is missing")
    if expected == "FAIL":
        if payload.get("result") != "Failed" or record.get("native", {}).get("exit") != 65:
            die("deliberate harness failure did not remain a native failure")
        failures = _failure_texts(payload)
        if failures != ["D2 deliberate harness failure"]:
            die("deliberate harness failure has an unexpected native failure list")
    else:
        if payload.get("result") != "Passed" or record.get("native", {}).get("exit") != 0:
            die("corrected harness execution did not pass natively")
        if _failure_texts(payload):
            die("corrected harness execution has native failures")
    for call in record.get("calls", []):
        issues = call.get("resolvedIssues")
        if issues or (isinstance(call.get("issues"), list) and call.get("issues")) or call.get("error"):
            die("harness execution contains an audit issue or thrown error")


def restore(identifier: str, initial_states: dict[str, str], original_settings: dict[str, str], record: dict[str, Any]) -> None:
    actions: list[dict[str, Any]] = []
    for name, value in original_settings.items():
        action = run_command(["xcrun", "simctl", "ui", identifier, name, value], timeout=60)
        action.pop("output", None)
        actions.append(action)
    readback: dict[str, str] = {}
    readback_error: str | None = None
    try:
        readback = {name: setting(identifier, name) for name in original_settings}
    except BaseException as error:
        readback_error = str(error)
    settings_exact = readback_error is None and readback == original_settings
    try:
        current = devices().get(identifier)
        if settings_exact and initial_states.get(identifier) == "Shutdown" and current == "Booted":
            action = run_command(["xcrun", "simctl", "shutdown", identifier], timeout=120)
            action.pop("output", None)
            actions.append(action)
    finally:
        final_states = devices()
        record["restoration"] = {"actions": actions, "readback": readback, "readbackError": readback_error,
                                  "settingsReadbackExact": settings_exact,
                                  "allActionExit0": all(item.get("exit") == 0 and not item.get("timedOut") for item in actions),
                                  "finalBootStates": final_states,
                                  "bootStatesMatch": final_states == initial_states,
                                  "otherBootStatesUntouched": all(final_states.get(k) == v for k, v in initial_states.items() if k != identifier)}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("execution", choices=NAMES)
    parser.add_argument("arm", choices=("X", "Y"))
    parser.add_argument("max_calls", type=int)
    parser.add_argument("--force-fail", action="store_true")
    parser.add_argument("--build-record", required=True, type=Path)
    args = parser.parse_args()
    expected_calls = 2 if args.execution.startswith("0") and args.execution.endswith(("failure", "pass")) else 30
    if args.max_calls != expected_calls:
        die(f"{args.execution} requires max_calls={expected_calls}")
    if args.force_fail != (args.execution == NAMES[0]):
        die("--force-fail is allowed only for 01-harness-failure")
    ROOT.mkdir(parents=True, exist_ok=True)
    target_dir = ROOT / args.execution
    if target_dir.exists():
        die(f"execution directory already exists: {target_dir}")
    require_ledger(args.execution)
    runner_record = read_json(args.build_record)
    runner = load_runner(runner_record)
    build = check_build(args.build_record, runner)
    target_dir.mkdir()
    record: dict[str, Any] = {"status": "running", "execution": args.execution, "arm": args.arm,
                              "maxCalls": args.max_calls, "forceFail": args.force_fail, "method": METHOD,
                              "selector": SELECTOR, "build": build, "startedUTC": now()}
    write_json(target_dir / "execution.json", record)
    initial_states: dict[str, str] = {}
    original_settings: dict[str, str] = {}
    failed = False
    try:
        active = subprocess.run(["pgrep", "-x", "xcodebuild"], capture_output=True, text=True)
        if active.stdout.strip():
            die("xcodebuild is already active")
        initial_states = devices(); record["initialBootStates"] = initial_states
        if TARGET not in initial_states:
            die("target simulator is unavailable")
        original_settings = {name: setting(TARGET, name) for name in ("appearance", "content_size", "increase_contrast")}
        record["originalSimctlSettings"] = original_settings
        write_json(target_dir / "execution.json", record)
        if initial_states[TARGET] == "Shutdown":
            boot = run_command(["xcrun", "simctl", "boot", TARGET], timeout=120)
            bootstatus = run_command(["xcrun", "simctl", "bootstatus", TARGET, "-b"], timeout=300)
            record["boot"] = {"boot": boot, "bootstatus": bootstatus}
            if boot.get("exit") != 0 or bootstatus.get("exit") != 0:
                die("target simulator failed to boot")
        runfile = target_dir / "ACEClientAppUITests.xctestrun"
        env = {"ACE_D2_ARM": args.arm, "ACE_D2_MAX_CALLS": str(args.max_calls)}
        if args.force_fail:
            env["ACE_D2_FORCE_FAIL"] = "1"
        runner.configure_xctestrun(Path(build["template"]), runfile, env)
        payload = plistlib.loads(runfile.read_bytes())
        actual_env = payload["ACEClientAppUITests"].get("EnvironmentVariables", {})
        if any(actual_env.get(k) != v for k, v in env.items()):
            die("xctestrun environment injection mismatch")
        record["xctestrun"] = {"path": str(runfile), "sha256": sha256(runfile), "environment": env}
        write_json(target_dir / "execution.json", record)
        result_bundle = target_dir / "result.xcresult"
        command = ["xcodebuild", "test-without-building", "-xctestrun", str(runfile), "-destination", f"id={TARGET}",
                   "-parallel-testing-enabled", "NO", f"-only-testing:{SELECTOR}", "-resultBundlePath", str(result_bundle)]
        native_log = target_dir / "native.log"
        native = run_command(command, native_log, timeout=900)
        native["resultBundle"] = str(result_bundle)
        write_native = dict(native)
        write_native.pop("output", None)
        write_json(target_dir / "native-command.json", write_native)
        record["native"] = {key: value for key, value in native.items() if key != "output"}
        calls, raw_markers = json_markers(native_log)
        record["rawMarkerLines"] = raw_markers
        record["calls"] = calls
        record["callCount"] = len(calls)
        summary_cmd, summary_text = run_capture(["xcrun", "xcresulttool", "get", "test-results", "summary", "--path", str(result_bundle)])
        summary = None
        try: summary = json.loads(summary_text)
        except json.JSONDecodeError: pass
        write_json(target_dir / "native-summary.json", summary if summary is not None else {"raw": summary_text, "command": summary_cmd})
        tests_cmd, tests_text = run_capture(["xcrun", "xcresulttool", "get", "test-results", "tests", "--path", str(result_bundle)])
        tests = None
        try: tests = json.loads(tests_text)
        except json.JSONDecodeError: pass
        write_json(target_dir / "native-tests.json", tests if tests is not None else {"raw": tests_text, "command": tests_cmd})
        leaves: list[dict[str, Any]] = []
        def walk(value: Any) -> None:
            if isinstance(value, dict):
                if value.get("nodeType") == "Test Case": leaves.append(value)
                for child in value.values(): walk(child)
            elif isinstance(value, list):
                for child in value: walk(child)
        walk(tests)
        record["summary"] = {"command": summary_cmd, "payload": summary}
        record["methodProof"] = {"command": tests_cmd, "method": METHOD,
                                  "matchingLeaves": [x for x in leaves if x.get("nodeIdentifier") == METHOD],
                                  "testCaseCount": len(leaves), "exactlyOne": len(leaves) == 1 and sum(x.get("nodeIdentifier") == METHOD for x in leaves) == 1}
        attachments = target_dir / "attachments"
        attach_cmd, _ = run_capture(["xcrun", "xcresulttool", "export", "attachments", "--path", str(result_bundle), "--output-path", str(attachments)])
        manifest = attachments / "manifest.json"
        manifest_entries: Any = None
        if manifest.is_file():
            try:
                manifest_entries = read_json(manifest)
            except (OSError, json.JSONDecodeError):
                manifest_entries = None
        manifest_method_count = sum(1 for item in manifest_entries or []
                                    if isinstance(item, dict) and item.get("testIdentifier") == METHOD)
        record["attachments"] = {"command": attach_cmd, "path": str(attachments), "manifest": str(manifest),
                                  "manifestMethodCount": manifest_method_count,
                                  "manifestExactMethod": manifest_method_count == 1}
        record["resultBundle"] = {"path": str(result_bundle), "exists": result_bundle.is_dir()}
        record["nativeOutcome"] = "PASS" if isinstance(summary, dict) and summary.get("result") == "Passed" else "FAIL"
        call0 = calls[0] if calls and str(calls[0].get("callNumber", calls[0].get("call", ""))) == "0" else None
        if call0 is not None:
            for key in ("error", "auditError", "thrownError", "auditErrorText"):
                if isinstance(call0.get(key), str) and call0[key]:
                    record["call0Error"] = call0[key]
                    break
        record["mechanicalGateSuccess"] = method_proof_ok = bool(record["methodProof"]["exactlyOne"] and
                                                                   result_bundle.is_dir() and len(calls) == args.max_calls + 1 and
                                                                   record["attachments"].get("manifestExactMethod") is True)
        if args.execution in NAMES[:2]:
            expected_result = "Failed" if args.execution == NAMES[0] else "Passed"
            failures = _failure_texts(summary)
            clean_calls = all(not call.get("resolvedIssues") and not call.get("error") for call in calls)
            if args.execution == NAMES[0]:
                method_proof_ok = (native.get("exit") == 65 and isinstance(summary, dict) and summary.get("result") == expected_result
                                   and failures == ["D2 deliberate harness failure"] and clean_calls)
            else:
                method_proof_ok = (native.get("exit") == 0 and isinstance(summary, dict) and summary.get("result") == expected_result
                                   and not failures and clean_calls)
            record["mechanicalGateSuccess"] = bool(method_proof_ok and record["methodProof"]["exactlyOne"] and
                                                    record["attachments"].get("manifestExactMethod") is True)
        record["status"] = "completed"
    except BaseException as error:
        failed = True
        record["status"] = "blocked"
        record["mechanicalGateSuccess"] = False
        record["launcherError"] = str(error)
    finally:
        if initial_states and original_settings:
            try: restore(TARGET, initial_states, original_settings, record)
            except Exception as error: record["restorationError"] = str(error)
        if record.get("restoration", {}).get("bootStatesMatch") is not True:
            failed = True
        if record.get("restoration", {}).get("settingsReadbackExact") is not True:
            failed = True
        if record.get("restoration", {}).get("allActionExit0") is not True:
            failed = True
        if failed:
            record["status"] = "blocked"
            record["mechanicalGateSuccess"] = False
        write_json(target_dir / "execution.json", record)
    if failed:
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
