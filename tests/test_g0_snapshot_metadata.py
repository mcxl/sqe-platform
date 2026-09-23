"""Regression tests: altered G0 seed row metadata must not be trusted.

Main's tests cover a missing snapshot and an altered ``snapshot_json``. These tests cover the
other two columns the loader verifies, ``created_at`` and ``created_by``. Fictional data only.
"""

from pathlib import Path

import pytest

from src.ace.workbench.storage import WorkbenchStore
from tests.test_relationship_review import approve_all_current_relationships


@pytest.mark.parametrize(
    ("column", "value"),
    [("created_at", "2031-01-01T00:00:00Z"), ("created_by", "intruder")],
)
def test_altered_seed_metadata_is_not_loaded_and_blocks_completing_approval(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, column: str, value: str
) -> None:
    from src.ace.workbench.relationship_review import RelationshipReviewService
    from src.ace.workbench.relationship_review_storage import RelationshipReviewStorage

    store = WorkbenchStore(tmp_path / "local-data")
    RelationshipReviewService(store)  # seeds the fictional G0 snapshot
    with store.connect() as connection:
        connection.execute("DROP TRIGGER relationship_trace_input_snapshots_no_update")
        altered = connection.execute(
            f"UPDATE relationship_trace_input_snapshots SET {column} = ?"
            " WHERE engagement_id = 'ENG-FIC-0001'",
            (value,),
        ).rowcount
        connection.commit()
    assert altered == 1

    monkeypatch.setattr(RelationshipReviewStorage, "_seed", staticmethod(lambda connection: None))
    storage = RelationshipReviewStorage(store)
    with store.connect() as connection:
        assert storage._trace_inputs_for_engagement(connection, "ENG-FIC-0001") is None

    review = RelationshipReviewService(store)
    result = approve_all_current_relationships(review)
    assert result["result"]["code"] == "RELATIONSHIP_MATE_REQUIRED"
