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
    def test_mapping_has_44_unique_known_ids_and_six_groups(self):
        mapping, errors = runner.load_mapping()
        self.assertEqual(errors, [])
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

    def test_ios_core_commands_use_controlled_fictional_inputs(self):
        with mock.patch.object(runner.shutil, "which", return_value="xcodebuild"), mock.patch.object(runner, "run_command", return_value={"status": "passed"}) as run_command:
            runner.component_checks("core", "ios")
        self.assertEqual(run_command.call_count, 6)
        for call in run_command.call_args_list:
            self.assertEqual(call.kwargs["environment"], runner.IOS_TEST_ENVIRONMENT)
            self.assertNotIn("expected_failure", call.kwargs)

    def test_ios_release_matrix_uses_appearance_and_expected_rejection(self):
        with mock.patch.object(runner.shutil, "which", return_value="xcodebuild"), mock.patch.object(runner, "run_command", return_value={"status": "passed"}) as run_command:
            runner.component_checks("release", "ios")
        calls = run_command.call_args_list
        release_calls = [call for call in calls if call.args[0].startswith("ios-release-")]
        self.assertEqual(len(release_calls), 20)
        self.assertEqual(sum(call.kwargs["environment"].get("ACE_UI_TEST_APPEARANCE") == "light" for call in release_calls), 10)
        self.assertEqual(sum(call.kwargs["environment"].get("ACE_UI_TEST_APPEARANCE") == "dark" for call in release_calls), 10)
        negative = next(call for call in calls if call.args[0] == "ios-negative-config")
        self.assertEqual(negative.kwargs["environment"], runner.NEGATIVE_CONFIG_ENVIRONMENT)
        self.assertEqual(negative.kwargs["expected_failure"], runner.NEGATIVE_CONFIG_REJECTION)

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
