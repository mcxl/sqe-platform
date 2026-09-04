# Phase 6 Stage 2: Client Release Workflow

## Purpose And Scope

Stage 2 moves the internal release workflow into `ClientReleaseService` while
preserving the Phase 6A and Phase 6B1 public client API, HTML, schema,
migrations, active triggers, and fictional-data controls. It does not add a
write route or a public release API. `WorkbenchStore` retains migration,
trigger-installation, and fictional seed ownership. Stage 3 confirms this
continuing ownership and records the final trigger decision in
[`phase6-stage3-release-trigger-decisions.md`](phase6-stage3-release-trigger-decisions.md).

## Internal Contract

Every `ClientReleaseService` operation receives the caller's active
`sqlite3.Connection`. The service never opens a connection, commits, or rolls
back the caller's transaction. `begin_release_write(connection)` starts a
fresh outer `BEGIN IMMEDIATE` transaction only when the connection has no
active transaction; after it returns, the caller owns the transaction and its
commit or rollback. Write operations use a nested savepoint, so a package and
its service-coordinated immutable audit event are atomic while the outer
transaction remains usable after a failure.

`build_next_draft` version allocation requires a fresh `BEGIN IMMEDIATE`
before **any** caller reads, normally through `begin_release_write`. Unrestricted
deferred transactions are unsupported for version allocation: they can retain
a stale read snapshot while another allocator commits. Python's `sqlite3` API
does not expose the current `BEGIN` mode, so the service can require an active
transaction but cannot reliably reject a deferred one at runtime.

| Workflow Operation | Service Responsibility | SQLite Adapter Responsibility | Authority |
|---|---|---|---|
| `build_draft` | Validate DRAFT-only input; coordinate package creation then the exact `RELEASE_CREATED` event in one savepoint; return the stored package. | Insert package then its creation audit event using the supplied connection. | SQLite triggers and constraints remain final validation. |
| `begin_release_write` | Start a fresh `BEGIN IMMEDIATE` allocation transaction only when no transaction is active; leave its completion to the caller. | None. | SQLite serialises writers before any allocation read. |
| `build_next_draft` | Require the caller's active immediate transaction; verify engagement existence, then select the next version from all stored package history, including DRAFT, WITHDRAWN, and supported null-ID legacy rows; build and audit the DRAFT in one savepoint. | Check engagement existence and read the next version. | The caller's prior SQLite immediate transaction serialises selection and insertion; stored history reserves every committed version. |
| `validate_release` | Confirm package existence, DRAFT state, and non-empty entries before publication. | Read package and entry count. | Publication triggers validate source snapshots, engagement isolation, approvals, audit lineage, timestamps, and version rules. |
| `publish_release` | Coordinate validation and the DRAFT-to-PUBLISHED request inside a savepoint. | Execute the transition. | `client_release_packages_auto_publish_event` continues to create the exact publication event. |
| `withdraw_release` | Validate canonical UTC time and trimmed actor; coordinate transition then exact `RELEASE_WITHDRAWN` event in one savepoint. | Execute transition then its withdrawal audit insert. | Immutable package transition trigger remains final authority. |
| Current/history/engagement reads | Select package, immutable entries, history, and projection metadata through one supplied connection. | Execute only the required SQL. | The route performs HTTP translation, G0 guarding, and response/HTML projection. |

## Compatibility And Invariants

- Existing Phase 6A and Phase 6B1 history remains readable, including the
  supported nullable `release_id` in internal history records.
- A version is never reused: all stored package rows reserve their version.
- The service retains the exact existing creation and withdrawal event IDs:
  `EVT-{release_id}-CREATED` and `EVT-{release_id}-WDN`. Publication remains
  trigger-audited as `EVT-{release_id}-PUB`.
- Source changes, cross-engagement sources, invalid source values, missing
  approval evidence, missing audit lineage, version collisions, and invalid
  lifecycle transitions continue to fail closed through the active SQLite
  constraints and triggers.
- No route opens a second connection for release or engagement metadata. The
  client route retains authentication, G0 checks, error translation, and the
  byte-compatible response/HTML projection.

## Improvement Record

| Problem | Proposal | Safety And Simplicity | Affected Files | Proving Tests |
|---|---|---|---|---|
| A no-op engagement `UPDATE` upgrades a deferred transaction after callers may already have read a stale snapshot. It also obscures that allocation has a caller transaction precondition. | Replace the no-op update with `begin_release_write`, which issues `BEGIN IMMEDIATE` only before any outer transaction exists. `build_next_draft` requires the active caller transaction but does not claim it can inspect or enforce its begin mode. | The explicit contract obtains the writer reservation before reads, prevents the stale-snapshot upgrade path, preserves caller commit/rollback ownership, and removes an unrelated write. Engagement validation remains a narrow read inside the savepoint. | `client_release_service.py`, `release_storage.py`, `test_client_release.py`, this contract. | Two independent thread-owned connections call `begin_release_write`; the second blocks, then allocates the next version after the first commits. Exact lifecycle snapshots prove package and audit deltas with no extra events. |

## Failure-First Evidence

`TestClientReleaseServiceBoundary` characterises next-version selection,
creation-event deltas, independent-connection serialisation, supplied-connection
engagement reads, route delegation, nested-savepoint rollback, lifecycle
transitions, exact audit deltas, and nullable legacy history. The established
release integrity groups continue to cover source lineage, approval and audit
evidence, version collisions, migrations, repeated startup, and trigger
behaviour.
