# Phase 6B2: Read-Only Client Release Projection

## Scope And Acceptance Contract

This approved Phase 6B2 slice introduces one pure, transport-neutral
`ClientReleaseProjection`. It prepares caller-supplied current release and
engagement data as the existing `ClientReleaseResponse`. It adds no mobile
client, endpoint, field, write path, schema, migration, trigger, dependency,
or authentication change.

The existing `GET /client/api/v1/release/current` API and `GET /client` HTML
page are the compatibility contract. The projection exposes only engagement
name, review status, release version, published time, conclusion title,
summary, evidence reference, and action description, owner, target date, and
delivery status.

## Understand: Baseline And State Matrix

Baseline: `3726793e1c0c6d8c3799cbde2456e72b9b05a3c5`. The required PR 54–58
heads and merges are ancestors of this isolated worktree; `.codegraph` is not
present.

Baseline characterisation used fictional data only. On the baseline,
`TestClientApi`, `TestClientPage`, `TestActionAPIResponse`,
`TestActionHTMLPage`, and `TestClientReleaseServiceBoundary` passed 50 tests.
The captured `GET /client/api/v1/release/current` response was HTTP 200,
`application/json`, 599 bytes, SHA-256
`5e19bc98c09286a2eb8181650462cfb5ae6952eb342da080643d54a8ab6856af`.
It contained the existing six top-level response fields, release version 2,
the approved conclusion snapshot, and one `OPEN` action snapshot. The
captured `GET /client` response was HTTP 200, `text/html; charset=utf-8`,
3,156 bytes, SHA-256
`017f19c4e4ebf5e98cb2c9493deec789a5bbf2107a39f6326c6d4fb8b0788e3d`.

| Domain Condition | Expected Result | Source Reference | Test Reference Or Baseline Gap |
|---|---|---|---|
| Current fictional `PUBLISHED` release | Return the existing response fields from the immutable package and entries. | `ClientReleaseStorage.current_release`; `ClientReleaseProjection.project`. | `TestClientApi.test_valid_credentials_return_current_package`; new `TestClientReleaseProjection.test_projects_current_release_exactly`. |
| No current published release | Return `Release unavailable` with blank metadata, version 0, no conclusion, and no actions. | `ClientReleaseProjection.project` constructs the unavailable response after the route's selected-release read. Baseline evidence: `client_routes._get_client_data` translated its earlier HTTP 404. | Baseline gap: no direct response-model test; new `test_returns_existing_unavailable_response_without_current_release`. |
| `DRAFT` release only | Exclude it: storage selects only `status = 'PUBLISHED'`; consequently return unavailable. | `ClientReleaseStorage.current_release`; `TestReleaseEligibility`. | `TestReleaseEligibility.test_release_package_is_immutable`; new unavailable projection test covers its selected-input outcome. |
| `WITHDRAWN` release only | Exclude it: storage selects only `status = 'PUBLISHED'`; consequently return unavailable. | `ClientReleaseStorage.current_release`. | `TestReleaseEligibility.test_withdrawn_package_is_not_current`; new unavailable projection test covers its selected-input outcome. |
| Valid conclusion snapshot | Return title, summary, and evidence reference from the immutable entry. | `ClientReleaseProjection.project` conclusion branch; baseline implementation was `client_routes._get_client_data`. | `TestClientApi.test_valid_credentials_return_current_package`; new exact projection test. |
| Valid action snapshot | Return description, owner, target date, and delivery status from immutable entry fields. | `ClientReleaseProjection.project` action branch; baseline implementation was `client_routes._get_client_data`. | `TestActionAPIResponse.test_approved_action_appears_in_api`; new exact projection test. |
| More than one valid action | Preserve supplied entry order, which storage defines as `release_entry_id` ascending. | `ClientReleaseStorage.current_release` entry `ORDER BY`; `ClientReleaseProjection.project` action append loop. | Baseline gap: no direct ordering test; new `test_filters_entries_and_preserves_supplied_order`. |
| Missing action owner or target date | Exclude the action. | `ClientReleaseProjection.project` owner/target guard; baseline implementation was `client_routes._get_client_data`. | `TestActionReleaseRules.test_missing_owner_blocks_publication`; `test_missing_target_date_blocks_publication`; new filtering test protects legacy projection behaviour. |
| Invalid action date or delivery status | Exclude the action. | `ClientReleaseProjection.project` delivery and ISO-date guards; baseline implementation was `client_routes._get_client_data`. | `TestTargetDateValidation`; `TestActionReleaseRules.test_invalid_delivery_status_blocked`; new filtering test. |
| Unknown source record type | Exclude it. | `ClientReleaseProjection.project` deliberate skip behaviour; baseline implementation was `client_routes._get_client_data`. | Baseline gap: no direct projection test; new filtering test. |
| Missing engagement record | Return `Engagement not found` with blank metadata, version 0, no conclusion, and no actions when a current release exists. | `ClientReleaseProjection.project` missing-engagement response; baseline implementation was `client_routes._get_client_data`. | Baseline gap: no direct response-model test; new `test_returns_existing_missing_engagement_response`. |
| Non-fictional engagement | Return HTTP 503 with the current generic unavailable error before projection. | `client_routes._get_client_data` G0 guard. | `TestClientApi.test_g0_guard_rejects_non_fictional_engagement`. |
| Cross-engagement request | Return no release or action information for another engagement. | `require_client`; `ClientReleaseStorage.current_release` parameterised engagement filter; release triggers. | `TestActionAPIResponse.test_other_engagement_action_hidden`; `TestActionIntegrity.test_other_engagement_release_package_hidden`. |
| Missing or invalid client credentials | Preserve independent client authentication: generic HTTP 403; missing configuration fails closed with HTTP 503. | `require_client` dependency retained by both routes. | `TestClientApi.test_missing_credentials_return_403`; `test_invalid_credentials_return_403`; `test_missing_configuration_fails_closed`. |
| Successful read | Leave release packages, entries, sources, and audit rows unchanged; use one route-owned connection; retain all 18 release triggers. | Read-only `ClientReleaseStorage` methods; route `store.connect()` context; `WorkbenchStore` trigger ownership. | `TestClientApi.test_client_get_endpoints_leave_release_rows_unchanged`; `TestClientReleaseServiceBoundary.test_current_release_and_history_use_the_active_connection`; `test_route_delegates...`; `TestReleaseTriggerInventory`. |

The prior route mixed current-release response projection with HTTP, G0, and
connection responsibilities. The recorded baseline gaps are adapter-level
characterisation gaps, not unknown behaviour. The failure-first tests named in
the matrix define the existing results before the adapter is implemented.

## Specify: Transport-Neutral Projection Contract

### Inputs And Output

`ClientReleaseProjection.project(package, entries, engagement)` accepts only
caller-provided mappings:

- `package` is the current `PUBLISHED` package selected by the service, or
  `None` when no current package exists;
- `entries` are that package's immutable release entries in storage order;
- `engagement` is the caller-supplied engagement metadata, or `None` when the
  current package has no engagement record.

It returns the existing `ClientReleaseResponse` model and never returns
internal identifiers, approval attribution, audit history, package history, or
withdrawal details.

The adapter performs no SQL, opens no connection, starts no transaction, and
performs no write. It does not authenticate, evaluate G0, translate HTTP
errors, select packages, or render HTML.

### Filtering, Ordering, And Empty States

The service/storage layer selects the current package only from `PUBLISHED`
packages for the authenticated engagement and orders its entries by
`release_entry_id`. The adapter trusts that supplied current-release selection
and projects only `CONCLUSION` and valid `ACTION` snapshots:

- a conclusion copies title, summary, and evidence reference;
- an action copies description, owner, target date, and delivery status only
  when owner and target date are non-empty, delivery status is `OPEN` or
  `COMPLETE`, and target date is an exact ISO calendar date;
- invalid action snapshots and unknown entry types are excluded without
  reordering valid actions.

With no package, it returns the established `Release unavailable` response.
With a package but no engagement, it returns the established `Engagement not
found` response. Otherwise it returns the engagement title/state, package
version/publication time, and the filtered snapshots. These rules retain the
current empty HTML behaviour because the unchanged renderer receives the same
response model.

### Ownership And Compatibility

- `ClientReleaseService` remains lifecycle authority and reads current-release
  and engagement data via `ClientReleaseStorage` using the one caller-owned
  route connection.
- `ClientReleaseStorage` remains the sole release SQL owner. `WorkbenchStore`
  remains migration and trigger-installation owner.
- The route retains HTTP dependencies, client authentication, G0 validation
  and its HTTP 503 response, the one `store.connect()` call, and the unchanged
  HTML renderer. It does not construct unavailable responses or translate a
  no-current-release condition to HTTP 404 in the final design.
- The adapter owns response projection, including the unavailable and missing
  engagement responses. It must not call `begin_release_write()`.

No route/API/schema/trigger/migration/authentication/dependency/mobile or
user-visible change is compatible with this contract. The existing raw API and
HTML byte records above are acceptance evidence.

## In-Bound Improvement Record

| Required Record | Decision |
|---|---|
| Current problem | Current response projection is embedded in the route, so a future mobile adapter would duplicate filtering and snapshot rules. |
| Proposed improvement | Move only pure response projection into `ClientReleaseProjection`; delegate to it after the route's unchanged service reads and G0 guard. |
| Safer or simpler | One mapping-only implementation removes duplication while retaining the route's connection, HTTP, authentication, G0, selection, and HTML responsibilities. |
| Affected allowed files | `docs/specs/phase6b2-read-only-client-release-projection.md`, `client_release_projection.py`, `client_routes.py`, `test_client_release_projection.py`, and `test_client_release.py`. |
| Proving tests | Baseline byte characterisation; failure-first pure adapter tests; focused API/HTML, G0/authentication, one-connection, no-mutation, and 18-trigger inventory tests. |
