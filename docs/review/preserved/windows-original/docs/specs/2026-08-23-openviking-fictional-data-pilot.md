# OpenViking Fictional-Data Pilot

## Status

OpenViking is a deferred candidate. This specification does not approve implementation.

## Entry Gates

Complete these gates before installation or integration:

1. Legal reviews the OpenViking AGPLv3 licence.
2. Privacy reviews each model, embedding and storage transfer.
3. Architecture confirms that ACE remains authoritative.
4. The user approves each new dependency or tool.
5. The pilot owner confirms that session memory is disabled.

Stop if the product cannot disable session memory for the full pilot.

## Goal

Test whether OpenViking can return useful source-linked context to ACE.

Do not test memory, autonomous decisions, approvals or audit-record storage.

## Pilot Boundary

- Use fictional documents only.
- Use no real client information.
- Use no public hosted demo.
- Run in an approved private environment only.
- Treat remote model and embedding calls as external data transfers.
- Use OpenViking for context search only.
- Disable session memory.
- Keep ACE as the only authoritative audit system.
- Keep the mobile app on the ACE API only.
- Add no dependency or tool without approval.

## Fictional Test Set

Use two separate fictional Engagements with similar terms.

Each Engagement must contain:

- one policy;
- one procedure;
- one inspection record;
- one source with an outdated version;
- one source with a conflicting statement; and
- stable source locations.

The corpus must support positive, negative and cross-Engagement queries.

## Pilot Flow

```text
ACE sends an Engagement-bound context request
      -> retrieval adapter
      -> OpenViking with session memory disabled
      -> ranked source-linked context
      -> ACE workbench context panel
```

The returned context does not create an Evidence Item or proposal.

An auditor can start a separate ACE intake action when the context is useful.

That action must use normal ACE source and proposal controls.

## Retrieval Result Rules

Each result must include:

- Engagement identifier.
- Source identifier and version.
- Exact source location.
- Source-linked context part.
- Result rank and provider score.
- OpenViking, adapter and index versions.
- Model and embedding provider details.
- Run identifier and time.
- External-transfer status.

ACE must reject a result that lacks source identity or location.

ACE must not display `✓` for a retrieval result.

If a result becomes a proposal, the new proposal starts as `○ Suggested`.

## Session-Memory Controls

- Set session memory to disabled in configuration.
- Confirm the setting at start-up.
- Confirm the setting in each retrieval run record.
- Do not send earlier queries or results with a new query.
- Do not restore a prior retrieval session.
- Do not share session identifiers between Engagements.
- Fail the pilot if memory remains after restart or deletion.

## Source Provenance Tests

- Each result links to one allowed fictional source version.
- Each result shows an exact source location.
- Each returned source hash matches the indexed source.
- An outdated source is marked by ACE source controls.
- A missing source location causes result rejection.
- Rebuilding the index keeps source identifiers stable.

## Engagement Isolation Tests

- Engagement A queries search only the A namespace.
- Engagement B queries search only the B namespace.
- An unscoped query is rejected.
- A mismatched result is rejected by ACE.
- A query with a shared term returns no other Engagement result.
- Caches, indexes and logs do not join Engagement content.

## Context-Only Tests

- Retrieval cannot create or change an Auditor Decision.
- Retrieval cannot create or change an Approved Relationship.
- Retrieval cannot create or change an Approved Conclusion.
- Retrieval failure does not change an existing ACE record.
- The mobile app cannot call OpenViking directly.
- Provider credentials do not enter the mobile app.

## Deletion Tests

Delete all OpenViking data for fictional Engagement A.

Confirm deletion from:

- copied source parts;
- indexes and embeddings;
- context and retrieval stores;
- caches;
- session or memory stores;
- controlled temporary files; and
- provider stores covered by the pilot.

Restart the service. Confirm that no A context returns.

Confirm that Engagement B remains complete and searchable.

Record provider logs, backups, retention periods and deletion delays.

The deletion test fails if any session memory remains.

## External-Transfer Tests

- List every model, embedding, storage and telemetry destination.
- Record whether each component is local or remote.
- Block each remote transfer until its path has approval.
- Confirm that no real client information exists in a request.
- Confirm that logs follow the approved content rule.

## Measures

- Relevant result count.
- Unsupported result count.
- Missing source-location count.
- Cross-Engagement result count.
- Outdated-source warning count.
- Session-memory test result.
- Deletion result for each store.
- Auditor time to locate the source.

## Pass Conditions

- Legal review permits the approved pilot form.
- The pilot uses fictional information only.
- Session memory stays disabled.
- Each result has source provenance.
- No result changes an ACE audit record.
- Engagement isolation tests pass.
- Deletion tests pass or state each retained item.
- No mobile client calls OpenViking directly.

## Open Decisions

- Approved deployment and data location.
- Local or remote model and embedding path.
- Index and raw source storage location.
- Retention, logging, telemetry and backup rules.
- The exact session-memory disable control.
- AGPLv3 duties for use, changes, network access and distribution.
- Licence duties for all material dependencies.
- The later rule for moving context into an ACE proposal queue.

## Stop Conditions

Stop before:

- installation without legal and user approval;
- any real client information;
- a public hosted demo;
- enabled or uncertain session memory;
- a new dependency or tool;
- an unapproved remote transfer;
- an architecture or security-boundary change;
- a public API or schema change; or
- implementation outside a fresh approved Codex task.

## Decision Output

The pilot can recommend adopt, revise, defer or reject.

It cannot approve production use or real client use.
