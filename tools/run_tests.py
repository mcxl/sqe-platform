#!/usr/bin/env python3
"""Run dependency-free SQE component checks without installing software."""
from __future__ import annotations

import argparse
import hashlib
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
from typing import Callable

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
    "package",
    "entry",
    "device",
    "software",
    "operator",
    "date",
    "result",
    "artifact",
    "reviewer",
)
ACTIVE_RECORD_REVIEWED_FIELDS = (
    "repository",
    "commit",
    "package",
    "entry",
    "device",
    "software",
    "operator",
    "date",
    "result",
    "artifact",
    "reviewer",
    "status",
)
PLAN_FIELDS = frozenset(
    {
        "scope",
        "releaseEvidence",
        "status",
        "activeRecordRequirements",
        "resultFieldSchema",
        "controlledRegister",
        "entries",
        "packageMappings",
        "repository",
    }
)
REGISTER_FIELDS = frozenset(
    {
        "scope",
        "releaseEvidence",
        "status",
        "activeRecordRequirements",
        "resultFieldSchema",
        "workflow",
        "simulatorProvisioning",
        "packages",
        "results",
        "repository",
    }
)
ACTIVE_RECORD_REQUIREMENT_FIELDS = frozenset(
    {"repository", "commit", "status", "reviewedRecordFields"}
)
CONTROLLED_REGISTER_FIELDS = frozenset(
    {"path", "workflow", "status", "simulatorProvisioning", "historicalCommitChain"}
)
HISTORICAL_COMMIT_CHAIN_FIELDS = frozenset({"status", "note"})
SIMULATOR_PROVISIONING_FIELDS = frozenset(
    {"status", "exactTargets", "runtime", "procedure", "failure"}
)
PLAN_ENTRY_FIELDS = frozenset(
    {"identifiers", "stage", "device", "procedure", "expectedResult", "status"}
)
PACKAGE_MAPPING_FIELDS = frozenset({"package", "identifiers"})
PACKAGE_FIELDS = frozenset({"package", "name", "status", "identifiers"})
EVIDENCE_RECORD_FIELDS = frozenset({"status", "result"})
IOS_RUNTIME_MAJOR = 26
SIMULATOR_VERIFICATION_SECONDS = 180
SIMULATOR_POLL_INTERVAL_SECONDS = 1
LIVE_COMMAND_TIMEOUT_SECONDS = 600
LIVE_ARTIFACT_MAX_BYTES = 64 * 1024 * 1024
LIVE_BASELINE_COMMIT = "7da6228dc87ad970aa8d44365fbc3823c58020da"
LIVE_REPOSITORY = "mcxl/sqe-platform"
LIVE_ARTIFACT_ROOT = Path("/private/tmp/mcx-19-live-evidence")
LIVE_WORKFLOW = "ace-ios-live-evidence-manual"
LIVE_WORKFLOW_ENVIRONMENT_KEY = "ACE_LIVE_EVIDENCE_WORKFLOW"
LIVE_BRANCH = "codex/mcx-19-live-evidence-harness"
LIVE_OPERATING_ENVIRONMENT_KEYS = (
    "PATH",
    "HOME",
    "TMPDIR",
    "DEVELOPER_DIR",
    "LANG",
    "LC_ALL",
)
LIVE_CONTROLLED_ENVIRONMENT_KEYS = frozenset(
    (*IOS_TEST_ENVIRONMENT, *NEGATIVE_CONFIG_ENVIRONMENT, "ACE_UI_TEST_APPEARANCE")
)
IOS_CORE_DEVICE = "iPhone SE (3rd generation)"
IOS_RELEASE_DEVICES = (IOS_CORE_DEVICE, "iPhone 16 Pro Max")
LIVE_UI_METHODS = (
    "testLaunchShowsSafeConfigurationState",
    "testSignInPasswordFieldIsSecure",
    "testFictionalReleaseHasApprovedCopyControls",
    "testAllControlledScenariosShowExpectedStateAndAudit",
    "testReleaseOrientationHooks",
)
LIVE_FAILURE_SUMMARY_MAX_ITEMS = 23
LIVE_SETUP_FAILURE_REASON = "live-setup-failed"
SIMULATOR_RESOLUTION_FAILURE_REASON = "simulator-resolution-failed"
SIMULATOR_RESOLUTION_TIMEOUT_REASON = "simulator-resolution-timeout"
LIVE_PUBLISHED_FAILURE_REASONS = frozenset(
    {
        "command-timeout",
        "command-start-failed",
        "command-nonzero",
        "result-bundle-missing",
        "result-summary-invalid",
        "result-count-mismatch",
        "negative-configuration-not-rejected",
        LIVE_SETUP_FAILURE_REASON,
        SIMULATOR_RESOLUTION_FAILURE_REASON,
        SIMULATOR_RESOLUTION_TIMEOUT_REASON,
        "controlled-failure",
    }
)
SIMULATOR_UUID = re.compile(
    r"^[0-9A-Fa-f]{8}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{12}$"
)


class SimulatorResolutionError(ValueError):
    """Raised when a required iOS simulator cannot be safely resolved."""

    def __init__(
        self,
        message: str,
        reason: str = SIMULATOR_RESOLUTION_FAILURE_REASON,
    ) -> None:
        super().__init__(message)
        self.reason = reason


class LiveCommandResult(tuple):
    """Keep a command result reason separate from its two public tuple values."""

    def __new__(
        cls, exit_code: int, detail: str, reason: str | None = None
    ) -> "LiveCommandResult":
        result = super().__new__(cls, (exit_code, detail))
        result.reason = reason
        return result


def _require_exact_fields(
    value: object,
    expected: frozenset[str] | tuple[str, ...],
    context: str,
    errors: list[str],
) -> bool:
    """Reject a controlled object with absent or extra claim fields."""

    if not isinstance(value, dict) or set(value) != set(expected):
        errors.append(f"{context} schema is invalid")
        return False
    return True


def _is_non_empty_string(value: object) -> bool:
    """Return true only for a string with visible content."""

    return isinstance(value, str) and bool(value.strip())


def _is_canonical_string_list(value: object, expected: tuple[str, ...]) -> bool:
    """Return true only for the specified ordered list of strings."""

    return isinstance(value, list) and value == list(expected)


def _validate_active_record_requirements(
    requirements: object,
    context: str,
    errors: list[str],
) -> bool:
    """Validate the controlled pending-record requirements."""

    if not _require_exact_fields(
        requirements, ACTIVE_RECORD_REQUIREMENT_FIELDS, context, errors
    ):
        return False
    if (
        requirements["repository"] != "mcxl/sqe-platform"
        or requirements["commit"] != "executing Git head"
        or requirements["status"] != "pending"
        or not _is_canonical_string_list(
            requirements["reviewedRecordFields"], ACTIVE_RECORD_REVIEWED_FIELDS
        )
    ):
        errors.append(f"{context} is invalid")
        return False
    return True


def _validate_simulator_provisioning(
    simulator: object,
    context: str,
    errors: list[str],
) -> bool:
    """Validate the controlled pending simulator-provisioning record."""

    if not _require_exact_fields(
        simulator, SIMULATOR_PROVISIONING_FIELDS, context, errors
    ):
        return False
    if (
        simulator["status"] != "pending"
        or not _is_canonical_string_list(simulator["exactTargets"], IOS_RELEASE_DEVICES)
        or any(
            not _is_non_empty_string(simulator[field])
            for field in ("runtime", "procedure", "failure")
        )
    ):
        errors.append(f"{context} is invalid")
        return False
    return True


def _package_identifier_mapping(
    mappings: object,
    source_ids: list[str],
    context: str,
    errors: list[str],
) -> dict[str, set[str]]:
    """Read one controlled package map and reject incomplete mappings."""

    if not isinstance(mappings, list):
        errors.append(f"{context} package mappings are invalid")
        return {}
    package_ids: dict[str, set[str]] = {}
    identifiers: set[str] = set()
    for mapping in mappings:
        if not _require_exact_fields(mapping, PACKAGE_MAPPING_FIELDS, context, errors):
            continue
        package = mapping["package"]
        mapped_ids = mapping["identifiers"]
        if (
            not isinstance(package, str)
            or not package.strip()
            or package in package_ids
            or not isinstance(mapped_ids, list)
            or not mapped_ids
            or any(not isinstance(identifier, str) or not identifier for identifier in mapped_ids)
            or len(mapped_ids) != len(set(mapped_ids))
        ):
            errors.append(f"{context} package mapping is invalid")
            continue
        mapped_set = set(mapped_ids)
        duplicate_ids = identifiers & mapped_set
        if duplicate_ids:
            errors.append(
                f"{context} package mapping is ambiguous: {', '.join(sorted(duplicate_ids))}"
            )
            continue
        package_ids[package] = mapped_set
        identifiers.update(mapped_set)
    if identifiers != set(source_ids):
        errors.append(f"{context} package identifiers do not match the runtime plan")
    return package_ids


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
    entries = plan.get("entries", [])
    source_ids = [
        identifier
        for entry in entries
        if isinstance(entry, dict)
        for identifier in entry.get("identifiers", [])
    ]
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
    _require_exact_fields(plan, PLAN_FIELDS, "runtime plan", errors)
    if plan.get("scope") != "G0-public-planning-only":
        errors.append("runtime plan is outside public G0 scope")
    if plan.get("releaseEvidence") is not False:
        errors.append("runtime plan must not claim release evidence")
    if plan.get("status") != "pending":
        errors.append("runtime plan status must be pending")
    if plan.get("repository") != "mcxl/sqe-platform":
        errors.append("runtime plan repository is not mcxl/sqe-platform")
    if not _is_canonical_string_list(
        plan.get("resultFieldSchema"), EVIDENCE_RESULT_FIELDS
    ):
        errors.append("runtime plan result field schema is invalid")
    active_requirements = plan.get("activeRecordRequirements")
    _validate_active_record_requirements(
        active_requirements,
        "runtime plan active record requirements",
        errors,
    )
    entries = plan.get("entries")
    if not isinstance(entries, list):
        errors.append("runtime plan entries are invalid")
    else:
        entry_identifiers: set[str] = set()
        for entry in entries:
            if not _require_exact_fields(entry, PLAN_ENTRY_FIELDS, "runtime plan entry", errors):
                continue
            identifiers = entry["identifiers"]
            if (
                entry["status"] != "pending"
                or not isinstance(identifiers, list)
                or not identifiers
                or any(not _is_non_empty_string(identifier) for identifier in identifiers)
                or len(identifiers) != len(set(identifiers))
                or any(
                    not _is_non_empty_string(entry[field])
                    for field in ("stage", "device", "procedure", "expectedResult")
                )
            ):
                errors.append("runtime plan entry is invalid")
                continue
            duplicate_identifiers = entry_identifiers & set(identifiers)
            if duplicate_identifiers:
                errors.append("runtime plan entry identifiers are ambiguous")
                continue
            entry_identifiers.update(identifiers)
    plan_packages = _package_identifier_mapping(
        plan.get("packageMappings"), source_ids, "runtime plan", errors
    )
    controlled = plan.get("controlledRegister")
    if not _require_exact_fields(
        controlled, CONTROLLED_REGISTER_FIELDS, "runtime plan controlled register", errors
    ):
        return ["controlled public evidence register is missing"], "invalid"
    if (
        controlled["workflow"] != "ace-ios-evidence-preflight-manual"
        or controlled["status"] != "pending"
    ):
        errors.append("runtime plan controlled register is invalid")
    simulator = controlled["simulatorProvisioning"]
    _validate_simulator_provisioning(
        simulator, "runtime plan simulator provisioning", errors
    )
    historical = controlled["historicalCommitChain"]
    if not _require_exact_fields(
        historical,
        HISTORICAL_COMMIT_CHAIN_FIELDS,
        "runtime plan historical commit chain",
        errors,
    ) or (
        historical.get("status") != "quarantined"
        or not _is_non_empty_string(historical.get("note"))
    ):
        errors.append("runtime plan historical commit chain is invalid")
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
    _require_exact_fields(register, REGISTER_FIELDS, "controlled public evidence register", errors)
    if register.get("scope") != "G0-public-planning-only":
        errors.append("controlled public evidence register is outside G0 scope")
    if register.get("releaseEvidence") is not False:
        errors.append("controlled public evidence register must not claim release evidence")
    if register.get("status") != controlled["status"]:
        errors.append("controlled public evidence register status does not match the runtime plan")
    if register.get("repository") != "mcxl/sqe-platform":
        errors.append("controlled public evidence register repository is not mcxl/sqe-platform")
    if not _is_canonical_string_list(
        register.get("resultFieldSchema"), EVIDENCE_RESULT_FIELDS
    ):
        errors.append("controlled public evidence register result field schema is invalid")
    register_requirements = register.get("activeRecordRequirements")
    if _validate_active_record_requirements(
        register_requirements,
        "controlled public evidence register active record requirements",
        errors,
    ) and register_requirements != active_requirements:
        errors.append("controlled public evidence register active record requirements do not match the runtime plan")
    if register.get("workflow") != controlled["workflow"]:
        errors.append("controlled public evidence register workflow does not match the runtime plan")
    register_simulator = register.get("simulatorProvisioning")
    if not _validate_simulator_provisioning(
        register_simulator,
        "controlled public evidence register simulator provisioning",
        errors,
    ) or register_simulator.get("status") != controlled["simulatorProvisioning"].get("status"):
        errors.append("controlled public evidence register simulator provisioning is invalid")
    results = register.get("results")
    if not isinstance(results, dict):
        return ["controlled public evidence results are missing"], "invalid"
    packages = register.get("packages")
    if not isinstance(packages, list):
        return ["controlled public evidence packages are missing"], "invalid"
    register_packages: list[dict] = []
    package_by_identifier: dict[str, dict] = {}
    for package in packages:
        if (
            not _require_exact_fields(package, PACKAGE_FIELDS, "controlled public evidence package", errors)
            or not isinstance(package.get("package"), str)
            or not package["package"].strip()
            or not _is_non_empty_string(package.get("name"))
            or package.get("status") != "pending"
            or not isinstance(package.get("identifiers"), list)
        ):
            errors.append("controlled public evidence package is invalid")
            continue
        register_packages.append({"package": package["package"], "identifiers": package["identifiers"]})
        for identifier in package["identifiers"]:
            if not isinstance(identifier, str) or not identifier:
                errors.append("controlled public evidence package identifier is invalid")
            elif identifier in package_by_identifier:
                errors.append(f"{identifier}: public evidence package is ambiguous")
            else:
                package_by_identifier[identifier] = package
    registered_mappings = _package_identifier_mapping(
        register_packages, source_ids, "controlled public evidence register", errors
    )
    if registered_mappings != plan_packages:
        errors.append("controlled public evidence package mappings do not match the runtime plan")
    expected_ids = set(source_ids)
    if set(results) != expected_ids:
        errors.append("controlled public evidence result identifiers do not match the runtime plan")
    if set(package_by_identifier) != expected_ids:
        errors.append("controlled public evidence package identifiers do not match the runtime plan")
    for identifier in source_ids:
        record = results.get(identifier)
        if not _require_exact_fields(
            record, EVIDENCE_RECORD_FIELDS, f"{identifier}: public evidence record", errors
        ):
            errors.append(f"{identifier}: public evidence record is invalid")
            continue
        status = record.get("status")
        result = record.get("result")
        if (
            status != "pending"
            or not _require_exact_fields(
                result, EVIDENCE_RESULT_FIELDS, f"{identifier}: public evidence result", errors
            )
        ):
            errors.append(f"{identifier}: public evidence status or result is invalid")
            continue
        values = {field: result.get(field) for field in EVIDENCE_RESULT_FIELDS}
        package = package_by_identifier.get(identifier)
        if package is None:
            errors.append(f"{identifier}: public evidence package is missing")
            continue
        if package["status"] != "pending":
            errors.append(f"{identifier}: public evidence package must be pending")
        if any(not isinstance(value, str) or value for value in values.values()):
            errors.append(f"{identifier}: pending public evidence must have blank result fields")
    if errors:
        return errors, "invalid"
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
        if appearance not in {"light", "dark"}:
            raise ValueError("UI test appearance must be light or dark")
        environment["ACE_UI_TEST_APPEARANCE"] = appearance
    return environment


def ios_release_ui_matrix(
    destinations: dict[str, str], methods: tuple[str, ...] | list[str]
) -> list[tuple[str, list[str], dict[str, str], int]]:
    """Build the one approved release UI selector matrix for both runner paths."""

    return [
        (
            f"ios-release-{device}-{appearance}-{method}",
            [
                "xcodebuild", "test", "-project", "ACEClientApp.xcodeproj",
                "-scheme", "ACEClientAppUITests", "-configuration", "Debug",
                "-destination", destinations[device],
                f"-only-testing:ACEClientAppUITests/ACEClientAppUITests/{method}",
                f"ACE_UI_TEST_APPEARANCE={appearance}",
            ],
            ios_test_environment(appearance),
            1,
        )
        for device in IOS_RELEASE_DEVICES
        for appearance in ("light", "dark")
        for method in methods
    ]


def _simctl_list(timeout: float | None = None) -> dict:
    if timeout is not None and timeout <= 0:
        raise SimulatorResolutionError(
            "simctl list has no verification time remaining",
            SIMULATOR_RESOLUTION_TIMEOUT_REASON,
        )
    try:
        completed = subprocess.run(
            ["xcrun", "simctl", "list", "-j"],
            cwd=ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            check=False,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired as error:
        raise SimulatorResolutionError(
            "simctl list exceeded the verification deadline",
            SIMULATOR_RESOLUTION_TIMEOUT_REASON,
        ) from error
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


def _simctl_create(name: str, device_type: str, runtime: str, timeout: float) -> str:
    if timeout <= 0:
        raise SimulatorResolutionError(
            "simctl create has no verification time remaining",
            SIMULATOR_RESOLUTION_TIMEOUT_REASON,
        )
    try:
        completed = subprocess.run(
            ["xcrun", "simctl", "create", name, device_type, runtime],
            cwd=ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            check=False,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired as error:
        raise SimulatorResolutionError(
            "simctl create exceeded the verification deadline",
            SIMULATOR_RESOLUTION_TIMEOUT_REASON,
        ) from error
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
    runtime_devices = devices.get(runtime)
    if not isinstance(runtime_devices, list):
        raise SimulatorResolutionError(f"simulator runtime is unavailable for {name}")
    exact_matches = [
        device
        for device in runtime_devices
        if isinstance(device, dict)
        and device.get("name") == name
        and device.get("deviceTypeIdentifier") == device_type
    ]
    if len(exact_matches) != 1:
        raise SimulatorResolutionError(f"exact simulator is ambiguous after creation: {name}")
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
        or device.get("udid", "").upper() != identifier.upper()
    ):
        raise SimulatorResolutionError(f"simulator identity verification failed for {name}")
    return identifier.upper()


def _record_simulator_event(
    recorder: Callable[[str, object], None] | None,
    name: str,
    value: object,
) -> None:
    """Record controlled simulator metadata when a caller requests it."""

    if recorder is not None:
        recorder(name, value)


def _controlled_simulator_snapshot(snapshot: dict, names: tuple[str, ...]) -> dict:
    """Keep only selected simulator metadata for later controlled review."""

    runtimes = snapshot.get("runtimes")
    device_types = snapshot.get("devicetypes")
    devices_by_runtime = snapshot.get("devices")
    return {
        "runtimes": [
            {
                key: runtime.get(key)
                for key in ("identifier", "version", "isAvailable")
            }
            for runtime in (runtimes if isinstance(runtimes, list) else [])
            if isinstance(runtime, dict)
            and _runtime_version(runtime) is not None
        ],
        "devicetypes": [
            {
                key: device_type.get(key)
                for key in ("name", "identifier")
            }
            for device_type in (device_types if isinstance(device_types, list) else [])
            if isinstance(device_type, dict) and device_type.get("name") in names
        ],
        "devices": {
            runtime: [
                {
                    key: device.get(key)
                    for key in ("name", "udid", "isAvailable", "deviceTypeIdentifier")
                }
                for device in devices
                if isinstance(device, dict) and device.get("name") in names
            ]
            for runtime, devices in (devices_by_runtime.items() if isinstance(devices_by_runtime, dict) else [])
            if isinstance(runtime, str) and isinstance(devices, list)
        },
    }


def resolve_ios_destinations(
    names: tuple[str, ...],
    recorder: Callable[[str, object], None] | None = None,
) -> dict[str, str]:
    """Resolve or create exact iOS 26 simulator devices before test execution."""

    if len(names) != len(set(names)):
        raise SimulatorResolutionError("required simulator names must be unique")
    deadline = time.monotonic() + SIMULATOR_VERIFICATION_SECONDS
    remaining = deadline - time.monotonic()
    if remaining <= 0:
        raise SimulatorResolutionError(
            "simctl list has no verification time remaining",
            SIMULATOR_RESOLUTION_TIMEOUT_REASON,
        )
    snapshot = _simctl_list(timeout=remaining)
    _record_simulator_event(
        recorder, "initial-snapshot", _controlled_simulator_snapshot(snapshot, names)
    )
    runtime = _select_ios_runtime(snapshot)
    _record_simulator_event(recorder, "selected-runtime", runtime)
    device_types = {
        name: _device_type_identifier(snapshot, name)
        for name in names
    }
    _record_simulator_event(recorder, "device-types", device_types)
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
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise SimulatorResolutionError(
                    "simctl create has no verification time remaining",
                    SIMULATOR_RESOLUTION_TIMEOUT_REASON,
                )
            identifiers[name] = _simctl_create(
                name, device_types[name], runtime, timeout=remaining
            )
            _record_simulator_event(
                recorder,
                "created-simulator",
                {"name": name, "uuid": identifiers[name]},
            )
            created = True
    if created:
        verification_error: SimulatorResolutionError | None = SimulatorResolutionError(
            "verification deadline expired before the created simulator was observed",
            SIMULATOR_RESOLUTION_TIMEOUT_REASON,
        )
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                verification_error = SimulatorResolutionError(
                    "created simulator did not become available before the verification deadline",
                    SIMULATOR_RESOLUTION_TIMEOUT_REASON,
                )
                break
            snapshot = _simctl_list(timeout=remaining)
            _record_simulator_event(
                recorder, "poll-snapshot", _controlled_simulator_snapshot(snapshot, names)
            )
            try:
                for name in names:
                    _verify_simulator(snapshot, runtime, name, device_types[name], identifiers[name])
                verification_error = None
                break
            except SimulatorResolutionError as error:
                verification_error = error
                if "ambiguous after creation" in str(error):
                    break
                remaining = deadline - time.monotonic()
                if remaining > 0:
                    time.sleep(min(SIMULATOR_POLL_INTERVAL_SECONDS, remaining))
        if verification_error is not None:
            raise SimulatorResolutionError(
                f"created simulator did not become available: {verification_error}",
                verification_error.reason,
            )
    destinations = {
        name: f"platform=iOS Simulator,id={_verify_simulator(snapshot, runtime, name, device_types[name], identifiers[name])}"
        for name in names
    }
    _record_simulator_event(recorder, "resolved-destinations", destinations)
    return destinations


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


def _live_artifact_root(path: Path) -> Path:
    """Create one empty, external, non-symlinked live-artifact directory."""

    if not path.is_absolute():
        raise ValueError("live artifact root must be an absolute path")
    if path.exists() or path.is_symlink():
        raise ValueError("live artifact root must not already exist")
    for parent in (path.parent, *path.parents):
        if parent.exists() and parent.is_symlink():
            raise ValueError("live artifact root has a symlinked parent")
    parent = path.parent.resolve(strict=True)
    root = parent / path.name
    if root.is_relative_to(ROOT.resolve()):
        raise ValueError("live artifact root must be outside the Git working tree")
    root.mkdir(mode=0o700)
    if root.is_symlink() or root.resolve() != root:
        raise ValueError("live artifact root is not a safe directory")
    return root


def _safe_live_path(root: Path, relative: str) -> Path:
    """Return one controlled path below the external artifact root."""

    path = root / relative
    if path.resolve(strict=False).is_relative_to(root.resolve()) is False:
        raise ValueError("live artifact path escapes its root")
    return path


def _live_artifact_checksums(root: Path) -> dict[str, str]:
    """Hash only regular, bounded files below the controlled artifact root."""

    checksums: dict[str, str] = {}
    for path in sorted(root.rglob("*")):
        if path.is_symlink():
            raise ValueError("live artifact contains a symlink")
        if not path.is_file():
            continue
        if not path.resolve().is_relative_to(root.resolve()):
            raise ValueError("live artifact escapes its root")
        if path.stat().st_size > LIVE_ARTIFACT_MAX_BYTES:
            raise ValueError("live artifact exceeds the review size limit")
        relative = str(path.relative_to(root))
        if relative == "live-evidence-manifest.json":
            continue
        digest = hashlib.sha256()
        with path.open("rb") as handle:
            for block in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(block)
        checksums[relative] = digest.hexdigest()
    return checksums


def _verify_live_artifact_checksums(root: Path, expected: dict[str, str]) -> None:
    """Fail when the controlled artifact set changes after its checksum record."""

    if _live_artifact_checksums(root) != expected:
        raise ValueError("live artifact checksum mismatch")


def _scan_live_artifacts(root: Path) -> None:
    """Reject clear secret or unredacted username values without echoing content."""

    sensitive_key = r'(?:"(?:password|authorization|authorisation|keychain[ _-]?secret|credential|token)"|(?:password|authorization|authorisation|keychain[ _-]?secret|credential|token))'
    username_key = r'(?:"(?:username|user)"|(?:username|user))'
    forbidden = re.compile(rf"(?i){sensitive_key}\s*[:=]\s*\S+")
    unredacted_username = re.compile(
        rf'(?i){username_key}\s*[:=]\s*(?!"?\[redacted\]"?(?:\s|,|\}}|$))\S+'
    )
    for path in sorted(root.rglob("*")):
        if path.is_symlink():
            raise ValueError("live artifact contains a symlink")
        if not path.is_file():
            continue
        if path.stat().st_size > LIVE_ARTIFACT_MAX_BYTES:
            raise ValueError("live artifact exceeds the review size limit")
        raw_content = path.read_bytes()
        text_forms = (
            raw_content.decode("utf-8", errors="ignore"),
            raw_content.decode("utf-16-le", errors="ignore"),
            raw_content.decode("utf-16-be", errors="ignore"),
        )
        if any(
            forbidden.search(content) or unredacted_username.search(content)
            for content in text_forms
        ):
            raise ValueError("live artifact secret or redaction check failed")


def _live_command_environment(environment: dict[str, str]) -> dict[str, str]:
    """Allow only Xcode operating values and the controlled test-input values."""

    if not set(environment).issubset(LIVE_CONTROLLED_ENVIRONMENT_KEYS):
        raise ValueError("live command has an unapproved environment input")
    command_environment = {
        key: os.environ[key]
        for key in LIVE_OPERATING_ENVIRONMENT_KEYS
        if os.environ.get(key)
    }
    command_environment.update(environment)
    return command_environment


def _run_live_command(
    name: str,
    command: list[str],
    cwd: Path,
    environment: dict[str, str],
    log_path: Path,
) -> tuple[int, str]:
    """Run one approved command and retain output only outside the repository."""

    command_environment = _live_command_environment(environment)
    try:
        with log_path.open("w", encoding="utf-8", errors="replace") as log:
            completed = subprocess.run(
                command,
                cwd=cwd,
                env=command_environment,
                text=True,
                stdout=log,
                stderr=subprocess.STDOUT,
                check=False,
                timeout=LIVE_COMMAND_TIMEOUT_SECONDS,
            )
    except subprocess.TimeoutExpired:
        return LiveCommandResult(
            1, f"{name} exceeded its time limit", "command-timeout"
        )
    except OSError:
        return LiveCommandResult(
            1, f"{name} could not start", "command-start-failed"
        )
    if completed.returncode != 0:
        return LiveCommandResult(
            1, f"{name} returned a non-zero result", "command-nonzero"
        )
    return LiveCommandResult(0, f"{name} completed")


def _xcodebuild_options_before_build_settings(
    command: list[str], options: list[str]
) -> list[str]:
    """Put Xcode options before controlled command-line build settings."""

    for index, argument in enumerate(command):
        if re.fullmatch(r"ACE_[A-Z0-9_]+=.*", argument):
            return [*command[:index], *options, *command[index:]]
    return [*command, *options]


def _run_live_ios_test(
    name: str,
    command: list[str],
    cwd: Path,
    environment: dict[str, str],
    expected_tests: int,
    root: Path,
) -> dict:
    """Run one approved XCTest selector with an external result bundle and count gate."""

    result_path = _safe_live_path(root, f"{name}.xcresult")
    log_path = _safe_live_path(root, f"{name}.log")
    command_result = _run_live_command(
        name,
        _xcodebuild_options_before_build_settings(
            command, ["-resultBundlePath", str(result_path)]
        ),
        cwd,
        environment,
        log_path,
    )
    exit_code, detail = command_result
    if exit_code:
        return {
            "name": name,
            "status": "failed",
            "exit": 1,
            "detail": detail,
            "reason": _published_live_failure_reason(
                getattr(command_result, "reason", None)
            ),
        }
    if not result_path.is_dir() or result_path.is_symlink():
        return {
            "name": name,
            "status": "failed",
            "exit": 1,
            "detail": f"{name} result bundle is missing",
            "reason": "result-bundle-missing",
        }
    summary_path = _safe_live_path(root, f"{name}-summary.json")
    summary_result = _run_live_command(
        f"{name}-xcresult",
        [
            "xcrun", "xcresulttool", "get", "test-results", "summary",
            "--path", str(result_path),
        ],
        cwd,
        {},
        summary_path,
    )
    summary_exit, summary_detail = summary_result
    if summary_exit:
        return {
            "name": name,
            "status": "failed",
            "exit": 1,
            "detail": summary_detail,
            "reason": _published_live_failure_reason(
                getattr(summary_result, "reason", None)
            ),
        }
    try:
        counts = _xcresult_counts(json.loads(summary_path.read_text(encoding="utf-8")))
    except (OSError, json.JSONDecodeError):
        counts = None
    if counts is None:
        return {
            "name": name,
            "status": "failed",
            "exit": 1,
            "detail": f"{name} has no executed-test summary",
            "reason": "result-summary-invalid",
        }
    passed, failed, skipped = counts
    if passed != expected_tests or failed != 0 or skipped != 0:
        return {
            "name": name,
            "status": "failed",
            "exit": 1,
            "detail": f"{name} result count mismatch",
            "reason": "result-count-mismatch",
        }
    return {"name": name, "status": "passed", "exit": 0, "detail": f"{name} executed {passed} tests"}


def _live_repository_metadata(expected_commit: str) -> dict[str, str]:
    """Bind a live run to the approved repository, ancestry, clean tree, and Git head."""

    def git(*arguments: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["git", *arguments], cwd=ROOT, text=True, stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL, check=False,
        )

    remote = git("remote", "get-url", "origin")
    head = git("rev-parse", "HEAD")
    ancestry = git("merge-base", "--is-ancestor", LIVE_BASELINE_COMMIT, "HEAD")
    clean = git("status", "--porcelain", "--untracked-files=all")
    allowed_remotes = {
        "https://github.com/mcxl/sqe-platform.git",
        "git@github.com:mcxl/sqe-platform.git",
        "ssh://git@github.com/mcxl/sqe-platform.git",
        "https://mcxl@github.com/mcxl/sqe-platform",
    }
    remote_value = remote.stdout
    if remote_value.endswith("\r\n"):
        remote_value = remote_value[:-2]
    elif remote_value.endswith("\n"):
        remote_value = remote_value[:-1]
    commit = head.stdout.strip()
    failed_checks = []
    if remote.returncode != 0 or remote_value not in allowed_remotes:
        failed_checks.append("repository-identity")
    if re.fullmatch(r"[0-9a-f]{40}", expected_commit) is None:
        failed_checks.append("expected-commit-format")
    if head.returncode != 0 or re.fullmatch(r"[0-9a-f]{40}", commit) is None:
        failed_checks.append("git-head")
    if (
        re.fullmatch(r"[0-9a-f]{40}", expected_commit) is not None
        and re.fullmatch(r"[0-9a-f]{40}", commit) is not None
        and commit != expected_commit
    ):
        failed_checks.append("expected-commit-match")
    if ancestry.returncode != 0:
        failed_checks.append("baseline-ancestry")
    if clean.returncode != 0 or clean.stdout.strip():
        failed_checks.append("clean-tree")
    if failed_checks:
        raise ValueError("repository binding failed: " + ", ".join(failed_checks))
    return {"repository": LIVE_REPOSITORY, "commit": commit, "baseline": LIVE_BASELINE_COMMIT}


def _live_execution_context(artifact_root: Path, expected_commit: str) -> dict[str, str]:
    """Require the exact manual Codemagic workflow and checked-out build context."""

    build_directory = os.environ.get("CM_BUILD_DIR")
    if (
        artifact_root != LIVE_ARTIFACT_ROOT
        or not _is_non_empty_string(os.environ.get("CM_BUILD_ID"))
        or not _is_non_empty_string(build_directory)
        or Path(build_directory).resolve() != ROOT.resolve()
        or os.environ.get(LIVE_WORKFLOW_ENVIRONMENT_KEY) != LIVE_WORKFLOW
        or os.environ.get("CM_COMMIT") != expected_commit
        or os.environ.get("CM_BRANCH") != LIVE_BRANCH
        or os.environ.get("CM_TRIGGER_SOURCE") != "api"
        or not _is_non_empty_string(os.environ.get("CM_BUILD_STARTED_BY"))
    ):
        raise ValueError("verified Codemagic live workflow context is invalid")
    return {"workflow": LIVE_WORKFLOW}


def _write_live_manifest(root: Path, manifest: dict) -> None:
    """Write controlled review metadata without command output or environment values."""

    path = _safe_live_path(root, "live-evidence-manifest.json")
    path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _live_failure_detail(error: Exception) -> str:
    """Return fixed safe text for a live setup or simulator failure."""

    reason = _live_failure_reason(error)
    if reason == SIMULATOR_RESOLUTION_TIMEOUT_REASON:
        return "simulator resolution timed out"
    if reason == SIMULATOR_RESOLUTION_FAILURE_REASON:
        return "simulator resolution failed"
    return "live setup failed"


def _live_failure_reason(error: Exception) -> str:
    """Return one fixed reason code without reading exception text."""

    if isinstance(error, SimulatorResolutionError):
        reason = getattr(error, "reason", SIMULATOR_RESOLUTION_FAILURE_REASON)
        if reason == SIMULATOR_RESOLUTION_TIMEOUT_REASON:
            return reason
        return SIMULATOR_RESOLUTION_FAILURE_REASON
    return LIVE_SETUP_FAILURE_REASON


def _live_setup_failure(error: Exception) -> dict:
    """Build one public live setup failure without exception data."""

    reason = _live_failure_reason(error)
    return {
        "name": "live-evidence",
        "status": "failed",
        "exit": 1,
        "detail": _live_failure_detail(error),
        "reason": reason,
    }


def _published_live_failure_reason(reason: object, name: object = None) -> str:
    """Return one fixed public reason code for a failed live command."""

    if name == "ios-negative-config":
        return "negative-configuration-not-rejected"
    if isinstance(reason, str) and reason in LIVE_PUBLISHED_FAILURE_REASONS:
        return reason
    return "controlled-failure"


def _published_live_result(check: dict) -> dict:
    """Remove untrusted failure detail before a live result is published."""

    result = dict(check)
    if result.get("exit") != 0:
        reason = _published_live_failure_reason(
            result.get("reason"), result.get("name")
        )
        result["reason"] = reason
        result["detail"] = "controlled live command failed"
    else:
        result.pop("reason", None)
    return result


def _live_command_failure_summary(checks: list[dict]) -> str:
    """Return bounded, ordered live command names and controlled reason codes."""

    destinations = {device: "" for device in IOS_RELEASE_DEVICES}
    allowed_names = {
        "ios-65-unit",
        "ios-evidence-contract",
        "ios-negative-config",
        *(name for name, *_ in ios_release_ui_matrix(destinations, LIVE_UI_METHODS)),
    }
    reasons_by_name: dict[str, set[str]] = {}
    for item in checks:
        name = item.get("name")
        if (
            item.get("exit") != 0
            and isinstance(name, str)
            and name in allowed_names
        ):
            reasons_by_name.setdefault(name, set()).add(
                _published_live_failure_reason(item.get("reason"), name)
            )
    names = sorted(reasons_by_name)[:LIVE_FAILURE_SUMMARY_MAX_ITEMS]
    names_text = ", ".join(names)
    reasons_text = ", ".join(
        f"{name}={min(reasons_by_name[name])}" for name in names
    )
    return f"failed live commands: {names_text}; reasons: {reasons_text}"


def live_evidence_checks(artifact_root: Path, expected_commit: str) -> list[dict]:
    """Run the approved manual live scope and fail closed on every control error."""

    try:
        root = _live_artifact_root(artifact_root)
    except (OSError, ValueError) as error:
        return [_live_setup_failure(error)]
    manifest: dict[str, object] = {
        "scope": "MCX-19-manual-live-evidence",
        "releaseEvidence": False,
        "status": "failed",
        "results": [],
    }
    try:
        _write_live_manifest(root, manifest)
    except (OSError, ValueError) as error:
        return [_live_setup_failure(error)]
    try:
        manifest.update(_live_execution_context(artifact_root, expected_commit))
        _write_live_manifest(root, manifest)
        metadata = _live_repository_metadata(expected_commit)
        manifest.update(metadata)
        _write_live_manifest(root, manifest)
        if tuple(ui_methods()) != LIVE_UI_METHODS:
            raise ValueError("approved UI test scope does not match the repository")
        if shutil.which("xcodebuild") is None or shutil.which("xcrun") is None:
            raise ValueError("required iOS test tools are unavailable")

        events: list[dict[str, object]] = []
        destinations = resolve_ios_destinations(
            IOS_RELEASE_DEVICES,
            recorder=lambda name, value: events.append({"event": name, "value": value}),
        )
        _safe_live_path(root, "simulator-resolution.json").write_text(
            json.dumps(events, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        manifest["simulatorMetadata"] = "simulator-resolution.json"
        _write_live_manifest(root, manifest)
        ios = ROOT / "ios" / "ACEClientApp"
        checks = [
            _run_live_ios_test(
                "ios-65-unit",
                ["xcodebuild", "test", "-project", "ACEClientApp.xcodeproj", "-scheme", "ACEClientApp", "-destination", destinations[IOS_CORE_DEVICE], "-only-testing:ACEClientAppTests"],
                ios, ios_test_environment(), 65, root,
            )
        ]
        checks.extend(
            _run_live_ios_test(name, command, ios, environment, expected, root)
            for name, command, environment, expected in ios_release_ui_matrix(
                destinations, LIVE_UI_METHODS
            )
        )
        checks.append(_run_live_ios_test(
            "ios-evidence-contract",
            ["xcodebuild", "test", "-project", "ACEClientApp.xcodeproj", "-scheme", "ACEClientApp", "-destination", destinations[IOS_CORE_DEVICE], "-only-testing:ACEClientAppTests/AcceptanceEvidenceContractTests"],
            ios, ios_test_environment(), 42, root,
        ))
        negative_log = _safe_live_path(root, "ios-negative-config.log")
        negative_exit, _ = _run_live_command(
            "ios-negative-config",
            [
                "xcodebuild", "build", "-project", "ACEClientApp.xcodeproj",
                "-scheme", "ACEClientApp",
                *(f"{key}={value}" for key, value in NEGATIVE_CONFIG_ENVIRONMENT.items()),
            ],
            ios, NEGATIVE_CONFIG_ENVIRONMENT, negative_log,
        )
        try:
            negative_rejected = (
                negative_exit != 0
                and NEGATIVE_CONFIG_REJECTION
                in negative_log.read_text(encoding="utf-8", errors="replace")
            )
        except OSError:
            negative_rejected = False
        if not negative_rejected:
            checks.append(
                {
                    "name": "ios-negative-config",
                    "status": "failed",
                    "exit": 1,
                    "detail": "negative configuration did not fail as required",
                    "reason": "negative-configuration-not-rejected",
                }
            )
        else:
            checks.append({"name": "ios-negative-config", "status": "passed", "exit": 0, "detail": "negative configuration rejected"})
        checks = [_published_live_result(check) for check in checks]
        manifest["results"] = checks
        _write_live_manifest(root, manifest)
        if any(check["exit"] != 0 for check in checks):
            detail = _live_command_failure_summary(checks)
            manifest["failure"] = detail
            _write_live_manifest(root, manifest)
            return [{"name": "live-evidence", "status": "failed", "exit": 1, "detail": detail}]
        required_files = {"simulator-resolution.json", "ios-negative-config.log"}
        required_bundles: set[str] = set()
        for check in checks:
            if check["name"] != "ios-negative-config":
                required_files.update({f"{check['name']}.log", f"{check['name']}-summary.json"})
                required_bundles.add(f"{check['name']}.xcresult")
        checksums = _live_artifact_checksums(root)
        if (
            not required_files.issubset(checksums)
            or any(not _safe_live_path(root, bundle).is_dir() for bundle in required_bundles)
        ):
            raise ValueError("one or more required live artifacts are missing")
        _scan_live_artifacts(root)
        _verify_live_artifact_checksums(root, checksums)
        manifest.update({"status": "passed-not-release-evidence", "results": checks, "checksums": checksums})
        _write_live_manifest(root, manifest)
        return checks
    except (OSError, ValueError, SimulatorResolutionError) as error:
        result = _live_setup_failure(error)
        manifest["failure"] = result["reason"]
        try:
            _write_live_manifest(root, manifest)
        except (OSError, ValueError):
            pass
        return [result]


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
        reason = _live_failure_reason(error)
        return [{
            "name": "ios-simulator",
            "status": "failed",
            "exit": 1,
            "detail": _live_failure_detail(error),
            "reason": reason,
        }]
    destination = destinations[IOS_CORE_DEVICE]
    unit = ["xcodebuild", "test", "-project", "ACEClientApp.xcodeproj", "-scheme", "ACEClientApp", "-destination", destination, "-only-testing:ACEClientAppTests"]
    checks = [{"name": "ios-simulator", "status": "passed", "exit": 0, "detail": "resolved exact simulator UUIDs"}, run_ios_test("ios-65-unit", unit, ios, ios_test_environment(), 65)]
    checks.extend(run_ios_test(f"ios-core-ui-light-{method}", ["xcodebuild", "test", "-project", "ACEClientApp.xcodeproj", "-scheme", "ACEClientAppUITests", "-configuration", "Debug", "-destination", destination, f"-only-testing:ACEClientAppUITests/ACEClientAppUITests/{method}", "ACE_UI_TEST_APPEARANCE=light"], ios, ios_test_environment("light"), 1) for method in methods)
    if level == "release":
        checks.extend(
            run_ios_test(name, command, ios, environment, expected)
            for name, command, environment, expected in ios_release_ui_matrix(
                destinations, methods
            )
        )
        checks.extend([run_ios_test("ios-evidence-contract", ["xcodebuild", "test", "-project", "ACEClientApp.xcodeproj", "-scheme", "ACEClientApp", "-destination", destination, "-only-testing:ACEClientAppTests/AcceptanceEvidenceContractTests"], ios, ios_test_environment(), 42), run_command("ios-negative-config", ["xcodebuild", "build", "-project", "ACEClientApp.xcodeproj", "-scheme", "ACEClientApp"], ios, environment=NEGATIVE_CONFIG_ENVIRONMENT, expected_failure=NEGATIVE_CONFIG_REJECTION)])
    return checks


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("level", choices=["focused", "core", "release", "evidence-check", "live-evidence"])
    parser.add_argument("--component", choices=["python", "web", "ios"])
    parser.add_argument("--artifact-root")
    parser.add_argument("--expected-commit")
    args = parser.parse_args(argv)
    data, mapping_errors = load_mapping()
    if args.level != "evidence-check" and not args.component:
        parser.error("--component is required except for evidence-check")
    if args.level == "live-evidence" and args.component != "ios":
        parser.error("live-evidence requires --component ios")
    if args.level == "live-evidence" and args.artifact_root is None:
        parser.error("live-evidence requires --artifact-root")
    if args.level == "live-evidence" and (
        args.expected_commit is None
        or re.fullmatch(r"[0-9a-f]{40}", args.expected_commit) is None
    ):
        parser.error("live-evidence requires --expected-commit as a lower-case 40-hex SHA")
    results = []
    if mapping_errors:
        results.append({"name": "mapping", "status": "failed", "exit": 1, "detail": "; ".join(mapping_errors)})
    elif args.level == "evidence-check":
        results.append({"name": "public-g0-preflight", "status": "passed", "exit": 0, "detail": f"44 source IDs map once to G1-G6; {data['evidencePreflightState']}; manual evidence was not run"})
    elif args.level == "live-evidence":
        results.extend(live_evidence_checks(Path(args.artifact_root), args.expected_commit))
    else:
        results.extend(component_checks(args.level, args.component))
    exits = {item["exit"] for item in results}
    exit_code = 1 if 1 in exits else 2 if 2 in exits else 0
    if args.level == "live-evidence":
        print("report=external-artifact-root/live-evidence-manifest.json")
    else:
        REPORT_DIR.mkdir(parents=True, exist_ok=True)
        report = {"timestamp": datetime.now(timezone.utc).isoformat(), "level": args.level, "component": args.component, "mapping": data.get("iosPrimaryGroups", {}), "evidencePreflightState": data.get("evidencePreflightState"), "releaseEvidence": False, "results": results, "exit": exit_code}
        report_path = REPORT_DIR / f"{args.level}-{args.component or 'manual'}.json"
        report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        print(f"report={report_path.relative_to(ROOT)}")
    for item in results: print(f"{item['name']}: {item['status']}: {item['detail'].splitlines()[0] if item['detail'] else ''}")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
