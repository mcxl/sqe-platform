# ACE Provider-Neutral Extraction And Retrieval Boundaries

## Status

This document defines planning boundaries only. It does not approve implementation.

## Purpose

ACE can use several extraction and retrieval providers without changing audit authority.

ACE remains the authoritative audit system. The auditor remains the approval authority.

## Locked Decisions

- Sift-KG supplies proposals and an exploratory graph only.
- ACE imports raw Sift-KG results into proposal queues.
- A Sift-KG graph merge is not approved data.
- OpenViking supplies context search only.
- OpenViking session memory stays disabled for the first pilot.
- The mobile app calls only the ACE API.
- Every pilot uses fictional data only.
- No pilot uses a public hosted demo.
- A remote model call is an external data transfer.
- No implementation can add a dependency or tool without approval.
- OpenViking needs an AGPLv3 legal review before use.
- The workbench shows `○` for suggestions.
- The workbench shows `✓` only after auditor confirmation.

## Authority Boundary

ACE owns these records and actions:

- Engagement and source records.
- Evidence Items and Evidence Reviews.
- Proposal queues and proposal versions.
- Auditor Decisions.
- Approved Relationships and Approved Conclusions.
- MATE and CONTRA gates.
- Audit history and client-safe views.

Providers can return candidate content. They cannot set an ACE approval state.

## Logical Components

### Extraction Adapter

The extraction adapter sends a selected source part to an approved provider.

It returns the raw provider result and a run record. It does not approve the result.

The logical request contains:

- Engagement identifier.
- Source identifier and source version.
- Selected source location.
- Selected source text or a controlled local reference.
- Requested candidate types.
- Approved provider and model configuration.
- A new idempotency key.

The logical result contains:

- Engagement, source and source-version identifiers.
- Exact source locations for each candidate.
- Candidate type, value and provider confidence.
- Provider warnings and raw result.
- Provider, model and configuration versions.
- Run identifier and time.
- External-transfer status.
- Raw result hash.

ACE stores the raw result before it maps candidates into proposal queues.

### Retrieval Adapter

The retrieval adapter receives a bounded context request from ACE.

The logical request contains:

- Engagement identifier.
- Auditor query or approved workbench query.
- Allowed source identifiers and versions.
- Maximum result count.
- Approved provider configuration.
- Session memory set to disabled.

The logical result contains:

- Engagement, source and source-version identifiers.
- Source location and a source-linked context part.
- Result rank and provider score.
- Provider, model and index versions.
- Run identifier and time.
- External-transfer status.

A retrieval result is context only. It does not create an Evidence Item.

It does not create a Proposed Relationship, conclusion or Auditor Decision.

### Exploratory Graph Adapter

The exploratory graph is a disposable provider workspace.

It can show raw Sift-KG candidates and possible links. ACE does not read approvals from it.

No graph merge changes an ACE proposal, decision or approved record.

If ACE later projects approved records, that projection uses a separate read-only path.

## Mobile Boundary

The mobile app calls only a versioned ACE API.

ACE selects and calls any provider adapter on the server side.

The mobile app must not hold provider credentials. It must not call a provider directly.

The mobile app must not keep a second authoritative record.

## Suggestion And Confirmation States

Use `○` for all provider suggestions and imported proposals.

Use `✓` only when ACE finds an approving Auditor Decision for the same proposal version.

A revised proposal returns to `○`. The earlier decision stays in the audit history.

Use a text label with each symbol. Do not use colour or the symbol alone.

## Source Provenance

Each provider run must retain this chain:

```text
Engagement
  -> Source
  -> Source Version
  -> Selected Source Location
  -> Provider Run
  -> Raw Provider Result
  -> ACE Proposal Version Or Retrieval Result
```

Record these fields:

- Engagement identifier.
- Source identifier, name, version and content hash.
- Page, section, paragraph, row, time or byte location.
- Selected text hash where the format permits it.
- Provider, adapter, model and configuration versions.
- Prompt or extraction-rule version where applicable.
- Run time and run identifier.
- External-transfer status and destination class.
- Raw input and output hashes.
- ACE mapping version.
- Proposal or retrieval-result identifier.

Do not claim provenance when a result cannot identify its source location.

## Engagement Isolation

Each request must contain one Engagement identifier.

ACE must confirm that each allowed source belongs to that Engagement.

Provider workspaces, indexes, graphs, caches and logs must use separate Engagement namespaces.

A provider result must match the request Engagement and an allowed source.

ACE must reject missing, unknown or mismatched Engagement identifiers.

Do not use a global query when it can return content from several Engagements.

Do not reuse retrieval sessions, caches or provider memory across Engagements.

## Deletion Tests

Use two fictional Engagements, A and B. Give each Engagement similar terms.

Run these tests for each provider:

1. Delete provider data for Engagement A.
2. Confirm that A sources, indexes, embeddings and graph data are absent.
3. Confirm that A caches, sessions and controlled temporary files are absent.
4. Confirm that A no longer appears in context or graph results.
5. Confirm that Engagement B remains complete and searchable.
6. Confirm that ACE records follow the approved fictional-pilot deletion rule.
7. Record retained provider logs, backups and deletion delays.
8. Record any data that the provider cannot delete.

The test fails if deleted A content appears in any B result.

The test also fails when deletion evidence cannot identify every provider store.

## Failure Controls

ACE must fail closed when provenance, Engagement identity or source identity is missing.

ACE must reject provider claims that an item is approved.

ACE must reject a result from an unapproved model or transfer path.

ACE must show provider failure without changing an earlier ACE decision.

## Open Decisions

| Area | Decision Needed | Gate |
| --- | --- | --- |
| Architecture | Select the first adapter process and transport. | Architecture review |
| Architecture | Select the raw-result format and controlled storage location. | Architecture review |
| Architecture | Select separate stores or strict namespaces for Engagement isolation. | Security review |
| Architecture | Define graph disposal and approved-projection separation. | Architecture review |
| Privacy | Decide whether any remote model can receive fictional pilot text. | Privacy approval |
| Privacy | Set provider logging, telemetry, training and retention rules. | Privacy approval |
| Privacy | Set deletion times and acceptable backup retention. | Privacy approval |
| Privacy | Approve each data location and subprocess provider. | Privacy approval |
| Licence | Confirm the current Sift-KG licence and all material dependencies. | Licence review |
| Licence | Review OpenViking AGPLv3 duties for the proposed use. | Legal review |
| Licence | Decide whether network use, changes or distribution require source release. | Legal review |
| Product | Select the allowed source types for each fictional pilot. | Pilot approval |
| Product | Define when a retrieval result can enter an ACE proposal queue. | Method review |
| Operations | Define deletion evidence and the pilot disposal owner. | Operations review |

No open decision can be treated as approved by an investigation report.

## Implementation Gate

Implementation needs a fresh Codex task and the required Sol Advisor workflow.

The implementation task must name allowed files, tests, time limit and stop conditions.
