from copy import deepcopy
import importlib.util
import json
import plistlib
import sys
import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path
from types import SimpleNamespace


MODULE = Path(__file__).parents[1] / "ace_ios_local.py"
SPEC = importlib.util.spec_from_file_location("ace_ios_local", MODULE)
ace = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules[SPEC.name] = ace
SPEC.loader.exec_module(ace)


class CoverageMatrixTests(unittest.TestCase):
    def test_approved_coverage_counts_and_states(self):
        cases = ace.coverage_cases()
        self.assertEqual(len(cases), 836)
        self.assertEqual(sum(case.audit for case in cases), 512)
        self.assertEqual(sum(not case.audit for case in cases), 324)
        self.assertEqual({case.scenario for case in cases}, set(ace.SCENARIOS))
        self.assertEqual(len(ace.coverage_batches(cases)), 58)
        self.assertEqual(ace.DEFAULT_SIZE, "large")
        self.assertEqual(ace.EXL_SIZE, "extra-large")

    def test_pilot_contains_22_cases_and_two_layout_only_release_cases(self):
        cases = ace.pilot_cases()
        self.assertEqual(len(cases), 22)
        self.assertEqual(sum(case.audit for case in cases), 20)
        self.assertEqual(sum(ace.expected_audit_invocations(case) for case in cases), 36)
        self.assertEqual([case.scenario for case in cases if not case.audit], ["release", "release"])
        configuration = lambda case: (case.device, case.scenario, case.settings)
        self.assertEqual(len({configuration(case) for case in cases}), 22)
        self.assertTrue({configuration(case) for case in cases}.issubset({configuration(case) for case in ace.coverage_cases()}))


class XctestrunTests(unittest.TestCase):
    def test_format_one_flat_target_is_configured(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            template = root / "source.xctestrun"
            output = root / "target.xctestrun"
            template.write_bytes(plistlib.dumps({
                "ACEClientAppUITests": {
                    "BlueprintName": "ACEClientAppUITests", "EnvironmentVariables": {"OLD": "1"},
                    "DependentProductPaths": ["__TESTROOT__/Debug-iphonesimulator/ACEClientApp.app"],
                    "TestBundlePath": "__TESTHOST__/PlugIns/ACEClientAppUITests.xctest",
                    "TestingEnvironmentVariables": {"XCODE_SCHEME_NAME": "ACEClientAppUITests", "DYLD_FRAMEWORK_PATH": "__TESTROOT__/Debug-iphonesimulator"},
                    "UITargetAppEnvironmentVariables": {"XCODE_SCHEME_NAME": "ACEClientAppUITests"},
                },
                "__xctestrun_metadata__": {"ContainerInfo": {"ContainerName": "ACEClientApp", "SchemeName": "ACEClientAppUITests"}, "FormatVersion": 1},
            }))
            ace.configure_xctestrun(template, output, {"ACE_COVERAGE_CASES_JSON": "[]"})
            payload = plistlib.loads(output.read_bytes())
            self.assertEqual(payload["ACEClientAppUITests"]["EnvironmentVariables"], {"OLD": "1", "ACE_COVERAGE_CASES_JSON": "[]"})
            self.assertEqual(payload["ACEClientAppUITests"]["DependentProductPaths"], [str(root / "Debug-iphonesimulator/ACEClientApp.app")])
            self.assertEqual(payload["ACEClientAppUITests"]["TestBundlePath"], "__TESTHOST__/PlugIns/ACEClientAppUITests.xctest")

    def test_rejects_configuration_style_format(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            template = root / "source.xctestrun"
            template.write_bytes(plistlib.dumps({"__xctestrun_metadata__": {"FormatVersion": 2}, "TestConfigurations": []}))
            with self.assertRaisesRegex(ace.RunnerError, "format"):
                ace.configure_xctestrun(template, root / "out", {})


class NativeRecordTests(unittest.TestCase):
    def test_selected_forwards_input_and_retains_original_record_when_input_is_deleted(self):
        selector = "ACEClientAppUITests/ACEClientAppUITests/testBothAppearances"
        candidate = {"commit": "candidate", "status": "clean"}
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            input_path = root / "ui.json"
            input_values = {"ACE_UI_TEST_APPEARANCE": "dark"}
            input_path.write_text(json.dumps(input_values), encoding="utf-8")
            template = root / "template.xctestrun"
            template.write_bytes(plistlib.dumps({"__xctestrun_metadata__": {"FormatVersion": 1}, "ACEClientAppUITests": {"EnvironmentVariables": {}}}))
            forwarded, restored = [], []

            def fake_command(command, **_kwargs):
                bundle = Path(command[command.index("-resultBundlePath") + 1])
                bundle.mkdir(parents=True, exist_ok=True)
                input_path.unlink()
                return {"command": command, "exit": 0, "stdout": "", "stderr": ""}

            with patch.object(ace, "preflight", return_value={"devices": {"iPhone 17": {"udid": "id"}}}), \
                 patch.object(ace, "candidate", return_value=candidate), \
                 patch.object(ace, "build", return_value={"template": str(template)}), \
                 patch.object(ace, "simulator_state", return_value="Shutdown"), \
                 patch.object(ace, "boot_required_simulator"), \
                 patch.object(ace, "restore_boot_state", side_effect=lambda *_args: restored.append(True)), \
                 patch.object(ace, "enumerate_selectors", return_value={selector}), \
                 patch.object(ace, "configure_xctestrun", side_effect=lambda _template, _output, environment, _target: forwarded.append(environment)), \
                 patch.object(ace, "command", side_effect=fake_command), \
                 patch.object(ace, "native_summary", return_value=1), \
                 patch.object(ace, "_export_attachments"):
                with self.assertRaisesRegex(ace.RunnerError, "environment is invalid"):
                    ace.selected([selector], root, device="iPhone 17", test_environment_path=input_path)
            failure = json.loads((root / "selected-failure.json").read_text(encoding="utf-8"))
            persisted = json.loads((root / "selected-input.json").read_text(encoding="utf-8"))
            self.assertEqual(forwarded, [input_values])
            self.assertEqual(failure["testEnvironment"]["values"], input_values)
            self.assertEqual(persisted["values"], input_values)
            self.assertTrue(restored)

    def test_selected_restores_shutdown_state_after_partial_boot_failure(self):
        selector = "ACEClientAppUITests/ACEClientAppUITests/testBothAppearances"
        candidate = {"commit": "candidate", "status": "clean"}
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            template = root / "template.xctestrun"
            template.write_bytes(plistlib.dumps({"__xctestrun_metadata__": {"FormatVersion": 1}, "ACEClientAppUITests": {"EnvironmentVariables": {}}}))
            restored = []
            with patch.object(ace, "preflight", return_value={"devices": {"iPhone 17": {"udid": "id"}}}), \
                 patch.object(ace, "candidate", return_value=candidate), \
                 patch.object(ace, "build", return_value={"template": str(template)}), \
                 patch.object(ace, "simulator_state", return_value="Shutdown"), \
                 patch.object(ace, "boot_required_simulator", side_effect=ace.RunnerError("bootstatus failed")), \
                 patch.object(ace, "restore_boot_state", side_effect=lambda *_args: restored.append(True)):
                with self.assertRaisesRegex(ace.RunnerError, "bootstatus failed"):
                    ace.selected([selector], root, device="iPhone 17")
            self.assertTrue(restored)
            self.assertEqual(json.loads((root / "selected-boot-restoration.json").read_text(encoding="utf-8"))["result"], "restored")

    def test_selected_ui_environment_accepts_only_the_approved_values_and_hashes(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "ui.json"
            values = {"ACE_UI_TEST_APPEARANCE": "dark", "ACE_EXPECTED_CONTENT_SIZE_CATEGORY": "large"}
            path.write_text(json.dumps(values), encoding="utf-8")
            environment, record = ace.selected_test_environment(path, "ACEClientAppUITests")
            self.assertEqual(environment, values)
            self.assertEqual(record["path"], str(path.resolve()))
            original_hash = record["sha256"]
            path.write_text(json.dumps({"ACE_UI_TEST_APPEARANCE": "light"}), encoding="utf-8")
            self.assertNotEqual(ace.selected_test_environment(path, "ACEClientAppUITests")[1]["sha256"], original_hash)
            with self.assertRaisesRegex(ace.RunnerError, "only for UI"):
                ace.selected_test_environment(path, "ACEClientAppTests")
            path.write_text(json.dumps({"ACE_COVERAGE_CASES_JSON": "[]"}), encoding="utf-8")
            with self.assertRaisesRegex(ace.RunnerError, "unknown"):
                ace.selected_test_environment(path, "ACEClientAppUITests")

    def test_selected_boot_helpers_restore_only_an_initially_shutdown_simulator(self):
        commands = []
        def checked(command, **_kwargs):
            commands.append(command)
            return {"exit": 0}

        with patch.object(ace, "simulator_state", return_value="Booted"), \
             patch.object(ace, "checked", side_effect=checked):
            self.assertTrue(ace.boot_required_simulator("id", "Shutdown"))
            ace.restore_boot_state("id", "Shutdown")
        self.assertEqual(commands, [["xcrun", "simctl", "boot", "id"], ["xcrun", "simctl", "bootstatus", "id", "-b"], ["xcrun", "simctl", "shutdown", "id"]])

    def test_restore_boot_state_skips_shutdown_when_the_simulator_is_already_shutdown(self):
        with patch.object(ace, "simulator_state", return_value="Shutdown") as simulator_state, \
             patch.object(ace, "checked") as checked:
            ace.restore_boot_state("id", "Shutdown")
        simulator_state.assert_called_once_with("id")
        checked.assert_not_called()

    def test_restore_boot_state_propagates_state_and_shutdown_errors(self):
        with self.subTest("unavailable-state"):
            with patch.object(ace, "simulator_state", side_effect=ace.RunnerError("required simulator state is unavailable")), \
                 patch.object(ace, "checked") as checked:
                with self.assertRaisesRegex(ace.RunnerError, "state is unavailable"):
                    ace.restore_boot_state("id", "Shutdown")
            checked.assert_not_called()

        with self.subTest("shutdown-error"):
            with patch.object(ace, "simulator_state", return_value="Booted"), \
                 patch.object(ace, "checked", side_effect=ace.RunnerError("command failed: xcrun simctl shutdown id")):
                with self.assertRaisesRegex(ace.RunnerError, "simctl shutdown"):
                    ace.restore_boot_state("id", "Shutdown")

    def test_pilot_readiness_rejects_loose_prose_and_bad_artifact_hash(self):
        candidate = {"commit": "abc", "status": "clean", "sourceHashes": {}, "statusDetail": "", "workingTreeSha256": "x"}
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            record = root / "gate.json"
            record.write_text("candidate abc passed", encoding="utf-8")
            with self.assertRaisesRegex(ace.RunnerError, "distinct"):
                ace.pilot_readiness(candidate, {"pocock": record, "functional": record, "evidence-gate": record, "private-input": record})
            artifact = root / "artifact.txt"
            artifact.write_text("evidence", encoding="utf-8")
            record.write_text(json.dumps({"candidate": candidate, "status": "passed", "evidence": [{"path": str(artifact), "sha256": "bad"}]}), encoding="utf-8")
            with self.assertRaisesRegex(ace.RunnerError, "distinct"):
                ace.pilot_readiness(candidate, {"pocock": record, "functional": record, "evidence-gate": record, "private-input": record})

    def test_attachment_manifest_maps_human_name_to_uuid_export(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            image = root / "E28C726E-95E6-4B9A-B95B-3C717BD48381.png"
            image.write_bytes(b"image")
            (root / "manifest.json").write_text(json.dumps([{"attachments": [{
                "exportedFileName": image.name,
                "suggestedHumanReadableName": "Fictional release — forced-dark_0_D76568E4.png",
            }]}]), encoding="utf-8")
            ace.verify_screenshot_attachments([{"screenshots": ["Fictional release — forced-dark"]}], root)
            with self.assertRaisesRegex(ace.RunnerError, "no exported"):
                ace.verify_screenshot_attachments([{"screenshots": ["missing"]}], root)
            duplicate = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
            duplicate[0]["attachments"].append(dict(duplicate[0]["attachments"][0]))
            (root / "manifest.json").write_text(json.dumps(duplicate), encoding="utf-8")
            with self.assertRaisesRegex(ace.RunnerError, "does not retain"):
                ace.attachment_name_map(root)

    def test_runtime_schema_requires_the_retained_version_build_and_identifier(self):
        runtime = {"runtimes": [{"name": "iOS 26.4", "version": "26.4.1", "buildversion": "23E254a",
                                  "identifier": "com.apple.CoreSimulator.SimRuntime.iOS-26-4", "isAvailable": True}]}
        self.assertEqual(ace.required_runtime(runtime)["identifier"], "com.apple.CoreSimulator.SimRuntime.iOS-26-4")
        runtime["runtimes"][0]["buildversion"] = "other"
        with self.assertRaisesRegex(ace.RunnerError, "runtime"):
            ace.required_runtime(runtime)

    def test_environment_identity_ignores_only_runtime_last_usage_without_mutating_raw_input(self):
        before = {
            "python": "/Library/Frameworks/Python.framework/Versions/3.14/bin/python3",
            "xcode": "Xcode 26.4.1 Build version 17E202",
            "runtime": {"buildversion": "23E254a", "identifier": "com.apple.CoreSimulator.SimRuntime.iOS-26-4",
                        "isAvailable": True, "lastUsage": {"x86_64": "2026-09-14T21:58:52Z"}},
            "devices": {"iPhone 17": {"udid": "A"}, "iPhone 17 Pro Max": {"udid": "B"}},
        }
        after = deepcopy(before)
        after["runtime"]["lastUsage"]["x86_64"] = "2026-09-14T22:20:13Z"
        before_raw, after_raw = deepcopy(before), deepcopy(after)

        self.assertEqual(ace.environment_identity(before), ace.environment_identity(after))
        self.assertEqual(before, before_raw)
        self.assertEqual(after, after_raw)
        self.assertIn("lastUsage", before["runtime"])
        self.assertIn("lastUsage", after["runtime"])

    def test_environment_identity_rejects_runtime_device_tool_and_python_changes(self):
        environment = {
            "python": "/Library/Frameworks/Python.framework/Versions/3.14/bin/python3",
            "xcode": "Xcode 26.4.1 Build version 17E202",
            "runtime": {"buildversion": "23E254a", "identifier": "com.apple.CoreSimulator.SimRuntime.iOS-26-4",
                        "isAvailable": True, "lastUsage": {"x86_64": "2026-09-14T21:58:52Z"}},
            "devices": {"iPhone 17": {"udid": "A"}, "iPhone 17 Pro Max": {"udid": "B"}},
        }

        def changed(path, value):
            result = deepcopy(environment)
            target = result
            for key in path[:-1]:
                target = target[key]
            target[path[-1]] = value
            return result

        changes = (
            ("runtime build", ("runtime", "buildversion"), "other"),
            ("runtime identity", ("runtime", "identifier"), "other.runtime"),
            ("runtime availability", ("runtime", "isAvailable"), False),
            ("device", ("devices", "iPhone 17", "udid"), "changed"),
            ("tool", ("xcode",), "Xcode other"),
            ("python", ("python",), "/other/python3"),
        )
        for name, path, value in changes:
            with self.subTest(change=name):
                self.assertNotEqual(ace.environment_identity(environment), ace.environment_identity(changed(path, value)))

    def test_device_records_rejects_malformed_required_udid(self):
        original = ace.json_command
        ace.json_command = lambda *_args: {"devices": {"com.apple.CoreSimulator.SimRuntime.iOS-26-4": [
            {"name": "iPhone 17", "isAvailable": True, "udid": "invalid"},
            {"name": "iPhone 17 Pro Max", "isAvailable": True, "udid": "D1BAA05C-52DD-4E57-832F-C0A75718E085"},
        ]}}
        try:
            with self.assertRaisesRegex(ace.RunnerError, "invalid UDID"):
                ace._device_records("com.apple.CoreSimulator.SimRuntime.iOS-26-4")
        finally:
            ace.json_command = original

    def test_actual_native_enumeration_schema_rejects_disabled_tests(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "inventory.json"
            inventory = {"errors": [], "values": [{"disabledTests": [], "enabledTests": [
                {"identifier": "ACEClientAppTests/ACEClientAppTests/testExample()"}], "testPlan": "ACEClientApp"}]}
            path.write_text(json.dumps(inventory), encoding="utf-8")
            self.assertEqual(ace.parse_enumeration(path), {"ACEClientAppTests/ACEClientAppTests/testExample"})
            inventory["values"][0]["disabledTests"] = [{"identifier": "ACEClientAppTests/ACEClientAppTests/testOther()"}]
            path.write_text(json.dumps(inventory), encoding="utf-8")
            with self.assertRaisesRegex(ace.RunnerError, "disabled"):
                ace.parse_enumeration(path)

    def test_retained_summary_schema_requires_a_complete_pass(self):
        passed = {"devicesAndConfigurations": [], "expectedFailures": 0, "failedTests": 0,
                  "passedTests": 1, "result": "Passed", "skippedTests": 0, "totalTestCount": 1}
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            bundle = root / "result.xcresult"
            bundle.mkdir()
            original = ace.checked
            ace.checked = lambda *_args, **_kwargs: {"stdout": json.dumps(passed), "exit": 0}
            try:
                self.assertEqual(ace.native_summary(bundle, root / "summary.json", 1), 1)
                passed["result"] = "Failed"
                passed["failedTests"] = 1
                with self.assertRaisesRegex(ace.RunnerError, "complete pass"):
                    ace.native_summary(bundle, root / "failed.json", 1)
                passed["result"] = "Passed"
                passed["failedTests"] = 0
                passed["expectedFailures"] = 1
                with self.assertRaisesRegex(ace.RunnerError, "complete pass"):
                    ace.native_summary(bundle, root / "expected.json", 1)
                passed["expectedFailures"] = 0
                passed["skippedTests"] = True
                with self.assertRaisesRegex(ace.RunnerError, "complete pass"):
                    ace.native_summary(bundle, root / "typed.json", 1)
            finally:
                ace.checked = original

    def test_case_markers_require_matching_observed_settings_and_screenshot(self):
        settings = ace.Settings("light", "medium", "portrait")
        case = ace.make_case("test", "iPhone 17", "signIn", settings, True)
        ace.verify_case_markers((case,), [{"id": case.id, "scenario": "signIn", "observed": settings.payload(), "result": "passed", "screenshots": ["screen"], "auditInvocations": 1}])
        with self.assertRaisesRegex(ace.RunnerError, "incomplete"):
                ace.verify_case_markers((case,), [{"id": case.id, "scenario": "signIn", "observed": settings.payload(), "result": "passed", "screenshots": [], "auditInvocations": 1}])

    def test_complex_audit_viewports_do_not_change_audited_case_count(self):
        settings = ace.Settings("light", "medium", "portrait")
        self.assertEqual(ace.expected_audit_invocations(ace.make_case("test", "iPhone 17", "release", settings, True)), 2)
        self.assertEqual(ace.expected_audit_invocations(ace.make_case("test", "iPhone 17", "noActions", settings, True)), 2)
        self.assertEqual(ace.expected_audit_invocations(ace.make_case("test", "iPhone 17", "release", settings, False)), 0)

    def test_marker_reader_rejects_invalid_json(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "native.log"
            path.write_text("ACE_CASE_RESULT not-json\n", encoding="utf-8")
            with self.assertRaisesRegex(ace.RunnerError, "invalid"):
                ace.marker_records(path, ace.CASE_MARKER)


class PartialBootRecoveryTests(unittest.TestCase):
    def test_bootstatus_failure_still_restores_original_shutdown_state(self):
        with tempfile.TemporaryDirectory() as directory:
            evidence = Path(directory)
            identity = {"commit": "controlled", "status": "clean"}
            devices = {"iPhone 17": {"udid": "2EB0863C-470E-467D-A0C6-CD216DA70C67"}}
            with patch.object(ace, "preflight", return_value={"devices": devices}), \
                 patch.object(ace, "candidate", return_value=identity), \
                 patch.object(ace, "build", return_value={"template": "unused"}), \
                 patch.object(ace, "simulator_state", return_value="Shutdown"), \
                 patch.object(ace, "boot_required_simulator", side_effect=ace.RunnerError("bootstatus failed")), \
                 patch.object(ace, "restore_boot_state") as restore:
                with self.assertRaisesRegex(ace.RunnerError, "bootstatus failed"):
                    ace.run_coverage(ace.pilot_cases(), evidence)
                restore.assert_called_once_with(devices["iPhone 17"]["udid"], "Shutdown")
            failure = json.loads((evidence / "coverage-final-failure.json").read_text())
            self.assertEqual(failure["primaryError"], "bootstatus failed")
            self.assertEqual(failure["restorationFailures"], [])


class SerialDeviceExecutionTests(unittest.TestCase):
    def run_pilot(self, initial_states, failure_device=None, initial_orientations=None, cases=None):
        identity = {"commit": "controlled", "status": "clean"}
        devices = {device: {"udid": device} for device in ace.DEVICES}
        states = dict(initial_states)
        events = []
        settings = {"appearance": "light", "content_size": "large", "increase_contrast": "disabled"}
        flags = {"boldText": False, "reduceMotion": False, "increaseContrast": False, "orientation": "portrait"}

        initial_orientations = initial_orientations or {}
        cases = ace.pilot_cases() if cases is None else cases
        initial_flags = {device: {**flags, "orientation": initial_orientations.get(device, "portrait")}
                         for device in ace.DEVICES}
        native_values = {device: dict(value) for device, value in initial_flags.items()}

        def simulator_state(identifier):
            events.append(("state", identifier))
            return states[identifier]

        def boot(identifier, initial_state):
            events.append(("boot", identifier))
            if states[identifier] == "Shutdown":
                native_values[identifier]["orientation"] = "portrait"
            states[identifier] = "Booted"
            return initial_state == "Shutdown"

        def checked(command, **_kwargs):
            if command[:3] == ["xcrun", "simctl", "shutdown"]:
                if states[command[3]] == "Shutdown":
                    raise ace.RunnerError("duplicate simulator shutdown")
                events.append(("shutdown", command[3]))
                states[command[3]] = "Shutdown"
            return {"exit": 0}

        def native_flags(identifier, _template, _evidence, label, request):
            events.append(("nativeFlags", identifier, label, request["mode"]))
            if request["mode"] == "read":
                return dict(native_values[identifier])
            native_values[identifier] = {key: request[key] for key in flags}
            return dict(native_values[identifier])

        def run_batch(device, _identifier, _settings, _cases, _build, _evidence, index):
            events.append(("batch", device, index))
            (evidence / "batches" / f"{index:03d}").mkdir(parents=True, exist_ok=True)
            if device == failure_device:
                raise ace.RunnerError("first device native failure")
            return {"device": device, "nativeTestCount": 1, "caseRecords": []}

        with tempfile.TemporaryDirectory() as directory:
            evidence = Path(directory)
            (evidence / "restoration").mkdir()
            with patch.object(ace, "preflight", return_value={"devices": devices}), \
                 patch.object(ace, "candidate", return_value=identity), \
                 patch.object(ace, "build", return_value={"template": "unused"}), \
                 patch.object(ace, "simulator_state", side_effect=simulator_state), \
                 patch.object(ace, "boot_required_simulator", side_effect=boot), \
                 patch.object(ace, "checked", side_effect=checked), \
                 patch.object(ace, "current_simctl_settings", return_value=settings), \
                 patch.object(ace, "native_flags", side_effect=native_flags), \
                 patch.object(ace, "restore_simctl_settings", side_effect=lambda identifier, _previous, _evidence, _device, phase: events.append(("restoreSettings", identifier, phase)) or []), \
                 patch.object(ace, "run_batch", side_effect=run_batch):
                if failure_device is None:
                    result = ace.run_coverage(cases, evidence)
                else:
                    with self.assertRaisesRegex(ace.RunnerError, "first device native failure"):
                        ace.run_coverage(cases, evidence)
                    result = None
        return events, states, result, native_values

    def test_runs_one_required_device_before_booting_the_next(self):
        events, states, result, _native_values = self.run_pilot({device: "Shutdown" for device in ace.DEVICES})
        first_iphone17_batch = next(index for index, event in enumerate(events) if event[0] == "batch" and event[1] == "iPhone 17")
        pro_max_boot = next(index for index, event in enumerate(events) if event == ("boot", "iPhone 17 Pro Max"))
        iphone17_shutdown = next(index for index, event in enumerate(events) if event == ("shutdown", "iPhone 17"))
        self.assertLess(first_iphone17_batch, pro_max_boot)
        self.assertLess(iphone17_shutdown, pro_max_boot)
        self.assertEqual(states, {device: "Shutdown" for device in ace.DEVICES})
        shutdowns = {device: sum(event == ("shutdown", device) for event in events) for device in ace.DEVICES}
        self.assertEqual(shutdowns, {device: 1 for device in ace.DEVICES})
        self.assertEqual(result["caseCount"], 22)
        self.assertEqual(sum(ace.expected_audit_invocations(case) for case in ace.pilot_cases()), 36)

    def test_full_plan_finishes_one_device_before_starting_the_next(self):
        events, states, result, _native_values = self.run_pilot(
            {device: "Shutdown" for device in ace.DEVICES}, cases=ace.coverage_cases()
        )
        batch_devices = [event[1] for event in events if event[0] == "batch"]
        self.assertEqual(batch_devices, sorted(batch_devices, key=ace.DEVICES.index))
        pro_max_boot = next(index for index, event in enumerate(events) if event == ("boot", "iPhone 17 Pro Max"))
        last_iphone17_batch = max(index for index, event in enumerate(events) if event[0] == "batch" and event[1] == "iPhone 17")
        self.assertLess(last_iphone17_batch, pro_max_boot)
        self.assertEqual(states, {device: "Shutdown" for device in ace.DEVICES})
        self.assertEqual(result["caseCount"], len(ace.coverage_cases()))

    def test_parks_initially_booted_idle_device_and_restores_boot_states(self):
        events, states, _result, native_values = self.run_pilot({device: "Booted" for device in ace.DEVICES},
                                                                  initial_orientations={device: "landscape" for device in ace.DEVICES})
        first_iphone17_batch = next(index for index, event in enumerate(events) if event[0] == "batch" and event[1] == "iPhone 17")
        pro_max_shutdown = next(index for index, event in enumerate(events) if event == ("shutdown", "iPhone 17 Pro Max"))
        self.assertLess(pro_max_shutdown, first_iphone17_batch)
        pro_max_native_read = next(index for index, event in enumerate(events) if event == ("nativeFlags", "iPhone 17 Pro Max", "iPhone 17 Pro Max-read", "read"))
        self.assertLess(pro_max_native_read, pro_max_shutdown)
        self.assertEqual(states, {device: "Booted" for device in ace.DEVICES})
        expected_flags = {"boldText": False, "reduceMotion": False, "increaseContrast": False, "orientation": "landscape"}
        self.assertEqual(native_values, {device: dict(expected_flags) for device in ace.DEVICES})

    def test_uses_unique_native_restore_evidence_labels(self):
        events, _states, _result, _native_values = self.run_pilot(
            {device: "Booted" for device in ace.DEVICES}, initial_orientations={device: "landscape" for device in ace.DEVICES}
        )
        restore_labels = [event[2] for event in events if event[0] == "nativeFlags" and "-restore-" in event[2]]
        self.assertEqual(len(restore_labels), len(set(restore_labels)))
        self.assertIn("iPhone 17-restore-batch", restore_labels)
        self.assertIn("iPhone 17-restore-post-boot", restore_labels)
        self.assertIn("iPhone 17 Pro Max-restore-batch", restore_labels)
        simctl_labels = [(event[1], event[2]) for event in events if event[0] == "restoreSettings"]
        self.assertEqual(len(simctl_labels), len(set(simctl_labels)))
        self.assertIn(("iPhone 17", "batch"), simctl_labels)
        self.assertIn(("iPhone 17", "post-boot"), simctl_labels)

    def test_simctl_restoration_evidence_includes_phase(self):
        previous = {"appearance": "light", "content_size": "large", "increase_contrast": "disabled"}
        with tempfile.TemporaryDirectory() as directory:
            evidence = Path(directory)
            with patch.object(ace, "command", return_value={"exit": 0}), \
                 patch.object(ace, "current_simctl_settings", return_value=previous):
                self.assertEqual(ace.restore_device_configuration("test-udid", previous, None, Path("unused"), evidence, "iPhone 17", "batch"), [])
                self.assertEqual(ace.restore_device_configuration("test-udid", previous, None, Path("unused"), evidence, "iPhone 17", "post-boot"), [])
            names = {path.name for path in (evidence / "restoration").iterdir()}
        self.assertEqual(names, {
            "iPhone 17-simctl-batch-commands.json", "iPhone 17-simctl-batch-readback.json",
            "iPhone 17-simctl-post-boot-commands.json", "iPhone 17-simctl-post-boot-readback.json",
        })

    def test_records_all_initial_boot_states_before_parking(self):
        events, _states, _result, _native_values = self.run_pilot({device: "Booted" for device in ace.DEVICES})
        first_shutdown = next(index for index, event in enumerate(events) if event[0] == "shutdown")
        initial_state_reads = [index for index, event in enumerate(events) if event[0] == "state"][:len(ace.DEVICES)]
        self.assertEqual(len(initial_state_reads), len(ace.DEVICES))
        self.assertTrue(all(index < first_shutdown for index in initial_state_reads))

    def test_first_device_failure_does_not_start_the_second_device(self):
        events, states, result, _native_values = self.run_pilot({device: "Shutdown" for device in ace.DEVICES}, failure_device="iPhone 17")
        self.assertIsNone(result)
        self.assertFalse(any(event[0] in {"boot", "nativeFlags", "batch"} and event[1] == "iPhone 17 Pro Max" for event in events))
        self.assertEqual(states, {device: "Shutdown" for device in ace.DEVICES})

    def test_mixed_boot_state_restores_landscape_after_final_boot(self):
        initial_states = {"iPhone 17": "Shutdown", "iPhone 17 Pro Max": "Booted"}
        _events, states, _result, native_values = self.run_pilot(
            initial_states, initial_orientations={"iPhone 17 Pro Max": "landscape"}
        )
        self.assertEqual(states, initial_states)
        self.assertEqual(native_values["iPhone 17 Pro Max"]["orientation"], "landscape")

    def test_first_device_failure_restores_parked_landscape_device_after_final_boot(self):
        initial_states = {"iPhone 17": "Shutdown", "iPhone 17 Pro Max": "Booted"}
        events, states, result, native_values = self.run_pilot(
            initial_states, failure_device="iPhone 17", initial_orientations={"iPhone 17 Pro Max": "landscape"}
        )
        self.assertIsNone(result)
        self.assertFalse(any(event[0] == "batch" and event[1] == "iPhone 17 Pro Max" for event in events))
        self.assertEqual(states, initial_states)
        self.assertEqual(native_values["iPhone 17 Pro Max"]["orientation"], "landscape")

class CommandAndResourceEvidenceTests(unittest.TestCase):
    def full_gate_fixture(self, root: Path):
        candidate = {"commit": "candidate", "status": "clean"}
        grouped: dict[tuple[str, ace.Settings], list[ace.Case]] = {}
        for case in ace.pilot_cases():
            grouped.setdefault((case.device, case.settings), []).append(case)
        self.assertEqual(len(grouped), 6)
        batches = []
        for number, ((device, _settings), cases) in enumerate(grouped.items(), 1):
            run = root / f"batch-{number}"
            bundle, attachments = run / "result.xcresult", run / "attachments"
            bundle.mkdir(parents=True)
            (bundle / "result").write_text("native result", encoding="utf-8")
            attachments.mkdir()
            native_attachments, records = [], []
            for index, case in enumerate(cases, 1):
                exported = f"{number:08X}-0000-4000-8000-{index:012X}.png"
                (attachments / exported).write_bytes((case.id + " image").encode("utf-8"))
                native_attachments.append({"exportedFileName": exported, "suggestedHumanReadableName": case.id})
                records.append({"id": case.id, "scenario": case.scenario, "observed": case.settings.payload(),
                                "result": "passed", "screenshots": [case.id],
                                "auditInvocations": ace.expected_audit_invocations(case)})
            unmapped = f"{number:08X}-0000-4000-8000-FFFFFFFFFFFF.png"
            (attachments / unmapped).write_bytes(b"native image without a case marker")
            (attachments / "manifest.json").write_text(json.dumps([{"attachments": native_attachments}]), encoding="utf-8")
            summary, log = run / "native-summary.json", run / "native.log"
            summary.write_text("summary", encoding="utf-8")
            log.write_text("native log", encoding="utf-8")
            batches.append({"device": device, "exit": 0, "resultBundle": str(bundle),
                            "attachmentDirectory": str(attachments), "resultBundleSha256": ace.directory_hash(bundle),
                            "attachmentSha256": ace.directory_hash(attachments), "summarySha256": ace.sha256(summary),
                            "logSha256": ace.sha256(log), "caseRecords": records})
        readiness_paths = {}
        for role in ace.READINESS_ROLES:
            artifact = root / f"{role}-artifact.txt"
            artifact.write_text(role, encoding="utf-8")
            record = root / f"{role}.json"
            record.write_text(json.dumps({"role": role, "candidate": candidate, "status": "passed",
                "evidence": [{"path": str(artifact), "sha256": ace.sha256(artifact)}]}), encoding="utf-8")
            readiness_paths[role] = record
        readiness = ace.pilot_readiness(candidate, readiness_paths)
        products = root / "products"
        products.mkdir()
        pilot = {"mode": "pilot", "candidate": candidate, "readinessEvidence": readiness,
                 "build": {"products": str(products)},
                 "caseCount": 22, "auditCount": 20, "layoutCount": 2, "batches": batches}
        manifest = root / "pilot-manifest.json"
        manifest.write_text(json.dumps(pilot), encoding="utf-8")
        captures, max_raw = ace.pilot_capture_measurements(pilot)
        hashes, max_case_images, max_unmapped = ace.pilot_image_measurements(pilot, captures)
        remaining = tuple(case for case in ace.coverage_cases()
                          if ace.canonical_case(case.device, case.scenario, case.settings.payload()) not in captures)
        remaining_images = len(remaining) * max_case_images + len(ace.coverage_batches(remaining)) * max_unmapped
        raw = len(remaining) * max_raw
        proof = root / "retention.txt"
        proof.write_text("retained", encoding="utf-8")
        resources = {"pilotMaxRawBatchBytes": max_raw, "rawPerRemainingCaseUpperBoundBytes": max_raw,
                     "pilotMaxCaseImageCount": max_case_images, "pilotMaxUnmappedBatchImageCount": max_unmapped,
                     "remainingImageCount": remaining_images, "remainingRawEvidenceBytes": raw,
                     "scratchBytes": 0, "requiredFreeBytes": 2 * raw + ace.MIN_FREE_BYTES,
                     "perImageReviewSeconds": 1, "projectedImageInspectionSeconds": remaining_images}
        ledger = {"status": "passed", "candidate": candidate, "pilotManifestSha256": ace.sha256(manifest),
                  "resourceGate": resources, "reviewMeasurement": {"elapsedSeconds": len(hashes),
                  "inspectedImageSha256": sorted(hashes)}, "reviewedImageSha256": sorted(hashes),
                  "retrievalEvidence": {"path": str(proof), "sha256": ace.sha256(proof)},
                  "retentionEvidence": {"path": str(proof), "sha256": ace.sha256(proof)}}
        ledger_path = root / "review-ledger.json"
        ledger_path.write_text(json.dumps(ledger), encoding="utf-8")
        return candidate, manifest, ledger_path, batches[0], Path(batches[0]["attachmentDirectory"])

    def test_timeout_retains_partial_streams_in_the_command_log(self):
        script = "import sys,time; print('partial stdout', flush=True); print('partial stderr', file=sys.stderr, flush=True); time.sleep(2)"
        record = ace.command([sys.executable, "-c", script], timeout=1)
        self.assertIsNone(record["exit"])
        self.assertTrue(record["timedOut"])
        self.assertIn("partial stdout", record["stdout"])
        self.assertIn("partial stderr", record["stderr"])
        with tempfile.TemporaryDirectory() as directory:
            log = Path(directory) / "native.log"
            log.write_text(record["stdout"] + record["stderr"], encoding="utf-8")
            self.assertIn("partial stdout", log.read_text(encoding="utf-8"))
            self.assertIn("partial stderr", log.read_text(encoding="utf-8"))

    def test_case_linked_pilot_capture_rejects_missing_or_changed_attachment(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            run = root / "batch"
            bundle = run / "result.xcresult"
            attachments = run / "attachments"
            bundle.mkdir(parents=True)
            attachments.mkdir()
            image = attachments / "E28C726E-95E6-4B9A-B95B-3C717BD48381.png"
            image.write_bytes(b"first image")
            (attachments / "manifest.json").write_text(json.dumps([{"attachments": [{
                "exportedFileName": image.name, "suggestedHumanReadableName": "case-image",
            }]}]), encoding="utf-8")
            pilot = {"batches": [{"device": "iPhone 17", "resultBundle": str(bundle),
                "attachmentDirectory": str(attachments), "caseRecords": [{"scenario": "signIn",
                "observed": {"appearance": "light"}, "screenshots": ["case-image"]}]}]}
            captures, maximum = ace.pilot_capture_measurements(pilot)
            self.assertEqual(len(captures), 1)
            self.assertGreaterEqual(maximum, len(b"first image"))
            image.unlink()
            with self.assertRaisesRegex(ace.RunnerError, "exported"):
                ace.pilot_capture_measurements(pilot)
            image.write_bytes(b"changed image")
            original_hash = next(iter(next(iter(captures.values()))))
            changed_hash = next(iter(next(iter(ace.pilot_capture_measurements(pilot)[0].values()))))
            self.assertNotEqual(changed_hash, original_hash)

    def test_measured_review_projection_requires_complete_affordable_evidence(self):
        candidate = {"commit": "candidate", "status": "clean"}
        hashes = {"a" * 64}
        resources = {"perImageReviewSeconds": 2, "projectedImageInspectionSeconds": 20}
        ledger = {"reviewMeasurement": {"elapsedSeconds": 2, "inspectedImageSha256": sorted(hashes)}}
        ace.validate_review_projection(resources, ledger, candidate, "b" * 64, hashes, 10)
        ledger["reviewMeasurement"]["inspectedImageSha256"] = []
        with self.assertRaisesRegex(ace.RunnerError, "incomplete"):
            ace.validate_review_projection(resources, ledger, candidate, "b" * 64, hashes, 10)

    def test_over_threshold_projection_requires_measured_review_arrangement(self):
        candidate = {"commit": "candidate", "status": "clean"}
        hashes = {"a" * 64}
        remaining = 10_000
        resources = {"perImageReviewSeconds": 4, "projectedImageInspectionSeconds": 40_000}
        ledger = {"reviewMeasurement": {"elapsedSeconds": 4, "inspectedImageSha256": sorted(hashes)}}
        with self.assertRaisesRegex(ace.RunnerError, "arrangement"):
            ace.validate_review_projection(resources, ledger, candidate, "b" * 64, hashes, remaining)
        with tempfile.TemporaryDirectory() as directory:
            proof = Path(directory) / "review-method.txt"
            proof.write_text("measured review method", encoding="utf-8")
            ledger["reviewArrangement"] = {"candidate": candidate, "pilotManifestSha256": "b" * 64,
                "method": "second measured review", "uniquePilotImageSha256": sorted(hashes),
                "measuredPilotReviewSeconds": 4, "elapsedSeconds": 2,
                "inspectedImageSha256": sorted(hashes), "perImageSeconds": 2,
                "projectedActiveSeconds": 20_000,
                "evidence": [{"path": str(proof), "sha256": ace.sha256(proof)}]}
            ace.validate_review_projection(resources, ledger, candidate, "b" * 64, hashes, remaining)
            ledger["reviewArrangement"]["projectedActiveSeconds"] = 40_000
            with self.assertRaisesRegex(ace.RunnerError, "affordable"):
                ace.validate_review_projection(resources, ledger, candidate, "b" * 64, hashes, remaining)

    def test_full_gate_reconstructs_22_case_pilot_and_rejects_changed_image(self):
        with tempfile.TemporaryDirectory() as directory:
            candidate, manifest, ledger, batch, attachments = self.full_gate_fixture(Path(directory))
            required = json.loads(ledger.read_text(encoding="utf-8"))["resourceGate"]["requiredFreeBytes"]
            with patch.object(ace.shutil, "disk_usage", return_value=SimpleNamespace(free=required)):
                self.assertEqual(ace.validate_full_gate(manifest, ledger, candidate)["caseCount"], 22)
                image = next(path for path in attachments.iterdir() if path.suffix == ".png")
                image.write_bytes(b"x" * image.stat().st_size)
                batch["attachmentSha256"] = ace.directory_hash(attachments)
                pilot = json.loads(manifest.read_text(encoding="utf-8"))
                pilot["batches"][0]["attachmentSha256"] = batch["attachmentSha256"]
                manifest.write_text(json.dumps(pilot), encoding="utf-8")
                ledger_data = json.loads(ledger.read_text(encoding="utf-8"))
                ledger_data["pilotManifestSha256"] = ace.sha256(manifest)
                ledger.write_text(json.dumps(ledger_data), encoding="utf-8")
                with self.assertRaisesRegex(ace.RunnerError, "review measurement"):
                    ace.validate_full_gate(manifest, ledger, candidate)

    def test_full_gate_rejects_unreviewed_retained_native_image(self):
        with tempfile.TemporaryDirectory() as directory:
            candidate, manifest, ledger, _batch, _attachments = self.full_gate_fixture(Path(directory))
            ledger_data = json.loads(ledger.read_text(encoding="utf-8"))
            ledger_data["reviewMeasurement"]["inspectedImageSha256"].pop()
            ledger.write_text(json.dumps(ledger_data), encoding="utf-8")
            required = ledger_data["resourceGate"]["requiredFreeBytes"]
            with patch.object(ace.shutil, "disk_usage", return_value=SimpleNamespace(free=required)):
                with self.assertRaisesRegex(ace.RunnerError, "review measurement"):
                    ace.validate_full_gate(manifest, ledger, candidate)


if __name__ == "__main__":
    unittest.main()
