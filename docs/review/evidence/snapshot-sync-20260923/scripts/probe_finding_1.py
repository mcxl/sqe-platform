"""Disposable probe: does a forged (model_construct) approved assessment pass evaluation?

Fictional data only. Run from the repository root with PYTHONPATH set to the checkout.
"""

import src.ace

print("code under test:", src.ace.__file__)

from src.ace.domain.assessment import ApprovedMATEAssessment  # noqa: E402
from src.ace.engine.approval import (  # noqa: E402
    ApprovalBlockedError,
    evaluate_approved_assessment,
)
from tests.test_approval_gate import build_assessment  # noqa: E402

genuine = build_assessment()
forged = ApprovedMATEAssessment.model_construct(
    **{field: getattr(genuine, field) for field in ApprovedMATEAssessment.model_fields}
)
try:
    result = evaluate_approved_assessment(forged)
    print("forged assessment evaluated:", type(result).__name__)
except ApprovalBlockedError as error:
    print("forged assessment blocked:", error)
