#!/usr/bin/env python3
"""Run controlled local ACE iOS verification.

Commands are ``preflight``, ``selected``, ``pilot``, and ``full``.  The runner
uses only Python's standard library and Apple command-line tools.  It keeps
build products and evidence on the Mac.  ``pilot`` and ``full`` fail closed
unless they can freeze a clean candidate, build it generically, use its
generated xctestrun file, retain native result bundles, and inspect every
native batch record.  Do not use this tool to export bulk evidence to Windows.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import plistlib
import re
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from collections import defaultdict
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable

ROOT = Path(__file__).resolve().parents[1]
IOS_ROOT = ROOT / "ios" / "ACEClientApp"
PROJECT = IOS_ROOT / "ACEClientApp.xcodeproj"
SCHEME = "ACEClientAppUITests"
PYTHON_RUNTIME = "/Library/Frameworks/Python.framework/Versions/3.14/bin/python3"
RUNTIME = "iOS 26.4.1"
DEVICES = ("iPhone 17", "iPhone 17 Pro Max")
SCENARIOS = (
    "signIn", "loading", "release", "emptyRelease", "emptyEngagement",
    "noConclusion", "noActions", "denied", "unavailable", "unexpected",
    "connection", "timeout", "invalidResponse", "keychainRead",
    "keychainWrite", "keychainDeletion", "copyConfirmation", "privacy",
)
COMPLEX_SCENARIOS = ("signIn", "release", "noConclusion", "noActions", "copyConfirmation")
TEXT_SIZES = (
    "extra-small", "small", "medium", "large", "extra-large",
    "extra-extra-large", "extra-extra-extra-large", "accessibility-medium",
    "accessibility-large", "accessibility-extra-large",
    "accessibility-extra-extra-large", "accessibility-extra-extra-extra-large",
)
DEFAULT_SIZE = "large"
EXL_SIZE = "extra-large"
MAX_SIZE = "accessibility-extra-extra-extra-large"
COVERAGE_SELECTOR = "ACEClientAppUITests/ACEClientAppUITests/testCoverageBatch"
SETTINGS_SELECTOR = "ACEClientAppUITests/ACEClientAppUITests/testConfigureAccessibilitySettings"
OLD_UI_SELECTORS = (
    "ACEClientAppUITests/ACEClientAppUITests/testBothAppearances",
    "ACEClientAppUITests/ACEClientAppUITests/testLaunchShowsSafeConfigurationState",
    "ACEClientAppUITests/ACEClientAppUITests/testSignInPasswordFieldIsSecure",
    "ACEClientAppUITests/ACEClientAppUITests/testFictionalReleaseHasApprovedCopyControls",
    "ACEClientAppUITests/ACEClientAppUITests/testClippingNoActionsStandaloneAudit",
    "ACEClientAppUITests/ACEClientAppUITests/testClippingNoConclusionStandaloneAudit",
    "ACEClientAppUITests/ACEClientAppUITests/testAllControlledScenariosShowExpectedStateAndAudit",
    "ACEClientAppUITests/ACEClientAppUITests/testReleaseOrientationHooks",
    "ACEClientAppUITests/ACEClientAppUITests/testNormalDeviceSettings",
)
MIN_FREE_BYTES = 20 * 1024**3
CASE_MARKER = "ACE_CASE_RESULT "
SETTINGS_MARKER = "ACE_SETTINGS_RESULT "
SELECTED_UI_ENVIRONMENT_KEYS = {
    "ACE_UI_TEST_APPEARANCE": {"light", "dark"},
    "ACE_EXPECTED_EFFECTIVE_INTERFACE_STYLE": {"light", "dark"},
    "ACE_EXPECTED_CONTENT_SIZE_CATEGORY": set(TEXT_SIZES),
    "ACE_UI_TEST_RETAIN_INITIAL_AUDIT_SCREENSHOT": {"0", "1"},
}


class RunnerError(RuntimeError):
    """A required controlled condition was not available."""


@dataclass(frozen=True)
class Settings:
    appearance: str
    contentSize: str
    orientation: str
    boldText: bool = False
    reduceMotion: bool = False
    increaseContrast: bool = False

    def payload(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class Case:
    id: str
    group: str
    device: str
    scenario: str
    settings: Settings
    audit: bool

    def payload(self) -> dict[str, object]:
        return {"id": self.id, "scenario": self.scenario, "settings": self.settings.payload(), "audit": self.audit}


def _case_id(group: str, device: str, scenario: str, settings: Settings) -> str:
    values = (group, device, scenario, settings.appearance, settings.contentSize, settings.orientation,
              str(int(settings.boldText)), str(int(settings.reduceMotion)), str(int(settings.increaseContrast)))
    return ".".join(re.sub(r"[^A-Za-z0-9]+", "-", value).strip("-") for value in values)


def make_case(group: str, device: str, scenario: str, settings: Settings, audit: bool) -> Case:
    return Case(_case_id(group, device, scenario, settings), group, device, scenario, settings, audit)


def coverage_cases() -> tuple[Case, ...]:
    """Create the approved 836 unique configurations with their audit assignment."""
    cases: dict[tuple[str, str, Settings], Case] = {}

    def add(group: str, device: str, scenario: str, settings: Settings, audit: bool) -> None:
        key = (device, scenario, settings)
        if key in cases:
            return
        cases[key] = make_case(group, device, scenario, settings, audit)

    for device in DEVICES:
        for orientation in ("portrait", "landscape"):
            for appearance in ("light", "dark"):
                settings = Settings(appearance, DEFAULT_SIZE, orientation)
                for scenario in SCENARIOS:
                    add("standard", device, scenario, settings, True)
    for device in DEVICES:
        for size in TEXT_SIZES:
            for scenario in SCENARIOS:
                add("text", device, scenario, Settings("light", size, "portrait"), size in (EXL_SIZE, MAX_SIZE))
    for device in DEVICES:
        for size in (EXL_SIZE, MAX_SIZE):
            for orientation in ("portrait", "landscape"):
                for appearance in ("light", "dark"):
                    for scenario in COMPLEX_SCENARIOS:
                        add("difficult", device, scenario, Settings(appearance, size, orientation), True)
    for device in DEVICES:
        for appearance in ("light", "dark"):
            for flag in ("boldText", "reduceMotion", "increaseContrast"):
                values = {"boldText": False, "reduceMotion": False, "increaseContrast": False, flag: True}
                settings = Settings(appearance, DEFAULT_SIZE, "portrait", **values)
                for scenario in SCENARIOS:
                    add("individual", device, scenario, settings, True)
    for device in DEVICES:
        for appearance in ("light", "dark"):
            settings = Settings(appearance, MAX_SIZE, "landscape", True, True, True)
            for scenario in COMPLEX_SCENARIOS:
                add("combined", device, scenario, settings, True)
    result = tuple(cases.values())
    if len(result) != 836 or sum(case.audit for case in result) != 512:
        raise AssertionError("approved coverage matrix changed")
    return result


def coverage_batches(cases: Iterable[Case]) -> tuple[tuple[str, Settings, tuple[Case, ...]], ...]:
    cases = tuple(cases)
    grouped: dict[tuple[str, Settings], list[Case]] = defaultdict(list)
    for case in cases:
        grouped[(case.device, case.settings)].append(case)
    batches = tuple((device, settings, tuple(values)) for (device, settings), values in grouped.items())
    if cases == coverage_cases() and len(batches) != 58:
        raise AssertionError("approved setting batch count changed")
    return batches


def pilot_cases() -> tuple[Case, ...]:
    cases: list[Case] = []
    for device in DEVICES:
        for scenario in COMPLEX_SCENARIOS:
            cases.append(make_case("pilot", device, scenario, Settings("light", DEFAULT_SIZE, "portrait"), True))
            cases.append(make_case("pilot", device, scenario, Settings("dark", MAX_SIZE, "landscape", True, True, True), True))
        cases.append(make_case("pilot", device, "release", Settings("light", "medium", "portrait"), False))
    if len(cases) != 22:
        raise AssertionError("approved pilot changed")
    return tuple(cases)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def command(command: list[str], cwd: Path | None = None, timeout: int = 1800, env: dict[str, str] | None = None) -> dict[str, object]:
    started = datetime.now(timezone.utc).isoformat()
    started_clock = time.monotonic()
    try:
        result = subprocess.run(command, cwd=cwd, env=env, text=True, capture_output=True, timeout=timeout, check=False)
    except subprocess.TimeoutExpired as error:
        def partial(value: object) -> str:
            return value.decode("utf-8", errors="replace") if isinstance(value, bytes) else str(value or "")
        return {"command": command, "start": started, "end": datetime.now(timezone.utc).isoformat(),
                "exit": None, "timedOut": True, "error": str(error), "stdout": partial(error.stdout),
                "stderr": partial(error.stderr), "seconds": round(time.monotonic() - started_clock, 3)}
    except OSError as error:
        return {"command": command, "start": started, "end": datetime.now(timezone.utc).isoformat(),
                "exit": None, "timedOut": False, "error": str(error), "stdout": "", "stderr": "",
                "seconds": round(time.monotonic() - started_clock, 3)}
    return {"command": command, "exit": result.returncode, "stdout": result.stdout, "stderr": result.stderr,
            "timedOut": False, "start": started, "end": datetime.now(timezone.utc).isoformat(), "seconds": round(time.monotonic() - started_clock, 3)}


def checked(command_line: list[str], **kwargs: Any) -> dict[str, object]:
    record = command(command_line, **kwargs)
    if record.get("exit") != 0:
        raise RunnerError(f"command failed: {' '.join(command_line)}")
    return record


def json_command(command_line: list[str]) -> object:
    record = checked(command_line, timeout=30)
    try:
        return json.loads(str(record["stdout"]))
    except json.JSONDecodeError as error:
        raise RunnerError(f"command did not return JSON: {' '.join(command_line)}") from error


def git_value(*args: str) -> str:
    return str(checked(["git", *args], cwd=ROOT, timeout=30)["stdout"]).strip()


def candidate(allow_dirty: bool = False) -> dict[str, object]:
    status = git_value("status", "--porcelain")
    if status and not allow_dirty:
        raise RunnerError("candidate is not clean")
    commit = git_value("rev-parse", "HEAD")
    tracked = git_value("ls-files") + "\n" + git_value("ls-files", "--others", "--exclude-standard")
    source_hashes: dict[str, str] = {}
    for path in tracked.splitlines():
        if path.startswith(("ios/", "docs/plans/", "docs/specs/", "quality/")) or path.startswith("tools/"):
            item = ROOT / path
            if item.is_file():
                source_hashes[path] = sha256(item)
    for path in ("tools/ace_ios_local.py", "tools/tests/test_ace_ios_local.py"):
        item = ROOT / path
        if item.is_file():
            source_hashes[path] = sha256(item)
    tracked_paths = tuple(source_hashes)
    dirty_diff = git_value("diff", "--binary", "--", *tracked_paths) if status else ""
    return {"commit": commit, "status": "dirty" if status else "clean", "statusDetail": status,
            "workingTreeSha256": hashlib.sha256(dirty_diff.encode("utf-8")).hexdigest(), "sourceHashes": source_hashes}


def _device_records(runtime_identifier: str) -> dict[str, dict[str, object]]:
    payload = json_command(["xcrun", "simctl", "list", "devices", "available", "-j"])
    if not isinstance(payload, dict) or not isinstance(payload.get("devices"), dict):
        raise RunnerError("simctl device format is unsupported")
    records: dict[str, dict[str, object]] = {}
    for runtime_name, devices in payload["devices"].items():
        if runtime_name != runtime_identifier or not isinstance(devices, list):
            continue
        for item in devices:
            if isinstance(item, dict) and item.get("name") in DEVICES and item.get("isAvailable") is True:
                name, identifier = item["name"], item.get("udid")
                if not isinstance(identifier, str) or not re.fullmatch(r"[A-F0-9]{8}-[A-F0-9]{4}-[A-F0-9]{4}-[A-F0-9]{4}-[A-F0-9]{12}", identifier, re.I):
                    raise RunnerError(f"required simulator has an invalid UDID: {name}")
                if name in records:
                    raise RunnerError(f"ambiguous required simulator: {name}")
                records[name] = {"udid": identifier, "runtimeIdentifier": runtime_name}
    if set(records) != set(DEVICES):
        raise RunnerError("required iPhone 17 simulators on iOS 26.4.1 are unavailable")
    return records


def required_runtime(payload: object) -> dict[str, object]:
    available = payload.get("runtimes") if isinstance(payload, dict) else None
    matches = [item for item in available or [] if isinstance(item, dict) and item.get("name") == "iOS 26.4"
               and item.get("version") == "26.4.1" and item.get("buildversion") == "23E254a" and item.get("isAvailable") is True]
    if len(matches) != 1 or matches[0].get("identifier") != "com.apple.CoreSimulator.SimRuntime.iOS-26-4":
        raise RunnerError("iOS 26.4.1 runtime is unavailable")
    return matches[0]


def preflight() -> dict[str, object]:
    if sys.platform != "darwin":
        raise RunnerError("preflight requires macOS")
    if Path(sys.executable).resolve() != Path(PYTHON_RUNTIME).resolve():
        raise RunnerError(f"use {PYTHON_RUNTIME}")
    xcode = checked(["xcodebuild", "-version"], timeout=30)
    xcode_lines = str(xcode.get("stdout", "")).splitlines()
    if xcode_lines[:2] != ["Xcode 26.4.1", "Build version 17E202"]:
        raise RunnerError("Xcode 26.4.1 is required")
    runtimes = json_command(["xcrun", "simctl", "list", "runtimes", "-j"])
    runtime = required_runtime(runtimes)
    devices = _device_records(runtime["identifier"])
    free = shutil.disk_usage(ROOT).free
    if free < MIN_FREE_BYTES:
        raise RunnerError("Mac free space is below the 20 GiB reserve")
    return {"python": sys.executable, "xcode": str(xcode["stdout"]).strip(), "runtime": runtime,
            "devices": devices, "freeBytes": free}


def generated_xctestrun(build_root: Path) -> Path:
    files = tuple(build_root.rglob("*.xctestrun"))
    if len(files) != 1:
        raise RunnerError("generic build did not produce exactly one xctestrun")
    return files[0]


def configure_xctestrun(template: Path, output: Path, environment: dict[str, str], target_name: str = "ACEClientAppUITests") -> None:
    try:
        with template.open("rb") as stream:
            payload = plistlib.load(stream)
    except (OSError, plistlib.InvalidFileException) as error:
        raise RunnerError("generated xctestrun is unreadable") from error
    metadata = payload.get("__xctestrun_metadata__") if isinstance(payload, dict) else None
    if not isinstance(metadata, dict) or metadata.get("FormatVersion") != 1:
        raise RunnerError("unsupported xctestrun format: expected format 1")
    target = payload.get(target_name)
    if not isinstance(target, dict) or "TestConfigurations" in payload or "TestConfigurations" in metadata:
        raise RunnerError(f"unsupported xctestrun layout: expected flat {target_name} target")
    target_environment = target.get("EnvironmentVariables", {})
    if not isinstance(target_environment, dict):
        raise RunnerError("unsupported xctestrun environment layout")
    target_environment.update(environment)
    target["EnvironmentVariables"] = target_environment
    def resolve_test_root(value: object) -> object:
        if isinstance(value, str):
            return value.replace("__TESTROOT__", str(template.parent))
        if isinstance(value, list):
            return [resolve_test_root(item) for item in value]
        if isinstance(value, dict):
            return {key: resolve_test_root(item) for key, item in value.items()}
        return value
    payload = resolve_test_root(payload)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("wb") as stream:
        plistlib.dump(payload, stream, sort_keys=True)


def build(candidate_record: dict[str, object], evidence: Path, scheme: str = SCHEME) -> dict[str, object]:
    build_root = evidence / "build"
    build_root.mkdir(parents=True, exist_ok=True)
    result_bundle = evidence / "build.xcresult"
    record = command([
        "xcodebuild", "build-for-testing", "-project", str(PROJECT), "-scheme", scheme,
        "-configuration", "Debug", "-sdk", "iphonesimulator", "-destination", "generic/platform=iOS Simulator",
        "-parallel-testing-enabled", "NO", "-derivedDataPath", str(build_root), "-resultBundlePath", str(result_bundle),
        "ACE_PREVIEW_ORIGIN=https://preview.example.invalid", "ACE_BUNDLE_IDENTIFIER=com.example.aceclientapp",
        "ARCHS=x86_64", "ONLY_ACTIVE_ARCH=YES", "CODE_SIGN_IDENTITY=", "CODE_SIGNING_REQUIRED=NO", "CODE_SIGNING_ALLOWED=NO",
    ], cwd=ROOT, timeout=1800)
    (evidence / "build-command.json").write_text(json.dumps(record, indent=2, sort_keys=True), encoding="utf-8")
    (evidence / "build.log").write_text(str(record.get("stdout", "")) + str(record.get("stderr", "")), encoding="utf-8")
    if record.get("exit") != 0:
        raise RunnerError("generic build-for-testing failed; retained build log is required evidence")
    template = generated_xctestrun(build_root)
    products = build_root / "Build" / "Products"
    if not result_bundle.is_dir() or not products.is_dir():
        raise RunnerError("generic build did not retain required products and result bundle")
    return {"identity": sha256(template), "template": str(template), "buildCommand": record["command"],
            "buildExit": record["exit"], "buildLog": str(evidence / "build.log"), "buildLogSha256": sha256(evidence / "build.log"),
            "buildResultBundle": str(result_bundle), "buildResultBundleSha256": directory_hash(result_bundle),
            "products": str(products), "productSha256": directory_hash(products), "candidate": candidate_record, "scheme": scheme}


def setting_commands(identifier: str, settings: Settings) -> tuple[list[str], ...]:
    contrast = "enabled" if settings.increaseContrast else "disabled"
    return (
        ["xcrun", "simctl", "ui", identifier, "appearance", settings.appearance],
        ["xcrun", "simctl", "ui", identifier, "content_size", settings.contentSize],
        ["xcrun", "simctl", "ui", identifier, "increase_contrast", contrast],
    )


def current_simctl_settings(identifier: str) -> dict[str, str]:
    values: dict[str, str] = {}
    for setting in ("appearance", "content_size", "increase_contrast"):
        result = checked(["xcrun", "simctl", "ui", identifier, setting], timeout=30)
        value = str(result.get("stdout", "")).strip().lower()
        if not value:
            raise RunnerError(f"simctl did not report {setting}")
        values[setting] = value
    return values


def simulator_state(identifier: str) -> str:
    payload = json_command(["xcrun", "simctl", "list", "devices", "-j"])
    devices = payload.get("devices") if isinstance(payload, dict) else None
    states = [item.get("state") for values in devices.values() if isinstance(values, list)
              for item in values if isinstance(item, dict) and item.get("udid") == identifier]
    if len(states) != 1 or states[0] not in {"Booted", "Shutdown"}:
        raise RunnerError("required simulator state is unavailable")
    return states[0]


def boot_required_simulator(identifier: str, initial_state: str) -> bool:
    if initial_state == "Booted":
        return False
    checked(["xcrun", "simctl", "boot", identifier], timeout=120)
    checked(["xcrun", "simctl", "bootstatus", identifier, "-b"], timeout=300)
    return True


def restore_boot_state(identifier: str, initial_state: str) -> None:
    if initial_state == "Shutdown":
        if simulator_state(identifier) != "Shutdown":
            checked(["xcrun", "simctl", "shutdown", identifier], timeout=120)


def restore_simctl_settings(identifier: str, previous: dict[str, str], evidence: Path, device: str, phase: str) -> list[str]:
    failures: list[str] = []
    records: list[dict[str, object]] = []
    for setting, value in previous.items():
        result = command(["xcrun", "simctl", "ui", identifier, setting, value], timeout=60)
        records.append(result)
        if result.get("exit") != 0:
            failures.append(setting)
    path = evidence / "restoration" / f"{device}-simctl-{phase}-commands.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(records, indent=2, sort_keys=True), encoding="utf-8")
    return failures


def restore_device_configuration(identifier: str, previous: dict[str, str] | None,
                                 previous_native_flags: dict[str, object] | None, template: Path,
                                 evidence: Path, device: str, phase: str) -> list[str]:
    failures: list[str] = []
    if previous is not None:
        failures.extend(f"{device}:{field}" for field in restore_simctl_settings(identifier, previous, evidence, device, phase))
        try:
            observed_simctl = current_simctl_settings(identifier)
            (evidence / "restoration" / f"{device}-simctl-{phase}-readback.json").write_text(
                json.dumps({"expected": previous, "observed": observed_simctl}, indent=2, sort_keys=True), encoding="utf-8")
            if observed_simctl != previous:
                failures.append(f"{device}:simctl-readback")
        except RunnerError:
            failures.append(f"{device}:simctl-readback")
    if previous_native_flags is not None:
        try:
            restored = native_flags(identifier, template, evidence, f"{device}-restore-{phase}", {"mode": "set", **previous_native_flags})
            if restored != previous_native_flags:
                failures.append(f"{device}:native-flags")
        except RunnerError:
            failures.append(f"{device}:native-restore")
    return failures


def marker_records(log: Path, marker: str) -> list[dict[str, object]]:
    if not log.is_file():
        raise RunnerError("native test log is missing")
    records: list[dict[str, object]] = []
    for line in log.read_text(encoding="utf-8", errors="replace").splitlines():
        if marker in line:
            try:
                value = json.loads(line.split(marker, 1)[1])
            except json.JSONDecodeError as error:
                raise RunnerError("native marker JSON is invalid") from error
            if not isinstance(value, dict):
                raise RunnerError("native marker is not an object")
            records.append(value)
    return records


def native_summary(bundle: Path, output: Path, expected_count: int) -> int:
    result = checked(["xcrun", "xcresulttool", "get", "test-results", "summary", "--path", str(bundle)], timeout=120)
    try:
        payload = json.loads(str(result["stdout"]))
    except json.JSONDecodeError as error:
        raise RunnerError("native result summary is invalid") from error
    required = ("totalTestCount", "passedTests", "failedTests", "skippedTests", "expectedFailures", "result")
    if not isinstance(payload, dict) or any(key not in payload for key in required):
        raise RunnerError("native result summary has an unsupported schema")
    output.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    if (any(type(payload[field]) is not int for field in required[:-1]) or payload["result"] != "Passed"
            or payload["expectedFailures"] != 0 or payload["failedTests"] != 0 or payload["skippedTests"] != 0
            or payload["totalTestCount"] != expected_count or payload["passedTests"] != expected_count):
        raise RunnerError("native result summary is not a complete pass")
    return expected_count


def _export_attachments(bundle: Path, output: Path) -> None:
    output.mkdir(parents=True, exist_ok=True)
    checked(["xcrun", "xcresulttool", "export", "attachments", "--path", str(bundle), "--output-path", str(output)], timeout=300)
    if not any(path.is_file() for path in output.rglob("*")):
        raise RunnerError("native result has no exported attachments")


def attachment_name_map(attachments: Path) -> dict[str, str]:
    manifest = attachments / "manifest.json"
    try:
        payload = json.loads(manifest.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise RunnerError("native attachment manifest is unavailable") from error
    if not isinstance(payload, list):
        raise RunnerError("native attachment manifest has an invalid schema")
    result: dict[str, str] = {}
    exports: set[str] = set()
    for entry in payload:
        values = entry.get("attachments") if isinstance(entry, dict) else None
        if not isinstance(values, list):
            raise RunnerError("native attachment manifest has invalid attachments")
        for attachment in values:
            if not isinstance(attachment, dict):
                raise RunnerError("native attachment manifest item is invalid")
            human, exported = attachment.get("suggestedHumanReadableName"), attachment.get("exportedFileName")
            if (not isinstance(human, str) or not isinstance(exported, str)
                    or not re.fullmatch(r"[A-F0-9]{8}-[A-F0-9]{4}-[A-F0-9]{4}-[A-F0-9]{4}-[A-F0-9]{12}(?:\.[A-Za-z0-9]{1,10})?", exported, re.I)
                    or human in result or exported in exports or not (attachments / exported).is_file()):
                raise RunnerError("native attachment manifest does not retain its exported file")
            result[human] = exported
            exports.add(exported)
    return result


def verify_screenshot_attachments(records: Iterable[dict[str, object]], attachments: Path) -> None:
    names = attachment_name_map(attachments)
    for record in records:
        screenshots = record.get("screenshots")
        if not isinstance(screenshots, list):
            raise RunnerError("native screenshot marker is invalid")
        for screenshot in screenshots:
            if not isinstance(screenshot, str) or not any(name == screenshot or name.startswith(screenshot + "_") for name in names):
                raise RunnerError("native screenshot marker has no exported attachment")


def screenshot_exports(screenshots: object, attachments: Path) -> tuple[str, ...]:
    """Resolve each marker name to one retained attachment file."""
    if not isinstance(screenshots, list) or not all(isinstance(name, str) for name in screenshots):
        raise RunnerError("native screenshot marker is invalid")
    names = attachment_name_map(attachments)
    exports: list[str] = []
    for screenshot in screenshots:
        matches = [exported for human, exported in names.items() if human == screenshot or human.startswith(screenshot + "_")]
        if len(matches) != 1:
            raise RunnerError("native screenshot marker does not map to one attachment")
        exports.append(matches[0])
    return tuple(exports)


def verify_case_markers(cases: tuple[Case, ...], records: list[dict[str, object]]) -> None:
    expected = {case.id: case for case in cases}
    actual = {record.get("id"): record for record in records}
    if set(actual) != set(expected) or len(actual) != len(records):
        raise RunnerError("native case markers do not match batch cases")
    for case_id, case in expected.items():
        record = actual[case_id]
        if record.get("scenario") != case.scenario or record.get("observed") != case.settings.payload():
            raise RunnerError(f"native settings differ for {case_id}")
        expected_audits = expected_audit_invocations(case)
        if record.get("result") != "passed" or record.get("auditInvocations") != expected_audits:
            raise RunnerError(f"native audit record is incomplete for {case_id}")
        if not isinstance(record.get("screenshots"), list) or not record["screenshots"]:
            raise RunnerError(f"native evidence is incomplete for {case_id}")


def expected_audit_invocations(case: Case) -> int:
    """Keep required viewports separate from the 512 audited case count."""
    if not case.audit:
        return 0
    return {"release": 2, "noConclusion": 2, "noActions": 2, "copyConfirmation": 2}.get(case.scenario, 1)


def native_flags(identifier: str, template: Path, evidence: Path, label: str, request: dict[str, object]) -> dict[str, object]:
    """Read or set native accessibility flags in a separate XCTest process."""
    root = evidence / "native-settings" / label
    runfile = root / "ACEClientAppUITests.xctestrun"
    configure_xctestrun(template, runfile, {"ACE_ACCESSIBILITY_SETTINGS_JSON": json.dumps(request, separators=(",", ":"))})
    bundle = root / "result.xcresult"
    root.mkdir(parents=True, exist_ok=True)
    process = command(["xcodebuild", "test-without-building", "-xctestrun", str(runfile), "-destination", f"id={identifier}",
                       "-parallel-testing-enabled", "NO", "-only-testing:" + SETTINGS_SELECTOR, "-resultBundlePath", str(bundle)], cwd=IOS_ROOT, timeout=1800)
    log = root / "native.log"
    log.write_text(str(process.get("stdout", "")) + str(process.get("stderr", "")), encoding="utf-8")
    (root / "command.json").write_text(json.dumps(process, indent=2, sort_keys=True), encoding="utf-8")
    failures: list[str] = []
    if not bundle.is_dir():
        failures.append("result bundle missing")
    else:
        try:
            native_summary(bundle, root / "summary.json", 1)
        except RunnerError as error:
            failures.append(str(error))
        try:
            _export_attachments(bundle, root / "attachments")
        except RunnerError as error:
            failures.append("attachment export: " + str(error))
    if process.get("exit") != 0:
        failures.append("native settings process failed")
    if failures:
        (root / "failure.json").write_text(json.dumps({"request": request, "command": process, "failures": failures}, indent=2, sort_keys=True), encoding="utf-8")
        raise RunnerError("native settings selector failed after evidence collection: " + "; ".join(failures))
    records = marker_records(log, SETTINGS_MARKER)
    if len(records) != 1 or records[0].get("mode") != request.get("mode"):
        raise RunnerError("native settings marker is missing")
    observed = records[0].get("observed")
    fields = ("boldText", "reduceMotion", "increaseContrast", "orientation")
    if (not isinstance(observed, dict) or set(observed) != set(fields)
            or any(type(observed[key]) is not bool for key in fields[:3])
            or observed.get("orientation") not in {"portrait", "landscape"}):
        raise RunnerError("native settings marker has invalid observed values")
    if request.get("mode") == "set" and any(observed[key] != request[key] for key in fields):
        raise RunnerError("native settings selector did not apply requested flags")
    return {key: observed[key] for key in fields}


def run_batch(device: str, identifier: str, settings: Settings, cases: tuple[Case, ...], build_record: dict[str, object], evidence: Path, index: int) -> dict[str, object]:
    for setting in setting_commands(identifier, settings):
        checked(setting, timeout=60)
    payload = json.dumps([case.payload() for case in cases], separators=(",", ":"))
    batch_root = evidence / "batches" / f"{index:03d}"
    runfile = batch_root / "ACEClientAppUITests.xctestrun"
    configure_xctestrun(Path(str(build_record["template"])), runfile, {
        "ACE_COVERAGE_CASES_JSON": payload,
    })
    result_bundle = batch_root / "result.xcresult"
    log = batch_root / "native.log"
    batch_root.mkdir(parents=True, exist_ok=True)
    process = command([
        "xcodebuild", "test-without-building", "-xctestrun", str(runfile), "-destination", f"id={identifier}",
        "-parallel-testing-enabled", "NO", "-only-testing:" + COVERAGE_SELECTOR,
        "-resultBundlePath", str(result_bundle),
    ], cwd=IOS_ROOT, timeout=1800)
    log.write_text(str(process.get("stdout", "")) + str(process.get("stderr", "")), encoding="utf-8")
    (batch_root / "native-command.json").write_text(json.dumps(process, indent=2, sort_keys=True), encoding="utf-8")
    summary = batch_root / "native-summary.json"
    attachments = batch_root / "attachments"
    failures: list[str] = []
    count = 0
    if not result_bundle.is_dir():
        failures.append("result bundle missing")
    else:
        try:
            count = native_summary(result_bundle, summary, 1)
        except RunnerError as error:
            failures.append(str(error))
        try:
            _export_attachments(result_bundle, attachments)
        except RunnerError as error:
            failures.append(str(error))
    if process.get("exit") != 0:
        failures.append("native process failed")
    if failures:
        raise RunnerError(f"native batch {index} failed after evidence collection: {'; '.join(failures)}")
    records = marker_records(log, CASE_MARKER)
    verify_case_markers(cases, records)
    verify_screenshot_attachments(records, attachments)
    return {"device": device, "settings": settings.payload(), "caseCount": len(cases), "auditCount": sum(case.audit for case in cases),
            "nativeTestCount": count, "runfileSha256": sha256(runfile), "resultBundle": str(result_bundle),
            "resultBundleSha256": directory_hash(result_bundle), "attachmentDirectory": str(attachments),
            "attachmentSha256": directory_hash(attachments), "summarySha256": sha256(summary),
            "logSha256": sha256(log), "command": process["command"], "exit": process["exit"], "caseRecords": records}


def directory_hash(path: Path) -> str:
    digest = hashlib.sha256()
    for item in sorted(path.rglob("*")):
        if item.is_file():
            digest.update(str(item.relative_to(path)).encode("utf-8"))
            digest.update(sha256(item).encode("ascii"))
    return digest.hexdigest()


def directory_bytes(path: Path) -> int:
    return sum(item.stat().st_size for item in path.rglob("*") if item.is_file() and not item.is_symlink())


def reuse_build(candidate_record: dict[str, object], pilot: dict[str, object]) -> dict[str, object]:
    build_record = pilot.get("build")
    if not isinstance(build_record, dict) or pilot.get("candidate") != candidate_record:
        raise RunnerError("pilot candidate does not exactly match the full candidate")
    if build_record.get("candidate") != candidate_record or build_record.get("scheme") != SCHEME:
        raise RunnerError("retained pilot build does not bind the UI candidate and scheme")
    template = Path(str(build_record.get("template", "")))
    identity = build_record.get("identity")
    bundle = Path(str(build_record.get("buildResultBundle", "")))
    log = Path(str(build_record.get("buildLog", "")))
    products = Path(str(build_record.get("products", "")))
    if (not template.is_file() or not isinstance(identity, str) or sha256(template) != identity
            or not bundle.is_dir() or build_record.get("buildResultBundleSha256") != directory_hash(bundle)
            or not products.is_dir() or build_record.get("productSha256") != directory_hash(products)
            or not log.is_file() or build_record.get("buildLogSha256") != sha256(log)):
        raise RunnerError("retained pilot build identity is unavailable")
    return build_record


def environment_identity(environment: object) -> dict[str, object]:
    if not isinstance(environment, dict):
        raise RunnerError("recorded environment identity is invalid")
    identity = {key: environment.get(key) for key in ("python", "xcode", "runtime", "devices")}
    runtime = identity["runtime"]
    if isinstance(runtime, dict):
        identity["runtime"] = {key: value for key, value in runtime.items() if key != "lastUsage"}
    return identity


def canonical_case(device: str, scenario: str, settings: dict[str, object]) -> tuple[str, str, str]:
    return device, scenario, json.dumps(settings, sort_keys=True, separators=(",", ":"))


def eligible_pilot_cases(pilot: dict[str, object]) -> set[tuple[str, str, str]]:
    eligible: set[tuple[str, str, str]] = set()
    batches = pilot.get("batches")
    if not isinstance(batches, list):
        raise RunnerError("pilot batches are unavailable for reuse")
    for batch in batches:
        if not isinstance(batch, dict) or not isinstance(batch.get("device"), str) or not isinstance(batch.get("caseRecords"), list):
            raise RunnerError("pilot case evidence is invalid for reuse")
        for record in batch["caseRecords"]:
            if not isinstance(record, dict) or record.get("result") != "passed" or not isinstance(record.get("scenario"), str) or not isinstance(record.get("observed"), dict):
                raise RunnerError("pilot case did not pass for reuse")
            eligible.add(canonical_case(batch["device"], record["scenario"], record["observed"]))
    return eligible


def pilot_capture_measurements(pilot: dict[str, object]) -> tuple[dict[tuple[str, str, str], tuple[str, ...]], int]:
    """Measure retained images per pilot case and raw evidence per pilot batch."""
    batches = pilot.get("batches")
    if not isinstance(batches, list):
        raise RunnerError("pilot batches are unavailable for measurement")
    captures: dict[tuple[str, str, str], tuple[str, ...]] = {}
    batch_bytes: list[int] = []
    for batch in batches:
        if not isinstance(batch, dict) or not isinstance(batch.get("device"), str) or not isinstance(batch.get("caseRecords"), list):
            raise RunnerError("pilot batch has invalid capture records")
        attachments = Path(str(batch.get("attachmentDirectory", "")))
        result_bundle = Path(str(batch.get("resultBundle", "")))
        if not attachments.is_dir() or not result_bundle.is_dir():
            raise RunnerError("pilot capture artifacts are unavailable")
        batch_bytes.append(directory_bytes(result_bundle.parent))
        for record in batch["caseRecords"]:
            if not isinstance(record, dict) or not isinstance(record.get("scenario"), str) or not isinstance(record.get("observed"), dict):
                raise RunnerError("pilot case capture record is invalid")
            key = canonical_case(batch["device"], record["scenario"], record["observed"])
            if key in captures:
                raise RunnerError("pilot case capture is duplicated")
            captures[key] = tuple(sha256(attachments / exported) for exported in screenshot_exports(record.get("screenshots"), attachments))
    if not captures or not batch_bytes:
        raise RunnerError("pilot capture measurements are empty")
    return captures, max(batch_bytes)


def pilot_image_measurements(pilot: dict[str, object], captures: dict[tuple[str, str, str], tuple[str, ...]]) -> tuple[set[str], int, int]:
    """Measure all retained native images and unmapped images per pilot batch."""
    batches = pilot.get("batches")
    if not isinstance(batches, list):
        raise RunnerError("pilot batches are unavailable for image measurement")
    hashes: set[str] = set()
    max_case_images = 0
    max_unmapped_batch_images = 0
    for batch in batches:
        if not isinstance(batch, dict) or not isinstance(batch.get("device"), str) or not isinstance(batch.get("caseRecords"), list):
            raise RunnerError("pilot batch has invalid image records")
        attachments = Path(str(batch.get("attachmentDirectory", "")))
        if not attachments.is_dir():
            raise RunnerError("pilot image artifacts are unavailable")
        retained = {path.resolve() for path in attachments.rglob("*")
                    if path.is_file() and path.suffix.lower() in {".png", ".jpg", ".jpeg"}}
        mapped: set[Path] = set()
        for record in batch["caseRecords"]:
            if not isinstance(record, dict) or not isinstance(record.get("scenario"), str) or not isinstance(record.get("observed"), dict):
                raise RunnerError("pilot case image record is invalid")
            key = canonical_case(batch["device"], record["scenario"], record["observed"])
            if key not in captures:
                raise RunnerError("pilot case image capture is unavailable")
            exports = screenshot_exports(record.get("screenshots"), attachments)
            paths = {attachments.joinpath(exported).resolve() for exported in exports}
            if not paths.issubset(retained):
                raise RunnerError("pilot case screenshot is not a retained image")
            mapped.update(paths)
            max_case_images = max(max_case_images, len(paths))
        hashes.update(sha256(path) for path in retained)
        max_unmapped_batch_images = max(max_unmapped_batch_images, len(retained - mapped))
    if not hashes or max_case_images <= 0:
        raise RunnerError("pilot image measurements are empty")
    return hashes, max_case_images, max_unmapped_batch_images


def validate_review_projection(resources: dict[str, object], ledger: dict[str, object], candidate_record: dict[str, object],
                               pilot_manifest_hash: str, unique_hashes: set[str], remaining_images: int) -> None:
    """Bind a review projection to unique, case-linked pilot images."""
    measurement = ledger.get("reviewMeasurement")
    inspected = measurement.get("inspectedImageSha256") if isinstance(measurement, dict) else None
    if (not isinstance(measurement, dict) or type(measurement.get("elapsedSeconds")) is not int
            or measurement["elapsedSeconds"] <= 0 or not isinstance(inspected, list)
            or not all(isinstance(value, str) for value in inspected) or len(inspected) != len(set(inspected))
            or set(inspected) != unique_hashes or not unique_hashes):
        raise RunnerError("pilot image review measurement is incomplete")
    measured_per_image = (measurement["elapsedSeconds"] + len(unique_hashes) - 1) // len(unique_hashes)
    projected = remaining_images * measured_per_image
    if (type(resources.get("perImageReviewSeconds")) is not int or resources["perImageReviewSeconds"] != measured_per_image
            or type(resources.get("projectedImageInspectionSeconds")) is not int
            or resources["projectedImageInspectionSeconds"] != projected):
        raise RunnerError("pilot image projection is not measured")
    if projected <= 8 * 60 * 60:
        return
    arrangement = ledger.get("reviewArrangement")
    if (not isinstance(arrangement, dict) or arrangement.get("candidate") != candidate_record
            or arrangement.get("pilotManifestSha256") != pilot_manifest_hash
            or not isinstance(arrangement.get("method"), str) or not arrangement["method"].strip()
            or arrangement.get("uniquePilotImageSha256") != sorted(unique_hashes)
            or arrangement.get("measuredPilotReviewSeconds") != measurement["elapsedSeconds"]
            or type(arrangement.get("elapsedSeconds")) is not int or arrangement["elapsedSeconds"] <= 0
            or not isinstance(arrangement.get("inspectedImageSha256"), list)
            or arrangement["inspectedImageSha256"] != sorted(unique_hashes)
            or type(arrangement.get("perImageSeconds")) is not int or arrangement["perImageSeconds"] <= 0
            or arrangement["perImageSeconds"] != (arrangement["elapsedSeconds"] + len(unique_hashes) - 1) // len(unique_hashes)
            or type(arrangement.get("projectedActiveSeconds")) is not int
            or arrangement["projectedActiveSeconds"] != remaining_images * arrangement["perImageSeconds"]
            or arrangement["projectedActiveSeconds"] > 8 * 60 * 60):
        raise RunnerError("image review arrangement is not measured and affordable")
    evidence = arrangement.get("evidence")
    if not isinstance(evidence, list) or not evidence:
        raise RunnerError("image review arrangement evidence is unavailable")
    for item in evidence:
        if not isinstance(item, dict) or not isinstance(item.get("path"), str) or not isinstance(item.get("sha256"), str):
            raise RunnerError("image review arrangement evidence is invalid")
        path = Path(item["path"])
        if not path.is_file() or path.is_symlink() or sha256(path) != item["sha256"]:
            raise RunnerError("image review arrangement evidence hash does not verify")


def run_coverage(cases: tuple[Case, ...], evidence: Path, retained_pilot: dict[str, object] | None = None,
                 frozen_candidate: dict[str, object] | None = None) -> dict[str, object]:
    environment = preflight()
    candidate_record = candidate() if frozen_candidate is None else frozen_candidate
    if candidate() != candidate_record:
        raise RunnerError("candidate identity changed before coverage")
    if retained_pilot is not None and environment_identity(retained_pilot.get("environment", {})) != environment_identity(environment):
        raise RunnerError("pilot environment identity differs from the full environment")
    build_record = reuse_build(candidate_record, retained_pilot) if retained_pilot is not None else build(candidate_record, evidence)
    devices = environment["devices"]
    assert isinstance(devices, dict)
    reused = set() if retained_pilot is None else eligible_pilot_cases(retained_pilot)
    execution_cases = tuple(case for case in cases if canonical_case(case.device, case.scenario, case.settings.payload()) not in reused)
    unordered_batch_plan = coverage_batches(execution_cases)
    batch_plan = tuple(batch for device in DEVICES for batch in unordered_batch_plan if batch[0] == device)
    final_batch_index = {device: index for index, (device, _settings, _cases) in enumerate(batch_plan, 1)}
    previous: dict[str, dict[str, str]] = {}
    previous_native_flags: dict[str, dict[str, object]] = {}
    initial_boot_states: dict[str, str] = {}
    prepared_devices: set[str] = set()
    batch_restored_devices: set[str] = set()
    post_boot_restored_devices: set[str] = set()
    failed_restoration_devices: set[str] = set()
    restoration_failures: list[str] = []
    records: list[dict[str, object]] = []
    primary_error: RunnerError | None = None
    try:
        for device in DEVICES:
            if device not in devices:
                continue
            data = devices[device]
            assert isinstance(data, dict)
            initial_boot_states[device] = simulator_state(str(data["udid"]))
        for device in DEVICES:
            if device not in devices or initial_boot_states[device] != "Booted":
                continue
            data = devices[device]
            assert isinstance(data, dict)
            identifier = str(data["udid"])
            previous[device] = current_simctl_settings(identifier)
            previous_native_flags[device] = native_flags(identifier, Path(str(build_record["template"])), evidence, f"{device}-read", {"mode": "read"})
            checked(["xcrun", "simctl", "shutdown", identifier], timeout=120)
        for index, (device, settings, batch_cases) in enumerate(batch_plan, 1):
            if candidate() != candidate_record:
                raise RunnerError("candidate identity changed before native batch")
            data = devices[device]
            assert isinstance(data, dict)
            identifier = str(data["udid"])
            if device not in prepared_devices:
                boot_required_simulator(identifier, simulator_state(identifier))
                if device not in previous:
                    previous[device] = current_simctl_settings(identifier)
                    previous_native_flags[device] = native_flags(identifier, Path(str(build_record["template"])), evidence, f"{device}-read", {"mode": "read"})
                prepared_devices.add(device)
            native_flags(identifier, Path(str(build_record["template"])), evidence, f"{index:03d}-set", {
                "mode": "set", "boldText": settings.boldText, "reduceMotion": settings.reduceMotion,
                "increaseContrast": settings.increaseContrast, "orientation": settings.orientation,
            })
            records.append(run_batch(device, identifier, settings, batch_cases, build_record, evidence, index))
            (evidence / "batches" / f"{index:03d}" / "checkpoint.json").write_text(
                json.dumps({"status": "passed", "record": records[-1]}, indent=2, sort_keys=True), encoding="utf-8")
            if candidate() != candidate_record:
                raise RunnerError("candidate identity changed after native batch")
            if index == final_batch_index[device]:
                device_restore_failures = restore_device_configuration(
                    identifier, previous[device], previous_native_flags[device], Path(str(build_record["template"])), evidence, device, "batch"
                )
                batch_restored_devices.add(device)
                restoration_failures.extend(device_restore_failures)
                if device_restore_failures:
                    failed_restoration_devices.add(device)
                    raise RunnerError("simulator setting restoration failed: " + ", ".join(restoration_failures))
                if index == len(batch_plan):
                    post_boot_restored_devices.add(device)
                if initial_boot_states[device] == "Shutdown" or index != len(batch_plan):
                    checked(["xcrun", "simctl", "shutdown", identifier], timeout=120)
    except RunnerError as error:
        primary_error = error
        (evidence / "coverage-checkpoint.json").write_text(json.dumps({"status": "failed", "candidate": candidate_record,
            "completedBatches": records, "error": str(error)}, indent=2, sort_keys=True), encoding="utf-8")
    finally:
        for device in initial_boot_states:
            data = devices[device]
            assert isinstance(data, dict)
            identifier = str(data["udid"])
            if initial_boot_states[device] == "Shutdown":
                if device in prepared_devices and device not in batch_restored_devices and device not in failed_restoration_devices:
                    device_restore_failures = restore_device_configuration(
                        identifier, previous.get(device), previous_native_flags.get(device), Path(str(build_record["template"])), evidence, device, "failure"
                    )
                    batch_restored_devices.add(device)
                    restoration_failures.extend(device_restore_failures)
                    if device_restore_failures:
                        failed_restoration_devices.add(device)
                try:
                    restore_boot_state(identifier, initial_boot_states[device])
                except RunnerError:
                    restoration_failures.append(f"{device}:boot-state")
            else:
                try:
                    boot_required_simulator(identifier, simulator_state(identifier))
                except RunnerError:
                    restoration_failures.append(f"{device}:boot-state")
                    continue
                if device not in post_boot_restored_devices and device in previous and device not in failed_restoration_devices:
                    device_restore_failures = restore_device_configuration(
                        identifier, previous[device], previous_native_flags.get(device), Path(str(build_record["template"])), evidence, device, "post-boot"
                    )
                    post_boot_restored_devices.add(device)
                    restoration_failures.extend(device_restore_failures)
                    if device_restore_failures:
                        failed_restoration_devices.add(device)
    if primary_error is not None:
        suffix = "" if not restoration_failures else "; restoration failures: " + ", ".join(restoration_failures)
        (evidence / "coverage-final-failure.json").write_text(json.dumps({"candidate": candidate_record,
            "primaryError": str(primary_error), "restorationFailures": restoration_failures, "completedBatches": records},
            indent=2, sort_keys=True), encoding="utf-8")
        raise RunnerError(str(primary_error) + suffix)
    if restoration_failures:
        (evidence / "coverage-final-failure.json").write_text(json.dumps({"candidate": candidate_record,
            "primaryError": None, "restorationFailures": restoration_failures, "completedBatches": records},
            indent=2, sort_keys=True), encoding="utf-8")
        raise RunnerError("simulator setting restoration failed: " + ", ".join(restoration_failures))
    if candidate() != candidate_record:
        raise RunnerError("candidate identity changed before final report")
    result = {"candidate": candidate_record, "environment": environment, "build": build_record, "batches": records,
              "caseCount": len(cases), "auditCount": sum(case.audit for case in cases), "layoutCount": sum(not case.audit for case in cases),
              "executedCaseCount": len(execution_cases), "reusedPilotCaseCount": len(cases) - len(execution_cases),
              "auditInvocationCount": sum(int(case_record["auditInvocations"]) for record in records for case_record in record["caseRecords"]),
              "nativeTestCount": sum(int(record["nativeTestCount"]) for record in records)}
    return result


def validate_pilot_result(result: dict[str, object]) -> None:
    if result.get("caseCount") != 22 or result.get("auditCount") != 20 or result.get("layoutCount") != 2:
        raise RunnerError("pilot counts are incomplete")
    batches = result.get("batches")
    if not isinstance(batches, list):
        raise RunnerError("pilot native records are unavailable")
    expected = {canonical_case(case.device, case.scenario, case.settings.payload()): case for case in pilot_cases()}
    actual: dict[tuple[str, str, str], dict[str, object]] = {}
    for batch in batches:
        if not isinstance(batch, dict) or not isinstance(batch.get("device"), str) or not isinstance(batch.get("caseRecords"), list):
            raise RunnerError("pilot native batch record is invalid")
        for record in batch["caseRecords"]:
            if not isinstance(record, dict) or not isinstance(record.get("scenario"), str) or not isinstance(record.get("observed"), dict):
                raise RunnerError("pilot case marker is invalid")
            key = canonical_case(batch["device"], record["scenario"], record["observed"])
            if key in actual:
                raise RunnerError("pilot case marker is duplicated")
            actual[key] = record
    if set(actual) != set(expected):
        raise RunnerError("pilot case markers do not reconstruct the approved 22 cases")
    for key, case in expected.items():
        record = actual[key]
        if record.get("result") != "passed" or record.get("auditInvocations") != expected_audit_invocations(case):
            raise RunnerError("pilot native audit marker is incomplete")


READINESS_ROLES = ("pocock", "functional", "evidence-gate", "private-input")


def pilot_readiness(candidate_record: dict[str, object], records: dict[str, Path]) -> dict[str, dict[str, str]]:
    """Bind the required external readiness evidence to this exact candidate."""
    if set(records) != set(READINESS_ROLES):
        raise RunnerError("pilot readiness roles are incomplete")
    resolved = [path.expanduser().resolve() for path in records.values()]
    if len(set(resolved)) != len(resolved):
        raise RunnerError("pilot readiness roles must use distinct records")
    hashes: dict[str, dict[str, str]] = {}
    for role, path in records.items():
        item = path.expanduser().resolve()
        if not item.is_file() or item.is_symlink() or item.stat().st_size == 0:
            raise RunnerError("candidate-bound pilot readiness evidence is unavailable")
        payload = _load_object(item, "pilot readiness evidence")
        evidence = payload.get("evidence")
        if payload.get("role") != role or payload.get("candidate") != candidate_record or payload.get("status") != "passed" or not isinstance(evidence, list) or not evidence:
            raise RunnerError("pilot readiness evidence is not bound to this candidate")
        for artifact in evidence:
            if not isinstance(artifact, dict) or not isinstance(artifact.get("path"), str) or not isinstance(artifact.get("sha256"), str):
                raise RunnerError("pilot readiness evidence has an invalid artifact")
            evidence_path = Path(artifact["path"])
            if not evidence_path.is_file() or evidence_path.is_symlink() or sha256(evidence_path) != artifact["sha256"]:
                raise RunnerError("pilot readiness artifact hash does not verify")
        hashes[role] = {"path": str(item), "sha256": sha256(item)}
    return hashes


def _load_object(path: Path, description: str) -> dict[str, object]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise RunnerError(f"{description} is unreadable") from error
    if not isinstance(value, dict):
        raise RunnerError(f"{description} is not an object")
    return value


def validate_full_gate(pilot_manifest: Path, review_ledger: Path, candidate_record: dict[str, object]) -> dict[str, object]:
    """Require retained pilot evidence and explicit human resource/image approval."""
    pilot = _load_object(pilot_manifest, "pilot manifest")
    if pilot.get("mode") != "pilot" or pilot.get("candidate") != candidate_record:
        raise RunnerError("pilot manifest candidate differs from the full candidate")
    readiness = pilot.get("readinessEvidence")
    if not isinstance(readiness, dict):
        raise RunnerError("pilot readiness evidence is incomplete")
    try:
        reread = pilot_readiness(candidate_record, {role: Path(str(value["path"])) for role, value in readiness.items()
                                                     if isinstance(value, dict) and isinstance(value.get("path"), str)})
    except (KeyError, RunnerError) as error:
        raise RunnerError("pilot readiness evidence does not reverify") from error
    if reread != readiness:
        raise RunnerError("pilot readiness evidence hashes changed")
    validate_pilot_result(pilot)
    batches = pilot.get("batches")
    if not isinstance(batches, list) or any(not isinstance(batch, dict) or batch.get("exit") != 0 for batch in batches):
        raise RunnerError("pilot native batch evidence is incomplete")
    for batch in batches:
        bundle = Path(str(batch.get("resultBundle", "")))
        attachments = Path(str(batch.get("attachmentDirectory", "")))
        summary = bundle.parent / "native-summary.json"
        log = bundle.parent / "native.log"
        if (not bundle.is_dir() or not attachments.is_dir() or not summary.is_file() or not log.is_file()
                or batch.get("resultBundleSha256") != directory_hash(bundle)
                or batch.get("attachmentSha256") != directory_hash(attachments)
                or batch.get("summarySha256") != sha256(summary) or batch.get("logSha256") != sha256(log)):
            raise RunnerError("pilot native artifact hashes do not verify")
        records = batch.get("caseRecords")
        if not isinstance(records, list):
            raise RunnerError("pilot case records are missing")
        verify_screenshot_attachments(records, attachments)
    ledger = _load_object(review_ledger, "review ledger")
    if ledger.get("status") != "passed" or ledger.get("candidate") != candidate_record:
        raise RunnerError("review record is not bound to this candidate")
    if ledger.get("pilotManifestSha256") != sha256(pilot_manifest):
        raise RunnerError("review ledger does not bind the retained pilot manifest")
    resources = ledger.get("resourceGate")
    if not isinstance(resources, dict):
        raise RunnerError("pilot resource projection is unavailable")
    if type(resources.get("remainingRawEvidenceBytes")) is not int or type(resources.get("requiredFreeBytes")) is not int:
        raise RunnerError("pilot resource projection is incomplete")
    captures, max_raw_batch = pilot_capture_measurements(pilot)
    reused = eligible_pilot_cases(pilot)
    if set(captures) != reused:
        raise RunnerError("pilot capture records do not match reusable pilot cases")
    remaining_cases = tuple(case for case in coverage_cases()
                            if canonical_case(case.device, case.scenario, case.settings.payload()) not in reused)
    remaining_batches = coverage_batches(remaining_cases)
    if len(remaining_cases) != 836 - len(reused):
        raise RunnerError("pilot case reuse does not reconstruct the approved matrix")
    expected_images, max_case_images, max_unmapped_batch_images = pilot_image_measurements(pilot, captures)
    remaining_images = len(remaining_cases) * max_case_images + len(remaining_batches) * max_unmapped_batch_images
    # A pilot batch is an observed upper bound for one remaining case. It is
    # deliberately not represented as a measured per-case result.
    projected = len(remaining_cases) * max_raw_batch
    if (resources.get("pilotMaxRawBatchBytes") != max_raw_batch
            or resources.get("rawPerRemainingCaseUpperBoundBytes") != max_raw_batch
            or resources.get("pilotMaxCaseImageCount") != max_case_images
            or resources.get("pilotMaxUnmappedBatchImageCount") != max_unmapped_batch_images):
        raise RunnerError("pilot resource record does not match retained evidence maxima")
    if resources.get("remainingImageCount") != remaining_images:
        raise RunnerError("pilot image projection does not match retained evidence maxima")
    scratch = resources.get("scratchBytes")
    if type(scratch) is not int:
        raise RunnerError("pilot scratch projection is incomplete")
    build_products = Path(str(pilot.get("build", {}).get("products", ""))) if isinstance(pilot.get("build"), dict) else Path()
    minimum_scratch = directory_bytes(build_products) if build_products.is_dir() else 0
    if scratch < minimum_scratch:
        raise RunnerError("pilot scratch projection is below retained build products")
    minimum_required = (2 * projected) + scratch + MIN_FREE_BYTES
    if resources["remainingRawEvidenceBytes"] != projected or scratch < 0 or resources["requiredFreeBytes"] < minimum_required:
        raise RunnerError("pilot resource projection is invalid")
    if shutil.disk_usage(ROOT).free < resources["requiredFreeBytes"]:
        raise RunnerError("Mac free space no longer meets the approved full-run projection")
    validate_review_projection(resources, ledger, candidate_record, sha256(pilot_manifest), expected_images, remaining_images)
    for role in ("retrievalEvidence", "retentionEvidence"):
        proof = ledger.get(role)
        if not isinstance(proof, dict) or not isinstance(proof.get("path"), str) or not isinstance(proof.get("sha256"), str):
            raise RunnerError("pilot retrieval and retention evidence is incomplete")
        proof_path = Path(proof["path"])
        if not proof_path.is_file() or proof_path.is_symlink() or sha256(proof_path) != proof["sha256"]:
            raise RunnerError("pilot retrieval and retention evidence hash does not verify")
    reviewed = ledger.get("reviewedImageSha256")
    if (not isinstance(reviewed, list) or not all(isinstance(value, str) for value in reviewed)
            or len(reviewed) != len(set(reviewed)) or set(reviewed) != expected_images or not expected_images):
        raise RunnerError("review ledger does not cover every retained pilot image")
    return pilot


def write_manifest(evidence: Path, result: dict[str, object], mode: str) -> Path:
    evidence.mkdir(parents=True, exist_ok=True)
    manifest = evidence / "manifest.json"
    payload = {"mode": mode, "created": time.time(), **result}
    manifest.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    return manifest


def parse_enumeration(path: Path) -> set[str]:
    payload = _load_object(path, "native test enumeration")
    if payload.get("errors") != [] or not isinstance(payload.get("values"), list):
        raise RunnerError("native test enumeration reported errors")
    selectors: set[str] = set()
    for value in payload["values"]:
        if not isinstance(value, dict) or value.get("disabledTests") != [] or not isinstance(value.get("enabledTests"), list):
            raise RunnerError("native test enumeration has disabled or invalid tests")
        for test in value["enabledTests"]:
            identifier = test.get("identifier") if isinstance(test, dict) else None
            if not isinstance(identifier, str) or not identifier.endswith("()"):
                raise RunnerError("native test enumeration identifier is invalid")
            selectors.add(identifier[:-2])
    if not selectors:
        raise RunnerError("native test enumeration is empty")
    return selectors


def selected_test_environment(path: Path | None, target: str) -> tuple[dict[str, str], dict[str, object] | None]:
    if path is None:
        return {}, None
    if target != "ACEClientAppUITests":
        raise RunnerError("--test-env-json is available only for UI selectors")
    resolved = path.expanduser().resolve()
    if not resolved.is_file() or resolved.is_symlink():
        raise RunnerError("selected test environment file is unavailable")
    try:
        payload = json.loads(resolved.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise RunnerError("selected test environment JSON is invalid") from error
    if not isinstance(payload, dict) or set(payload) - set(SELECTED_UI_ENVIRONMENT_KEYS):
        raise RunnerError("selected test environment has unknown keys")
    if any(type(value) is not str or value not in SELECTED_UI_ENVIRONMENT_KEYS[key] for key, value in payload.items()):
        raise RunnerError("selected test environment has invalid values")
    return payload, {"path": str(resolved), "sha256": sha256(resolved), "values": payload}


def selected_test_environment_change(path: Path | None, target: str, original: dict[str, object] | None) -> str | None:
    if original is None:
        return None
    try:
        current = selected_test_environment(path, target)[1]
    except RunnerError as error:
        return "selected test environment is invalid after test: " + str(error)
    if current != original:
        return "selected test environment file changed"
    return None


def enumerate_selectors(template: Path, identifier: str, evidence: Path) -> set[str]:
    output = evidence / "test-enumeration.json"
    record = command(["xcodebuild", "test-without-building", "-xctestrun", str(template), "-destination", f"id={identifier}",
                      "-parallel-testing-enabled", "NO", "-enumerate-tests", "-test-enumeration-style", "flat",
                      "-test-enumeration-format", "json", "-test-enumeration-output-path", str(output)], cwd=IOS_ROOT, timeout=300)
    (evidence / "test-enumeration-command.json").write_text(json.dumps(record, indent=2, sort_keys=True), encoding="utf-8")
    if record.get("exit") != 0 or not output.is_file():
        raise RunnerError("native test enumeration failed")
    return parse_enumeration(output)


def selected(selectors: list[str], evidence: Path, diagnostic_dirty: bool = False, device: str = "iPhone 17",
             test_environment_path: Path | None = None) -> dict[str, object]:
    if not selectors:
        raise RunnerError("selected requires at least one --test selector")
    if any(not re.fullmatch(r"[A-Za-z0-9_./-]+", selector) for selector in selectors):
        raise RunnerError("test selector is invalid")
    targets = {selector.split("/", 1)[0] for selector in selectors}
    if len(targets) != 1 or targets not in ({"ACEClientAppTests"}, {"ACEClientAppUITests"}):
        raise RunnerError("selected tests must use one known unit or UI target")
    target = next(iter(targets))
    test_environment, environment_record = selected_test_environment(test_environment_path, target)
    if environment_record is not None:
        (evidence / "selected-input.json").write_text(json.dumps(environment_record, indent=2, sort_keys=True), encoding="utf-8")
    environment = preflight()
    candidate_record = candidate(allow_dirty=diagnostic_dirty)
    scheme = "ACEClientApp" if target == "ACEClientAppTests" else SCHEME
    build_record = build(candidate_record, evidence, scheme)
    if candidate(allow_dirty=diagnostic_dirty) != candidate_record:
        raise RunnerError("candidate identity changed after selected build")
    devices = environment["devices"]
    assert isinstance(devices, dict)
    identifier = str(devices[device]["udid"])
    initial_boot_state = simulator_state(identifier)
    restore_record: dict[str, object] = {"initialState": initial_boot_state}
    try:
        boot_required_simulator(identifier, initial_boot_state)
        enumerated = enumerate_selectors(Path(str(build_record["template"])), identifier, evidence)
        if not set(selectors).issubset(enumerated):
            raise RunnerError("selected test selector was not found by native enumeration")
        runfile = evidence / "selected.xctestrun"
        configure_xctestrun(Path(str(build_record["template"])), runfile, test_environment, target)
        bundle = evidence / "selected.xcresult"
        process = command(["xcodebuild", "test-without-building", "-xctestrun", str(runfile), "-destination", f"id={identifier}",
                           "-parallel-testing-enabled", "NO", *["-only-testing:" + selector for selector in selectors], "-resultBundlePath", str(bundle)], cwd=IOS_ROOT, timeout=1800)
        (evidence / "selected-command.json").write_text(json.dumps(process, indent=2, sort_keys=True), encoding="utf-8")
        (evidence / "selected.log").write_text(str(process.get("stdout", "")) + str(process.get("stderr", "")), encoding="utf-8")
        summary, attachments, failures, count = evidence / "selected-summary.json", evidence / "selected-attachments", [], 0
        if not bundle.is_dir():
            failures.append("result bundle missing")
        else:
            try: count = native_summary(bundle, summary, len(selectors))
            except RunnerError as error: failures.append(str(error))
            try: _export_attachments(bundle, attachments)
            except RunnerError as error:
                if target == "ACEClientAppUITests": failures.append(str(error))
        if process.get("exit") != 0: failures.append("native process failed")
        environment_error = selected_test_environment_change(test_environment_path, target, environment_record)
        if environment_error is not None:
            failures.append(environment_error)
        if candidate(allow_dirty=diagnostic_dirty) != candidate_record: failures.append("candidate identity changed after selected test")
        if failures:
            (evidence / "selected-failure.json").write_text(json.dumps({"candidate": candidate_record, "device": device,
                "selectors": selectors, "testEnvironment": environment_record, "command": process, "failures": failures}, indent=2, sort_keys=True), encoding="utf-8")
            raise RunnerError("selected native tests failed after evidence collection: " + "; ".join(failures))
        return {"candidate": candidate_record, "environment": environment, "device": device, "build": build_record, "selectors": selectors,
                "testEnvironment": environment_record, "nativeTestCount": count, "resultBundle": str(bundle), "resultBundleSha256": directory_hash(bundle),
                "runfileSha256": sha256(runfile), "summarySha256": sha256(summary), "attachmentSha256": directory_hash(attachments) if attachments.is_dir() else None,
                "command": process["command"], "logSha256": sha256(evidence / "selected.log"), "exit": process["exit"]}
    finally:
        if initial_boot_state == "Shutdown":
            try:
                restore_boot_state(identifier, initial_boot_state)
                restore_record["result"] = "restored"
            except RunnerError as error:
                restore_record["result"] = "failed"
                restore_record["error"] = str(error)
            (evidence / "selected-boot-restoration.json").write_text(json.dumps(restore_record, indent=2, sort_keys=True), encoding="utf-8")
            if restore_record["result"] == "failed":
                raise RunnerError("selected simulator boot restoration failed")


def main(argv: list[str] | None = None) -> int:
    os.umask(0o077)
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--evidence-root", type=Path,
                        default=Path.home() / "ace-private" / "mcx19b-implementation-20260914" / "ace-ios-local-runs")
    sub = parser.add_subparsers(dest="mode", required=True)
    sub.add_parser("preflight")
    selected_parser = sub.add_parser("selected")
    selected_parser.add_argument("--test", action="append", default=[])
    selected_parser.add_argument("--diagnostic-dirty", action="store_true")
    selected_parser.add_argument("--device", choices=DEVICES, default="iPhone 17")
    selected_parser.add_argument("--test-env-json", type=Path)
    pilot_parser = sub.add_parser("pilot")
    pilot_parser.add_argument("--pocock-evidence", type=Path, required=True)
    pilot_parser.add_argument("--functional-evidence", type=Path, required=True)
    pilot_parser.add_argument("--evidence-gate", type=Path, required=True)
    pilot_parser.add_argument("--private-input-record", type=Path, required=True)
    full_parser = sub.add_parser("full")
    full_parser.add_argument("--pilot-manifest", type=Path, required=True)
    full_parser.add_argument("--review-ledger", type=Path, required=True)
    args = parser.parse_args(argv)
    evidence_parent = args.evidence_root.expanduser().resolve()
    evidence = evidence_parent / (datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "-" + args.mode + "-" + os.urandom(6).hex())
    evidence.mkdir(parents=True, exist_ok=False)
    evidence.chmod(0o700)
    try:
        if args.mode == "preflight":
            result = preflight()
        elif args.mode == "selected":
            result = selected(args.test, evidence, args.diagnostic_dirty, args.device, args.test_env_json)
        elif args.mode == "pilot":
            frozen_candidate = candidate()
            readiness_paths = {"pocock": args.pocock_evidence, "functional": args.functional_evidence,
                               "evidence-gate": args.evidence_gate, "private-input": args.private_input_record}
            readiness = pilot_readiness(frozen_candidate, readiness_paths)
            result = run_coverage(pilot_cases(), evidence, frozen_candidate=frozen_candidate)
            if pilot_readiness(frozen_candidate, readiness_paths) != readiness or candidate() != frozen_candidate:
                raise RunnerError("pilot candidate or readiness evidence changed before manifest")
            result["readinessEvidence"] = readiness
            validate_pilot_result(result)
        else:
            current_candidate = candidate()
            pilot = validate_full_gate(args.pilot_manifest, args.review_ledger, current_candidate)
            result = run_coverage(coverage_cases(), evidence, pilot, frozen_candidate=current_candidate)
            result["pilotManifest"] = str(args.pilot_manifest.resolve())
            result["pilotManifestSha256"] = sha256(args.pilot_manifest)
            result["reviewLedger"] = str(args.review_ledger.resolve())
            result["reviewLedgerSha256"] = sha256(args.review_ledger)
        manifest = write_manifest(evidence, result, args.mode)
        print(json.dumps({"result": "passed", "manifest": str(manifest)}, sort_keys=True))
        return 0
    except RunnerError as error:
        failure = evidence / "failure.json"
        failure.write_text(json.dumps({"mode": args.mode, "error": str(error)}, indent=2, sort_keys=True), encoding="utf-8")
        print(json.dumps({"result": "blocked", "error": str(error), "evidence": str(failure)}, sort_keys=True), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
