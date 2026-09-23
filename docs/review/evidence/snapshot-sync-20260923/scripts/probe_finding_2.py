"""Disposable probe: does the loader trust a G0 seed row whose created_at was altered?

Fictional data only. Uses a temporary data directory that is deleted on exit.
"""

import tempfile
from pathlib import Path

import src.ace

print("code under test:", src.ace.__file__)

from src.ace.workbench.relationship_review import RelationshipReviewService  # noqa: E402
from src.ace.workbench.relationship_review_storage import (  # noqa: E402
    RelationshipReviewStorage,
)
from src.ace.workbench.storage import WorkbenchStore  # noqa: E402

with tempfile.TemporaryDirectory() as directory:
    store = WorkbenchStore(Path(directory) / "local-data")
    RelationshipReviewService(store)  # seeds the fictional G0 snapshot
    with store.connect() as connection:
        connection.execute("DROP TRIGGER relationship_trace_input_snapshots_no_update")
        altered = connection.execute(
            "UPDATE relationship_trace_input_snapshots SET created_at = '2031-01-01T00:00:00Z'"
            " WHERE engagement_id = 'ENG-FIC-0001'"
        ).rowcount
        connection.commit()
    print("rows altered:", altered)
    with store.connect() as connection:
        loaded = RelationshipReviewStorage(store)._trace_inputs_for_engagement(
            connection, "ENG-FIC-0001"
        )
    print("tampered row loaded:", loaded is not None)
