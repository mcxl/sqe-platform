# Phase 6 Stage 1: Client Release Service Boundary

## Purpose And Scope

This Stage 1 pilot introduces an internal `ClientReleaseService` facade for
the existing fictional client release lifecycle. It does not change the
client API, HTML, database schema, migrations, triggers, authentication, or
G0 controls. SQLite remains the authority for persistent lifecycle and
history integrity.

## Understand: Complete Release-State Matrix

| State Or Condition | Expected Result | Source Reference | Test Reference Or Explicit Gap |
|---|---|---|---|
| `DRAFT` package | May receive entries and transition only to `PUBLISHED`; it is never current. | `client_release_packages_no_update`; `client_release_packages_validate_publish`; `client_release_entries_no_terminal_insert`. | `TestReleaseEligibility.test_release_package_is_immutable`; `TestClientReleaseServiceBoundary.test_lifecycle_facade_preserves_trigger_enforced_transitions`. |
| `PUBLISHED` package | Is current only while published; there is **at most one** current package per engagement; may transition only to `WITHDRAWN` without content change. | `one_current_release_per_engagement`; `client_release_packages_no_update`. | `TestReleaseEligibility.test_only_one_current_package`; `TestReleaseEligibility.test_published_to_withdrawn_transition_allowed`. |
| `WITHDRAWN` package | Is terminal, not current, and retained in immutable history. | `client_release_packages_no_update`; route query filters `status = 'PUBLISHED'`. | `TestReleaseEligibility.test_withdrawn_package_is_not_current`; `TestClientReleaseServiceBoundary.test_current_release_and_history_use_the_active_connection`. |
| Fresh database | Creates current Phase 6B1 schema, valid seeded package history, active triggers, and positive integer versions. | `WorkbenchStore._initialise`; `_add_phase6a_columns_and_tables`; `_add_phase6b1_tables`. | `TestReleaseEligibility.test_fresh_seed_versions_are_positive_integers_and_unique`; `TestReleaseEligibility.test_fresh_schema_requires_positive_integer_release_versions`. |
| Phase 6A database | Migrates conclusions, audit-event constraint, release entries, and preserves historical released/withdrawn packages for the Phase 6B1 upgrade. | `_build_phase6a_release_database`; `_add_phase6b1_tables`. | `TestActionMigration.test_approved_actions_migration_preserves_rows`; `TestPhase6ATo6B1FictionalUpgrade.test_null_legacy_id_at_version_three_skips_optional_draft_seed`. |
| Phase 6B1 database | Retains action snapshot columns, source-validation triggers, terminal entry trigger, and idempotent reopen behaviour. | `_add_phase6b1_tables`; `_create_phase6b1_release_validation_triggers`; `_create_client_release_entry_terminal_insert_trigger`. | `TestTriggerLifecycle.test_reopen_replaces_terminal_entry_trigger_and_blocks_null_id_entry`; `TestActionMigration.test_approved_actions_migration_preserves_rows`. |
| Approved conclusion source | Only an approved, matching engagement/version conclusion with snapshot and approval-event lineage can publish; released snapshot remains immutable. | `client_release_entries_validate_conclusion_source`; `client_release_packages_validate_publish`. | `TestReleaseEligibility.test_published_package_references_approved_conclusion`; `TestReleaseEligibility.test_source_change_does_not_alter_published_content`. |
| Approved action source | Only an approved, matching engagement/version action with exact action snapshot and approval-event lineage can publish; released snapshot remains immutable. | `client_release_entries_validate_action_source`; `client_release_packages_validate_publish`. | `TestActionReleaseRules.test_missing_owner_blocks_publication`; `TestActionAPIResponse.test_published_action_survives_rejected_status_change`. |
| Invalid, cross-engagement, or changed source | Insert/publication fails closed and no client-visible release mutation occurs. | Source-validation and publication triggers. | `TestActionSourceValidation.test_cross_engagement_action_source_blocked`; `TestConclusionSourceValidation.test_cross_engagement_conclusion_rejected`; `TestReleasePublicationIntegrity.test_legacy_cross_engagement_entry_rejected_after_upgrade`; changed-source immutability is `TestReleaseEligibility.test_source_change_does_not_alter_published_content`. |
| Missing approval or matching audit event | Insert/publication fails closed. | `client_release_entries_validate_action_source`; `client_release_entries_validate_conclusion_source`; `client_release_packages_validate_publish`. | `TestActionSourceValidation.test_candidate_action_source_blocked`; `TestConclusionSourceValidation.test_unapproved_conclusion_rejected`. Explicit gap: matching-event permutations are covered by existing Phase 6B1 validation tests but are not represented by one aggregate test name in this matrix. |
| Invalid action dates or empty required source values | Source insert/publication fails closed. | Approved-action schema checks and action/conclusion source-validation triggers. | `TestActionReleaseRules.test_missing_owner_blocks_publication`; `TestActionReleaseRules.test_missing_target_date_blocks_publication`; `TestTargetDateValidation.test_malformed_date_rejected`; `TestTargetDateValidation.test_impossible_calendar_date_rejected`. |
| Invalid publication or withdrawal metadata | Publication trigger rejects invalid publication metadata; service rejects non-canonical/pre-publication withdrawal time and blank/untrimmed actor before mutation. | `client_release_packages_validate_publish`; `ClientReleaseService.withdraw_release`. | Publication-metadata validation test groups; `TestClientReleaseServiceBoundary.test_withdraw_rejects_invalid_metadata_without_mutation`. |
| Repeated startup | Reinstalls replacement triggers and preserves valid migrated records without duplicate seed events. | `WorkbenchStore._initialise`; trigger replacement helpers; seed `INSERT OR IGNORE` controls. | `TestTriggerLifecycle.test_reopen_replaces_terminal_entry_trigger_and_blocks_null_id_entry`; `TestPhase6ATo6B1FictionalUpgrade.test_null_legacy_id_at_version_three_skips_optional_draft_seed`. |
| Version collisions, non-positive, fractional, or decreasing versions | New inserts and publication fail closed; existing invalid versions fail closed on startup. | Package CHECK; `client_release_packages_require_draft_insert`; `client_release_packages_validate_publish`; `_validate_client_release_package_versions`. | `TestReleasePackageCreationIntegrity.test_existing_invalid_release_versions_fail_closed_during_migration`; `TestReleasePackageCreationIntegrity.test_duplicate_legacy_draft_versions_cannot_publish`; `TestReleasePackageCreationIntegrity.test_zero_negative_fractional_repeated_and_decreasing_versions_reject`. |
| Null release identifiers in supported legacy history | Existing legacy row remains stored, reserves its version, is not publishable, and is returned by internal history with nullable `release_id`; new null IDs are rejected. | `_build_phase6a_release_database`; `client_release_packages_require_draft_insert`; `ClientReleaseService.get_release_history`. | `TestPhase6ATo6B1FictionalUpgrade.test_null_legacy_id_at_version_three_skips_optional_draft_seed`; `TestClientReleaseServiceBoundary.test_history_preserves_supported_null_legacy_release_id`; `TestReleasePackageCreationIntegrity.test_new_release_package_with_null_id_is_rejected`. |
| Null release-entry identifiers | Fresh schema rejects them; legacy null entry IDs fail closed during migration without row changes. | `_add_phase6b1_tables`; `_validate_client_release_entry_ids`. | `TestClientReleaseEntryIdIntegrity.test_fresh_schema_requires_non_null_release_entry_ids`; `TestClientReleaseEntryIdIntegrity.test_legacy_null_entry_ids_fail_closed_without_row_changes`. |

Routes select the current `PUBLISHED` package and its immutable entries, then
project the existing response and HTML. The G0 fictional-data guard remains in
`client_routes.py`. Release migrations and fictional seed history are applied
by `WorkbenchStore._initialise`; trigger installation and re-installation are
also owned there. Audit events are immutable; creation and source-approval
history are required at publication, and publication creates its audit event
through `client_release_packages_auto_publish_event`.

### Evidence Gaps

No pre-existing application write route invokes the release lifecycle. Stage
1 therefore characterises the stored lifecycle and the existing read route;
the facade write operations preserve the trigger-enforced SQL operations for
future internal callers but do not add a route or public write API.

## Specify: Internal Contract

`ClientReleaseService` accepts an active `sqlite3.Connection` for every
operation. It never calls `WorkbenchStore.connect()`. Write operations require
an active caller transaction and use a nested savepoint for their paired
package-and-audit-event SQL. On a caught failure, the service rolls back to and
releases only its savepoint; it never commits or rolls back the caller
transaction. The route opens one connection and passes it to
`get_current_release`, which avoids a second SQLite connection inside a
transaction.

| Operation | Contract | Errors |
|---|---|---|
| `build_draft` | Reject terminal metadata, then insert a `DRAFT` `ReleasePackage` and matching immutable `RELEASE_CREATED` event through one nested savepoint; reload the persisted package. | `ClientReleaseStateError`; SQLite integrity errors remain unchanged. |
| `validate_release` | Confirm the package exists, is `DRAFT`, and contains an entry through the adapter. SQLite performs complete source/history validation when publishing. | `ClientReleaseNotFoundError`, `ClientReleaseStateError`, `ClientReleaseValidationError`. |
| `publish_release` | Require an active caller transaction, then validate and request the existing `DRAFT` to `PUBLISHED` update inside one nested savepoint. | `ClientReleaseNotFoundError`, `ClientReleaseStateError`, `ClientReleaseValidationError`; SQLite trigger errors remain unchanged. |
| `withdraw_release` | Validate a canonical UTC withdrawal time not before publication and a nonblank, trimmed actor; then request the existing `PUBLISHED` to `WITHDRAWN` update and add its immutable withdrawal event through one nested savepoint. | `ClientReleaseNotFoundError`, `ClientReleaseStateError`, `ClientReleaseValidationError`; SQLite trigger errors remain unchanged. |
| `get_current_release` | Return the current immutable package and entries, or `None`. | None. |
| `get_release_history` | Return all package history in descending version order. | None. |

The service coordinates intent and nested savepoints, the adapter owns release
SQL (including entry counting), routes own HTTP and response projection, and
SQLite owns schema, migration, trigger, audit, and transaction enforcement.
Callers commit or roll back their own transaction. History remains append-only
in practice: package content and entries are immutable; only the constrained
published-to-withdrawn transition is allowed.

## In-Bound Improvement Record

- **Problem:** `client_routes.py` directly queried release package and entry
  tables, so the internal release boundary did not exist.
- **Proposal:** Add a small service plus connection-only SQLite adapter, then
  route current-release selection through the service.
- **Safety And Simplicity:** It preserves queries, output projection, active
  triggers, and public routes; no schema or dependency changes are required.
- **Affected Files And Rules:** service, adapter, read route, focused release
  tests, and this record only. G0, authentication, public schema, and all
  SQLite triggers remain unchanged.
- **Proving Tests:** baseline `tests/test_client_release.py`; service current
  release/history characterisation; the same focused suite after the change.

## Review-Follow-Up Improvement Record

| Problem | Proposed Improvement | Why Safer And Simpler | Affected Files And Rules | Proving Tests |
|---|---|---|---|---|
| A creation or withdrawal audit-event insert can fail after its package mutation, leaving partial internal state in the caller transaction. | Wrap each paired adapter mutation in a service-owned nested SQLite savepoint; on failure, `ROLLBACK TO SAVEPOINT` then `RELEASE SAVEPOINT`; never commit or roll back the caller transaction. | The caller keeps transaction ownership while each package/event pair has one all-or-nothing boundary. It adds no schema or trigger change. | `client_release_service.py`, `release_storage.py`, service tests. Existing package, audit-event, and trigger rules remain authoritative. | Force duplicate creation and withdrawal event failures; prove no new package or status change survives and the outer transaction remains usable. |
| Withdrawal accepts unvalidated timestamp and actor values before calling SQLite. | Require canonical UTC `YYYY-MM-DDTHH:MM:SSZ`, require `withdrawn_at >= published_at`, and reject blank or untrimmed `withdrawn_by`. | Service validation gives deterministic internal errors before mutation while retaining SQLite as final lifecycle enforcement. | `client_release_service.py`, service tests, contract record. No public route or API changes. | Non-canonical and pre-publication timestamps; blank and padded actor tests; prove package state is unchanged. |
| `build_draft` can return a caller model containing terminal metadata that was not inserted. | Reject publication and withdrawal metadata on a `DRAFT`, then reload and return the persisted package. | The result cannot misrepresent database state, and the rule matches the existing immutable transition model. | `client_release_service.py`, service tests, contract record. | Terminal metadata rejection and returned-model equality with stored package. |
| Existing connection tests prove argument passing but not visibility of uncommitted state or route connection count. | Characterise uncommitted history visibility via the supplied connection and count route `connect()` calls. | Demonstrates the no-second-connection rule directly without changing route behaviour. | `client_routes.py` tests only; service contract remains connection-owned. | Uncommitted draft appears through the provided connection; route opens exactly one connection. |
| The lifecycle test duplicates ACTION release-entry SQL despite an existing helper with explicit snapshot arguments; entry-count SQL sits in the service rather than the adapter. | Reuse `_insert_action_release_entry` with every source snapshot value supplied explicitly, and move entry counting into `ClientReleaseStorage`. | Reuse preserves trigger-tested insert semantics and reduces duplication; adapter ownership consistently contains release SQL. | `test_client_release.py`, `client_release_service.py`, `release_storage.py`. The helper safely preserves exact snapshots because it accepts title, summary, owner, target date, status, evidence reference, and version. | Lifecycle publication remains trigger-valid with helper inputs; service tests cover missing-entry validation. |
| `publish_release` did not enforce the documented active caller transaction or give validation and update one service-owned unit. | Require an active caller transaction and execute validation plus the trigger-backed publish update through one nested savepoint. | It aligns all internal write operations with the transaction contract, preserves outer transaction ownership, and leaves trigger validation unchanged. | `client_release_service.py`, `test_client_release.py`, contract record. No public route, schema, trigger, or API change. | Publish without an active transaction raises with no mutation; valid publication in an active transaction succeeds. |
| Normal history conversion treated a supported legacy `NULL` package identifier as invalid and could omit history by raising during conversion; the matrix also understated the current-release uniqueness rule. | Return dedicated immutable internal history records with nullable `release_id` for every stored row, and correct the matrix to “at most one” current release with complete source and test evidence. | It preserves audit history without changing public models, routes, schema, or trigger rules, while keeping normal history fields directly usable. | `client_release_service.py`, `test_client_release.py`, this specification. | Phase 6A null-ID upgrade fixture proves null and later valid rows return in descending version order; focused matrix references identify all release-state evidence and explicit gaps. |
