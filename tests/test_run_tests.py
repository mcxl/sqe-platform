import importlib.util
import json
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

    def test_simulator_resolution_creates_and_verifies_missing_exact_device(self):
        created_uuid = "33333333-3333-3333-3333-333333333333"
        initial = self.simulator_snapshot([])
        resolved = self.simulator_snapshot([
            {"name": runner.IOS_CORE_DEVICE, "udid": created_uuid, "isAvailable": True, "deviceTypeIdentifier": "com.apple.CoreSimulator.SimDeviceType.iPhone-SE-3rd-generation"},
        ])
        with mock.patch.object(runner, "_simctl_list", side_effect=[initial, resolved]), mock.patch.object(runner, "_simctl_create", return_value=created_uuid) as create:
            destinations = runner.resolve_ios_destinations((runner.IOS_CORE_DEVICE,))
        self.assertEqual(destinations[runner.IOS_CORE_DEVICE], f"platform=iOS Simulator,id={created_uuid}")
        create.assert_called_once_with(runner.IOS_CORE_DEVICE, "com.apple.CoreSimulator.SimDeviceType.iPhone-SE-3rd-generation", "com.apple.CoreSimulator.SimRuntime.iOS-26-1")

    def test_simulator_resolution_rejects_device_without_type_identifier(self):
        core_uuid = "66666666-6666-6666-6666-666666666666"
        snapshot = self.simulator_snapshot([
            {"name": runner.IOS_CORE_DEVICE, "udid": core_uuid, "isAvailable": True},
        ])
        with mock.patch.object(runner, "_simctl_list", return_value=snapshot), mock.patch.object(runner, "_simctl_create", return_value=core_uuid), mock.patch.object(runner.time, "sleep"):
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
        with mock.patch.object(runner.shutil, "which", return_value="xcodebuild"), mock.patch.object(runner, "resolve_ios_destinations", side_effect=runner.SimulatorResolutionError("no available iOS 26 runtime")), mock.patch.object(runner, "run_ios_test") as run_ios_test:
            checks = runner.component_checks("release", "ios")
        self.assertEqual(checks[0]["status"], "failed")
        self.assertIn("no available iOS 26 runtime", checks[0]["detail"])
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

    def test_reviewed_public_evidence_requires_complete_controlled_artifact(self):
        plan = {"controlledRegister": {"path": "register.json"}}
        with tempfile.TemporaryDirectory() as directory:
            plan_path = Path(directory) / "plan.json"
            register = {
                "results": {
                    "IOS-TEST-001": {
                        "status": "reviewed",
                        "result": {field: "value" for field in runner.EVIDENCE_RESULT_FIELDS},
                    }
                }
            }
            (Path(directory) / "register.json").write_text(json.dumps(register), encoding="utf-8")
            errors, state = runner.validate_public_evidence_records(
                plan_path,
                ["IOS-TEST-001"],
                plan,
            )
        self.assertEqual(state, "invalid")
        self.assertTrue(any("artifact" in error for error in errors))

    def test_ios_core_commands_use_controlled_fictional_inputs(self):
        destinations = {runner.IOS_CORE_DEVICE: "platform=iOS Simulator,id=11111111-1111-1111-1111-111111111111"}
        with mock.patch.object(runner.shutil, "which", return_value="xcodebuild"), mock.patch.object(runner, "resolve_ios_destinations", return_value=destinations), mock.patch.object(runner, "run_ios_test", return_value={"status": "passed"}) as run_ios_test:
            runner.component_checks("core", "ios")
        self.assertEqual(run_ios_test.call_count, 6)
        for call in run_ios_test.call_args_list:
            self.assertEqual(call.args[3], runner.IOS_TEST_ENVIRONMENT)
        ui_calls = [call for call in run_ios_test.call_args_list if call.args[0].startswith("ios-core-ui-")]
        self.assertTrue(all("ACEClientAppUITests" in call.args[1] for call in ui_calls))
        self.assertTrue(all("Debug" in call.args[1] for call in ui_calls))

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
