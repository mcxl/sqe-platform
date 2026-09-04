import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


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


if __name__ == "__main__":
    unittest.main()
