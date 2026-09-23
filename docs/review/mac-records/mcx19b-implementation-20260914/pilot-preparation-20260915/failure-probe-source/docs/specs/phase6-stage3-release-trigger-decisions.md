# Phase 6 Stage 3: Release Trigger Decisions

## Purpose And Scope

Stage 3 reviewed every SQLite trigger that participates in the fictional
client-release lifecycle after Stage 2 moved workflow coordination into
`ClientReleaseService`. The review covers fresh databases, Phase 6A and Phase
6B1 upgrades, repeat initialisation, direct SQL, and service lifecycle calls.

No trigger is removed. This is the smallest safe outcome: Stage 2 moved only
creation and withdrawal **coordination** into the service. It did not create a
service-owned SQLite trigger. Every active release-related trigger still
enforces a database boundary that a service check alone cannot protect from
direct SQL, a legacy database, seed recovery, or a future caller.

## Classification Vocabulary

- **Service-owned:** service validation, savepoints, allocation, or paired
  audit writes; not a SQLite trigger.
- **Database-required/keep:** SQLite is the final direct-SQL, migration, or
  immutable-history boundary.
- **Shared/rationalised/keep:** the service provides an earlier error while
  SQLite remains the final authority.

## Understand: Final Trigger Inventory

| Trigger | Table And Event | Business Rule | Service Also Enforces? | Classification | Boundary And Dependency | Evidence |
|---|---|---|---|---|---|---|
| `client_release_packages_require_draft_insert` | `client_release_packages`, `BEFORE INSERT` | New package IDs are present; packages start as `DRAFT`; creator and version are valid and version increases. | Partly; `build_draft` checks only DRAFT input. | Database-required/keep | Consistency and direct-SQL safety; installed after valid history is seeded and reinstalled on open. | `TestReleasePackageInsertBoundary`; `TestReleasePackageCreationIntegrity`. |
| `client_release_packages_no_update` | `client_release_packages`, `BEFORE UPDATE` | Only the allowed state transitions and content-preserving package updates are permitted. | Partly; the service validates withdrawal metadata and writes its withdrawal audit event. | Shared/rationalised/keep | Immutability and direct-SQL safety; rebuilt by Phase 6B1 upgrade. | `TestTriggerBlockedTransitions`; `TestPublicationMetadata`; service lifecycle tests. |
| `client_release_packages_no_delete` | `client_release_packages`, `BEFORE DELETE` | Package history is immutable. | No. | Database-required/keep | Immutability and migration/direct-SQL safety; created idempotently. | `TestReleaseEligibility.test_release_package_is_immutable`; `TestReleaseDirectSqlImmutability.test_published_package_delete_rejected_and_row_unchanged`. |
| `client_release_packages_validate_publish` | `client_release_packages`, `BEFORE UPDATE` | Publication needs valid entries, lineage, approvals, audit events, chronology, and unique increasing versions. | Partly; service requires DRAFT and non-empty entries. | Database-required/keep | Security and consistency boundary for direct SQL and legacy DRAFT entries; replaced after table rebuilds. | `TestReleasePublicationIntegrity`; source-validation and upgrade groups. |
| `client_release_packages_auto_publish_event` | `client_release_packages`, `AFTER UPDATE` | Each DRAFT-to-PUBLISHED transition creates exactly one `RELEASE_PUBLISHED` audit event. | No; deliberately trigger-owned. | Database-required/keep | Publication-audit integrity and direct-SQL safety; recreated after audit-table migration to avoid `_old` references. | `TestReleaseAuditEvents`; `TestTriggerLifecycle`. |
| `client_release_entries_no_terminal_insert` | `client_release_entries`, `BEFORE INSERT` | No entries are added to PUBLISHED or WITHDRAWN packages. | No. | Database-required/keep | Immutable-history and direct-SQL safety; replaced after seeds with NULL-safe identity lookup. | `TestTriggerLifecycle.test_reopen_replaces_terminal_entry_trigger_and_blocks_null_id_entry`. |
| `client_release_entries_no_update` | `client_release_entries`, `BEFORE UPDATE` | Release snapshots are immutable. | No. | Database-required/keep | Immutability and direct-SQL safety; recreated if entry table is rebuilt. | `TestReleaseDirectSqlImmutability.test_release_entry_update_rejected_and_row_unchanged`; entry integrity tests. |
| `client_release_entries_no_delete` | `client_release_entries`, `BEFORE DELETE` | Release snapshots are retained. | No. | Database-required/keep | Immutability and direct-SQL safety; recreated if entry table is rebuilt. | `TestReleaseDirectSqlImmutability.test_release_entry_delete_rejected_and_row_unchanged`; entry integrity tests. |
| `client_release_entries_validate_action_source` | `client_release_entries`, `BEFORE INSERT` for ACTION | Action source, engagement, snapshot, approval, and audit lineage must match. | No. | Database-required/keep | Security and engagement-isolation boundary; replaced after action or audit table migration. | `TestActionSourceValidation`; `TestTriggerLifecycle.test_new_rules_apply_after_upgrade`. |
| `client_release_entries_validate_conclusion_source` | `client_release_entries`, `BEFORE INSERT` for CONCLUSION | Conclusion source, engagement, snapshot, approval, and audit lineage must match. | No. | Database-required/keep | Security and engagement-isolation boundary; replaced after audit-table migration. | `TestConclusionSourceValidation`; `TestReleasePublicationIntegrity`. |
| `client_release_entries_one_conclusion` | `client_release_entries`, `BEFORE INSERT` for CONCLUSION | A package has at most one conclusion. | No. | Database-required/keep | Consistency and direct-SQL safety; publish validation also fails closed for legacy duplicates. | `TestReleaseCreationAndConclusionCardinality`. |
| `client_release_entries_one_action_source` | `client_release_entries`, `BEFORE INSERT` for ACTION | A package has at most one snapshot of an action source version. | No. | Database-required/keep | Consistency and direct-SQL safety; publish validation also fails closed for legacy duplicates. | `TestActionSourceCardinality`. |
| `conclusions_no_update_after_approval` | `conclusions`, `BEFORE UPDATE` | Approved conclusions cannot change. | No. | Database-required/keep | Source immutability and direct-SQL safety; replaced on open. | `TestApprovedConclusionImmutability`. |
| `conclusions_no_delete_after_approval` | `conclusions`, `BEFORE DELETE` | Approved conclusions cannot be removed. | No. | Database-required/keep | Source lineage and direct-SQL safety; replaced on open. | `TestApprovedConclusionImmutability`. |
| `approved_actions_no_update_after_approval` | `approved_actions`, `BEFORE UPDATE` | Approved actions cannot change. | No. | Database-required/keep | Source immutability and direct-SQL safety; recreated after action-table migration. | `TestApprovedActionLock`. |
| `approved_actions_no_delete_after_approval` | `approved_actions`, `BEFORE DELETE` | Approved actions cannot be removed. | No. | Database-required/keep | Source lineage and direct-SQL safety; recreated after action-table migration. | `TestApprovedActionLock`. |
| `engagement_audit_events_no_update` | `engagement_audit_events`, `BEFORE UPDATE` | Audit history cannot change. | No. | Database-required/keep | Audit integrity for service, trigger, and direct-SQL writes; recreated after audit-table migration. | `TestReleaseAuditEvents`; migration tests. |
| `engagement_audit_events_no_delete` | `engagement_audit_events`, `BEFORE DELETE` | Audit history cannot be removed. | No. | Database-required/keep | Audit integrity for service, trigger, and direct-SQL writes; recreated after audit-table migration. | `TestReleaseDirectSqlImmutability.test_engagement_audit_event_delete_rejected_and_row_unchanged`; migration tests. |

## Specify: Ownership Boundary

- **Service-owned:** validation of service inputs, nested savepoints, creation
  audit insertion, withdrawal audit insertion, and caller-owned `BEGIN
  IMMEDIATE` allocation. None is a SQLite trigger and there is no redundant
  service-owned trigger to remove.
- **Database-required:** source immutability and lineage, engagement isolation,
  release and entry immutability, cardinality, version uniqueness, direct-SQL
  lifecycle safety, and immutable audit history.
- **Shared but retained:** the service gives callers early state and
  non-empty-entry errors while the package insert and publication triggers
  remain the final authority. This keeps historical and direct-SQL writes
  fail-closed.
- **Publication audit:** remains trigger-owned. Moving it to the service would
  weaken direct-SQL publication auditing and change the established ownership
  without a separate, safely scoped migration.

### Residual Direct-SQL Boundary

`client_release_packages_no_update` does not require complete withdrawal
metadata or create a withdrawal audit event. Direct SQL can therefore make a
minimal PUBLISHED-to-WITHDRAWN transition without the service-owned withdrawal
event. This is an explicit retained limitation of the current boundary, not a
Stage 3 defect: adding database enforcement would alter lifecycle behaviour and
is outside this minimal refactor.

## In-Bound Improvement Record

| Problem | Improvement | Why Safer And Simpler | Affected Files | Proving Tests |
|---|---|---|---|---|
| Trigger ownership and reopen evidence were distributed across Stage 1, Stage 2, migrations, and release tests. | Record the final inventory, preserve complete immutable audit snapshots across fresh/reopen and predecessor replacement, and distinguish the expected Phase 6A migration audit additions from legacy history. Add direct-SQL immutability regressions for package, entry, and audit deletes plus entry update. | Makes the no-removal decision reviewable with complete audit rows and direct-SQL failure evidence, without altering a database security or consistency boundary. | This decision record, `test_client_release.py`, README, development state. | `TestReleaseTriggerInventory`; `TestReleaseDirectSqlImmutability`; existing migration and service lifecycle groups. |

## Test: Failure-First Evidence

`TestReleaseTriggerInventory` uses one broad query and exact tuple inventory to
fail on missing or unexpected release triggers, then rejects obsolete `_old`
references. It compares complete ordered `(event_id, engagement_id, event_type,
recorded_at, actor)` audit snapshots across fresh initialisation/reopen and a
Phase 6B1 predecessor-trigger upgrade/reopen. For the Phase 6A fixture, it
first captures every legacy audit row, proves those rows remain exact after
upgrade, records the four expected migration events, then preserves the full
upgraded snapshot on reopen. `TestReleaseDirectSqlImmutability` proves the
retained package, entry, and audit boundaries reject direct writes, preserve
the exact protected rows, and leave the outer transaction usable before
rollback.

## Build And Release Outcome

`WorkbenchStore` remains the continuing owner of release migration and trigger
installation after Stage 3. Stage 3 changes no public schema, route,
authentication, dependency, mobile, or Phase 6B2 behaviour. Trigger
installation stays deterministic and idempotent; no migration SQL changes
because the inventory found no obsolete trigger and no safe redundant trigger.
Full-suite, API/HTML, browser, freeze, review, commit, and pull-request actions
remain outside this implementation lane.
