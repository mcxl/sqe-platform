#!/usr/bin/env python3
"""One manual G0 iOS diagnostic. It is never release evidence."""
from __future__ import annotations

import json
import hashlib
import math
import os
from pathlib import Path
import re
import selectors
import shutil
import signal
import stat
import subprocess
import sys
import tarfile
import time

try:
    from tools import run_tests as rt
except ModuleNotFoundError:
    import run_tests as rt

WORKFLOW = "ace-ios-diagnostic-manual"
NATIVE_CYCLE_WORKFLOW = "ace-ios-native-cycle-manual"
ROOT = Path("/private/tmp/mcx-19-diagnostic")
SAFE_ROOT = Path("/private/tmp/mcx-19-diagnostic-safe")
PRIVATE_ROOT = Path("/private/tmp/mcx-19-native-cycle-private")
PRIVATE_ARCHIVE_NAME = "mcx19-native-cycle-records.tar.gz"
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
COPY_CONTROLS_MODE = "copy-controls"
UNIT_SETTINGS_MODE = "unit-settings"
NATIVE_CYCLE_MODE = "native-cycle"
DIAGNOSTIC_MODE_ENVIRONMENT_KEY = "ACE_IOS_DIAGNOSTIC_MODE"
UNIT_TEST_TARGET = "ACEClientAppTests"
UNIT_EXPECTED_TEST_COUNT = 65
NATIVE_CYCLE_TEST_SELECTOR = (
    "ACEClientAppTests/ACEClientAppTests/"
    "testActionOrderAndUnknownFieldsRemainSafe"
)
NATIVE_CYCLE_EXPECTED_TEST_COUNT = 1
UNIT_WORKFLOW_SECONDS = 300
UNIT_SETUP_SECONDS = 90
NATIVE_CYCLE_SETUP_SECONDS = 180
UNIT_UI_SYNTAX_SECONDS = 8
UNIT_SETTINGS_QUERY_SECONDS = 8
UNIT_XCODEBUILD_SECONDS = 120
UNIT_SUMMARY_SECONDS = 12
UNIT_PUBLICATION_SECONDS = 5
UNIT_PUBLICATION_COUNT = 4
UNIT_ALLOCATED_SECONDS = (
    UNIT_SETUP_SECONDS + UNIT_UI_SYNTAX_SECONDS + (2 * UNIT_SETTINGS_QUERY_SECONDS)
    + UNIT_XCODEBUILD_SECONDS + UNIT_SUMMARY_SECONDS
    + (UNIT_PUBLICATION_COUNT * UNIT_PUBLICATION_SECONDS)
)
NATIVE_CYCLE_WORKFLOW_SECONDS = 480
NATIVE_CYCLE_ATTACHMENT_SECONDS = 30
NATIVE_CYCLE_PACKAGING_SECONDS = 45
NATIVE_CYCLE_DECODER_SECONDS = 30
NATIVE_CYCLE_ALLOCATED_SECONDS = (
    NATIVE_CYCLE_SETUP_SECONDS + UNIT_UI_SYNTAX_SECONDS + (2 * UNIT_SETTINGS_QUERY_SECONDS)
    + UNIT_XCODEBUILD_SECONDS + UNIT_SUMMARY_SECONDS
    + NATIVE_CYCLE_ATTACHMENT_SECONDS + NATIVE_CYCLE_PACKAGING_SECONDS
    + NATIVE_CYCLE_DECODER_SECONDS
    + (UNIT_PUBLICATION_COUNT * UNIT_PUBLICATION_SECONDS)
)
PRIVATE_RECORD_MAX_FILE_BYTES = 64 * 1024 * 1024
PRIVATE_RECORD_MAX_FILES = 4096
PRIVATE_RECORD_MAX_ARCHIVE_BYTES = 256 * 1024 * 1024
PRIVATE_RECORD_SECRET = re.compile(
    rb"(?i)(?:[\"']?(?:password|token|authorization|credential|secret)[\"']?\s*[:=]\s*[\"']?)(?!\[redacted\])[^\s,}\]]+"
)
PRIVATE_RECORD_CREDENTIAL_PREFIX = re.compile(
    rb"\b(?:gh[pousr]_[A-Za-z0-9_]+|github_pat_[A-Za-z0-9_]+|sk-[A-Za-z0-9_-]+)\b"
)
PRIVATE_RECORD_REAL_CLIENT = re.compile(rb"(?i)real[ _-]?client")
PRIVATE_ARCHIVE_PATH = re.compile(r"records/[A-Za-z0-9._/-]{1,1024}")
PRIVATE_RESULT_BUNDLE_ARCHIVE_PATH = re.compile(
    r"records/unit\.xcresult/[A-Za-z0-9._/~=-]{1,1024}"
)
PRIVATE_DECODE_MAX_OBJECTS = 64
PRIVATE_DECODE_MAX_OBJECT_BYTES = 1024 * 1024
PRIVATE_DECODE_MAX_TOTAL_BYTES = 8 * 1024 * 1024
PRIVATE_DECODE_MAX_NODES = 100_000
PRIVATE_DECODE_MAX_STRING_CHARACTERS = 512 * 1024
PRIVATE_DECODE_MAX_IDENTIFIER_CHARACTERS = 512
PRIVATE_DECODE_IDENTIFIER = re.compile(r"[A-Za-z0-9_~=-]{1,512}")


def redact(text: str) -> str:
    """Remove private data, while retaining allowlisted repository locations."""
    repository_root = re.escape(str(rt.ROOT.resolve()).replace("\\", "/")).replace(
        "/", r"[\\/]"
    )
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


def context(workflow: str = WORKFLOW) -> str:
    expected = os.environ.get("ACE_LIVE_EVIDENCE_APPROVED_COMMIT", "")
    if (
        sys.platform != "darwin"
        or os.environ.get(rt.LIVE_WORKFLOW_ENVIRONMENT_KEY) != workflow
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


def diagnostic_mode() -> str:
    mode = os.environ.get(DIAGNOSTIC_MODE_ENVIRONMENT_KEY, COPY_CONTROLS_MODE)
    if mode not in {COPY_CONTROLS_MODE, UNIT_SETTINGS_MODE, NATIVE_CYCLE_MODE}:
        raise ValueError("diagnostic mode rejected")
    return mode


def _existing_core_destination() -> str:
    """Resolve or create the verified core simulator without changing settings."""

    return rt.resolve_ios_destinations(
        (rt.IOS_CORE_DEVICE,), verification_seconds=UNIT_SETUP_SECONDS,
        require_ready=True, allow_create=True,
    )[rt.IOS_CORE_DEVICE]


def _native_cycle_destination() -> str:
    """Resolve the core simulator within the native-cycle setup limit."""

    return rt.resolve_ios_destinations(
        (rt.IOS_CORE_DEVICE,), verification_seconds=NATIVE_CYCLE_SETUP_SECONDS,
        require_ready=True, allow_create=True,
    )[rt.IOS_CORE_DEVICE]


def _bounded_ui_syntax_probe(identifier: str) -> dict[str, object]:
    """Retain only the two requested simctl UI syntax tokens."""

    log = ROOT / "simctl-help-ui.log"
    result = run(["xcrun", "simctl", "help", "ui"], {}, log, UNIT_UI_SYNTAX_SECONDS)
    state, content = _safe_text(log, LOG_RESPONSE_LIMIT)
    record: dict[str, object] = {
        "commandKind": "simctl-help-ui", **result, "responseStatus": state,
        "requestedSettings": ["appearance", "content_size"],
    }
    if state == "available" and content is not None:
        record["supportedSettings"] = [
            setting for setting in ("appearance", "content_size")
            if re.search(rf"(?m)^\s*{re.escape(setting)}(?:\s|$)", content)
        ]
    return record


def _bounded_unit_settings_probes(identifier: str) -> list[dict[str, object]]:
    """Read only fixed single-token simulator responses for the unit probe."""

    probes = []
    for setting in ("appearance", "content_size"):
        log = ROOT / f"unit-simctl-{setting}-query.log"
        result = run(
            ["xcrun", "simctl", "ui", identifier, setting], {}, log,
            UNIT_SETTINGS_QUERY_SECONDS,
        )
        state, content = _safe_text(log, 128)
        record: dict[str, object] = {
            "commandKind": "simctl-ui-query", "setting": setting,
            **result, "responseStatus": state,
        }
        if state == "available" and content is not None:
            value = content.strip().lower()
            if re.fullmatch(r"[a-z-]{1,80}", value):
                record["response"] = value
            else:
                record["responseStatus"] = "unpublished-invalid"
        probes.append(record)
    return probes


def _collect_unit_summary(unit: dict[str, object], bundle: Path) -> None:
    """Collect counts and structured failures without publishing summary text."""

    unit["testFailures"] = []
    unit["testFailureStatus"] = "unavailable"
    if not bundle.is_dir() or bundle.is_symlink():
        unit["summaryStatus"] = "result-bundle-unavailable"
        return
    summary = ROOT / "unit-summary.json"
    result = run(
        ["xcrun", "xcresulttool", "get", "test-results", "summary", "--path", str(bundle)],
        {}, summary, UNIT_SUMMARY_SECONDS,
    )
    unit["summaryCommand"] = {
        "commandKind": "xcresult-summary", **result,
        "responseStatus": "not-published" if result.get("processExit") == 0 else "command-failed",
    }
    if result.get("processExit") != 0:
        unit["summaryStatus"] = "command-failed"
        return
    state, content = rt._bounded_live_file_text(ROOT, summary, rt.LIVE_RESULT_SUMMARY_MAX_BYTES)
    if state != "available" or content is None:
        unit["summaryStatus"] = state
        return
    try:
        payload = json.loads(content)
    except (ValueError, RecursionError):
        unit["summaryStatus"] = "unreadable"
        return
    counts = rt._xcresult_counts(payload)
    if counts is not None:
        unit["actualCounts"] = {"passed": counts[0], "failed": counts[1], "skipped": counts[2]}
    failures, failure_status = rt._xcresult_failure_details(payload)
    unit["testFailures"] = rt._published_test_failures(failures, True)
    unit["testFailureStatus"] = failure_status
    unit["summaryStatus"] = "available"


class PrivateRecordCollectionError(ValueError):
    """Stop private collection without disclosing a raw record."""

    def __init__(
        self,
        reason: str,
        diagnostic: dict[str, object] | None = None,
        sensitive_matcher: str | None = None,
        private_candidate: bytes | None = None,
        private_record_identity: str | None = None,
    ) -> None:
        super().__init__(reason)
        self.diagnostic = diagnostic
        self.sensitive_matcher = sensitive_matcher
        self.private_candidate = private_candidate
        self.private_record_identity = private_record_identity


def _archive_path_source(archive_path: str) -> str:
    if archive_path.startswith("records/unit.xcresult/"):
        return "result-bundle"
    if archive_path.startswith("records/unit-attachment-export/"):
        return "attachment-export"
    return "generated-record"


def _archive_path_diagnostic(archive_path: str) -> dict[str, object]:
    """Classify an invalid archive path without retaining it."""

    punctuation = []
    for character, label in (
        ("=", "equals"), ("+", "plus"), ("~", "tilde"), (" ", "space"),
    ):
        if character in archive_path:
            punctuation.append(label)
    allowed_diagnostic_characters = (
        "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789._/-=+~ "
    )
    if any(
        ord(character) < 128 and character not in allowed_diagnostic_characters
        for character in archive_path
    ):
        punctuation.append("other-ascii")
    if any(ord(character) > 127 for character in archive_path):
        punctuation.append("non-ascii")
    relative = archive_path.removeprefix("records/")
    if not archive_path.startswith("records/") or not relative:
        rule = "prefix"
    elif len(relative) > 1024:
        rule = "path-length"
    elif any(part == "" for part in relative.split("/")):
        rule = "empty-segment"
    elif any(part in {".", ".."} for part in relative.split("/")):
        rule = "dot-segment"
    else:
        rule = "unsupported-character"
    return {
        "source": _archive_path_source(archive_path),
        "rule": rule,
        "punctuationClasses": punctuation,
    }


def _sensitive_record_matcher(content: bytes) -> str | None:
    if PRIVATE_RECORD_SECRET.search(content):
        return "key-value"
    if PRIVATE_RECORD_CREDENTIAL_PREFIX.search(content):
        return "credential-prefix"
    if PRIVATE_RECORD_REAL_CLIENT.search(content):
        return "real-client"
    return None


def _credential_prefix_classification(
    content: bytes, match: re.Match[bytes] | None = None
) -> dict[str, str]:
    """Classify a matched credential prefix without retaining its bytes."""

    match = match or PRIVATE_RECORD_CREDENTIAL_PREFIX.search(content)
    if match is None:
        return {}
    observed = match.group()
    if observed.startswith(b"github_pat_"):
        family = "github-pat-style"
    elif observed.startswith(b"sk-"):
        family = "sk-dash"
    else:
        family = "github-legacy-style"
    if len(observed) <= 20:
        length_bucket = "up-to-20"
    elif len(observed) <= 40:
        length_bucket = "21-to-40"
    elif len(observed) <= 80:
        length_bucket = "41-to-80"
    else:
        length_bucket = "81-or-more"
    if match.start() < 64 or len(content) - match.end() < 64:
        neighbourhood_shape = "boundary-truncated"
    else:
        neighbourhood = content[match.start() - 64:match.end() + 64]
        try:
            decoded = neighbourhood.decode("utf-8")
        except UnicodeDecodeError:
            neighbourhood_shape = "non-utf8"
        else:
            neighbourhood_shape = (
                "utf8-with-control"
                if any(
                    not character.isprintable() and character not in "\t\n\r"
                    for character in decoded
                )
                else "utf8-printable"
            )
    return {
        "prefixFamily": family,
        "observedLengthBucket": length_bucket,
        "neighbourhoodShape": neighbourhood_shape,
    }


def _private_record_kind(archive_path: str) -> str:
    """Classify a record name without retaining the name."""

    name = archive_path.rsplit("/", 1)[-1]
    if name == "Info.plist":
        return "info-plist"
    if (
        archive_path == "records/unit.xcresult/Data"
        or archive_path.startswith("records/unit.xcresult/Data/")
    ):
        return "data-object"
    if name.endswith(".plist"):
        return "plist"
    if name.endswith(".json"):
        return "json"
    if name.endswith(".log"):
        return "text-log"
    if name.endswith(".xcactivitylog"):
        return "activity-log"
    return "other"


def _private_collection_root() -> Path:
    if PRIVATE_ROOT.exists() or PRIVATE_ROOT.is_symlink():
        raise PrivateRecordCollectionError("private-root-unavailable")
    PRIVATE_ROOT.mkdir(mode=0o700, parents=True)
    return PRIVATE_ROOT


def _private_relative(root: Path, path: Path) -> Path:
    try:
        relative = path.resolve().relative_to(root.resolve())
    except (OSError, ValueError) as error:
        raise PrivateRecordCollectionError("path-escape") from error
    if not relative.parts or any(part in {"", ".", ".."} for part in relative.parts):
        raise PrivateRecordCollectionError("invalid-relative-path")
    return relative


def _private_regular_files(root: Path) -> list[Path]:
    if root.is_symlink() or not root.is_dir():
        raise PrivateRecordCollectionError("record-root-unavailable")
    selected = []
    for path in sorted(root.rglob("*")):
        if path.is_symlink():
            raise PrivateRecordCollectionError("symlink-record")
        _private_relative(root, path)
        try:
            mode = path.lstat().st_mode
        except OSError as error:
            raise PrivateRecordCollectionError("record-stat-failed") from error
        if stat.S_ISDIR(mode):
            continue
        if not stat.S_ISREG(mode):
            raise PrivateRecordCollectionError("special-record")
        selected.append(path)
        if len(selected) > PRIVATE_RECORD_MAX_FILES:
            raise PrivateRecordCollectionError("record-count-exceeded")
    return selected


def _private_file_metadata(path: Path) -> tuple[int, str, list[dict[str, str]]]:
    """Read every byte and return safe scanner observations with file metadata."""

    if path.is_symlink() or not path.is_file():
        raise PrivateRecordCollectionError("record-unavailable")
    try:
        size = path.stat().st_size
    except OSError as error:
        raise PrivateRecordCollectionError("record-stat-failed") from error
    if size > PRIVATE_RECORD_MAX_FILE_BYTES:
        raise PrivateRecordCollectionError("record-size-exceeded")
    try:
        with path.open("rb") as stream:
            content = stream.read(PRIVATE_RECORD_MAX_FILE_BYTES + 1)
        if len(content) > PRIVATE_RECORD_MAX_FILE_BYTES:
            raise PrivateRecordCollectionError("record-size-exceeded")
        if path.stat().st_size != len(content):
            raise PrivateRecordCollectionError("record-changed-during-read")
    except OSError as error:
        raise PrivateRecordCollectionError("record-read-failed") from error
    observations: list[dict[str, str]] = []
    for matcher, pattern in (
        ("key-value", PRIVATE_RECORD_SECRET),
        ("credential-prefix", PRIVATE_RECORD_CREDENTIAL_PREFIX),
        ("real-client", PRIVATE_RECORD_REAL_CLIENT),
    ):
        for match in pattern.finditer(content):
            observation = {"matcher": matcher}
            if matcher == "credential-prefix":
                observation.update(_credential_prefix_classification(content, match))
            observations.append(observation)
    return size, hashlib.sha256(content).hexdigest(), observations


def _private_quarantine_permitted(
    archive_path: str, command: str, observation: dict[str, str], allow_quarantine: bool
) -> bool:
    """Allow only the approved unresolved binary result-data exception."""

    return (
        allow_quarantine
        and command == "xcodebuild-test"
        and archive_path.startswith("records/unit.xcresult/Data/")
        and observation.get("matcher") == "credential-prefix"
        and observation.get("neighbourhoodShape") == "non-utf8"
    )


def _private_record_metadata(
    path: Path, archive_path: str, command: str, allow_quarantine: bool
) -> tuple[int, str, str]:
    """Reject every non-approved match after the complete-file scan."""

    size, digest, observations = _private_file_metadata(path)
    quarantined = False
    for observation in observations:
        if _private_quarantine_permitted(
            archive_path, command, observation, allow_quarantine
        ):
            quarantined = True
            continue
        diagnostic = {
            "source": _archive_path_source(archive_path),
            **observation,
        }
        if observation.get("matcher") == "credential-prefix":
            diagnostic["recordKind"] = _private_record_kind(archive_path)
        raise PrivateRecordCollectionError(
            "sensitive-record", diagnostic,
            sensitive_matcher=observation.get("matcher"),
        )
    return size, digest, "quarantined-pending-review" if quarantined else "complete"


def _write_private_json(root: Path, name: str, value: object) -> Path:
    path = root / name
    temporary = root / f".{name}.tmp"
    if path.exists() or path.is_symlink() or temporary.exists() or temporary.is_symlink():
        raise PrivateRecordCollectionError("private-record-path-unavailable")
    try:
        temporary.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        os.replace(temporary, path)
    except OSError as error:
        temporary.unlink(missing_ok=True)
        raise PrivateRecordCollectionError("private-record-write-failed") from error
    return path


def _native_attachment_export(bundle: Path, unit: dict[str, object]) -> Path:
    output = ROOT / "unit-attachment-export"
    log = ROOT / "unit-attachment-export.log"
    if output.exists() or output.is_symlink():
        raise PrivateRecordCollectionError("attachment-output-unavailable")
    command = [
        "xcrun", "xcresulttool", "export", "attachments", "--path", str(bundle),
        "--output-path", str(output),
    ]
    result = run(
        command,
        {}, log, NATIVE_CYCLE_ATTACHMENT_SECONDS,
    )
    unit["attachmentExportCommand"] = {
        "executedCommand": command,
        "processExit": result.get("processExit"),
    }
    if result.get("processExit") != 0:
        raise PrivateRecordCollectionError("attachment-export-failed")
    _private_regular_files(output)
    return output


def _native_failure_export(summary: Path, private_root: Path) -> Path:
    try:
        payload = json.loads(summary.read_text(encoding="utf-8"))
    except (OSError, ValueError, RecursionError) as error:
        raise PrivateRecordCollectionError("failure-export-unavailable") from error
    failures, status = rt._xcresult_failure_details(payload)
    return _write_private_json(
        private_root, "unit-failures.json", {"status": status, "failures": failures}
    )


def _private_terminate(process: subprocess.Popen[bytes]) -> bool:
    """Stop only the decoder process group that this helper started."""

    try:
        os.killpg(process.pid, signal.SIGKILL)
    except (AttributeError, OSError):
        if process.poll() is None:
            try:
                process.kill()
            except OSError:
                return False
    try:
        process.wait(timeout=1)
    except (OSError, subprocess.TimeoutExpired):
        return False
    return True


def _private_xcresult_error_classification(stderr: bytes) -> str:
    """Classify bounded private stderr without retaining its text or values."""

    lowered = stderr.lower()
    if b"unrecognized option" in lowered or b"unknown option" in lowered:
        return "unsupported-option"
    if b"unknown command" in lowered or b"unrecognized command" in lowered:
        return "unsupported-command"
    if b"invalid" in lowered:
        return "invalid-request"
    return "unclassified"


def _write_private_streams(
    streams: tuple[Path, Path], stdout: bytes, stderr: bytes
) -> None:
    """Write bounded exact command streams only to fixed private paths."""

    for path, content in zip(streams, (stdout, stderr), strict=True):
        temporary = path.with_name(f".{path.name}.tmp")
        if (
            path.exists() or path.is_symlink()
            or temporary.exists() or temporary.is_symlink()
        ):
            raise PrivateRecordCollectionError("private-record-path-unavailable")
        try:
            temporary.write_bytes(content)
            os.replace(temporary, path)
        except OSError as error:
            temporary.unlink(missing_ok=True)
            raise PrivateRecordCollectionError("private-record-write-failed") from error


def _private_xcresult_command(
    command: list[str], timeout_seconds: float, output_limit: int,
    private_result: dict[str, object] | None = None,
    private_streams: tuple[Path, Path] | None = None,
) -> tuple[str, bytes | None]:
    """Run native decoding with private, bounded output and no log file."""

    if timeout_seconds <= 0 or output_limit <= 0:
        return "timeout", None
    process: subprocess.Popen[bytes] | None = None
    selector: selectors.BaseSelector | None = None
    content = bytearray()
    errors = bytearray()
    try:
        process = subprocess.Popen(
            command,
            cwd=rt.ROOT / "ios/ACEClientApp",
            env=diagnostic_command_environment({}),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            start_new_session=True,
        )
        if process.stdout is None or process.stderr is None:
            _private_terminate(process)
            return "start-failed", None
        selector = selectors.DefaultSelector()
        selector.register(process.stdout, selectors.EVENT_READ, "stdout")
        selector.register(process.stderr, selectors.EVENT_READ, "stderr")
        deadline = time.monotonic() + timeout_seconds
        combined_size = 0
        while selector.get_map():
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                if private_streams is not None:
                    _write_private_streams(private_streams, bytes(content), bytes(errors))
                return ("timeout", None) if _private_terminate(process) else ("cleanup-failed", None)
            events = selector.select(min(remaining, 0.1))
            for key, _event in events:
                chunk = os.read(key.fd, min(64 * 1024, output_limit - combined_size + 1))
                if not chunk:
                    selector.unregister(key.fileobj)
                    continue
                combined_size += len(chunk)
                if combined_size > output_limit:
                    if private_streams is not None:
                        _write_private_streams(private_streams, bytes(content), bytes(errors))
                    return ("output-limit", None) if _private_terminate(process) else ("cleanup-failed", None)
                if key.data == "stdout":
                    content.extend(chunk)
                else:
                    errors.extend(chunk)
        exit_code = process.wait(timeout=max(0.1, deadline - time.monotonic()))
        if private_streams is not None:
            _write_private_streams(private_streams, bytes(content), bytes(errors))
        if private_result is not None:
            published_exit = rt._published_process_exit(exit_code)
            if published_exit is not None:
                private_result["processExit"] = published_exit
            if exit_code != 0:
                private_result["errorClassification"] = _private_xcresult_error_classification(
                    bytes(errors)
                )
        return ("complete", bytes(content)) if exit_code == 0 else ("command-failed", None)
    except (OSError, ValueError, subprocess.SubprocessError):
        if process is not None:
            return ("start-failed", None) if _private_terminate(process) else ("cleanup-failed", None)
        return "start-failed", None
    finally:
        if selector is not None:
            selector.close()
        if process is not None:
            if process.stdout is not None:
                process.stdout.close()
            if process.stderr is not None:
                process.stderr.close()


def _private_type_name(value: object) -> str | None:
    if not isinstance(value, dict):
        return None
    descriptor = value.get("_type")
    if not isinstance(descriptor, dict):
        return None
    name = descriptor.get("_name")
    return name if isinstance(name, str) else None


def _private_reference_identifier(value: object) -> tuple[str | None, bool]:
    """Read only an identifier in a JSON value that declares Reference type."""

    if _private_type_name(value) != "Reference" or not isinstance(value, dict):
        return None, False
    encoded = value.get("_value")
    identifier = encoded.get("id") if isinstance(encoded, dict) else value.get("id")
    if isinstance(identifier, dict):
        identifier = identifier.get("_value")
    if (
        not isinstance(identifier, str)
        or len(identifier) > PRIVATE_DECODE_MAX_IDENTIFIER_CHARACTERS
        or PRIVATE_DECODE_IDENTIFIER.fullmatch(identifier) is None
    ):
        return None, True
    return identifier, True


def _private_decoded_values(
    value: object, candidate: bytes
) -> tuple[bool, bool, list[str], bool]:
    """Inspect decoded values, excluding schema labels and Reference identifiers."""

    pending = [value]
    references: list[str] = []
    nodes = 0
    value_match = False
    reference_match = False
    while pending:
        current = pending.pop()
        nodes += 1
        if nodes > PRIVATE_DECODE_MAX_NODES:
            return value_match, reference_match, references, False
        identifier, is_reference = _private_reference_identifier(current)
        if is_reference:
            if identifier is None:
                return value_match, reference_match, references, False
            references.append(identifier)
            reference_match = reference_match or candidate in identifier.encode("utf-8")
            continue
        if isinstance(current, dict):
            pending.extend(
                child for key, child in current.items()
                if key not in {"_type", "formatDescription"}
            )
        elif isinstance(current, list):
            pending.extend(current)
        elif isinstance(current, str):
            if len(current) > PRIVATE_DECODE_MAX_STRING_CHARACTERS:
                return value_match, reference_match, references, False
            try:
                encoded = current.encode("utf-8")
            except UnicodeEncodeError:
                return value_match, reference_match, references, False
            if candidate in encoded and _sensitive_record_matcher(encoded) is not None:
                value_match = True
    return value_match, reference_match, references, True


def _private_decode_result_bundle(
    bundle: Path, candidate: bytes, private_record_identity: str | None, deadline: float
) -> dict[str, object]:
    """Compare a private candidate with native decoded strings, and fail closed."""

    def unavailable(reason: str) -> dict[str, object]:
        return {
            "status": "decode-unavailable",
            "decodeReason": reason,
            "inspectedScope": "none",
            "decodedGraphCoverage": "unavailable",
            "flaggedRecordCoverage": "unverified",
            "decodedObjectCount": 0,
            "observedMatchLocation": "not-seen",
        }

    if not candidate or private_record_identity is None or not bundle.is_dir() or bundle.is_symlink():
        return unavailable("input-unavailable")

    decoder_deadline = min(deadline, time.monotonic() + NATIVE_CYCLE_DECODER_SECONDS)

    def command(arguments: list[str], maximum_bytes: int) -> tuple[str, bytes | None]:
        remaining = decoder_deadline - time.monotonic()
        if remaining <= 0:
            return "timeout", None
        return _private_xcresult_command(arguments, min(5.0, remaining), maximum_bytes)

    top_status, top_help = command(["xcrun", "xcresulttool", "--help"], 64 * 1024)
    if top_status != "complete" or top_help is None or b"get" not in top_help:
        return unavailable("top-help-unavailable")
    get_status, get_help = command(["xcrun", "xcresulttool", "get", "--help"], 64 * 1024)
    if get_status != "complete" or get_help is None or b"object" not in get_help:
        return unavailable("get-help-unavailable")
    object_status, object_help = command(
        ["xcrun", "xcresulttool", "get", "object", "--help"], 64 * 1024
    )
    required_options = (b"--legacy", b"--path", b"--format", b"--id")
    if (
        object_status != "complete"
        or object_help is None
        or not all(option in object_help for option in required_options)
    ):
        return unavailable("object-help-unsupported")

    root_status, root_data = command(
        [
            "xcrun", "xcresulttool", "get", "object", "--legacy", "--path",
            str(bundle), "--format", "json",
        ],
        PRIVATE_DECODE_MAX_OBJECT_BYTES,
    )
    if root_status != "complete" or root_data is None:
        return unavailable(f"root-{root_status}")
    try:
        root = json.loads(root_data)
    except (ValueError, UnicodeDecodeError, RecursionError):
        return unavailable("root-schema-unreadable")

    pending: list[str] = []
    visited: set[str] = set()
    decoded_object_count = 0
    total_bytes = len(root_data)
    if total_bytes > PRIVATE_DECODE_MAX_TOTAL_BYTES:
        return unavailable("total-output-limit")
    value_match = False
    reference_match = False
    complete_graph = True
    reason = "flagged-record-coverage-unverified"
    current: object | None = root
    if not isinstance(root, (dict, list)):
        complete_graph = False
        reason = "root-schema-incomplete"
    while current is not None:
        decoded_object_count += 1
        current_value_match, current_reference_match, references, complete_values = _private_decoded_values(
            current, candidate
        )
        value_match = value_match or current_value_match
        reference_match = reference_match or current_reference_match
        complete_graph = complete_graph and complete_values
        if not complete_values:
            reason = "decoded-values-incomplete"
        for identifier in references:
            if identifier not in visited and identifier not in pending:
                pending.append(identifier)
        if not pending:
            break
        if decoded_object_count >= PRIVATE_DECODE_MAX_OBJECTS:
            complete_graph = False
            reason = "object-limit"
            break
        identifier = pending.pop()
        visited.add(identifier)
        remaining_bytes = PRIVATE_DECODE_MAX_TOTAL_BYTES - total_bytes
        if remaining_bytes <= 0:
            complete_graph = False
            reason = "total-output-limit"
            break
        child_status, child_data = command(
            [
                "xcrun", "xcresulttool", "get", "object", "--legacy", "--path",
                str(bundle), "--id", identifier, "--format", "json",
            ],
            min(PRIVATE_DECODE_MAX_OBJECT_BYTES, remaining_bytes),
        )
        if child_status != "complete" or child_data is None:
            complete_graph = False
            reason = f"child-{child_status}"
            break
        if len(child_data) > remaining_bytes:
            complete_graph = False
            reason = "total-output-limit"
            break
        total_bytes += len(child_data)
        try:
            child = json.loads(child_data)
        except (ValueError, UnicodeDecodeError, RecursionError):
            complete_graph = False
            reason = "child-schema-unreadable"
            break
        if not isinstance(child, (dict, list)):
            complete_graph = False
            reason = "child-schema-incomplete"
            break
        current = child

    location = (
        "both" if value_match and reference_match
        else "value" if value_match
        else "reference-id" if reference_match
        else "not-seen"
    )
    return {
        "status": (
            "decoded-string-match" if value_match
            else "reference-id-match" if reference_match
            else "coverage-incomplete"
        ),
        "decodeReason": (
            "value-observed" if value_match
            else "reference-id-observed" if reference_match
            else reason
        ),
        "inspectedScope": "decoded-result-object-graph",
        "decodedGraphCoverage": "complete-graph" if complete_graph else "partial-graph",
        "flaggedRecordCoverage": "unverified",
        "decodedObjectCount": decoded_object_count,
        "observedMatchLocation": location,
    }


def _private_help_supports_path_only_command(help_output: bytes) -> bool:
    """Accept a command only when its installed usage requires no extra flags."""

    try:
        text = help_output.decode("utf-8")
    except UnicodeDecodeError:
        return False
    for line in text.splitlines():
        if "usage:" not in line.casefold():
            continue
        required = re.sub(r"\[[^\]]*\]", "", line)
        flags = set(re.findall(r"--[A-Za-z][A-Za-z0-9-]*", required))
        if flags == {"--path"}:
            return True
    return False


def _private_xcresult_inspection_capabilities(
    bundle: Path, private_root: Path, deadline: float
) -> tuple[dict[str, dict[str, object]], list[tuple[Path, str, str]]]:
    """Use only installed help-approved Apple inspection commands.

    This helper records command outcomes only.  It does not map an export to a raw
    Data member and it does not resolve a quarantined record.
    """

    capabilities: dict[str, dict[str, object]] = {}
    sources: list[tuple[Path, str, str]] = []
    commands = (
        ("test-details", ["xcrun", "xcresulttool", "get", "test-results", "test-details"]),
        ("activities", ["xcrun", "xcresulttool", "get", "test-results", "activities"]),
        ("test-list", ["xcrun", "xcresulttool", "get", "test-results", "tests"]),
        ("log", ["xcrun", "xcresulttool", "get", "log"]),
    )
    for name, base in commands:
        remaining = deadline - time.monotonic()
        record: dict[str, object] = {"status": "unavailable"}
        help_streams = (
            private_root / f"inspection-{name}-help.stdout",
            private_root / f"inspection-{name}-help.stderr",
        )
        if remaining <= 0:
            record["status"] = "time-reserve-exhausted"
            capabilities[name] = record
            continue
        sources.extend((
            (help_streams[0], f"records/private-inspection/{name}-help.stdout", "xcresult-private-inspection-help"),
            (help_streams[1], f"records/private-inspection/{name}-help.stderr", "xcresult-private-inspection-help"),
        ))
        help_record: dict[str, object] = {}
        help_status, help_output = _private_xcresult_command(
            [*base, "--help"], min(3.0, remaining), 64 * 1024, help_record,
            help_streams,
        )
        if (
            help_status != "complete"
            or help_output is None
            or not _private_help_supports_path_only_command(help_output)
        ):
            record.update(help_record)
            record["status"] = "syntax-pending"
            capabilities[name] = record
            continue
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            record["status"] = "time-reserve-exhausted"
            capabilities[name] = record
            continue
        command_record: dict[str, object] = {}
        command_streams = (
            private_root / f"inspection-{name}.stdout",
            private_root / f"inspection-{name}.stderr",
        )
        sources.extend((
            (command_streams[0], f"records/private-inspection/{name}.stdout", "xcresult-private-inspection"),
            (command_streams[1], f"records/private-inspection/{name}.stderr", "xcresult-private-inspection"),
        ))
        command_status, _ = _private_xcresult_command(
            [*base, "--path", str(bundle)],
            min(3.0, remaining),
            PRIVATE_DECODE_MAX_OBJECT_BYTES,
            command_record,
            command_streams,
        )
        record.update(command_record)
        record["status"] = "available" if command_status == "complete" else command_status
        capabilities[name] = record
    return capabilities, sources


def _private_record_entries(
    sources: list[tuple[Path, str, str]], state: str, allow_quarantine: bool = False
) -> list[dict[str, object]]:
    if len(sources) > PRIVATE_RECORD_MAX_FILES:
        raise PrivateRecordCollectionError("record-count-exceeded")
    entries: list[dict[str, object]] = []
    archive_paths: set[str] = set()
    for path, archive_path, command in sources:
        relative = archive_path.removeprefix("records/")
        path_pattern = (
            PRIVATE_RESULT_BUNDLE_ARCHIVE_PATH
            if archive_path.startswith("records/unit.xcresult/")
            and command == "xcodebuild-test"
            else PRIVATE_ARCHIVE_PATH
        )
        if (
            len(relative) > 1024
            or not path_pattern.fullmatch(archive_path)
            or not relative
            or any(part in {"", ".", ".."} for part in relative.split("/"))
        ):
            raise PrivateRecordCollectionError(
                "archive-path-invalid", _archive_path_diagnostic(archive_path)
            )
        if archive_path in archive_paths:
            raise PrivateRecordCollectionError("archive-path-duplicate")
        archive_paths.add(archive_path)
        size, digest, scanner_state = _private_record_metadata(
            path, archive_path, command, allow_quarantine
        )
        entry: dict[str, object] = {
            "relativePath": archive_path,
            "producingCommand": command,
            "size": size,
            "sha256": digest,
            "state": state,
        }
        if scanner_state != "complete":
            entry["scannerStatus"] = scanner_state
        entries.append(entry)
    return entries


def _write_private_archive(
    private_root: Path,
    sources: list[tuple[Path, str, str]],
    entries: list[dict[str, object]],
    allow_quarantine: bool = False,
) -> Path:
    archive = private_root / PRIVATE_ARCHIVE_NAME
    temporary = private_root / f".{PRIVATE_ARCHIVE_NAME}.tmp"
    if archive.exists() or archive.is_symlink() or temporary.exists() or temporary.is_symlink():
        raise PrivateRecordCollectionError("archive-path-unavailable")
    expected = {
        entry["relativePath"]: (
            entry["size"], entry["sha256"], entry.get("scannerStatus", "complete")
        )
        for entry in entries
    }
    if len(expected) != len(entries) or sum(entry["size"] for entry in entries) > PRIVATE_RECORD_MAX_ARCHIVE_BYTES:
        raise PrivateRecordCollectionError("archive-size-or-path-invalid")
    try:
        with tarfile.open(temporary, "w:gz", format=tarfile.PAX_FORMAT) as output:
            for path, archive_path, command in sources:
                size, digest, scanner_state = _private_record_metadata(
                    path, archive_path, command, allow_quarantine
                )
                if expected.get(archive_path) != (size, digest, scanner_state):
                    raise PrivateRecordCollectionError("record-changed-during-packaging")
                info = output.gettarinfo(str(path), arcname=archive_path)
                if not info.isreg():
                    raise PrivateRecordCollectionError("archive-record-not-regular")
                info.uid = 0
                info.gid = 0
                info.uname = ""
                info.gname = ""
                info.mtime = 0
                with path.open("rb") as stream:
                    output.addfile(info, stream)
        _verify_private_archive(temporary, expected)
        os.replace(temporary, archive)
    except PrivateRecordCollectionError:
        temporary.unlink(missing_ok=True)
        raise
    except (OSError, tarfile.TarError) as error:
        temporary.unlink(missing_ok=True)
        raise PrivateRecordCollectionError("archive-write-failed") from error
    return archive


def _verify_private_archive(
    archive: Path, expected: dict[str, tuple[object, object, object]]
) -> None:
    try:
        with tarfile.open(archive, "r:gz") as input_archive:
            members = input_archive.getmembers()
            names = [member.name for member in members]
            if len(names) != len(set(names)) or set(names) != set(expected):
                raise PrivateRecordCollectionError("archive-members-invalid")
            for member in members:
                if not member.isreg() or expected[member.name][0] != member.size:
                    raise PrivateRecordCollectionError("archive-member-invalid")
                stream = input_archive.extractfile(member)
                if stream is None:
                    raise PrivateRecordCollectionError("archive-member-unreadable")
                digest = hashlib.sha256()
                while chunk := stream.read(64 * 1024):
                    digest.update(chunk)
                if digest.hexdigest() != expected[member.name][1]:
                    raise PrivateRecordCollectionError("archive-member-checksum-invalid")
    except (OSError, tarfile.TarError) as error:
        raise PrivateRecordCollectionError("archive-validation-failed") from error


def _collect_native_cycle_records(
    commit: str, unit: dict[str, object], bundle: Path, decode_deadline: float | None = None
) -> str:
    """Archive one command-derived record set, or return a safe failure reason."""

    try:
        if not bundle.is_dir() or bundle.is_symlink():
            raise PrivateRecordCollectionError("result-bundle-unavailable")
        if unit.get("summaryStatus") != "available":
            raise PrivateRecordCollectionError("summary-unavailable")
        private_root = _private_collection_root()
        summary = ROOT / "unit-summary.json"
        attachments = _native_attachment_export(bundle, unit)
        failure_export = _native_failure_export(summary, private_root)
        bundle_sources = _private_regular_files(bundle)
        if not bundle_sources:
            raise PrivateRecordCollectionError("result-bundle-empty")
        attachment_sources = [
            (path, f"records/unit-attachment-export/{_private_relative(attachments, path).as_posix()}",
             "xcresult-attachment-export")
            for path in _private_regular_files(attachments)
        ]
        state = "complete" if isinstance(unit.get("processExit"), int) else "incomplete"
        attachment_inventory = _write_private_json(
            private_root,
            "unit-attachment-inventory.json",
            {"files": _private_record_entries(attachment_sources, state)},
        )
        sources: list[tuple[Path, str, str]] = [
            (path, f"records/unit.xcresult/{_private_relative(bundle, path).as_posix()}", "xcodebuild-test")
            for path in bundle_sources
        ] + [
            (ROOT / "unit.log", "records/unit.log", "xcodebuild-test"),
            (ROOT / "unit-summary.json", "records/unit-summary.json", "xcresult-summary"),
            (ROOT / "simctl-help-ui.log", "records/simctl-help-ui.log", "simctl-help-ui"),
            (ROOT / "unit-simctl-appearance-query.log", "records/unit-simctl-appearance-query.log", "simctl-ui-appearance-query"),
            (ROOT / "unit-simctl-content_size-query.log", "records/unit-simctl-content_size-query.log", "simctl-ui-content_size-query"),
            (ROOT / "unit-attachment-export.log", "records/unit-attachment-export.log", "xcresult-attachment-export"),
            (failure_export, "records/unit-failures.json", "failure-export"),
            (attachment_inventory, "records/unit-attachment-inventory.json", "attachment-inventory"),
            *attachment_sources,
        ]
        entries = _private_record_entries(sources, state, allow_quarantine=True)
        collection_state = (
            "quarantined-pending-review"
            if any(entry.get("scannerStatus") == "quarantined-pending-review" for entry in entries)
            else state
        )
        inspection, inspection_sources = (
            _private_xcresult_inspection_capabilities(
                bundle, private_root, decode_deadline
            )
            if collection_state == "quarantined-pending-review" and decode_deadline is not None
            else ({}, [])
        )
        sources.extend(inspection_sources)
        if inspection_sources:
            entries = _private_record_entries(sources, state, allow_quarantine=True)
        commands = {
            "xcodebuild-test": unit.get("executedCommand"),
            "xcresult-summary": unit.get("summaryCommand"),
            "xcresult-attachment-export": unit.get("attachmentExportCommand"),
        }
        probe_commands = unit.get("probeCommands")
        if isinstance(probe_commands, dict):
            commands.update(probe_commands)
        if inspection:
            commands["private-inspection"] = inspection
        inventory = _write_private_json(private_root, "collection-inventory.json", {
            "candidateCommit": commit,
            "buildId": _build_id(),
            "workflow": NATIVE_CYCLE_WORKFLOW,
            "collectionState": collection_state,
            "testSelector": NATIVE_CYCLE_TEST_SELECTOR,
            "processExit": unit.get("processExit"),
            "actualCounts": unit.get("actualCounts"),
            "failureStatus": unit.get("testFailureStatus"),
            "commands": commands,
            "records": entries,
        })
        inventory_source = (inventory, "records/collection-inventory.json", "collection-inventory")
        inventory_entry = _private_record_entries([inventory_source], state)
        _write_private_archive(
            private_root,
            [*sources, inventory_source],
            [*entries, *inventory_entry],
            allow_quarantine=True,
        )
        return collection_state
    except PrivateRecordCollectionError as error:
        if (
            error.sensitive_matcher == "credential-prefix"
            and error.private_candidate is not None
            and decode_deadline is not None
        ):
            unit["privateDecodeDiagnostic"] = _private_decode_result_bundle(
                bundle, error.private_candidate, error.private_record_identity, decode_deadline
            )
        if error.diagnostic is not None:
            unit["privateRecordCollectionDiagnostic"] = error.diagnostic
        return str(error)


def unit_settings_main() -> int:
    """Run one non-accepting unit diagnostic against an existing simulator."""

    if UNIT_ALLOCATED_SECONDS != 266 or UNIT_ALLOCATED_SECONDS >= 270:
        raise RuntimeError("unit diagnostic time budget is invalid")
    deadline = time.monotonic() + UNIT_WORKFLOW_SECONDS
    try:
        commit = context()
        rt._live_artifact_root(ROOT)
        rt._live_artifact_root(SAFE_ROOT)
    except (OSError, ValueError):
        print("diagnostic setup rejected; no test started", flush=True)
        return 1
    report: dict[str, object] = {
        "scope": "one-core-unit-settings-diagnostic", "diagnosticMode": UNIT_SETTINGS_MODE,
        "workflow": WORKFLOW, "branch": rt.LIVE_BRANCH, "device": rt.IOS_CORE_DEVICE,
        "releaseEvidence": False, "diagnosticStatus": "started",
        "intentionalNonZeroExit": True, "commit": commit, "results": {},
    }
    build_id = _build_id()
    if build_id is not None:
        report["buildId"] = build_id
    try:
        publish(report, deadline)
    except OSError:
        print("diagnostic setup rejected; no test started", flush=True)
        return 1
    try:
        destination = _existing_core_destination()
    except (rt.SimulatorResolutionError, OSError, ValueError) as error:
        report["diagnosticStatus"] = "setup-failed"
        report["results"] = {"setup": {
            "phase": "simulator-readiness",
            "reason": (
                "timeout"
                if getattr(error, "reason", None) == rt.SIMULATOR_RESOLUTION_TIMEOUT_REASON
                else "resolution-failed"
            ),
        }}
        _publish_unit_report(report, deadline)
        print("diagnostic setup rejected; no test started", flush=True)
        return 1
    identifier = _simulator_identifier(destination)
    if identifier is None:
        return 1
    probes = {
        "uiSyntax": _bounded_ui_syntax_probe(identifier),
        "settings": _bounded_unit_settings_probes(identifier),
    }
    report["results"] = {"simulatorProbes": probes}
    if not _publish_unit_report(report, deadline):
        return 1
    bundle = ROOT / "unit.xcresult"
    unit_log = ROOT / "unit.log"
    unit: dict[str, object] = run(
        ["xcodebuild", "test", "-project", "ACEClientApp.xcodeproj", "-scheme", "ACEClientApp", "-destination", destination, "-parallel-testing-enabled", "NO", f"-only-testing:{UNIT_TEST_TARGET}", "-resultBundlePath", str(bundle)],
        rt.ios_test_environment(), unit_log, UNIT_XCODEBUILD_SECONDS,
    )
    unit.update({"commandKind": "xcodebuild-test", "target": UNIT_TEST_TARGET,
                 "expectedTestCount": UNIT_EXPECTED_TEST_COUNT, "device": rt.IOS_CORE_DEVICE})
    if type(unit.get("processExit")) is int and unit["processExit"] != 0:
        unit["logErrorLines"] = errors(unit_log)
    report["results"] = {"simulatorProbes": probes, "unit": unit}
    if not _publish_unit_report(report, deadline):
        return 1
    _collect_unit_summary(unit, bundle)
    actual = unit.get("actualCounts")
    unit["status"] = "passed" if (
        unit.get("processExit") == 0
        and actual == {"passed": UNIT_EXPECTED_TEST_COUNT, "failed": 0, "skipped": 0}
    ) else "failed"
    report["diagnosticStatus"] = "completed-not-release-evidence"
    if not _publish_unit_report(report, deadline):
        return 1
    return 1


def native_cycle_main() -> int:
    """Run one selected native test and retain private original records."""

    if (
        NATIVE_CYCLE_ALLOCATED_SECONDS >= NATIVE_CYCLE_WORKFLOW_SECONDS
        or NATIVE_CYCLE_WORKFLOW_SECONDS != 480
    ):
        raise RuntimeError("native-cycle time budget is invalid")
    deadline = time.monotonic() + NATIVE_CYCLE_WORKFLOW_SECONDS
    try:
        commit = context(NATIVE_CYCLE_WORKFLOW)
        rt._live_artifact_root(ROOT)
        rt._live_artifact_root(SAFE_ROOT)
    except (OSError, ValueError):
        print("diagnostic setup rejected; no test started", flush=True)
        return 1
    report: dict[str, object] = {
        "scope": "one-native-cycle-unit-test",
        "diagnosticMode": NATIVE_CYCLE_MODE,
        "workflow": NATIVE_CYCLE_WORKFLOW,
        "branch": rt.LIVE_BRANCH,
        "device": rt.IOS_CORE_DEVICE,
        "releaseEvidence": False,
        "diagnosticStatus": "started",
        "commit": commit,
        "results": {},
    }
    build_id = _build_id()
    if build_id is not None:
        report["buildId"] = build_id
    try:
        publish(report, deadline)
    except OSError:
        print("diagnostic setup rejected; no test started", flush=True)
        return 1
    try:
        destination = _native_cycle_destination()
    except (rt.SimulatorResolutionError, OSError, ValueError) as error:
        report["diagnosticStatus"] = "setup-failed"
        report["results"] = {"setup": {
            "phase": "simulator-readiness",
            "reason": (
                "timeout"
                if getattr(error, "reason", None) == rt.SIMULATOR_RESOLUTION_TIMEOUT_REASON
                else "resolution-failed"
            ),
        }}
        _publish_unit_report(report, deadline)
        return 1
    identifier = _simulator_identifier(destination)
    if identifier is None:
        return 1
    probes = {
        "uiSyntax": _bounded_ui_syntax_probe(identifier),
        "settings": _bounded_unit_settings_probes(identifier),
    }
    report["results"] = {"simulatorProbes": probes}
    if not _publish_unit_report(report, deadline):
        return 1
    bundle = ROOT / "unit.xcresult"
    unit_log = ROOT / "unit.log"
    command = [
        "xcodebuild", "test", "-project", "ACEClientApp.xcodeproj", "-scheme", "ACEClientApp",
        "-destination", destination, "-parallel-testing-enabled", "NO",
        f"-only-testing:{NATIVE_CYCLE_TEST_SELECTOR}", "-resultBundlePath", str(bundle),
    ]
    unit: dict[str, object] = run(
        command,
        rt.ios_test_environment(), unit_log, UNIT_XCODEBUILD_SECONDS,
    )
    unit.update({
        "commandKind": "xcodebuild-test",
        "selector": NATIVE_CYCLE_TEST_SELECTOR,
        "expectedTestCount": NATIVE_CYCLE_EXPECTED_TEST_COUNT,
        "device": rt.IOS_CORE_DEVICE,
        "resolvedDestination": destination,
        "executedCommand": command,
        "probeCommands": {
            "simctl-help-ui": {"executedCommand": ["xcrun", "simctl", "help", "ui"]},
            "simctl-ui-appearance-query": {
                "executedCommand": ["xcrun", "simctl", "ui", identifier, "appearance"],
            },
            "simctl-ui-content_size-query": {
                "executedCommand": ["xcrun", "simctl", "ui", identifier, "content_size"],
            },
        },
    })
    if type(unit.get("processExit")) is int and unit["processExit"] != 0:
        unit["logErrorLines"] = errors(unit_log)
    report["results"] = {"simulatorProbes": probes, "unit": unit}
    if not _publish_unit_report(report, deadline):
        return 1
    _collect_unit_summary(unit, bundle)
    if isinstance(unit.get("summaryCommand"), dict):
        unit["summaryCommand"]["executedCommand"] = [
            "xcrun", "xcresulttool", "get", "test-results", "summary", "--path", str(bundle),
        ]
    actual = unit.get("actualCounts")
    unit["status"] = "passed" if (
        unit.get("processExit") == 0
        and actual == {"passed": NATIVE_CYCLE_EXPECTED_TEST_COUNT, "failed": 0, "skipped": 0}
    ) else "failed"
    collection = (
        "collection-time-reserve-exhausted"
        if time.monotonic() + NATIVE_CYCLE_ATTACHMENT_SECONDS + NATIVE_CYCLE_PACKAGING_SECONDS + NATIVE_CYCLE_DECODER_SECONDS + UNIT_PUBLICATION_SECONDS >= deadline
        else _collect_native_cycle_records(
            commit, unit, bundle,
            deadline - NATIVE_CYCLE_PACKAGING_SECONDS - UNIT_PUBLICATION_SECONDS,
        )
    )
    unit["privateRecordCollection"] = collection
    report["diagnosticStatus"] = "completed-not-release-evidence"
    if not _publish_unit_report(report, deadline):
        return 1
    return 0 if unit["status"] == "passed" and collection == "complete" else 1


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


def _publish_unit_report(report: dict, deadline: float) -> bool:
    """Publish the latest partial unit report before its fixed deadline."""

    try:
        publish(report, deadline)
    except OSError:
        print("diagnostic publication stopped; previous report retained", flush=True)
        return False
    return True


def publish(report: dict, deadline: float | None = None) -> None:
    """Atomically publish one report within an optional fixed deadline."""

    if deadline is not None and time.monotonic() >= deadline:
        raise OSError("diagnostic publication time expired")
    content = json.dumps(report, indent=2, sort_keys=True)
    target = SAFE_ROOT / "diagnostic.json"
    temporary = SAFE_ROOT / ".diagnostic.json.tmp"
    if temporary.exists() or temporary.is_symlink():
        raise OSError("diagnostic publication staging path is unavailable")
    temporary.write_text(content + "\n", encoding="utf-8")
    if deadline is not None and time.monotonic() >= deadline:
        temporary.unlink(missing_ok=True)
        raise OSError("diagnostic publication time expired")
    os.replace(temporary, target)
    print(content, flush=True)


def copy_controls_main() -> int:
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
        destination = rt.resolve_ios_destinations((rt.IOS_CORE_DEVICE,), allow_create=True)[rt.IOS_CORE_DEVICE]
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
        ["xcodebuild", "test", "-project", "ACEClientApp.xcodeproj", "-scheme", "ACEClientAppUITests", "-configuration", "Debug", "-destination", destination, "-parallel-testing-enabled", "NO", f"-only-testing:{METHOD_PATH}", "-resultBundlePath", str(bundle), "ACE_UI_TEST_APPEARANCE=light"],
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


def main() -> int:
    """Select one explicit non-accepting diagnostic mode."""

    try:
        mode = diagnostic_mode()
    except ValueError:
        print("diagnostic setup rejected; no test started", flush=True)
        return 1
    if mode == UNIT_SETTINGS_MODE:
        return unit_settings_main()
    if mode == NATIVE_CYCLE_MODE:
        return native_cycle_main()
    return copy_controls_main()


if __name__ == "__main__":
    raise SystemExit(main())
