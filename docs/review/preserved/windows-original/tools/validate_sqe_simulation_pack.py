"""Validate the synthetic ACE/MATE coaching pack and the local ACE sample set."""

from __future__ import annotations

from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
SCENARIO = ROOT / "docs" / "simulations" / "2026-08-08-sqe-ace-mate-simulation-scenario.md"
COACHING = ROOT / "docs" / "simulations" / "2026-08-08-sqe-ace-mate-coaching-guide.md"
WORKSHEET = ROOT / "docs" / "simulations" / "2026-08-08-sqe-ace-mate-learner-worksheet.md"

REQUIRED_SCOPES = (
    "Governance And Oversight",
    "Safety Management Framework",
    "Risk Register",
    "Identification, Escalation And Monitoring",
    "Third-Party Risk Management",
    "Safety In Design",
)


def check_documents() -> list[str]:
    errors: list[str] = []
    for path in (SCENARIO, COACHING, WORKSHEET):
        if not path.exists():
            errors.append(f"missing simulation file: {path}")
            continue
        text = path.read_text(encoding="utf-8")
        if "fictional" not in text.lower():
            errors.append(f"file does not identify fictional content: {path.name}")
        if "Operational Effectiveness" in text and "does not assess" not in text.lower():
            errors.append(f"assurance boundary needs review: {path.name}")

    scenario_text = SCENARIO.read_text(encoding="utf-8")
    coaching_text = COACHING.read_text(encoding="utf-8")
    worksheet_text = WORKSHEET.read_text(encoding="utf-8")

    for scope in REQUIRED_SCOPES:
        if scope not in scenario_text or scope not in worksheet_text:
            errors.append(f"scope area missing from scenario or worksheet: {scope}")

    for term in (
        "Mandate",
        "Accountability",
        "Trigger",
        "Escalation",
        "CONTRA",
        "Connected Trace",
        "Repeat exercise",
        "Project Kraken",
        "Golden Rules",
    ):
        if term not in coaching_text:
            errors.append(f"coaching term missing: {term}")

    if coaching_text.count("Repeat exercise") < 5:
        errors.append("repeat exercises are not defined for all simulated days")

    return errors


def check_ace_samples() -> list[str]:
    errors: list[str] = []
    try:
        from src.ace.app import SAMPLE_CONTROLS
        from src.ace.domain.enums import ControlRating
        from src.ace.engine.evaluator import evaluate_control
    except Exception as error:  # pragma: no cover - environment diagnostic
        return [f"ACE import failed: {error}"]

    expected = (
        ControlRating.ADEQUATE,
        ControlRating.PARTIALLY_ADEQUATE,
        ControlRating.INADEQUATE,
        ControlRating.PARTIALLY_ADEQUATE,
        ControlRating.INADEQUATE,
    )
    actual = tuple(evaluate_control(control).rating for control in SAMPLE_CONTROLS)
    if actual != expected:
        errors.append(f"ACE sample ratings changed: expected {expected}, got {actual}")

    low_confidence = SAMPLE_CONTROLS[-1]
    if "confidence score is below 0.8" not in (low_confidence.reviewer_notes or ""):
        errors.append("ACE low-confidence sample no longer reports its review flag")
    return errors


def main() -> int:
    errors = check_documents() + check_ace_samples()
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1

    print("Simulation pack: PASS")
    print("Synthetic scenario: PASS")
    print("Six-scope scan: PASS")
    print("Repeat-exercise coverage: PASS")
    print("ACE sample evaluation: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
