#!/usr/bin/env python3
"""Run dependency-free SQE component checks without installing software."""
from __future__ import annotations

import argparse
import hashlib
import io
import importlib.util
import json
import math
import os
import platform
import re
import shutil
import subprocess
import sys
import tempfile
import tarfile
import time
import zlib
from datetime import datetime, timedelta, timezone
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
CODEMAGIC_XCODE_VERSION = "26.4.1"
SIMULATOR_VERIFICATION_SECONDS = 360
SIMULATOR_POLL_INTERVAL_SECONDS = 1
LIVE_COMMAND_TIMEOUT_SECONDS = 600
LIVE_DIAGNOSTIC_COLLECTION_TIMEOUT_SECONDS = 30
LIVE_ARTIFACT_MAX_BYTES = 64 * 1024 * 1024
LIVE_BASELINE_COMMIT = "7da6228dc87ad970aa8d44365fbc3823c58020da"
LIVE_REPOSITORY = "mcxl/sqe-platform"
LIVE_ARTIFACT_ROOT = Path("/private/tmp/mcx-19-live-evidence")
LIVE_PRIVATE_COLLECTION_ROOT = Path("/private/tmp/mcx-19-full-matrix-private")
LIVE_PRIVATE_COLLECTION_ARCHIVE = "mcx19-full-matrix-records.tar.gz"
LIVE_PRIVATE_PRESERVED_DIRECTORY = "preserved-records"
LIVE_PRIVATE_COLLECTION_MAX_FILES = 4096
LIVE_PRIVATE_COLLECTION_MAX_FILE_BYTES = 64 * 1024 * 1024
LIVE_PRIVATE_COLLECTION_MAX_ARCHIVE_BYTES = 256 * 1024 * 1024
LIVE_PRIVATE_COLLECTION_STATUSES = frozenset(
    {"complete", "incomplete", "quarantined-pending-review", "failed"}
)
LIVE_PRIVATE_COLLECTION_FAILURE_REASON = "private-collection-failed"
LIVE_PRIVATE_COLLECTION_QUARANTINE_REASON = "private-collection-quarantined"
LIVE_REMOTE_RETENTION_UNAVAILABLE_REASON = "remote-retention-unavailable"
LIVE_REVIEW_MANIFEST = "live-evidence-review-manifest.json"
LIVE_REVIEW_STAGE = ".review-artifact-stage"
LIVE_REVIEW_ARTIFACTS = "review-artifacts"
LIVE_SCREENSHOT_DIRECTORY = "screenshots"
LIVE_DIAGNOSTIC_IMAGE_DIRECTORY = "diagnostic-images"
SIMULATOR_RESOLUTION_LOG = "simulator-resolution.log"
LIVE_WORKFLOW = "ace-ios-live-evidence-manual"
LIVE_REPAIR_WORKFLOW = "ace-ios-repair-check-manual"
RETENTION_PILOT_WORKFLOW = "ace-ios-retention-pilot-manual"
LIVE_WORKFLOW_ENVIRONMENT_KEY = "ACE_LIVE_EVIDENCE_WORKFLOW"
LIVE_BRANCH = "codex/mcx-19-live-evidence-harness"
LIVE_REPAIR_SCOPE = "MCX-19-live-repair-check"
LIVE_REPAIR_SNAPSHOT = "repair-check.json"
RETENTION_PILOT_ARTIFACT_ROOT = Path("/private/tmp/mcx-19-retention-pilot")
RETENTION_PILOT_PRIVATE_ROOT = Path("/private/tmp/mcx-19-retention-pilot-private")
RETENTION_PILOT_ARCHIVE = "mcx19-retention-pilot-records.tar.gz"
RETENTION_PILOT_ACK_TIMEOUT_SECONDS = 600
RETENTION_PILOT_ACK_POLL_SECONDS = 5
RETENTION_PILOT_PHASES = (
    "transport-probe",
    "ios-release-iPhone 17-light-testLaunchShowsSafeConfigurationState",
    "ios-release-iPhone 17-light-testSignInPasswordFieldIsSecure",
)
LIVE_OPERATING_ENVIRONMENT_KEYS = (
    "PATH",
    "HOME",
    "TMPDIR",
    "DEVELOPER_DIR",
    "LANG",
    "LC_ALL",
)
LIVE_CONTROLLED_ENVIRONMENT_KEYS = frozenset(
    (*IOS_TEST_ENVIRONMENT, *NEGATIVE_CONFIG_ENVIRONMENT, "ACE_UI_TEST_APPEARANCE",
     "TEST_RUNNER_ACE_UI_TEST_APPEARANCE",
     "ACE_EXPECTED_EFFECTIVE_INTERFACE_STYLE",
     "TEST_RUNNER_ACE_EXPECTED_EFFECTIVE_INTERFACE_STYLE",
     "ACE_EXPECTED_CONTENT_SIZE_CATEGORY",
     "TEST_RUNNER_ACE_EXPECTED_CONTENT_SIZE_CATEGORY")
)
IOS_CORE_DEVICE = "iPhone 17"
IOS_RELEASE_DEVICES = (IOS_CORE_DEVICE, "iPhone 17 Pro Max")
LIVE_UI_METHODS = (
    "testBothAppearances",
    "testLaunchShowsSafeConfigurationState",
    "testSignInPasswordFieldIsSecure",
    "testFictionalReleaseHasApprovedCopyControls",
    "testAllControlledScenariosShowExpectedStateAndAudit",
    "testReleaseOrientationHooks",
)
LIVE_REPAIR_UI_METHODS = (
    "testFictionalReleaseHasApprovedCopyControls",
)
LIVE_REPAIR_DEVICE = "iPhone 17 Pro Max"
LIVE_NORMAL_SETTINGS_METHOD = "testNormalDeviceSettings"
LIVE_NORMAL_SETTINGS_APPEARANCES = ("light", "dark")
LIVE_CONTENT_SIZE = "accessibility-extra-extra-extra-large"
LIVE_CONTENT_SIZES = frozenset({
    "extra-small", "small", "medium", "large", "extra-large",
    "extra-extra-large", "extra-extra-extra-large", "accessibility-medium",
    "accessibility-large", "accessibility-extra-large",
    "accessibility-extra-extra-large", "accessibility-extra-extra-extra-large",
})
LIVE_CONTROLLED_SCENARIOS = (
    "loading", "emptyRelease", "emptyEngagement", "noConclusion", "noActions",
    "denied", "unavailable", "unexpected", "connection", "timeout",
    "invalidResponse", "secure", "keychainRead", "keychainWrite",
    "keychainDeletion", "deletionOnly", "deletionRetry", "copyConfirmation", "privacy",
)
LIVE_RELEASE_DETAIL_FIELDS = (
    "Engagement name", "Review status", "Release version", "Published date and time",
    "Conclusion title", "Conclusion summary", "Evidence reference", "Action description",
    "Action owner", "Action target date", "Action status",
)
LIVE_FAILURE_SUMMARY_MAX_ITEMS = 31
LIVE_RESULT_SUMMARY_MAX_BYTES = 1024 * 1024
LIVE_RESULT_SUMMARY_MAX_NODES = 10_000
LIVE_PROCESS_EXIT_MIN = -(2**31)
LIVE_PROCESS_EXIT_MAX = 2**31 - 1
LIVE_SETUP_FAILURE_REASON = "live-setup-failed"
SIMULATOR_RESOLUTION_FAILURE_REASON = "simulator-resolution-failed"
SIMULATOR_RESOLUTION_TIMEOUT_REASON = "simulator-resolution-timeout"
LIVE_PUBLISHED_FAILURE_REASONS = frozenset(
    {
        "command-timeout",
        "command-start-failed",
        "command-nonzero",
        "negative-configuration-exited-zero",
        "negative-configuration-unrelated-nonzero",
        "negative-configuration-timeout",
        "negative-configuration-start-failed",
        "negative-configuration-log-missing",
        "negative-configuration-log-unsafe",
        "negative-configuration-log-oversized",
        "negative-configuration-log-unreadable",
        "result-bundle-missing",
        "result-summary-invalid",
        "result-count-mismatch",
        "attachment-export-failed",
        "attachment-missing",
        "attachment-invalid",
        "safe-image-retention-failed",
        "simulator-setting-query-failed",
        "simulator-setting-set-failed",
        "simulator-setting-restore-failed",
        "negative-configuration-not-rejected",
        LIVE_SETUP_FAILURE_REASON,
        SIMULATOR_RESOLUTION_FAILURE_REASON,
        SIMULATOR_RESOLUTION_TIMEOUT_REASON,
        "controlled-failure",
        LIVE_PRIVATE_COLLECTION_FAILURE_REASON,
        LIVE_PRIVATE_COLLECTION_QUARANTINE_REASON,
        LIVE_REMOTE_RETENTION_UNAVAILABLE_REASON,
    }
)
LIVE_PUBLISHED_DIAGNOSTICS = frozenset(
    {
        "test-failures-recorded",
        "result-summary-no-failed-tests",
        "result-bundle-missing",
        "result-summary-command-failed",
        "result-summary-missing",
        "result-summary-unsafe",
        "result-summary-oversized",
        "result-summary-unreadable",
        "result-summary-malformed",
        "result-summary-over-complex",
        "diagnostic-gap",
    }
)
LIVE_DIAGNOSTIC_IMAGE_STATUSES = frozenset(
    {
        "available",
        "partial",
        "attachment-export-failed",
        "attachment-invalid",
        "attachment-missing",
        "result-bundle-unavailable",
    }
)
LIVE_DIAGNOSTIC_ATTACHMENT_PROBLEMS = frozenset(
    {"attachment-ambiguous", "attachment-invalid"}
)
NEGATIVE_CONFIGURATION_REASONS = frozenset(
    {
        "negative-configuration-exited-zero",
        "negative-configuration-unrelated-nonzero",
        "negative-configuration-timeout",
        "negative-configuration-start-failed",
        "negative-configuration-log-missing",
        "negative-configuration-log-unsafe",
        "negative-configuration-log-oversized",
        "negative-configuration-log-unreadable",
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


class SafeImageRetentionError(ValueError):
    """Stop the run after a checked safe-image collection failure."""


class PrivateCollectionError(ValueError):
    """Stop the run with fixed private-retention diagnostics only."""

    def __init__(self, phase: str, category: str, command: str) -> None:
        super().__init__("private collection stopped")
        self.phase = phase
        self.category = category
        self.command = command


def _require_remote_retention(command: str) -> None:
    """Stop before a second command until retrieval has direct evidence."""

    raise PrivateCollectionError(
        "remote-retrievability", LIVE_REMOTE_RETENTION_UNAVAILABLE_REASON, command
    )


class LiveCommandResult(tuple):
    """Keep a command result reason separate from its two public tuple values."""

    def __new__(
        cls,
        exit_code: int,
        detail: str,
        reason: str | None = None,
        process_exit: int | None = None,
    ) -> "LiveCommandResult":
        result = super().__new__(cls, (exit_code, detail))
        result.reason = reason
        result.process_exit = process_exit
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
        # xcodebuild forwards TEST_RUNNER_ variables to XCTest without the prefix.
        environment["TEST_RUNNER_ACE_UI_TEST_APPEARANCE"] = appearance
    return environment


def ios_normal_settings_environment(appearance: str) -> dict[str, str]:
    """Provide an observed-style expectation without forcing the app appearance."""

    if appearance not in {"light", "dark"}:
        raise ValueError("normal device appearance must be light or dark")
    return {
        **IOS_TEST_ENVIRONMENT,
        "ACE_EXPECTED_EFFECTIVE_INTERFACE_STYLE": appearance,
        "TEST_RUNNER_ACE_EXPECTED_EFFECTIVE_INTERFACE_STYLE": appearance,
        "ACE_EXPECTED_CONTENT_SIZE_CATEGORY": LIVE_CONTENT_SIZE,
        "TEST_RUNNER_ACE_EXPECTED_CONTENT_SIZE_CATEGORY": LIVE_CONTENT_SIZE,
    }


def ios_negative_configuration_command() -> list[str]:
    """Reach the invalid-input build phase without device signing requirements."""
    return [
        "xcodebuild", "build", "-project", "ACEClientApp.xcodeproj",
        "-scheme", "ACEClientApp", "-sdk", "iphonesimulator",
        "-destination", "generic/platform=iOS Simulator", "CODE_SIGNING_ALLOWED=NO",
        *(f"{key}={value}" for key, value in NEGATIVE_CONFIG_ENVIRONMENT.items()),
    ]


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


def ios_live_repair_check_matrix(
    destinations: dict[str, str]
) -> list[tuple[str, list[str], dict[str, str], int]]:
    """Build the fixed one-command repair-check native scope."""

    return [
        item for item in ios_release_ui_matrix(destinations, LIVE_REPAIR_UI_METHODS)
        if f"-{LIVE_REPAIR_DEVICE}-light-" in item[0]
    ]


def ios_normal_settings_matrix(destinations: dict[str, str]) -> list[tuple[str, list[str], dict[str, str], int]]:
    """Run the normal-device-settings check outside the forced appearance matrix."""

    return [
        (
            f"ios-normal-settings-{device}-{appearance}",
            [
                "xcodebuild", "test", "-project", "ACEClientApp.xcodeproj",
                "-scheme", "ACEClientAppUITests", "-configuration", "Debug",
                "-destination", destinations[device],
                "-only-testing:ACEClientAppUITests/ACEClientAppUITests/"
                f"{LIVE_NORMAL_SETTINGS_METHOD}",
            ],
            ios_normal_settings_environment(appearance),
            1,
        )
        for device in IOS_RELEASE_DEVICES
        for appearance in LIVE_NORMAL_SETTINGS_APPEARANCES
    ]


def _simulator_text(value: object) -> str:
    """Convert captured process data to UTF-8 text for the controlled log."""

    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return value if isinstance(value, str) else ""


_ACTIVE_SIMULATOR_LOG_ROOT: Path | None = None
_SIMULATOR_OPERATION_SEQUENCE = 0


def _write_simulator_resolution_log(root: Path | None, event: dict[str, object]) -> None:
    """Append one simulator command event to disk and standard error."""

    line = json.dumps(event, sort_keys=True)
    if root is None:
        print("simulator-resolution=" + line, file=sys.stderr, flush=True)
        return
    try:
        path = _safe_live_path(root, SIMULATOR_RESOLUTION_LOG)
        path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as handle:
            handle.write(line + "\n")
    except OSError as error:
        raise SimulatorResolutionError("simulator resolution log could not be written") from error
    print("simulator-resolution=" + line, file=sys.stderr, flush=True)


def _write_simulator_operation_record(root: Path | None, relative: str, event: dict[str, object]) -> None:
    """Write one simulator operation record at its unique controlled path."""

    if root is not None:
        _safe_live_path(root, relative).parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        _write_live_json_atomically(root, relative, event)


def _run_simulator_command(
    root: Path | None,
    phase: str,
    command: list[str],
    timeout: float,
) -> subprocess.CompletedProcess[str]:
    """Run one simulator preflight command with a full command record."""

    global _SIMULATOR_OPERATION_SEQUENCE
    _SIMULATOR_OPERATION_SEQUENCE += 1
    operation_relative = f"simulator-operations/{_SIMULATOR_OPERATION_SEQUENCE:08d}.json"

    def record(event: dict[str, object]) -> None:
        value = {**event, "operationRecord": operation_relative}
        _write_simulator_resolution_log(root, value)
        _write_simulator_operation_record(root, operation_relative, value)

    started_at = datetime.now(timezone.utc)
    started = time.monotonic()
    deadline_at = started_at + timedelta(seconds=timeout)
    record({
        "event": "started",
        "phase": phase,
        "command": " ".join(command),
        "argv": command,
        "exitCode": None,
        "elapsedSeconds": None,
        "stdout": "",
        "stderr": "",
        "startTimeUTC": started_at.isoformat(),
        "deadline": datetime.fromtimestamp(
            started_at.timestamp() + timeout, timezone.utc
        ).isoformat(),
        "remainingSeconds": timeout,
    })
    try:
        completed = subprocess.run(
            command,
            cwd=ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired as error:
        elapsed = time.monotonic() - started
        record({
            "event": "timed-out",
            "phase": phase,
            "command": " ".join(command),
            "argv": command,
            "exitCode": None,
            "startTimeUTC": started_at.isoformat(),
            "deadline": deadline_at.isoformat(),
            "remainingSeconds": 0,
            "elapsedSeconds": elapsed,
            "stdout": _simulator_text(error.stdout),
            "stderr": _simulator_text(error.stderr),
        })
        raise
    except OSError:
        elapsed = time.monotonic() - started
        record({
            "event": "start-failed",
            "phase": phase,
            "command": " ".join(command),
            "argv": command,
            "exitCode": None,
            "startTimeUTC": started_at.isoformat(),
            "deadline": deadline_at.isoformat(),
            "remainingSeconds": max(timeout - elapsed, 0),
            "elapsedSeconds": elapsed,
            "stdout": "",
            "stderr": "",
        })
        raise
    elapsed = time.monotonic() - started
    record({
        "event": "completed",
        "phase": phase,
        "command": " ".join(command),
        "argv": command,
        "exitCode": completed.returncode,
        "startTimeUTC": started_at.isoformat(),
        "deadline": deadline_at.isoformat(),
        "remainingSeconds": max(timeout - elapsed, 0),
        "elapsedSeconds": elapsed,
        "stdout": _simulator_text(completed.stdout),
        "stderr": _simulator_text(completed.stderr),
    })
    return completed


def _simulator_log_root() -> Path | None:
    """Return the active external root for simulator diagnostics."""

    return _ACTIVE_SIMULATOR_LOG_ROOT


def _write_simulator_environment(destinations: dict[str, str]) -> None:
    """Export verified simulator UUIDs to Codemagic's step environment file."""

    environment_file = os.environ.get("CM_ENV")
    if not environment_file:
        raise SimulatorResolutionError("Codemagic environment file is unavailable")
    values: dict[str, str] = {}
    names = (
        (IOS_CORE_DEVICE, "ACE_IOS_CORE_SIMULATOR_UDID"),
        ("iPhone 17 Pro Max", "ACE_IOS_PRO_MAX_SIMULATOR_UDID"),
    )
    for device, key in names:
        destination = destinations.get(device)
        if not isinstance(destination, str):
            raise SimulatorResolutionError(f"verified simulator destination is missing: {device}")
        match = re.search(r"(?:^|,)id=([0-9A-Fa-f-]{36})(?:,|$)", destination)
        if match is None or SIMULATOR_UUID.fullmatch(match.group(1)) is None:
            raise SimulatorResolutionError(f"verified simulator UUID is invalid: {device}")
        values[key] = match.group(1)
    try:
        with Path(environment_file).open("a", encoding="utf-8") as stream:
            for key, value in values.items():
                stream.write(f"{key}={value}\n")
    except OSError as error:
        raise SimulatorResolutionError("Codemagic environment file could not be updated") from error


def _simctl_list(timeout: float | None = None) -> dict:
    if timeout is not None and timeout <= 0:
        raise SimulatorResolutionError(
            "simctl list has no verification time remaining",
            SIMULATOR_RESOLUTION_TIMEOUT_REASON,
        )
    effective_timeout = (
        SIMULATOR_VERIFICATION_SECONDS if timeout is None else timeout
    )
    try:
        completed = _run_simulator_command(
            _simulator_log_root(),
            "simctl-list-json",
            ["xcrun", "simctl", "list", "-j"],
            effective_timeout,
        )
    except subprocess.TimeoutExpired as error:
        raise SimulatorResolutionError(
            "simctl list -j timed out: argv=['xcrun', 'simctl', 'list', '-j']",
            SIMULATOR_RESOLUTION_TIMEOUT_REASON,
        ) from error
    if completed.returncode != 0:
        raise SimulatorResolutionError(
            f"simctl list -j failed with exit code {completed.returncode}: argv=['xcrun', 'simctl', 'list', '-j']"
        )
    try:
        data = json.loads(completed.stdout or "")
    except json.JSONDecodeError as error:
        raise SimulatorResolutionError("simctl list returned invalid JSON") from error
    if not isinstance(data, dict):
        raise SimulatorResolutionError("simctl list returned an invalid object")
    return data


def _xcode_version(timeout: float, root: Path | None = None) -> str:
    """Return the exact Xcode version selected by the provider image."""

    if timeout <= 0:
        raise SimulatorResolutionError(
            "xcode version query has no verification time remaining",
            SIMULATOR_RESOLUTION_TIMEOUT_REASON,
        )
    try:
        completed = _run_simulator_command(
            _simulator_log_root() if root is None else root,
            "preflight-xcode-version",
            ["xcodebuild", "-version"],
            timeout,
        )
    except subprocess.TimeoutExpired as error:
        raise SimulatorResolutionError(
            "xcodebuild -version timed out: argv=['xcodebuild', '-version']",
            SIMULATOR_RESOLUTION_TIMEOUT_REASON,
        ) from error
    except OSError as error:
        raise SimulatorResolutionError("xcodebuild version query could not start") from error
    if completed.returncode != 0:
        raise SimulatorResolutionError(
            f"xcodebuild -version failed with exit code {completed.returncode}: argv=['xcodebuild', '-version']"
        )
    for line in (completed.stdout or "").splitlines():
        match = re.fullmatch(r"Xcode (\d+(?:\.\d+)+)", line.strip())
        if match is not None:
            return match.group(1)
    raise SimulatorResolutionError("xcodebuild version query returned no Xcode version")


def _simctl_create(name: str, device_type: str, runtime: str, timeout: float) -> str:
    if timeout <= 0:
        raise SimulatorResolutionError(
            "simctl create has no verification time remaining",
            SIMULATOR_RESOLUTION_TIMEOUT_REASON,
        )
    try:
        completed = _run_simulator_command(
            _simulator_log_root(),
            "simctl-create",
            ["xcrun", "simctl", "create", name, device_type, runtime],
            timeout,
        )
    except subprocess.TimeoutExpired as error:
        raise SimulatorResolutionError(
            f"simctl create timed out: argv=['xcrun', 'simctl', 'create', '{name}', '{device_type}', '{runtime}']",
            SIMULATOR_RESOLUTION_TIMEOUT_REASON,
        ) from error
    if completed.returncode != 0:
        raise SimulatorResolutionError(
            f"simctl create failed for {name} with exit code {completed.returncode}"
        )
    identifier = (completed.stdout or "").strip()
    if SIMULATOR_UUID.fullmatch(identifier) is None:
        raise SimulatorResolutionError(
            f"simctl create returned an invalid UUID for {name}"
        )
    return identifier.upper()


def _simctl_boot(identifier: str, timeout: float) -> bool:
    """Request boot of one verified simulator without retaining command output."""

    if timeout <= 0:
        raise SimulatorResolutionError(
            "simctl boot has no verification time remaining",
            SIMULATOR_RESOLUTION_TIMEOUT_REASON,
        )
    try:
        completed = _run_simulator_command(
            _simulator_log_root(),
            "simctl-boot",
            ["xcrun", "simctl", "boot", identifier],
            timeout,
        )
    except subprocess.TimeoutExpired as error:
        raise SimulatorResolutionError(
            f"simctl boot timed out: argv=['xcrun', 'simctl', 'boot', '{identifier}']",
            SIMULATOR_RESOLUTION_TIMEOUT_REASON,
        ) from error
    except OSError as error:
        raise SimulatorResolutionError("simctl boot could not start") from error
    # simctl returns 149 when the verified device is already booted.
    if completed.returncode not in (0, 149):
        raise SimulatorResolutionError(
            f"simctl boot failed with exit code {completed.returncode}: argv=['xcrun', 'simctl', 'boot', '{identifier}']"
        )
    return completed.returncode == 0


def _simctl_bootstatus(identifier: str, timeout: float) -> None:
    """Require boot completion for one verified simulator without retaining output."""

    if timeout <= 0:
        raise SimulatorResolutionError(
            "simctl bootstatus has no verification time remaining",
            SIMULATOR_RESOLUTION_TIMEOUT_REASON,
        )
    try:
        completed = _run_simulator_command(
            _simulator_log_root(),
            "simctl-bootstatus",
            ["xcrun", "simctl", "bootstatus", identifier, "-b"],
            timeout,
        )
    except subprocess.TimeoutExpired as error:
        raise SimulatorResolutionError(
            f"simctl bootstatus timed out: argv=['xcrun', 'simctl', 'bootstatus', '{identifier}', '-b']",
            SIMULATOR_RESOLUTION_TIMEOUT_REASON,
        ) from error
    except OSError as error:
        raise SimulatorResolutionError("simctl bootstatus could not start") from error
    if completed.returncode != 0:
        raise SimulatorResolutionError(
            f"simctl bootstatus failed with exit code {completed.returncode}: argv=['xcrun', 'simctl', 'bootstatus', '{identifier}', '-b']"
        )


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
    verification_seconds: float | None = None,
    require_ready: bool = False,
    allow_create: bool = False,
) -> dict[str, str]:
    """Resolve exact iOS 26 simulator devices before test execution."""

    if len(names) != len(set(names)):
        raise SimulatorResolutionError("required simulator names must be unique")
    if type(require_ready) is not bool:
        raise SimulatorResolutionError("simulator readiness option is invalid")
    if type(allow_create) is not bool:
        raise SimulatorResolutionError("simulator creation option is invalid")
    if (
        verification_seconds is not None
        and (
            not isinstance(verification_seconds, (int, float))
            or not math.isfinite(verification_seconds)
            or verification_seconds <= 0
        )
    ):
        raise SimulatorResolutionError("simulator verification time is invalid")
    deadline = time.monotonic() + (
        SIMULATOR_VERIFICATION_SECONDS
        if verification_seconds is None else verification_seconds
    )
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
            if not allow_create:
                inventory = _controlled_simulator_snapshot(snapshot, names)
                _record_simulator_event(recorder, "missing-simulator", inventory)
                raise SimulatorResolutionError(
                    f"required simulator is missing and creation is disabled: {name}"
                )
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
    verified_identifiers = {
        name: _verify_simulator(snapshot, runtime, name, device_types[name], identifiers[name])
        for name in names
    }
    if require_ready:
        for name in names:
            identifier = verified_identifiers[name]
            remaining = deadline - time.monotonic()
            boot_started = _simctl_boot(identifier, remaining)
            if not boot_started:
                _record_simulator_event(recorder, "already-booted", name)
            remaining = deadline - time.monotonic()
            _simctl_bootstatus(identifier, remaining)
    destinations = {
        name: f"platform=iOS Simulator,id={verified_identifiers[name]}"
        for name in names
    }
    _record_simulator_event(recorder, "resolved-destinations", destinations)
    return destinations


def _simulator_preflight_action(error: SimulatorResolutionError) -> str:
    """Return a fixed operator action without storing command output."""

    if error.reason == SIMULATOR_RESOLUTION_TIMEOUT_REASON:
        return "Retry with the Codemagic mac_mini_m4 image and Xcode 26.4.1."
    if str(error).startswith("required Codemagic iOS tools"):
        return "Select the Codemagic mac_mini_m4 image with xcodebuild, xcrun, and Xcode 26.4.1."
    if "Xcode" in str(error) or str(error).startswith("xcodebuild"):
        return "Select the Codemagic mac_mini_m4 image with the exact Xcode 26.4.1 version."
    return (
        "Select the Codemagic Xcode 26.4.1 image with an available iOS 26 runtime "
        "and exact iPhone 17 and iPhone 17 Pro Max simulator device types."
    )


def _preflight_simctl_json(root: Path, phase: str, command: list[str], timeout: float) -> dict:
    """Run one JSON simctl inventory command and fail with its exact argv."""

    try:
        completed = _run_simulator_command(root, phase, command, timeout)
    except subprocess.TimeoutExpired as error:
        raise SimulatorResolutionError(
            f"{phase} timed out: argv={command}", SIMULATOR_RESOLUTION_TIMEOUT_REASON
        ) from error
    except OSError as error:
        raise SimulatorResolutionError(f"{phase} could not start: argv={command}") from error
    if completed.returncode != 0:
        raise SimulatorResolutionError(
            f"{phase} failed with exit code {completed.returncode}: argv={command}"
        )
    try:
        value = json.loads(completed.stdout or "")
    except json.JSONDecodeError as error:
        raise SimulatorResolutionError(f"{phase} returned invalid JSON: argv={command}") from error
    if not isinstance(value, dict):
        raise SimulatorResolutionError(f"{phase} returned an invalid object: argv={command}")
    return value


def _live_simulator_preflight(root: Path) -> dict[str, str]:
    """Record provider simulator availability before the live matrix starts."""

    global _ACTIVE_SIMULATOR_LOG_ROOT
    previous_root = _ACTIVE_SIMULATOR_LOG_ROOT
    _ACTIVE_SIMULATOR_LOG_ROOT = root

    diagnostic: dict[str, object] = {
        "status": "failed",
        "required": {
            "xcodeVersion": CODEMAGIC_XCODE_VERSION,
            "iosRuntimeMajor": IOS_RUNTIME_MAJOR,
            "devices": list(IOS_RELEASE_DEVICES),
        },
        "tools": {"xcodebuild": False, "xcrun": False},
        "xcode": {"available": False},
        "runtime": {"available": False},
        "devices": {name: {"available": False, "ready": False} for name in IOS_RELEASE_DEVICES},
        "events": [],
    }
    deadline = time.monotonic() + SIMULATOR_VERIFICATION_SECONDS

    def remaining_seconds() -> float:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise SimulatorResolutionError(
                "simulator preflight has no verification time remaining",
                SIMULATOR_RESOLUTION_TIMEOUT_REASON,
            )
        return remaining

    def record(name: str, value: object) -> None:
        events = diagnostic["events"]
        assert isinstance(events, list)
        events.append({"event": name, "value": value})
        if name == "selected-runtime" and isinstance(value, str):
            diagnostic["runtime"] = {"available": True, "identifier": value}
        elif name == "device-types" and isinstance(value, dict):
            devices = diagnostic["devices"]
            assert isinstance(devices, dict)
            for device, identifier in value.items():
                if device in devices and isinstance(identifier, str):
                    devices[device] = {"available": True, "ready": False, "identifier": identifier}
        elif name == "resolved-destinations" and isinstance(value, dict):
            devices = diagnostic["devices"]
            assert isinstance(devices, dict)
            for device in IOS_RELEASE_DEVICES:
                if isinstance(value.get(device), str):
                    entry = devices[device]
                    assert isinstance(entry, dict)
                    entry["ready"] = True

    try:
        tools = diagnostic["tools"]
        assert isinstance(tools, dict)
        tools["xcodebuild"] = shutil.which("xcodebuild") is not None
        tools["xcrun"] = shutil.which("xcrun") is not None
        if not tools["xcodebuild"] or not tools["xcrun"]:
            raise SimulatorResolutionError("required Codemagic iOS tools are unavailable")
        diagnostic["buildContext"] = {
            "CM_BUILD_ID": os.environ.get("CM_BUILD_ID", "unavailable"),
            "CM_BRANCH": os.environ.get("CM_BRANCH", "unavailable"),
            "macOSVersion": platform.mac_ver()[0] or "unavailable",
            "simulatorCommandPhase": "preflight",
        }
        observed_version = _xcode_version(remaining_seconds(), root=root)
        diagnostic["xcode"] = {"available": True, "version": observed_version}
        if observed_version != CODEMAGIC_XCODE_VERSION:
            raise SimulatorResolutionError("Codemagic Xcode version does not match the workflow")
        runtimes = _preflight_simctl_json(
            root, "preflight-simctl-list-runtimes",
            ["xcrun", "simctl", "list", "runtimes", "-j"],
            remaining_seconds(),
        )
        runtime = _select_ios_runtime(runtimes)
        diagnostic["runtime"] = {"available": True, "identifier": runtime}
        device_types = _preflight_simctl_json(
            root, "preflight-simctl-list-devicetypes",
            ["xcrun", "simctl", "list", "devicetypes", "-j"],
            remaining_seconds(),
        )
        device_identifiers = {
            name: _device_type_identifier(device_types, name)
            for name in IOS_RELEASE_DEVICES
        }
        diagnostic["devices"] = {
            name: {"available": True, "ready": False, "identifier": device_identifiers[name]}
            for name in IOS_RELEASE_DEVICES
        }
        _preflight_simctl_json(
            root, "preflight-simctl-list-devices-available",
            ["xcrun", "simctl", "list", "devices", "available", "-j"],
            remaining_seconds(),
        )
        destinations = resolve_ios_destinations(
            IOS_RELEASE_DEVICES,
            recorder=record,
            verification_seconds=remaining_seconds(),
            require_ready=True,
            allow_create=False,
        )
        _write_simulator_environment(destinations)
        diagnostic["status"] = "passed"
    except SimulatorResolutionError as error:
        diagnostic["failure"] = {
            "reason": _live_failure_reason(error),
            "action": _simulator_preflight_action(error),
        }
        _write_live_json_atomically(root, "simulator-resolution.json", diagnostic)
        _ACTIVE_SIMULATOR_LOG_ROOT = previous_root
        raise
    _write_live_json_atomically(root, "simulator-resolution.json", diagnostic)
    _ACTIVE_SIMULATOR_LOG_ROOT = previous_root
    return destinations


def _xcresult_counts(payload: object) -> tuple[int, int, int] | None:
    """Return passed, failed, and skipped counts from an xcresult summary."""

    counts, _ = _bounded_xcresult_counts(payload)
    return counts


def _bounded_xcresult_counts(
    payload: object,
) -> tuple[tuple[int, int, int] | None, bool]:
    """Return bounded result counts and whether JSON complexity exceeded the limit."""

    candidates: list[tuple[int, int, int]] = []
    pending = [payload]
    visited = 0
    while pending:
        value = pending.pop()
        visited += 1
        if visited > LIVE_RESULT_SUMMARY_MAX_NODES:
            return None, True
        if isinstance(value, dict):
            passed = value.get("passedTests")
            failed = value.get("failedTests")
            skipped = value.get("skippedTests", 0)
            if all(
                type(count) is int and 0 <= count <= LIVE_RESULT_SUMMARY_MAX_NODES
                for count in (passed, failed, skipped)
            ):
                candidates.append((passed, failed, skipped))
            pending.extend(value.values())
        elif isinstance(value, list):
            pending.extend(value)

    return max(candidates, key=lambda counts: sum(counts), default=None), False


def _bounded_live_file_text(
    root: Path, path: Path, maximum_bytes: int = LIVE_RESULT_SUMMARY_MAX_BYTES
) -> tuple[str, str | None]:
    """Read one bounded regular artifact without publishing its content."""

    try:
        if path.is_symlink():
            return "unsafe", None
        if not path.exists():
            return "missing", None
        if not path.is_file():
            return "unsafe", None
        if not path.resolve().is_relative_to(root.resolve()):
            return "unsafe", None
        if path.stat().st_size > maximum_bytes:
            return "oversized", None
        with path.open("rb") as handle:
            content = handle.read(maximum_bytes + 1)
        if len(content) > maximum_bytes:
            return "oversized", None
        return "available", content.decode("utf-8")
    except UnicodeDecodeError:
        return "unreadable", None
    except OSError:
        return "unreadable", None


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
        relative = path.relative_to(root).as_posix()
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


_PRIVATE_COLLECTION_SECRET = re.compile(
    rb"(?i)(?:[\"']?(?:password|token|authorization|credential|secret)[\"']?\s*[:=]\s*[\"']?)(?!\[redacted\])[^\s,}\]]+"
)
_PRIVATE_COLLECTION_CREDENTIAL_PREFIX = re.compile(
    rb"\b(?:gh[pousr]_[A-Za-z0-9_]+|github_pat_[A-Za-z0-9_]+|sk-[A-Za-z0-9_-]+)\b"
)
_PRIVATE_COLLECTION_ADJUDICATED_PNG_COMMAND = (
    "ios-release-iPhone 17 Pro Max-dark-testAllControlledScenariosShowExpectedStateAndAudit"
)
_PRIVATE_COLLECTION_ADJUDICATED_PNG_LOGICAL_NAME = "Controlled state — noActions — dark"
_PRIVATE_COLLECTION_ADJUDICATED_PNG_SHA256 = (
    "78747bc1422718c935af0de86487fff9982253528473bfa9dab4b396bbbc08c8"
)
_PRIVATE_COLLECTION_ADJUDICATED_PNG_BYTES = 215120
_PRIVATE_COLLECTION_ADJUDICATED_PNG_OFFSET = 54574
_PRIVATE_COLLECTION_ADJUDICATED_PNG_LENGTH = 7
_PRIVATE_COLLECTION_ADJUDICATED_PNG_STATUS = "adjudicated-known-png-false-positive"
_PRIVATE_COLLECTION_REAL_CLIENT = re.compile(rb"(?i)real[ _-]?client")
_PRIVATE_COLLECTION_UNREDACTED_USERNAME = re.compile(
    rb'(?i)(?:["\']?(?:username|user)["\']?)\s*[:=]\s*(?!["\']?\[redacted\]["\']?(?:\s|,|}|$))\S+'
)


def _private_collection_status(status: object) -> str:
    """Return one fixed private-collection state for safe progress records."""

    return status if status in LIVE_PRIVATE_COLLECTION_STATUSES else "incomplete"


def _private_collection_root() -> Path:
    """Create or validate the fixed private sibling root outside public artifacts."""

    root = LIVE_PRIVATE_COLLECTION_ROOT
    if root.is_symlink():
        raise ValueError("private collection root is unsafe")
    for parent in (root.parent, *root.parents):
        if parent.exists() and parent.is_symlink():
            raise ValueError("private collection root has a symlinked parent")
    root.mkdir(mode=0o700, parents=True, exist_ok=True)
    if root.is_symlink() or not root.is_dir():
        raise ValueError("private collection root is unsafe")
    return root


def _private_collection_relative(root: Path, path: Path) -> str:
    """Return a bounded archive suffix after link and traversal checks."""

    if path.is_symlink() or not path.is_file():
        raise ValueError("private collection source is not a regular file")
    for ancestor in (path.parent, *path.parents):
        if ancestor.is_symlink():
            raise ValueError("private collection source has a symlinked ancestor")
        if ancestor == root:
            break
    try:
        relative = path.resolve().relative_to(root.resolve())
    except (OSError, ValueError) as error:
        raise ValueError("private collection source escapes its root") from error
    if not relative.parts or any(
        not part or part in {".", ".."} or len(part) > 255
        or "\x00" in part or "\\" in part
        or not part.isascii() or any(ord(character) < 32 or ord(character) == 127 for character in part)
        for part in relative.parts
    ):
        raise ValueError("private collection source path is invalid")
    return relative.as_posix()


def _private_collection_regular_files(root: Path) -> list[Path]:
    """Select only bounded regular files below one already-approved source root."""

    if root.is_symlink() or not root.is_dir():
        raise ValueError("private collection source root is unsafe")
    selected: list[Path] = []
    for path in sorted(root.rglob("*")):
        if path.is_symlink():
            raise ValueError("private collection source contains a symlink")
        if path.is_dir():
            continue
        _private_collection_relative(root, path)
        selected.append(path)
        if len(selected) > LIVE_PRIVATE_COLLECTION_MAX_FILES:
            raise ValueError("private collection source count exceeds the limit")
    return selected


def _private_collection_credential_shape(content: bytes, match: re.Match[bytes]) -> str:
    """Classify the fixed match neighbourhood without retaining matched bytes."""

    if match.start() < 64 or len(content) - match.end() < 64:
        return "boundary-truncated"
    try:
        decoded = content[match.start() - 64:match.end() + 64].decode("utf-8")
    except UnicodeDecodeError:
        return "non-utf8"
    return "utf8-with-control" if any(
        not character.isprintable() and character not in "\t\n\r" for character in decoded
    ) else "utf8-printable"


def _private_collection_quarantine_permitted(
    archive_path: str, command: str, shape: str
) -> bool:
    """Permit only the approved unresolved binary result-data exception."""

    return (
        command in _live_command_names() - {"ios-negative-config"}
        and archive_path.startswith(f"records/commands/{command}/result.xcresult/Data/")
        and shape == "non-utf8"
    )


def _private_collection_adjudicated_png_scope(
    path: Path, archive_path: str, command: str
) -> bool:
    """Recognise the one attachment-export record that can need PNG adjudication."""

    prefix = f"records/commands/{_PRIVATE_COLLECTION_ADJUDICATED_PNG_COMMAND}/attachment-export/"
    return (
        command == _PRIVATE_COLLECTION_ADJUDICATED_PNG_COMMAND
        and archive_path == prefix + path.name
        and Path(archive_path).name == path.name
    )


def _private_collection_adjudicated_png_match_in_idat(
    content: bytes, match: re.Match[bytes]
) -> bool:
    """Confirm that the fixed match lies in PNG image data without retaining it."""

    offset = 8
    while offset + 12 <= len(content):
        length = int.from_bytes(content[offset:offset + 4], "big")
        end = offset + 12 + length
        if end > len(content):
            return False
        if content[offset + 4:offset + 8] == b"IDAT":
            data_start = offset + 8
            data_end = data_start + length
            if data_start <= match.start() and match.end() <= data_end:
                return True
        offset = end
    return False


def _private_collection_is_adjudicated_png_false_positive(
    source_root: Path,
    path: Path,
    archive_path: str,
    command: str,
    content: bytes,
    digest: str,
    raw_matches: list[tuple[str, re.Match[bytes]]],
) -> bool:
    """Permit one reviewed binary match only when all immutable evidence agrees."""

    if not _private_collection_adjudicated_png_scope(path, archive_path, command):
        return False
    entries = _attachment_export_entries(source_root, path.parent)
    if entries is None:
        return False
    names = [
        logical for logical, exported in entries
        if exported == path and (
            logical == _PRIVATE_COLLECTION_ADJUDICATED_PNG_LOGICAL_NAME
            or re.fullmatch(
                rf"{re.escape(_PRIVATE_COLLECTION_ADJUDICATED_PNG_LOGICAL_NAME)}_[0-9]+_[0-9A-Fa-f-]+(?:\.png)?",
                logical,
            )
        )
    ]
    if (
        len(names) != 1
        or len(content) != _PRIVATE_COLLECTION_ADJUDICATED_PNG_BYTES
        or digest != _PRIVATE_COLLECTION_ADJUDICATED_PNG_SHA256
        or len(raw_matches) != 1
    ):
        return False
    matcher, match = raw_matches[0]
    return (
        matcher == "credential-prefix"
        and match.start() == _PRIVATE_COLLECTION_ADJUDICATED_PNG_OFFSET
        and match.end() - match.start() == _PRIVATE_COLLECTION_ADJUDICATED_PNG_LENGTH
        and _private_collection_credential_shape(content, match) == "non-utf8"
        and _valid_png(path)
        and _private_collection_adjudicated_png_match_in_idat(content, match)
    )


def _private_collection_archive_path(archive_path: str, command: str) -> None:
    """Reject non-portable archive paths before they can reach private storage."""

    if (
        len(archive_path) > 1024
        or not archive_path.isascii()
        or "\\" in archive_path
        or any(ord(character) < 32 or ord(character) == 127 for character in archive_path)
    ):
        raise ValueError("private collection archive path is invalid")
    parts = archive_path.split("/")
    if any(not part or part in {".", ".."} or len(part) > 255 for part in parts):
        raise ValueError("private collection archive path is invalid")
    expected_prefix = (
        ["records", "setup", "simulator-operations"]
        if command == "setup" else ["records", "commands", command]
    )
    if parts[:len(expected_prefix)] != expected_prefix:
        raise ValueError("private collection archive path is invalid")


def _private_collection_file_metadata(
    source_root: Path, path: Path, archive_path: str, command: str
) -> tuple[int, str, str]:
    """Scan every private source byte and return only provenance-safe metadata."""

    _private_collection_relative(source_root, path)
    _private_collection_archive_path(archive_path, command)
    try:
        size = path.stat().st_size
    except OSError as error:
        raise ValueError("private collection source cannot be read") from error
    if size < 0 or size > LIVE_PRIVATE_COLLECTION_MAX_FILE_BYTES:
        raise ValueError("private collection source exceeds the size limit")
    try:
        with path.open("rb") as stream:
            content = stream.read(LIVE_PRIVATE_COLLECTION_MAX_FILE_BYTES + 1)
    except OSError as error:
        raise ValueError("private collection source cannot be read") from error
    if len(content) > LIVE_PRIVATE_COLLECTION_MAX_FILE_BYTES:
        raise ValueError("private collection source exceeds the size limit")
    if len(content) != size or path.stat().st_size != size:
        raise ValueError("private collection source changed during read")
    digest = hashlib.sha256(content).hexdigest()
    sensitive_key = r'(?:"(?:password|authorization|authorisation|keychain[ _-]?secret|credential|token)"|(?:password|authorization|authorisation|keychain[ _-]?secret|credential|token))'
    username_key = r'(?:"(?:username|user)"|(?:username|user))'
    forbidden = re.compile(rf"(?i){sensitive_key}\s*[:=]\s*\S+")
    unredacted_username = re.compile(
        rf'(?i){username_key}\s*[:=]\s*(?!"?\[redacted\]"?(?:\s|,|\}}|$))\S+'
    )
    if any(
        forbidden.search(text) or unredacted_username.search(text)
        for text in (
            content.decode("utf-8", errors="ignore"),
            content.decode("utf-16-le", errors="ignore"),
            content.decode("utf-16-be", errors="ignore"),
        )
    ):
        raise ValueError("private collection content was rejected")
    raw_matches = [
        (matcher, match)
        for matcher, pattern in (
            ("key-value", _PRIVATE_COLLECTION_SECRET),
            ("credential-prefix", _PRIVATE_COLLECTION_CREDENTIAL_PREFIX),
            ("real-client", _PRIVATE_COLLECTION_REAL_CLIENT),
            ("unredacted-username", _PRIVATE_COLLECTION_UNREDACTED_USERNAME),
        )
        for match in pattern.finditer(content)
    ]
    if _private_collection_is_adjudicated_png_false_positive(
        source_root, path, archive_path, command, content, digest, raw_matches
    ):
        return size, digest, _PRIVATE_COLLECTION_ADJUDICATED_PNG_STATUS
    if _private_collection_adjudicated_png_scope(path, archive_path, command) and raw_matches:
        raise ValueError("private collection content was rejected")
    quarantined = False
    for matcher, match in raw_matches:
        if (
            matcher == "credential-prefix"
            and _private_collection_quarantine_permitted(
                archive_path, command, _private_collection_credential_shape(content, match)
            )
        ):
            quarantined = True
            continue
        raise ValueError("private collection content was rejected")
    return (
        size,
        digest,
        "quarantined-pending-review" if quarantined else "complete",
    )


def _private_collection_sources(
    root: Path, planned: list[dict[str, object]], checks: list[dict], active: str | None
) -> tuple[list[tuple[Path, Path, str, str]], bool]:
    """Derive all collection sources from the exact planned and started commands."""

    planned_names = [item.get("name") for item in planned if isinstance(item, dict)]
    if (
        len(planned_names) != len(planned)
        or set(planned_names) != _live_command_names()
        or len(set(planned_names)) != len(planned_names)
    ):
        raise ValueError("private collection planned scope is invalid")
    started = [check.get("name") for check in checks if isinstance(check, dict)]
    if active in _live_command_names() and active not in started:
        started.append(active)
    if any(name not in planned_names for name in started) or len(set(started)) != len(started):
        raise ValueError("private collection started scope is invalid")
    complete = set(started) == set(planned_names)
    checks_by_name = {
        check["name"]: check for check in checks
        if isinstance(check, dict) and isinstance(check.get("name"), str)
    }
    sources: list[tuple[Path, Path, str, str]] = []
    for command in started:
        assert isinstance(command, str)
        prefix = f"records/commands/{command}"
        if command == "ios-negative-config":
            path = _safe_live_path(root, "ios-negative-config.log")
            if not path.exists() and not path.is_symlink():
                complete = False
            else:
                sources.append((root, path, f"{prefix}/log", command))
            continue
        for relative, archive_name in (
            (f"{command}.log", "log"),
            (f"{command}-summary.json", "summary.json"),
            (f"{command}-attachment-export.log", "attachment-export.log"),
            (f"{command}-diagnostic-attachment-export.log", "diagnostic-attachment-export.log"),
        ):
            path = _safe_live_path(root, relative)
            if not path.exists() and not path.is_symlink():
                if archive_name in {"log", "summary.json"}:
                    complete = False
            else:
                sources.append((root, path, f"{prefix}/{archive_name}", command))
        setting_logs = checks_by_name.get(command, {}).get("private_setting_logs")
        if command.startswith("ios-normal-settings-"):
            if not isinstance(setting_logs, list):
                complete = False
            else:
                expected_logs = _normal_setting_log_paths_from_records(command, setting_logs)
                if setting_logs != expected_logs:
                    raise ValueError("private collection setting-log scope is invalid")
                for relative in expected_logs:
                    path = _safe_live_path(root, relative)
                    if not path.exists() and not path.is_symlink():
                        complete = False
                    else:
                        sources.append((root, path, f"{prefix}/simulator-settings/{relative}", command))
        elif setting_logs is not None:
            raise ValueError("private collection setting-log scope is invalid")
        for relative, archive_name in (
            (f"{command}.xcresult", "result.xcresult"),
            (f"{command}-attachment-export", "attachment-export"),
            (f"{command}-diagnostic-attachment-export", "diagnostic-attachment-export"),
        ):
            directory = _safe_live_path(root, relative)
            if not directory.exists() and not directory.is_symlink():
                if archive_name == "result.xcresult":
                    complete = False
                continue
            files = _private_collection_regular_files(directory)
            manifest = directory / "manifest.json"
            if archive_name.endswith("attachment-export") and manifest in files:
                files = [manifest, *(path for path in files if path != manifest)]
            for path in files:
                suffix = _private_collection_relative(directory, path)
                sources.append((directory, path, f"{prefix}/{archive_name}/{suffix}", command))
    if len(sources) > LIVE_PRIVATE_COLLECTION_MAX_FILES:
        raise ValueError("private collection source count exceeds the limit")
    return sources, complete


def _private_collection_command_sources(
    root: Path, planned: list[dict[str, object]], check: dict
) -> list[tuple[Path, Path, str, str]]:
    """Get one completed command's required private records."""

    command = check.get("name")
    if not isinstance(command, str) or command not in _live_command_names():
        raise ValueError("private collection command is invalid")
    sources, _complete = _private_collection_sources(root, planned, [check], None)
    command_sources = [source for source in sources if source[3] == command]
    archive_paths = {source[2] for source in command_sources}
    prefix = f"records/commands/{command}/"
    required = {f"{prefix}log"}
    if command != "ios-negative-config":
        required.add(f"{prefix}summary.json")
        if not any(path.startswith(f"{prefix}result.xcresult/") for path in archive_paths):
            raise ValueError("private collection result bundle is empty")
        if command.startswith("ios-normal-settings-"):
            setting_logs = check.get("private_setting_logs")
            if not isinstance(setting_logs, list):
                raise ValueError("private collection setting logs are missing")
            required.update(f"{prefix}simulator-settings/{path}" for path in setting_logs)
    if not required.issubset(archive_paths):
        raise ValueError("private collection required record is missing")
    return command_sources


def _private_collection_candidate(manifest: dict[str, object]) -> dict[str, str]:
    """Return the verified candidate identity without environment data."""

    candidate = {
        key: manifest[key]
        for key in ("workflow", "repository", "commit", "branch", "buildId")
        if isinstance(manifest.get(key), str)
    }
    if set(candidate) != {"workflow", "repository", "commit", "branch", "buildId"}:
        raise ValueError("private collection candidate identity is incomplete")
    if candidate.get("workflow") != LIVE_WORKFLOW:
        raise ValueError("private collection candidate workflow is invalid")
    if "repository" in candidate and candidate["repository"] != LIVE_REPOSITORY:
        raise ValueError("private collection candidate repository is invalid")
    if "commit" in candidate and re.fullmatch(r"[0-9a-f]{40}", candidate["commit"]) is None:
        raise ValueError("private collection candidate commit is invalid")
    if "branch" in candidate and candidate["branch"] != LIVE_BRANCH:
        raise ValueError("private collection candidate branch is invalid")
    if "buildId" in candidate and re.fullmatch(r"[A-Za-z0-9_-]{1,128}", candidate["buildId"]) is None:
        raise ValueError("private collection candidate build is invalid")
    return candidate


def _verify_private_completed_command(
    root: Path, planned: list[dict[str, object]], check: dict
) -> None:
    """Verify passed command records before another command can start."""

    command = check.get("name")
    expected = next((item.get("expectedTests") for item in planned if item.get("name") == command), None)
    if check.get("exit") != 0 or not isinstance(expected, int):
        return
    summary = _safe_live_path(root, f"{command}-summary.json")
    try:
        counts, _over_complex = _bounded_xcresult_counts(json.loads(summary.read_text(encoding="utf-8")))
    except (OSError, ValueError, json.JSONDecodeError, RecursionError) as error:
        raise ValueError("private collection summary is invalid") from error
    if counts != (expected, 0, 0):
        raise ValueError("private collection test counts are invalid")
    expected_images = _expected_logical_screenshot_names(command)
    screenshots = check.get("screenshots")
    if not isinstance(screenshots, list) or len(screenshots) != len(expected_images):
        raise ValueError("private collection screenshot inventory is invalid")
    for relative in screenshots:
        if not isinstance(relative, str):
            raise ValueError("private collection screenshot path is invalid")
        image = _safe_live_path(root, f"{LIVE_REVIEW_STAGE}/{relative}")
        if image.is_symlink() or not image.is_file() or not _valid_png(image):
            raise ValueError("private collection screenshot is invalid")


def _private_collection_preserved_root(private_root: Path) -> Path:
    """Create the bounded command-copy directory below fixed private storage."""

    root = private_root / LIVE_PRIVATE_PRESERVED_DIRECTORY
    if root.is_symlink() or (root.exists() and not root.is_dir()):
        raise ValueError("private collection preserved root is unsafe")
    root.mkdir(mode=0o700, exist_ok=True)
    return root


def _private_collection_preserved_sources(
    private_root: Path, command: str, candidate: dict[str, str]
) -> list[tuple[Path, Path, str, str]]:
    """Read and verify one immutable command-copy inventory."""

    command_root = _private_collection_preserved_root(private_root) / command
    inventory_path = command_root / "inventory.json"
    if command_root.is_symlink() or inventory_path.is_symlink() or not inventory_path.is_file():
        raise ValueError("private collection preserved inventory is missing")
    try:
        inventory = json.loads(inventory_path.read_text(encoding="utf-8"))
    except (OSError, ValueError, json.JSONDecodeError) as error:
        raise ValueError("private collection preserved inventory is unreadable") from error
    if (
        not isinstance(inventory, dict)
        or inventory.get("command") != command
        or inventory.get("candidate") != candidate
        or not isinstance(inventory.get("records"), list)
    ):
        raise ValueError("private collection preserved inventory is invalid")
    sources: list[tuple[Path, Path, str, str]] = []
    for record in inventory["records"]:
        if (
            not isinstance(record, dict)
            or set(record) != {"relativePath", "size", "sha256", "scannerStatus"}
            or not isinstance(record["relativePath"], str)
            or not isinstance(record["size"], int)
            or not isinstance(record["sha256"], str)
            or record["scannerStatus"] not in {
                "complete", "quarantined-pending-review",
                _PRIVATE_COLLECTION_ADJUDICATED_PNG_STATUS,
            }
        ):
            raise ValueError("private collection preserved record is invalid")
        archive_path = record["relativePath"]
        suffix = archive_path.removeprefix(f"records/commands/{command}/")
        source_command = command
        if suffix == archive_path and command == "ios-65-unit":
            suffix = archive_path.removeprefix("records/setup/")
            source_command = "setup"
            suffix = f"setup/{suffix}"
        if suffix == archive_path:
            raise ValueError("private collection preserved path is invalid")
        path = command_root / suffix
        size, digest, scanner_status = _private_collection_file_metadata(
            command_root, path, archive_path, source_command
        )
        if (size, digest, scanner_status) != (
            record["size"], record["sha256"], record["scannerStatus"]
        ):
            raise ValueError("private collection preserved record changed")
        sources.append((command_root, path, archive_path, source_command))
    if not sources or len({source[2] for source in sources}) != len(sources):
        raise ValueError("private collection preserved inventory is incomplete")
    paths = {source[2] for source in sources}
    prefix = f"records/commands/{command}/"
    required = {f"{prefix}log"}
    if command != "ios-negative-config":
        required.add(f"{prefix}summary.json")
        if not any(path.startswith(f"{prefix}result.xcresult/") for path in paths):
            raise ValueError("private collection preserved result bundle is empty")
        if command.startswith("ios-normal-settings-"):
            setting_prefix = f"{prefix}simulator-settings/"
            records = [source[2].removeprefix(setting_prefix) for source in sources if source[2].startswith(setting_prefix)]
            expected = _normal_setting_log_paths_from_records(command, records)
            if records != expected:
                raise ValueError("private collection preserved setting logs are invalid")
            required.update(setting_prefix + record for record in records)
    if not required.issubset(paths):
        raise ValueError("private collection preserved record is missing")
    if not any(path.startswith(f"{prefix}simulator-operations/") for path in paths):
        raise ValueError("private collection preserved simulator operations are missing")
    return sources


def _preserve_private_command_records(
    root: Path,
    planned: list[dict[str, object]],
    check: dict,
    manifest: dict[str, object],
) -> None:
    """Copy, scan, and verify one command before another command can start."""

    command = check.get("name")
    if not isinstance(command, str):
        raise ValueError("private collection command is invalid")
    candidate = _private_collection_candidate(manifest)
    private_root = _private_collection_root()
    command_root = _private_collection_preserved_root(private_root) / command
    if command_root.exists() or command_root.is_symlink():
        _private_collection_preserved_sources(private_root, command, candidate)
        return
    sources = _private_collection_command_sources(root, planned, check)
    operations = _safe_live_path(root, "simulator-operations")
    operation_files = _private_collection_regular_files(operations)
    if not operation_files:
        raise ValueError("private collection simulator operations are missing")
    sources.extend(
        (operations, path, f"records/commands/{command}/simulator-operations/{_private_collection_relative(operations, path)}", command)
        for path in operation_files
    )
    if len(sources) > LIVE_PRIVATE_COLLECTION_MAX_FILES:
        raise ValueError("private collection source count exceeds the limit")
    stage = _private_collection_preserved_root(private_root) / f".{command}.tmp"
    if stage.exists() or stage.is_symlink():
        raise ValueError("private collection preservation stage is unsafe")
    records: list[dict[str, object]] = []
    try:
        stage.mkdir(mode=0o700)
        for source_root, source, archive_path, source_command in sources:
            size, digest, scanner_status = _private_collection_file_metadata(
                source_root, source, archive_path, source_command
            )
            suffix = archive_path.removeprefix(f"records/commands/{command}/")
            if suffix == archive_path and source_command == "setup":
                suffix = "setup/" + archive_path.removeprefix("records/setup/")
            if suffix == archive_path:
                raise ValueError("private collection preserved path is invalid")
            target = stage / suffix
            target.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
            shutil.copyfile(source, target)
            copied = _private_collection_file_metadata(
                stage, target, archive_path, source_command
            )
            if copied != (size, digest, scanner_status):
                raise ValueError("private collection preserved copy changed")
            records.append({
                "relativePath": archive_path, "size": size, "sha256": digest,
                "scannerStatus": scanner_status,
            })
        inventory = json.dumps({
            "candidate": candidate, "command": command, "records": records,
        }, indent=2, sort_keys=True).encode("utf-8") + b"\n"
        (stage / "inventory.json").write_bytes(inventory)
        os.replace(stage, command_root)
        _private_collection_preserved_sources(private_root, command, candidate)
    except (OSError, ValueError, json.JSONDecodeError):
        if stage.exists() and stage.is_dir() and not stage.is_symlink():
            shutil.rmtree(stage)
        raise


def _verify_private_collection_archive(
    archive: Path, expected: dict[str, tuple[int, str]]
) -> None:
    """Verify every archived member has the exact selected original bytes."""

    try:
        with tarfile.open(archive, "r:gz") as input_archive:
            members = input_archive.getmembers()
            names = [member.name for member in members]
            if len(names) != len(set(names)) or set(names) != set(expected):
                raise ValueError("private collection archive members are invalid")
            for member in members:
                if not member.isreg() or member.size != expected[member.name][0]:
                    raise ValueError("private collection archive member is invalid")
                stream = input_archive.extractfile(member)
                if stream is None:
                    raise ValueError("private collection archive member is unreadable")
                digest = hashlib.sha256()
                for chunk in iter(lambda: stream.read(64 * 1024), b""):
                    digest.update(chunk)
                if digest.hexdigest() != expected[member.name][1]:
                    raise ValueError("private collection archive checksum is invalid")
    except (OSError, tarfile.TarError) as error:
        raise ValueError("private collection archive validation failed") from error


def _finalise_private_live_collection(
    root: Path,
    planned: list[dict[str, object]],
    checks: list[dict],
    active: str | None,
    manifest: dict[str, object],
) -> str:
    """Archive exact available original records, without publishing their contents."""

    private_root: Path | None = None
    temporary: Path | None = None
    try:
        private_root = _private_collection_root()
        archive = private_root / LIVE_PRIVATE_COLLECTION_ARCHIVE
        if archive.is_symlink() or (archive.exists() and not archive.is_file()):
            raise ValueError("private collection archive path is unsafe")
        temporary = private_root / f".{LIVE_PRIVATE_COLLECTION_ARCHIVE}.tmp"
        if temporary.exists() or temporary.is_symlink():
            if temporary.is_file() and not temporary.is_symlink():
                temporary.unlink()
            else:
                raise ValueError("private collection temporary path is unsafe")
        if not planned:
            return "incomplete"
        planned_names = [item.get("name") for item in planned if isinstance(item, dict)]
        if len(planned_names) != len(planned) or set(planned_names) != _live_command_names():
            raise ValueError("private collection planned scope is invalid")
        completed_commands = {
            check.get("name") for check in checks
            if isinstance(check, dict) and isinstance(check.get("name"), str)
        }
        if any(command not in planned_names for command in completed_commands):
            raise ValueError("private collection completed scope is invalid")
        complete = active is None and completed_commands == set(planned_names)
        candidate = _private_collection_candidate(manifest)
        checks_by_name = {
            check["name"] for check in checks
            if isinstance(check, dict) and isinstance(check.get("name"), str)
        }
        for command in sorted(completed_commands):
            check = next(item for item in checks if item.get("name") == command)
            _preserve_private_command_records(root, planned, check, manifest)
        sources = [
            source
            for command in sorted(checks_by_name)
            for source in _private_collection_preserved_sources(private_root, command, candidate)
        ]
        entries: list[dict[str, object]] = []
        expected: dict[str, tuple[int, str]] = {}
        for source_root, path, archive_path, command in sources:
            size, digest, scanner_status = _private_collection_file_metadata(
                source_root, path, archive_path, command
            )
            if archive_path in expected:
                raise ValueError("private collection archive path is duplicated")
            expected[archive_path] = (size, digest)
            entries.append({
                "relativePath": archive_path,
                "producingCommand": command,
                "commandState": "complete" if command in completed_commands else "incomplete",
                "size": size,
                "sha256": digest,
                "scannerStatus": scanner_status,
            })
        if not entries:
            if active is not None or not complete:
                return "incomplete"
            raise ValueError("private collection has no bounded source set")
        if len(entries) > LIVE_PRIVATE_COLLECTION_MAX_FILES:
            raise ValueError("private collection source count exceeds the limit")
        if sum(item["size"] for item in entries) > LIVE_PRIVATE_COLLECTION_MAX_ARCHIVE_BYTES:
            raise ValueError("private collection source size exceeds the limit")
        quarantined = any(item["scannerStatus"] == "quarantined-pending-review" for item in entries)
        status = "quarantined-pending-review" if quarantined else "complete" if complete else "incomplete"
        inventory = json.dumps({
            "scope": "MCX-19-full-matrix-private-records",
            "collectionStatus": status,
            "candidate": {
                key: manifest[key] for key in ("workflow", "repository", "commit", "branch", "buildId")
                if isinstance(manifest.get(key), str)
            },
            "plannedCommandCount": len(planned),
            "startedCommandCount": len(completed_commands | ({active} if active in planned_names else set())),
            "records": entries,
        }, indent=2, sort_keys=True).encode("utf-8") + b"\n"
        inventory_path = "records/collection-inventory.json"
        expected[inventory_path] = (len(inventory), hashlib.sha256(inventory).hexdigest())
        with tarfile.open(temporary, "w:gz", format=tarfile.PAX_FORMAT) as output:
            for source_root, path, archive_path, command in sources:
                size, digest, scanner_status = _private_collection_file_metadata(
                    source_root, path, archive_path, command
                )
                if expected[archive_path] != (size, digest):
                    raise ValueError("private collection source changed during packaging")
                info = output.gettarinfo(str(path), arcname=archive_path)
                if not info.isreg():
                    raise ValueError("private collection archive record is unsafe")
                info.uid = info.gid = 0
                info.uname = info.gname = ""
                info.mtime = 0
                with path.open("rb") as stream:
                    output.addfile(info, stream)
            inventory_info = tarfile.TarInfo(inventory_path)
            inventory_info.size = len(inventory)
            inventory_info.mode = 0o600
            inventory_info.mtime = 0
            output.addfile(inventory_info, io.BytesIO(inventory))
        _verify_private_collection_archive(temporary, expected)
        os.replace(temporary, archive)
        return status
    except (OSError, ValueError, tarfile.TarError):
        if private_root is not None:
            diagnostic = private_root / "retention-diagnostic.json"
            command = active if active in _live_command_names() else "collection"
            try:
                diagnostic.write_text(json.dumps({
                    "phase": "final-packaging",
                    "category": LIVE_PRIVATE_COLLECTION_FAILURE_REASON,
                    "command": command,
                }, sort_keys=True) + "\n", encoding="utf-8")
            except OSError:
                pass
        if temporary is not None and temporary.is_file() and not temporary.is_symlink():
            temporary.unlink(missing_ok=True)
        return "failed"


def _expected_logical_screenshot_names(name: str) -> tuple[str, ...]:
    """Return the complete, fixed attachment inventory for one UI command."""

    appearance = "dark" if "-dark-" in name or name.endswith("-dark") else "light"
    if name.endswith("-testBothAppearances"):
        return tuple(f"Fictional release — forced-{value}" for value in ("light", "dark"))
    if name.endswith("-testLaunchShowsSafeConfigurationState"):
        return (f"Controlled state — configuration — {appearance}",)
    if name.endswith("-testSignInPasswordFieldIsSecure"):
        return (f"Controlled state — signIn — {appearance}",)
    if name.endswith("-testFictionalReleaseHasApprovedCopyControls"):
        return (
            *(f"Release detail — {field} — {appearance}" for field in LIVE_RELEASE_DETAIL_FIELDS),
            f"Fictional release — approved-controls — {appearance}",
            f"Controlled state — copyConfirmation — {appearance}",
        )
    if name.endswith("-testAllControlledScenariosShowExpectedStateAndAudit"):
        return tuple(f"Controlled state — {scenario} — {appearance}" for scenario in LIVE_CONTROLLED_SCENARIOS)
    if name.endswith("-testReleaseOrientationHooks"):
        return tuple(f"Release — {orientation} — {appearance}" for orientation in ("landscape-left", "portrait"))
    if name.startswith("ios-normal-settings-"):
        normal = f"normal-device-settings-{appearance}"
        return (
            *(f"Release detail — {field} — {normal}" for field in LIVE_RELEASE_DETAIL_FIELDS),
            f"Fictional release — normal-device-settings — {appearance}",
        )
    return ()


def _valid_png(path: Path) -> bool:
    """Validate supported iOS screenshot PNG pixels without publishing image content."""

    try:
        if path.stat().st_size > LIVE_ARTIFACT_MAX_BYTES:
            return False
        data = path.read_bytes()
    except OSError:
        return False
    if len(data) < 45 or not data.startswith(b"\x89PNG\r\n\x1a\n"):
        return False
    offset, seen_ihdr, seen_idat = 8, False, False
    width = height = channels = bit_depth = 0
    compressed = bytearray()
    while offset < len(data):
        if offset + 12 > len(data):
            return False
        size = int.from_bytes(data[offset:offset + 4], "big")
        kind = data[offset + 4:offset + 8]
        end = offset + 12 + size
        if end > len(data):
            return False
        chunk = data[offset + 8:offset + 8 + size]
        checksum = int.from_bytes(data[offset + 8 + size:end], "big")
        if zlib.crc32(kind + chunk) & 0xffffffff != checksum:
            return False
        if kind == b"IHDR":
            if seen_ihdr or seen_idat or size != 13:
                return False
            width, height = int.from_bytes(chunk[:4], "big"), int.from_bytes(chunk[4:8], "big")
            bit_depth, colour_type, compression, filtering, interlace = chunk[8:]
            channels = {2: 3, 6: 4}.get(colour_type, 0)
            if (
                not 1 <= width <= 10000 or not 1 <= height <= 10000
                or bit_depth not in {8, 16} or not channels
                or compression != 0 or filtering != 0 or interlace != 0
            ):
                return False
            seen_ihdr = True
        elif kind == b"IDAT":
            if not seen_ihdr:
                return False
            seen_idat = True
            compressed.extend(chunk)
        elif kind == b"IEND":
            if not (seen_ihdr and seen_idat and size == 0 and end == len(data)):
                return False
            row_bytes = width * channels * (bit_depth // 8)
            expected = height * (row_bytes + 1)
            if expected > LIVE_ARTIFACT_MAX_BYTES:
                return False
            try:
                decoder = zlib.decompressobj()
                pixels = decoder.decompress(compressed, expected + 1)
            except zlib.error:
                return False
            if (
                not decoder.eof or decoder.unused_data or decoder.unconsumed_tail
                or len(pixels) != expected
            ):
                return False
            return all(pixels[index] <= 4 for index in range(0, len(pixels), row_bytes + 1))
        elif kind[:1].isupper():
            return False
        offset = end
    return False


def _attachment_export_entries(root: Path, export_directory: Path) -> list[tuple[str, Path]] | None:
    """Map Xcode's exported names to attachment names through its manifest JSON."""

    state, content = _bounded_live_file_text(root, export_directory / "manifest.json")
    if state != "available" or content is None:
        return None
    try:
        payload = json.loads(content)
    except (ValueError, RecursionError):
        return None
    if not isinstance(payload, list):
        return None
    entries: list[tuple[str, Path]] = []
    for test in payload:
        if not isinstance(test, dict) or not isinstance(test.get("attachments"), list):
            return None
        for attachment in test["attachments"]:
            if not isinstance(attachment, dict):
                return None
            logical = attachment.get("suggestedHumanReadableName")
            exported = attachment.get("exportedFileName")
            if not isinstance(logical, str) or not isinstance(exported, str):
                return None
            path = export_directory / exported
            if Path(exported).name != exported or not path.resolve(strict=False).is_relative_to(export_directory.resolve()):
                return None
            entries.append((logical, path))
    return entries


def _retain_live_screenshots(
    name: str, cwd: Path, root: Path, result_path: Path
) -> tuple[list[str] | None, str | None]:
    """Stage exact named fictional PNG attachments for publication after final checks."""

    expected = _expected_logical_screenshot_names(name)
    if not expected:
        return [], None
    export_directory = _safe_live_path(root, f"{name}-attachment-export")
    log_path = _safe_live_path(root, f"{name}-attachment-export.log")
    if export_directory.exists() or export_directory.is_symlink():
        return None, "attachment-invalid"
    export_result = _run_live_command(
        f"{name}-attachments",
        ["xcrun", "xcresulttool", "export", "attachments", "--path", str(result_path),
         "--output-path", str(export_directory)], cwd, {}, log_path,
    )
    if export_result[0] != 0:
        return None, "attachment-export-failed"
    entries = _attachment_export_entries(root, export_directory)
    if entries is None:
        return None, "attachment-invalid"
    by_name: dict[str, Path] = {}
    for logical, path in entries:
        matched = next((required for required in expected if logical == required or re.fullmatch(
            rf"{re.escape(required)}_[0-9]+_[0-9A-Fa-f-]+(?:\.png)?", logical
        )), None)
        if matched is None or matched in by_name:
            return None, "attachment-missing"
        by_name[matched] = path
    if set(by_name) != set(expected) or len(entries) != len(expected):
        return None, "attachment-missing"
    target_directory = _safe_live_path(root, f"{LIVE_REVIEW_STAGE}/{LIVE_SCREENSHOT_DIRECTORY}/{name}")
    try:
        target_directory.mkdir(parents=True, exist_ok=False)
        retained: list[str] = []
        for number, logical in enumerate(expected, 1):
            source = by_name[logical]
            if source.is_symlink() or not source.is_file() or source.stat().st_size > LIVE_ARTIFACT_MAX_BYTES or not _valid_png(source):
                return None, "attachment-invalid"
            target = target_directory / f"{number:02d}.png"
            shutil.copyfile(source, target)
            retained.append(target.relative_to(_safe_live_path(root, LIVE_REVIEW_STAGE)).as_posix())
    except OSError:
        return None, "attachment-invalid"
    return retained, None


def _retain_live_diagnostic_images(
    name: str,
    cwd: Path,
    root: Path,
    result_path: Path,
    collection_exits: dict[str, int | None] | None = None,
) -> tuple[str, list[dict[str, str]], list[str], str | None, bool]:
    """Retain available valid fictional attachments for a failed XCTest command.

    These images are diagnostic records only.  They never enter the accepted review
    stage, and a partial set never changes the failed command outcome.
    """

    expected = _expected_logical_screenshot_names(name)
    if not expected:
        return "available", [], [], None, False
    try:
        if (
            not result_path.is_dir()
            or result_path.is_symlink()
            or not result_path.resolve().is_relative_to(root.resolve())
        ):
            return "result-bundle-unavailable", [], list(expected), None, False
    except OSError:
        return "result-bundle-unavailable", [], list(expected), None, False
    export_directory = _safe_live_path(root, f"{name}-diagnostic-attachment-export")
    export_log = _safe_live_path(root, f"{name}-diagnostic-attachment-export.log")
    if export_directory.exists() or export_directory.is_symlink():
        return "attachment-invalid", [], list(expected), "attachment-invalid", False
    export_result = _run_live_command(
        f"{name}-diagnostic-attachments",
        [
            "xcrun", "xcresulttool", "export", "attachments", "--path",
            str(result_path), "--output-path", str(export_directory),
        ],
        cwd,
        {},
        export_log,
    )
    if collection_exits is not None:
        collection_exits["attachmentExport"] = _published_process_exit(
            getattr(export_result, "process_exit", None)
        )
    if export_result[0] != 0:
        return "attachment-export-failed", [], list(expected), None, False
    entries = _attachment_export_entries(root, export_directory)
    if entries is None:
        return "attachment-invalid", [], list(expected), "attachment-invalid", False
    grouped: dict[str, list[Path]] = {}
    for logical, source in entries:
        matched = next((candidate for candidate in expected if logical == candidate or re.fullmatch(
            rf"{re.escape(candidate)}_[0-9]+_[0-9A-Fa-f-]+(?:\.png)?", logical
        )), None)
        if matched is not None:
            grouped.setdefault(matched, []).append(source)
    sources: dict[str, Path] = {}
    ambiguous = {logical for logical, sources_for_logical in grouped.items() if len(sources_for_logical) != 1}
    invalid = False
    for matched, sources_for_logical in grouped.items():
        if matched in ambiguous:
            continue
        source = sources_for_logical[0]
        try:
            valid = (
                not source.is_symlink()
                and source.is_file()
                and source.resolve().is_relative_to(export_directory.resolve())
                and source.stat().st_size <= LIVE_ARTIFACT_MAX_BYTES
                and _valid_png(source)
            )
        except OSError:
            valid = False
        if valid:
            sources[matched] = source
        else:
            invalid = True
    missing = [logical for logical in expected if logical not in sources]
    if not sources:
        problem = "attachment-ambiguous" if ambiguous else "attachment-invalid" if invalid else None
        return "attachment-missing", [], missing, problem, False
    target = _safe_live_path(root, f"{LIVE_DIAGNOSTIC_IMAGE_DIRECTORY}/{name}")
    stage = _safe_live_path(root, f".diagnostic-image-stage-{name}")
    if target.exists() or target.is_symlink() or stage.exists() or stage.is_symlink():
        return "attachment-invalid", [], list(expected), "attachment-invalid", False
    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        stage.mkdir(parents=True, exist_ok=False)
        records: list[dict[str, str]] = []
        for number, logical in enumerate(expected, 1):
            source = sources.get(logical)
            if source is None:
                continue
            filename = f"{number:02d}.png"
            staged = stage / filename
            shutil.copyfile(source, staged)
            if not _valid_png(staged):
                raise OSError("diagnostic image validation failed")
            records.append({
                "logicalName": logical,
                "path": f"{LIVE_DIAGNOSTIC_IMAGE_DIRECTORY}/{name}/{filename}",
                "sha256": hashlib.sha256(staged.read_bytes()).hexdigest(),
            })
        _scan_live_artifacts(stage)
        os.replace(stage, target)
    except (OSError, ValueError):
        if stage.exists() and stage.is_dir() and not stage.is_symlink():
            try:
                for path in stage.iterdir():
                    path.unlink(missing_ok=True)
                stage.rmdir()
            except OSError:
                pass
        return "attachment-invalid", [], list(expected), "attachment-invalid", True
    problem = "attachment-ambiguous" if ambiguous else "attachment-invalid" if invalid else None
    return ("available" if not missing else "partial"), records, missing, problem, False


def _diagnostic_retention_fields(
    name: str,
    cwd: Path,
    root: Path,
    result_path: Path,
    collection_exits: dict[str, int | None] | None = None,
) -> dict[str, object]:
    """Keep diagnostic retention failures separate from native command failures."""

    status, images, missing, problem, retention_failed = _retain_live_diagnostic_images(
        name, cwd, root, result_path, collection_exits
    )
    fields: dict[str, object] = {
        "diagnostic_image_status": status,
        "diagnostic_images": images,
        "missing_diagnostic_image_names": missing,
        "diagnostic_attachment_problem": problem,
    }
    if retention_failed:
        fields["safe_image_retention_failure"] = True
    return fields


def _retain_completed_review_images(root: Path, checks: list[dict]) -> str | None:
    """Copy each completed success image to the safe diagnostic path atomically."""

    stage_root = _safe_live_path(root, LIVE_REVIEW_STAGE)
    for check in checks:
        if check.get("safe_images"):
            continue
        name = check.get("name")
        screenshots = check.get("screenshots")
        expected = _expected_logical_screenshot_names(name) if isinstance(name, str) else ()
        if not expected:
            continue
        if check.get("exit") != 0 and check.get("reason") in {
            "command-nonzero", "command-timeout", "command-start-failed",
        }:
            continue
        if screenshots is None:
            if check.get("exit") != 0:
                continue
            return "safe-image-retention-failed"
        if not isinstance(screenshots, list) or len(screenshots) != len(expected):
            return "safe-image-retention-failed"
        target = _safe_live_path(root, f"{LIVE_DIAGNOSTIC_IMAGE_DIRECTORY}/{name}")
        stage = _safe_live_path(root, f".safe-image-stage-{name}")
        if target.exists() or target.is_symlink() or stage.exists() or stage.is_symlink():
            return "safe-image-retention-failed"
        records: list[dict[str, str]] = []
        try:
            stage.mkdir(parents=True, exist_ok=False)
            for number, (logical, relative) in enumerate(zip(expected, screenshots), 1):
                if not isinstance(relative, str):
                    raise ValueError("review screenshot path is invalid")
                source = _safe_live_path(stage_root, relative)
                if (
                    source.is_symlink()
                    or not source.is_file()
                    or source.stat().st_size > LIVE_ARTIFACT_MAX_BYTES
                    or not _valid_png(source)
                ):
                    raise ValueError("review screenshot is invalid")
                filename = f"{number:02d}.png"
                copied = stage / filename
                shutil.copyfile(source, copied)
                if not _valid_png(copied):
                    raise ValueError("review screenshot copy is invalid")
                records.append({
                    "logicalName": logical,
                    "path": f"{LIVE_DIAGNOSTIC_IMAGE_DIRECTORY}/{name}/{filename}",
                    "sha256": hashlib.sha256(copied.read_bytes()).hexdigest(),
                })
            _scan_live_artifacts(stage)
            target.parent.mkdir(parents=True, exist_ok=True)
            os.replace(stage, target)
        except (OSError, ValueError):
            if stage.exists() and stage.is_dir() and not stage.is_symlink():
                for path in stage.iterdir():
                    path.unlink(missing_ok=True)
                stage.rmdir()
            return "safe-image-retention-failed"
        check["safe_images"] = records
    return None


_NORMAL_SETTING_LOG_OPERATIONS = (
    ("appearance", "before-query"),
    ("content_size", "before-query"),
    ("appearance", "requested-set"),
    ("appearance", "requested-query"),
    ("content_size", "requested-set"),
    ("content_size", "requested-query"),
    ("appearance", "restore-set"),
    ("appearance", "restore-query"),
    ("content_size", "restore-set"),
    ("content_size", "restore-query"),
)


def _normal_setting_log_paths(name: str, identifier: str) -> list[str]:
    """Return the exact private log paths for one planned setting command."""

    if (
        name not in _live_command_names()
        or not name.startswith("ios-normal-settings-")
        or re.fullmatch(r"[0-9A-Fa-f-]{36}", identifier) is None
    ):
        raise ValueError("normal setting log scope is invalid")
    return [
        f"simctl-{name}-{identifier}-{setting}-{operation}.log"
        for setting, operation in _NORMAL_SETTING_LOG_OPERATIONS
    ]


def _normal_setting_log_paths_from_records(name: str, records: list[object]) -> list[str]:
    """Validate setting-log provenance and return its fixed expected paths."""

    if (
        len(records) != len(_NORMAL_SETTING_LOG_OPERATIONS)
        or any(not isinstance(record, str) for record in records)
        or len(set(records)) != len(records)
    ):
        raise ValueError("private collection setting-log scope is invalid")
    first = records[0]
    prefix = f"simctl-{name}-"
    if not isinstance(first, str) or not first.startswith(prefix):
        raise ValueError("private collection setting-log path is invalid")
    identifier = first[len(prefix):].split("-appearance-before-query.log", 1)[0]
    expected = _normal_setting_log_paths(name, identifier)
    if records != expected:
        raise ValueError("private collection setting-log path is invalid")
    return expected


def _simctl_ui_value(
    root: Path,
    identifier: str,
    setting: str,
    value: str | None = None,
    query_evidence: list[dict[str, object]] | None = None,
    *,
    log_relative: str,
) -> tuple[bool, str | None]:
    """Use simctl only through a controlled log and accept fixed setting values."""

    suffix = "query" if value is None else "set"
    log_path = _safe_live_path(root, log_relative)
    command = ["xcrun", "simctl", "ui", identifier, setting]
    if value is not None:
        command.append(value)
    result = _run_live_command(f"simctl-{setting}-{suffix}", command, ROOT, {}, log_path)
    if result[0] != 0:
        if value is None and query_evidence is not None:
            query_evidence.append({
                "setting": setting,
                "processExit": _published_process_exit(getattr(result, "process_exit", None)),
                "responseStatus": "command-failed",
            })
        return False, None
    state, content = _bounded_live_file_text(root, log_path)
    if state != "available" or content is None:
        if value is None and query_evidence is not None:
            query_evidence.append({
                "setting": setting,
                "processExit": _published_process_exit(getattr(result, "process_exit", None)),
                "responseStatus": state,
            })
        return False, None
    if value is not None:
        return True, value
    observed = content.strip().lower()
    if query_evidence is not None:
        evidence: dict[str, object] = {
            "setting": setting,
            "processExit": _published_process_exit(getattr(result, "process_exit", None)),
            "responseStatus": "available",
        }
        if re.fullmatch(r"[a-z-]{1,80}", observed):
            evidence["response"] = observed
        else:
            evidence["responseStatus"] = "unpublished-invalid"
        query_evidence.append(evidence)
    if setting == "appearance" and observed in {"light", "dark"}:
        return True, observed
    if setting == "content_size" and observed in LIVE_CONTENT_SIZES:
        return True, observed
    return False, None


def _normal_settings_result(
    name: str,
    command: list[str],
    cwd: Path,
    environment: dict[str, str],
    root: Path,
    identifier: str,
    appearance: str,
) -> dict:
    """Set and restore simulator settings around one non-forced UI test."""

    private_setting_logs = _normal_setting_log_paths(name, identifier)
    setting_log_paths = dict(zip(_NORMAL_SETTING_LOG_OPERATIONS, private_setting_logs, strict=True))
    query_evidence: list[dict[str, object]] = []
    appearance_ok, previous_appearance = _simctl_ui_value(
        root, identifier, "appearance", query_evidence=query_evidence,
        log_relative=setting_log_paths[("appearance", "before-query")],
    )
    content_ok, previous_content = _simctl_ui_value(
        root, identifier, "content_size", query_evidence=query_evidence,
        log_relative=setting_log_paths[("content_size", "before-query")],
    )
    observations = {
        "appearanceBefore": previous_appearance,
        "contentSizeBefore": previous_content,
        "appearanceRequested": appearance,
        "contentSizeRequested": LIVE_CONTENT_SIZE,
        "queryEvidence": query_evidence,
    }
    if not appearance_ok or not content_ok:
        return {"name": name, "status": "failed", "exit": 1,
                "detail": "simulator settings could not be queried",
                "reason": "simulator-setting-query-failed",
                "simulator_settings": observations, "private_setting_logs": private_setting_logs}
    result: dict | None = None
    setting_failed = False
    restore_failed = False
    try:
        if not _simctl_ui_value(root, identifier, "appearance", appearance,
                                log_relative=setting_log_paths[("appearance", "requested-set")])[0]:
            setting_failed = True
        else:
            observed, value = _simctl_ui_value(
                root, identifier, "appearance",
                log_relative=setting_log_paths[("appearance", "requested-query")],
            )
            observations["appearanceObserved"] = value if observed else None
            setting_failed = not observed or value != appearance
        if not setting_failed:
            if not _simctl_ui_value(root, identifier, "content_size", LIVE_CONTENT_SIZE,
                                    log_relative=setting_log_paths[("content_size", "requested-set")])[0]:
                setting_failed = True
            else:
                observed, value = _simctl_ui_value(
                    root, identifier, "content_size",
                    log_relative=setting_log_paths[("content_size", "requested-query")],
                )
                observations["contentSizeObserved"] = value if observed else None
                setting_failed = not observed or value != LIVE_CONTENT_SIZE
        if not setting_failed:
            result = _run_live_ios_test(name, command, cwd, environment, 1, root)
    finally:
        restored_appearance = _simctl_ui_value(
            root, identifier, "appearance", previous_appearance,
            log_relative=setting_log_paths[("appearance", "restore-set")],
        )[0]
        verified_appearance, observed_appearance = _simctl_ui_value(
            root, identifier, "appearance",
            log_relative=setting_log_paths[("appearance", "restore-query")],
        )
        restored_content = _simctl_ui_value(
            root, identifier, "content_size", previous_content,
            log_relative=setting_log_paths[("content_size", "restore-set")],
        )[0]
        verified_content, observed_content = _simctl_ui_value(
            root, identifier, "content_size",
            log_relative=setting_log_paths[("content_size", "restore-query")],
        )
        observations["appearanceRestored"] = observed_appearance if verified_appearance else None
        observations["contentSizeRestored"] = observed_content if verified_content else None
        restore_failed = not (
            restored_appearance and verified_appearance and observed_appearance == previous_appearance
            and restored_content and verified_content and observed_content == previous_content
        )
    if restore_failed:
        return {**(result or {}), "name": name, "status": "failed", "exit": 1,
                "detail": "simulator settings could not be restored",
                "reason": "simulator-setting-restore-failed",
                "check_exit_before_restore": result.get("exit") if result else None,
                "check_reason_before_restore": result.get("reason") if result else None,
                "simulator_settings": observations, "private_setting_logs": private_setting_logs}
    if setting_failed:
        return {"name": name, "status": "failed", "exit": 1,
                "detail": "simulator settings could not be set and verified",
                "reason": "simulator-setting-set-failed",
                "simulator_settings": observations, "private_setting_logs": private_setting_logs}
    assert result is not None
    return {**result, "simulator_settings": observations, "private_setting_logs": private_setting_logs}


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
    timeout = (
        LIVE_DIAGNOSTIC_COLLECTION_TIMEOUT_SECONDS
        if name.endswith("-diagnostic-attachments")
        else LIVE_COMMAND_TIMEOUT_SECONDS
    )
    if command[:3] == ["xcrun", "simctl", "ui"] and _ACTIVE_SIMULATOR_LOG_ROOT is not None:
        try:
            completed = _run_simulator_command(
                _ACTIVE_SIMULATOR_LOG_ROOT, f"live-{name}", command, timeout
            )
        except subprocess.TimeoutExpired:
            return LiveCommandResult(1, f"{name} exceeded its time limit", "command-timeout")
        except OSError:
            return LiveCommandResult(1, f"{name} could not start", "command-start-failed")
        log_path.write_text(
            (completed.stdout or "") + (completed.stderr or ""), encoding="utf-8", errors="replace"
        )
        if completed.returncode != 0:
            return LiveCommandResult(
                1, f"{name} returned a non-zero result", "command-nonzero",
                _published_process_exit(completed.returncode),
            )
        return LiveCommandResult(
            0, f"{name} completed", process_exit=_published_process_exit(completed.returncode)
        )
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
                timeout=timeout,
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
            1,
            f"{name} returned a non-zero result",
            "command-nonzero",
            _published_process_exit(completed.returncode),
        )
    return LiveCommandResult(
        0, f"{name} completed", process_exit=_published_process_exit(completed.returncode)
    )


def _xcodebuild_options_before_build_settings(
    command: list[str], options: list[str]
) -> list[str]:
    """Put Xcode options before controlled command-line build settings."""

    for index, argument in enumerate(command):
        if re.fullmatch(r"ACE_[A-Z0-9_]+=.*", argument):
            return [*command[:index], *options, *command[index:]]
    return [*command, *options]


def _published_process_exit(value: object) -> int | None:
    """Return a completed-process exit code only when it is a safe integer."""

    if (
        type(value) is int
        and LIVE_PROCESS_EXIT_MIN <= value <= LIVE_PROCESS_EXIT_MAX
    ):
        return value
    return None


def _bounded_failure_text(value: object) -> tuple[str | None, str]:
    """Return a short assertion field without public private command output."""

    if value is None:
        return None, "absent"
    if type(value) in (int, float, bool):
        return str(value).lower(), "available"
    if not isinstance(value, str):
        return None, "invalid"
    text = value.strip()
    if not text:
        return None, "absent"
    environment_values = {
        candidate for candidate in os.environ.values()
        if isinstance(candidate, str) and len(candidate) >= 8
    }
    if (
        len(text) > 512
        or not all(character.isprintable() for character in text)
        or any(candidate in text for candidate in environment_values)
        or re.search(r"(?i)(?:https?|ssh)://|\b[^\s@]+@[^\s@]+\b", text)
        or re.search(r"(?i)[\"']?(?:password|token|authorization|credential|secret)[\"']?\s*[:=]", text)
        or re.search(r"(?i)\b(?:ghp_[A-Za-z0-9_]+|github_pat_[A-Za-z0-9_]+|sk-[A-Za-z0-9_-]+)\b", text)
        or re.search(r"(?:(?:[A-Za-z]:)?[\\/](?:Users|private|var|Volumes|Applications)[\\/])", text)
    ):
        return None, "redacted"
    return text, "available"


def _repository_relative_source_path(value: object) -> tuple[str | None, str]:
    """Accept a source file only below an approved repository directory."""

    if not isinstance(value, str):
        return None, "absent" if value is None else "invalid"
    path = value.strip().replace("\\", "/")
    root = str(ROOT.resolve()).replace("\\", "/").rstrip("/")
    absolute = path.startswith("/") or re.match(r"^[A-Za-z]:/", path) is not None
    if absolute:
        if not path.casefold().startswith(root.casefold() + "/"):
            return None, "invalid"
        relative = path[len(root) + 1:]
    else:
        relative = path
    if re.fullmatch(
        r"(?:apps|ios|quality|security|src|tests|tools|workflows)/[^\s:]+", relative
    ) is None:
        return None, "invalid"
    if (
        len(relative) > 256
        or ".." in relative.split("/")
        or not re.fullmatch(r"[A-Za-z0-9._/ -]+", relative)
    ):
        return None, "invalid"
    return relative, "available"


def _published_test_identifier(value: object) -> tuple[str | None, str]:
    """Return one bounded, non-sensitive XCTest identifier."""

    identifier, status = _bounded_failure_text(value)
    if identifier is None:
        return None, status
    if re.fullmatch(r"[A-Za-z0-9_.\-\[\]() /:]+", identifier) is None:
        return None, "invalid"
    return identifier, "available"


def _normalise_xcresult_failure(failure: object) -> dict[str, object] | None:
    """Create one fixed-shape failure record from an XCResult test failure."""

    if not isinstance(failure, dict):
        return None

    def field_value(names: tuple[str, ...]) -> object:
        for field in names:
            if field in failure:
                return failure[field]
        return None

    detail: dict[str, object] = {}
    identifier, identifier_status = _published_test_identifier(
        field_value(("testCaseName", "testIdentifier", "testName"))
    )
    detail["testIdentifierStatus"] = identifier_status
    if identifier is not None:
        detail["testIdentifier"] = identifier

    source_value = field_value(("file", "fileName", "filePath", "sourceFile"))
    source_line = field_value(("line", "lineNumber", "sourceLine"))
    location = field_value(("location", "sourceLocation", "sourceCodeLocation"))
    if isinstance(location, dict):
        if source_value is None:
            for key in ("file", "fileName", "filePath", "sourceFile"):
                if key in location:
                    source_value = location[key]
                    break
        if source_line is None:
            for key in ("line", "lineNumber", "sourceLine"):
                if key in location:
                    source_line = location[key]
                    break
    elif isinstance(location, str) and source_value is None:
        candidate, separator, line_text = location.rpartition(":")
        source_value = candidate if separator and line_text.isdigit() else location
        if separator and line_text.isdigit():
            source_line = int(line_text)
    source_file, source_file_status = _repository_relative_source_path(source_value)
    detail["sourceFileStatus"] = source_file_status
    if source_file is not None:
        detail["sourceFile"] = source_file
    if type(source_line) is int and 0 < source_line <= 1_000_000:
        detail["sourceLine"] = source_line
        detail["sourceLineStatus"] = "available"
    else:
        detail["sourceLineStatus"] = "absent" if source_line is None else "invalid"
    for output, names in (
        ("expected", ("expected", "expectedValue", "expectedOutcome")),
        ("actual", ("actual", "actualValue", "actualOutcome")),
        ("failureMessage", ("failureText", "failureMessage", "message", "description")),
    ):
        value, status = _bounded_failure_text(field_value(names))
        detail[output + "Status"] = status
        if value is not None:
            detail[output] = value
    return detail


def _xcresult_failure_details(payload: object) -> tuple[list[dict[str, object]], str]:
    """Find bounded XCResult failures without accepting arbitrary result objects."""

    selected: list[dict[str, object]] = []
    pending = [payload]
    visited = 0
    found = False
    while pending:
        value = pending.pop()
        visited += 1
        if visited > LIVE_RESULT_SUMMARY_MAX_NODES:
            return selected, "truncated"
        if isinstance(value, dict):
            failures = value.get("testFailures")
            if failures is not None:
                if not isinstance(failures, list):
                    return selected, "invalid"
                found = True
                for failure in failures:
                    detail = _normalise_xcresult_failure(failure)
                    if detail is not None:
                        selected.append(detail)
                    if len(selected) == 30:
                        return selected, "truncated"
            pending.extend(value.values())
        elif isinstance(value, list):
            pending.extend(value)
    return selected, "available" if found else "not-recorded"


def _live_ios_failure_evidence(
    name: str,
    cwd: Path,
    root: Path,
    result_path: Path,
    collection_exits: dict[str, int | None] | None = None,
) -> tuple[str, list[dict[str, object]], str]:
    """Read bounded XCTest failures while keeping raw XCResult data private."""

    try:
        if not result_path.is_dir() or result_path.is_symlink():
            return "result-bundle-missing", [], "unavailable"
        if not result_path.resolve().is_relative_to(root.resolve()):
            return "result-bundle-missing", [], "unavailable"
    except OSError:
        return "result-bundle-missing", [], "unavailable"
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
    if collection_exits is not None:
        collection_exits["summary"] = _published_process_exit(
            getattr(summary_result, "process_exit", None)
        )
    if summary_result[0] != 0:
        return "result-summary-command-failed", [], "unavailable"
    state, content = _bounded_live_file_text(root, summary_path)
    if state != "available":
        return f"result-summary-{state}", [], "unavailable"
    try:
        payload = json.loads(content)
    except (TypeError, ValueError):
        return "result-summary-malformed", [], "unavailable"
    except RecursionError:
        return "result-summary-over-complex", [], "unavailable"
    counts, over_complex = _bounded_xcresult_counts(payload)
    if over_complex:
        return "result-summary-over-complex", [], "unavailable"
    details, detail_status = _xcresult_failure_details(payload)
    if counts is None:
        return "diagnostic-gap", details, detail_status
    if counts[1] > 0:
        return "test-failures-recorded", details, detail_status
    return "result-summary-no-failed-tests", [], "not-recorded"


def _live_ios_failure_diagnostic(
    name: str, cwd: Path, root: Path, result_path: Path
) -> str:
    """Return the legacy fixed diagnostic code for callers that need it."""

    return _live_ios_failure_evidence(name, cwd, root, result_path)[0]


def _live_test_counts(root: Path, name: str) -> dict[str, object]:
    """Return only validated XCTest counts, or an explicit unknown state."""

    state, content = _bounded_live_file_text(
        root, _safe_live_path(root, f"{name}-summary.json")
    )
    if state != "available" or content is None:
        return {"status": "unknown"}
    try:
        payload = json.loads(content)
    except (TypeError, ValueError, RecursionError):
        return {"status": "unknown"}
    counts, over_complex = _bounded_xcresult_counts(payload)
    if counts is None or over_complex:
        return {"status": "unknown"}
    passed, failed, skipped = counts
    return {
        "status": "available",
        "passed": passed,
        "failed": failed,
        "skipped": skipped,
    }


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
            command,
            ["-parallel-testing-enabled", "NO", "-resultBundlePath", str(result_path)],
        ),
        cwd,
        environment,
        log_path,
    )
    exit_code, detail = command_result
    if exit_code:
        collection_exits: dict[str, int | None] = {}
        diagnostic, failures, failure_status = _live_ios_failure_evidence(
            name, cwd, root, result_path, collection_exits
        ) if getattr(command_result, "reason", None) == "command-nonzero" else (
            "diagnostic-gap", [], "unavailable"
        )
        retention = _diagnostic_retention_fields(name, cwd, root, result_path, collection_exits)
        return {
            "name": name,
            "status": "failed",
            "exit": 1,
            "detail": detail,
            "reason": _published_live_failure_reason(
                getattr(command_result, "reason", None)
            ),
            "diagnostic": diagnostic,
            "test_failures": failures,
            "test_failure_status": failure_status,
            "test_counts": _live_test_counts(root, name),
            **retention,
            "collection_process_exits": collection_exits,
            "process_exit": getattr(command_result, "process_exit", None),
        }
    if not result_path.is_dir() or result_path.is_symlink():
        return {
            "name": name,
            "status": "failed",
            "exit": 1,
            "detail": f"{name} result bundle is missing",
            "reason": "result-bundle-missing",
            "process_exit": getattr(command_result, "process_exit", None),
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
        collection_exits = {
            "summary": _published_process_exit(
                getattr(summary_result, "process_exit", None)
            )
        }
        retention = _diagnostic_retention_fields(name, cwd, root, result_path, collection_exits)
        return {
            "name": name,
            "status": "failed",
            "exit": 1,
            "detail": summary_detail,
            "reason": _published_live_failure_reason(
                getattr(summary_result, "reason", None)
            ),
            "diagnostic": "result-summary-command-failed",
            "test_counts": {"status": "unknown"},
            "collection_process_exits": collection_exits,
            **retention,
            "process_exit": getattr(command_result, "process_exit", None),
        }
    summary_state, summary_content = _bounded_live_file_text(root, summary_path)
    try:
        payload = json.loads(summary_content)
    except (TypeError, ValueError):
        counts, over_complex, malformed = None, False, True
    except RecursionError:
        counts, over_complex, malformed = None, True, False
    else:
        counts, over_complex = _bounded_xcresult_counts(payload)
        malformed = False
    if counts is None:
        collection_exits: dict[str, int | None] = {"summary": 0}
        retention = _diagnostic_retention_fields(name, cwd, root, result_path, collection_exits)
        return {
            "name": name,
            "status": "failed",
            "exit": 1,
            "detail": f"{name} has no executed-test summary",
            "reason": "result-summary-invalid",
            "diagnostic": (
                "result-summary-over-complex"
                if over_complex
                else f"result-summary-{summary_state}"
                if summary_state != "available"
                else "result-summary-malformed" if malformed else "diagnostic-gap"
            ),
            "test_counts": {"status": "unknown"},
            "collection_process_exits": collection_exits,
            **retention,
            "process_exit": getattr(command_result, "process_exit", None),
        }
    passed, failed, skipped = counts
    if passed != expected_tests or failed != 0 or skipped != 0:
        failures, failure_status = _xcresult_failure_details(payload)
        collection_exits: dict[str, int | None] = {}
        retention = _diagnostic_retention_fields(name, cwd, root, result_path, collection_exits)
        return {
            "name": name,
            "status": "failed",
            "exit": 1,
            "detail": f"{name} result count mismatch",
            "reason": "result-count-mismatch",
            "test_failures": failures,
            "test_failure_status": failure_status,
            "test_counts": {
                "status": "available",
                "passed": passed,
                "failed": failed,
                "skipped": skipped,
            },
            **retention,
            "collection_process_exits": collection_exits,
            "process_exit": getattr(command_result, "process_exit", None),
        }
    screenshots, screenshot_failure = _retain_live_screenshots(
        name, cwd, root, result_path
    )
    if screenshot_failure is not None:
        collection_exits: dict[str, int | None] = {"summary": 0}
        retention = _diagnostic_retention_fields(name, cwd, root, result_path, collection_exits)
        return {
            "name": name,
            "status": "failed",
            "exit": 1,
            "detail": f"{name} required screenshot artifact is unavailable",
            "reason": screenshot_failure,
            "test_counts": {
                "status": "available", "passed": passed, "failed": failed, "skipped": skipped,
            },
            "collection_process_exits": collection_exits,
            **retention,
            "process_exit": getattr(command_result, "process_exit", None),
        }
    return {
        "name": name,
        "status": "passed",
        "exit": 0,
        "detail": f"{name} executed {passed} tests",
        "process_exit": getattr(command_result, "process_exit", None),
        "screenshots": screenshots,
    }


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


def _live_execution_context(
    artifact_root: Path, expected_commit: str, expected_workflow: str = LIVE_WORKFLOW
) -> dict[str, str]:
    """Require the exact manual Codemagic workflow and checked-out build context."""

    build_directory = os.environ.get("CM_BUILD_DIR")
    build_id = os.environ.get("CM_BUILD_ID")
    if (
        artifact_root != LIVE_ARTIFACT_ROOT
        or not _is_non_empty_string(build_id)
        or re.fullmatch(r"[A-Za-z0-9_-]{1,128}", build_id or "") is None
        or not _is_non_empty_string(build_directory)
        or Path(build_directory).resolve() != ROOT.resolve()
        or expected_workflow not in {LIVE_WORKFLOW, LIVE_REPAIR_WORKFLOW}
        or os.environ.get(LIVE_WORKFLOW_ENVIRONMENT_KEY) != expected_workflow
        or os.environ.get("CM_COMMIT") != expected_commit
        or os.environ.get("CM_BRANCH") != LIVE_BRANCH
        or os.environ.get("CM_TRIGGER_SOURCE") != "api"
        or not _is_non_empty_string(os.environ.get("CM_BUILD_STARTED_BY"))
    ):
        raise ValueError("verified Codemagic live workflow context is invalid")
    return {"workflow": expected_workflow, "branch": LIVE_BRANCH, "buildId": build_id}


def _write_live_manifest(root: Path, manifest: dict) -> None:
    """Write controlled review metadata without command output or environment values."""

    _write_live_json_atomically(root, "live-evidence-manifest.json", manifest)


def _write_live_json_atomically(root: Path, relative: str, value: object) -> None:
    """Replace one controlled JSON record after the complete file reaches storage."""

    path = _safe_live_path(root, relative)
    if path.is_symlink():
        raise ValueError("live JSON publication path is a symlink")
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", dir=root, delete=False
        ) as handle:
            temporary = Path(handle.name)
            json.dump(value, handle, indent=2, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        for attempt in range(3):
            try:
                os.replace(temporary, path)
                break
            except PermissionError as error:
                if getattr(error, "winerror", None) not in (5, 32) or attempt == 2:
                    raise
                time.sleep(0.1)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def _write_live_review_manifest(
    root: Path, manifest: dict[str, object], checks: list[dict], checksums: dict[str, str]
) -> None:
    """Write the small publication manifest without logs, bundles, or raw test data."""

    stage = _safe_live_path(root, LIVE_REVIEW_STAGE)
    screenshot_paths = [path for check in checks for path in check.get("screenshots", []) if isinstance(path, str)]
    expected_count = sum(len(_expected_logical_screenshot_names(check["name"])) for check in checks)
    if (
        len(screenshot_paths) != expected_count
        or any(f"{LIVE_REVIEW_STAGE}/{path}" not in checksums for path in screenshot_paths)
    ):
        raise ValueError("required named screenshot artifacts are missing")
    screenshot_records = []
    for check in checks:
        name = check["name"]
        paths = check.get("screenshots", [])
        expected = _expected_logical_screenshot_names(name)
        if len(paths) != len(expected):
            raise ValueError("screenshot attachment inventory does not match")
        device = next((item for item in IOS_RELEASE_DEVICES if f"-{item}-" in name), IOS_CORE_DEVICE)
        appearance = "dark" if "-dark-" in name or name.endswith("-dark") else "light"
        normal_settings = name.startswith("ios-normal-settings-")
        observed_settings = _published_simulator_settings(check.get("simulator_settings"))
        for logical, path in zip(expected, paths):
            captured_appearance = logical.rsplit("forced-", 1)[1] if name.endswith("-testBothAppearances") else appearance
            screenshot_records.append({
                "path": path,
                "sha256": checksums[f"{LIVE_REVIEW_STAGE}/{path}"],
                "logicalName": logical,
                "device": device,
                "appearance": captured_appearance,
                "appearanceMode": "system-setting-at-launch" if normal_settings else "app-override",
                "contentSize": observed_settings.get("contentSizeObserved", "not-recorded"),
            })
    review = {
        "scope": manifest["scope"],
        "workflow": manifest["workflow"],
        "repository": manifest["repository"],
        "commit": manifest["commit"],
        "baseline": manifest["baseline"],
        "releaseEvidence": False,
        "status": "pending-manual-native-inspection",
        "results": [_published_live_result(check) for check in checks],
        "screenshots": sorted(screenshot_records, key=lambda record: record["path"]),
        "manualChecksPending": [
            "Inspect retained fictional screenshots on the approved device matrix.",
            "Verify Bold Text, Reduce Motion, and Increase Contrast manually.",
            "Run the remaining automated Dynamic Type size matrix and inspect its screenshots.",
            "Complete orientation checks for the remaining screens and states.",
            "Verify settings changed while the app remains open manually.",
            "Inspect normal-startup screenshots after simulator setting changes.",
            "Complete VoiceOver, normal screenshot, app-switcher, physical-device, and server-connection evidence.",
        ],
    }
    path = _safe_live_path(stage, LIVE_REVIEW_MANIFEST)
    if path.is_symlink():
        raise ValueError("live review manifest path is a symlink")
    path.write_text(json.dumps(review, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_live_progress(root: Path, checks: list[dict], active: str | None) -> None:
    """Retain an atomic, checked, allowlisted snapshot after each command."""

    _write_live_snapshot(root, checks, active)


def _write_live_snapshot(
    root: Path,
    checks: list[dict],
    active: str | None,
    *,
    planned: list[dict[str, object]] | None = None,
    expected_identity: dict[str, str] | None = None,
    verified_identity: dict[str, str] | None = None,
    interrupted: bool = False,
    fault: str | None = None,
    private_collection_status: str = "incomplete",
) -> None:
    """Persist one safe live-run state without inferring unavailable results."""

    names = _live_command_names()
    if active not in names | {None, "setup", "artifact-validation"} or len(checks) > len(names):
        raise ValueError("invalid live progress scope")
    completed = [_published_live_result(check) for check in checks]
    completed_names = [item["name"] for item in completed]
    if len(set(completed_names)) != len(completed_names):
        raise ValueError("duplicate completed live command")
    planned_records: list[dict[str, object]] = []
    for item in planned or []:
        if (
            not isinstance(item, dict)
            or item.get("name") not in names
            or (
                item.get("expectedTests") is not None
                and (
                    type(item.get("expectedTests")) is not int
                    or not 0 < item["expectedTests"] <= LIVE_RESULT_SUMMARY_MAX_NODES
                )
            )
        ):
            raise ValueError("invalid live command inventory")
        planned_records.append({"name": item["name"], "expectedTests": item["expectedTests"]})
    planned_names = [item["name"] for item in planned_records]
    if len(set(planned_names)) != len(planned_names):
        raise ValueError("duplicate planned live command")
    if planned_names and not set(completed_names).issubset(planned_names):
        raise ValueError("completed command is outside the planned inventory")
    for check in completed:
        for field in ("diagnosticImages", "safeImages"):
            for image in check.get(field, []):
                path = _safe_live_path(root, image["path"])
                if (
                    path.is_symlink()
                    or not path.is_file()
                    or not _valid_png(path)
                    or hashlib.sha256(path.read_bytes()).hexdigest() != image["sha256"]
                ):
                    raise ValueError("retained image snapshot validation failed")
    failed = [item for item in completed if item["exit"] != 0]
    not_run = [
        name for name in planned_names
        if name not in completed_names and name != active
    ]
    progress = {
        "releaseEvidence": False,
        "status": "incomplete",
        "privateCollectionStatus": _private_collection_status(private_collection_status),
        "runState": (
            "interrupted" if interrupted else "failed" if failed or fault else "complete"
            if planned_names and not not_run and active is None else "incomplete"
        ),
        "activeCommand": active,
        "active": active if active in names else None,
        "planned": planned_records,
        "completed": completed,
        "failed": failed,
        "interrupted": interrupted,
        "notRun": not_run,
    }
    for field, identity in (
        ("expectedIdentity", expected_identity),
        ("verifiedIdentity", verified_identity),
    ):
        if identity is None:
            continue
        expected_fields = (
            {
                "scope": "MCX-19-manual-live-evidence",
                "workflow": LIVE_WORKFLOW,
                "repository": LIVE_REPOSITORY,
                "expectedCommit": None,
                "expectedBranch": LIVE_BRANCH,
                "baseline": LIVE_BASELINE_COMMIT,
            }
            if field == "expectedIdentity"
            else {
                "scope": "MCX-19-manual-live-evidence",
                "workflow": LIVE_WORKFLOW,
                "repository": LIVE_REPOSITORY,
                "commit": None,
                "branch": LIVE_BRANCH,
                "baseline": LIVE_BASELINE_COMMIT,
                "buildId": None,
            }
        )
        commit_field = "expectedCommit" if field == "expectedIdentity" else "commit"
        if (
            not isinstance(identity, dict)
            or set(identity) != set(expected_fields)
            or any(identity[key] != value for key, value in expected_fields.items() if value is not None)
            or not isinstance(identity.get(commit_field), str)
            or re.fullmatch(r"[0-9a-f]{40}", identity[commit_field]) is None
            or (
                field == "verifiedIdentity"
                and (
                    not isinstance(identity.get("buildId"), str)
                    or re.fullmatch(r"[A-Za-z0-9_-]{1,128}", identity["buildId"]) is None
                )
            )
        ):
            raise ValueError("invalid live run identity")
        progress[field] = dict(sorted(identity.items()))
    if fault is not None:
        if fault not in LIVE_PUBLISHED_FAILURE_REASONS:
            raise ValueError("invalid live snapshot fault")
        progress["fault"] = fault
    _write_live_json_atomically(root, "live-evidence-progress.json", progress)
    # The console record survives even if the provider cannot collect artifacts on cancellation.
    print("live-progress=" + json.dumps({
        "activeCommand": active,
        "completedCount": len(completed),
        "lastCompleted": completed[-1] if completed else None,
        "releaseEvidence": False,
        "privateCollectionStatus": _private_collection_status(private_collection_status),
    }, sort_keys=True), flush=True)


def _live_failure_detail(error: Exception) -> str:
    """Return fixed safe text for a live setup or simulator failure."""

    reason = _live_failure_reason(error)
    if reason == SIMULATOR_RESOLUTION_TIMEOUT_REASON:
        return "simulator resolution timed out"
    if reason == SIMULATOR_RESOLUTION_FAILURE_REASON:
        return "simulator resolution failed"
    if reason == LIVE_REMOTE_RETENTION_UNAVAILABLE_REASON:
        return "remote retention is unavailable"
    if reason == LIVE_PRIVATE_COLLECTION_FAILURE_REASON:
        return "private evidence collection failed"
    return "live setup failed"


def _live_failure_reason(error: Exception) -> str:
    """Return one fixed reason code without reading exception text."""

    if isinstance(error, SafeImageRetentionError):
        return "safe-image-retention-failed"
    if isinstance(error, PrivateCollectionError):
        if error.category == LIVE_REMOTE_RETENTION_UNAVAILABLE_REASON:
            return LIVE_REMOTE_RETENTION_UNAVAILABLE_REASON
        return LIVE_PRIVATE_COLLECTION_FAILURE_REASON
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
        if isinstance(reason, str) and reason in NEGATIVE_CONFIGURATION_REASONS:
            return reason
        return "negative-configuration-not-rejected"
    if isinstance(reason, str) and reason in LIVE_PUBLISHED_FAILURE_REASONS:
        return reason
    return "controlled-failure"


def _published_simulator_settings(value: object) -> dict[str, str]:
    """Retain only known simulator setting names and enumerated observations."""

    if not isinstance(value, dict):
        return {}
    result = {}
    for prefix, allowed in (("appearance", {"light", "dark"}), ("contentSize", LIVE_CONTENT_SIZES)):
        for suffix in ("Before", "Requested", "Observed", "Restored"):
            field = prefix + suffix
            observed = value.get(field)
            if isinstance(observed, str) and observed in allowed:
                result[field] = observed
    return result


def _published_test_failures(value: object, failed: bool) -> list[dict[str, object]]:
    """Revalidate failure records at the public manifest boundary."""

    if not failed or not isinstance(value, list):
        return []
    records = []
    for item in value[:30]:
        if not isinstance(item, dict):
            continue
        record: dict[str, object] = {}
        valid = True
        for field in (
            "testIdentifier", "sourceFile", "sourceLine", "expected", "actual", "failureMessage"
        ):
            status = item.get(field + "Status")
            if status not in {"available", "absent", "invalid", "redacted"}:
                valid = False
                break
            if status == "available":
                candidate = item.get(field)
                if field == "testIdentifier":
                    published, published_status = _published_test_identifier(candidate)
                elif field == "sourceFile":
                    published, published_status = _repository_relative_source_path(candidate)
                elif field == "sourceLine":
                    published = candidate if type(candidate) is int and 0 < candidate <= 1_000_000 else None
                    published_status = "available" if published is not None else "invalid"
                else:
                    published, published_status = _bounded_failure_text(candidate)
                if published is None or published_status != "available":
                    record[field + "Status"] = (
                        published_status if published_status != "absent" else "invalid"
                    )
                else:
                    record[field + "Status"] = "available"
                    record[field] = published
            elif field in item:
                valid = False
                break
            else:
                record[field + "Status"] = status
        if valid:
            records.append(record)
    return records


def _published_simulator_query_evidence(value: object) -> list[dict[str, object]]:
    """Publish only the two fixed simulator query responses."""

    if not isinstance(value, list):
        return []
    records = []
    for item in value[:2]:
        if not isinstance(item, dict) or item.get("setting") not in {"appearance", "content_size"}:
            continue
        record: dict[str, object] = {"setting": item["setting"]}
        process_exit = _published_process_exit(item.get("processExit"))
        if process_exit is not None:
            record["processExit"] = process_exit
        if item.get("responseStatus") in {"available", "command-failed", "missing", "unsafe", "oversized", "unreadable", "unpublished-invalid"}:
            record["responseStatus"] = item["responseStatus"]
        if item.get("responseStatus") == "available" and isinstance(item.get("response"), str) and re.fullmatch(r"[a-z-]{1,80}", item["response"]):
            record["response"] = item["response"]
        records.append(record)
    return records


def _published_test_counts(value: object) -> dict[str, object]:
    """Publish exact bounded count values only when the summary validated them."""

    if not isinstance(value, dict) or value.get("status") != "available":
        return {"status": "unknown"}
    counts = {field: value.get(field) for field in ("passed", "failed", "skipped")}
    if not all(type(count) is int and 0 <= count <= LIVE_RESULT_SUMMARY_MAX_NODES for count in counts.values()):
        return {"status": "unknown"}
    return {"status": "available", **counts}


def _published_collection_process_exits(value: object) -> tuple[dict[str, int], dict[str, str]]:
    """Keep collection exits separate from the XCTest process exit."""

    if not isinstance(value, dict):
        return {}, {}
    exits: dict[str, int] = {}
    status: dict[str, str] = {}
    prior_status = value.get("status") if isinstance(value.get("status"), dict) else {}
    for name in ("summary", "attachmentExport"):
        if name not in value:
            if prior_status.get(name) == "unknown":
                status[name] = "unknown"
            continue
        process_exit = _published_process_exit(value[name])
        if process_exit is None:
            status[name] = "unknown"
        else:
            exits[name] = process_exit
            status[name] = "available"
    return exits, status


def _published_retained_images(
    name: str, value: object, directory: str
) -> list[dict[str, str]]:
    """Allow only fixed retained-image paths and their SHA-256 values."""

    expected = _expected_logical_screenshot_names(name)
    if not isinstance(value, list) or len(value) > len(expected):
        return []
    records: list[dict[str, str]] = []
    seen: set[str] = set()
    for item in value:
        if not isinstance(item, dict):
            return []
        logical = item.get("logicalName")
        path = item.get("path")
        digest = item.get("sha256")
        if (
            not isinstance(logical, str)
            or logical not in expected
            or logical in seen
            or not isinstance(path, str)
            or not isinstance(digest, str)
            or re.fullmatch(r"[0-9a-f]{64}", digest) is None
        ):
            return []
        number = expected.index(logical) + 1
        if path != f"{directory}/{name}/{number:02d}.png":
            return []
        seen.add(logical)
        records.append({"logicalName": logical, "path": path, "sha256": digest})
    return records


def _published_diagnostic_images(name: str, value: object) -> list[dict[str, str]]:
    return _published_retained_images(name, value, LIVE_DIAGNOSTIC_IMAGE_DIRECTORY)


def _published_live_result(check: dict) -> dict:
    """Publish only fixed data and bounded completed-process metadata."""

    names = _live_command_names()
    name = check.get("name")
    if not isinstance(name, str) or name not in names:
        name = "controlled-live-command"
    logical_exit = 0 if type(check.get("exit")) is int and check["exit"] == 0 else 1
    result = {
        "name": name,
        "status": "passed" if logical_exit == 0 else "failed",
        "exit": logical_exit,
        "detail": (
            "negative configuration rejected"
            if logical_exit == 0 and name == "ios-negative-config"
            else _published_live_success_detail(name, check.get("detail"))
            if logical_exit == 0
            else "controlled live command failed"
        ),
    }
    process_exit = _published_process_exit(check.get("processExit"))
    if process_exit is None:
        process_exit = _published_process_exit(check.get("process_exit"))
    if process_exit is not None:
        result["processExit"] = process_exit
    if name.startswith("ios-normal-settings-"):
        raw_settings = check.get("simulatorSettings")
        if not isinstance(raw_settings, dict):
            raw_settings = check.get("simulator_settings")
        settings = _published_simulator_settings(raw_settings)
        if settings:
            result["simulatorSettings"] = settings
        raw_queries = check.get("simulatorQueryEvidence")
        if raw_queries is None and isinstance(raw_settings, dict):
            raw_queries = raw_settings.get("queryEvidence")
        queries = _published_simulator_query_evidence(raw_queries)
        if queries:
            result["simulatorQueryEvidence"] = queries
        before_restore = check.get("checkExitBeforeRestore")
        if before_restore is None:
            before_restore = check.get("check_exit_before_restore")
        if type(before_restore) is int and before_restore in {0, 1}:
            result["checkExitBeforeRestore"] = before_restore
            if before_restore != 0:
                result["checkReasonBeforeRestore"] = _published_live_failure_reason(
                    check.get("checkReasonBeforeRestore", check.get("check_reason_before_restore")), name
                )
    if logical_exit != 0:
        result["reason"] = _published_live_failure_reason(check.get("reason"), name)
        diagnostic = check.get("diagnostic")
        if isinstance(diagnostic, str) and diagnostic in LIVE_PUBLISHED_DIAGNOSTICS:
            result["diagnostic"] = diagnostic
        result["testCounts"] = _published_test_counts(
            check.get("testCounts", check.get("test_counts"))
        )
        raw_collection_exits = check.get(
            "collectionProcessExits", check.get("collection_process_exits")
        )
        raw_collection_status = check.get("collectionProcessExitStatus")
        if isinstance(raw_collection_exits, dict) and isinstance(raw_collection_status, dict):
            raw_collection_exits = {**raw_collection_exits, "status": raw_collection_status}
        elif raw_collection_exits is None and isinstance(raw_collection_status, dict):
            raw_collection_exits = {"status": raw_collection_status}
        collection_exits, collection_status = _published_collection_process_exits(
            raw_collection_exits
        )
        if collection_exits:
            result["collectionProcessExits"] = collection_exits
        if collection_status:
            result["collectionProcessExitStatus"] = collection_status
        image_status = check.get(
            "diagnosticImageStatus", check.get("diagnostic_image_status")
        )
        if image_status in LIVE_DIAGNOSTIC_IMAGE_STATUSES:
            result["diagnosticImageStatus"] = image_status
        attachment_problem = check.get(
            "diagnosticAttachmentProblem", check.get("diagnostic_attachment_problem")
        )
        if attachment_problem in LIVE_DIAGNOSTIC_ATTACHMENT_PROBLEMS:
            result["diagnosticAttachmentProblem"] = attachment_problem
        images = _published_diagnostic_images(
            name, check.get("diagnosticImages", check.get("diagnostic_images"))
        )
        if images:
            result["diagnosticImages"] = images
        missing = check.get(
            "missingDiagnosticImageNames", check.get("missing_diagnostic_image_names")
        )
        expected_images = _expected_logical_screenshot_names(name)
        if (
            isinstance(missing, list)
            and len(missing) <= len(expected_images)
            and all(isinstance(item, str) and item in expected_images for item in missing)
            and len(set(missing)) == len(missing)
        ):
            result["missingDiagnosticImageNames"] = [
                item for item in expected_images if item in missing
            ]
    elif name == "ios-negative-config":
        result["reason"] = "negative-configuration-rejected"
    result["testFailures"] = _published_test_failures(
        check.get("testFailures", check.get("test_failures")), logical_exit != 0
    )
    safe_images = _published_retained_images(
        name,
        check.get("safeImages", check.get("safe_images")),
        LIVE_DIAGNOSTIC_IMAGE_DIRECTORY,
    )
    if safe_images:
        result["safeImages"] = safe_images
    if logical_exit != 0:
        status = check.get("testFailureStatus", check.get("test_failure_status"))
        result["testFailureStatus"] = (
            status if status in {"available", "not-recorded", "truncated", "invalid", "unavailable"}
            else "unavailable"
        )
    return result


def _published_live_success_detail(name: str, detail: object) -> str:
    """Keep a generated test count only when it is bounded and matches its command."""

    if not isinstance(detail, str):
        return "controlled live command completed"
    match = re.fullmatch(rf"{re.escape(name)} executed ([0-9]+) tests", detail)
    if match is None:
        return "controlled live command completed"
    digits = match.group(1)
    if len(digits) > 10:
        return "controlled live command completed"
    count = int(digits)
    if count > LIVE_RESULT_SUMMARY_MAX_NODES:
        return "controlled live command completed"
    return f"{name} executed {count} tests"


def _live_command_names() -> set[str]:
    """Return the fixed names in the approved live command scope."""

    destinations = {device: "" for device in IOS_RELEASE_DEVICES}
    return {
        "ios-65-unit",
        "ios-evidence-contract",
        "ios-negative-config",
        *(name for name, *_ in ios_release_ui_matrix(destinations, LIVE_UI_METHODS)),
        *(name for name, *_ in ios_normal_settings_matrix(destinations)),
    }


def _live_command_failure_summary(checks: list[dict]) -> str:
    """Return bounded, ordered live command names and controlled reason codes."""

    allowed_names = _live_command_names()
    reasons_by_name: dict[str, set[str]] = {}
    diagnostics_by_name: dict[str, set[str]] = {}
    process_exits_by_name: dict[str, int] = {}
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
            diagnostic = item.get("diagnostic")
            if isinstance(diagnostic, str) and diagnostic in LIVE_PUBLISHED_DIAGNOSTICS:
                diagnostics_by_name.setdefault(name, set()).add(diagnostic)
            process_exit = _published_process_exit(item.get("processExit"))
            if process_exit is None:
                process_exit = _published_process_exit(item.get("process_exit"))
            if process_exit is not None:
                previous_exit = process_exits_by_name.get(name)
                if previous_exit is None or process_exit < previous_exit:
                    process_exits_by_name[name] = process_exit
    names = sorted(reasons_by_name)[:LIVE_FAILURE_SUMMARY_MAX_ITEMS]
    names_text = ", ".join(names)
    reasons_text = ", ".join(
        f"{name}={min(reasons_by_name[name])}" for name in names
    )
    diagnostics_text = ", ".join(
        f"{name}={min(diagnostics_by_name[name])}"
        for name in names
        if name in diagnostics_by_name
    )
    summary = f"failed live commands: {names_text}; reasons: {reasons_text}"
    process_exits_text = ", ".join(
        f"{name}={process_exits_by_name[name]}"
        for name in names
        if name in process_exits_by_name
    )
    if process_exits_text:
        summary += f"; process exits: {process_exits_text}"
    if diagnostics_text:
        summary += f"; diagnostics: {diagnostics_text}"
    return summary


def _negative_configuration_result(
    root: Path, log_path: Path, command_result: tuple[int, str]
) -> dict:
    """Classify the controlled rejection check without publishing its log content."""

    logical_exit, _ = command_result
    process_exit = getattr(command_result, "process_exit", None)
    command_reason = getattr(command_result, "reason", None)
    result = {
        "name": "ios-negative-config",
        "status": "failed",
        "exit": 1,
        "detail": "negative configuration did not fail as required",
        "process_exit": process_exit,
    }
    if logical_exit == 0:
        result["reason"] = "negative-configuration-exited-zero"
        return result
    if command_reason == "command-timeout":
        result["reason"] = "negative-configuration-timeout"
        return result
    if command_reason == "command-start-failed":
        result["reason"] = "negative-configuration-start-failed"
        return result
    state, content = _bounded_live_file_text(root, log_path)
    if state != "available":
        result["reason"] = f"negative-configuration-log-{state}"
        return result
    if command_reason == "command-nonzero" and NEGATIVE_CONFIG_REJECTION in content:
        return {
            "name": "ios-negative-config",
            "status": "passed",
            "exit": 0,
            "detail": "negative configuration rejected",
            "reason": "negative-configuration-rejected",
            "process_exit": process_exit,
        }
    result["reason"] = "negative-configuration-unrelated-nonzero"
    return result


def _live_repair_command_names() -> set[str]:
    """Return the fixed one-command diagnostic repair scope."""

    destinations = {device: "" for device in IOS_RELEASE_DEVICES}
    return {name for name, *_ in ios_live_repair_check_matrix(destinations)}


def _repair_check_identity(
    identity: object, *, expected: bool
) -> dict[str, str]:
    """Validate one repair-check identity before publication."""

    fields = (
        {
            "scope": LIVE_REPAIR_SCOPE,
            "workflow": LIVE_REPAIR_WORKFLOW,
            "repository": LIVE_REPOSITORY,
            "expectedCommit": None,
            "expectedBranch": LIVE_BRANCH,
            "baseline": LIVE_BASELINE_COMMIT,
        }
        if expected
        else {
            "scope": LIVE_REPAIR_SCOPE,
            "workflow": LIVE_REPAIR_WORKFLOW,
            "repository": LIVE_REPOSITORY,
            "commit": None,
            "branch": LIVE_BRANCH,
            "baseline": LIVE_BASELINE_COMMIT,
            "buildId": None,
        }
    )
    commit_field = "expectedCommit" if expected else "commit"
    if (
        not isinstance(identity, dict)
        or set(identity) != set(fields)
        or any(identity[key] != value for key, value in fields.items() if value is not None)
        or not isinstance(identity.get(commit_field), str)
        or re.fullmatch(r"[0-9a-f]{40}", identity[commit_field]) is None
        or (
            not expected
            and (
                not isinstance(identity.get("buildId"), str)
                or re.fullmatch(r"[A-Za-z0-9_-]{1,128}", identity["buildId"]) is None
            )
        )
    ):
        raise ValueError("invalid repair-check identity")
    return dict(sorted(identity.items()))


def _write_live_repair_snapshot(
    root: Path,
    checks: list[dict],
    active: str | None,
    *,
    planned: list[dict[str, object]],
    expected_identity: dict[str, str],
    verified_identity: dict[str, str] | None = None,
    interrupted: bool = False,
    fault: str | None = None,
) -> None:
    """Publish an incremental, non-release result for the fixed repair scope."""

    names = _live_repair_command_names()
    if active not in names | {None, "setup"} or len(checks) > len(names):
        raise ValueError("invalid repair-check progress scope")
    planned_records: list[dict[str, object]] = []
    expected_counts = {name: 1 for name in names}
    for item in planned:
        if (
            not isinstance(item, dict)
            or item.get("name") not in names
            or item.get("expectedTests") != expected_counts[item.get("name")]
        ):
            raise ValueError("invalid repair-check command inventory")
        planned_records.append({"name": item["name"], "expectedTests": item["expectedTests"]})
    planned_names = [item["name"] for item in planned_records]
    if len(set(planned_names)) != len(planned_names) or (planned_names and set(planned_names) != names):
        raise ValueError("repair-check command inventory is incomplete")
    completed = [_published_live_result(check) for check in checks]
    completed_names = [item["name"] for item in completed]
    if (
        len(set(completed_names)) != len(completed_names)
        or not set(completed_names).issubset(names)
        or (planned_names and not set(completed_names).issubset(planned_names))
    ):
        raise ValueError("invalid completed repair-check command")
    for check in completed:
        for image in check.get("diagnosticImages", []):
            path = _safe_live_path(root, image["path"])
            if (
                path.is_symlink()
                or not path.is_file()
                or not _valid_png(path)
                or hashlib.sha256(path.read_bytes()).hexdigest() != image["sha256"]
            ):
                raise ValueError("retained repair diagnostic image is invalid")
    failed = [item for item in completed if item["exit"] != 0]
    not_run = [name for name in planned_names if name not in completed_names and name != active]
    completed_scope = bool(planned_names) and not not_run and active is None
    status = "failed" if failed or fault else "passed" if completed_scope else "incomplete"
    snapshot: dict[str, object] = {
        "scope": LIVE_REPAIR_SCOPE,
        "workflow": LIVE_REPAIR_WORKFLOW,
        "releaseEvidence": False,
        "status": status,
        "runState": "interrupted" if interrupted else status,
        "activeCommand": active,
        "planned": planned_records,
        "completed": completed,
        "failed": failed,
        "notRun": not_run,
        "interrupted": interrupted,
        "expectedIdentity": _repair_check_identity(expected_identity, expected=True),
    }
    if verified_identity is not None:
        snapshot["verifiedIdentity"] = _repair_check_identity(verified_identity, expected=False)
    if fault is not None:
        if fault not in LIVE_PUBLISHED_FAILURE_REASONS:
            raise ValueError("invalid repair-check fault")
        snapshot["fault"] = fault
    _write_live_json_atomically(root, LIVE_REPAIR_SNAPSHOT, snapshot)
    print("live-repair-check=" + json.dumps({
        "activeCommand": active,
        "completedCount": len(completed),
        "releaseEvidence": False,
        "status": status,
    }, sort_keys=True), flush=True)


def _live_repair_setup_failure(error: Exception) -> dict:
    """Build one controlled repair-check setup failure."""

    return {
        "name": "live-repair-check",
        "status": "failed",
        "exit": 1,
        "detail": _live_failure_detail(error),
        "reason": _live_failure_reason(error),
    }


def live_repair_check(artifact_root: Path, expected_commit: str) -> list[dict]:
    """Run only the fixed MCX-19 repair diagnostic scope outside release evidence."""

    try:
        root = _live_artifact_root(artifact_root)
    except (OSError, ValueError) as error:
        return [_live_repair_setup_failure(error)]
    global _ACTIVE_SIMULATOR_LOG_ROOT
    previous_simulator_log_root = _ACTIVE_SIMULATOR_LOG_ROOT
    _ACTIVE_SIMULATOR_LOG_ROOT = root
    expected_identity = {
        "scope": LIVE_REPAIR_SCOPE,
        "workflow": LIVE_REPAIR_WORKFLOW,
        "repository": LIVE_REPOSITORY,
        "expectedCommit": expected_commit,
        "expectedBranch": LIVE_BRANCH,
        "baseline": LIVE_BASELINE_COMMIT,
    }
    verified_identity: dict[str, str] | None = None
    planned: list[dict[str, object]] = []
    checks: list[dict] = []
    active: str | None = "setup"
    interrupted = False

    def snapshot(fault: str | None = None) -> None:
        _write_live_repair_snapshot(
            root, checks, active, planned=planned,
            expected_identity=expected_identity, verified_identity=verified_identity,
            interrupted=interrupted, fault=fault,
        )

    try:
        snapshot()
        context = _live_execution_context(
            artifact_root, expected_commit, LIVE_REPAIR_WORKFLOW
        )
        metadata = _live_repository_metadata(expected_commit)
        verified_identity = {
            "scope": LIVE_REPAIR_SCOPE,
            "workflow": LIVE_REPAIR_WORKFLOW,
            "repository": metadata["repository"],
            "commit": metadata["commit"],
            "branch": context["branch"],
            "baseline": metadata["baseline"],
            "buildId": context["buildId"],
        }
        if tuple(ui_methods()) != (*LIVE_UI_METHODS, LIVE_NORMAL_SETTINGS_METHOD):
            raise ValueError("approved UI test scope does not match the repository")
        destinations = _live_simulator_preflight(root)
        ios = ROOT / "ios" / "ACEClientApp"
        commands = ios_live_repair_check_matrix(destinations)
        planned = [
            {"name": name, "expectedTests": expected}
            for name, _command, _environment, expected in commands
        ]
        if len(planned) != 1:
            raise ValueError("repair-check command scope is invalid")
        active = None
        snapshot()
        for name, command, environment, expected in commands:
            active = name
            snapshot()
            checks.append(_run_live_ios_test(name, command, ios, environment, expected, root))
            active = None
            snapshot()
        if any(check["exit"] != 0 for check in checks):
            detail = _live_command_failure_summary(checks)
            return [{"name": "live-repair-check", "status": "failed", "exit": 1, "detail": detail}]
        return checks
    except KeyboardInterrupt:
        interrupted = True
        try:
            snapshot()
        except (OSError, ValueError):
            pass
        raise
    except (OSError, ValueError, SimulatorResolutionError) as error:
        result = _live_repair_setup_failure(error)
        try:
            snapshot(result["reason"])
        except (OSError, ValueError):
            pass
        return [result]
    finally:
        _ACTIVE_SIMULATOR_LOG_ROOT = previous_simulator_log_root


def live_evidence_checks(artifact_root: Path, expected_commit: str) -> list[dict]:
    """Run the approved manual live scope and fail closed on every control error."""

    try:
        root = _live_artifact_root(artifact_root)
    except (OSError, ValueError) as error:
        return [_live_setup_failure(error)]
    global _ACTIVE_SIMULATOR_LOG_ROOT
    previous_simulator_log_root = _ACTIVE_SIMULATOR_LOG_ROOT
    _ACTIVE_SIMULATOR_LOG_ROOT = root
    manifest: dict[str, object] = {
        "scope": "MCX-19-manual-live-evidence",
        "releaseEvidence": False,
        "status": "failed",
        "privateCollectionStatus": "incomplete",
        "results": [],
        "expectedCommit": expected_commit,
    }
    expected_identity = {
        "scope": "MCX-19-manual-live-evidence",
        "workflow": LIVE_WORKFLOW,
        "repository": LIVE_REPOSITORY,
        "expectedCommit": expected_commit,
        "expectedBranch": LIVE_BRANCH,
        "baseline": LIVE_BASELINE_COMMIT,
    }
    verified_identity: dict[str, str] | None = None
    planned: list[dict[str, object]] = []
    checks: list[dict] = []
    private_collection_checks = checks
    active: str | None = "setup"
    private_collection_status = "incomplete"
    private_collection_finalised = False
    interrupted_run = False

    def finalise_private_collection() -> str:
        """Record a fixed collection status on every normal or failed exit path."""

        nonlocal private_collection_status, private_collection_finalised
        if private_collection_finalised:
            return private_collection_status
        private_collection_status = _finalise_private_live_collection(
            root, planned, private_collection_checks, active, manifest
        )
        private_collection_finalised = True
        manifest["privateCollectionStatus"] = private_collection_status
        try:
            fault = manifest.get("failure")
            _write_live_snapshot(
                root,
                checks,
                active,
                planned=planned,
                expected_identity=expected_identity,
                verified_identity=verified_identity,
                fault=fault if fault in LIVE_PUBLISHED_FAILURE_REASONS else None,
                interrupted=interrupted_run,
                private_collection_status=private_collection_status,
            )
            _write_live_manifest(root, manifest)
        except (OSError, ValueError):
            pass
        return private_collection_status

    try:
        _write_live_manifest(root, manifest)
        _write_live_snapshot(
            root, checks, active, planned=planned, expected_identity=expected_identity
        )
    except (OSError, ValueError) as error:
        return [_live_setup_failure(error)]
    try:
        manifest.update(_live_execution_context(artifact_root, expected_commit))
        _write_live_manifest(root, manifest)
        metadata = _live_repository_metadata(expected_commit)
        manifest.update(metadata)
        manifest.pop("expectedCommit", None)
        build_id = manifest.get("buildId")
        if (
            all(isinstance(metadata.get(field), str) for field in ("repository", "commit", "baseline"))
            and isinstance(build_id, str)
        ):
            verified_identity = {
                "scope": "MCX-19-manual-live-evidence",
                "workflow": LIVE_WORKFLOW,
            "repository": metadata["repository"],
            "commit": metadata["commit"],
            "branch": manifest["branch"],
                "baseline": metadata["baseline"],
                "buildId": build_id,
            }
        _write_live_manifest(root, manifest)
        if tuple(ui_methods()) != (*LIVE_UI_METHODS, LIVE_NORMAL_SETTINGS_METHOD):
            raise ValueError("approved UI test scope does not match the repository")
        manifest["simulatorMetadata"] = "simulator-resolution.json"
        _write_live_manifest(root, manifest)
        destinations = _live_simulator_preflight(root)
        ios = ROOT / "ios" / "ACEClientApp"
        def record(check: dict) -> None:
            nonlocal active
            checks.append(check)
            active = None
            retention_failure = (
                "safe-image-retention-failed"
                if check.get("safe_image_retention_failure")
                else _retain_completed_review_images(root, checks)
            )
            manifest["results"] = [_published_live_result(item) for item in checks]
            _write_live_snapshot(
                root,
                checks,
                None,
                planned=planned,
                expected_identity=expected_identity,
                verified_identity=verified_identity,
                fault=retention_failure,
            )
            _write_live_manifest(root, manifest)
            if retention_failure is not None:
                raise SafeImageRetentionError("safe image retention failed")
            try:
                _verify_private_completed_command(root, planned, check)
                _preserve_private_command_records(root, planned, check, manifest)
            except (OSError, ValueError, json.JSONDecodeError) as error:
                raise PrivateCollectionError(
                    "command-preservation", LIVE_PRIVATE_COLLECTION_FAILURE_REASON, check["name"]
                ) from error
            _require_remote_retention(check["name"])

        commands = [(
            "ios-65-unit",
            ["xcodebuild", "test", "-project", "ACEClientApp.xcodeproj", "-scheme", "ACEClientApp", "-destination", destinations[IOS_CORE_DEVICE], "-only-testing:ACEClientAppTests"],
            ios_test_environment(), 65,
        )]
        commands.extend(ios_release_ui_matrix(destinations, LIVE_UI_METHODS))
        commands.append((
            "ios-evidence-contract",
            ["xcodebuild", "test", "-project", "ACEClientApp.xcodeproj", "-scheme", "ACEClientApp", "-destination", destinations[IOS_CORE_DEVICE], "-only-testing:ACEClientAppTests/AcceptanceEvidenceContractTests"],
            ios_test_environment(), 42,
        ))
        normal_settings_commands = ios_normal_settings_matrix(destinations)
        planned = [
            {"name": name, "expectedTests": expected}
            for name, _command, _environment, expected in commands
        ]
        planned.extend(
            {"name": name, "expectedTests": expected}
            for name, _command, _environment, expected in normal_settings_commands
        )
        planned.append({"name": "ios-negative-config", "expectedTests": None})
        manifest["plannedCommands"] = planned
        _write_live_snapshot(
            root,
            checks,
            None,
            planned=planned,
            expected_identity=expected_identity,
            verified_identity=verified_identity,
        )
        _write_live_manifest(root, manifest)
        for name, command, environment, expected in commands:
            active = name
            _write_live_snapshot(
                root, checks, active, planned=planned,
                expected_identity=expected_identity, verified_identity=verified_identity,
            )
            record(_run_live_ios_test(name, command, ios, environment, expected, root))
        for name, command, environment, expected in normal_settings_commands:
            appearance = environment["ACE_EXPECTED_EFFECTIVE_INTERFACE_STYLE"]
            identifier = command[command.index("-destination") + 1].split("id=", 1)[1]
            active = name
            _write_live_snapshot(
                root, checks, active, planned=planned,
                expected_identity=expected_identity, verified_identity=verified_identity,
            )
            record(_normal_settings_result(
                name, command, ios, environment, root, identifier, appearance
            ))
        negative_log = _safe_live_path(root, "ios-negative-config.log")
        active = "ios-negative-config"
        _write_live_snapshot(
            root, checks, active, planned=planned,
            expected_identity=expected_identity, verified_identity=verified_identity,
        )
        negative_result = _run_live_command(
            "ios-negative-config",
            ios_negative_configuration_command(),
            ios, NEGATIVE_CONFIG_ENVIRONMENT, negative_log,
        )
        record(
            _negative_configuration_result(root, negative_log, negative_result)
        )
        if all(check["exit"] == 0 for check in checks):
            active = "artifact-validation"
            _write_live_snapshot(
                root, checks, active, planned=planned,
                expected_identity=expected_identity, verified_identity=verified_identity,
            )
        raw_checks = checks
        checks = [_published_live_result(check) for check in raw_checks]
        manifest["results"] = checks
        _write_live_manifest(root, manifest)
        if any(check["exit"] != 0 for check in checks):
            detail = _live_command_failure_summary(checks)
            manifest["failure"] = detail
            _write_live_manifest(root, manifest)
            return [{"name": "live-evidence", "status": "failed", "exit": 1, "detail": detail}]
        required_files = {
            "simulator-resolution.json",
            SIMULATOR_RESOLUTION_LOG,
            "ios-negative-config.log",
        }
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
        _write_live_review_manifest(root, manifest, raw_checks, checksums)
        stage = _safe_live_path(root, LIVE_REVIEW_STAGE)
        published = _safe_live_path(root, LIVE_REVIEW_ARTIFACTS)
        if published.exists() or published.is_symlink():
            raise ValueError("published review artifacts already exist")
        _scan_live_artifacts(root)
        os.replace(stage, published)
        active = None
        private_collection_status = finalise_private_collection()
        if private_collection_status != "complete":
            manifest.update({
                "status": (
                    "pending-private-quarantine-review"
                    if private_collection_status == "quarantined-pending-review"
                    else "failed"
                ),
                "privateCollectionStatus": private_collection_status,
                "results": checks,
            })
            _write_live_manifest(root, manifest)
            reason = (
                LIVE_PRIVATE_COLLECTION_QUARANTINE_REASON
                if private_collection_status == "quarantined-pending-review"
                else LIVE_PRIVATE_COLLECTION_FAILURE_REASON
            )
            return [{
                "name": "live-evidence",
                "status": "failed",
                "exit": 1,
                "detail": "private evidence collection requires review"
                if private_collection_status == "quarantined-pending-review"
                else "private evidence collection failed",
                "reason": reason,
            }]
        _write_live_snapshot(
            root, raw_checks, active, planned=planned,
            expected_identity=expected_identity, verified_identity=verified_identity,
            private_collection_status=private_collection_status,
        )
        checksums = _live_artifact_checksums(root)
        _scan_live_artifacts(root)
        _verify_live_artifact_checksums(root, checksums)
        manifest.update({"status": "passed-not-release-evidence", "results": checks, "checksums": checksums})
        _write_live_manifest(root, manifest)
        _verify_live_artifact_checksums(root, checksums)
        return checks
    except KeyboardInterrupt:
        interrupted_run = True
        try:
            _write_live_snapshot(
                root,
                checks,
                active,
                planned=planned,
                expected_identity=expected_identity,
                verified_identity=verified_identity,
                interrupted=True,
            )
        except (OSError, ValueError):
            pass
        raise
    except (OSError, ValueError, SimulatorResolutionError) as error:
        result = _live_setup_failure(error)
        manifest["failure"] = result["reason"]
        if isinstance(error, PrivateCollectionError):
            manifest["retentionDiagnostic"] = {
                "phase": error.phase,
                "category": error.category,
                "command": error.command,
            }
        try:
            _write_live_snapshot(
                root,
                checks,
                active,
                planned=planned,
                expected_identity=expected_identity,
                verified_identity=verified_identity,
                fault=result["reason"],
            )
            _write_live_manifest(root, manifest)
        except (OSError, ValueError):
            pass
        return [result]
    finally:
        try:
            finalise_private_collection()
        finally:
            _ACTIVE_SIMULATOR_LOG_ROOT = previous_simulator_log_root


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
    if tuple(methods) != (*LIVE_UI_METHODS, LIVE_NORMAL_SETTINGS_METHOD):
        return [{"name": "ios-matrix", "status": "unavailable", "exit": 2, "detail": "UI methods do not match the controlled inventory"}]
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
    checks.extend(run_ios_test(f"ios-core-ui-light-{method}", ["xcodebuild", "test", "-project", "ACEClientApp.xcodeproj", "-scheme", "ACEClientAppUITests", "-configuration", "Debug", "-destination", destination, f"-only-testing:ACEClientAppUITests/ACEClientAppUITests/{method}", "ACE_UI_TEST_APPEARANCE=light"], ios, ios_test_environment("light"), 1) for method in LIVE_UI_METHODS)
    if level == "release":
        checks.extend(
            run_ios_test(name, command, ios, environment, expected)
            for name, command, environment, expected in ios_release_ui_matrix(
                destinations, LIVE_UI_METHODS
            )
        )
        checks.extend([run_ios_test("ios-evidence-contract", ["xcodebuild", "test", "-project", "ACEClientApp.xcodeproj", "-scheme", "ACEClientApp", "-destination", destination, "-only-testing:ACEClientAppTests/AcceptanceEvidenceContractTests"], ios, ios_test_environment(), 42), run_command("ios-negative-config", ios_negative_configuration_command(), ios, environment=NEGATIVE_CONFIG_ENVIRONMENT, expected_failure=NEGATIVE_CONFIG_REJECTION)])
    return checks


def _retention_pilot_private_root() -> Path:
    """Return the fixed private root for the manual SSH retention pilot."""

    root = RETENTION_PILOT_PRIVATE_ROOT
    if root.is_symlink():
        raise ValueError("retention pilot private root is unsafe")
    for parent in (root.parent, *root.parents):
        if parent.exists() and parent.is_symlink():
            raise ValueError("retention pilot private root has a symlinked parent")
    root.mkdir(mode=0o700, parents=True, exist_ok=True)
    if root.is_symlink() or not root.is_dir():
        raise ValueError("retention pilot private root is unsafe")
    return root


def _retention_pilot_context(artifact_root: Path, expected_commit: str) -> dict[str, str]:
    """Require the exact, allowlisted manual pilot workflow context."""

    build_directory = os.environ.get("CM_BUILD_DIR")
    build_id = os.environ.get("CM_BUILD_ID")
    if (
        artifact_root != RETENTION_PILOT_ARTIFACT_ROOT
        or not _is_non_empty_string(build_id)
        or re.fullmatch(r"[A-Za-z0-9_-]{1,128}", build_id or "") is None
        or not _is_non_empty_string(build_directory)
        or Path(build_directory).resolve() != ROOT.resolve()
        or os.environ.get(LIVE_WORKFLOW_ENVIRONMENT_KEY) != RETENTION_PILOT_WORKFLOW
        or os.environ.get("CM_COMMIT") != expected_commit
        or os.environ.get("CM_BRANCH") != LIVE_BRANCH
        or not _is_non_empty_string(os.environ.get("CM_BUILD_STARTED_BY"))
    ):
        raise ValueError("verified Codemagic retention pilot context is invalid")
    return {
        "workflow": RETENTION_PILOT_WORKFLOW,
        "repository": LIVE_REPOSITORY,
        "commit": expected_commit,
        "branch": LIVE_BRANCH,
        "buildId": build_id,
    }


def _retention_pilot_phase_path(root: Path, build_id: str, phase: str) -> Path:
    """Return one fixed, allowlisted checkpoint path without caller path input."""

    if phase not in RETENTION_PILOT_PHASES:
        raise ValueError("retention pilot phase is invalid")
    path = root / "checkpoints" / build_id / phase
    if path.resolve(strict=False).is_relative_to(root.resolve()) is False:
        raise ValueError("retention pilot checkpoint path is invalid")
    return path


def _retention_pilot_ack_path(root: Path, build_id: str, phase: str) -> Path:
    """Return the fixed operator ACK path for one allowed pilot phase."""

    if phase not in RETENTION_PILOT_PHASES:
        raise ValueError("retention pilot phase is invalid")
    path = root / "acks" / build_id / f"{phase}.ack.json"
    if path.resolve(strict=False).is_relative_to(root.resolve()) is False:
        raise ValueError("retention pilot ACK path is invalid")
    return path


def _retention_pilot_copy_records(
    artifact_root: Path, private_root: Path, phase: str, candidate: dict[str, str],
    allow_partial: bool = False,
) -> tuple[Path, str, dict[str, str], dict[str, str]]:
    """Copy and hash the fixed probe or one successful individual XCTest record."""

    checkpoint = _retention_pilot_phase_path(private_root, candidate["buildId"], phase)
    if checkpoint.exists() or checkpoint.is_symlink():
        raise ValueError("retention pilot checkpoint already exists")
    stage = checkpoint.with_name(f".{phase}.tmp")
    if stage.exists() or stage.is_symlink():
        raise ValueError("retention pilot checkpoint stage is unsafe")
    records: dict[str, str] = {}
    scanner_status: dict[str, str] = {}
    try:
        stage.mkdir(mode=0o700, parents=True)
        if phase == "transport-probe":
            source = stage / "records" / "transport-probe.txt"
            source.parent.mkdir(mode=0o700, parents=True)
            source.write_text("MCX-19 fictional SSH transport probe\n", encoding="utf-8")
            records["records/transport-probe.txt"] = hashlib.sha256(source.read_bytes()).hexdigest()
            scanner_status["records/transport-probe.txt"] = "complete"
        else:
            sources = [
                (f"{phase}.log", "records/log"),
                (f"{phase}-summary.json", "records/summary.json"),
                (f"{phase}.xcresult", "records/result.xcresult"),
                (f"{phase}-attachment-export.log", "records/source-export.log"),
                (f"{phase}-attachment-export", "records/source-export"),
                (f"{LIVE_REVIEW_STAGE}/{LIVE_SCREENSHOT_DIRECTORY}/{phase}", "records/screenshots"),
                ("simulator-operations", "records/simulator-operations"),
            ]
            for relative, destination in sources:
                source = _safe_live_path(artifact_root, relative)
                if source.is_symlink() or not source.exists():
                    if allow_partial:
                        continue
                    raise ValueError("retention pilot required record is missing")
                files = [source] if source.is_file() else _private_collection_regular_files(source)
                if not files:
                    if allow_partial:
                        continue
                    raise ValueError("retention pilot required record is empty")
                for item in files:
                    suffix = "" if source.is_file() else _private_collection_relative(source, item)
                    target = stage / destination / suffix if suffix else stage / destination
                    target.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
                    archive_path = (
                        f"records/commands/{phase}/"
                        f"{target.relative_to(stage / 'records').as_posix()}"
                    )
                    source_root = artifact_root if source.is_file() else source
                    original_metadata = _private_collection_file_metadata(
                        source_root, item, archive_path, phase
                    )
                    shutil.copyfile(item, target)
                    if target.is_symlink() or not target.is_file():
                        raise ValueError("retention pilot copied record is invalid")
                    copied_metadata = _private_collection_file_metadata(
                        stage, target, archive_path, phase
                    )
                    if copied_metadata != original_metadata:
                        raise ValueError("retention pilot copied record changed")
                    record_path = target.relative_to(stage).as_posix()
                    records[record_path] = copied_metadata[1]
                    scanner_status[record_path] = copied_metadata[2]
            if allow_partial and not records:
                raise ValueError("retention pilot has no failed-case record")
        manifest = {
            "schemaVersion": 1,
            "candidate": candidate,
            "phaseId": phase,
            "records": records,
            "recordScannerStatus": scanner_status,
            "collectionStatus": "incomplete" if allow_partial else "complete",
            "releaseEvidence": False,
        }
        manifest_bytes = json.dumps(manifest, indent=2, sort_keys=True).encode("utf-8") + b"\n"
        (stage / "checkpoint-manifest.json").write_bytes(manifest_bytes)
        manifest_sha = hashlib.sha256(manifest_bytes).hexdigest()
        os.replace(stage, checkpoint)
        return checkpoint, manifest_sha, records, scanner_status
    except (OSError, ValueError):
        if stage.exists() and stage.is_dir() and not stage.is_symlink():
            shutil.rmtree(stage)
        raise


def _retention_pilot_ack_valid(
    path: Path, candidate: dict[str, str], phase: str, manifest_sha: str, records: dict[str, str]
) -> bool:
    """Accept only the exact fixed ACK that binds this stored checkpoint."""

    try:
        if path.is_symlink() or not path.is_file() or path.stat().st_size > 1024 * 1024:
            return False
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError, json.JSONDecodeError):
        return False
    return (
        isinstance(value, dict)
        and set(value) == {
            "schemaVersion", "commit", "buildId", "phaseId", "checkpointManifestSha256", "recordSha256"
        }
        and value.get("schemaVersion") == 1
        and value.get("commit") == candidate["commit"]
        and value.get("buildId") == candidate["buildId"]
        and value.get("phaseId") == phase
        and value.get("checkpointManifestSha256") == manifest_sha
        and value.get("recordSha256") == records
    )


def _retention_pilot_records_match(checkpoint: Path, records: dict[str, str]) -> bool:
    """Rehash every stored record before an ACK can release the next test."""

    if not records:
        return False
    try:
        for relative, expected in records.items():
            path = checkpoint / relative
            if (
                not isinstance(relative, str)
                or not isinstance(expected, str)
                or re.fullmatch(r"[0-9a-f]{64}", expected) is None
                or path.is_symlink()
                or not path.is_file()
                or not path.resolve().is_relative_to(checkpoint.resolve())
                or hashlib.sha256(path.read_bytes()).hexdigest() != expected
            ):
                return False
    except OSError:
        return False
    return True


def _retention_pilot_wait_for_ack(
    private_root: Path, candidate: dict[str, str], phase: str, manifest_sha: str,
    records: dict[str, str], timeout_seconds: int = RETENTION_PILOT_ACK_TIMEOUT_SECONDS,
) -> bool:
    """Wait only for an exact operator ACK and record every blocked poll privately."""

    checkpoint = _retention_pilot_phase_path(private_root, candidate["buildId"], phase)
    ack = _retention_pilot_ack_path(private_root, candidate["buildId"], phase)
    ack.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    blocked = checkpoint / "blocked-polls.jsonl"
    deadline = time.monotonic() + timeout_seconds
    while True:
        if (
            _retention_pilot_records_match(checkpoint, records)
            and _retention_pilot_ack_valid(ack, candidate, phase, manifest_sha, records)
        ):
            receipt = {
                "schemaVersion": 1,
                "phaseId": phase,
                "checkpointManifestSha256": manifest_sha,
                "ackSha256": hashlib.sha256(ack.read_bytes()).hexdigest(),
            }
            (checkpoint / "ack-receipt.json").write_text(
                json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8"
            )
            return True
        with blocked.open("a", encoding="utf-8") as stream:
            stream.write(json.dumps({"event": "ack-blocked", "phaseId": phase}, sort_keys=True) + "\n")
        if time.monotonic() >= deadline:
            (checkpoint / "retention-diagnostic.json").write_text(
                json.dumps({"phase": phase, "category": "operator-ack-timeout"}, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            return False
        time.sleep(RETENTION_PILOT_ACK_POLL_SECONDS)


def _retention_pilot_report_scanner_status(statuses: dict[str, str]) -> dict[str, object]:
    """Publish scanner totals only; private manifests retain record paths."""

    counts = {status: list(statuses.values()).count(status) for status in
              ("complete", "quarantined-pending-review", _PRIVATE_COLLECTION_ADJUDICATED_PNG_STATUS)}
    return {
        "recordScannerStatusCounts": counts,
        "scannerReviewStatus": "pending-review" if counts["quarantined-pending-review"] else "complete",
    }


def _retention_pilot_archive(
    private_root: Path, candidate: dict[str, str], success: bool = True
) -> Path:
    """Archive a complete ACKed pilot or an explicit incomplete diagnostic."""

    checkpoints = private_root / "checkpoints" / candidate["buildId"]
    if checkpoints.is_symlink() or not checkpoints.is_dir():
        raise ValueError("retention pilot checkpoints are unavailable")
    archive = private_root / RETENTION_PILOT_ARCHIVE
    temporary = private_root / f".{RETENTION_PILOT_ARCHIVE}.tmp"
    if archive.exists() or archive.is_symlink() or temporary.exists() or temporary.is_symlink():
        raise ValueError("retention pilot archive path is unsafe")
    checkpoint_paths = sorted(checkpoints.iterdir())
    phase_checkpoints = [path for path in checkpoint_paths if path.is_dir() and not path.is_symlink()]
    if len(phase_checkpoints) != len(checkpoint_paths) or any(
        path.name not in RETENTION_PILOT_PHASES for path in phase_checkpoints
    ):
        raise ValueError("retention pilot checkpoint path is invalid")
    if success and {path.name for path in phase_checkpoints} != set(RETENTION_PILOT_PHASES):
        raise ValueError("retention pilot success archive requires all pilot phases")
    available_files = _private_collection_regular_files(checkpoints)
    if not available_files:
        raise ValueError("retention pilot archive has no records")
    expected_record_hashes: dict[Path, str] = {}
    expected_manifest_hashes: dict[Path, str] = {}
    expected_receipt_hashes: dict[Path, str] = {}
    expected_control_hashes: dict[Path, str] = {}
    expected_acks: dict[Path, tuple[Path, str, str, str, dict[str, str]]] = {}
    validated_files: set[Path] = set()
    archive_members: list[tuple[Path, str]] = []
    for checkpoint in phase_checkpoints:
        manifest_path = checkpoint / "checkpoint-manifest.json"
        try:
            manifest_bytes = manifest_path.read_bytes()
            manifest = json.loads(manifest_bytes)
        except (OSError, ValueError, json.JSONDecodeError) as error:
            raise ValueError("retention pilot checkpoint manifest is invalid") from error
        if (
            not isinstance(manifest, dict)
            or set(manifest) != {
                "schemaVersion", "candidate", "phaseId", "records", "recordScannerStatus",
                "collectionStatus", "releaseEvidence",
            }
            or manifest.get("schemaVersion") != 1
            or manifest.get("candidate") != candidate
            or manifest.get("phaseId") != checkpoint.name
            or manifest.get("releaseEvidence") is not False
            or manifest.get("collectionStatus") not in {"complete", "incomplete"}
            or (success and manifest.get("collectionStatus") != "complete")
            or not isinstance(manifest.get("records"), dict)
            or not isinstance(manifest.get("recordScannerStatus"), dict)
            or set(manifest["records"]) != set(manifest["recordScannerStatus"])
            or any(not isinstance(path, str) or not isinstance(digest, str)
                   for path, digest in manifest["records"].items())
            or any(status not in {
                "complete", "quarantined-pending-review", _PRIVATE_COLLECTION_ADJUDICATED_PNG_STATUS,
            }
                   for status in manifest["recordScannerStatus"].values())
            or not _retention_pilot_records_match(checkpoint, manifest["records"])
        ):
            raise ValueError("retention pilot checkpoint verification failed")
        manifest_sha = hashlib.sha256(manifest_bytes).hexdigest()
        expected_manifest_hashes[manifest_path] = manifest_sha
        validated_files.add(manifest_path)
        expected_record_hashes.update({
            checkpoint / relative: digest
            for relative, digest in manifest["records"].items()
        })
        validated_files.update(expected_record_hashes)
        blocked = checkpoint / "blocked-polls.jsonl"
        if blocked.exists():
            try:
                if blocked.is_symlink() or not blocked.is_file() or blocked.stat().st_size > 1024 * 1024:
                    raise ValueError("retention pilot blocked-poll control is invalid")
                blocked_values = [json.loads(line) for line in blocked.read_text(encoding="utf-8").splitlines()]
            except (OSError, ValueError, json.JSONDecodeError) as error:
                raise ValueError("retention pilot blocked-poll control is invalid") from error
            if not blocked_values or any(
                not isinstance(value, dict) or value != {"event": "ack-blocked", "phaseId": checkpoint.name}
                for value in blocked_values
            ):
                raise ValueError("retention pilot blocked-poll control is invalid")
            expected_control_hashes[blocked] = hashlib.sha256(blocked.read_bytes()).hexdigest()
            validated_files.add(blocked)
        diagnostic = checkpoint / "retention-diagnostic.json"
        if diagnostic.exists():
            try:
                if diagnostic.is_symlink() or not diagnostic.is_file() or diagnostic.stat().st_size > 1024 * 1024:
                    raise ValueError("retention pilot diagnostic control is invalid")
                diagnostic_value = json.loads(diagnostic.read_text(encoding="utf-8"))
            except (OSError, ValueError, json.JSONDecodeError) as error:
                raise ValueError("retention pilot diagnostic control is invalid") from error
            if diagnostic_value not in (
                {"phase": checkpoint.name, "category": "operator-ack-timeout"},
                {"phase": checkpoint.name, "category": "native-test-failed"},
                {"phase": checkpoint.name, "category": "safe-image-retention-failed"},
            ):
                raise ValueError("retention pilot diagnostic control is invalid")
            expected_control_hashes[diagnostic] = hashlib.sha256(diagnostic.read_bytes()).hexdigest()
            validated_files.add(diagnostic)
        receipt = checkpoint / "ack-receipt.json"
        if receipt.exists():
            try:
                receipt_bytes = receipt.read_bytes()
                ack_receipt = json.loads(receipt_bytes)
            except (OSError, ValueError, json.JSONDecodeError) as error:
                raise ValueError("retention pilot ACK receipt is invalid") from error
            ack = _retention_pilot_ack_path(private_root, candidate["buildId"], checkpoint.name)
            if (
                not isinstance(ack_receipt, dict)
                or set(ack_receipt) != {
                    "schemaVersion", "phaseId", "checkpointManifestSha256", "ackSha256"
                }
                or ack_receipt.get("schemaVersion") != 1
                or ack_receipt.get("phaseId") != checkpoint.name
                or ack_receipt.get("checkpointManifestSha256") != manifest_sha
                or not _retention_pilot_ack_valid(
                    ack, candidate, checkpoint.name, manifest_sha, manifest["records"]
                )
                or ack_receipt.get("ackSha256") != hashlib.sha256(ack.read_bytes()).hexdigest()
            ):
                raise ValueError("retention pilot ACK receipt is invalid")
            expected_receipt_hashes[receipt] = hashlib.sha256(receipt_bytes).hexdigest()
            expected_acks[receipt] = (
                ack, ack_receipt["ackSha256"], checkpoint.name, manifest_sha, manifest["records"]
            )
            expected_acks[ack] = expected_acks[receipt]
            validated_files.add(receipt)
            archive_members.append((ack, f"acks/{candidate['buildId']}/{checkpoint.name}.ack.json"))
        elif success:
            raise ValueError("retention pilot success archive requires an ACK receipt")
    if set(available_files) != validated_files:
        raise ValueError("retention pilot has an unexpected checkpoint entry")
    archive_members.extend(
        (path, path.relative_to(private_root).as_posix()) for path in sorted(validated_files)
    )
    with tarfile.open(temporary, "w:gz", format=tarfile.PAX_FORMAT) as output:
        expected_archive: dict[str, tuple[int, str]] = {}
        for path, relative in archive_members:
            data = path.read_bytes()
            if len(data) > LIVE_PRIVATE_COLLECTION_MAX_FILE_BYTES:
                raise ValueError("retention pilot archive record exceeds the size limit")
            digest = hashlib.sha256(data).hexdigest()
            if path in expected_record_hashes and digest != expected_record_hashes[path]:
                raise ValueError("retention pilot record changed during packaging")
            if path in expected_manifest_hashes and digest != expected_manifest_hashes[path]:
                raise ValueError("retention pilot manifest changed during packaging")
            if path in expected_receipt_hashes and digest != expected_receipt_hashes[path]:
                raise ValueError("retention pilot ACK receipt changed during packaging")
            if path in expected_control_hashes and digest != expected_control_hashes[path]:
                raise ValueError("retention pilot control changed during packaging")
            if path in expected_acks:
                ack, ack_sha, phase, manifest_sha, records = expected_acks[path]
                if (
                    not _retention_pilot_ack_valid(ack, candidate, phase, manifest_sha, records)
                    or hashlib.sha256(ack.read_bytes()).hexdigest() != ack_sha
                ):
                    raise ValueError("retention pilot ACK changed during packaging")
            expected_archive[relative] = (len(data), digest)
            info = output.gettarinfo(str(path), arcname=relative)
            if not info.isreg():
                raise ValueError("retention pilot archive record is unsafe")
            info.uid = info.gid = 0
            info.uname = info.gname = ""
            info.mtime = 0
            output.addfile(info, io.BytesIO(data))
    _verify_private_collection_archive(temporary, expected_archive)
    os.replace(temporary, archive)
    return archive


def retention_pilot_checks(artifact_root: Path, expected_commit: str) -> list[dict]:
    """Run two individual fictional UI tests through the attended SSH ACK protocol."""

    root: Path | None = None
    private_root: Path | None = None
    candidate: dict[str, str] | None = None
    report: dict[str, object] | None = None
    checks: list[dict] = []
    try:
        root = _live_artifact_root(artifact_root)
        candidate = _retention_pilot_context(artifact_root, expected_commit)
        metadata = _live_repository_metadata(expected_commit)
        if metadata["commit"] != candidate["commit"]:
            raise ValueError("retention pilot repository binding is invalid")
        private_root = _retention_pilot_private_root()
        report = {
            "scope": "MCX-19-manual-retention-pilot",
            "releaseEvidence": False,
            "candidate": candidate,
            "status": "awaiting-operator-ack",
            "phases": [],
        }
        _write_live_json_atomically(root, "retention-pilot-report.json", report)
        probe, probe_sha, probe_records, probe_status = _retention_pilot_copy_records(root, private_root, "transport-probe", candidate)
        report["phases"].append({"phaseId": "transport-probe", "checkpoint": str(probe), "manifestSha256": probe_sha, **_retention_pilot_report_scanner_status(probe_status)})
        _write_live_json_atomically(root, "retention-pilot-report.json", report)
        if not _retention_pilot_wait_for_ack(private_root, candidate, "transport-probe", probe_sha, probe_records):
            report["status"] = "blocked"
            report["archive"] = str(_retention_pilot_archive(private_root, candidate, success=False))
            _write_live_json_atomically(root, "retention-pilot-report.json", report)
            return [{"name": "retention-pilot", "status": "blocked", "exit": 1, "detail": "operator ACK was not accepted"}]
        destinations = _live_simulator_preflight(root)
        ios = ROOT / "ios" / "ACEClientApp"
        for phase in RETENTION_PILOT_PHASES[1:]:
            method = phase.rsplit("-", 1)[1]
            command = [
                "xcodebuild", "test", "-project", "ACEClientApp.xcodeproj", "-scheme", "ACEClientAppUITests",
                "-configuration", "Debug", "-destination", destinations[IOS_CORE_DEVICE],
                f"-only-testing:ACEClientAppUITests/ACEClientAppUITests/{method}", "ACE_UI_TEST_APPEARANCE=light",
            ]
            check = _run_live_ios_test(phase, command, ios, ios_test_environment("light"), 1, root)
            checks.append(check)
            image_failure = _retain_completed_review_images(root, checks)
            if check.get("exit") != 0 or image_failure is not None:
                category = "native-test-failed" if check.get("exit") != 0 else "safe-image-retention-failed"
                checkpoint, manifest_sha, _records, scanner_status = _retention_pilot_copy_records(
                    root, private_root, phase, candidate, allow_partial=True
                )
                (checkpoint / "retention-diagnostic.json").write_text(
                    json.dumps({"phase": phase, "category": category}, sort_keys=True) + "\n",
                    encoding="utf-8",
                )
                report["phases"].append({
                    "phaseId": phase, "checkpoint": str(checkpoint), "manifestSha256": manifest_sha,
                    "collectionStatus": "incomplete", **_retention_pilot_report_scanner_status(scanner_status),
                })
                report["status"] = "failed"
                report["failure"] = category
                report["results"] = [{"name": item["name"], "exit": item["exit"]} for item in checks]
                report["archive"] = str(_retention_pilot_archive(private_root, candidate, success=False))
                _write_live_json_atomically(root, "retention-pilot-report.json", report)
                return [{"name": "retention-pilot", "status": "failed", "exit": 1, "detail": category}]
            checkpoint, manifest_sha, records, scanner_status = _retention_pilot_copy_records(root, private_root, phase, candidate)
            report["phases"].append({"phaseId": phase, "checkpoint": str(checkpoint), "manifestSha256": manifest_sha, **_retention_pilot_report_scanner_status(scanner_status)})
            _write_live_json_atomically(root, "retention-pilot-report.json", report)
            if not _retention_pilot_wait_for_ack(private_root, candidate, phase, manifest_sha, records):
                report["status"] = "blocked"
                report["archive"] = str(_retention_pilot_archive(private_root, candidate, success=False))
                _write_live_json_atomically(root, "retention-pilot-report.json", report)
                return [{"name": "retention-pilot", "status": "blocked", "exit": 1, "detail": "operator ACK was not accepted"}]
        archive = _retention_pilot_archive(private_root, candidate)
        report["status"] = "complete"
        report["archive"] = str(archive)
        report["results"] = [{"name": check["name"], "exit": check["exit"]} for check in checks]
        _write_live_json_atomically(root, "retention-pilot-report.json", report)
        return [{"name": "retention-pilot", "status": "passed", "exit": 0, "detail": "two individual fictional UI tests retained after exact ACKs"}]
    except (OSError, ValueError, SimulatorResolutionError) as error:
        if root is not None and private_root is not None and candidate is not None and report is not None:
            report["status"] = "failed"
            report["failure"] = "retention-pilot-failed"
            report["results"] = [{"name": item["name"], "exit": item["exit"]} for item in checks]
            try:
                report["archive"] = str(_retention_pilot_archive(private_root, candidate, success=False))
            except (OSError, ValueError):
                report["archive"] = "unavailable"
            try:
                _write_live_json_atomically(root, "retention-pilot-report.json", report)
            except (OSError, ValueError):
                pass
        return [{"name": "retention-pilot", "status": "failed", "exit": 1, "detail": str(error)}]


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("level", choices=["focused", "core", "release", "evidence-check", "live-evidence", "live-repair-check", "retention-pilot"])
    parser.add_argument("--component", choices=["python", "web", "ios"])
    parser.add_argument("--artifact-root")
    parser.add_argument("--expected-commit")
    args = parser.parse_args(argv)
    data, mapping_errors = load_mapping()
    if args.level != "evidence-check" and not args.component:
        parser.error("--component is required except for evidence-check")
    if args.level in {"live-evidence", "live-repair-check", "retention-pilot"} and args.component != "ios":
        parser.error(f"{args.level} requires --component ios")
    if args.level in {"live-evidence", "live-repair-check", "retention-pilot"} and args.artifact_root is None:
        parser.error(f"{args.level} requires --artifact-root")
    if args.level in {"live-evidence", "live-repair-check", "retention-pilot"} and (
        args.expected_commit is None
        or re.fullmatch(r"[0-9a-f]{40}", args.expected_commit) is None
    ):
        parser.error(f"{args.level} requires --expected-commit as a lower-case 40-hex SHA")
    results = []
    if mapping_errors:
        results.append({"name": "mapping", "status": "failed", "exit": 1, "detail": "; ".join(mapping_errors)})
    elif args.level == "evidence-check":
        results.append({"name": "public-g0-preflight", "status": "passed", "exit": 0, "detail": f"44 source IDs map once to G1-G6; {data['evidencePreflightState']}; manual evidence was not run"})
    elif args.level == "live-evidence":
        results.extend(live_evidence_checks(Path(args.artifact_root), args.expected_commit))
    elif args.level == "live-repair-check":
        results.extend(live_repair_check(Path(args.artifact_root), args.expected_commit))
    elif args.level == "retention-pilot":
        results.extend(retention_pilot_checks(Path(args.artifact_root), args.expected_commit))
    else:
        results.extend(component_checks(args.level, args.component))
    exits = {item["exit"] for item in results}
    exit_code = 1 if 1 in exits else 2 if 2 in exits else 0
    if args.level == "live-evidence":
        print("report=external-artifact-root/live-evidence-manifest.json")
    elif args.level == "live-repair-check":
        print(f"report=external-artifact-root/{LIVE_REPAIR_SNAPSHOT}")
    elif args.level == "retention-pilot":
        print("report=external-artifact-root/retention-pilot-report.json")
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
