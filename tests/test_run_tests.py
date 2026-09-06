import importlib.util
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("run_tests", ROOT / "tools" / "run_tests.py")
runner = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(runner)


class RunnerContractTests(unittest.TestCase):
    def simulator_snapshot(self, devices):
        return {
            "runtimes": [{"identifier": "com.apple.CoreSimulator.SimRuntime.iOS-26-1", "version": "26.1", "isAvailable": True}],
            "devicetypes": [
                {"name": runner.IOS_CORE_DEVICE, "identifier": "com.apple.CoreSimulator.SimDeviceType.iPhone-SE-3rd-generation"},
                {"name": "iPhone 16 Pro Max", "identifier": "com.apple.CoreSimulator.SimDeviceType.iPhone-16-Pro-Max"},
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
            "iPhone 16 Pro Max": "platform=iOS Simulator,id=22222222-2222-2222-2222-222222222222",
        }

        def resolve(names, recorder=None):
            self.assertEqual(names, runner.IOS_RELEASE_DEVICES)
            assert recorder is not None
            recorder("selected-runtime", "com.apple.CoreSimulator.SimRuntime.iOS-26-1")
            recorder("device-types", {runner.IOS_CORE_DEVICE: "core", "iPhone 16 Pro Max": "max"})
            recorder("resolved-destinations", destinations)
            return destinations

        def ios_test(name, command, cwd, environment, expected_tests, artifact_root):
            manifest = json.loads(
                (artifact_root / "live-evidence-manifest.json").read_text(encoding="utf-8")
            )
            self.assertEqual(manifest["status"], "failed")
            self.assertEqual(manifest["results"], [])
            (artifact_root / f"{name}.log").write_text("controlled result", encoding="utf-8")
            (artifact_root / f"{name}.xcresult").mkdir()
            (artifact_root / f"{name}.xcresult" / "Info.plist").write_text("controlled", encoding="utf-8")
            (artifact_root / f"{name}-summary.json").write_text(
                json.dumps({"passedTests": expected_tests, "failedTests": 0, "skippedTests": 0}),
                encoding="utf-8",
            )
            return {"name": name, "status": "passed", "exit": 0, "detail": "controlled"}

        def negative(name, command, cwd, environment, log_path):
            self.assertEqual(name, "ios-negative-config")
            log_path.write_text(runner.NEGATIVE_CONFIG_REJECTION, encoding="utf-8")
            return 1, "controlled rejection"

        return (
            mock.patch.object(runner, "LIVE_ARTIFACT_ROOT", root),
            mock.patch.object(runner, "_live_execution_context", return_value={"workflow": runner.LIVE_WORKFLOW}),
            mock.patch.object(runner, "_live_repository_metadata", return_value={"repository": runner.LIVE_REPOSITORY, "commit": "a" * 40, "baseline": runner.LIVE_BASELINE_COMMIT}),
            mock.patch.object(runner, "ui_methods", return_value=list(runner.LIVE_UI_METHODS)),
            mock.patch.object(runner.shutil, "which", return_value="controlled-tool"),
            mock.patch.object(runner, "resolve_ios_destinations", side_effect=resolve),
            mock.patch.object(runner, "_run_live_ios_test", side_effect=ios_test),
            mock.patch.object(runner, "_run_live_command", side_effect=negative),
        )

    def test_live_evidence_success_fixture_writes_initial_external_controlled_manifest(self):
        with tempfile.TemporaryDirectory() as directory:
            root = self.live_artifact_root(directory)
            contexts = self.run_live_success_fixture(root)
            with contexts[0], contexts[1], contexts[2], contexts[3], contexts[4], contexts[5], contexts[6], contexts[7]:
                checks = runner.live_evidence_checks(root, "a" * 40)
            self.assertEqual(len(checks), 23, checks)
            self.assertTrue(all(check["exit"] == 0 for check in checks))
            manifest = json.loads((root / "live-evidence-manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["status"], "passed-not-release-evidence")
            self.assertFalse(manifest["releaseEvidence"])
            self.assertEqual(manifest["commit"], "a" * 40)
            self.assertTrue(manifest["checksums"])

    def test_live_evidence_publishes_fixed_simulator_failure_codes(self):
        cases = (
            ("wrong runtime", "injected runtime detail", runner.SIMULATOR_RESOLUTION_FAILURE_REASON),
            ("wrong simulator type", "injected type detail", runner.SIMULATOR_RESOLUTION_FAILURE_REASON),
            ("duplicate UUID", "injected UUID detail", runner.SIMULATOR_RESOLUTION_FAILURE_REASON),
            ("timeout", "injected timeout detail", runner.SIMULATOR_RESOLUTION_TIMEOUT_REASON),
        )
        for name, message, expected_reason in cases:
            with self.subTest(name=name), tempfile.TemporaryDirectory() as directory:
                root = self.live_artifact_root(directory)
                error = runner.SimulatorResolutionError(message, expected_reason)
                with mock.patch.object(runner, "LIVE_ARTIFACT_ROOT", root), mock.patch.object(runner, "_live_execution_context", return_value={}), mock.patch.object(runner, "_live_repository_metadata", return_value={}), mock.patch.object(runner, "ui_methods", return_value=list(runner.LIVE_UI_METHODS)), mock.patch.object(runner.shutil, "which", return_value="controlled-tool"), mock.patch.object(runner, "resolve_ios_destinations", side_effect=error), mock.patch.object(runner, "_run_live_ios_test") as ios_test:
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
            self.assertEqual(checks[0]["reason"], runner.LIVE_SETUP_FAILURE_REASON)
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

    def test_live_evidence_command_failure_summary_identifies_the_failed_command(self):
        with tempfile.TemporaryDirectory() as directory:
            root = self.live_artifact_root(directory)
            contexts = self.run_live_success_fixture(root)
            raw_output = "raw command output\nsecret-like=value\nunrelated-value"

            def command_result(name, command, cwd, environment, expected_tests, artifact_root):
                status = "failed" if name == "ios-65-unit" else "passed"
                return {
                    "name": name,
                    "status": status,
                    "exit": 1 if status == "failed" else 0,
                    "detail": raw_output,
                }

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
        self.assertEqual(
            output.getvalue().splitlines(),
            [
                "report=external-artifact-root/live-evidence-manifest.json",
                "live-evidence: failed: failed live commands: ios-65-unit; reasons: ios-65-unit=controlled-failure",
            ],
        )
        failed_result = next(
            result
            for result in manifest["results"]
            if result["name"] == "ios-65-unit"
        )
        self.assertEqual(failed_result["reason"], "controlled-failure")
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
            ),
            ("start", OSError("controlled"), "command-start-failed"),
            (
                "nonzero",
                subprocess.CompletedProcess(["xcodebuild"], 1, "controlled"),
                "command-nonzero",
            ),
        )
        with tempfile.TemporaryDirectory() as directory:
            for name, response, expected_reason in cases:
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
            negative["reason"], "negative-configuration-not-rejected"
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
                {"workflow": runner.LIVE_WORKFLOW},
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

    def test_simulator_resolution_uses_existing_exact_device_ids(self):
        core_uuid = "11111111-1111-1111-1111-111111111111"
        max_uuid = "22222222-2222-2222-2222-222222222222"
        snapshot = self.simulator_snapshot([
            {"name": runner.IOS_CORE_DEVICE, "udid": core_uuid, "isAvailable": True, "deviceTypeIdentifier": "com.apple.CoreSimulator.SimDeviceType.iPhone-SE-3rd-generation"},
            {"name": "iPhone 16 Pro Max", "udid": max_uuid, "isAvailable": True, "deviceTypeIdentifier": "com.apple.CoreSimulator.SimDeviceType.iPhone-16-Pro-Max"},
        ])
        with mock.patch.object(runner, "_simctl_list", return_value=snapshot), mock.patch.object(runner, "_simctl_create") as create:
            destinations = runner.resolve_ios_destinations(runner.IOS_RELEASE_DEVICES)
        self.assertEqual(destinations[runner.IOS_CORE_DEVICE], f"platform=iOS Simulator,id={core_uuid}")
        self.assertEqual(destinations["iPhone 16 Pro Max"], f"platform=iOS Simulator,id={max_uuid}")
        create.assert_not_called()

    def test_simulator_resolution_rejects_existing_exact_device_with_invalid_uuid(self):
        snapshot = self.simulator_snapshot([
            {
                "name": runner.IOS_CORE_DEVICE,
                "udid": "not-a-simulator-uuid",
                "isAvailable": True,
                "deviceTypeIdentifier": "com.apple.CoreSimulator.SimDeviceType.iPhone-SE-3rd-generation",
            },
        ])
        with mock.patch.object(runner, "_simctl_list", return_value=snapshot):
            with self.assertRaisesRegex(runner.SimulatorResolutionError, "simulator UUID is invalid"):
                runner.resolve_ios_destinations((runner.IOS_CORE_DEVICE,))

    def test_simulator_resolution_creates_and_verifies_missing_exact_device(self):
        created_uuid = "33333333-3333-3333-3333-333333333333"
        initial = self.simulator_snapshot([])
        resolved = self.simulator_snapshot([
            {"name": runner.IOS_CORE_DEVICE, "udid": created_uuid, "isAvailable": True, "deviceTypeIdentifier": "com.apple.CoreSimulator.SimDeviceType.iPhone-SE-3rd-generation"},
        ])
        with mock.patch.object(runner, "_simctl_list", side_effect=[initial, resolved]), mock.patch.object(runner, "_simctl_create", return_value=created_uuid) as create:
            destinations = runner.resolve_ios_destinations((runner.IOS_CORE_DEVICE,))
        self.assertEqual(destinations[runner.IOS_CORE_DEVICE], f"platform=iOS Simulator,id={created_uuid}")
        create.assert_called_once_with(runner.IOS_CORE_DEVICE, "com.apple.CoreSimulator.SimDeviceType.iPhone-SE-3rd-generation", "com.apple.CoreSimulator.SimRuntime.iOS-26-1", timeout=mock.ANY)

    def test_simulator_creation_rejects_a_concurrent_exact_device(self):
        created_uuid = "cccccccc-cccc-cccc-cccc-cccccccccccc"
        concurrent_uuid = "dddddddd-dddd-dddd-dddd-dddddddddddd"
        initial = self.simulator_snapshot([])
        concurrent = self.simulator_snapshot([
            {"name": runner.IOS_CORE_DEVICE, "udid": created_uuid, "isAvailable": True, "deviceTypeIdentifier": "com.apple.CoreSimulator.SimDeviceType.iPhone-SE-3rd-generation"},
            {"name": runner.IOS_CORE_DEVICE, "udid": concurrent_uuid, "isAvailable": True, "deviceTypeIdentifier": "com.apple.CoreSimulator.SimDeviceType.iPhone-SE-3rd-generation"},
        ])
        with mock.patch.object(runner, "_simctl_list", side_effect=[initial, concurrent]), mock.patch.object(runner, "_simctl_create", return_value=created_uuid), mock.patch.object(runner.time, "monotonic", side_effect=[0, 0, 0, 0]):
            with self.assertRaisesRegex(runner.SimulatorResolutionError, "ambiguous"):
                runner.resolve_ios_destinations((runner.IOS_CORE_DEVICE,))

    def test_simulator_resolution_rejects_device_without_type_identifier(self):
        core_uuid = "66666666-6666-6666-6666-666666666666"
        snapshot = self.simulator_snapshot([
            {"name": runner.IOS_CORE_DEVICE, "udid": core_uuid, "isAvailable": True},
        ])
        with mock.patch.object(runner, "_simctl_list", return_value=snapshot), mock.patch.object(runner, "_simctl_create", return_value=core_uuid), mock.patch.object(runner.time, "sleep"), mock.patch.object(runner.time, "monotonic", side_effect=[0, 0, 0, 0, 0, 180]):
            with self.assertRaisesRegex(runner.SimulatorResolutionError, "did not become available"):
                runner.resolve_ios_destinations((runner.IOS_CORE_DEVICE,))

    def test_simulator_resolution_rejects_ambiguous_or_unverifiable_devices(self):
        snapshot = self.simulator_snapshot([
            {"name": runner.IOS_CORE_DEVICE, "udid": "44444444-4444-4444-4444-444444444444", "isAvailable": True, "deviceTypeIdentifier": "com.apple.CoreSimulator.SimDeviceType.iPhone-SE-3rd-generation"},
            {"name": runner.IOS_CORE_DEVICE, "udid": "55555555-5555-5555-5555-555555555555", "isAvailable": True, "deviceTypeIdentifier": "com.apple.CoreSimulator.SimDeviceType.iPhone-SE-3rd-generation"},
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
        self.assertEqual(run_ios_test.call_count, 6)
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
            {"name": runner.IOS_CORE_DEVICE, "udid": created_uuid, "isAvailable": True, "deviceTypeIdentifier": "com.apple.CoreSimulator.SimDeviceType.iPhone-SE-3rd-generation"},
        ])
        with mock.patch.object(runner, "_simctl_list", side_effect=[initial, resolved]) as listing, mock.patch.object(runner, "_simctl_create", return_value=created_uuid), mock.patch.object(runner.time, "monotonic", side_effect=[100, 100, 100, 100]):
            runner.resolve_ios_destinations((runner.IOS_CORE_DEVICE,))
        self.assertEqual(runner.SIMULATOR_VERIFICATION_SECONDS, 180)
        self.assertEqual(runner.LIVE_COMMAND_TIMEOUT_SECONDS, 600)
        self.assertLess(
            runner.SIMULATOR_VERIFICATION_SECONDS,
            runner.LIVE_COMMAND_TIMEOUT_SECONDS,
        )
        self.assertEqual(listing.call_args_list[0].kwargs["timeout"], 180)
        self.assertEqual(listing.call_args_list[1].kwargs["timeout"], 180)

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
        self.assertIn("max_build_duration: 90", workflow)
        self.assertIn("groups:\n        - mcx19_live_evidence", workflow)
        self.assertEqual(config.count("mcx19_live_evidence"), 1)
        self.assertIn("ACE_LIVE_EVIDENCE_WORKFLOW: ace-ios-live-evidence-manual", workflow)
        self.assertIn("ACE_LIVE_EVIDENCE_APPROVED_COMMIT", workflow)
        self.assertIn(
            "python3 tools/run_tests.py live-evidence --component ios --artifact-root /private/tmp/mcx-19-live-evidence --expected-commit \"$ACE_LIVE_EVIDENCE_APPROVED_COMMIT\"",
            workflow,
        )
        self.assertNotIn("push", workflow)
        self.assertNotIn("pull_request", workflow)
        self.assertNotIn("artifacts:", workflow)
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
            ("plan simulator targets", lambda plan, register: plan["controlledRegister"]["simulatorProvisioning"].update({"exactTargets": "iPhone SE (3rd generation)"})),
            ("register simulator targets", lambda plan, register: register["simulatorProvisioning"].update({"exactTargets": "iPhone SE (3rd generation)"})),
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
            {"name": runner.IOS_CORE_DEVICE, "udid": created_uuid, "isAvailable": True, "deviceTypeIdentifier": "com.apple.CoreSimulator.SimDeviceType.iPhone-SE-3rd-generation"},
        ])
        with mock.patch.object(runner, "_simctl_list", side_effect=[initial, resolved]), mock.patch.object(runner, "_simctl_create", return_value=created_uuid) as create, mock.patch.object(runner.time, "monotonic", side_effect=[100, 100, 105, 105]):
            runner.resolve_ios_destinations((runner.IOS_CORE_DEVICE,))
        self.assertEqual(create.call_args.kwargs["timeout"], 175)

        with mock.patch.object(runner, "_simctl_list", return_value=initial), mock.patch.object(runner, "_simctl_create") as create, mock.patch.object(runner.time, "monotonic", side_effect=[100, 100, 280]):
            with self.assertRaisesRegex(runner.SimulatorResolutionError, "create has no verification time remaining"):
                runner.resolve_ios_destinations((runner.IOS_CORE_DEVICE,))
        create.assert_not_called()

    def test_ios_release_matrix_uses_appearance_and_expected_rejection(self):
        destinations = {name: f"platform=iOS Simulator,id={number * 11111111:08d}-1111-1111-1111-111111111111" for number, name in enumerate(runner.IOS_RELEASE_DEVICES, 1)}
        with mock.patch.object(runner.shutil, "which", return_value="xcodebuild"), mock.patch.object(runner, "resolve_ios_destinations", return_value=destinations), mock.patch.object(runner, "run_ios_test", return_value={"status": "passed"}) as run_ios_test, mock.patch.object(runner, "run_command", return_value={"status": "passed"}) as run_command:
            runner.component_checks("release", "ios")
        calls = run_ios_test.call_args_list
        release_calls = [call for call in calls if call.args[0].startswith("ios-release-")]
        self.assertEqual(len(release_calls), 20)
        self.assertEqual(sum(call.args[3].get("ACE_UI_TEST_APPEARANCE") == "light" for call in release_calls), 10)
        self.assertEqual(sum(call.args[3].get("ACE_UI_TEST_APPEARANCE") == "dark" for call in release_calls), 10)
        self.assertTrue(all(any(argument == f"ACE_UI_TEST_APPEARANCE={call.args[3]['ACE_UI_TEST_APPEARANCE']}" for argument in call.args[1]) for call in release_calls))
        self.assertTrue(all("ACEClientAppUITests" in call.args[1] for call in release_calls))
        negative = next(
            call
            for call in run_command.call_args_list
            if call.args[0] == "ios-negative-config"
        )
        self.assertEqual(negative.kwargs["environment"], runner.NEGATIVE_CONFIG_ENVIRONMENT)
        self.assertEqual(negative.kwargs["expected_failure"], runner.NEGATIVE_CONFIG_REJECTION)

    def test_ui_scheme_forwards_the_appearance_build_setting_to_xctest(self):
        scheme = (ROOT / "ios/ACEClientApp/ACEClientApp.xcodeproj/xcshareddata/xcschemes/ACEClientAppUITests.xcscheme").read_text(encoding="utf-8")
        self.assertIn('key="ACE_UI_TEST_APPEARANCE"', scheme)
        self.assertIn('value="$(ACE_UI_TEST_APPEARANCE)"', scheme)
        self.assertIn('<TestAction buildConfiguration="Debug"', scheme)

    def test_make_ui_test_sets_an_overridable_light_appearance(self):
        makefile = (ROOT / "ios/ACEClientApp/Makefile").read_text(encoding="utf-8")
        ui_test_target = makefile.split("ui-test:", 1)[1].split(
            "# Remove derived data.", 1
        )[0]
        self.assertIn("UI_TEST_APPEARANCE ?= light", makefile)
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
        device_type = "com.apple.CoreSimulator.SimDeviceType.iPhone-SE-3rd-generation"
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


if __name__ == "__main__":
    unittest.main()
