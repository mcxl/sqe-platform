"""Run a small synthetic MATE approval and ACE evaluation demonstration."""

from __future__ import annotations

from pathlib import Path
import argparse
import sys


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.ace.domain.assessment import (  # noqa: E402
    AuditorDecision,
    AuditorDecisionStatus,
    ContradictionStatus,
    EvidenceAvailability,
    EvidenceReviewRecord,
    EvidenceSufficiency,
    MateDimension,
    ProposedAnswer,
    ProposedDimensionAssessment,
    SourceReference,
    SourceStatus,
)
from src.ace.domain.enums import HazardCategory  # noqa: E402
from src.ace.engine.approval import ApprovalBlockedError, build_approved_assessment, evaluate_approved_assessment  # noqa: E402


def build_demo(*, unresolved_trigger: bool = False):
    proposals = []
    reviews = []
    decisions = []
    for dimension in MateDimension:
        source = SourceReference(
            source_id=f"SIM-SRC-{dimension.value}",
            document_title=f"Northstar synthetic {dimension.label} record",
            document_version="1.0",
            source_location=f"Section {dimension.label}-1",
            source_wording=f"Synthetic wording for the {dimension.label} assessment.",
            status=SourceStatus.CURRENT,
        )
        review_id = f"SIM-REV-{dimension.value}"
        proposal_id = f"SIM-PROP-{dimension.value}"
        answer = (
            ProposedAnswer.UNRESOLVED
            if unresolved_trigger and dimension is MateDimension.TRIGGER
            else ProposedAnswer.YES
        )
        reviews.append(
            EvidenceReviewRecord(
                review_id=review_id,
                source_references=(source,),
                supporting_source_ids=(source.source_id,),
                evidence_availability=(
                    EvidenceAvailability.REQUESTED_NOT_PROVIDED
                    if answer is ProposedAnswer.UNRESOLVED
                    else EvidenceAvailability.REVIEWED_SUPPORTIVE,
                ),
                contradiction_status=ContradictionStatus.NONE_IDENTIFIED,
                assumptions_checked=("The source is fictional and current.",),
                limitations=("This exercise assesses control design only.",),
                proposed_sufficiency=(
                    EvidenceSufficiency.INSUFFICIENT
                    if answer is ProposedAnswer.UNRESOLVED
                    else EvidenceSufficiency.SUFFICIENT_FOR_DESIGN_ASSESSMENT
                ),
            )
        )
        proposals.append(
            ProposedDimensionAssessment(
                proposal_id=proposal_id,
                proposal_version=1,
                dimension=dimension,
                proposed_answer=answer,
                rationale=f"Synthetic rationale for {dimension.label}.",
                evidence_review_id=review_id,
            )
        )
        decisions.append(
            AuditorDecision(
                decision_id=f"SIM-DEC-{dimension.value}",
                proposal_id=proposal_id,
                proposal_version=1,
                dimension=dimension,
                decision_status=AuditorDecisionStatus.APPROVED,
                approved_answer=True,
                final_sufficiency=EvidenceSufficiency.SUFFICIENT_FOR_DESIGN_ASSESSMENT,
                reviewer_id="LEARNER-LEAD-AUDITOR",
                review_notes="Synthetic training decision.",
                reviewed_at="2026-08-08T00:00:00+00:00",
            )
        )

    return build_approved_assessment(
        control_id="SIM-SID-001",
        title="Synthetic Safety In Design handover control",
        description="Synthetic control for training only.",
        hazard_category=HazardCategory.SAFETY_IN_DESIGN,
        proposals=tuple(proposals),
        evidence_reviews=tuple(reviews),
        decisions=tuple(decisions),
        confidence_score=0.95,
        reviewer_notes="Synthetic exercise. Operational effectiveness is not assessed.",
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--unresolved-trigger",
        action="store_true",
        help="Show the approval gate blocking unresolved Trigger evidence.",
    )
    args = parser.parse_args()

    try:
        result = evaluate_approved_assessment(build_demo(unresolved_trigger=args.unresolved_trigger))
    except ApprovalBlockedError as error:
        print(f"MATE approval blocked as expected: {error}")
        return 0 if args.unresolved_trigger else 1

    print(f"Approved MATE assessment: {result.control_id}")
    print(f"ACE design rating: {result.rating.value}")
    print(f"Failed dimensions: {', '.join(result.failed_dimensions) or 'None'}")
    print("Fictional evidence only; operational effectiveness is not assessed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
