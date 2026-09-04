#!/usr/bin/env python3
"""Run dependency-free SQE component checks without installing software."""
from __future__ import annotations

import argparse
import importlib.util
import json
import os
import shutil
import subprocess
import sys
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
    return data, errors


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
    destination = "platform=iOS Simulator,name=iPhone SE (3rd generation)"
    unit = ["xcodebuild", "test", "-project", "ACEClientApp.xcodeproj", "-scheme", "ACEClientApp", "-destination", destination, "-only-testing:ACEClientAppTests"]
    checks = [run_command("ios-65-unit", unit, ios, environment=ios_test_environment())]
    checks.extend(run_command(f"ios-core-ui-{method}", ["xcodebuild", "test", "-project", "ACEClientApp.xcodeproj", "-scheme", "ACEClientApp", "-destination", destination, f"-only-testing:ACEClientAppUITests/ACEClientAppUITests/{method}"], ios, environment=ios_test_environment()) for method in methods)
    if level == "release":
        for device in ("iPhone SE (3rd generation)", "iPhone 16 Pro Max"):
            for appearance in ("light", "dark"):
                for method in methods:
                    checks.append(run_command(f"ios-release-{device}-{appearance}-{method}", ["xcodebuild", "test", "-project", "ACEClientApp.xcodeproj", "-scheme", "ACEClientApp", "-destination", f"platform=iOS Simulator,name={device}", "-only-testing:ACEClientAppUITests/ACEClientAppUITests/" + method], ios, environment=ios_test_environment(appearance)))
        checks.extend([run_command("ios-evidence-contract", ["xcodebuild", "test", "-project", "ACEClientApp.xcodeproj", "-scheme", "ACEClientApp", "-destination", destination, "-only-testing:ACEClientAppTests/AcceptanceEvidenceContractTests"], ios, environment=ios_test_environment()), run_command("ios-negative-config", ["xcodebuild", "build", "-project", "ACEClientApp.xcodeproj", "-scheme", "ACEClientApp"], ios, environment=NEGATIVE_CONFIG_ENVIRONMENT, expected_failure=NEGATIVE_CONFIG_REJECTION)])
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
        results.append({"name": "mapping", "status": "passed", "exit": 0, "detail": "44 source IDs map once to G1-G6; manual evidence was not run"})
    else:
        results.extend(component_checks(args.level, args.component))
    exits = {item["exit"] for item in results}
    exit_code = 1 if 1 in exits else 2 if 2 in exits else 0
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    report = {"timestamp": datetime.now(timezone.utc).isoformat(), "level": args.level, "component": args.component, "mapping": data.get("iosPrimaryGroups", {}), "results": results, "exit": exit_code}
    report_path = REPORT_DIR / f"{args.level}-{args.component or 'manual'}.json"
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"report={report_path.relative_to(ROOT)}")
    for item in results: print(f"{item['name']}: {item['status']}: {item['detail'].splitlines()[0] if item['detail'] else ''}")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
