"""Validate the car-safe ACE/MATE learning playbook."""

from __future__ import annotations

from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
PLAYBOOK = ROOT / "docs" / "podcast" / "ACE_MATE_Car_Listening_Playbook.md"
PRINT = ROOT / "docs" / "podcast" / "ACE_MATE_Car_Listening_Playbook_Print.md"
WORKSHEET = ROOT / "docs" / "podcast" / "ACE_MATE_Parked_Practice_Worksheet.md"
SCORECARD = ROOT / "docs" / "podcast" / "ACE_MATE_Progress_Scorecard.md"
SCENARIO = ROOT / "docs" / "simulations" / "2026-08-08-sqe-ace-mate-simulation-scenario.md"
JOURNEY = ROOT / "docs" / "podcast" / "2026-08-09-ace-mate-podlog-learning-journey.md"


def main() -> int:
    errors: list[str] = []
    paths = (PLAYBOOK, PRINT, WORKSHEET, SCORECARD)
    for path in paths:
        if not path.exists():
            errors.append(f"missing file: {path}")

    playbook = PLAYBOOK.read_text(encoding="utf-8") if PLAYBOOK.exists() else ""
    print_version = PRINT.read_text(encoding="utf-8") if PRINT.exists() else ""
    worksheet = WORKSHEET.read_text(encoding="utf-8") if WORKSHEET.exists() else ""
    scorecard = SCORECARD.read_text(encoding="utf-8") if SCORECARD.exists() else ""
    scenario = SCENARIO.read_text(encoding="utf-8") if SCENARIO.exists() else ""
    journey = JOURNEY.read_text(encoding="utf-8") if JOURNEY.exists() else ""

    for text, label in (
        (playbook, "playbook"),
        (print_version, "print version"),
    ):
        for term in (
            "ACE",
            "MATE",
            "Mandate",
            "Accountability",
            "Trigger",
            "Escalation",
            "Operational Effectiveness",
            "Do not read, write or use a screen while driving",
        ):
            if term not in text:
                errors.append(f"{label} missing: {term}")
        for episode in range(6):
            if f"Episode {episode:02d}" not in text:
                errors.append(f"{label} missing Episode {episode:02d}")

    for term in (
        "Score 0-1",
        "Score 2",
        "Score 3",
        "Repeat Exercise",
        "Parked Follow-Up",
        "Progression Check",
    ):
        if term not in playbook:
            errors.append(f"playbook missing adaptive element: {term}")

    for term in ("MATE Record", "Connected Trace", "Repeat Exercise", "Score"):
        if term not in worksheet:
            errors.append(f"worksheet missing: {term}")
    if "Adaptive Rules" not in scorecard:
        errors.append("scorecard missing adaptive rules")

    for text, label in ((scenario, "scenario"), (journey, "podcast journey")):
        if "Energy Inc" not in text:
            errors.append(f"{label} missing Energy Inc case name")
        if "Northstar" in text:
            errors.append(f"{label} still contains the old case name")
    if "wind-farm" not in scenario:
        errors.append("scenario must remain a wind-farm business")

    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1

    print("Car playbook: PASS")
    print("Print version: PASS")
    print("Episode coverage 00-05: PASS")
    print("Safety controls: PASS")
    print("Adaptive learning controls: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
