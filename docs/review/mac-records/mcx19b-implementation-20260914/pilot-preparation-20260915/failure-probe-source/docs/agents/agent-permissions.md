# Relationship Review Actor Permission Boundary

Agents can read Relationship Review items, save drafts, and request approval previews.

Agents cannot record APPROVED, REJECTED, or CHANGES_REQUIRED decisions.

Only the authenticated Accountable Auditor can record a final Relationship Review decision.

Only the authenticated Accountable Auditor can create a corrected revision after CHANGES_REQUIRED.

All Relationship Review actions use the current READY_FOR_CAPTURE Engagement.

G0 requires an explicitly fictional current Engagement. It blocks all other data.

The pilot queue contains fictional data only.
