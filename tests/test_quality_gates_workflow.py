"""Static contracts for the GitHub iOS aggregate gate."""
from pathlib import Path
import unittest


WORKFLOW = Path(__file__).parents[1] / ".github/workflows/quality-gates.yml"


class QualityGatesWorkflowTests(unittest.TestCase):
    def test_ios_changes_select_a_substantive_github_gate(self) -> None:
        workflow = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("ios: ${{ steps.paths.outputs.ios }}", workflow)
        self.assertIn("ios/*)", workflow)
        self.assertIn("ios-contract:", workflow)
        self.assertIn("needs.changes.outputs.ios == 'true'", workflow)
        self.assertIn("ios-contract]", workflow)
        self.assertIn('[[ "$IOS_CHANGED" != true || "$IOS_RESULT" == success ]]', workflow)
