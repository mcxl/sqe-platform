#!/usr/bin/env python3
"""Run dependency-free SQE component checks without installing software."""
from __future__ import annotations

import argparse
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORT_DIR = ROOT / ".artifacts" / "tests"
CONFIG = ROOT / "quality" / "test-groups.json"
IOS_TEST_ENVIRONMENT = {
    "ACE_PREVIEW_ORIGIN": "https://preview.example.invalid",
    "ACE_BUNDLE_IDENTIFIER": "com.example.aceclientapp",
}
NEGATIVE_CONFIG_ENVIRONMENT = {
    "ACE_PREVIEW_ORIGIN": "http://invalid.example.invalid",
    "ACE_BUNDLE_IDENTIFIER": "com.example.aceclientapp",
}
NEGATIVE_CONFIG_REJECTION = "ACE_PREVIEW_ORIGIN must be an approved HTTPS origin"
EVIDENCE_RESULT_FIELDS = (
    "repository",
    "commit",
    "device",
    "software",
    "operator",
    "date",
    "result",
    "artifact",
    "reviewer",
)
IOS_RUNTIME_MAJOR = 26
SIMULATOR_POLL_ATTEMPTS = 3
SIMULATOR_POLL_INTERVAL_SECONDS = 1
IOS_CORE_DEVICE = "iPhone SE (3rd generation)"
IOS_RELEASE_DEVICES = (IOS_CORE_DEVICE, "iPhone 16 Pro Max")
SIMULATOR_UUID = re.compile(
    r"^[0-9A-Fa-f]{8}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{12}$"
)


class SimulatorResolutionError(ValueError):
    """Raised when a required iOS simulator cannot be safely resolved."""


def load_mapping() -> tuple[dict, list[str]]:
    data = json.loads(CONFIG.read_text(encoding="utf-8"))
    errors: list[str] = []
    groups = data.get("groups", {})
    if set(groups) != {"G1", "G2", "G3", "G4", "G5", "G6"}:
        errors.append("exactly G1 through G6 are required")
    source = ROOT / data.get("iosRuntimeRequirementSource", "")
    try:
        plan = json.loads(source.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        return data, [f"runtime requirement source is unavailable: {error}"]
    source_ids = [identifier for entry in plan.get("entries", []) for identifier in entry.get("identifiers", [])]
    mapping = data.get("iosPrimaryGroups", {})
    mapping_ids = [identifier for group in mapping.values() for identifier in group]
    duplicates = sorted({item for item in mapping_ids if mapping_ids.count(item) > 1})
    source_duplicates = sorted({item for item in source_ids if source_ids.count(item) > 1})
    missing = sorted(set(source_ids) - set(mapping_ids))
    unknown = sorted(set(mapping_ids) - set(source_ids))
    unused = sorted(set(groups) - {group for group, ids in mapping.items() if ids})
    if len(source_ids) != 44:
        errors.append(f"runtime source must contain 44 identifiers, found {len(source_ids)}")
    if source_duplicates:
        errors.append("duplicate source IDs: " + ", ".join(source_duplicates))
    if duplicates:
        errors.append("duplicate mapped IDs: " + ", ".join(duplicates))
    if missing:
        errors.append("missing mapped IDs: " + ", ".join(missing))
    if unknown:
        errors.append("unknown mapped IDs: " + ", ".join(unknown))
    if unused:
        errors.append("unused groups: " + ", ".join(unused))
    evidence_errors, evidence_state = validate_public_evidence_records(
        source,
        source_ids,
        plan,
    )
    errors.extend(evidence_errors)
    data["evidencePreflightState"] = evidence_state
    return data, errors


def validate_public_evidence_records(
    plan_path: Path,
    source_ids: list[str],
    plan: dict,
) -> tuple[list[str], str]:
    """Validate public record completeness without accepting runtime evidence."""

    errors: list[str] = []
    if plan.get("scope") != "G0-public-planning-only":
        errors.append("runtime plan is outside public G0 scope")
    if plan.get("releaseEvidence") is not False:
        errors.append("runtime plan must not claim release evidence")
    if plan.get("repository") != "mcxl/sqe-platform":
        errors.append("runtime plan repository is not mcxl/sqe-platform")
    controlled = plan.get("controlledRegister")
    if not isinstance(controlled, dict):
        return ["controlled public evidence register is missing"], "invalid"
    register_name = controlled.get("path")
    if not isinstance(register_name, str) or Path(register_name).is_absolute():
        return ["controlled public evidence register path is invalid"], "invalid"
    register_path = (plan_path.parent / register_name).resolve()
    if not register_path.is_relative_to(plan_path.parent.resolve()):
        return ["controlled public evidence register path escapes the runtime plan"], "invalid"
    try:
        register = json.loads(register_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        return [f"controlled public evidence register is unavailable: {error}"], "invalid"
    if register.get("scope") != "G0-public-planning-only":
        errors.append("controlled public evidence register is outside G0 scope")
    if register.get("releaseEvidence") is not False:
        errors.append("controlled public evidence register must not claim release evidence")
    if register.get("repository") != "mcxl/sqe-platform":
        errors.append("controlled public evidence register repository is not mcxl/sqe-platform")
    results = register.get("results")
    if not isinstance(results, dict):
        return ["controlled public evidence results are missing"], "invalid"
    expected_ids = set(source_ids)
    if set(results) != expected_ids:
        errors.append("controlled public evidence result identifiers do not match the runtime plan")
    reviewed = 0
    for identifier in source_ids:
        record = results.get(identifier)
        if not isinstance(record, dict):
            errors.append(f"{identifier}: public evidence record is invalid")
            continue
        status = record.get("status")
        result = record.get("result")
        if status not in {"pending", "reviewed"} or not isinstance(result, dict):
            errors.append(f"{identifier}: public evidence status or result is invalid")
            continue
        values = {field: result.get(field) for field in EVIDENCE_RESULT_FIELDS}
        if status == "pending":
            if any(values.values()):
                errors.append(f"{identifier}: pending public evidence must have blank result fields")
            continue
        reviewed += 1
        if any(not isinstance(value, str) or not value.strip() for value in values.values()):
            errors.append(f"{identifier}: reviewed public evidence is incomplete")
            continue
        if values["repository"] != "mcxl/sqe-platform":
            errors.append(f"{identifier}: reviewed public evidence repository is invalid")
        current_head = subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True,
            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, check=False,
        )
        if current_head.returncode != 0 or values["commit"] != current_head.stdout.strip():
            errors.append(f"{identifier}: reviewed public evidence commit is not the executing Git head")
        artifact = (ROOT / str(values["artifact"])).resolve()
        controlled_root = (ROOT / "ios" / "ACEClientApp" / "build" / "phase6-1").resolve()
        if not artifact.is_relative_to(controlled_root) or not artifact.exists():
            errors.append(f"{identifier}: reviewed public evidence artifact is unavailable")
    if errors:
        return errors, "invalid"
    if reviewed:
        return [], "reviewed-records-present-not-release-evidence"
    return [], "pending-not-release-evidence"


def run_command(
    name: str,
    command: list[str],
    cwd: Path,
    environment: dict[str, str] | None = None,
    expected_failure: str | None = None,
) -> dict:
    if shutil.which(command[0]) is None:
        return {"name": name, "status": "unavailable", "exit": 2, "detail": f"missing tool: {command[0]}"}
    try:
        completed = subprocess.run(
            command,
            cwd=cwd,
            env={**os.environ, **environment} if environment else None,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            check=False,
        )
    except OSError as error:
        return {"name": name, "status": "unavailable", "exit": 2, "detail": str(error)}
    detail = completed.stdout or ""
    if expected_failure is not None:
        passed = completed.returncode != 0 and expected_failure in detail
        return {"name": name, "status": "passed" if passed else "failed", "exit": 0 if passed else 1, "detail": detail[-4000:]}
    return {"name": name, "status": "passed" if completed.returncode == 0 else "failed", "exit": 0 if completed.returncode == 0 else 1, "detail": detail[-4000:]}


def python_toolchain() -> list[str]:
    missing = [name for name in ("pytest", "reportlab", "docx", "lxml") if importlib.util.find_spec(name) is None]
    if not (shutil.which("soffice") or shutil.which("libreoffice")):
        missing.append("LibreOffice")
    return missing


def ui_methods() -> list[str]:
    source = (ROOT / "ios" / "ACEClientApp" / "ACEClientAppUITests" / "ACEClientAppUITests.swift").read_text(encoding="utf-8")
    return [line.split("func ", 1)[1].split("(", 1)[0] for line in source.splitlines() if line.strip().startswith("func test")]


def ios_test_environment(appearance: str | None = None) -> dict[str, str]:
    environment = dict(IOS_TEST_ENVIRONMENT)
    if appearance is not None:
        environment["ACE_UI_TEST_APPEARANCE"] = appearance
    return environment


def _simctl_list() -> dict:
    completed = subprocess.run(
        ["xcrun", "simctl", "list", "-j"],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    if completed.returncode != 0:
        raise SimulatorResolutionError(
            f"simctl list failed: {(completed.stdout or '').strip()}"
        )
    try:
        data = json.loads(completed.stdout)
    except json.JSONDecodeError as error:
        raise SimulatorResolutionError("simctl list returned invalid JSON") from error
    if not isinstance(data, dict):
        raise SimulatorResolutionError("simctl list returned an invalid object")
    return data


def _simctl_create(name: str, device_type: str, runtime: str) -> str:
    completed = subprocess.run(
        ["xcrun", "simctl", "create", name, device_type, runtime],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    if completed.returncode != 0:
        raise SimulatorResolutionError(
            f"simctl create failed for {name}: {(completed.stdout or '').strip()}"
        )
    identifier = (completed.stdout or "").strip()
    if SIMULATOR_UUID.fullmatch(identifier) is None:
        raise SimulatorResolutionError(
            f"simctl create returned an invalid UUID for {name}"
        )
    return identifier.upper()


def _runtime_version(runtime: dict) -> tuple[int, ...] | None:
    identifier = runtime.get("identifier")
    version = runtime.get("version")
    if (
        runtime.get("isAvailable") is not True
        or not isinstance(identifier, str)
        or not identifier.startswith("com.apple.CoreSimulator.SimRuntime.iOS-")
        or not isinstance(version, str)
        or re.fullmatch(r"\d+(?:\.\d+)*", version) is None
    ):
        return None
    parsed = tuple(int(part) for part in version.split("."))
    if parsed[0] != IOS_RUNTIME_MAJOR:
        return None
    return parsed


def _select_ios_runtime(snapshot: dict) -> str:
    runtimes = snapshot.get("runtimes")
    if not isinstance(runtimes, list):
        raise SimulatorResolutionError("simctl runtimes are unavailable")
    candidates = [
        (version, runtime["identifier"])
        for runtime in runtimes
        if isinstance(runtime, dict)
        and (version := _runtime_version(runtime)) is not None
    ]
    if not candidates:
        raise SimulatorResolutionError(
            f"no available iOS {IOS_RUNTIME_MAJOR} runtime exists"
        )
    highest_version = max(version for version, _ in candidates)
    highest = [identifier for version, identifier in candidates if version == highest_version]
    if len(highest) != 1:
        raise SimulatorResolutionError("highest available iOS runtime is ambiguous")
    return highest[0]


def _device_type_identifier(snapshot: dict, name: str) -> str:
    device_types = snapshot.get("devicetypes")
    if not isinstance(device_types, list):
        raise SimulatorResolutionError("simctl device types are unavailable")
    matches = [
        device_type.get("identifier")
        for device_type in device_types
        if isinstance(device_type, dict)
        and device_type.get("name") == name
        and isinstance(device_type.get("identifier"), str)
    ]
    if len(matches) != 1:
        raise SimulatorResolutionError(f"exact device type is unavailable: {name}")
    return matches[0]


def _matching_simulators(
    snapshot: dict,
    runtime: str,
    name: str,
    device_type: str,
) -> list[dict]:
    devices = snapshot.get("devices")
    if not isinstance(devices, dict):
        raise SimulatorResolutionError("simctl devices are unavailable")
    runtime_devices = devices.get(runtime)
    if not isinstance(runtime_devices, list):
        return []
    name_matches = [
        device
        for device in runtime_devices
        if isinstance(device, dict) and device.get("name") == name
    ]
    return [
        device
        for device in name_matches
        if device.get("deviceTypeIdentifier") == device_type
        and device.get("isAvailable") is True
    ]


def _verify_simulator(
    snapshot: dict,
    runtime: str,
    name: str,
    device_type: str,
    identifier: str,
) -> str:
    if SIMULATOR_UUID.fullmatch(identifier) is None:
        raise SimulatorResolutionError(f"simulator UUID is invalid for {name}")
    devices = snapshot.get("devices")
    if not isinstance(devices, dict):
        raise SimulatorResolutionError("simctl devices are unavailable")
    matches = [
        (runtime_id, device)
        for runtime_id, runtime_devices in devices.items()
        if isinstance(runtime_devices, list)
        for device in runtime_devices
        if isinstance(device, dict) and device.get("udid", "").upper() == identifier.upper()
    ]
    if len(matches) != 1:
        raise SimulatorResolutionError(f"simulator UUID is not unique for {name}")
    resolved_runtime, device = matches[0]
    if (
        resolved_runtime != runtime
        or device.get("name") != name
        or device.get("deviceTypeIdentifier") != device_type
        or device.get("isAvailable") is not True
    ):
        raise SimulatorResolutionError(f"simulator identity verification failed for {name}")
    return identifier.upper()


def resolve_ios_destinations(names: tuple[str, ...]) -> dict[str, str]:
    """Resolve or create exact iOS 26 simulator devices before test execution."""

    if len(names) != len(set(names)):
        raise SimulatorResolutionError("required simulator names must be unique")
    snapshot = _simctl_list()
    runtime = _select_ios_runtime(snapshot)
    device_types = {
        name: _device_type_identifier(snapshot, name)
        for name in names
    }
    identifiers: dict[str, str] = {}
    created = False
    for name in names:
        matches = _matching_simulators(snapshot, runtime, name, device_types[name])
        if len(matches) > 1:
            raise SimulatorResolutionError(f"exact simulator is ambiguous: {name}")
        if matches:
            identifier = matches[0].get("udid")
            if not isinstance(identifier, str):
                raise SimulatorResolutionError(f"simulator UUID is missing for {name}")
            identifiers[name] = identifier
        else:
            identifiers[name] = _simctl_create(name, device_types[name], runtime)
            created = True
    if created:
        verification_error: SimulatorResolutionError | None = None
        for attempt in range(SIMULATOR_POLL_ATTEMPTS):
            snapshot = _simctl_list()
            try:
                for name in names:
                    _verify_simulator(snapshot, runtime, name, device_types[name], identifiers[name])
                verification_error = None
                break
            except SimulatorResolutionError as error:
                verification_error = error
                if attempt + 1 < SIMULATOR_POLL_ATTEMPTS:
                    time.sleep(SIMULATOR_POLL_INTERVAL_SECONDS)
        if verification_error is not None:
            raise SimulatorResolutionError(
                f"created simulator did not become available: {verification_error}"
            )
    return {
        name: f"platform=iOS Simulator,id={_verify_simulator(snapshot, runtime, name, device_types[name], identifiers[name])}"
        for name in names
    }


def _xcresult_counts(payload: object) -> tuple[int, int, int] | None:
    """Return passed, failed, and skipped counts from an xcresult summary."""

    candidates: list[tuple[int, int, int]] = []

    def visit(value: object) -> None:
        if isinstance(value, dict):
            passed = value.get("passedTests")
            failed = value.get("failedTests")
            skipped = value.get("skippedTests", 0)
            if all(isinstance(count, int) for count in (passed, failed, skipped)):
                candidates.append((passed, failed, skipped))
            for child in value.values():
                visit(child)
        elif isinstance(value, list):
            for child in value:
                visit(child)

    visit(payload)
    return max(candidates, key=lambda counts: sum(counts), default=None)


def run_ios_test(
    name: str,
    command: list[str],
    cwd: Path,
    environment: dict[str, str],
    expected_tests: int,
) -> dict:
    """Run one iOS test command and fail closed on absent result counts."""

    if shutil.which("xcrun") is None:
        return {
            "name": name,
            "status": "unavailable",
            "exit": 2,
            "detail": "missing tool: xcrun",
        }
    with tempfile.TemporaryDirectory(prefix="ace-xcresult-") as directory:
        result_path = Path(directory) / "result.xcresult"
        result = run_command(
            name,
            [*command, "-resultBundlePath", str(result_path)],
            cwd,
            environment=environment,
        )
        if result["exit"] != 0:
            return result
        summary = run_command(
            f"{name}-xcresult",
            [
                "xcrun",
                "xcresulttool",
                "get",
                "test-results",
                "summary",
                "--path",
                str(result_path),
            ],
            cwd,
        )
    if summary["exit"] != 0:
        return {
            "name": name,
            "status": summary["status"],
            "exit": summary["exit"],
            "detail": f"xcresult summary failed: {summary['detail']}",
        }
    try:
        counts = _xcresult_counts(json.loads(summary["detail"]))
    except json.JSONDecodeError:
        counts = None
    if counts is None:
        return {
            "name": name,
            "status": "failed",
            "exit": 1,
            "detail": "xcresult has no executed-test summary",
        }
    passed, failed, skipped = counts
    if passed != expected_tests or failed != 0 or skipped != 0:
        return {
            "name": name,
            "status": "failed",
            "exit": 1,
            "detail": (
                "xcresult count mismatch: "
                f"expected {expected_tests} passed, passed {passed}, "
                f"failed {failed}, skipped {skipped}"
            ),
        }
    return {
        "name": name,
        "status": "passed",
        "exit": 0,
        "detail": f"xcresult passed {passed} tests with 0 failures and 0 skipped",
    }


def component_checks(level: str, component: str) -> list[dict]:
    if component == "python":
        missing = python_toolchain()
        if missing:
            return [{"name": "python-toolchain", "status": "unavailable", "exit": 2, "detail": "missing required toolchain: " + ", ".join(missing)}]
        return [run_command("python-full", [sys.executable, "-m", "pytest", "-q"], ROOT)]
    if component == "web":
        web = ROOT / "apps" / "relationship-review-pilot"
        if not (web / "node_modules").is_dir():
            return [{"name": "web-dependencies", "status": "unavailable", "exit": 2, "detail": "node_modules is unavailable; runner does not install dependencies"}]
        checks = [run_command("web-unit", ["npm", "test", "--", "--run"], web), run_command("web-typecheck", ["npm", "run", "typecheck"], web), run_command("web-lint", ["npm", "run", "lint"], web)]
        if level == "release": checks.append(run_command("web-build", ["npm", "run", "build"], web))
        return checks
    ios = ROOT / "ios" / "ACEClientApp"
    if shutil.which("xcodebuild") is None:
        return [{"name": "ios-xcode", "status": "unavailable", "exit": 2, "detail": "xcodebuild is unavailable"}]
    methods = ui_methods()
    if len(methods) != 5:
        return [{"name": "ios-matrix", "status": "unavailable", "exit": 2, "detail": f"expected five UI methods, found {len(methods)}"}]
    required_devices = IOS_RELEASE_DEVICES if level == "release" else (IOS_CORE_DEVICE,)
    if shutil.which("xcrun") is None:
        return [{"name": "ios-simulator", "status": "unavailable", "exit": 2, "detail": "missing tool: xcrun"}]
    try:
        destinations = resolve_ios_destinations(required_devices)
    except SimulatorResolutionError as error:
        return [{"name": "ios-simulator", "status": "failed", "exit": 1, "detail": str(error)}]
    destination = destinations[IOS_CORE_DEVICE]
    unit = ["xcodebuild", "test", "-project", "ACEClientApp.xcodeproj", "-scheme", "ACEClientApp", "-destination", destination, "-only-testing:ACEClientAppTests"]
    checks = [{"name": "ios-simulator", "status": "passed", "exit": 0, "detail": "resolved exact simulator UUIDs"}, run_ios_test("ios-65-unit", unit, ios, ios_test_environment(), 65)]
    checks.extend(run_ios_test(f"ios-core-ui-{method}", ["xcodebuild", "test", "-project", "ACEClientApp.xcodeproj", "-scheme", "ACEClientAppUITests", "-configuration", "Debug", "-destination", destination, f"-only-testing:ACEClientAppUITests/ACEClientAppUITests/{method}"], ios, ios_test_environment(), 1) for method in methods)
    if level == "release":
        for device in IOS_RELEASE_DEVICES:
            for appearance in ("light", "dark"):
                for method in methods:
                    checks.append(run_ios_test(f"ios-release-{device}-{appearance}-{method}", ["xcodebuild", "test", "-project", "ACEClientApp.xcodeproj", "-scheme", "ACEClientAppUITests", "-configuration", "Debug", "-destination", destinations[device], "-only-testing:ACEClientAppUITests/ACEClientAppUITests/" + method, f"ACE_UI_TEST_APPEARANCE={appearance}"], ios, ios_test_environment(appearance), 1))
        checks.extend([run_ios_test("ios-evidence-contract", ["xcodebuild", "test", "-project", "ACEClientApp.xcodeproj", "-scheme", "ACEClientApp", "-destination", destination, "-only-testing:ACEClientAppTests/AcceptanceEvidenceContractTests"], ios, ios_test_environment(), 42), run_command("ios-negative-config", ["xcodebuild", "build", "-project", "ACEClientApp.xcodeproj", "-scheme", "ACEClientApp"], ios, environment=NEGATIVE_CONFIG_ENVIRONMENT, expected_failure=NEGATIVE_CONFIG_REJECTION)])
    return checks


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("level", choices=["focused", "core", "release", "evidence-check"])
    parser.add_argument("--component", choices=["python", "web", "ios"])
    args = parser.parse_args(argv)
    data, mapping_errors = load_mapping()
    if args.level != "evidence-check" and not args.component:
        parser.error("--component is required except for evidence-check")
    results = []
    if mapping_errors:
        results.append({"name": "mapping", "status": "failed", "exit": 1, "detail": "; ".join(mapping_errors)})
    elif args.level == "evidence-check":
        results.append({"name": "public-g0-preflight", "status": "passed", "exit": 0, "detail": f"44 source IDs map once to G1-G6; {data['evidencePreflightState']}; manual evidence was not run"})
    else:
        results.extend(component_checks(args.level, args.component))
    exits = {item["exit"] for item in results}
    exit_code = 1 if 1 in exits else 2 if 2 in exits else 0
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    report = {"timestamp": datetime.now(timezone.utc).isoformat(), "level": args.level, "component": args.component, "mapping": data.get("iosPrimaryGroups", {}), "evidencePreflightState": data.get("evidencePreflightState"), "releaseEvidence": False, "results": results, "exit": exit_code}
    report_path = REPORT_DIR / f"{args.level}-{args.component or 'manual'}.json"
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"report={report_path.relative_to(ROOT)}")
    for item in results: print(f"{item['name']}: {item['status']}: {item['detail'].splitlines()[0] if item['detail'] else ''}")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
