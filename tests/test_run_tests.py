import importlib.util
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
        with mock.patch.object(runner, "_simctl_list", return_value=snapshot), mock.patch.object(runner, "_simctl_create", return_value=core_uuid), mock.patch.object(runner.time, "sleep"), mock.patch.object(runner.time, "monotonic", side_effect=[0, 0, 0, 0, 0, 30]):
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
        self.assertTrue(any("artifact" in error for error in errors))

    def test_reviewed_public_evidence_requires_its_package_and_entry(self):
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
        self.assertTrue(any("package is invalid" in error for error in errors))
        self.assertTrue(any("entry is invalid" in error for error in errors))

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
            "IOS-BASE-001: public evidence result schema is invalid", errors
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
                    "IOS-BASE-001: reviewed public evidence is incomplete", errors
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
        self.assertEqual(listing.call_args_list[0].kwargs["timeout"], 30)
        self.assertEqual(listing.call_args_list[1].kwargs["timeout"], 30)

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
            ("package status", lambda plan, register: register["packages"][0].update({"status": "approved"})),
            ("record status", lambda plan, register: register["results"]["IOS-BASE-001"].update({"status": "approved"})),
        )
        for name, mutate in cases:
            with self.subTest(name=name):
                plan, register = self.controlled_evidence_fixture()
                mutate(plan, register)
                errors, state = self.validate_fixture(plan, register)
                self.assertEqual(state, "invalid")
                self.assertTrue(any("invalid" in error or "status" in error for error in errors))

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
        self.assertEqual(create.call_args.kwargs["timeout"], 25)

        with mock.patch.object(runner, "_simctl_list", return_value=initial), mock.patch.object(runner, "_simctl_create") as create, mock.patch.object(runner.time, "monotonic", side_effect=[100, 100, 130]):
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
