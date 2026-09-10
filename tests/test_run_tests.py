import importlib.util
import hashlib
from contextlib import ExitStack, redirect_stderr, redirect_stdout
from io import StringIO
import json
import os
import shutil
import subprocess
import sys
import tarfile
import tempfile
import unittest
import zlib
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("run_tests", ROOT / "tools" / "run_tests.py")
runner = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(runner)


class RunnerContractTests(unittest.TestCase):
    @staticmethod
    def png_fixture(
        payload: bytes | None = None, width: int = 1, height: int = 1
    ) -> bytes:
        def chunk(kind: bytes, data: bytes) -> bytes:
            return (
                len(data).to_bytes(4, "big") + kind + data
                + zlib.crc32(kind + data).to_bytes(4, "big")
            )

        pixels = payload if payload is not None else b"\x00\x00\x00\x00\x00"
        return (
            b"\x89PNG\r\n\x1a\n"
            + chunk(b"IHDR", width.to_bytes(4, "big") + height.to_bytes(4, "big") + b"\x08\x06\x00\x00\x00")
            + chunk(b"IDAT", zlib.compress(pixels))
            + chunk(b"IEND", b"")
        )
    def simulator_snapshot(self, devices):
        return {
            "runtimes": [{"identifier": "com.apple.CoreSimulator.SimRuntime.iOS-26-1", "version": "26.1", "isAvailable": True}],
            "devicetypes": [
                {"name": runner.IOS_CORE_DEVICE, "identifier": "com.apple.CoreSimulator.SimDeviceType.iPhone-17"},
                {"name": "iPhone 17 Pro Max", "identifier": "com.apple.CoreSimulator.SimDeviceType.iPhone-17-Pro-Max"},
            ],
            "devices": {"com.apple.CoreSimulator.SimRuntime.iOS-26-1": devices},
        }

    def controlled_evidence_fixture(self):
        plan = json.loads(
            (ROOT / "ios/ACEClientApp/RuntimeEvidencePlan.json").read_text(
                encoding="utf-8"
            )
        )
        register = json.loads(
            (ROOT / "ios/ACEClientApp/Phase6_1EvidenceRegister.json").read_text(
                encoding="utf-8"
            )
        )
        plan["controlledRegister"]["path"] = "register.json"
        return plan, register

    def validate_fixture(self, plan, register):
        source_ids = [
            identifier
            for entry in plan["entries"]
            for identifier in entry["identifiers"]
        ]
        with tempfile.TemporaryDirectory() as directory:
            plan_path = Path(directory) / "plan.json"
            (Path(directory) / "register.json").write_text(
                json.dumps(register), encoding="utf-8"
            )
            return runner.validate_public_evidence_records(plan_path, source_ids, plan)

    def live_artifact_root(self, directory):
        return Path(directory) / "mcx-19-live-artifacts"

    def run_live_success_fixture(self, root):
        destinations = {
            runner.IOS_CORE_DEVICE: "platform=iOS Simulator,id=11111111-1111-1111-1111-111111111111",
            "iPhone 17 Pro Max": "platform=iOS Simulator,id=22222222-2222-2222-2222-222222222222",
        }

        def resolve(names, recorder=None, verification_seconds=None, require_ready=False):
            self.assertEqual(names, runner.IOS_RELEASE_DEVICES)
            assert recorder is not None
            self.assertTrue(require_ready)
            recorder("selected-runtime", "com.apple.CoreSimulator.SimRuntime.iOS-26-1")
            recorder("device-types", {runner.IOS_CORE_DEVICE: "core", "iPhone 17 Pro Max": "max"})
            recorder("resolved-destinations", destinations)
            return destinations

        def ios_test(name, command, cwd, environment, expected_tests, artifact_root):
            manifest = json.loads(
                (artifact_root / "live-evidence-manifest.json").read_text(encoding="utf-8")
            )
            self.assertEqual(manifest["status"], "failed")
            self.assertNotIn(name, [item["name"] for item in manifest["results"]])
            (artifact_root / f"{name}.log").write_text("controlled result", encoding="utf-8")
            (artifact_root / f"{name}.xcresult").mkdir()
            (artifact_root / f"{name}.xcresult" / "Info.plist").write_text("controlled", encoding="utf-8")
            (artifact_root / f"{name}-summary.json").write_text(
                json.dumps({"passedTests": expected_tests, "failedTests": 0, "skippedTests": 0}),
                encoding="utf-8",
            )
            screenshots = []
            logical_names = runner._expected_logical_screenshot_names(name)
            if logical_names:
                directory = artifact_root / runner.LIVE_REVIEW_STAGE / runner.LIVE_SCREENSHOT_DIRECTORY / name
                directory.mkdir(parents=True)
                png = self.png_fixture()
                for number, _ in enumerate(logical_names, 1):
                    screenshot = directory / f"{number:02d}.png"
                    screenshot.write_bytes(png)
                    screenshots.append(screenshot.relative_to(artifact_root / runner.LIVE_REVIEW_STAGE).as_posix())
            return {"name": name, "status": "passed", "exit": 0, "detail": "controlled", "screenshots": screenshots}

        simulator_settings = {"appearance": "light", "content_size": "medium"}

        def controlled_command(name, command, cwd, environment, log_path):
            if name.startswith("simctl-"):
                setting = command[-2] if name.endswith("-set") else command[-1]
                if name.endswith("-query"):
                    log_path.write_text(simulator_settings[setting], encoding="utf-8")
                else:
                    simulator_settings[setting] = command[-1]
                    log_path.write_text("controlled", encoding="utf-8")
                return runner.LiveCommandResult(0, "controlled", process_exit=0)
            self.assertEqual(name, "ios-negative-config")
            log_path.write_text(runner.NEGATIVE_CONFIG_REJECTION, encoding="utf-8")
            return runner.LiveCommandResult(1, "controlled rejection", "command-nonzero", 1)

        def preflight(_root, phase, _command, _timeout):
            if phase == "preflight-simctl-list-runtimes":
                return {"runtimes": [{"identifier": "com.apple.CoreSimulator.SimRuntime.iOS-26-1", "version": "26.1", "isAvailable": True}]}
            if phase == "preflight-simctl-list-devicetypes":
                return {"devicetypes": [
                    {"name": runner.IOS_CORE_DEVICE, "identifier": "core"},
                    {"name": "iPhone 17 Pro Max", "identifier": "max"},
                ]}
            if phase == "preflight-simctl-list-devices-available":
                return {"devices": {"com.apple.CoreSimulator.SimRuntime.iOS-26-1": []}}
            raise AssertionError(f"unexpected preflight phase {phase}")

        def live_preflight(root_path):
            (root_path / "simulator-resolution.json").write_text(
                json.dumps({"status": "passed", "devices": destinations}),
                encoding="utf-8",
            )
            (root_path / runner.SIMULATOR_RESOLUTION_LOG).write_text(
                "fixture simulator preflight\n", encoding="utf-8"
            )
            return destinations

        return (
            mock.patch.multiple(
                runner,
                LIVE_ARTIFACT_ROOT=root,
                LIVE_PRIVATE_COLLECTION_ROOT=root.parent / "private-collection",
                _xcode_version=lambda _timeout, **_kwargs: runner.CODEMAGIC_XCODE_VERSION,
                _preflight_simctl_json=preflight,
                _live_simulator_preflight=live_preflight,
            ),
            mock.patch.object(runner, "_live_execution_context", return_value={"workflow": runner.LIVE_WORKFLOW}),
            mock.patch.object(runner, "_live_repository_metadata", return_value={"repository": runner.LIVE_REPOSITORY, "commit": "a" * 40, "baseline": runner.LIVE_BASELINE_COMMIT}),
            mock.patch.object(runner, "ui_methods", return_value=[*runner.LIVE_UI_METHODS, runner.LIVE_NORMAL_SETTINGS_METHOD]),
            mock.patch.object(runner.shutil, "which", return_value="controlled-tool"),
            mock.patch.object(runner, "resolve_ios_destinations", side_effect=resolve),
            mock.patch.object(runner, "_run_live_ios_test", side_effect=ios_test),
            mock.patch.object(runner, "_run_live_command", side_effect=controlled_command),
        )

    def assert_diagnostic_retention_operational_failure(self, phase):
        with tempfile.TemporaryDirectory() as directory:
            root = self.live_artifact_root(directory)
            contexts = self.run_live_success_fixture(root)
            failed_name = (
                f"ios-release-{runner.IOS_CORE_DEVICE}-light-"
                f"{runner.LIVE_UI_METHODS[0]}"
            )
            simulator_settings = {"appearance": "light", "content_size": "medium"}
            xcodebuild_calls = []

            def controlled_command(name, command, _cwd, _environment, log_path):
                if name.startswith("simctl-"):
                    setting = command[-2] if name.endswith("-set") else command[-1]
                    if name.endswith("-query"):
                        log_path.write_text(simulator_settings[setting], encoding="utf-8")
                    else:
                        simulator_settings[setting] = command[-1]
                        log_path.write_text("controlled", encoding="utf-8")
                    return runner.LiveCommandResult(0, "controlled", process_exit=0)
                if name == "ios-negative-config":
                    log_path.write_text(runner.NEGATIVE_CONFIG_REJECTION, encoding="utf-8")
                    return runner.LiveCommandResult(1, "controlled", "command-nonzero", 1)
                if name.endswith("-diagnostic-attachments"):
                    output = Path(command[-1])
                    output.mkdir()
                    logical_names = runner._expected_logical_screenshot_names(failed_name)
                    attachments = []
                    for number, logical in enumerate(logical_names, 1):
                        filename = f"{number:02d}.png"
                        (output / filename).write_bytes(self.png_fixture())
                        attachments.append({
                            "suggestedHumanReadableName": logical,
                            "exportedFileName": filename,
                        })
                    (output / "manifest.json").write_text(
                        json.dumps([{"attachments": attachments}]), encoding="utf-8"
                    )
                    return runner.LiveCommandResult(0, "controlled", process_exit=0)
                if name.endswith("-xcresult"):
                    base = name.removesuffix("-xcresult")
                    expected = 65 if base == "ios-65-unit" else 42 if base == "ios-evidence-contract" else 1
                    log_path.write_text(json.dumps({
                        "passedTests": expected, "failedTests": 0, "skippedTests": 0,
                    }), encoding="utf-8")
                    return runner.LiveCommandResult(0, "controlled", process_exit=0)
                if command[0] == "xcodebuild":
                    xcodebuild_calls.append(name)
                    result_path = Path(command[command.index("-resultBundlePath") + 1])
                    result_path.mkdir()
                    if name == failed_name:
                        return runner.LiveCommandResult(1, "controlled", "command-nonzero", 1)
                    return runner.LiveCommandResult(0, "controlled", process_exit=0)
                raise AssertionError(f"unexpected command {name}")

            original_scan = runner._scan_live_artifacts

            def fail_diagnostic_scan(path):
                if Path(path).name.startswith(".diagnostic-image-stage-"):
                    raise ValueError("controlled")
                return original_scan(path)

            with ExitStack() as stack:
                for context in contexts[:6]:
                    stack.enter_context(context)
                stack.enter_context(mock.patch.object(
                    runner, "_run_live_command", side_effect=controlled_command
                ))
                if phase == "copy":
                    stack.enter_context(mock.patch.object(
                        runner.shutil, "copyfile", side_effect=OSError("controlled")
                    ))
                else:
                    stack.enter_context(mock.patch.object(
                        runner, "_scan_live_artifacts", side_effect=fail_diagnostic_scan
                    ))
                    if phase == "scan-cleanup-denied":
                        original_unlink = Path.unlink

                        def deny_stage_unlink(path, *args, **kwargs):
                            if path.parent.name.startswith(".diagnostic-image-stage-"):
                                raise PermissionError("controlled")
                            return original_unlink(path, *args, **kwargs)

                        stack.enter_context(mock.patch.object(
                            Path, "unlink", new=deny_stage_unlink
                        ))
                result = runner.live_evidence_checks(root, "a" * 40)

            self.assertEqual(result[0]["reason"], "safe-image-retention-failed")
            snapshot = json.loads((root / "live-evidence-progress.json").read_text())
            self.assertEqual(snapshot["fault"], "safe-image-retention-failed")
            self.assertEqual(xcodebuild_calls, ["ios-65-unit", failed_name])
            native = snapshot["completed"][-1]
            self.assertEqual(native["name"], failed_name)
            self.assertEqual(native["reason"], "command-nonzero")
            self.assertEqual(native["diagnosticImageStatus"], "attachment-invalid")
            self.assertNotIn("safeImageRetentionFailure", native)

    def test_live_progress_survives_interruption_after_one_completed_command(self):
        with tempfile.TemporaryDirectory() as directory:
            root = self.live_artifact_root(directory)
            contexts = self.run_live_success_fixture(root)
            output = StringIO()
            first = {"name": "ios-65-unit", "exit": 0, "detail": "ios-65-unit executed 65 tests", "process_exit": 0}
            with contexts[0], contexts[1], contexts[2], contexts[3], contexts[4], contexts[5], mock.patch.object(
                runner, "_run_live_ios_test", side_effect=[first, KeyboardInterrupt()]
            ), contexts[7], redirect_stdout(output):
                with self.assertRaises(KeyboardInterrupt):
                    runner.live_evidence_checks(root, "a" * 40)
            progress = json.loads((root / "live-evidence-progress.json").read_text())
            manifest = json.loads((root / "live-evidence-manifest.json").read_text())
            self.assertFalse(progress["releaseEvidence"])
            self.assertEqual(progress["status"], "incomplete")
            self.assertEqual(progress["completed"], [runner._published_live_result(first)])
            self.assertIn(progress["activeCommand"], runner._live_command_names())
            self.assertNotEqual(progress["activeCommand"], "ios-65-unit")
            self.assertEqual(manifest["results"], progress["completed"])
            self.assertIn('"processExit": 0', output.getvalue())

    def test_live_progress_filters_data_flushes_and_preserves_previous_file_on_write_failure(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            raw = {"name": "ios-65-unit", "exit": 1, "process_exit": 65,
                   "detail": "password=do-not-publish", "reason": "token=do-not-publish"}
            with mock.patch("builtins.print") as printed:
                runner._write_live_progress(root, [raw], "ios-negative-config")
            self.assertTrue(printed.call_args.kwargs["flush"])
            path = root / "live-evidence-progress.json"
            before = path.read_bytes()
            self.assertNotIn(b"do-not-publish", before)
            self.assertNotIn("do-not-publish", str(printed.call_args))
            self.assertEqual(json.loads(before)["completed"][0]["processExit"], 65)
            with mock.patch.object(runner.os, "replace", side_effect=OSError("write failed")):
                with self.assertRaises(OSError):
                    runner._write_live_progress(root, [], "setup")
            self.assertEqual(path.read_bytes(), before)
            self.assertEqual(list(root.iterdir()), [path])
            with self.assertRaises(ValueError):
                runner._write_live_progress(root, [], "password=do-not-publish")

    def test_live_progress_survives_abrupt_process_exit(self):
        with tempfile.TemporaryDirectory() as directory:
            code = (
                "import os, runpy; from pathlib import Path; "
                f"runner = runpy.run_path({str(ROOT / 'tools/run_tests.py')!r}); "
                f"runner['_write_live_progress'](Path({directory!r}), "
                "[{'name': 'ios-65-unit', 'exit': 0, 'process_exit': 0}], 'ios-negative-config'); "
                "os._exit(17)"
            )
            process = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, timeout=15)
            self.assertEqual(process.returncode, 17)
            event = json.loads(process.stdout.removeprefix("live-progress="))
            self.assertEqual(event["completedCount"], 1)
            self.assertEqual(event["activeCommand"], "ios-negative-config")
            progress = json.loads((Path(directory) / "live-evidence-progress.json").read_text())
            self.assertEqual(progress["completed"][0]["processExit"], 0)
            self.assertFalse(progress["releaseEvidence"])

    def test_mixed_result_retains_earlier_success_images_outside_review_stage(self):
        with tempfile.TemporaryDirectory() as directory:
            root = self.live_artifact_root(directory)
            contexts = self.run_live_success_fixture(root)
            calls = 0

            def ios_test(name, _command, _cwd, _environment, _expected, artifact_root):
                nonlocal calls
                calls += 1
                if calls == 2:
                    images = artifact_root / runner.LIVE_REVIEW_STAGE / runner.LIVE_SCREENSHOT_DIRECTORY / name
                    images.mkdir(parents=True)
                    paths = []
                    for number, _logical in enumerate(runner._expected_logical_screenshot_names(name), 1):
                        image = images / f"{number:02d}.png"
                        image.write_bytes(self.png_fixture())
                        paths.append(image.relative_to(artifact_root / runner.LIVE_REVIEW_STAGE).as_posix())
                    return {"name": name, "exit": 0, "detail": f"{name} executed 1 tests", "screenshots": paths}
                if calls == 1:
                    return {"name": name, "exit": 0, "detail": f"{name} executed 65 tests"}
                return {"name": name, "exit": 1, "reason": "command-nonzero", "test_counts": {"status": "unknown"}}

            with contexts[0], contexts[1], contexts[2], contexts[3], contexts[4], contexts[5], contexts[7], mock.patch.object(
                runner, "_run_live_ios_test", side_effect=ios_test
            ):
                result = runner.live_evidence_checks(root, "a" * 40)
            self.assertEqual(result[0]["exit"], 1)
            progress = json.loads((root / "live-evidence-progress.json").read_text())
            successful = next(item for item in progress["completed"] if item["name"].endswith("-testBothAppearances"))
            retained = successful["safeImages"]
            self.assertTrue(all((root / image["path"]).is_file() for image in retained))
            self.assertFalse((root / runner.LIVE_REVIEW_ARTIFACTS).exists())

    def test_diagnostic_attachment_rejects_valid_png_metadata_secret(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            bundle = root / "result.xcresult"
            bundle.mkdir()
            name = f"ios-release-{runner.IOS_CORE_DEVICE}-light-testLaunchShowsSafeConfigurationState"
            logical = runner._expected_logical_screenshot_names(name)[0]

            def export(_name, command, _cwd, _environment, _log):
                output = Path(command[-1])
                output.mkdir()
                image = self.png_fixture()
                chunk_type = b"tEXt"
                chunk_data = b"token=private"
                chunk = (
                    len(chunk_data).to_bytes(4, "big") + chunk_type + chunk_data
                    + zlib.crc32(chunk_type + chunk_data).to_bytes(4, "big")
                )
                capture = output / "capture.png"
                capture.write_bytes(image[:-12] + chunk + image[-12:])
                self.assertTrue(runner._valid_png(capture))
                (output / "manifest.json").write_text(json.dumps([{"attachments": [{"suggestedHumanReadableName": logical, "exportedFileName": "capture.png"}]}]), encoding="utf-8")
                return runner.LiveCommandResult(0, "controlled", process_exit=0)

            with mock.patch.object(runner, "_run_live_command", side_effect=export):
                status, images, missing, problem, retention_failed = runner._retain_live_diagnostic_images(name, ROOT, root, bundle)
            self.assertEqual(status, "attachment-invalid")
            self.assertEqual(images, [])
            self.assertEqual(problem, "attachment-invalid")
            self.assertTrue(retention_failed)
            self.assertEqual(missing, [logical])
            self.assertFalse(any((root / runner.LIVE_DIAGNOSTIC_IMAGE_DIRECTORY).rglob("*.png")))

    def test_restoration_failure_retains_validated_staged_screenshots(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            name = f"ios-normal-settings-{runner.IOS_CORE_DEVICE}-light"
            source = root / runner.LIVE_REVIEW_STAGE / runner.LIVE_SCREENSHOT_DIRECTORY / name
            source.mkdir(parents=True)
            paths = []
            for number, _logical in enumerate(runner._expected_logical_screenshot_names(name), 1):
                image = source / f"{number:02d}.png"
                image.write_bytes(self.png_fixture())
                paths.append(image.relative_to(root / runner.LIVE_REVIEW_STAGE).as_posix())
            check = {"name": name, "exit": 1, "reason": "simulator-setting-restore-failed", "screenshots": paths}
            runner._retain_completed_review_images(root, [check])
            published = runner._published_live_result(check)
            self.assertEqual(published["reason"], "simulator-setting-restore-failed")
            self.assertTrue(all((root / item["path"]).is_file() for item in published["safeImages"]))

    def test_safe_image_collection_failure_stops_before_next_command(self):
        with tempfile.TemporaryDirectory() as directory:
            root = self.live_artifact_root(directory)
            contexts = self.run_live_success_fixture(root)
            calls = 0

            def ios_test(name, _command, _cwd, _environment, _expected, artifact_root):
                nonlocal calls
                calls += 1
                if calls == 1:
                    return {"name": name, "exit": 0, "detail": f"{name} executed 65 tests"}
                image_root = artifact_root / runner.LIVE_REVIEW_STAGE / runner.LIVE_SCREENSHOT_DIRECTORY / name
                image_root.mkdir(parents=True)
                paths = []
                for number, _logical in enumerate(runner._expected_logical_screenshot_names(name), 1):
                    image = image_root / f"{number:02d}.png"
                    image.write_bytes(self.png_fixture())
                    paths.append(image.relative_to(artifact_root / runner.LIVE_REVIEW_STAGE).as_posix())
                return {"name": name, "exit": 0, "detail": f"{name} executed 1 tests", "screenshots": paths}

            with contexts[0], contexts[1], contexts[2], contexts[3], contexts[4], contexts[5], contexts[7], mock.patch.object(
                runner, "_run_live_ios_test", side_effect=ios_test
            ), mock.patch.object(runner.shutil, "copyfile", side_effect=OSError("controlled")):
                result = runner.live_evidence_checks(root, "a" * 40)
            self.assertEqual(calls, 2)
            self.assertEqual(result[0]["exit"], 1)
            snapshot = json.loads((root / "live-evidence-progress.json").read_text())
            self.assertEqual(snapshot["fault"], "safe-image-retention-failed")
            self.assertEqual(snapshot["completed"][-1]["exit"], 0)

    def test_diagnostic_copy_failure_preserves_native_reason_and_stops(self):
        self.assert_diagnostic_retention_operational_failure("copy")

    def test_diagnostic_scan_failure_preserves_native_reason_and_stops(self):
        self.assert_diagnostic_retention_operational_failure("scan")

    def test_diagnostic_scan_cleanup_denial_preserves_native_reason_and_stops(self):
        self.assert_diagnostic_retention_operational_failure("scan-cleanup-denied")

    def test_failed_ui_without_staged_screenshots_keeps_native_reason(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            name = f"ios-release-{runner.IOS_CORE_DEVICE}-light-testBothAppearances"
            check = {
                "name": name,
                "exit": 1,
                "reason": "command-nonzero",
                "diagnostic": "test-failures-recorded",
                "test_counts": {"status": "unknown"},
            }
            self.assertIsNone(runner._retain_completed_review_images(root, [check]))
            published = runner._published_live_result(check)
            self.assertEqual(published["reason"], "command-nonzero")
            self.assertNotIn("safeImages", published)

    def test_successful_ui_without_staged_screenshots_fails_safe_retention(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            name = f"ios-release-{runner.IOS_CORE_DEVICE}-light-testBothAppearances"
            check = {"name": name, "exit": 0, "detail": "controlled"}
            self.assertEqual(
                runner._retain_completed_review_images(root, [check]),
                "safe-image-retention-failed",
            )

    def test_diagnostic_attachment_marks_duplicate_logical_name_ambiguous(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            bundle = root / "result.xcresult"
            bundle.mkdir()
            name = f"ios-release-{runner.IOS_CORE_DEVICE}-light-testLaunchShowsSafeConfigurationState"
            logical = runner._expected_logical_screenshot_names(name)[0]

            def export(_name, command, _cwd, _environment, _log):
                output = Path(command[-1])
                output.mkdir()
                for filename in ("one.png", "two.png"):
                    (output / filename).write_bytes(self.png_fixture())
                (output / "manifest.json").write_text(json.dumps([{"attachments": [
                    {"suggestedHumanReadableName": logical, "exportedFileName": "one.png"},
                    {"suggestedHumanReadableName": logical, "exportedFileName": "two.png"},
                ]}]), encoding="utf-8")
                return runner.LiveCommandResult(0, "controlled", process_exit=0)

            with mock.patch.object(runner, "_run_live_command", side_effect=export):
                status, images, missing, problem, retention_failed = runner._retain_live_diagnostic_images(name, ROOT, root, bundle)
            self.assertEqual(status, "attachment-missing")
            self.assertEqual(images, [])
            self.assertEqual(missing, [logical])
            self.assertEqual(problem, "attachment-ambiguous")
            self.assertFalse(retention_failed)

    def test_diagnostic_attachment_rejects_duplicate_before_image_validation(self):
        for case, contents in (
            ("invalid-first", (b"invalid", self.png_fixture())),
            ("invalid-second", (self.png_fixture(), b"invalid")),
        ):
            with self.subTest(case=case), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                bundle = root / "result.xcresult"
                bundle.mkdir()
                name = f"ios-release-{runner.IOS_CORE_DEVICE}-light-testLaunchShowsSafeConfigurationState"
                logical = runner._expected_logical_screenshot_names(name)[0]

                def export(_name, command, _cwd, _environment, _log):
                    output = Path(command[-1])
                    output.mkdir()
                    for filename, content in zip(("one.png", "two.png"), contents):
                        (output / filename).write_bytes(content)
                    (output / "manifest.json").write_text(json.dumps([{"attachments": [
                        {"suggestedHumanReadableName": logical, "exportedFileName": "one.png"},
                        {"suggestedHumanReadableName": logical, "exportedFileName": "two.png"},
                    ]}]), encoding="utf-8")
                    return runner.LiveCommandResult(0, "controlled", process_exit=0)

                with mock.patch.object(runner, "_run_live_command", side_effect=export):
                    status, images, missing, problem, retention_failed = runner._retain_live_diagnostic_images(
                        name, ROOT, root, bundle
                    )
                self.assertEqual(status, "attachment-missing")
                self.assertEqual(images, [])
                self.assertEqual(missing, [logical])
                self.assertEqual(problem, "attachment-ambiguous")
                self.assertFalse(retention_failed)

    def test_live_progress_retries_only_bounded_windows_sharing_errors(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            original_replace = runner.os.replace
            sharing_error = PermissionError("transient sharing failure")
            sharing_error.winerror = 5
            calls = []

            def replace(source, destination):
                calls.append(destination)
                if len(calls) == 1:
                    raise sharing_error
                return original_replace(source, destination)

            with mock.patch.object(runner.os, "replace", side_effect=replace), mock.patch.object(runner.time, "sleep") as sleep:
                runner._write_live_progress(root, [], "setup")
            self.assertEqual(len(calls), 2)
            sleep.assert_called_once_with(0.1)
            before = (root / "live-evidence-progress.json").read_bytes()
            with mock.patch.object(runner.os, "replace", side_effect=sharing_error) as replace_mock, mock.patch.object(runner.time, "sleep"):
                with self.assertRaises(PermissionError):
                    runner._write_live_progress(root, [], "artifact-validation")
            self.assertEqual(replace_mock.call_count, 3)
            self.assertEqual((root / "live-evidence-progress.json").read_bytes(), before)

    def test_live_evidence_success_fixture_writes_initial_external_controlled_manifest(self):
        with tempfile.TemporaryDirectory() as directory:
            root = self.live_artifact_root(directory)
            contexts = self.run_live_success_fixture(root)
            with contexts[0], contexts[1], contexts[2], contexts[3], contexts[4], contexts[5], contexts[6], contexts[7]:
                checks = runner.live_evidence_checks(root, "a" * 40)
            self.assertEqual(len(checks), 31, checks)
            self.assertTrue(all(check["exit"] == 0 for check in checks))
            manifest = json.loads((root / "live-evidence-manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["status"], "passed-not-release-evidence")
            self.assertFalse(manifest["releaseEvidence"])
            self.assertEqual(manifest["commit"], "a" * 40)
            self.assertTrue(manifest["checksums"])
            published = root / runner.LIVE_REVIEW_ARTIFACTS
            review = json.loads((published / runner.LIVE_REVIEW_MANIFEST).read_text(encoding="utf-8"))
            self.assertFalse(review["releaseEvidence"])
            self.assertEqual(review["status"], "pending-manual-native-inspection")
            for screenshot in review["screenshots"]:
                self.assertEqual(screenshot["sha256"], hashlib.sha256((published / screenshot["path"]).read_bytes()).hexdigest())
                if "forced-" in screenshot["logicalName"]:
                    self.assertEqual(screenshot["appearance"], screenshot["logicalName"].rsplit("forced-", 1)[1])
                if screenshot["appearanceMode"] == "system-setting-at-launch":
                    self.assertEqual(screenshot["contentSize"], runner.LIVE_CONTENT_SIZE)
            self.assertFalse((root / runner.LIVE_REVIEW_STAGE).exists())
            progress = json.loads((root / "live-evidence-progress.json").read_text())
            self.assertEqual(progress["completed"], checks)
            self.assertEqual(len(progress["completed"]), 31)
            self.assertEqual(progress["completed"][-1]["reason"], "negative-configuration-rejected")
            self.assertIsNone(progress["activeCommand"])
            self.assertEqual(progress["runState"], "complete")
            self.assertEqual(progress["status"], "incomplete")
            self.assertEqual(progress["privateCollectionStatus"], "complete")
            self.assertFalse(progress["releaseEvidence"])

    def test_live_evidence_publishes_fixed_simulator_failure_codes(self):
        cases = (
            ("wrong runtime", "injected runtime detail", runner.SIMULATOR_RESOLUTION_FAILURE_REASON),
            ("wrong simulator type", "injected type detail", runner.SIMULATOR_RESOLUTION_FAILURE_REASON),
            ("duplicate UUID", "injected UUID detail", runner.SIMULATOR_RESOLUTION_FAILURE_REASON),
            ("bootstatus", "private bootstatus detail", runner.SIMULATOR_RESOLUTION_FAILURE_REASON),
            ("timeout", "injected timeout detail", runner.SIMULATOR_RESOLUTION_TIMEOUT_REASON),
        )
        for name, message, expected_reason in cases:
            with self.subTest(name=name), tempfile.TemporaryDirectory() as directory:
                root = self.live_artifact_root(directory)
                error = runner.SimulatorResolutionError(message, expected_reason)
                with mock.patch.object(runner, "LIVE_ARTIFACT_ROOT", root), mock.patch.object(runner, "_live_execution_context", return_value={}), mock.patch.object(runner, "_live_repository_metadata", return_value={}), mock.patch.object(runner, "ui_methods", return_value=[*runner.LIVE_UI_METHODS, runner.LIVE_NORMAL_SETTINGS_METHOD]), mock.patch.object(runner, "_live_simulator_preflight", side_effect=error), mock.patch.object(runner, "_run_live_ios_test") as ios_test:
                    checks = runner.live_evidence_checks(root, "a" * 40)
                self.assertEqual(checks[0]["status"], "failed")
                self.assertEqual(checks[0]["reason"], expected_reason)
                self.assertEqual(
                    checks[0]["detail"],
                    "simulator resolution timed out"
                    if expected_reason == runner.SIMULATOR_RESOLUTION_TIMEOUT_REASON
                    else "simulator resolution failed",
                )
                self.assertNotIn(message, checks[0]["detail"])
                ios_test.assert_not_called()
                manifest = json.loads((root / "live-evidence-manifest.json").read_text(encoding="utf-8"))
                self.assertEqual(manifest["status"], "failed")
                self.assertEqual(manifest["failure"], expected_reason)
                self.assertNotIn(message, json.dumps(manifest))

    def test_live_setup_failures_publish_fixed_reason_and_safe_text(self):
        injected = "injected-path-or-environment=value"
        with mock.patch.object(
            runner, "_live_artifact_root", side_effect=ValueError(injected)
        ):
            artifact_failure = runner.live_evidence_checks(Path("relative"), "a" * 40)
        self.assertEqual(artifact_failure[0]["reason"], runner.LIVE_SETUP_FAILURE_REASON)
        self.assertEqual(artifact_failure[0]["detail"], "live setup failed")
        self.assertNotIn(injected, json.dumps(artifact_failure))

        with tempfile.TemporaryDirectory() as directory:
            root = self.live_artifact_root(directory)
            with mock.patch.object(runner, "LIVE_ARTIFACT_ROOT", root), mock.patch.object(
                runner, "_write_live_manifest", side_effect=OSError(injected)
            ):
                manifest_failure = runner.live_evidence_checks(root, "a" * 40)
        self.assertEqual(manifest_failure[0]["reason"], runner.LIVE_SETUP_FAILURE_REASON)
        self.assertEqual(manifest_failure[0]["detail"], "live setup failed")
        self.assertNotIn(injected, json.dumps(manifest_failure))

        with tempfile.TemporaryDirectory() as directory:
            root = self.live_artifact_root(directory)
            with mock.patch.object(runner, "LIVE_ARTIFACT_ROOT", root), mock.patch.object(
                runner, "_live_execution_context", side_effect=ValueError(injected)
            ):
                context_failure = runner.live_evidence_checks(root, "a" * 40)
            manifest = json.loads((root / "live-evidence-manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(context_failure[0]["reason"], runner.LIVE_SETUP_FAILURE_REASON)
        self.assertEqual(context_failure[0]["detail"], "live setup failed")
        self.assertEqual(manifest["failure"], runner.LIVE_SETUP_FAILURE_REASON)
        self.assertNotIn(injected, json.dumps(manifest))

    def test_manifest_value_errors_publish_fixed_safe_failure(self):
        initial_injected = "injected initial manifest value error"
        with tempfile.TemporaryDirectory() as directory:
            root = self.live_artifact_root(directory)
            with mock.patch.object(runner, "LIVE_ARTIFACT_ROOT", root), mock.patch.object(
                runner, "_write_live_manifest", side_effect=ValueError(initial_injected)
            ):
                initial_failure = runner.live_evidence_checks(root, "a" * 40)
        self.assertEqual(initial_failure[0]["reason"], runner.LIVE_SETUP_FAILURE_REASON)
        self.assertEqual(initial_failure[0]["detail"], "live setup failed")
        self.assertNotIn(initial_injected, json.dumps(initial_failure))

        context_injected = "injected context value error"
        reporting_injected = "injected reporting manifest value error"
        original_write = runner._write_live_manifest

        def fail_failure_report(root, manifest):
            if "failure" in manifest:
                raise ValueError(reporting_injected)
            original_write(root, manifest)

        with tempfile.TemporaryDirectory() as directory:
            root = self.live_artifact_root(directory)
            with mock.patch.object(runner, "LIVE_ARTIFACT_ROOT", root), mock.patch.object(
                runner, "_live_execution_context", side_effect=ValueError(context_injected)
            ), mock.patch.object(runner, "_write_live_manifest", side_effect=fail_failure_report):
                reporting_failure = runner.live_evidence_checks(root, "a" * 40)
            manifest = json.loads(
                (root / "live-evidence-manifest.json").read_text(encoding="utf-8")
            )
        self.assertEqual(reporting_failure[0]["reason"], runner.LIVE_SETUP_FAILURE_REASON)
        self.assertEqual(reporting_failure[0]["detail"], "live setup failed")
        public_json = json.dumps({"result": reporting_failure, "manifest": manifest})
        self.assertNotIn(context_injected, public_json)
        self.assertNotIn(reporting_injected, public_json)

    def test_live_evidence_fails_closed_for_missing_artifact_and_nonzero_live_result(self):
        with tempfile.TemporaryDirectory() as directory:
            root = self.live_artifact_root(directory)
            contexts = self.run_live_success_fixture(root)
            def missing_artifact(name, command, cwd, environment, expected_tests, artifact_root):
                return {"name": name, "status": "passed", "exit": 0, "detail": "controlled"}
            with contexts[0], contexts[1], contexts[2], contexts[3], contexts[4], contexts[5], mock.patch.object(runner, "_run_live_ios_test", side_effect=missing_artifact), contexts[7]:
                checks = runner.live_evidence_checks(root, "a" * 40)
            self.assertEqual(checks[0]["status"], "failed")
            self.assertEqual(checks[0]["reason"], "safe-image-retention-failed")
            self.assertEqual(checks[0]["detail"], "live setup failed")

        with tempfile.TemporaryDirectory() as directory:
            root = self.live_artifact_root(directory)
            contexts = self.run_live_success_fixture(root)
            def nonzero(name, command, cwd, environment, expected_tests, artifact_root):
                return {"name": name, "status": "failed", "exit": 1, "detail": "controlled non-zero live result"}
            with contexts[0], contexts[1], contexts[2], contexts[3], contexts[4], contexts[5], mock.patch.object(runner, "_run_live_ios_test", side_effect=nonzero), contexts[7]:
                checks = runner.live_evidence_checks(root, "a" * 40)
            self.assertEqual(checks[0]["status"], "failed")
            self.assertTrue(checks[0]["detail"].startswith("failed live commands: "))
            self.assertIn("ios-65-unit", checks[0]["detail"])

    def test_live_evidence_requires_simulator_resolution_log(self):
        with tempfile.TemporaryDirectory() as directory:
            root = self.live_artifact_root(directory)
            contexts = self.run_live_success_fixture(root)
            destinations = {
                runner.IOS_CORE_DEVICE: "platform=iOS Simulator,id=11111111-1111-1111-1111-111111111111",
                "iPhone 17 Pro Max": "platform=iOS Simulator,id=22222222-2222-2222-2222-222222222222",
            }

            def missing_log(root_path):
                (root_path / "simulator-resolution.json").write_text(
                    json.dumps({"status": "passed", "devices": destinations}),
                    encoding="utf-8",
                )
                return destinations

            with contexts[0], contexts[1], contexts[2], contexts[3], contexts[4], contexts[5], contexts[6], contexts[7], mock.patch.object(
                runner, "_live_simulator_preflight", side_effect=missing_log
            ):
                checks = runner.live_evidence_checks(root, "a" * 40)
            self.assertEqual(checks[0]["status"], "failed")
            self.assertEqual(checks[0]["reason"], runner.LIVE_SETUP_FAILURE_REASON)
            self.assertEqual(checks[0]["detail"], "live setup failed")

    def test_live_evidence_command_failure_summary_identifies_the_failed_command(self):
        with tempfile.TemporaryDirectory() as directory:
            root = self.live_artifact_root(directory)
            contexts = self.run_live_success_fixture(root)
            raw_output = "raw command output\nsecret-like=value\nunrelated-value"
            start_failure_name = (
                f"ios-release-{runner.IOS_CORE_DEVICE}-light-"
                f"{runner.LIVE_UI_METHODS[0]}"
            )

            def command_result(name, command, cwd, environment, expected_tests, artifact_root):
                failure = {
                    "ios-65-unit": ("command-nonzero", 71),
                    "ios-evidence-contract": ("command-timeout", None),
                    start_failure_name: ("command-start-failed", None),
                }.get(name)
                if failure is None:
                    screenshots = []
                    logical_names = runner._expected_logical_screenshot_names(name)
                    if logical_names:
                        directory = artifact_root / runner.LIVE_REVIEW_STAGE / runner.LIVE_SCREENSHOT_DIRECTORY / name
                        directory.mkdir(parents=True)
                        for number, _ in enumerate(logical_names, 1):
                            screenshot = directory / f"{number:02d}.png"
                            screenshot.write_bytes(self.png_fixture())
                            screenshots.append(
                                screenshot.relative_to(
                                    artifact_root / runner.LIVE_REVIEW_STAGE
                                ).as_posix()
                            )
                    return {
                        "name": name,
                        "status": "passed",
                        "exit": 0,
                        "detail": raw_output,
                        "screenshots": screenshots,
                    }
                reason, process_exit = failure
                result = {
                    "name": name,
                    "status": "failed",
                    "exit": 1,
                    "detail": raw_output,
                    "reason": reason,
                }
                if process_exit is not None:
                    result["process_exit"] = process_exit
                return result

            with contexts[0], contexts[1], contexts[2], contexts[3], contexts[4], contexts[5], mock.patch.object(
                runner, "_run_live_ios_test", side_effect=command_result
            ), contexts[7], mock.patch.object(runner, "load_mapping", return_value=({}, [])):
                output = StringIO()
                with redirect_stdout(output):
                    exit_code = runner.main([
                        "live-evidence", "--component", "ios", "--artifact-root",
                        str(root), "--expected-commit", "a" * 40,
                    ])
                manifest = json.loads(
                    (root / "live-evidence-manifest.json").read_text(
                        encoding="utf-8"
                    )
                )

        self.assertEqual(exit_code, 1)
        output_lines = [line for line in output.getvalue().splitlines() if not line.startswith("live-progress=")]
        self.assertEqual(output_lines[0], "report=external-artifact-root/live-evidence-manifest.json")
        self.assertIn("ios-65-unit=71", output_lines[1])
        self.assertNotIn("ios-evidence-contract=", output_lines[1].split("; process exits: ")[1])
        self.assertNotIn(f"{start_failure_name}=", output_lines[1].split("; process exits: ")[1])
        failed_result = next(
            result
            for result in manifest["results"]
            if result["name"] == "ios-65-unit"
        )
        self.assertEqual(failed_result["reason"], "command-nonzero")
        self.assertEqual(failed_result["processExit"], 71)
        start_failure = next(
            result
            for result in manifest["results"]
            if result["name"] == start_failure_name
        )
        self.assertEqual(start_failure["reason"], "command-start-failed")
        self.assertNotIn("processExit", start_failure)
        for unsafe_value in ("raw command output", "secret-like=value", "unrelated-value"):
            self.assertNotIn(unsafe_value, output.getvalue())

    def test_live_command_failure_summary_has_only_ordered_controlled_names_and_reason_codes(self):
        summary = runner._live_command_failure_summary([
            {"name": "ios-negative-config", "exit": 1, "detail": "raw output", "reason": "command-timeout"},
            {"name": "unexpected-command", "exit": 1, "detail": "secret-like=value", "reason": "command-nonzero"},
            {"name": "ios-65-unit", "exit": 1, "detail": "unrelated-value", "reason": "untrusted-value"},
            {"name": "ios-negative-config", "exit": 1, "detail": "duplicate", "reason": "secret-like=value"},
        ])
        self.assertEqual(
            summary,
            "failed live commands: ios-65-unit, ios-negative-config; reasons: ios-65-unit=controlled-failure, ios-negative-config=negative-configuration-not-rejected",
        )
        for unsafe_value in ("raw output", "secret-like=value", "unrelated-value", "unexpected-command", "untrusted-value"):
            self.assertNotIn(unsafe_value, summary)

    def test_live_command_failure_paths_publish_fixed_reason_codes(self):
        cases = (
            (
                "timeout",
                subprocess.TimeoutExpired(["xcodebuild"], 30),
                "command-timeout",
                None,
            ),
            ("start", OSError("controlled"), "command-start-failed", None),
            (
                "nonzero",
                subprocess.CompletedProcess(["xcodebuild"], 37, "controlled"),
                "command-nonzero",
                37,
            ),
        )
        with tempfile.TemporaryDirectory() as directory:
            for name, response, expected_reason, expected_process_exit in cases:
                response_keyword = (
                    {"side_effect": response}
                    if isinstance(response, BaseException)
                    else {"return_value": response}
                )
                with self.subTest(name=name), mock.patch.object(
                    runner.subprocess, "run", **response_keyword
                ):
                    result = runner._run_live_command(
                        "ios-65-unit",
                        ["xcodebuild", "test"],
                        ROOT,
                        {},
                        Path(directory) / f"{name}.log",
                )
                self.assertEqual(result.reason, expected_reason)
                self.assertEqual(result.process_exit, expected_process_exit)
        with tempfile.TemporaryDirectory() as directory, mock.patch.object(
            runner.subprocess,
            "run",
            return_value=subprocess.CompletedProcess(["xcodebuild"], 0, "controlled"),
        ):
            result = runner._run_live_command(
                "ios-65-unit", ["xcodebuild", "test"], ROOT, {},
                Path(directory) / "completed.log",
            )
        self.assertEqual(tuple(result), (0, "ios-65-unit completed"))
        self.assertEqual(result.process_exit, 0)

    def test_failed_live_ios_result_summaries_publish_fixed_diagnostics(self):
        cases = (
            ("failed-tests", json.dumps({"passedTests": 0, "failedTests": 2}), "test-failures-recorded"),
            ("no-failed-tests", json.dumps({"passedTests": 0, "failedTests": 0}), "result-summary-no-failed-tests"),
            ("missing-summary", None, "result-summary-missing"),
            ("malformed-summary", "not-json", "result-summary-malformed"),
            ("oversized-summary", "x" * (runner.LIVE_RESULT_SUMMARY_MAX_BYTES + 1), "result-summary-oversized"),
            ("over-complex-summary", json.dumps(list(range(runner.LIVE_RESULT_SUMMARY_MAX_NODES + 1))), "result-summary-over-complex"),
            ("secret-like-summary", '{"token":"secret-like=value"}', "diagnostic-gap"),
            ("rejected-number", '{"failedTests": ' + "9" * 5_000 + "}", "result-summary-malformed"),
        )
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            result_path = root / "ios-65-unit.xcresult"
            result_path.mkdir()
            for case_name, summary, diagnostic in cases:
                with self.subTest(case=case_name):
                    summary_path = root / "ios-65-unit-summary.json"
                    summary_path.unlink(missing_ok=True)

                    def command(name, _command, _cwd, _environment, log_path):
                        if name == "ios-65-unit":
                            return runner.LiveCommandResult(1, "raw=secret", "command-nonzero", 71)
                        if summary is not None:
                            log_path.write_text(summary, encoding="utf-8")
                        return runner.LiveCommandResult(0, "controlled", process_exit=0)

                    with mock.patch.object(runner, "_run_live_command", side_effect=command):
                        result = runner._run_live_ios_test(
                            "ios-65-unit", ["xcodebuild", "test"], ROOT, {}, 2, root
                        )
                    published = runner._published_live_result(result)
                    self.assertEqual(result["status"], "failed")
                    self.assertEqual(result["exit"], 1)
                    self.assertEqual(published["diagnostic"], diagnostic)
                    self.assertEqual(published["processExit"], 71)
                    self.assertNotIn("secret-like=value", json.dumps(published))

    def test_failed_live_ios_result_bundle_and_summary_command_have_fixed_diagnostics(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            primary_failure = runner.LiveCommandResult(
                1, "raw=secret", "command-nonzero", 71
            )
            with mock.patch.object(runner, "_run_live_command", return_value=primary_failure):
                missing_bundle = runner._run_live_ios_test(
                    "ios-65-unit", ["xcodebuild", "test"], ROOT, {}, 2, root
                )
            self.assertEqual(missing_bundle["diagnostic"], "result-bundle-missing")
            (root / "ios-65-unit.xcresult").mkdir()
            with mock.patch.object(
                runner,
                "_run_live_command",
                side_effect=(primary_failure, runner.LiveCommandResult(1, "raw", "command-nonzero", 3)),
            ):
                summary_failure = runner._run_live_ios_test(
                    "ios-65-unit", ["xcodebuild", "test"], ROOT, {}, 2, root
                )
            self.assertEqual(summary_failure["diagnostic"], "result-summary-command-failed")
            self.assertEqual(summary_failure["exit"], 1)

    def test_failed_live_ios_result_retains_only_bounded_structured_evidence(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "ios-65-unit.xcresult").mkdir()
            payload = {
                "passedTests": 0,
                "failedTests": 1,
                "testFailures": [{
                    "testCaseName": "ACEClientAppTests.testRelease",
                    "fileName": str(ROOT / "ios" / "ACEClientApp" / "Tests.swift"),
                    "lineNumber": 42,
                    "expected": "RELEASED",
                    "actual": "DRAFT",
                    "failureText": "XCTAssertEqual failed",
                }],
            }

            def command(name, _command, _cwd, _environment, log_path):
                if name == "ios-65-unit":
                    return runner.LiveCommandResult(1, "raw", "command-nonzero", 65)
                log_path.write_text(json.dumps(payload), encoding="utf-8")
                return runner.LiveCommandResult(0, "controlled", process_exit=0)

            with mock.patch.object(runner, "_run_live_command", side_effect=command):
                result = runner._run_live_ios_test(
                    "ios-65-unit", ["xcodebuild", "test"], ROOT, {}, 1, root
                )
        published = runner._published_live_result(result)
        self.assertEqual(published["testFailureStatus"], "available")
        self.assertEqual(published["testFailures"], [{
            "testIdentifier": "ACEClientAppTests.testRelease",
            "testIdentifierStatus": "available",
            "sourceFile": "ios/ACEClientApp/Tests.swift",
            "sourceFileStatus": "available",
            "sourceLine": 42,
            "sourceLineStatus": "available",
            "expected": "RELEASED",
            "expectedStatus": "available",
            "actual": "DRAFT",
            "actualStatus": "available",
            "failureMessage": "XCTAssertEqual failed",
            "failureMessageStatus": "available",
        }])
        self.assertEqual(
            runner._published_live_result({"name": "ios-65-unit", "exit": 0})["testFailures"],
            [],
        )

    def test_public_failure_boundary_preserves_withheld_field_statuses(self):
        retained = {
            "testIdentifierStatus": "absent",
            "sourceFileStatus": "invalid",
            "sourceLineStatus": "absent",
            "expectedStatus": "redacted",
            "actualStatus": "redacted",
            "failureMessageStatus": "redacted",
        }
        published = runner._published_live_result({
            "name": "ios-65-unit", "exit": 1,
            "test_failures": [retained], "test_failure_status": "available",
        })
        self.assertEqual(published["testFailures"], [retained])
        self.assertEqual(published["testFailureStatus"], "available")
        unsafe = "token=private https://private.invalid /Users/person/private.swift " + "x" * 513
        normalised = runner._normalise_xcresult_failure({
            "testCaseName": unsafe, "fileName": "outside.swift",
            "expected": unsafe, "actual": unsafe, "failureText": unsafe,
        })
        assert normalised is not None
        safe = runner._published_live_result({
            "name": "ios-65-unit", "exit": 1,
            "test_failures": [normalised], "test_failure_status": "available",
        })
        self.assertNotIn("private", json.dumps(safe))
        self.assertEqual(safe["testFailures"][0]["sourceFileStatus"], "invalid")

    def test_live_result_publication_is_idempotent_for_published_evidence(self):
        name = next(
            candidate for candidate in runner._live_command_names()
            if candidate.startswith("ios-normal-settings-")
        )
        raw = {
            "name": name,
            "exit": 1,
            "reason": "command-nonzero",
            "process_exit": 65,
            "simulator_settings": {
                "appearanceObserved": "dark",
                "contentSizeObserved": runner.LIVE_CONTENT_SIZE,
                "queryEvidence": [{
                    "setting": "appearance", "processExit": 0,
                    "responseStatus": "available", "response": "dark",
                }],
            },
            "check_exit_before_restore": 1,
            "check_reason_before_restore": "command-nonzero",
            "test_failures": [{
                "testIdentifierStatus": "absent", "sourceFileStatus": "absent",
                "sourceLineStatus": "absent", "expectedStatus": "redacted",
                "actualStatus": "redacted", "failureMessageStatus": "redacted",
            }],
            "test_failure_status": "available",
        }
        published = runner._published_live_result(raw)
        self.assertEqual(runner._published_live_result(published), published)
        unknown_collection = runner._published_live_result({
            "name": "ios-65-unit", "exit": 1, "reason": "command-timeout",
            "collectionProcessExitStatus": {"summary": "unknown"},
        })
        self.assertEqual(
            unknown_collection["collectionProcessExitStatus"], {"summary": "unknown"}
        )
        self.assertEqual(
            runner._published_live_result(unknown_collection), unknown_collection
        )

    def test_failure_publication_redacts_environment_tokens_and_foreign_paths(self):
        with mock.patch.dict(os.environ, {"MCX19_TEST_SECRET": "unit-secret-123"}):
            for value in (
                "unit-secret-123", "prefix unit-secret-123 suffix", "ghp_abcdefghi",
                "github_pat_abcdefghi", "sk-abcdefghi", '{"password":"fictional-secret"}',
            ):
                self.assertEqual(runner._bounded_failure_text(value), (None, "redacted"))
            self.assertEqual(
                runner._repository_relative_source_path(
                    str(ROOT / "ios" / "ACEClientApp" / "ACEClientApp" / "ACEClientAppApp.swift")
                ),
                ("ios/ACEClientApp/ACEClientApp/ACEClientAppApp.swift", "available"),
            )
            self.assertEqual(
                runner._repository_relative_source_path("tests/test_run_tests.py"),
                ("tests/test_run_tests.py", "available"),
            )
            self.assertEqual(
                runner._repository_relative_source_path("/Users/client/ios/Customer.swift"),
                (None, "invalid"),
            )
            published = runner._published_test_failures([{
                "testIdentifier": "unit-secret-123", "testIdentifierStatus": "available",
                "sourceFile": str(ROOT / "ios" / "ACEClientApp" / "ACEClientApp" / "ACEClientAppApp.swift"),
                "sourceFileStatus": "available", "sourceLine": 12, "sourceLineStatus": "available",
                "expectedStatus": "redacted", "actualStatus": "redacted",
                "failureMessageStatus": "redacted",
            }], True)
        self.assertEqual(published[0]["testIdentifierStatus"], "redacted")
        self.assertNotIn("testIdentifier", published[0])
        self.assertEqual(published[0]["sourceFile"], "ios/ACEClientApp/ACEClientApp/ACEClientAppApp.swift")

    def test_failure_evidence_keeps_safe_details_when_counts_are_unusable(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            bundle = root / "ios-65-unit.xcresult"
            bundle.mkdir()
            payload = {"testFailures": [{
                "testCaseName": "ACEClientAppTests.testUnit",
                "fileName": str(ROOT / "ios" / "ACEClientApp" / "Tests.swift"),
                "lineNumber": 12,
            }]}

            def command(_name, _command, _cwd, _environment, log_path):
                log_path.write_text(json.dumps(payload), encoding="utf-8")
                return runner.LiveCommandResult(0, "controlled", process_exit=0)

            with mock.patch.object(runner, "_run_live_command", side_effect=command):
                diagnostic, failures, status = runner._live_ios_failure_evidence(
                    "ios-65-unit", ROOT, root, bundle
                )
        self.assertEqual(diagnostic, "diagnostic-gap")
        self.assertEqual(status, "available")
        self.assertEqual(failures[0]["sourceFile"], "ios/ACEClientApp/Tests.swift")

    def test_summary_collection_exit_does_not_replace_xctest_process_exit(self):
        cases = (
            ("nonzero", runner.LiveCommandResult(1, "raw", "command-nonzero", 83), "command-nonzero", 83),
            ("timeout", runner.LiveCommandResult(1, "raw", "command-timeout"), "command-timeout", None),
            ("start", runner.LiveCommandResult(1, "raw", "command-start-failed"), "command-start-failed", None),
        )
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "ios-65-unit.xcresult").mkdir()
            primary_result = runner.LiveCommandResult(0, "controlled", process_exit=0)
            for case_name, summary_result, reason, process_exit in cases:
                with self.subTest(case=case_name), mock.patch.object(
                    runner,
                    "_run_live_command",
                    side_effect=(
                        primary_result,
                        summary_result,
                        runner.LiveCommandResult(1, "raw", "command-start-failed"),
                    ),
                ):
                    result = runner._run_live_ios_test(
                        "ios-65-unit", ["xcodebuild", "test"], ROOT, {}, 2, root
                    )
                manifest_result = runner._published_live_result(result)
                aggregate = runner._live_command_failure_summary([manifest_result])
                self.assertEqual(manifest_result["status"], "failed")
                self.assertEqual(manifest_result["reason"], reason)
                self.assertEqual(
                    manifest_result["diagnostic"], "result-summary-command-failed"
                )
                self.assertEqual(manifest_result["processExit"], 0)
                self.assertIn("process exits: ios-65-unit=0", aggregate)
                if process_exit is None:
                    self.assertNotIn("collectionProcessExits", manifest_result)
                    self.assertEqual(
                        manifest_result["collectionProcessExitStatus"]["summary"],
                        "unknown",
                    )
                else:
                    self.assertEqual(manifest_result["collectionProcessExits"]["summary"], 83)

    def test_negative_configuration_result_has_fixed_outcomes_and_metadata(self):
        cases = (
            ("exited-zero", runner.LiveCommandResult(0, "raw", process_exit=0), None, "negative-configuration-exited-zero", 1),
            ("unrelated", runner.LiveCommandResult(1, "raw", "command-nonzero", 54), "other failure", "negative-configuration-unrelated-nonzero", 1),
            ("timeout", runner.LiveCommandResult(1, "raw", "command-timeout"), None, "negative-configuration-timeout", 1),
            ("start", runner.LiveCommandResult(1, "raw", "command-start-failed"), None, "negative-configuration-start-failed", 1),
            ("missing", runner.LiveCommandResult(1, "raw", "command-nonzero", 4), None, "negative-configuration-log-missing", 1),
            ("oversized", runner.LiveCommandResult(1, "raw", "command-nonzero", 4), "x" * (runner.LIVE_RESULT_SUMMARY_MAX_BYTES + 1), "negative-configuration-log-oversized", 1),
            ("rejected", runner.LiveCommandResult(1, "raw", "command-nonzero", 4), runner.NEGATIVE_CONFIG_REJECTION, "negative-configuration-rejected", 0),
        )
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            log_path = root / "ios-negative-config.log"
            for case_name, command_result, content, reason, logical_exit in cases:
                with self.subTest(case=case_name):
                    log_path.unlink(missing_ok=True)
                    if content is not None:
                        log_path.write_text(content, encoding="utf-8")
                    result = runner._negative_configuration_result(root, log_path, command_result)
                    published = runner._published_live_result(result)
                    self.assertEqual(result["exit"], logical_exit)
                    self.assertEqual(published["reason"], reason)
                    if command_result.process_exit is None:
                        self.assertNotIn("processExit", published)
                    else:
                        self.assertEqual(published["processExit"], command_result.process_exit)
                    self.assertNotIn("raw", json.dumps(published))
            log_path.unlink(missing_ok=True)
            log_path.mkdir()
            unsafe = runner._negative_configuration_result(
                root, log_path, runner.LiveCommandResult(1, "raw", "command-nonzero", 4)
            )
            log_path.rmdir()
            with mock.patch.object(
                runner, "_bounded_live_file_text", return_value=("unreadable", None)
            ):
                unreadable = runner._negative_configuration_result(
                    root, log_path, runner.LiveCommandResult(1, "raw", "command-nonzero", 4)
                )
        self.assertEqual(unsafe["reason"], "negative-configuration-log-unsafe")
        self.assertEqual(unreadable["reason"], "negative-configuration-log-unreadable")

    def test_live_publication_rejects_untrusted_diagnostics_and_exit_metadata(self):
        published = runner._published_live_result(
            {
                "name": "ios-65-unit",
                "status": "failed",
                "exit": 1,
                "detail": "raw command output secret-like=value",
                "reason": "untrusted-value",
                "diagnostic": "secret-like=value",
                "process_exit": "raw=17",
            }
        )
        self.assertEqual(published["reason"], "controlled-failure")
        self.assertNotIn("diagnostic", published)
        self.assertNotIn("processExit", published)
        self.assertNotIn("secret-like=value", json.dumps(published))
        oversized_exit = runner._published_live_result(
            {"name": "ios-65-unit", "exit": 1, "process_exit": 2**40}
        )
        self.assertNotIn("processExit", oversized_exit)
        successful = runner._published_live_result(
            {"name": "ios-65-unit", "status": "passed", "exit": 0, "detail": "raw", "process_exit": 0}
        )
        self.assertEqual(successful["status"], "passed")
        self.assertEqual(successful["exit"], 0)
        self.assertEqual(successful["processExit"], 0)
        self.assertEqual(
            runner._published_live_success_detail(
                "ios-65-unit", "ios-65-unit executed " + "9" * 5_000 + " tests"
            ),
            "controlled live command completed",
        )
        summary = runner._live_command_failure_summary([
            {"name": "ios-65-unit", "exit": 1, "reason": "command-nonzero", "diagnostic": "test-failures-recorded"},
            {"name": "ios-evidence-contract", "exit": 1, "reason": "raw=secret", "diagnostic": "raw=secret", "process_exit": "secret-like=17"},
            {"name": "unexpected-command", "exit": 1, "reason": "command-nonzero", "process_exit": 71},
        ])
        self.assertEqual(
            summary,
            "failed live commands: ios-65-unit, ios-evidence-contract; reasons: ios-65-unit=command-nonzero, ios-evidence-contract=controlled-failure; diagnostics: ios-65-unit=test-failures-recorded",
        )
        self.assertNotIn("raw=secret", summary)

    def test_simctl_timeouts_publish_the_simulator_timeout_code(self):
        with self.assertRaises(runner.SimulatorResolutionError) as expired_list:
            runner._simctl_list(timeout=0)
        self.assertEqual(
            expired_list.exception.reason,
            runner.SIMULATOR_RESOLUTION_TIMEOUT_REASON,
        )

        with self.assertRaises(runner.SimulatorResolutionError) as expired_create:
            runner._simctl_create("test", "device", "runtime", timeout=0)
        self.assertEqual(
            expired_create.exception.reason,
            runner.SIMULATOR_RESOLUTION_TIMEOUT_REASON,
        )

        timeout = subprocess.TimeoutExpired(["xcrun", "simctl"], 1)
        with mock.patch.object(runner.subprocess, "run", side_effect=timeout):
            with self.assertRaises(runner.SimulatorResolutionError) as listed:
                runner._simctl_list(timeout=1)
        self.assertEqual(listed.exception.reason, runner.SIMULATOR_RESOLUTION_TIMEOUT_REASON)

        with mock.patch.object(runner.subprocess, "run", side_effect=timeout):
            with self.assertRaises(runner.SimulatorResolutionError) as created:
                runner._simctl_create("test", "device", "runtime", timeout=1)
        self.assertEqual(created.exception.reason, runner.SIMULATOR_RESOLUTION_TIMEOUT_REASON)

    def test_live_ios_test_failure_paths_publish_fixed_reason_codes(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with mock.patch.object(
                runner,
                "_run_live_command",
                return_value=runner.LiveCommandResult(0, "controlled"),
            ):
                missing_bundle = runner._run_live_ios_test(
                    "ios-65-unit", ["xcodebuild", "test"], ROOT, {}, 2, root
                )
            self.assertEqual(missing_bundle["reason"], "result-bundle-missing")

            result_path = root / "ios-65-unit.xcresult"
            result_path.mkdir()
            with mock.patch.object(
                runner,
                "_run_live_command",
                return_value=runner.LiveCommandResult(0, "controlled"),
            ):
                missing_summary = runner._run_live_ios_test(
                    "ios-65-unit", ["xcodebuild", "test"], ROOT, {}, 2, root
                )
            self.assertEqual(missing_summary["reason"], "result-summary-invalid")

            summary_path = root / "ios-65-unit-summary.json"
            summary_path.write_text("not JSON", encoding="utf-8")
            with mock.patch.object(
                runner,
                "_run_live_command",
                return_value=runner.LiveCommandResult(0, "controlled"),
            ):
                invalid_summary = runner._run_live_ios_test(
                    "ios-65-unit", ["xcodebuild", "test"], ROOT, {}, 2, root
                )
            self.assertEqual(invalid_summary["reason"], "result-summary-invalid")

            summary_path.write_text(
                json.dumps({"passedTests": 1, "failedTests": 0, "skippedTests": 0}),
                encoding="utf-8",
            )
            with mock.patch.object(
                runner,
                "_run_live_command",
                return_value=runner.LiveCommandResult(0, "controlled"),
            ):
                count_mismatch = runner._run_live_ios_test(
                    "ios-65-unit", ["xcodebuild", "test"], ROOT, {}, 2, root
                )
            self.assertEqual(count_mismatch["reason"], "result-count-mismatch")

    def test_live_ios_test_places_result_bundle_before_build_settings(self):
        command = runner.ios_release_ui_matrix(
            {
                device: f"platform=iOS Simulator,id=controlled-{index}"
                for index, device in enumerate(runner.IOS_RELEASE_DEVICES)
            },
            [runner.LIVE_UI_METHODS[0]],
        )[0][1]
        with tempfile.TemporaryDirectory() as directory, mock.patch.object(
            runner,
            "_run_live_command",
            return_value=runner.LiveCommandResult(1, "controlled"),
        ) as live_command:
            runner._run_live_ios_test(
                "ios-release-controlled",
                command,
                ROOT,
                runner.ios_test_environment("light"),
                1,
                Path(directory),
            )
        executed = live_command.call_args.args[1]
        self.assertLess(
            executed.index("-resultBundlePath"),
            executed.index("ACE_UI_TEST_APPEARANCE=light"),
        )
        self.assertEqual(
            executed[executed.index("-parallel-testing-enabled"):executed.index("-parallel-testing-enabled") + 2],
            ["-parallel-testing-enabled", "NO"],
        )
        self.assertLess(
            executed.index("-parallel-testing-enabled"),
            executed.index("ACE_UI_TEST_APPEARANCE=light"),
        )

    def test_live_negative_configuration_passes_controlled_build_settings(self):
        with tempfile.TemporaryDirectory() as directory:
            root = self.live_artifact_root(directory)
            contexts = self.run_live_success_fixture(root)
            captured = {}

            def negative(name, command, cwd, environment, log_path):
                self.assertEqual(name, "ios-negative-config")
                captured["command"] = command
                captured["environment"] = environment
                log_path.write_text(runner.NEGATIVE_CONFIG_REJECTION, encoding="utf-8")
                return runner.LiveCommandResult(
                    1, "controlled rejection", "command-nonzero", 1
                )

            with contexts[0], contexts[1], contexts[2], contexts[3], contexts[4], contexts[5], contexts[6], mock.patch.object(
                runner, "_run_live_command", side_effect=negative
            ), mock.patch.object(
                runner, "_normal_settings_result",
                side_effect=lambda name, command, cwd, environment, root, identifier, appearance:
                runner._run_live_ios_test(name, command, cwd, environment, 1, root),
            ):
                checks = runner.live_evidence_checks(root, "a" * 40)
        self.assertTrue(all(check["exit"] == 0 for check in checks), checks)
        self.assertEqual(captured["environment"], runner.NEGATIVE_CONFIG_ENVIRONMENT)
        self.assertEqual(captured["command"], runner.ios_negative_configuration_command())
        self.assertEqual(
            captured["command"][-2:],
            [
                f"ACE_PREVIEW_ORIGIN={runner.NEGATIVE_CONFIG_ENVIRONMENT['ACE_PREVIEW_ORIGIN']}",
                f"ACE_BUNDLE_IDENTIFIER={runner.NEGATIVE_CONFIG_ENVIRONMENT['ACE_BUNDLE_IDENTIFIER']}",
            ],
        )

    def test_negative_configuration_failure_publishes_its_fixed_reason_code(self):
        with tempfile.TemporaryDirectory() as directory:
            root = self.live_artifact_root(directory)
            contexts = self.run_live_success_fixture(root)
            with contexts[0], contexts[1], contexts[2], contexts[3], contexts[4], contexts[5], contexts[6], mock.patch.object(
                runner,
                "_run_live_command",
                return_value=runner.LiveCommandResult(0, "untrusted detail"),
            ):
                runner.live_evidence_checks(root, "a" * 40)
            manifest = json.loads(
                (root / "live-evidence-manifest.json").read_text(encoding="utf-8")
            )
        negative = next(
            result
            for result in manifest["results"]
            if result["name"] == "ios-negative-config"
        )
        self.assertEqual(
            negative["reason"], "negative-configuration-exited-zero"
        )
        self.assertNotIn("untrusted detail", json.dumps(manifest))

    def test_live_artifact_checksum_and_secret_redaction_controls_fail_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            artifact = root / "controlled.log"
            artifact.write_text("controlled", encoding="utf-8")
            checksums = runner._live_artifact_checksums(root)
            artifact.write_text("changed", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "checksum mismatch"):
                runner._verify_live_artifact_checksums(root, checksums)
            artifact.write_text("Authorization: value", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "secret or redaction"):
                runner._scan_live_artifacts(root)
            artifact.write_text("username=[redacted]", encoding="utf-8")
            runner._scan_live_artifacts(root)
            artifact.write_text('"username": "[redacted]"', encoding="utf-8")
            runner._scan_live_artifacts(root)
            artifact.write_text(
                '{"username": "[redacted]", "result": "ok"}', encoding="utf-8"
            )
            runner._scan_live_artifacts(root)
            artifact.write_text('{ "user" : "[redacted]" }', encoding="utf-8")
            runner._scan_live_artifacts(root)
            artifact.write_text("username=unredacted", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "secret or redaction"):
                runner._scan_live_artifacts(root)
            for sensitive in (
                "credential=value",
                "token: value",
                '"password": "value"',
                '"authorisation": "value"',
                '"keychain secret": "value"',
                '"credential": "value"',
                '"token": "value"',
                '"username": "value"',
            ):
                artifact.write_text(sensitive, encoding="utf-8")
                with self.subTest(sensitive=sensitive), self.assertRaisesRegex(
                    ValueError, "secret or redaction"
                ):
                    runner._scan_live_artifacts(root)
            for encoding in ("utf-16-le", "utf-16-be"):
                with self.subTest(encoding=encoding):
                    artifact.write_bytes('{"token": "value"}'.encode(encoding))
                    with self.assertRaisesRegex(ValueError, "secret or redaction"):
                        runner._scan_live_artifacts(root)
                    artifact.write_bytes(
                        '{"username": "[redacted]", "result": "ok"}'.encode(encoding)
                    )
                    runner._scan_live_artifacts(root)
                    artifact.write_bytes('{"user": "unredacted"}'.encode(encoding))
                    with self.assertRaisesRegex(ValueError, "secret or redaction"):
                        runner._scan_live_artifacts(root)

    def test_live_command_environment_excludes_unrelated_secret_values(self):
        with tempfile.TemporaryDirectory() as directory, mock.patch.dict(
            os.environ,
            {"PATH": "controlled-path", "HOME": "controlled-home", "SENTINEL_SECRET": "must-not-pass"},
            clear=True,
        ), mock.patch.object(
            runner.subprocess,
            "run",
            return_value=subprocess.CompletedProcess([], 0, ""),
        ) as command:
            exit_code, detail = runner._run_live_command(
                "controlled",
                ["xcodebuild", "test"],
                ROOT,
                runner.IOS_TEST_ENVIRONMENT,
                Path(directory) / "controlled.log",
            )
        self.assertEqual((exit_code, detail), (0, "controlled completed"))
        environment = command.call_args.kwargs["env"]
        self.assertNotIn("SENTINEL_SECRET", environment)
        self.assertEqual(environment["PATH"], "controlled-path")
        self.assertEqual(environment["ACE_PREVIEW_ORIGIN"], runner.IOS_TEST_ENVIRONMENT["ACE_PREVIEW_ORIGIN"])
        with self.assertRaisesRegex(ValueError, "unapproved environment"):
            runner._live_command_environment({"SENTINEL_SECRET": "must-not-pass"})

    def test_live_command_environment_accepts_supported_ui_test_appearances(self):
        for appearance in ("light", "dark"):
            with self.subTest(appearance=appearance):
                environment = runner._live_command_environment(
                    runner.ios_test_environment(appearance)
                )
                self.assertEqual(environment["ACE_UI_TEST_APPEARANCE"], appearance)

    def live_repository_responses(
        self, remote, head="a" * 40, ancestry_exit=0, clean_output="", remote_output=None
    ):
        return (
            subprocess.CompletedProcess(
                [], 0, remote + "\n" if remote_output is None else remote_output
            ),
            subprocess.CompletedProcess([], 0, head + "\n"),
            subprocess.CompletedProcess([], ancestry_exit, ""),
            subprocess.CompletedProcess([], 0, clean_output),
        )

    def test_live_repository_binding_accepts_only_approved_remote_forms(self):
        approved_remotes = (
            "https://github.com/mcxl/sqe-platform.git",
            "git@github.com:mcxl/sqe-platform.git",
            "ssh://git@github.com/mcxl/sqe-platform.git",
            "https://mcxl@github.com/mcxl/sqe-platform",
        )
        for remote in approved_remotes:
            with self.subTest(remote=remote), mock.patch.object(
                runner.subprocess,
                "run",
                side_effect=self.live_repository_responses(remote),
            ):
                self.assertEqual(
                    runner._live_repository_metadata("a" * 40),
                    {
                        "repository": runner.LIVE_REPOSITORY,
                        "commit": "a" * 40,
                        "baseline": runner.LIVE_BASELINE_COMMIT,
                    },
                )

    def test_live_repository_binding_accepts_one_crlf_terminator(self):
        remote = "https://mcxl@github.com/mcxl/sqe-platform"
        with mock.patch.object(
            runner.subprocess,
            "run",
            side_effect=self.live_repository_responses(
                remote, remote_output=remote + "\r\n"
            ),
        ):
            self.assertEqual(
                runner._live_repository_metadata("a" * 40)["repository"],
                runner.LIVE_REPOSITORY,
            )

    def test_live_repository_binding_rejects_unapproved_remote_forms_without_values(self):
        rejected_remotes = (
            "https://mcxl:password@github.com/mcxl/sqe-platform",
            "https://github.com:443/mcxl/sqe-platform",
            "https://github.com/mcxl/sqe-platform?branch=main",
            "https://github.com/mcxl/sqe-platform#fragment",
            "https://mcxl@github.example.com/mcxl/sqe-platform",
            "https://mcxl@github.com/other-owner/sqe-platform",
            "https://mcxl@github.com/mcxl/other-repository",
            "http://github.com/mcxl/sqe-platform.git",
            "ftp://github.com/mcxl/sqe-platform.git",
            "https://other-user@github.com/mcxl/sqe-platform",
            " https://mcxl@github.com/mcxl/sqe-platform ",
        )
        for remote in rejected_remotes:
            with self.subTest(remote=remote), mock.patch.object(
                runner.subprocess,
                "run",
                side_effect=self.live_repository_responses(remote),
            ):
                with self.assertRaises(ValueError) as error:
                    runner._live_repository_metadata("a" * 40)
                self.assertEqual(
                    str(error.exception),
                    "repository binding failed: repository-identity",
                )
                self.assertNotIn(remote, str(error.exception))

    def test_live_repository_binding_rejects_extra_or_embedded_line_breaks(self):
        approved = "https://mcxl@github.com/mcxl/sqe-platform"
        unsafe_outputs = (
            approved + "\n\n",
            approved + "\r\n\r\n",
            approved + "\nextra-value\n",
        )
        for remote_output in unsafe_outputs:
            with self.subTest(remote_output=repr(remote_output)), mock.patch.object(
                runner.subprocess,
                "run",
                side_effect=self.live_repository_responses(
                    approved, remote_output=remote_output
                ),
            ):
                with self.assertRaisesRegex(
                    ValueError, "repository binding failed: repository-identity"
                ):
                    runner._live_repository_metadata("a" * 40)

    def test_live_repository_binding_reports_only_failed_check_names(self):
        remote = "https://mcxl:password@github.example:8443/other-owner/other-repository?secret=value#fragment"
        head = "c" * 40
        expected = "d" * 40
        clean_output = "secret-clean-tree"
        with mock.patch.object(
            runner.subprocess,
            "run",
            side_effect=self.live_repository_responses(
                remote, head, ancestry_exit=1, clean_output=clean_output
            ),
        ):
            with self.assertRaises(ValueError) as error:
                runner._live_repository_metadata(expected)
        detail = str(error.exception)
        self.assertEqual(
            detail,
            "repository binding failed: repository-identity, expected-commit-match, baseline-ancestry, clean-tree",
        )
        for supplied_value in (remote, head, expected, clean_output):
            self.assertNotIn(supplied_value, detail)

    def test_live_repository_binding_rejects_a_different_expected_commit(self):
        with mock.patch.object(
            runner.subprocess,
            "run",
            side_effect=self.live_repository_responses(
                "https://github.com/mcxl/sqe-platform.git"
            ),
        ):
            with self.assertRaisesRegex(
                ValueError, "repository binding failed: expected-commit-match"
            ):
                runner._live_repository_metadata("b" * 40)

    def test_live_execution_context_requires_codemagic_workflow_and_exact_root(self):
        expected_commit = "a" * 40
        environment = {
            "CM_BUILD_ID": "controlled-build",
            "CM_BUILD_DIR": str(ROOT),
            "CM_COMMIT": expected_commit,
            "CM_BRANCH": runner.LIVE_BRANCH,
            "CM_TRIGGER_SOURCE": "api",
            "CM_BUILD_STARTED_BY": "controlled-operator",
            runner.LIVE_WORKFLOW_ENVIRONMENT_KEY: runner.LIVE_WORKFLOW,
        }
        with mock.patch.dict(os.environ, environment, clear=True):
            self.assertEqual(
                runner._live_execution_context(runner.LIVE_ARTIFACT_ROOT, expected_commit),
                {
                    "workflow": runner.LIVE_WORKFLOW,
                    "branch": runner.LIVE_BRANCH,
                    "buildId": "controlled-build",
                },
            )
            with self.assertRaisesRegex(ValueError, "Codemagic live workflow context"):
                runner._live_execution_context(Path("/private/tmp/not-approved"), expected_commit)
            with mock.patch.dict(
                os.environ,
                {runner.LIVE_WORKFLOW_ENVIRONMENT_KEY: "different-workflow"},
            ):
                with self.assertRaisesRegex(ValueError, "Codemagic live workflow context"):
                    runner._live_execution_context(runner.LIVE_ARTIFACT_ROOT, expected_commit)
            with mock.patch.dict(os.environ, {"CM_BRANCH": "different-branch"}):
                with self.assertRaisesRegex(ValueError, "Codemagic live workflow context"):
                    runner._live_execution_context(runner.LIVE_ARTIFACT_ROOT, expected_commit)
            with mock.patch.dict(os.environ, {"CM_COMMIT": "b" * 40}):
                with self.assertRaisesRegex(ValueError, "Codemagic live workflow context"):
                    runner._live_execution_context(runner.LIVE_ARTIFACT_ROOT, expected_commit)
        for name, trigger in (("missing", None), ("webhook", "webhook"), ("schedule", "schedule")):
            with self.subTest(trigger=name):
                trigger_environment = dict(environment)
                if trigger is None:
                    del trigger_environment["CM_TRIGGER_SOURCE"]
                else:
                    trigger_environment["CM_TRIGGER_SOURCE"] = trigger
                with mock.patch.dict(os.environ, trigger_environment, clear=True):
                    with self.assertRaisesRegex(ValueError, "Codemagic live workflow context"):
                        runner._live_execution_context(runner.LIVE_ARTIFACT_ROOT, expected_commit)
        operator_environment = dict(environment)
        operator_environment["CM_BUILD_STARTED_BY"] = " "
        with mock.patch.dict(os.environ, operator_environment, clear=True):
            with self.assertRaisesRegex(ValueError, "Codemagic live workflow context"):
                runner._live_execution_context(runner.LIVE_ARTIFACT_ROOT, expected_commit)

    def test_live_cli_requires_a_lower_case_approved_commit_input(self):
        with redirect_stderr(StringIO()), self.assertRaises(SystemExit):
            runner.main([
                "live-evidence", "--component", "ios", "--artifact-root",
                str(runner.LIVE_ARTIFACT_ROOT),
            ])
        with redirect_stderr(StringIO()), self.assertRaises(SystemExit):
            runner.main([
                "live-evidence", "--component", "ios", "--artifact-root",
                str(runner.LIVE_ARTIFACT_ROOT), "--expected-commit", "A" * 40,
            ])

    def test_live_repair_check_has_exact_five_command_scope_and_is_not_release_evidence(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "repair-artifacts"
            destinations = {
                runner.IOS_CORE_DEVICE: "platform=iOS Simulator,id=11111111-1111-1111-1111-111111111111",
                "iPhone 17 Pro Max": "platform=iOS Simulator,id=22222222-2222-2222-2222-222222222222",
            }
            commands = []

            def preflight(artifact_root):
                (artifact_root / "simulator-resolution.json").write_text("{}", encoding="utf-8")
                (artifact_root / runner.SIMULATOR_RESOLUTION_LOG).write_text("controlled", encoding="utf-8")
                return destinations

            def ios_test(name, command, _cwd, environment, expected, artifact_root):
                commands.append((name, command, environment, expected))
                (artifact_root / f"{name}.log").write_text("controlled", encoding="utf-8")
                (artifact_root / f"{name}-summary.json").write_text("{}", encoding="utf-8")
                return {"name": name, "status": "passed", "exit": 0,
                        "detail": f"{name} executed {expected} tests", "process_exit": 0}

            context = {"workflow": runner.LIVE_REPAIR_WORKFLOW,
                       "branch": runner.LIVE_BRANCH, "buildId": "controlled-build"}
            metadata = {"repository": runner.LIVE_REPOSITORY, "commit": "a" * 40,
                        "baseline": runner.LIVE_BASELINE_COMMIT}
            with mock.patch.object(runner, "LIVE_ARTIFACT_ROOT", root), mock.patch.object(
                runner, "_live_execution_context", return_value=context
            ), mock.patch.object(runner, "_live_repository_metadata", return_value=metadata), mock.patch.object(
                runner, "_live_simulator_preflight", side_effect=preflight
            ), mock.patch.object(
                runner, "ui_methods", return_value=[*runner.LIVE_UI_METHODS, runner.LIVE_NORMAL_SETTINGS_METHOD]
            ), mock.patch.object(runner, "_run_live_ios_test", side_effect=ios_test):
                results = runner.live_repair_check(root, "a" * 40)
            snapshot = json.loads((root / runner.LIVE_REPAIR_SNAPSHOT).read_text(encoding="utf-8"))

        self.assertEqual(len(results), 5)
        self.assertEqual(len(commands), 5)
        self.assertEqual({item[0] for item in commands}, runner._live_repair_command_names())
        self.assertEqual(commands[0][0], "ios-65-unit")
        self.assertEqual(commands[0][3], 65)
        ui_commands = commands[1:]
        self.assertEqual({name.split("-light-", 1)[1] for name, *_ in ui_commands}, set(runner.LIVE_REPAIR_UI_METHODS))
        self.assertEqual({runner.IOS_CORE_DEVICE, "iPhone 17 Pro Max"}, {next(device for device in runner.IOS_RELEASE_DEVICES if f"-{device}-" in name) for name, *_ in ui_commands})
        self.assertTrue(all(environment["ACE_UI_TEST_APPEARANCE"] == "light" for _name, _command, environment, _expected in ui_commands))
        self.assertEqual(snapshot["scope"], runner.LIVE_REPAIR_SCOPE)
        self.assertEqual(snapshot["status"], "passed")
        self.assertFalse(snapshot["releaseEvidence"])
        self.assertEqual(snapshot["verifiedIdentity"]["commit"], "a" * 40)

    def test_live_repair_check_retains_failure_in_its_incremental_snapshot(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "repair-artifacts"
            destinations = {device: f"platform=iOS Simulator,id={index:08d}-1111-1111-1111-111111111111" for index, device in enumerate(runner.IOS_RELEASE_DEVICES, 1)}
            calls = []

            def preflight(artifact_root):
                (artifact_root / "simulator-resolution.json").write_text("{}", encoding="utf-8")
                (artifact_root / runner.SIMULATOR_RESOLUTION_LOG).write_text("controlled", encoding="utf-8")
                return destinations

            def ios_test(name, _command, _cwd, _environment, _expected, artifact_root):
                calls.append(name)
                (artifact_root / f"{name}.log").write_text("controlled failure log", encoding="utf-8")
                if len(calls) == 2:
                    return {"name": name, "status": "failed", "exit": 1,
                            "detail": "controlled", "reason": "command-nonzero", "process_exit": 71}
                return {"name": name, "status": "passed", "exit": 0, "detail": "controlled"}

            context = {"workflow": runner.LIVE_REPAIR_WORKFLOW,
                       "branch": runner.LIVE_BRANCH, "buildId": "controlled-build"}
            metadata = {"repository": runner.LIVE_REPOSITORY, "commit": "a" * 40,
                        "baseline": runner.LIVE_BASELINE_COMMIT}
            with mock.patch.object(runner, "LIVE_ARTIFACT_ROOT", root), mock.patch.object(
                runner, "_live_execution_context", return_value=context
            ), mock.patch.object(runner, "_live_repository_metadata", return_value=metadata), mock.patch.object(
                runner, "_live_simulator_preflight", side_effect=preflight
            ), mock.patch.object(
                runner, "ui_methods", return_value=[*runner.LIVE_UI_METHODS, runner.LIVE_NORMAL_SETTINGS_METHOD]
            ), mock.patch.object(runner, "_run_live_ios_test", side_effect=ios_test):
                result = runner.live_repair_check(root, "a" * 40)
            snapshot = json.loads((root / runner.LIVE_REPAIR_SNAPSHOT).read_text(encoding="utf-8"))

        self.assertEqual(result[0]["name"], "live-repair-check")
        self.assertEqual(len(calls), 5)
        self.assertEqual(snapshot["status"], "failed")
        self.assertEqual(snapshot["failed"][0]["reason"], "command-nonzero")
        self.assertEqual(snapshot["failed"][0]["processExit"], 71)
        self.assertFalse(snapshot["releaseEvidence"])

    def test_live_repair_context_rejects_a_different_workflow_or_commit(self):
        expected_commit = "a" * 40
        environment = {
            "CM_BUILD_ID": "controlled-build", "CM_BUILD_DIR": str(ROOT),
            "CM_COMMIT": expected_commit, "CM_BRANCH": runner.LIVE_BRANCH,
            "CM_TRIGGER_SOURCE": "api", "CM_BUILD_STARTED_BY": "controlled-operator",
            runner.LIVE_WORKFLOW_ENVIRONMENT_KEY: runner.LIVE_REPAIR_WORKFLOW,
        }
        with tempfile.TemporaryDirectory() as directory, mock.patch.object(
            runner, "LIVE_ARTIFACT_ROOT", Path(directory) / "repair-artifacts"
        ), mock.patch.dict(os.environ, environment, clear=True):
            self.assertEqual(
                runner._live_execution_context(
                    runner.LIVE_ARTIFACT_ROOT, expected_commit, runner.LIVE_REPAIR_WORKFLOW
                )["workflow"], runner.LIVE_REPAIR_WORKFLOW
            )
            with mock.patch.dict(os.environ, {runner.LIVE_WORKFLOW_ENVIRONMENT_KEY: runner.LIVE_WORKFLOW}):
                with self.assertRaisesRegex(ValueError, "Codemagic live workflow context"):
                    runner._live_execution_context(
                        runner.LIVE_ARTIFACT_ROOT, expected_commit, runner.LIVE_REPAIR_WORKFLOW
                    )
            with mock.patch.dict(os.environ, {"CM_COMMIT": "b" * 40}):
                with self.assertRaisesRegex(ValueError, "Codemagic live workflow context"):
                    runner._live_execution_context(
                        runner.LIVE_ARTIFACT_ROOT, expected_commit, runner.LIVE_REPAIR_WORKFLOW
                    )

    def test_simulator_resolution_uses_existing_exact_device_ids(self):
        core_uuid = "11111111-1111-1111-1111-111111111111"
        max_uuid = "22222222-2222-2222-2222-222222222222"
        snapshot = self.simulator_snapshot([
            {"name": runner.IOS_CORE_DEVICE, "udid": core_uuid, "isAvailable": True, "deviceTypeIdentifier": "com.apple.CoreSimulator.SimDeviceType.iPhone-17"},
            {"name": "iPhone 17 Pro Max", "udid": max_uuid, "isAvailable": True, "deviceTypeIdentifier": "com.apple.CoreSimulator.SimDeviceType.iPhone-17-Pro-Max"},
        ])
        with mock.patch.object(runner, "_simctl_list", return_value=snapshot), mock.patch.object(runner, "_simctl_create") as create:
            destinations = runner.resolve_ios_destinations(runner.IOS_RELEASE_DEVICES)
        self.assertEqual(destinations[runner.IOS_CORE_DEVICE], f"platform=iOS Simulator,id={core_uuid}")
        self.assertEqual(destinations["iPhone 17 Pro Max"], f"platform=iOS Simulator,id={max_uuid}")
        create.assert_not_called()

    def test_missing_exact_device_fails_without_creation_by_default(self):
        core_uuid = "11111111-1111-1111-1111-111111111111"
        snapshot = self.simulator_snapshot([{
            "name": runner.IOS_CORE_DEVICE,
            "udid": core_uuid,
            "isAvailable": True,
            "deviceTypeIdentifier": "com.apple.CoreSimulator.SimDeviceType.iPhone-17",
        }])
        with mock.patch.object(runner, "_simctl_list", return_value=snapshot), mock.patch.object(
            runner, "_simctl_create"
        ) as create:
            with self.assertRaisesRegex(runner.SimulatorResolutionError, "creation is disabled"):
                runner.resolve_ios_destinations(runner.IOS_RELEASE_DEVICES)
        create.assert_not_called()

    def test_simulator_command_records_timing_argv_stdout_and_stderr(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "live"
            root.mkdir()
            completed = subprocess.CompletedProcess(
                ["xcrun", "simctl", "list", "-j"], 0, "simulator stdout", "simulator stderr"
            )
            with mock.patch.object(runner.subprocess, "run", return_value=completed), mock.patch.object(
                runner.time, "monotonic", side_effect=[10.0, 10.5]
            ):
                runner._run_simulator_command(
                    root, "diagnostic", ["xcrun", "simctl", "list", "-j"], 30
                )
            records = [json.loads(line) for line in (root / runner.SIMULATOR_RESOLUTION_LOG).read_text().splitlines()]
            self.assertEqual([record["event"] for record in records], ["started", "completed"])
            self.assertEqual(records[0]["argv"], ["xcrun", "simctl", "list", "-j"])
            self.assertEqual(records[0]["phase"], "diagnostic")
            self.assertEqual(records[1]["exitCode"], 0)
            self.assertEqual(records[1]["stdout"], "simulator stdout")
            self.assertEqual(records[1]["stderr"], "simulator stderr")
            self.assertEqual(records[1]["elapsedSeconds"], 0.5)

    def test_simulator_timeout_reports_exact_subcommand_and_retains_stderr(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "live"
            root.mkdir()
            timeout = subprocess.TimeoutExpired(
                ["xcrun", "simctl", "list", "-j"], 1, output="partial stdout", stderr="simctl stderr"
            )
            previous_root = runner._ACTIVE_SIMULATOR_LOG_ROOT
            runner._ACTIVE_SIMULATOR_LOG_ROOT = root
            try:
                with mock.patch.object(runner.subprocess, "run", side_effect=timeout):
                    with self.assertRaisesRegex(runner.SimulatorResolutionError, "simctl list -j timed out"):
                        runner._simctl_list(timeout=1)
            finally:
                runner._ACTIVE_SIMULATOR_LOG_ROOT = previous_root
            records = [json.loads(line) for line in (root / runner.SIMULATOR_RESOLUTION_LOG).read_text().splitlines()]
            self.assertEqual(records[-1]["event"], "timed-out")
            self.assertEqual(records[-1]["argv"], ["xcrun", "simctl", "list", "-j"])
            self.assertEqual(records[-1]["stderr"], "simctl stderr")

    def test_live_simctl_ui_uses_the_simulator_command_recorder(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "live"
            root.mkdir()
            log_path = root / "simctl-ui.log"
            previous_root = runner._ACTIVE_SIMULATOR_LOG_ROOT
            runner._ACTIVE_SIMULATOR_LOG_ROOT = root
            try:
                completed = subprocess.CompletedProcess(
                    ["xcrun", "simctl", "ui", "fixture", "appearance", "dark"],
                    0,
                    "dark",
                    "",
                )
                with mock.patch.object(runner, "_run_simulator_command", return_value=completed) as command:
                    result = runner._run_live_command(
                        "simctl-appearance-set",
                        completed.args,
                        runner.ROOT,
                        {},
                        log_path,
                    )
            finally:
                runner._ACTIVE_SIMULATOR_LOG_ROOT = previous_root
            command.assert_called_once_with(root, "live-simctl-appearance-set", completed.args, runner.LIVE_COMMAND_TIMEOUT_SECONDS)
            self.assertEqual(result[0], 0)
            self.assertEqual(log_path.read_text(encoding="utf-8"), "dark")

    def test_live_simulator_preflight_fails_when_required_device_type_is_absent(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "live"
            root.mkdir()
            def preflight(_root, phase, _command, _timeout):
                if phase == "preflight-simctl-list-runtimes":
                    return {"runtimes": [{"identifier": "com.apple.CoreSimulator.SimRuntime.iOS-26-4", "version": "26.4", "isAvailable": True}]}
                if phase == "preflight-simctl-list-devicetypes":
                    return {"devicetypes": [{"name": runner.IOS_CORE_DEVICE, "identifier": "core"}]}
                raise AssertionError(f"unexpected preflight phase {phase}")
            with mock.patch.object(runner.shutil, "which", return_value="controlled-tool"), mock.patch.object(
                runner, "_xcode_version", return_value=runner.CODEMAGIC_XCODE_VERSION
            ), mock.patch.object(runner, "_preflight_simctl_json", side_effect=preflight):
                with self.assertRaisesRegex(runner.SimulatorResolutionError, "exact device type is unavailable"):
                    runner._live_simulator_preflight(root)
            diagnostic = json.loads((root / "simulator-resolution.json").read_text(encoding="utf-8"))
            self.assertEqual(diagnostic["failure"]["reason"], runner.SIMULATOR_RESOLUTION_FAILURE_REASON)
            self.assertIn("exact iPhone 17", diagnostic["failure"]["action"])

    def test_live_simulator_preflight_records_supported_provider_capabilities(self):
        destinations = {
            runner.IOS_CORE_DEVICE: "platform=iOS Simulator,id=11111111-1111-1111-1111-111111111111",
            "iPhone 17 Pro Max": "platform=iOS Simulator,id=22222222-2222-2222-2222-222222222222",
        }

        def resolve(names, recorder=None, verification_seconds=None, require_ready=False, allow_create=False):
            self.assertEqual(names, runner.IOS_RELEASE_DEVICES)
            self.assertIsNotNone(recorder)
            self.assertTrue(require_ready)
            self.assertFalse(allow_create)
            recorder("selected-runtime", "com.apple.CoreSimulator.SimRuntime.iOS-26-4")
            recorder("device-types", {
                runner.IOS_CORE_DEVICE: "com.apple.CoreSimulator.SimDeviceType.iPhone-17",
                "iPhone 17 Pro Max": "com.apple.CoreSimulator.SimDeviceType.iPhone-17-Pro-Max",
            })
            recorder("resolved-destinations", destinations)
            return destinations

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "live"
            root.mkdir()
            environment_file = root / "cm-env"
            timeouts = []
            def preflight(_root, phase, _command, _timeout):
                timeouts.append(_timeout)
                if phase == "preflight-simctl-list-runtimes":
                    return {"runtimes": [{"identifier": "com.apple.CoreSimulator.SimRuntime.iOS-26-4", "version": "26.4", "isAvailable": True}]}
                if phase == "preflight-simctl-list-devicetypes":
                    return {"devicetypes": [
                        {"name": runner.IOS_CORE_DEVICE, "identifier": "com.apple.CoreSimulator.SimDeviceType.iPhone-17"},
                        {"name": "iPhone 17 Pro Max", "identifier": "com.apple.CoreSimulator.SimDeviceType.iPhone-17-Pro-Max"},
                    ]}
                if phase == "preflight-simctl-list-devices-available":
                    return {"devices": {"com.apple.CoreSimulator.SimRuntime.iOS-26-4": []}}
                raise AssertionError(f"unexpected preflight phase {phase}")
            with mock.patch.dict(os.environ, {"CM_ENV": str(environment_file)}, clear=False), mock.patch.object(runner.shutil, "which", return_value="controlled-tool"), mock.patch.object(
                runner, "_xcode_version", side_effect=lambda timeout, **_kwargs: (timeouts.append(timeout) or runner.CODEMAGIC_XCODE_VERSION)
            ), mock.patch.object(runner, "_preflight_simctl_json", side_effect=preflight), mock.patch.object(
                runner, "resolve_ios_destinations", side_effect=resolve
            ):
                result = runner._live_simulator_preflight(root)
            self.assertEqual(result, destinations)
            diagnostic = json.loads((root / "simulator-resolution.json").read_text(encoding="utf-8"))
            self.assertEqual(diagnostic["status"], "passed")
            self.assertEqual(diagnostic["xcode"]["version"], runner.CODEMAGIC_XCODE_VERSION)
            self.assertEqual(diagnostic["runtime"]["identifier"], "com.apple.CoreSimulator.SimRuntime.iOS-26-4")
            self.assertTrue(all(item["available"] and item["ready"] for item in diagnostic["devices"].values()))
            self.assertEqual(len(timeouts), 4)
            self.assertEqual(timeouts, sorted(timeouts, reverse=True))
            self.assertEqual(
                environment_file.read_text(encoding="utf-8").splitlines(),
                [
                    "ACE_IOS_CORE_SIMULATOR_UDID=11111111-1111-1111-1111-111111111111",
                    "ACE_IOS_PRO_MAX_SIMULATOR_UDID=22222222-2222-2222-2222-222222222222",
                ],
            )

    def test_live_simulator_preflight_records_actionable_version_failure(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "live"
            root.mkdir()
            with mock.patch.object(runner.shutil, "which", return_value="controlled-tool"), mock.patch.object(
                runner, "_xcode_version", return_value="26.5.0"
            ), self.assertRaisesRegex(runner.SimulatorResolutionError, "Xcode version"):
                runner._live_simulator_preflight(root)
            diagnostic = json.loads((root / "simulator-resolution.json").read_text(encoding="utf-8"))
            self.assertEqual(diagnostic["status"], "failed")
            self.assertEqual(diagnostic["xcode"]["version"], "26.5.0")
            self.assertIn("exact Xcode 26.4.1", diagnostic["failure"]["action"])

    def test_live_simulator_preflight_requires_codamagic_environment_file(self):
        with tempfile.TemporaryDirectory() as directory:
            environment = os.environ.copy()
            environment.pop("CM_ENV", None)
            with mock.patch.dict(os.environ, environment, clear=True):
                with self.assertRaisesRegex(runner.SimulatorResolutionError, "environment file"):
                    runner._write_simulator_environment({
                        runner.IOS_CORE_DEVICE: "platform=iOS Simulator,id=11111111-1111-1111-1111-111111111111",
                        "iPhone 17 Pro Max": "platform=iOS Simulator,id=22222222-2222-2222-2222-222222222222",
                    })

    def test_simulator_readiness_boots_each_verified_uuid_with_one_deadline(self):
        core_uuid = "11111111-1111-1111-1111-111111111111"
        snapshot = self.simulator_snapshot([{
            "name": runner.IOS_CORE_DEVICE, "udid": core_uuid, "isAvailable": True,
            "deviceTypeIdentifier": "com.apple.CoreSimulator.SimDeviceType.iPhone-17",
        }])
        completed = [
            subprocess.CompletedProcess([], 149, "already booted"),
            subprocess.CompletedProcess([], 0, "ready"),
        ]
        with mock.patch.object(runner, "_simctl_list", return_value=snapshot) as listing, mock.patch.object(
            runner.time, "monotonic", side_effect=[100, 101, 102, 103, 104, 105, 106, 107]
        ), mock.patch.object(runner.subprocess, "run", side_effect=completed) as command:
            destinations = runner.resolve_ios_destinations(
                (runner.IOS_CORE_DEVICE,), require_ready=True
            )
        self.assertEqual(destinations[runner.IOS_CORE_DEVICE], f"platform=iOS Simulator,id={core_uuid}")
        self.assertEqual(
            [call.args[0] for call in command.call_args_list],
            [["xcrun", "simctl", "boot", core_uuid], ["xcrun", "simctl", "bootstatus", core_uuid, "-b"]],
        )
        self.assertEqual(listing.call_args.kwargs["timeout"], 359)
        self.assertEqual([call.kwargs["timeout"] for call in command.call_args_list], [358, 355])

    def test_simulator_readiness_accepts_a_fresh_boot_before_bootstatus(self):
        core_uuid = "11111111-1111-1111-1111-111111111111"
        snapshot = self.simulator_snapshot([{
            "name": runner.IOS_CORE_DEVICE, "udid": core_uuid, "isAvailable": True,
            "deviceTypeIdentifier": "com.apple.CoreSimulator.SimDeviceType.iPhone-17",
        }])
        completed = [
            subprocess.CompletedProcess([], 0, "booted"),
            subprocess.CompletedProcess([], 0, "ready"),
        ]
        with mock.patch.object(runner, "_simctl_list", return_value=snapshot), mock.patch.object(
            runner.time, "monotonic", side_effect=[100, 101, 102, 103, 104, 105, 106, 107]
        ), mock.patch.object(runner.subprocess, "run", side_effect=completed) as command:
            destinations = runner.resolve_ios_destinations(
                (runner.IOS_CORE_DEVICE,), require_ready=True
            )
        self.assertEqual(destinations[runner.IOS_CORE_DEVICE], f"platform=iOS Simulator,id={core_uuid}")
        self.assertEqual(
            [call.args[0] for call in command.call_args_list],
            [["xcrun", "simctl", "boot", core_uuid], ["xcrun", "simctl", "bootstatus", core_uuid, "-b"]],
        )

    def test_simulator_readiness_bootstatus_failure_halts_before_live_tests(self):
        core_uuid = "11111111-1111-1111-1111-111111111111"
        snapshot = self.simulator_snapshot([{
            "name": runner.IOS_CORE_DEVICE, "udid": core_uuid, "isAvailable": True,
            "deviceTypeIdentifier": "com.apple.CoreSimulator.SimDeviceType.iPhone-17",
        }])
        with mock.patch.object(runner, "_simctl_list", return_value=snapshot), mock.patch.object(
            runner.subprocess, "run", side_effect=[
                subprocess.CompletedProcess([], 0, ""),
                subprocess.CompletedProcess([], 1, "private failure"),
            ]
        ), self.assertRaisesRegex(runner.SimulatorResolutionError, "bootstatus failed"):
            runner.resolve_ios_destinations((runner.IOS_CORE_DEVICE,), require_ready=True)

    def test_simulator_resolution_rejects_existing_exact_device_with_invalid_uuid(self):
        snapshot = self.simulator_snapshot([
            {
                "name": runner.IOS_CORE_DEVICE,
                "udid": "not-a-simulator-uuid",
                "isAvailable": True,
                "deviceTypeIdentifier": "com.apple.CoreSimulator.SimDeviceType.iPhone-17",
            },
        ])
        with mock.patch.object(runner, "_simctl_list", return_value=snapshot):
            with self.assertRaisesRegex(runner.SimulatorResolutionError, "simulator UUID is invalid"):
                runner.resolve_ios_destinations((runner.IOS_CORE_DEVICE,))

    def test_simulator_resolution_creates_and_verifies_missing_exact_device(self):
        created_uuid = "33333333-3333-3333-3333-333333333333"
        initial = self.simulator_snapshot([])
        resolved = self.simulator_snapshot([
            {"name": runner.IOS_CORE_DEVICE, "udid": created_uuid, "isAvailable": True, "deviceTypeIdentifier": "com.apple.CoreSimulator.SimDeviceType.iPhone-17"},
        ])
        with mock.patch.object(runner, "_simctl_list", side_effect=[initial, resolved]), mock.patch.object(runner, "_simctl_create", return_value=created_uuid) as create:
            destinations = runner.resolve_ios_destinations((runner.IOS_CORE_DEVICE,), allow_create=True)
        self.assertEqual(destinations[runner.IOS_CORE_DEVICE], f"platform=iOS Simulator,id={created_uuid}")
        create.assert_called_once_with(runner.IOS_CORE_DEVICE, "com.apple.CoreSimulator.SimDeviceType.iPhone-17", "com.apple.CoreSimulator.SimRuntime.iOS-26-1", timeout=mock.ANY)

    def test_simulator_creation_rejects_a_concurrent_exact_device(self):
        created_uuid = "cccccccc-cccc-cccc-cccc-cccccccccccc"
        concurrent_uuid = "dddddddd-dddd-dddd-dddd-dddddddddddd"
        initial = self.simulator_snapshot([])
        concurrent = self.simulator_snapshot([
            {"name": runner.IOS_CORE_DEVICE, "udid": created_uuid, "isAvailable": True, "deviceTypeIdentifier": "com.apple.CoreSimulator.SimDeviceType.iPhone-17"},
            {"name": runner.IOS_CORE_DEVICE, "udid": concurrent_uuid, "isAvailable": True, "deviceTypeIdentifier": "com.apple.CoreSimulator.SimDeviceType.iPhone-17"},
        ])
        with mock.patch.object(runner, "_simctl_list", side_effect=[initial, concurrent]), mock.patch.object(runner, "_simctl_create", return_value=created_uuid), mock.patch.object(runner.time, "monotonic", side_effect=[0, 0, 0, 0]):
            with self.assertRaisesRegex(runner.SimulatorResolutionError, "ambiguous"):
                runner.resolve_ios_destinations((runner.IOS_CORE_DEVICE,), allow_create=True)

    def test_simulator_resolution_rejects_device_without_type_identifier(self):
        core_uuid = "66666666-6666-6666-6666-666666666666"
        snapshot = self.simulator_snapshot([
            {"name": runner.IOS_CORE_DEVICE, "udid": core_uuid, "isAvailable": True},
        ])
        with mock.patch.object(runner, "_simctl_list", return_value=snapshot), mock.patch.object(runner, "_simctl_create", return_value=core_uuid), mock.patch.object(runner.time, "sleep"), mock.patch.object(runner.time, "monotonic", side_effect=[0, 0, 0, 0, 0, 180]):
            with self.assertRaisesRegex(runner.SimulatorResolutionError, "did not become available"):
                runner.resolve_ios_destinations((runner.IOS_CORE_DEVICE,), allow_create=True)

    def test_simulator_resolution_rejects_ambiguous_or_unverifiable_devices(self):
        snapshot = self.simulator_snapshot([
            {"name": runner.IOS_CORE_DEVICE, "udid": "44444444-4444-4444-4444-444444444444", "isAvailable": True, "deviceTypeIdentifier": "com.apple.CoreSimulator.SimDeviceType.iPhone-17"},
            {"name": runner.IOS_CORE_DEVICE, "udid": "55555555-5555-5555-5555-555555555555", "isAvailable": True, "deviceTypeIdentifier": "com.apple.CoreSimulator.SimDeviceType.iPhone-17"},
        ])
        with mock.patch.object(runner, "_simctl_list", return_value=snapshot):
            with self.assertRaisesRegex(runner.SimulatorResolutionError, "ambiguous"):
                runner.resolve_ios_destinations((runner.IOS_CORE_DEVICE,))

    def test_ios_component_fails_before_xcodebuild_when_resolution_fails(self):
        injected = "injected simulator error"
        with mock.patch.object(runner.shutil, "which", return_value="xcodebuild"), mock.patch.object(runner, "resolve_ios_destinations", side_effect=runner.SimulatorResolutionError(injected)), mock.patch.object(runner, "run_ios_test") as run_ios_test:
            checks = runner.component_checks("release", "ios")
        self.assertEqual(checks[0]["status"], "failed")
        self.assertEqual(checks[0]["reason"], runner.SIMULATOR_RESOLUTION_FAILURE_REASON)
        self.assertEqual(checks[0]["detail"], "simulator resolution failed")
        self.assertNotIn(injected, json.dumps(checks))
        run_ios_test.assert_not_called()

    def test_mapping_has_44_unique_known_ids_and_six_groups(self):
        mapping, errors = runner.load_mapping()
        self.assertEqual(errors, [])
        self.assertEqual(mapping["evidencePreflightState"], "pending-not-release-evidence")
        self.assertEqual(set(mapping["groups"]), {f"G{number}" for number in range(1, 7)})
        identifiers = [item for values in mapping["iosPrimaryGroups"].values() for item in values]
        self.assertEqual(len(identifiers), 44)
        self.assertEqual(len(identifiers), len(set(identifiers)))

    def test_reports_are_under_ignored_artifacts_directory(self):
        self.assertEqual(runner.REPORT_DIR.relative_to(ROOT), Path(".artifacts/tests"))

    def test_runner_uses_no_install_command(self):
        source = (ROOT / "tools" / "run_tests.py").read_text(encoding="utf-8")
        self.assertNotIn("pip", source)
        self.assertNotIn("npm install", source)

    def test_inventories_remain_separate(self):
        mapping = json.loads((ROOT / "quality" / "test-groups.json").read_text(encoding="utf-8"))
        self.assertEqual(set(mapping["inventories"]), {"python", "web", "ios"})

    def test_invalid_mapping_reports_missing_duplicate_and_unknown_ids(self):
        mapping = json.loads((ROOT / "quality" / "test-groups.json").read_text(encoding="utf-8"))
        mapping["iosPrimaryGroups"]["G2"].pop()
        mapping["iosPrimaryGroups"]["G1"].extend(["IOS-BASE-001", "IOS-UNKNOWN-999"])
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "groups.json"
            path.write_text(json.dumps(mapping), encoding="utf-8")
            original = runner.CONFIG
            runner.CONFIG = path
            try:
                _, errors = runner.load_mapping()
            finally:
                runner.CONFIG = original
        self.assertTrue(any("duplicate" in item for item in errors))
        self.assertTrue(any("missing" in item for item in errors))
        self.assertTrue(any("unknown" in item for item in errors))

    def test_reviewed_public_evidence_is_rejected_before_artifact_acceptance(self):
        plan, register = self.controlled_evidence_fixture()
        plan["entries"] = [plan["entries"][0]]
        plan["packageMappings"] = [plan["packageMappings"][0]]
        register["packages"] = [register["packages"][0]]
        register["packages"][0]["status"] = "reviewed"
        register["results"] = {
            "IOS-BASE-001": {
                "status": "reviewed",
                "result": {
                    **{field: "value" for field in runner.EVIDENCE_RESULT_FIELDS},
                    "package": "P01",
                    "entry": "IOS-BASE-001",
                },
            }
        }
        errors, state = self.validate_fixture(plan, register)
        self.assertEqual(state, "invalid")
        self.assertTrue(any("pending" in error or "invalid" in error for error in errors))

    def test_reviewed_public_evidence_is_rejected_before_package_and_entry_acceptance(self):
        plan, register = self.controlled_evidence_fixture()
        plan["entries"] = [plan["entries"][0]]
        plan["packageMappings"] = [plan["packageMappings"][0]]
        register["packages"] = [register["packages"][0]]
        register["packages"][0]["status"] = "reviewed"
        register["results"] = {
            "IOS-BASE-001": {
                "status": "reviewed",
                "result": {
                    **{field: "value" for field in runner.EVIDENCE_RESULT_FIELDS},
                    "package": "P99",
                    "entry": "IOS-TEST-999",
                },
            }
        }
        errors, state = self.validate_fixture(plan, register)
        self.assertEqual(state, "invalid")
        self.assertTrue(any("pending" in error or "invalid" in error for error in errors))

    def test_reviewed_field_contract_includes_operator_date_and_result(self):
        expected = (
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
        plan, register = self.controlled_evidence_fixture()
        self.assertEqual(runner.ACTIVE_RECORD_REVIEWED_FIELDS, expected)
        self.assertEqual(
            plan["activeRecordRequirements"]["reviewedRecordFields"], list(expected)
        )
        self.assertEqual(
            register["activeRecordRequirements"]["reviewedRecordFields"], list(expected)
        )
        self.assertEqual(plan["resultFieldSchema"], list(runner.EVIDENCE_RESULT_FIELDS))
        self.assertEqual(register["resultFieldSchema"], list(runner.EVIDENCE_RESULT_FIELDS))

    def test_reviewed_public_evidence_rejects_a_missing_required_result_field(self):
        plan, register = self.controlled_evidence_fixture()
        plan["entries"] = [plan["entries"][0]]
        plan["packageMappings"] = [plan["packageMappings"][0]]
        register["packages"] = [register["packages"][0]]
        register["packages"][0]["status"] = "reviewed"
        result = {field: "value" for field in runner.EVIDENCE_RESULT_FIELDS}
        del result["operator"]
        register["results"] = {
            "IOS-BASE-001": {"status": "reviewed", "result": result}
        }
        errors, state = self.validate_fixture(plan, register)
        self.assertEqual(state, "invalid")
        self.assertIn(
            "IOS-BASE-001: public evidence status or result is invalid", errors
        )

    def test_reviewed_public_evidence_rejects_blank_required_result_values(self):
        for field in ("operator", "date", "result"):
            with self.subTest(field=field):
                plan, register = self.controlled_evidence_fixture()
                plan["entries"] = [plan["entries"][0]]
                plan["packageMappings"] = [plan["packageMappings"][0]]
                register["packages"] = [register["packages"][0]]
                register["packages"][0]["status"] = "reviewed"
                result = {
                    required_field: "value"
                    for required_field in runner.EVIDENCE_RESULT_FIELDS
                }
                result[field] = " "
                register["results"] = {
                    "IOS-BASE-001": {"status": "reviewed", "result": result}
                }
                errors, state = self.validate_fixture(plan, register)
                self.assertEqual(state, "invalid")
                self.assertIn(
                    "IOS-BASE-001: public evidence status or result is invalid", errors
                )

    def test_ios_core_commands_use_controlled_fictional_inputs(self):
        destinations = {runner.IOS_CORE_DEVICE: "platform=iOS Simulator,id=11111111-1111-1111-1111-111111111111"}
        with mock.patch.object(runner.shutil, "which", return_value="xcodebuild"), mock.patch.object(runner, "resolve_ios_destinations", return_value=destinations), mock.patch.object(runner, "run_ios_test", return_value={"status": "passed"}) as run_ios_test:
            runner.component_checks("core", "ios")
        self.assertEqual(run_ios_test.call_count, 7)
        for call in run_ios_test.call_args_list:
            if call.args[0].startswith("ios-core-ui-"):
                self.assertEqual(call.args[3]["ACE_UI_TEST_APPEARANCE"], "light")
                self.assertIn("ACE_UI_TEST_APPEARANCE=light", call.args[1])
            else:
                self.assertEqual(call.args[3], runner.IOS_TEST_ENVIRONMENT)
        ui_calls = [call for call in run_ios_test.call_args_list if call.args[0].startswith("ios-core-ui-")]
        self.assertTrue(all("ACEClientAppUITests" in call.args[1] for call in ui_calls))
        self.assertTrue(all("Debug" in call.args[1] for call in ui_calls))

    def test_simulator_poll_uses_the_remaining_monotonic_deadline(self):
        created_uuid = "77777777-7777-7777-7777-777777777777"
        initial = self.simulator_snapshot([])
        resolved = self.simulator_snapshot([
            {"name": runner.IOS_CORE_DEVICE, "udid": created_uuid, "isAvailable": True, "deviceTypeIdentifier": "com.apple.CoreSimulator.SimDeviceType.iPhone-17"},
        ])
        with mock.patch.object(runner, "_simctl_list", side_effect=[initial, resolved]) as listing, mock.patch.object(runner, "_simctl_create", return_value=created_uuid), mock.patch.object(runner.time, "monotonic", side_effect=[100, 100, 100, 100]):
            runner.resolve_ios_destinations((runner.IOS_CORE_DEVICE,), allow_create=True)
        self.assertEqual(runner.SIMULATOR_VERIFICATION_SECONDS, 360)
        self.assertEqual(runner.LIVE_COMMAND_TIMEOUT_SECONDS, 600)
        self.assertLess(
            runner.SIMULATOR_VERIFICATION_SECONDS,
            runner.LIVE_COMMAND_TIMEOUT_SECONDS,
        )
        self.assertEqual(listing.call_args_list[0].kwargs["timeout"], 360)
        self.assertEqual(listing.call_args_list[1].kwargs["timeout"], 360)

    def test_register_package_mapping_must_match_the_independent_plan_mapping(self):
        plan, register = self.controlled_evidence_fixture()
        register["packages"][0]["identifiers"], register["packages"][1]["identifiers"] = (
            register["packages"][1]["identifiers"],
            register["packages"][0]["identifiers"],
        )
        errors, state = self.validate_fixture(plan, register)
        self.assertEqual(state, "invalid")
        self.assertIn(
            "controlled public evidence package mappings do not match the runtime plan",
            errors,
        )

    def test_public_evidence_schemas_reject_extra_claims_and_non_pending_statuses(self):
        cases = (
            ("plan", lambda plan, register: plan.update({"releaseApproval": "approved"})),
            ("register", lambda plan, register: register.update({"approval": "approved"})),
            ("package", lambda plan, register: register["packages"][0].update({"release": "approved"})),
            ("entry", lambda plan, register: plan["entries"][0].update({"approval": "approved"})),
            ("record", lambda plan, register: register["results"]["IOS-BASE-001"].update({"release": "approved"})),
            ("result", lambda plan, register: register["results"]["IOS-BASE-001"]["result"].update({"approval": "approved"})),
            ("plan status", lambda plan, register: plan.update({"status": "reviewed"})),
            ("register status", lambda plan, register: register.update({"status": "reviewed"})),
            ("entry status", lambda plan, register: plan["entries"][0].update({"status": "reviewed"})),
            ("package reviewed status", lambda plan, register: register["packages"][0].update({"status": "reviewed"})),
            ("package status", lambda plan, register: register["packages"][0].update({"status": "approved"})),
            ("record reviewed status", lambda plan, register: register["results"]["IOS-BASE-001"].update({"status": "reviewed"})),
            ("record status", lambda plan, register: register["results"]["IOS-BASE-001"].update({"status": "approved"})),
        )
        for name, mutate in cases:
            with self.subTest(name=name):
                plan, register = self.controlled_evidence_fixture()
                mutate(plan, register)
                errors, state = self.validate_fixture(plan, register)
                self.assertEqual(state, "invalid")
                self.assertTrue(any("invalid" in error or "status" in error for error in errors))

    def test_live_codemagic_workflow_is_manual_only_and_uses_one_exact_command(self):
        config = (ROOT / "codemagic.yaml").read_text(encoding="utf-8")
        workflow = config.split("  ace-ios-live-evidence-manual:\n", 1)[1]
        self.assertNotIn("triggering:", workflow)
        self.assertIn("max_build_duration: 60", workflow)
        self.assertIn("instance_type: mac_mini_m2", workflow)
        self.assertIn("groups:\n        - mcx19_live_evidence", workflow)
        self.assertEqual(workflow.count("mcx19_live_evidence"), 1)
        self.assertIn("ACE_LIVE_EVIDENCE_WORKFLOW: ace-ios-live-evidence-manual", workflow)
        self.assertIn("ACE_LIVE_EVIDENCE_APPROVED_COMMIT", workflow)
        self.assertIn(
            "python3 tools/run_tests.py live-evidence --component ios --artifact-root /private/tmp/mcx-19-live-evidence --expected-commit \"$ACE_LIVE_EVIDENCE_APPROVED_COMMIT\"",
            workflow,
        )
        self.assertNotIn("push", workflow)
        self.assertNotIn("pull_request", workflow)
        self.assertEqual(workflow.split("    artifacts:\n", 1)[1].strip(),
                         "- /private/tmp/mcx-19-live-evidence/live-evidence-progress.json\n      - /private/tmp/mcx-19-live-evidence/simulator-resolution.json\n      - /private/tmp/mcx-19-live-evidence/simulator-resolution.log\n      - /private/tmp/mcx-19-live-evidence/*.log\n      - /private/tmp/mcx-19-live-evidence/*-summary.json\n      - /private/tmp/mcx-19-live-evidence/diagnostic-images/**/*.png\n      - /private/tmp/mcx-19-live-evidence/review-artifacts/live-evidence-review-manifest.json\n      - /private/tmp/mcx-19-live-evidence/review-artifacts/screenshots/**/*.png\n      - /private/tmp/mcx-19-full-matrix-private/mcx19-full-matrix-records.tar.gz")
        owned_paths = (
            "codemagic.yaml",
            "tools/run_tests.py",
            "tests/test_run_tests.py",
            "ios/ACEClientApp/RuntimeEvidencePlan.json",
            "ios/ACEClientApp/RuntimeEvidencePlan.md",
            "ios/ACEClientApp/Phase6_1EvidenceRegister.json",
            "ios/ACEClientApp/Phase6_1EvidenceRegister.md",
            "ios/ACEClientApp/evidence-matrix-audit.md",
        )
        owned_source = "\n".join(
            (ROOT / path).read_text(encoding="utf-8") for path in owned_paths
        )
        self.assertIn("/private/tmp/mcx-19-live-evidence", owned_source)
        obsolete_path = "/" + "tmp/mcx-19-live-evidence"
        self.assertIsNone(
            runner.re.search(r"(?<!/private)" + runner.re.escape(obsolete_path), owned_source)
        )

    def test_live_repair_check_codemagic_workflow_is_manual_and_has_fixed_artifacts(self):
        config = (ROOT / "codemagic.yaml").read_text(encoding="utf-8")
        workflow = config.split("  ace-ios-repair-check-manual:\n", 1)[1].split(
            "  ace-ios-live-evidence-manual:\n", 1
        )[0]
        self.assertNotIn("triggering:", workflow)
        self.assertIn("max_build_duration: 15", workflow)
        self.assertIn("instance_type: mac_mini_m2", workflow)
        self.assertEqual(workflow.count("mcx19_live_evidence"), 1)
        self.assertIn("xcode: 26.4.1", workflow)
        self.assertIn(
            "ACE_LIVE_EVIDENCE_WORKFLOW: ace-ios-repair-check-manual", workflow
        )
        self.assertIn(
            'python3 tools/run_tests.py live-repair-check --component ios --artifact-root /private/tmp/mcx-19-live-evidence --expected-commit "$ACE_LIVE_EVIDENCE_APPROVED_COMMIT"',
            workflow,
        )
        self.assertEqual(workflow.split("    artifacts:\n", 1)[1].strip(),
                         "- /private/tmp/mcx-19-live-evidence/repair-check.json\n      - /private/tmp/mcx-19-live-evidence/simulator-resolution.json\n      - /private/tmp/mcx-19-live-evidence/simulator-resolution.log\n      - /private/tmp/mcx-19-live-evidence/*.log\n      - /private/tmp/mcx-19-live-evidence/*-summary.json\n      - /private/tmp/mcx-19-live-evidence/diagnostic-images/**/*.png")

    def test_public_evidence_schemas_reject_noncanonical_value_types(self):
        cases = (
            ("plan result field schema", lambda plan, register: plan.update({"resultFieldSchema": "repository"})),
            ("register result field schema", lambda plan, register: register.update({"resultFieldSchema": "repository"})),
            ("plan reviewed fields", lambda plan, register: plan["activeRecordRequirements"].update({"reviewedRecordFields": "repository"})),
            ("register reviewed fields", lambda plan, register: register["activeRecordRequirements"].update({"reviewedRecordFields": "repository"})),
            ("reviewed fields list", lambda plan, register: plan["activeRecordRequirements"].update({"reviewedRecordFields": ["repository"]})),
            ("entry identifiers type", lambda plan, register: plan["entries"][0].update({"identifiers": [1]})),
            ("entry identifiers duplicate", lambda plan, register: plan["entries"][0].update({"identifiers": ["IOS-BASE-001", "IOS-BASE-001"]})),
            ("entry stage", lambda plan, register: plan["entries"][0].update({"stage": 1})),
            ("entry device", lambda plan, register: plan["entries"][0].update({"device": []})),
            ("entry procedure", lambda plan, register: plan["entries"][0].update({"procedure": None})),
            ("entry expected result", lambda plan, register: plan["entries"][0].update({"expectedResult": ""})),
            ("plan simulator targets", lambda plan, register: plan["controlledRegister"]["simulatorProvisioning"].update({"exactTargets": "iPhone 17"})),
            ("register simulator targets", lambda plan, register: register["simulatorProvisioning"].update({"exactTargets": "iPhone 17"})),
            ("simulator target list", lambda plan, register: plan["controlledRegister"]["simulatorProvisioning"].update({"exactTargets": [runner.IOS_CORE_DEVICE, runner.IOS_CORE_DEVICE]})),
            ("simulator runtime", lambda plan, register: plan["controlledRegister"]["simulatorProvisioning"].update({"runtime": 1})),
            ("simulator procedure", lambda plan, register: plan["controlledRegister"]["simulatorProvisioning"].update({"procedure": []})),
            ("simulator failure", lambda plan, register: plan["controlledRegister"]["simulatorProvisioning"].update({"failure": None})),
            ("historical note", lambda plan, register: plan["controlledRegister"]["historicalCommitChain"].update({"note": 1})),
            ("package name", lambda plan, register: register["packages"][0].update({"name": {}})),
        )
        for name, mutate in cases:
            with self.subTest(name=name):
                plan, register = self.controlled_evidence_fixture()
                mutate(plan, register)
                errors, state = self.validate_fixture(plan, register)
                self.assertEqual(state, "invalid")
                self.assertTrue(any("invalid" in error for error in errors))

    def test_simulator_creation_uses_the_remaining_monotonic_deadline(self):
        created_uuid = "88888888-8888-8888-8888-888888888888"
        initial = self.simulator_snapshot([])
        resolved = self.simulator_snapshot([
            {"name": runner.IOS_CORE_DEVICE, "udid": created_uuid, "isAvailable": True, "deviceTypeIdentifier": "com.apple.CoreSimulator.SimDeviceType.iPhone-17"},
        ])
        with mock.patch.object(runner, "_simctl_list", side_effect=[initial, resolved]), mock.patch.object(runner, "_simctl_create", return_value=created_uuid) as create, mock.patch.object(runner.time, "monotonic", side_effect=[100, 100, 105, 105]):
            runner.resolve_ios_destinations((runner.IOS_CORE_DEVICE,), allow_create=True)
        self.assertEqual(create.call_args.kwargs["timeout"], 355)

        with mock.patch.object(runner, "_simctl_list", return_value=initial), mock.patch.object(runner, "_simctl_create") as create, mock.patch.object(runner.time, "monotonic", side_effect=[100, 100, 460]):
            with self.assertRaisesRegex(runner.SimulatorResolutionError, "create has no verification time remaining"):
                runner.resolve_ios_destinations((runner.IOS_CORE_DEVICE,), allow_create=True)
        create.assert_not_called()

    def test_ios_release_matrix_uses_appearance_and_expected_rejection(self):
        destinations = {name: f"platform=iOS Simulator,id={number * 11111111:08d}-1111-1111-1111-111111111111" for number, name in enumerate(runner.IOS_RELEASE_DEVICES, 1)}
        with mock.patch.object(runner.shutil, "which", return_value="xcodebuild"), mock.patch.object(runner, "resolve_ios_destinations", return_value=destinations), mock.patch.object(runner, "run_ios_test", return_value={"status": "passed"}) as run_ios_test, mock.patch.object(runner, "run_command", return_value={"status": "passed"}) as run_command:
            runner.component_checks("release", "ios")
        calls = run_ios_test.call_args_list
        release_calls = [call for call in calls if call.args[0].startswith("ios-release-")]
        self.assertEqual(len(release_calls), 24)
        self.assertEqual(sum(call.args[3].get("ACE_UI_TEST_APPEARANCE") == "light" for call in release_calls), 12)
        self.assertEqual(sum(call.args[3].get("ACE_UI_TEST_APPEARANCE") == "dark" for call in release_calls), 12)
        self.assertTrue(all(any(argument == f"ACE_UI_TEST_APPEARANCE={call.args[3]['ACE_UI_TEST_APPEARANCE']}" for argument in call.args[1]) for call in release_calls))
        self.assertTrue(all("ACEClientAppUITests" in call.args[1] for call in release_calls))
        negative = next(
            call
            for call in run_command.call_args_list
            if call.args[0] == "ios-negative-config"
        )
        self.assertEqual(negative.kwargs["environment"], runner.NEGATIVE_CONFIG_ENVIRONMENT)
        self.assertEqual(negative.kwargs["expected_failure"], runner.NEGATIVE_CONFIG_REJECTION)
        self.assertEqual(negative.args[1], runner.ios_negative_configuration_command())

    def test_ui_runner_receives_appearance_without_conflicting_scheme_macro(self):
        scheme = (ROOT / "ios/ACEClientApp/ACEClientApp.xcodeproj/xcshareddata/xcschemes/ACEClientAppUITests.xcscheme").read_text(encoding="utf-8")
        self.assertNotIn('key="ACE_UI_TEST_APPEARANCE"', scheme)
        self.assertIn('<TestAction buildConfiguration="Debug"', scheme)
        for appearance in ("light", "dark"):
            environment = runner.ios_test_environment(appearance)
            self.assertEqual(environment["TEST_RUNNER_ACE_UI_TEST_APPEARANCE"], appearance)
            self.assertEqual(runner._live_command_environment(environment)["TEST_RUNNER_ACE_UI_TEST_APPEARANCE"], appearance)
        with self.assertRaises(ValueError):
            runner._live_command_environment({"TEST_RUNNER_UNAPPROVED": "blocked"})

    def test_appearance_indicator_reads_the_window_view_environment(self):
        source = (ROOT / "ios/ACEClientApp/ACEClientApp/ACEClientAppApp.swift").read_text(encoding="utf-8")
        app, indicator = source.split("private struct EffectiveInterfaceStyleIndicator: View {", 1)
        indicator = indicator.split("@MainActor", 1)[0]
        self.assertNotIn("@Environment", app)
        self.assertIn("EffectiveInterfaceStyleIndicator()", app.split("WindowGroup {", 1)[1])
        self.assertIn(r"@Environment(\.colorScheme)", indicator)
        self.assertIn('Text(colorScheme == .dark ? "dark" : "light")', indicator)
        self.assertNotIn("ProcessInfo", indicator)
        self.assertIn(".preferredColorScheme(uiTestColorScheme)", app)
        override = app.split("#if DEBUG", 1)[1].split("#endif", 1)[0]
        self.assertIn("guard UITestScenario.current != nil else { return nil }", override)
        self.assertIn('case "light": return .light', override)
        self.assertIn('case "dark": return .dark', override)
        self.assertIn('default: return nil', override)
        ui_test = (ROOT / "ios/ACEClientApp/ACEClientAppUITests/ACEClientAppUITests.swift").read_text(encoding="utf-8")
        launch = ui_test.split("private func launch(", 1)[1].split("private func launchWithNormalDeviceSettings", 1)[0]
        self.assertNotIn("XCTAssert", launch)
        self.assertNotIn("AppleInterfaceStyle", ui_test)
        appearance_test = ui_test.split("func testBothAppearances", 1)[1].split("func testLaunch", 1)[0]
        self.assertIn('for appearance in ["light", "dark"]', appearance_test)
        self.assertIn('app.terminate()', appearance_test)
        self.assertIn('indicator.waitForExistence(timeout: 5)', appearance_test)
        self.assertIn('NSPredicate(format: "label == %@", appearance), object: indicator', appearance_test)
        self.assertIn('XCTWaiter.wait(for: [displayedAppearance], timeout: 5)', appearance_test)
        self.assertIn('testBothAppearances', runner.LIVE_UI_METHODS)
        self.assertIn('func testNormalDeviceSettings()', ui_test)
        self.assertNotIn('ACE_UI_TEST_APPEARANCE"] =', ui_test.split("private func launchWithNormalDeviceSettings", 1)[1].split("func testBothAppearances", 1)[0])
        self.assertEqual(runner.LIVE_FAILURE_SUMMARY_MAX_ITEMS, 31)

    def test_negative_command_is_unsigned_simulator_and_keeps_invalid_inputs(self):
        command = runner.ios_negative_configuration_command()
        self.assertEqual(command[command.index("-sdk") + 1], "iphonesimulator")
        self.assertEqual(command[command.index("-destination") + 1], "generic/platform=iOS Simulator")
        self.assertIn("CODE_SIGNING_ALLOWED=NO", command)
        self.assertIn("ACE_PREVIEW_ORIGIN=http://invalid.example.invalid", command)
        self.assertNotIn("-allowProvisioningUpdates", command)

    def test_make_ui_test_sets_an_overridable_light_appearance(self):
        makefile = (ROOT / "ios/ACEClientApp/Makefile").read_text(encoding="utf-8")
        ui_test_target = makefile.split("ui-test:", 1)[1].split(
            "# Remove derived data.", 1
        )[0]
        self.assertIn("UI_TEST_APPEARANCE ?= light", makefile)
        self.assertIn('TEST_RUNNER_ACE_UI_TEST_APPEARANCE="$(UI_TEST_APPEARANCE)" xcodebuild test', ui_test_target)
        self.assertIn(
            "ACE_UI_TEST_APPEARANCE=$(UI_TEST_APPEARANCE)", ui_test_target
        )

    def test_make_ui_test_uses_the_strict_core_simulator_resolver(self):
        makefile = (ROOT / "ios/ACEClientApp/Makefile").read_text(encoding="utf-8")
        ui_test_target = makefile.split("ui-test:", 1)[1].split(
            "# Remove derived data.", 1
        )[0]
        resolver_call = (
            "from tools.run_tests import IOS_CORE_DEVICE, resolve_ios_destinations; "
            "print(resolve_ios_destinations((IOS_CORE_DEVICE,))[IOS_CORE_DEVICE])"
        )
        self.assertIn(resolver_call, ui_test_target)
        self.assertIn("PYTHONPATH=../..", ui_test_target)
        self.assertNotIn("$(CURDIR)", ui_test_target)
        self.assertNotIn("xcrun simctl list devices available", ui_test_target)
        self.assertIn('-destination "$$SIM_DEST"', ui_test_target)
        self.assertLess(
            ui_test_target.index("resolve_ios_destinations"),
            ui_test_target.index("xcodebuild test"),
        )

    def test_make_ui_test_executes_the_resolver_command_path_and_fails_closed(self):
        if os.name == "nt":
            self.skipTest("the ui-test command-path test requires a Unix shell")
        make = shutil.which("make")
        if make is None:
            self.fail("make is required for the ui-test command-path test")

        simulator_uuid = "11111111-1111-1111-1111-111111111111"
        destination = f"platform=iOS Simulator,id={simulator_uuid.upper()}"
        runtime = "com.apple.CoreSimulator.SimRuntime.iOS-26-1"
        device_type = "com.apple.CoreSimulator.SimDeviceType.iPhone-17"
        simulator_snapshot = {
            "runtimes": [
                {
                    "identifier": runtime,
                    "version": "26.1",
                    "isAvailable": True,
                }
            ],
            "devicetypes": [
                {"name": runner.IOS_CORE_DEVICE, "identifier": device_type}
            ],
            "devices": {
                runtime: [
                    {
                        "name": runner.IOS_CORE_DEVICE,
                        "udid": simulator_uuid,
                        "isAvailable": True,
                        "deviceTypeIdentifier": device_type,
                    }
                ]
            },
        }
        app_directory = ROOT / "ios" / "ACEClientApp"
        with tempfile.TemporaryDirectory() as directory:
            temporary = Path(directory)
            command_directory = temporary / "commands"
            command_directory.mkdir()
            python_command = command_directory / "python3"
            python_command.write_text(
                "#!/bin/sh\n"
                "if [ \"$1\" != -c ]; then\n"
                "  echo 'unexpected python3 command' >&2\n"
                "  exit 41\n"
                "fi\n"
                "case \"$2\" in\n"
                "  *\"from tools.run_tests import IOS_CORE_DEVICE, resolve_ios_destinations\"*) ;;\n"
                "  *) echo 'unexpected resolver command' >&2; exit 41 ;;\n"
                "esac\n"
                "exec \"$FAKE_TEST_PYTHON\" \"$@\"\n",
                encoding="utf-8",
            )
            xcrun_command = command_directory / "xcrun"
            xcrun_command.write_text(
                "#!/bin/sh\n"
                "if [ \"$1\" != simctl ] || [ \"$2\" != list ] || [ \"$3\" != -j ]; then\n"
                "  echo 'unexpected xcrun command' >&2\n"
                "  exit 42\n"
                "fi\n"
                "if [ \"$FAKE_XCRUN_MODE\" = fail ]; then\n"
                "  echo 'controlled resolver failure' >&2\n"
                "  exit 17\n"
                "fi\n"
                "printf '%s\\n' \"$FAKE_SIMCTL_SNAPSHOT\"\n",
                encoding="utf-8",
            )
            xcodebuild_command = command_directory / "xcodebuild"
            xcodebuild_command.write_text(
                "#!/bin/sh\n"
                "printf '%s\\n' \"$@\" > \"$FAKE_XCODEBUILD_LOG\"\n",
                encoding="utf-8",
            )
            python_command.chmod(python_command.stat().st_mode | 0o111)
            xcrun_command.chmod(xcrun_command.stat().st_mode | 0o111)
            xcodebuild_command.chmod(xcodebuild_command.stat().st_mode | 0o111)

            log_path = temporary / "xcodebuild-arguments.txt"
            environment = os.environ | {
                "PATH": str(command_directory) + os.pathsep + os.environ["PATH"],
                "FAKE_TEST_PYTHON": sys.executable,
                "FAKE_SIMCTL_SNAPSHOT": json.dumps(simulator_snapshot),
                "FAKE_XCODEBUILD_LOG": str(log_path),
            }
            success = subprocess.run(
                [make, "ui-test"],
                cwd=app_directory,
                env=environment,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(success.returncode, 0, success.stderr)
            arguments = log_path.read_text(encoding="utf-8").splitlines()
            self.assertEqual(arguments[arguments.index("-destination") + 1], destination)

            log_path.unlink()
            failure = subprocess.run(
                [make, "ui-test"],
                cwd=app_directory,
                env=environment | {"FAKE_XCRUN_MODE": "fail"},
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertNotEqual(failure.returncode, 0)
            self.assertIn("controlled resolver failure", failure.stderr)
            self.assertFalse(log_path.exists())

    def test_xcresult_counts_fail_closed_when_summary_is_missing_or_wrong(self):
        self.assertIsNone(runner._xcresult_counts({}))
        self.assertEqual(
            runner._xcresult_counts({"passedTests": 4, "failedTests": 1, "skippedTests": 2}),
            (4, 1, 2),
        )

    def test_xcresult_command_uses_xcode_26_summary_syntax_and_rejects_skips(self):
        responses = [
            {"name": "ios", "status": "passed", "exit": 0, "detail": ""},
            {"name": "summary", "status": "passed", "exit": 0, "detail": '{"passedTests": 2, "failedTests": 0, "skippedTests": 1}'},
        ]
        with mock.patch.object(runner.shutil, "which", return_value="xcrun"), mock.patch.object(runner, "run_command", side_effect=responses) as command:
            result = runner.run_ios_test("ios", ["xcodebuild", "test"], ROOT, {}, 2)
        summary_command = command.call_args_list[1].args[1]
        self.assertEqual(summary_command[:5], ["xcrun", "xcresulttool", "get", "test-results", "summary"])
        self.assertNotIn("--format", summary_command)
        self.assertEqual(result["status"], "failed")
        self.assertIn("skipped 1", result["detail"])

    def test_expected_failure_requires_rejection_text_and_nonzero_exit(self):
        cases = [(1, runner.NEGATIVE_CONFIG_REJECTION, "passed", 0), (0, runner.NEGATIVE_CONFIG_REJECTION, "failed", 1), (1, "different error", "failed", 1)]
        with mock.patch.object(runner.shutil, "which", return_value="xcodebuild"):
            for returncode, output, status, exit_code in cases:
                with self.subTest(returncode=returncode, output=output), mock.patch.object(runner.subprocess, "run", return_value=__import__("subprocess").CompletedProcess([], returncode, output)):
                    result = runner.run_command("negative", ["xcodebuild"], ROOT, expected_failure=runner.NEGATIVE_CONFIG_REJECTION)
                self.assertEqual(result["status"], status)
                self.assertEqual(result["exit"], exit_code)

    def test_normal_settings_keeps_test_outcome_when_restore_fails(self):
        settings = {"appearance": "light", "content_size": "large"}
        name = f"ios-normal-settings-{runner.IOS_CORE_DEVICE}-dark"

        def setting(root, identifier, key, value=None, query_evidence=None):
            if value is None:
                return True, settings[key]
            if key == "appearance" and value == "light":
                return False, None
            settings[key] = value
            return True, value

        native = {"name": name, "exit": 0, "process_exit": 0, "screenshots": []}
        with tempfile.TemporaryDirectory() as directory, mock.patch.object(
            runner, "_simctl_ui_value", side_effect=setting
        ), mock.patch.object(runner, "_run_live_ios_test", return_value=native):
            result = runner._normal_settings_result(
                name, ["xcodebuild", "test"], ROOT,
                runner.ios_normal_settings_environment("dark"), Path(directory),
                "11111111-1111-1111-1111-111111111111", "dark",
            )
        published = runner._published_live_result(result)
        self.assertEqual(published["exit"], 1)
        self.assertEqual(published["reason"], "simulator-setting-restore-failed")
        self.assertEqual(published["processExit"], 0)
        self.assertEqual(published["checkExitBeforeRestore"], 0)
        self.assertEqual(published["simulatorSettings"]["appearanceObserved"], "dark")
        self.assertEqual(published["simulatorSettings"]["contentSizeObserved"], runner.LIVE_CONTENT_SIZE)
        self.assertEqual(published["simulatorSettings"]["contentSizeRestored"], "large")

    def test_normal_settings_rejects_successful_set_without_matching_readback(self):
        def unchanged_setting(root, identifier, key, value=None, query_evidence=None):
            return True, value if value is not None else {"appearance": "light", "content_size": "large"}[key]

        with tempfile.TemporaryDirectory() as directory, mock.patch.object(
            runner, "_simctl_ui_value", side_effect=unchanged_setting
        ), mock.patch.object(runner, "_run_live_ios_test") as native:
            result = runner._normal_settings_result(
                f"ios-normal-settings-{runner.IOS_CORE_DEVICE}-dark", ["xcodebuild"], ROOT,
                runner.ios_normal_settings_environment("dark"), Path(directory),
                "11111111-1111-1111-1111-111111111111", "dark",
            )
        native.assert_not_called()
        self.assertEqual(result["reason"], "simulator-setting-set-failed")

    def test_normal_settings_restores_both_values_when_native_command_raises(self):
        original = {"appearance": "light", "content_size": "large"}
        settings = dict(original)

        def setting(root, identifier, key, value=None, query_evidence=None):
            if value is not None:
                settings[key] = value
            return True, settings[key]

        with tempfile.TemporaryDirectory() as directory, mock.patch.object(
            runner, "_simctl_ui_value", side_effect=setting
        ), mock.patch.object(runner, "_run_live_ios_test", side_effect=OSError("controlled")):
            with self.assertRaises(OSError):
                runner._normal_settings_result(
                    f"ios-normal-settings-{runner.IOS_CORE_DEVICE}-dark", ["xcodebuild"], ROOT,
                    runner.ios_normal_settings_environment("dark"), Path(directory),
                    "11111111-1111-1111-1111-111111111111", "dark",
                )
        self.assertEqual(settings, original)

    def test_simulator_observations_publish_only_known_enumerated_values(self):
        result = runner._published_simulator_settings({
            "appearanceBefore": "light", "appearanceObserved": "password=private",
            "contentSizeRequested": runner.LIVE_CONTENT_SIZE, "contentSizeRestored": [],
            "unexpected": "private", "contentSizeObserved": True,
        })
        self.assertEqual(result, {"appearanceBefore": "light", "contentSizeRequested": runner.LIVE_CONTENT_SIZE})

    def test_attachment_export_requires_the_complete_named_png_inventory(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            result = root / "result.xcresult"
            result.mkdir()
            name = f"ios-release-{runner.IOS_CORE_DEVICE}-light-testLaunchShowsSafeConfigurationState"

            def export(command_name, command, cwd, environment, log_path):
                output = Path(command[-1])
                output.mkdir()
                logical = runner._expected_logical_screenshot_names(name)[0]
                (output / "capture.png").write_bytes(self.png_fixture())
                (output / "manifest.json").write_text(json.dumps([{"attachments": [{"suggestedHumanReadableName": logical + "_0_123e4567-e89b-12d3-a456-426614174000.png", "exportedFileName": "capture.png"}]}]), encoding="utf-8")
                return runner.LiveCommandResult(0, "controlled", process_exit=0)

            with mock.patch.object(runner, "_run_live_command", side_effect=export):
                paths, failure = runner._retain_live_screenshots(name, ROOT, root, result)
            self.assertIsNone(failure)
            self.assertEqual(paths, [f"screenshots/{name}/01.png"])
            self.assertTrue((root / runner.LIVE_REVIEW_STAGE / paths[0]).is_file())
            self.assertFalse((root / runner.LIVE_REVIEW_ARTIFACTS).exists())

    def test_normal_settings_matrix_uses_two_devices_without_forced_appearance(self):
        destinations = {device: f"platform=iOS Simulator,id={index:08d}-1111-1111-1111-111111111111" for index, device in enumerate(runner.IOS_RELEASE_DEVICES, 1)}
        matrix = runner.ios_normal_settings_matrix(destinations)
        self.assertEqual(len(matrix), 4)
        self.assertEqual({"light", "dark"}, {environment["ACE_EXPECTED_EFFECTIVE_INTERFACE_STYLE"] for _, _, environment, _ in matrix})
        self.assertTrue(all("ACE_UI_TEST_APPEARANCE" not in environment and not any(argument.startswith("ACE_UI_TEST_APPEARANCE=") for argument in command) for _, command, environment, _ in matrix))
        self.assertTrue(all(runner.LIVE_NORMAL_SETTINGS_METHOD in command[-1] for _, command, _, _ in matrix))

    def test_attachment_export_rejects_incomplete_or_unsafe_metadata_and_pngs(self):
        name = f"ios-release-{runner.IOS_CORE_DEVICE}-light-testBothAppearances"
        expected = runner._expected_logical_screenshot_names(name)
        cases = {
            "missing": (expected[:1], self.png_fixture(), "attachment-missing"),
            "duplicate": ((expected[0], expected[0]), self.png_fixture(), "attachment-missing"),
            "extra": ((*expected, "unapproved attachment"), self.png_fixture(), "attachment-missing"),
            "corrupt": (expected, b"not-a-png", "attachment-invalid"),
            "too-many-pixels": (expected, self.png_fixture(b"\x00" * 6), "attachment-invalid"),
            "escape": (expected, self.png_fixture(), "attachment-invalid"),
        }
        for case, (logical_names, image, reason) in cases.items():
            with self.subTest(case=case), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                result = root / "result.xcresult"
                result.mkdir()

                def export(command_name, command, cwd, environment, log_path):
                    output = Path(command[-1])
                    output.mkdir()
                    attachments = []
                    for number, logical in enumerate(logical_names):
                        filename = "../outside.png" if case == "escape" and number == 0 else f"capture-{number}.png"
                        if filename != "../outside.png":
                            (output / filename).write_bytes(image)
                        attachments.append({"suggestedHumanReadableName": logical, "exportedFileName": filename})
                    (output / "manifest.json").write_text(json.dumps([{"attachments": attachments}]), encoding="utf-8")
                    return runner.LiveCommandResult(0, "controlled", process_exit=0)

                with mock.patch.object(runner, "_run_live_command", side_effect=export):
                    paths, failure = runner._retain_live_screenshots(name, ROOT, root, result)
                self.assertIsNone(paths)
                self.assertEqual(failure, reason)
                self.assertFalse((root / runner.LIVE_REVIEW_ARTIFACTS).exists())

    def test_normal_settings_stops_when_simulator_query_fails(self):
        responses = iter(((False, None), (False, None)))

        def query(*_args, **_kwargs):
            return next(responses)

        with tempfile.TemporaryDirectory() as directory, mock.patch.object(
            runner, "_simctl_ui_value", side_effect=query
        ):
            result = runner._normal_settings_result(
                "ios-normal-settings-test-light", ["xcodebuild", "test"], ROOT,
                runner.ios_normal_settings_environment("light"), Path(directory),
                "11111111-1111-1111-1111-111111111111", "light",
            )
        self.assertEqual(result["reason"], "simulator-setting-query-failed")

    def test_normal_settings_retains_supported_unknown_query_evidence(self):
        with tempfile.TemporaryDirectory() as directory, mock.patch.object(
            runner,
            "_run_live_command",
            return_value=runner.LiveCommandResult(0, "controlled", process_exit=0),
        ):
            query_evidence = []
            log = Path(directory) / "query.log"
            log.write_text("unknown\n", encoding="utf-8")
            with mock.patch.object(runner, "_safe_live_path", return_value=log):
                observed, value = runner._simctl_ui_value(
                    Path(directory), "11111111-1111-1111-1111-111111111111",
                    "appearance", query_evidence=query_evidence,
                )
        self.assertFalse(observed)
        self.assertIsNone(value)
        self.assertEqual(query_evidence, [{
            "setting": "appearance", "processExit": 0,
            "responseStatus": "available", "response": "unknown",
        }])
        published = runner._published_simulator_query_evidence([
            {"setting": "appearance", "responseStatus": "unpublished-invalid", "response": "unknown"},
            {"setting": "content_size", "responseStatus": "available", "response": "unknown"},
        ])
        self.assertNotIn("response", published[0])
        self.assertEqual(published[1]["response"], "unknown")

    def test_png_validation_rejects_oversized_or_incomplete_pixel_streams(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            cases = {
                "valid": self.png_fixture(),
                "corrupt": self.png_fixture()[:-1] + b"x",
                "truncated": self.png_fixture()[:-5],
                "overfull": self.png_fixture(b"\x00" * 6),
            }
            for case, content in cases.items():
                with self.subTest(case=case):
                    path = root / f"{case}.png"
                    path.write_bytes(content)
                    self.assertEqual(runner._valid_png(path), case == "valid")
            oversized = root / "oversized.png"
            oversized.write_bytes(self.png_fixture(width=10_000, height=10_000))
            with mock.patch.object(runner.zlib, "decompressobj") as decoder:
                self.assertFalse(runner._valid_png(oversized))
            decoder.assert_not_called()

    def test_private_full_matrix_collection_preserves_exact_binary_bundle_bytes(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "raw"
            private = Path(directory) / "private"
            root.mkdir()
            name = next(
                command for command in runner._live_command_names()
                if command.startswith("ios-release-iPhone 17-light-")
            )
            original = b" " * 63 + b"\xffsk-fictional-token!" + b" " * 64
            data = root / f"{name}.xcresult" / "Data"
            data.mkdir(parents=True)
            (data / "opaque").write_bytes(original)
            (root / f"{name}.log").write_text("controlled", encoding="utf-8")
            (root / f"{name}-summary.json").write_text("{}", encoding="utf-8")
            planned = [
                {"name": command, "expectedTests": None}
                for command in sorted(runner._live_command_names())
            ]
            with mock.patch.object(runner, "LIVE_PRIVATE_COLLECTION_ROOT", private):
                status = runner._finalise_private_live_collection(
                    root, planned, [{"name": name}], None,
                    {"workflow": runner.LIVE_WORKFLOW, "commit": "a" * 40},
                )
            self.assertEqual(status, "quarantined-pending-review")
            archive = private / runner.LIVE_PRIVATE_COLLECTION_ARCHIVE
            with tarfile.open(archive, "r:gz") as records:
                member = f"records/commands/{name}/result.xcresult/Data/opaque"
                self.assertEqual(records.extractfile(member).read(), original)
                inventory = json.load(records.extractfile("records/collection-inventory.json"))
            self.assertEqual(inventory["collectionStatus"], status)
            entry = next(item for item in inventory["records"] if item["relativePath"] == member)
            self.assertEqual(entry["sha256"], hashlib.sha256(original).hexdigest())
            self.assertEqual(entry["scannerStatus"], status)
            self.assertEqual(entry["commandState"], "complete")
            self.assertNotIn("sk-fictional-token", json.dumps({"status": status}))

    def test_private_full_matrix_collection_rejects_text_and_near_quarantine_matches(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            record = root / "opaque"
            cases = (
                ("text-secret", b"token=confirmed-secret", "records/commands/ios-65-unit/log", "ios-65-unit"),
                ("utf16-secret", "token=fictional-probe".encode("utf-16-le"), "records/commands/ios-65-unit/log", "ios-65-unit"),
                ("username", b"username=unredacted", "records/commands/ios-65-unit/log", "ios-65-unit"),
                ("wrong-path", b" " * 63 + b"\xffsk-fictional-token" + b" " * 64,
                 "records/commands/ios-65-unit/result.xcresult/DataX/opaque", "ios-65-unit"),
                ("wrong-command", b" " * 63 + b"\xffsk-fictional-token" + b" " * 64,
                 "records/commands/ios-65-unit/result.xcresult/Data/opaque", "ios-negative-config"),
                ("utf8", b" " * 64 + b"sk-fictional-token" + b" " * 64,
                 "records/commands/ios-65-unit/result.xcresult/Data/opaque", "ios-65-unit"),
            )
            for case, content, archive_path, command in cases:
                with self.subTest(case=case):
                    record.write_bytes(content)
                    with self.assertRaisesRegex(ValueError, "private collection (content was rejected|archive path is invalid)"):
                        runner._private_collection_file_metadata(root, record, archive_path, command)

    def test_private_full_matrix_collection_rejects_symlink_and_stale_archive(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "raw"
            private = Path(directory) / "private"
            root.mkdir()
            target = root / "target"
            target.write_bytes(b"controlled")
            with mock.patch.object(Path, "is_symlink", autospec=True, side_effect=lambda path: path == target):
                with self.assertRaisesRegex(ValueError, "not a regular file"):
                    runner._private_collection_relative(root, target)

            name = "ios-65-unit"
            (root / f"{name}.log").write_bytes(b"controlled")
            planned = [{"name": command, "expectedTests": None} for command in sorted(runner._live_command_names())]
            private.mkdir()
            stale = private / runner.LIVE_PRIVATE_COLLECTION_ARCHIVE
            stale.write_bytes(b"stale")
            with mock.patch.object(runner, "LIVE_PRIVATE_COLLECTION_ROOT", private):
                status = runner._finalise_private_live_collection(
                    root, planned, [{"name": name}], None, {"workflow": runner.LIVE_WORKFLOW}
                )
            self.assertEqual(status, "incomplete")
            self.assertNotEqual(stale.read_bytes(), b"stale")

    def test_private_full_matrix_collection_uses_only_the_full_planned_source_inventory(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            names = sorted(runner._live_command_names())
            planned = [{"name": name, "expectedTests": None} for name in names]
            checks = [{"name": name, "exit": 1 if number == 0 else 0} for number, name in enumerate(names)]
            for name in names:
                if name == "ios-negative-config":
                    (root / f"{name}.log").write_bytes(b"controlled")
                    continue
                (root / f"{name}.log").write_bytes(b"controlled")
                (root / f"{name}-summary.json").write_bytes(b"{}")
                data = root / f"{name}.xcresult" / "Data"
                data.mkdir(parents=True)
                (data / "object").write_bytes(b"controlled")
            sources, complete = runner._private_collection_sources(root, planned, checks, None)
            archive_paths = {archive_path for _source_root, _path, archive_path, _command in sources}
            self.assertTrue(complete)
            self.assertEqual(len(sources), (len(names) - 1) * 3 + 1)
            self.assertIn("records/commands/ios-negative-config/log", archive_paths)
            self.assertFalse(any("simulator-resolution" in path for path in archive_paths))
            self.assertTrue(all(path.startswith("records/commands/") for path in archive_paths))
            private = root / "private"
            with mock.patch.object(runner, "LIVE_PRIVATE_COLLECTION_ROOT", private):
                status = runner._finalise_private_live_collection(
                    root, planned, checks, None, {"workflow": runner.LIVE_WORKFLOW}
                )
            self.assertEqual(status, "complete")
            with tarfile.open(private / runner.LIVE_PRIVATE_COLLECTION_ARCHIVE, "r:gz") as records:
                inventory = json.load(records.extractfile("records/collection-inventory.json"))
            failed_entry = next(
                item for item in inventory["records"]
                if item["producingCommand"] == names[0]
            )
            self.assertEqual(failed_entry["commandState"], "complete")

    def test_private_collection_finaliser_reports_interruption_as_incomplete(self):
        with tempfile.TemporaryDirectory() as directory:
            root = self.live_artifact_root(directory)
            private = Path(directory) / "private"
            with mock.patch.object(runner, "LIVE_ARTIFACT_ROOT", root), mock.patch.object(
                runner, "LIVE_PRIVATE_COLLECTION_ROOT", private
            ), mock.patch.object(runner, "_live_execution_context", side_effect=KeyboardInterrupt):
                with self.assertRaises(KeyboardInterrupt):
                    runner.live_evidence_checks(root, "a" * 40)
            progress = json.loads((root / "live-evidence-progress.json").read_text(encoding="utf-8"))
            self.assertTrue(progress["interrupted"])
            self.assertEqual(progress["privateCollectionStatus"], "incomplete")

    def test_private_collection_marks_missing_started_records_incomplete(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            planned = [{"name": name, "expectedTests": None} for name in runner._live_command_names()]
            (root / "ios-65-unit.log").write_bytes(b"controlled")
            sources, complete = runner._private_collection_sources(
                root, planned, [{"name": name} for name in runner._live_command_names()], None
            )
            self.assertFalse(complete)
            self.assertEqual([item[2] for item in sources], ["records/commands/ios-65-unit/log"])


if __name__ == "__main__":
    unittest.main()
