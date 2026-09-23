# Sift-KG Fictional-Data Pilot

## Status

This is a separate pilot specification. It does not approve implementation.

## Goal

Test whether Sift-KG can supply useful source-linked proposals to ACE.

Test its graph only as a disposable exploration view.

## Pilot Boundary

- Use fictional documents only.
- Use no real client information.
- Use no public hosted demo.
- Add no dependency or tool without approval.
- Treat each remote model call as an external data transfer.
- Keep ACE as the authoritative audit system.
- Keep every Sift-KG output unapproved.
- Import raw results into ACE proposal queues.
- Do not import graph merges as approved data.
- Keep the mobile app outside this pilot.

## Fictional Test Set

Create two fictional Engagements. Use separate source sets and similar control names.

Each source set must include:

- One policy with a named Accountable Role.
- One procedure with a different role description.
- One source with a trigger date.
- One source with a conflicting trigger date.
- One source with an unsupported possible relationship.
- Stable page, section and paragraph locations.

The design must make cross-Engagement leakage easy to detect.

## Pilot Flow

```text
ACE selects fictional source parts
      -> extraction adapter
      -> Sift-KG and approved model path
      -> immutable raw extraction result
      -> ACE proposal queues ○
      -> auditor accepts, changes or rejects
      -> confirmed ACE version ✓
```

The exploratory graph can show candidates before review.

It cannot write an ACE decision. A graph merge cannot set `✓`.

## Required Proposal Types

The pilot can propose these types:

- Candidate fact.
- Candidate Binding Obligation.
- Candidate Risk.
- Candidate Control.
- Candidate Accountable Role.
- Candidate Trigger.
- Candidate Evidence Relationship.
- Candidate Risk-Control Relationship.
- Possible conflict.

Do not generate an Approved Conclusion or MATE rating.

## Raw Import Rules

ACE must store the complete raw extraction result before mapping it.

The import must preserve:

- Engagement identifier.
- Source identifier and version.
- Exact supporting source locations.
- Sift-KG version and run identifier.
- Model provider, model and configuration.
- External-transfer status.
- Raw input and output hashes.
- Mapping version.
- Import time.

Each mapped item starts as `○ Suggested`.

Only an ACE Auditor Decision for the same version can create `✓ Confirmed`.

## Source Provenance Tests

- Each proposal links to an existing fictional source version.
- Each proposal shows the exact supporting location.
- Each source hash matches the extracted source.
- Each proposal links to one raw provider result.
- A changed source version creates a new proposal version.
- A missing source location causes import rejection.
- A changed raw result hash causes import rejection.

## Engagement Isolation Tests

- Engagement A requests can select only A sources.
- Engagement B requests can select only B sources.
- A result with a mismatched Engagement identifier is rejected.
- A result with a source from another Engagement is rejected.
- Graph queries for A return no B node, edge or source part.
- Cache reuse cannot place A content in a B result.

## Approval-State Tests

- All imported items display `○ Suggested`.
- Graph operations cannot set an ACE approval state.
- Acceptance records the auditor and exact proposal version.
- Rejection does not delete the proposal or raw result.
- Revision creates a new `○` version.
- `✓ Confirmed` appears only after the matching auditor decision.

## Exploratory Graph Tests

- The graph can rebuild from raw fictional extraction results.
- The graph remains separate from approved ACE projections.
- A graph merge changes only the exploratory workspace.
- Graph deletion does not delete ACE audit records.
- ACE can work when the exploratory graph is unavailable.

## Deletion Tests

Delete all Sift-KG data for fictional Engagement A.

Confirm deletion from:

- copied source parts;
- raw provider working files;
- graph nodes and edges;
- indexes and embeddings;
- caches and sessions;
- controlled temporary files; and
- provider stores covered by the pilot.

Confirm that Engagement B remains unchanged.

Confirm that no A result appears in later A or B graph queries.

Record provider logs, backups, retention periods and deletion delays.

## External-Transfer Tests

- Record whether the model runs locally or remotely.
- Record each remote destination and subprocess provider.
- Block a remote call when the transfer path lacks approval.
- Confirm that no real client information exists in the request.
- Confirm that logs do not contain source text beyond the approved rule.

## Measures

Record these measures without changing audit authority:

- Source-location accuracy.
- Candidate precision after auditor review.
- Missing candidate count.
- Unsupported candidate count.
- Cross-Engagement result count.
- Raw import failure count.
- Deletion result for each store.
- Auditor review time per candidate.

## Pass Conditions

- No real client information enters the pilot.
- Every candidate has usable source provenance.
- Raw results enter ACE proposal queues as suggestions only.
- No graph action creates an approved ACE record.
- Engagement isolation tests pass.
- Deletion tests pass or state each retained item.
- Remote transfer remains blocked unless separately approved.
- The auditor can accept, change or reject each proposal version.

## Stop Conditions

Stop before:

- any real client information;
- a public hosted demo;
- a new dependency or tool;
- an unapproved remote model call;
- an architecture or security-boundary change;
- a public API or schema change; or
- any implementation outside a fresh approved Codex task.

## Decision Output

The pilot can recommend adopt, revise, defer or reject.

It cannot approve production use or real client use.
