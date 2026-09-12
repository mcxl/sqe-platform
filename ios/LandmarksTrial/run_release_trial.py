#!/usr/bin/env python3
"""Run the bounded manual ACE Apple Landmarks release trial."""
from __future__ import annotations
import argparse
import hashlib
import json
import os
import pathlib
import queue
import re
import shutil
import signal
import stat
import subprocess
import sys
import threading
import time
import traceback
import urllib.request
import zipfile
ARCHIVE_URL = "https://docs-assets.developer.apple.com/published/a88428e6793e/LandmarksBuildingAnAppWithLiquidGlass.zip"
ARCHIVE_SHA256 = "F19ED0EFFBE8AF975536034B2B5AF98002F06F5D600854A95EFB62CCC8303F41"
ARCHIVE_SIZE = 336053876
ROOT = pathlib.Path("/private/tmp/ace-landmarks-release-trial")
APP_RELATIVE = pathlib.Path("Build/Products/Debug-iphonesimulator/Landmarks.app")
TEST_TARGET = "LandmarksTrialUITests"
FOCUSED_TEST = f"{TEST_TARGET}/{TEST_TARGET}/testReleaseInformationAndCopyControls"
MATRIX_TEST = f"{TEST_TARGET}/{TEST_TARGET}/testReleaseLayoutAndAccessibility"
DIAGNOSTIC_TEST = f"{TEST_TARGET}/{TEST_TARGET}/testReleaseAuditDiagnostic"
CLIPBOARD_BRIDGE_TEST = f"{TEST_TARGET}/{TEST_TARGET}/testReleaseClipboardBridge"
FOCUSED_COPY_VALUES = (
    "Fictional Engagement", "RELEASED", "1", "2026-08-24T10:15:30Z",
    "Fictional conclusion", "Fictional summary", "FICTIONAL-REF-001",
    "Fictional action", "Fictional owner", "2026-08-25", "OPEN",
)
CLIPBOARD_SENTINEL = "ACE-CLIPBOARD-SENTINEL-20260912"
ALLOWED_OVERLAY_PATHS = frozenset(("Landmarks/Landmarks.xcodeproj/project.pbxproj", "Landmarks/Landmarks.xcodeproj/xcshareddata/xcschemes/LandmarksTrial.xcscheme", "Landmarks/LandmarksTrialUITests/LandmarksTrialUITests.swift", "Landmarks/Landmarks/LandmarksApp.swift", "Landmarks/Landmarks/ReleaseDetailData.swift", "Landmarks/Landmarks/ReleaseDetailView.swift", "Landmarks/Landmarks/ReleaseModels.swift"))
MODE = {
    "focused": {"work_seconds": 270, "final_seconds": 330, "test": FOCUSED_TEST, "devices": ("iPhone 17",), "contexts": (("light", "large"),)},
    "matrix": {"work_seconds": 510, "final_seconds": 570, "test": MATRIX_TEST, "devices": ("iPhone 17", "iPhone 17 Pro Max"), "contexts": (("light", "large"), ("light", "extra-large"), ("light", "accessibility-extra-extra-extra-large"), ("dark", "large"), ("dark", "extra-large"), ("dark", "accessibility-extra-extra-extra-large"))},
    "pilot": {"work_seconds": 600, "final_seconds": 660, "test_seconds": 480, "test": MATRIX_TEST, "devices": ("iPhone 17",), "contexts": (("dark", "accessibility-extra-extra-extra-large"),)},
    "diagnostic": {"work_seconds": 360, "final_seconds": 420, "test_seconds": 240, "test": DIAGNOSTIC_TEST, "devices": ("iPhone 17",), "contexts": (("light", "large"),)},
    "clipboard": {"work_seconds": 480, "final_seconds": 540, "test_seconds": 390, "test": CLIPBOARD_BRIDGE_TEST, "devices": ("iPhone 17",), "contexts": (("light", "large"),)},
}


def validate_clipboard_transitions(samples: list[dict[str, object]]) -> dict[str, object]:
    transitions: list[str] = []
    last = CLIPBOARD_SENTINEL
    for sample in samples:
        payload = sample.get("payload")
        if sample.get("exit") != 0 or not isinstance(payload, str):
            return {"passed": False, "expected": list(FOCUSED_COPY_VALUES), "actual": transitions,
                    "error": "Clipboard collector command did not return a payload"}
        if payload == last:
            continue
        if payload == CLIPBOARD_SENTINEL or payload in transitions:
            expected = FOCUSED_COPY_VALUES[len(transitions)] if len(transitions) < len(FOCUSED_COPY_VALUES) else None
            return {"passed": False, "expected": expected, "actual": payload, "observed_transitions": transitions,
                    "error": f"Clipboard returned an earlier value: {payload}"}
        expected = FOCUSED_COPY_VALUES[len(transitions)] if len(transitions) < len(FOCUSED_COPY_VALUES) else None
        if payload != expected:
            return {"passed": False, "expected": expected, "actual": payload,
                    "error": "Clipboard transition did not match the expected order"}
        transitions.append(payload)
        last = payload
    if tuple(transitions) != FOCUSED_COPY_VALUES:
        expected = FOCUSED_COPY_VALUES[len(transitions)] if len(transitions) < len(FOCUSED_COPY_VALUES) else None
        return {"passed": False, "expected": expected, "actual": transitions,
                "error": "Clipboard collector did not observe all expected values"}
    return {"passed": True, "expected": list(FOCUSED_COPY_VALUES), "actual": transitions}


class ClipboardBridgeRecorder:
    """Record one host pasteboard read for each XCTest bridge marker."""

    def __init__(self, reader) -> None:
        self.reader = reader
        self.records: list[dict[str, object]] = []
        self.reads_stopped = False

    def record_marker(self, index: int, seen_at_epoch: float) -> None:
        record: dict[str, object] = {
            "marker_index": index,
            "marker_seen_at_epoch": seen_at_epoch,
        }
        expected_index = len(self.records)
        if self.reads_stopped:
            record["read_status"] = "skipped_after_failure"
        elif index < 0 or index >= len(FOCUSED_COPY_VALUES):
            record["error"] = f"Clipboard bridge marker index {index} is out of range"
            self.reads_stopped = True
        elif index != expected_index:
            record["error"] = f"Unexpected clipboard bridge marker {index}; expected {expected_index}"
            self.reads_stopped = True
        else:
            expected = FOCUSED_COPY_VALUES[index]
            record["expected_payload"] = expected
            try:
                observation = self.reader(index)
            except Exception as error:
                observation = {"exit": None, "payload": None, "runner_error": str(error)}
            record["observation"] = observation
            if observation.get("timed_out"):
                record["error"] = "Host clipboard read timed out"
                self.reads_stopped = True
            elif observation.get("exit") != 0:
                record["error"] = "Host clipboard read returned a non-zero exit code"
                self.reads_stopped = True
            elif observation.get("payload") != expected:
                record["error"] = "Host clipboard payload did not match the approved value"
                self.reads_stopped = True
        self.records.append(record)

    def validation(self) -> dict[str, object]:
        marker_indexes = [record.get("marker_index") for record in self.records]
        expected_indexes = list(range(len(FOCUSED_COPY_VALUES)))
        payloads = [
            record.get("observation", {}).get("payload") if isinstance(record.get("observation"), dict) else None
            for record in self.records
        ]
        if marker_indexes != expected_indexes:
            return {
                "passed": False,
                "expected_marker_indexes": expected_indexes,
                "actual_marker_indexes": marker_indexes,
                "actual_payloads": payloads,
                "error": "Clipboard bridge markers were incomplete or out of order",
            }
        for position, record in enumerate(self.records):
            if record.get("error"):
                return {
                    "passed": False,
                    "expected": list(FOCUSED_COPY_VALUES),
                    "actual": payloads,
                    "error": record["error"],
                }
            observation = record.get("observation")
            if not isinstance(observation, dict):
                return {"passed": False, "expected": list(FOCUSED_COPY_VALUES), "actual": payloads,
                        "error": "Clipboard bridge marker had no host observation"}
            started = observation.get("started_at_epoch")
            finished = observation.get("finished_at_epoch")
            marker = record.get("marker_seen_at_epoch")
            if not isinstance(marker, (int, float)) or not isinstance(started, (int, float)) or not isinstance(finished, (int, float)):
                return {"passed": False, "expected": list(FOCUSED_COPY_VALUES), "actual": payloads,
                        "error": "Clipboard bridge observation did not retain timing evidence"}
            if started < marker:
                return {"passed": False, "expected": list(FOCUSED_COPY_VALUES), "actual": payloads,
                        "error": "Host clipboard read started before its bridge marker"}
            if finished < started:
                return {"passed": False, "expected": list(FOCUSED_COPY_VALUES), "actual": payloads,
                        "error": "Host clipboard read finished before it started"}
            if position + 1 < len(self.records):
                next_marker = self.records[position + 1].get("marker_seen_at_epoch")
                if not isinstance(next_marker, (int, float)) or finished >= next_marker:
                    return {"passed": False, "expected": list(FOCUSED_COPY_VALUES), "actual": payloads,
                            "error": "Host clipboard read did not finish before the next bridge marker"}
        return {"passed": True, "expected": list(FOCUSED_COPY_VALUES), "actual": payloads}


class Trial:
    def __init__(self, mode: str) -> None:
        self.mode = mode
        self.settings = MODE[mode]
        self.started = time.time()
        self.started_monotonic = time.monotonic()
        self.work_deadline = self.started_monotonic + self.settings["work_seconds"]
        self.final_deadline = self.started_monotonic + self.settings["final_seconds"]
        self.root = ROOT / mode
        self.source = self.root / "source"
        self.build = self.root / "build"
        self.evidence = self.root / "evidence"
        self.archive = self.root / "LandmarksBuildingAnAppWithLiquidGlass.zip"
        self.raw_log = self.evidence / "raw.log"
        self.commands: list[dict[str, object]] = []
        self.command_lock = threading.Lock()
        self.outcome: dict[str, object] = {"mode": mode, "result": "runner_failure", "cm_commit": os.environ.get("CM_COMMIT"), "cm_build_id": os.environ.get("CM_BUILD_ID"), "started_at_epoch": self.started}
    def write_text(self, path: pathlib.Path, text: str) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    def remaining(self, limit: int) -> int:
        left = self.work_deadline - time.monotonic()
        if left <= 0:
            raise RuntimeError(f"The {self.settings['work_seconds']}-second work budget expired")
        return min(limit, max(1, int(left)))
    def final_remaining(self, limit: int) -> int:
        left = self.final_deadline - time.monotonic()
        if left <= 0:
            raise RuntimeError(f"The {self.settings['final_seconds']}-second finalisation budget expired")
        return min(limit, max(1, int(left)))
    @staticmethod
    def stop_process_group(process: subprocess.Popen[str]) -> tuple[str, dict[str, str]]:
        cleanup: dict[str, str] = {}
        try:
            killpg = getattr(os, "killpg", None)
            if killpg is None:
                raise PermissionError("os.killpg is unavailable")
            killpg(process.pid, signal.SIGTERM)
        except ProcessLookupError:
            pass
        except PermissionError as error:
            cleanup["process_group_terminate_error"] = str(error)
            try:
                process.terminate()
            except ProcessLookupError:
                pass
            except OSError as direct_error:
                cleanup["direct_terminate_error"] = str(direct_error)
        try:
            return process.communicate(timeout=5)[0], cleanup
        except subprocess.TimeoutExpired:
            try:
                killpg = getattr(os, "killpg", None)
                if killpg is None:
                    raise PermissionError("os.killpg is unavailable")
                killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            except PermissionError as error:
                cleanup["process_group_kill_error"] = str(error)
                try:
                    process.kill()
                except ProcessLookupError:
                    pass
                except OSError as direct_error:
                    cleanup["direct_kill_error"] = str(direct_error)
            try:
                return process.communicate(timeout=5)[0], cleanup
            except subprocess.TimeoutExpired:
                cleanup["cleanup_error"] = "Process did not exit after direct cleanup"
                return "", cleanup
    def run(self, command: list[str], limit: int, *, allow_failure: bool = False, cwd: pathlib.Path | None = None, final: bool = False, input_text: str | None = None) -> tuple[str, int]:
        budget = self.final_remaining if final else self.remaining
        event: dict[str, object] = {"command": command, "started_at_epoch": time.time(), "limit_seconds": budget(limit)}
        output = ""
        process: subprocess.Popen[str] | None = None
        try:
            process = subprocess.Popen(
                command,
                cwd=cwd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                stdin=subprocess.PIPE if input_text is not None else None,
                text=True,
                start_new_session=True,
            )
            try:
                output, _ = process.communicate(input=input_text, timeout=event["limit_seconds"])
            except subprocess.TimeoutExpired:
                output, cleanup = self.stop_process_group(process)
                event["timed_out"] = True
                if cleanup:
                    event["cleanup"] = cleanup
                raise RuntimeError(f"Timed out after {event['limit_seconds']} seconds: {command[0]}")
            if process.returncode and not allow_failure:
                raise RuntimeError(f"Command failed ({process.returncode}) {' '.join(command)}")
            return output, process.returncode
        finally:
            with self.command_lock:
                self.raw_log.parent.mkdir(parents=True, exist_ok=True)
                with self.raw_log.open("a", encoding="utf-8") as log:
                    log.write("$ " + " ".join(command) + "\n" + output)
                event["finished_at_epoch"] = time.time()
                event["duration_seconds"] = round(event["finished_at_epoch"] - event["started_at_epoch"], 2)
                event["exit_code"] = process.returncode if process else None
                self.commands.append(event)
    def sha256(self, path: pathlib.Path, *, final: bool = False) -> str:
        budget = self.final_remaining if final else self.remaining
        digest = hashlib.sha256()
        with path.open("rb") as source:
            for block in iter(lambda: source.read(1024 * 1024), b""):
                budget(30)
                digest.update(block)
        return digest.hexdigest().upper()
    def tree_hashes(self, directory: pathlib.Path, *, final: bool = False) -> str:
        lines: list[str] = []
        for path in sorted(directory.rglob("*")):
            relative = path.relative_to(directory)
            if ".git" in relative.parts or not path.is_file():
                continue
            lines.append(f"{self.sha256(path, final=final)}  {relative.as_posix()}")
        return "\n".join(lines) + "\n"
    @staticmethod
    def hash_map(contents: str) -> dict[str, str]:
        return {line.split("  ", 1)[1]: line.split("  ", 1)[0] for line in contents.splitlines()}
    @staticmethod
    def difference(before: dict[str, str], after: dict[str, str]) -> list[dict[str, str | None]]:
        return [{"path": name, "before_sha256": before.get(name), "after_sha256": after.get(name)} for name in sorted(set(before) | set(after)) if before.get(name) != after.get(name)]
    def safe_extract(self) -> None:
        total = 0
        with zipfile.ZipFile(self.archive) as zipped:
            for member in zipped.infolist():
                self.remaining(30)
                candidate = pathlib.PurePosixPath(member.filename)
                mode = member.external_attr >> 16
                if candidate.is_absolute() or ".." in candidate.parts or stat.S_ISLNK(mode):
                    raise RuntimeError(f"Unsafe archive member: {member.filename}")
                total += member.file_size
                if total > 1_000_000_000:
                    raise RuntimeError("Archive expanded past the one-gigabyte safety limit")
                destination = self.source.joinpath(*candidate.parts)
                if member.is_dir():
                    destination.mkdir(parents=True, exist_ok=True)
                    continue
                destination.parent.mkdir(parents=True, exist_ok=True)
                with zipped.open(member) as input_file, destination.open("wb") as output_file:
                    while block := input_file.read(1024 * 1024):
                        self.remaining(30)
                        output_file.write(block)
    @staticmethod
    def dictionaries(value: object):
        if isinstance(value, dict):
            yield value
            for child in value.values():
                yield from Trial.dictionaries(child)
        elif isinstance(value, list):
            for child in value:
                yield from Trial.dictionaries(child)
    def download_and_overlay(self, repo: pathlib.Path) -> tuple[pathlib.Path, pathlib.Path]:
        harness = repo / "ios" / "LandmarksTrial"
        scheme = harness / "LandmarksTrial.xcscheme"
        test = harness / "LandmarksTrialUITests" / "LandmarksTrialUITests.swift"
        overlay = harness / "overlay_landmarks_project.py"
        ace_test = harness / "ACEReleaseUITests.swift"
        for required in (scheme, test, ace_test, overlay):
            if not required.is_file():
                raise RuntimeError(f"Missing release trial harness input: {required}")
        with urllib.request.urlopen(ARCHIVE_URL, timeout=self.remaining(30)) as response, self.archive.open("wb") as output:
            download_deadline = time.monotonic() + self.remaining(90)
            while block := response.read(1024 * 1024):
                if time.monotonic() > download_deadline:
                    raise RuntimeError("Approved source download exceeded 90 seconds")
                output.write(block)
        if self.archive.stat().st_size != ARCHIVE_SIZE:
            raise RuntimeError("Approved source archive size did not match")
        observed_archive_hash = self.sha256(self.archive)
        if observed_archive_hash != ARCHIVE_SHA256:
            raise RuntimeError("Approved source archive SHA-256 did not match")
        self.safe_extract()
        project = self.source / "Landmarks" / "Landmarks.xcodeproj"
        derived_root = self.source / "Landmarks"
        if not project.is_dir() or not derived_root.is_dir():
            raise RuntimeError("Approved archive did not contain Landmarks/Landmarks.xcodeproj")
        baseline = self.tree_hashes(self.source)
        self.write_text(self.evidence / "source-hashes-before-overlay.txt", baseline)
        test_destination = derived_root / "LandmarksTrialUITests" / "LandmarksTrialUITests.swift"
        scheme_destination = project / "xcshareddata" / "xcschemes" / "LandmarksTrial.xcscheme"
        test_destination.parent.mkdir(parents=True, exist_ok=True)
        scheme_destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(test, test_destination)
        shutil.copy2(scheme, scheme_destination)
        overlay_output, _ = self.run([sys.executable, str(overlay), str(project), "--ace"], 30, cwd=repo)
        self.write_text(self.evidence / "overlay.log", overlay_output)
        manifest_lines = [line for line in overlay_output.splitlines() if line.startswith("ACE_RELEASE_OVERLAY_MANIFEST=")]
        if len(manifest_lines) != 1:
            raise RuntimeError("ACE overlay did not return exactly one manifest line")
        try:
            overlay_manifest = json.loads(manifest_lines[0].split("=", 1)[1])
        except json.JSONDecodeError as error:
            raise RuntimeError("ACE overlay returned an invalid manifest") from error
        self.write_text(self.evidence / "overlay-manifest.json", json.dumps(overlay_manifest, indent=2) + "\n")
        changed = self.difference(self.hash_map(baseline), self.hash_map(self.tree_hashes(self.source)))
        changed_paths = {item["path"] for item in changed}
        if changed_paths != ALLOWED_OVERLAY_PATHS:
            raise RuntimeError("The ACE overlay did not make exactly the approved release trial changes")
        self.write_text(self.evidence / "overlay-diff.json", json.dumps(changed, indent=2) + "\n")
        self.write_text(self.evidence / "source-hashes-before-test.txt", self.tree_hashes(self.source))
        self.outcome["source_archive"] = {
            "url": ARCHIVE_URL,
            "expected_size_bytes": ARCHIVE_SIZE,
            "observed_size_bytes": self.archive.stat().st_size,
            "expected_sha256": ARCHIVE_SHA256,
            "observed_sha256": observed_archive_hash,
        }
        self.outcome["overlay_differences"] = changed
        return project, derived_root
    def simulator(self, name: str, devices: dict[str, list[dict[str, object]]]) -> tuple[str, str]:
        candidates: list[tuple[str, dict[str, object]]] = []
        for runtime, entries in devices.items():
            if "iOS-26-4" not in runtime:
                continue
            for device in entries:
                if device.get("isAvailable") and device.get("name") == name:
                    candidates.append((runtime, device))
        if not candidates:
            raise RuntimeError(f"No available {name} simulator with the approved iOS 26.4 runtime")
        runtime, device = sorted(candidates, key=lambda entry: (entry[0], str(entry[1].get("udid"))), reverse=True)[0]
        udid = str(device["udid"])
        state = device.get("state")
        if state == "Shutdown":
            self.run(["xcrun", "simctl", "boot", udid], 45)
        elif state != "Booted":
            raise RuntimeError(f"Selected {name} simulator was not Shutdown or Booted")
        self.run(["xcrun", "simctl", "bootstatus", udid, "-b"], 90)
        return runtime, udid
    def simctl_ui(self, udid: str, setting: str, value: str | None = None, *, final: bool = False) -> str:
        command = ["xcrun", "simctl", "ui", udid, setting]
        if value is not None:
            command.append(value)
        output, _ = self.run(command, 15, final=final)
        observed = output.strip().lower()
        if value is None:
            if setting == "appearance" and observed not in {"light", "dark"}:
                raise RuntimeError(f"Simulator returned an invalid appearance: {observed!r}")
            if setting == "content_size" and observed not in {
                "large", "extra-large", "accessibility-extra-extra-extra-large"
            }:
                raise RuntimeError(f"Simulator returned an invalid content size: {observed!r}")
        return observed

    def reset_focused_clipboard(self, udid: str) -> dict[str, object]:
        _, copy_exit = self.run(["xcrun", "simctl", "pbcopy", udid], 10, allow_failure=True,
                                input_text=CLIPBOARD_SENTINEL)
        payload, paste_exit = self.run(["xcrun", "simctl", "pbpaste", udid], 10, allow_failure=True)
        record = {"requested": CLIPBOARD_SENTINEL, "pbcopy_exit": copy_exit,
                  "pbpaste_exit": paste_exit, "observed": payload}
        if copy_exit != 0 or paste_exit != 0 or record["observed"] != CLIPBOARD_SENTINEL:
            raise RuntimeError("Could not reset and verify the focused simulator pasteboard")
        return record

    def start_clipboard_collector(self, udid: str) -> tuple[threading.Event, threading.Thread, list[dict[str, object]]]:
        stop = threading.Event()
        samples: list[dict[str, object]] = []

        def collect() -> None:
            while not stop.is_set():
                sample: dict[str, object] = {"started_at_epoch": time.time()}
                try:
                    payload, exit_code = self.run(["xcrun", "simctl", "pbpaste", udid], 5, allow_failure=True)
                    sample.update({"exit": exit_code, "payload": payload})
                except Exception as error:
                    sample.update({"exit": None, "payload": None, "error": str(error)})
                    samples.append(sample)
                    return
                finally:
                    sample["finished_at_epoch"] = time.time()
                    sample["duration_seconds"] = round(sample["finished_at_epoch"] - sample["started_at_epoch"], 3)
                samples.append(sample)
                stop.wait(0.1)

        thread = threading.Thread(target=collect, name="focused-clipboard-collector", daemon=True)
        thread.start()
        return stop, thread, samples

    def append_raw_log(self, text: str) -> None:
        with self.command_lock:
            self.raw_log.parent.mkdir(parents=True, exist_ok=True)
            with self.raw_log.open("a", encoding="utf-8") as log:
                log.write(text)

    @staticmethod
    def stop_streamed_process(process: subprocess.Popen[str]) -> dict[str, str]:
        cleanup: dict[str, str] = {}
        try:
            killpg = getattr(os, "killpg", None)
            if killpg is None:
                raise PermissionError("os.killpg is unavailable")
            killpg(process.pid, signal.SIGTERM)
        except ProcessLookupError:
            pass
        except PermissionError as error:
            cleanup["process_group_terminate_error"] = str(error)
            try:
                process.terminate()
            except ProcessLookupError:
                pass
            except OSError as direct_error:
                cleanup["direct_terminate_error"] = str(direct_error)
        try:
            process.wait(timeout=5)
            return cleanup
        except subprocess.TimeoutExpired:
            try:
                killpg = getattr(os, "killpg", None)
                if killpg is None:
                    raise PermissionError("os.killpg is unavailable")
                killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            except PermissionError as error:
                cleanup["process_group_kill_error"] = str(error)
                try:
                    process.kill()
                except ProcessLookupError:
                    pass
                except OSError as direct_error:
                    cleanup["direct_kill_error"] = str(direct_error)
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                cleanup["cleanup_error"] = "Process did not exit after direct cleanup"
            return cleanup

    def run_bridge_paste(self, udid: str) -> dict[str, object]:
        command = ["xcrun", "simctl", "pbpaste", udid]
        event: dict[str, object] = {
            "command": command,
            "started_at_epoch": time.time(),
            "limit_seconds": self.remaining(5),
        }
        observation: dict[str, object] = {
            "started_at_epoch": event["started_at_epoch"],
            "timed_out": False,
        }
        output = ""
        process: subprocess.Popen[str] | None = None
        try:
            process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                start_new_session=True,
            )
            try:
                output, _ = process.communicate(timeout=event["limit_seconds"])
            except subprocess.TimeoutExpired:
                output, cleanup = self.stop_process_group(process)
                observation["timed_out"] = True
                event["timed_out"] = True
                if cleanup:
                    observation["cleanup"] = cleanup
                    event["cleanup"] = cleanup
            observation["exit"] = process.returncode
            observation["payload"] = output
        except Exception as error:
            observation["exit"] = None
            observation["payload"] = None
            observation["runner_error"] = str(error)
        finally:
            observation["finished_at_epoch"] = time.time()
            observation["duration_seconds"] = round(
                observation["finished_at_epoch"] - observation["started_at_epoch"], 3
            )
            event["finished_at_epoch"] = observation["finished_at_epoch"]
            event["duration_seconds"] = observation["duration_seconds"]
            event["exit_code"] = process.returncode if process else None
            with self.command_lock:
                self.raw_log.parent.mkdir(parents=True, exist_ok=True)
                with self.raw_log.open("a", encoding="utf-8") as log:
                    log.write("$ " + " ".join(command) + "\n" + output)
                self.commands.append(event)
        return observation

    def run_streamed(self, command: list[str], limit: int, on_line, *, cwd: pathlib.Path | None = None) -> dict[str, object]:
        event: dict[str, object] = {
            "command": command,
            "started_at_epoch": time.time(),
            "limit_seconds": self.remaining(limit),
        }
        output: list[str] = []
        callback_errors: list[str] = []
        stream_queue: queue.Queue[tuple[str, float] | None] = queue.Queue()
        process: subprocess.Popen[str] | None = None
        reader: threading.Thread | None = None
        timed_out = False
        drain_deadline: float | None = None

        def drain(stdout) -> None:
            try:
                for line in stdout:
                    received_at_epoch = time.time()
                    self.append_raw_log(line)
                    stream_queue.put((line, received_at_epoch))
            finally:
                stream_queue.put(None)

        try:
            process = subprocess.Popen(
                command,
                cwd=cwd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                start_new_session=True,
            )
            if process.stdout is None:
                raise RuntimeError("Could not read streamed command output")
            self.append_raw_log("$ " + " ".join(command) + "\n")
            reader = threading.Thread(target=drain, args=(process.stdout,), name="clipboard-bridge-stream", daemon=True)
            reader.start()
            deadline = time.monotonic() + event["limit_seconds"]
            stream_closed = False
            while not stream_closed:
                if not timed_out and time.monotonic() >= deadline:
                    timed_out = True
                    drain_deadline = time.monotonic() + 10
                    event["timed_out"] = True
                    cleanup = self.stop_streamed_process(process)
                    if cleanup:
                        event["cleanup"] = cleanup
                if timed_out and drain_deadline is not None and time.monotonic() >= drain_deadline:
                    event["cleanup_error"] = "Stream output did not close after cleanup"
                    break
                try:
                    line = stream_queue.get(timeout=0.1)
                except queue.Empty:
                    continue
                if line is None:
                    stream_closed = True
                    continue
                line_text, received_at_epoch = line
                output.append(line_text)
                try:
                    on_line(line_text, received_at_epoch)
                except Exception as error:
                    callback_errors.append(str(error))
            if reader.is_alive():
                reader.join(timeout=5)
            if process.poll() is None:
                if not timed_out:
                    try:
                        process.wait(timeout=max(1, deadline - time.monotonic()))
                    except subprocess.TimeoutExpired:
                        timed_out = True
                        event["timed_out"] = True
                        cleanup = self.stop_streamed_process(process)
                        if cleanup:
                            event["cleanup"] = {**event.get("cleanup", {}), **cleanup}
                if process.poll() is None and not timed_out:
                    timed_out = True
                    event["timed_out"] = True
                    cleanup = self.stop_streamed_process(process)
                    if cleanup:
                        event["cleanup"] = {**event.get("cleanup", {}), **cleanup}
            if process.poll() is None:
                event["cleanup_error"] = "Streamed command did not exit"
        finally:
            event["finished_at_epoch"] = time.time()
            event["duration_seconds"] = round(event["finished_at_epoch"] - event["started_at_epoch"], 2)
            event["exit_code"] = process.returncode if process else None
            if callback_errors:
                event["callback_errors"] = callback_errors
            with self.command_lock:
                self.commands.append(event)
        return {
            "exit": process.returncode if process else None,
            "timed_out": timed_out,
            "callback_errors": callback_errors,
            "command_event": event,
            "output": "".join(output),
        }

    def run_clipboard_bridge(self, project: pathlib.Path, udid: str, result: pathlib.Path) -> tuple[dict[str, object], dict[str, object]]:
        recorder = ClipboardBridgeRecorder(lambda _index: self.run_bridge_paste(udid))

        def on_line(line: str, received_at_epoch: float) -> None:
            match = re.search(r"ACE_CLIPBOARD_BRIDGE_MARKER index=(\d+)", line)
            if match:
                recorder.record_marker(int(match.group(1)), received_at_epoch)

        command = [
            "xcodebuild", "test-without-building", "-project", str(project), "-scheme", "LandmarksTrial",
            "-sdk", "iphonesimulator", "-derivedDataPath", str(self.build), "-resultBundlePath", str(result),
            "-destination", f"platform=iOS Simulator,id={udid}", "CODE_SIGNING_ALLOWED=NO",
            "-parallel-testing-enabled", "NO", f"-only-testing:{CLIPBOARD_BRIDGE_TEST}",
        ]
        stream = self.run_streamed(command, self.settings["test_seconds"], on_line, cwd=project.parent)
        bridge = {
            "markers": recorder.records,
            "reads_stopped": recorder.reads_stopped,
            "validation": recorder.validation(),
            "xcode_stream": {key: value for key, value in stream.items() if key != "output"},
        }
        self.write_text(self.evidence / "clipboard-bridge.json", json.dumps(bridge, indent=2) + "\n")
        return stream, bridge

    def failure_screenshot(self, udid: str, label: str) -> dict[str, object]:
        path = self.evidence / "results" / f"{label}-simulator-failure.png"
        path.parent.mkdir(parents=True, exist_ok=True)
        try:
            _, exit_code = self.run(["xcrun", "simctl", "io", udid, "screenshot", str(path)], 20,
                                    allow_failure=True, final=True)
            return {"path": str(path.relative_to(self.evidence)), "exit": exit_code,
                    "exists": path.is_file()}
        except Exception as error:
            return {"path": str(path.relative_to(self.evidence)), "exit": None, "exists": path.is_file(),
                    "error": str(error)}
    def result_evidence(self, result: pathlib.Path, label: str, *, final: bool = False) -> dict[str, object]:
        record: dict[str, object] = {"label": label, "result_bundle": str(result)}
        if not result.is_dir():
            record["result_bundle_status"] = "missing"
            return record
        budget = self.final_remaining if final else self.remaining
        archive = self.evidence / "results" / f"{label}.xcresult.tar.gz"
        archive.parent.mkdir(parents=True, exist_ok=True)
        self.run(["/usr/bin/tar", "-czf", str(archive), "-C", str(result.parent), result.name], budget(60), final=final)
        summary, _ = self.run(
            ["xcrun", "xcresulttool", "get", "test-results", "summary", "--path", str(result)],
            budget(30), final=final,
        )
        tests, _ = self.run(
            ["xcrun", "xcresulttool", "get", "test-results", "tests", "--path", str(result)],
            budget(30), final=final,
        )
        self.write_text(self.evidence / "results" / f"{label}-summary.json", summary)
        self.write_text(self.evidence / "results" / f"{label}-tests.json", tests)
        parsed = json.loads(tests)
        cases = [node for node in self.dictionaries(parsed) if str(node.get("nodeType", "")).lower() in {"test case", "testcase"}]
        failed = [node for node in cases if str(node.get("result", "")).lower() == "failed"]
        detail_paths: list[str] = []
        for index, node in enumerate(failed):
            identifier = node.get("nodeIdentifier")
            if not isinstance(identifier, str):
                continue
            details, _ = self.run(
                ["xcrun", "xcresulttool", "get", "test-results", "test-details", "--path", str(result), "--test-id", identifier],
                budget(30), final=final,
            )
            detail = self.evidence / "results" / f"{label}-failure-{index}-details.json"
            self.write_text(detail, details)
            detail_paths.append(str(detail.relative_to(self.evidence)))
        attachments = self.evidence / "attachments" / label
        attachments.mkdir(parents=True, exist_ok=True)
        attachment_output, attachment_exit = self.run(
            ["xcrun", "xcresulttool", "export", "attachments", "--path", str(result), "--output-path", str(attachments)],
            budget(45), allow_failure=True, final=final,
        )
        pngs = sorted(attachments.rglob("*.png"))
        record.update({
            "failed_nodes": len(failed),
            "test_cases": [
                {"name": node.get("name"), "identifier": node.get("nodeIdentifier"), "result": node.get("result")}
                for node in cases
            ],
            "failure_details": detail_paths,
            "attachments_png": [str(path.relative_to(self.evidence)) for path in pngs],
            "attachment_export_exit": attachment_exit,
            "attachment_export_output": attachment_output[-1000:],
            "result_archive": str(archive.relative_to(self.evidence)),
            "result_archive_sha256": self.sha256(archive, final=final),
        })
        return record
    def build_for_testing(self, project: pathlib.Path, udid: str) -> pathlib.Path:
        result = self.evidence / "build-for-testing.xcresult"
        self.run([
            "xcodebuild", "build-for-testing", "-project", str(project), "-scheme", "LandmarksTrial",
            "-sdk", "iphonesimulator", "-configuration", "Debug", "-derivedDataPath", str(self.build),
            "-resultBundlePath", str(result), "-destination", f"platform=iOS Simulator,id={udid}",
            "CODE_SIGNING_ALLOWED=NO", "-parallel-testing-enabled", "NO",
        ], 210, cwd=project.parent)
        app = self.build / APP_RELATIVE
        if not app.is_dir():
            raise RuntimeError("Build-for-testing did not create Landmarks.app")
        self.write_text(self.evidence / "app-hash-before-test.txt", self.tree_hashes(app))
        return app

    def retain_diagnostic_candidate(self, app: pathlib.Path, native_status: str, native_exit: object) -> None:
        before_app = (self.evidence / "app-hash-before-test.txt").read_text(encoding="utf-8")
        after_app = self.tree_hashes(app, final=True)
        self.write_text(self.evidence / "app-hash-after-test.txt", after_app)
        if before_app != after_app:
            raise RuntimeError("Landmarks.app changed during the audit diagnostic")
        before_source = (self.evidence / "source-hashes-before-test.txt").read_text(encoding="utf-8")
        after_source = self.tree_hashes(self.source, final=True)
        self.write_text(self.evidence / "source-hashes-after-test.txt", after_source)
        if before_source != after_source:
            raise RuntimeError("The derived source changed during the audit diagnostic")
        candidate = self.root / "candidate" / "Landmarks.app"
        candidate.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(app, candidate, dirs_exist_ok=True)
        candidate_hashes = self.tree_hashes(candidate, final=True)
        self.write_text(self.evidence / "candidate-app-hash.txt", candidate_hashes)
        if candidate_hashes != after_app:
            raise RuntimeError("The provisional preview app did not match the tested diagnostic candidate")
        self.outcome["provisional_preview"] = {
            "status": "provisional_audit_diagnostic",
            "app_hash_before_test": "app-hash-before-test.txt",
            "app_hash_after_test": "app-hash-after-test.txt",
            "candidate_hash": "candidate-app-hash.txt",
            "source_hash_before_test": "source-hashes-before-test.txt",
            "source_hash_after_test": "source-hashes-after-test.txt",
            "native_test_status": native_status,
            "native_test_exit": native_exit,
        }

    def one_test(
        self,
        project: pathlib.Path,
        udid: str,
        test_name: str,
        label: str,
        *,
        traits: dict[str, str] | None = None,
    ) -> dict[str, object]:
        result = self.evidence / "results" / f"{label}.xcresult"
        observations: dict[str, object] = {"requested_traits": traits, "label": label, "test": test_name, "udid": udid}
        previous: dict[str, str] = {}
        test_exit: int | None = None
        failure: Exception | None = None
        collector_stop: threading.Event | None = None
        collector_thread: threading.Thread | None = None
        collector_samples: list[dict[str, object]] = []
        try:
            if traits:
                for setting in ("appearance", "content_size"):
                    previous[setting] = self.simctl_ui(udid, setting)
                    self.simctl_ui(udid, setting, traits[setting])
                    observed = self.simctl_ui(udid, setting)
                    observations[f"{setting}_observed"] = observed
                    if observed != traits[setting]:
                        raise RuntimeError(f"Simulator {setting} did not match the requested value")
            if test_name == FOCUSED_TEST:
                observations["clipboard_reset"] = self.reset_focused_clipboard(udid)
                collector_stop, collector_thread, collector_samples = self.start_clipboard_collector(udid)
            if test_name == CLIPBOARD_BRIDGE_TEST:
                observations["clipboard_reset"] = self.reset_focused_clipboard(udid)
                stream, bridge = self.run_clipboard_bridge(project, udid, result)
                observations["clipboard_bridge"] = bridge
                test_exit = stream["exit"] if isinstance(stream.get("exit"), int) else None
                if stream.get("timed_out"):
                    raise RuntimeError("XCTest stream timed out before the clipboard bridge completed")
                if stream.get("callback_errors"):
                    raise RuntimeError("Clipboard bridge stream callback failed")
                if not bridge["validation"].get("passed"):
                    raise RuntimeError(str(bridge["validation"].get("error")))
            else:
                _, test_exit = self.run([
                    "xcodebuild", "test-without-building", "-project", str(project), "-scheme", "LandmarksTrial",
                    "-sdk", "iphonesimulator", "-derivedDataPath", str(self.build), "-resultBundlePath", str(result),
                    "-destination", f"platform=iOS Simulator,id={udid}", "CODE_SIGNING_ALLOWED=NO",
                    "-parallel-testing-enabled", "NO", f"-only-testing:{test_name}",
                ], self.settings.get("test_seconds", 150), allow_failure=True, cwd=project.parent)
            if test_exit != 0:
                raise RuntimeError(f"XCTest returned {test_exit}: {test_name}")
        except Exception as error:
            failure = error
            observations["error"] = str(error)
        finally:
            if collector_stop is not None and collector_thread is not None:
                collector_stop.set()
                try:
                    collector_thread.join(timeout=self.final_remaining(15))
                except Exception as error:
                    observations["clipboard_collector_join_error"] = str(error)
                collector_record: dict[str, object] = {"samples": collector_samples,
                                                        "joined": not collector_thread.is_alive()}
                if collector_thread.is_alive():
                    collector_record["validation"] = {"passed": False, "error": "Clipboard collector did not stop"}
                else:
                    collector_record["validation"] = validate_clipboard_transitions(collector_samples)
                self.write_text(self.evidence / "focused-clipboard-collector.json", json.dumps(collector_record, indent=2) + "\n")
                observations["clipboard_collector"] = collector_record
                if failure is None and not collector_record["validation"].get("passed"):
                    failure = RuntimeError(str(collector_record["validation"].get("error")))
                    observations["error"] = str(failure)
            if test_name in (FOCUSED_TEST, DIAGNOSTIC_TEST):
                try:
                    clipboard, clipboard_exit = self.run(["xcrun", "simctl", "pbpaste", udid], 15,
                                                         allow_failure=True, final=True)
                    observations["clipboard_after_copy"] = {"exit": clipboard_exit, "payload": clipboard,
                                                              "reason": "failure-diagnostic" if failure else "pass-assertion"}
                    if failure is None and (clipboard_exit != 0 or clipboard != "OPEN"):
                        observations["clipboard_error"] = "The copy control did not leave OPEN in the simulator pasteboard"
                        failure = RuntimeError(str(observations["clipboard_error"]))
                        observations["error"] = str(failure)
                except Exception as error:
                    observations["clipboard_after_copy"] = {"exit": None, "payload": None, "reason": str(error)}
                    if failure is None:
                        observations["clipboard_error"] = str(error)
                        failure = error
                        observations["error"] = str(error)
            if failure is not None:
                observations["failure_screenshot"] = self.failure_screenshot(udid, label)
            if result.is_dir():
                try:
                    observations["result_evidence"] = self.result_evidence(result, label, final=failure is not None or self.mode == "diagnostic")
                except Exception as error:
                    observations["retention_error"] = str(error)
            if traits:
                restored: dict[str, str] = {}
                try:
                    for setting in ("appearance", "content_size"):
                        if setting in previous:
                            self.simctl_ui(udid, setting, previous[setting], final=True)
                            restored[setting] = self.simctl_ui(udid, setting, final=True)
                            if restored[setting] != previous[setting]:
                                raise RuntimeError(f"Simulator {setting} did not restore")
                except Exception as error:
                    observations["restore_error"] = str(error)
                observations["restored_traits"] = restored
            observations["test_exit"] = test_exit
            observations["passed"] = not any(name in observations for name in ("error", "restore_error", "clipboard_error")) and test_exit == 0
            self.write_text(self.evidence / "cases" / f"{label}.json", json.dumps(observations, indent=2) + "\n")
        if failure is not None:
            raise failure
        if observations.get("restore_error"):
            raise RuntimeError(str(observations["restore_error"]))
        if observations.get("clipboard_error"):
            raise RuntimeError(str(observations["clipboard_error"]))
        try:
            evidence = observations.get("result_evidence")
            if not isinstance(evidence, dict):
                raise RuntimeError("Xcode did not retain result evidence")
            if evidence.get("failed_nodes"):
                raise RuntimeError(f"Xcode recorded a failed node: {test_name}")
            cases = evidence.get("test_cases", [])
            if len(cases) != 1 or test_name.rsplit("/", 1)[-1] not in json.dumps(cases[0], sort_keys=True):
                raise RuntimeError(f"Xcode did not retain exactly the selected XCTest: {test_name}")
            if cases[0].get("result", "").lower() != "passed" or not evidence.get("attachments_png"):
                raise RuntimeError(f"Xcode did not retain a passing XCTest with a PNG attachment: {test_name}")
        except Exception as error:
            observations["error"] = str(error)
            observations["failure_screenshot"] = self.failure_screenshot(udid, label)
            observations["passed"] = False
            self.write_text(self.evidence / "cases" / f"{label}.json", json.dumps(observations, indent=2) + "\n")
            raise
        observations["passed"] = True
        self.write_text(self.evidence / "cases" / f"{label}.json", json.dumps(observations, indent=2) + "\n")
        return observations

    def run_trial(self, repo: pathlib.Path) -> None:
        self.root.mkdir(parents=True, exist_ok=True)
        self.build.mkdir(parents=True, exist_ok=True)
        self.evidence.mkdir(parents=True, exist_ok=True)
        self.raw_log.touch()
        project, derived_root = self.download_and_overlay(repo)
        for name, command, limit in (
            ("xcode-version.txt", ["xcodebuild", "-version"], 15),
            ("swift-version.txt", ["swift", "--version"], 15),
            ("simulator-list.json", ["xcrun", "simctl", "list", "devices", "available", "-j"], 90),
        ):
            output, _ = self.run(command, limit)
            self.write_text(self.evidence / name, output)
        devices = json.loads((self.evidence / "simulator-list.json").read_text(encoding="utf-8")).get("devices", {})
        selections: list[dict[str, str]] = []
        for name in self.settings["devices"]:
            runtime, udid = self.simulator(name, devices)
            selections.append({"name": name, "runtime": runtime, "udid": udid})
        self.write_text(self.evidence / "simulator-selections.json", json.dumps(selections, indent=2) + "\n")
        first_udid = selections[0]["udid"]
        app = self.build_for_testing(project, first_udid)
        records: list[dict[str, object]] = []
        for selection in selections:
            for appearance, content_size in self.settings["contexts"]:
                label = f"{selection['name'].replace(' ', '-').lower()}-{appearance}-{content_size}"
                traits = {"appearance": appearance, "content_size": content_size}
                try:
                    trial = self.one_test(project, selection["udid"], self.settings["test"], label, traits=traits)
                except Exception as error:
                    case_path = self.evidence / "cases" / f"{label}.json"
                    trial = json.loads(case_path.read_text(encoding="utf-8")) if case_path.is_file() else {"error": "case record missing"}
                    records.append({"device": selection, "test": self.settings["test"], "trial": trial})
                    self.write_text(self.evidence / "matrix-records.json", json.dumps(records, indent=2) + "\n")
                    if self.mode == "diagnostic":
                        self.retain_diagnostic_candidate(app, "failed", trial.get("test_exit"))
                        self.outcome["records"] = records
                        self.outcome["result"] = "diagnostic_failed"
                    raise
                records.append({"device": selection, "test": self.settings["test"], "trial": trial})
                self.write_text(self.evidence / "matrix-records.json", json.dumps(records, indent=2) + "\n")
                print(json.dumps({"progress": "case-passed", "mode": self.mode, "completed": len(records),
                                  "required": len(selections) * len(self.settings["contexts"]), "label": label}), flush=True)
        if self.mode == "diagnostic":
            self.retain_diagnostic_candidate(app, "passed", 0)
            self.outcome["records"] = records
            self.outcome["result"] = "diagnostic_passed"
            return
        self.write_text(self.evidence / "app-hash-after-test.txt", self.tree_hashes(app))
        if (self.evidence / "app-hash-before-test.txt").read_bytes() != (self.evidence / "app-hash-after-test.txt").read_bytes():
            raise RuntimeError("Landmarks.app changed during native tests")
        candidate = self.root / "candidate" / "Landmarks.app"
        candidate.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(app, candidate, dirs_exist_ok=True)
        candidate_hashes = self.tree_hashes(candidate)
        self.write_text(self.evidence / "candidate-app-hash.txt", candidate_hashes)
        if candidate_hashes != (self.evidence / "app-hash-after-test.txt").read_text(encoding="utf-8"):
            raise RuntimeError("The published preview app hash did not match the tested candidate")
        before_test = (self.evidence / "source-hashes-before-test.txt").read_bytes()
        after_test = self.tree_hashes(self.source)
        self.write_text(self.evidence / "source-hashes-after-test.txt", after_test)
        if before_test != after_test.encode("utf-8"):
            raise RuntimeError("The derived source changed during the native tests")
        self.outcome["records"] = records
        self.outcome["result"] = "passed"

    def finalise(self) -> None:
        finalisation: dict[str, object] = {}
        if self.source.is_dir():
            try:
                final_source_hashes = self.tree_hashes(self.source, final=True)
                self.write_text(self.evidence / "source-hashes-after-finalisation.txt", final_source_hashes)
                before_test = self.evidence / "source-hashes-before-test.txt"
                if before_test.exists() and before_test.read_text(encoding="utf-8") != final_source_hashes:
                    finalisation["source_integrity_error"] = "Derived source changed after the overlay"
                    self.outcome["result"] = "runner_failure"
            except Exception as error:
                finalisation["source_hash_error"] = str(error)
                self.outcome["result"] = "runner_failure"
        self.outcome["finished_at_epoch"] = time.time()
        self.outcome["elapsed_seconds"] = round(self.outcome["finished_at_epoch"] - self.started, 2)
        self.outcome["commands"] = self.commands
        finalisation["archive_status_payload"] = "The evidence archive contains status.json before its evidence_archive digest."
        self.outcome["finalisation"] = finalisation
        self.write_text(self.evidence / "status.json", json.dumps(self.outcome, indent=2) + "\n")
        try:
            if self.mode == "diagnostic":
                finalisation["evidence_archive_status"] = "not-created-for-diagnostic"
            elif self.evidence.exists():
                archive = self.root / "evidence.tar.gz"
                self.run(["/usr/bin/tar", "-czf", str(archive), "-C", str(self.root), "evidence"], 60, final=True)
                finalisation["evidence_archive"] = {"path": str(archive), "sha256": self.sha256(archive, final=True)}
        except Exception as error:
            finalisation["archive_error"] = str(error)
        self.outcome["finalisation"] = finalisation
        self.write_text(self.evidence / "status.json", json.dumps(self.outcome, indent=2) + "\n")
        print(json.dumps(self.outcome, indent=2))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=sorted(MODE), required=True)
    arguments = parser.parse_args()
    trial = Trial(arguments.mode)
    try:
        trial.run_trial(pathlib.Path(os.environ.get("CM_BUILD_DIR", os.getcwd())).resolve())
    except Exception as error:
        trial.outcome["error"] = str(error)
        trial.write_text(trial.evidence / "failure.txt", traceback.format_exc())
    finally:
        trial.finalise()
    return 0 if trial.outcome["result"] in {"passed", "diagnostic_passed"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
