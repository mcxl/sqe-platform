# Phase 6B2 Controlled Client Release Lifecycle

## Document Status

Status: Draft For Review

Date: 22 August 2026

This specification does not authorise implementation.

Phase 6B2 stays blocked until pull request 52 merges. The baseline must use the confirmed merge commit.

Pocock must approve this specification and its acceptance tests before coding starts.

## Phase 6B1 Review

### Evidence Summary

The Phase 6B1 branch activity covered approximately 44 elapsed hours.

At the review point, pull request 52 had these properties:

- 19 commits.
- Four changed files.
- 4,790 additions and 87 deletions.
- 23 Codex P2 findings.
- 12 Codex review records.
- 14 manual Codex review requests.
- One later Greptile P1 finding.

The Greptile finding showed that approval did not bind the approved action content.

The pull request head continued to change during this review. It was not a frozen candidate.

### Root Cause

Phase 6B1 started with a feature description. It did not start with a complete release lifecycle specification.

The first change added action display, schema changes, migrations, seed changes, and lifecycle transitions together.

This change made old Phase 6A lifecycle weaknesses part of the Phase 6B1 scope.

Codex then found each missing rule after the prior fix exposed the next rule.

The review process became the design process. This caused repeated correction and repeated review.

### Five-Why Summary

1. Phase 6B1 took a long time because reviewers found 23 separate P2 defects.
2. Reviewers found defects separately because no complete state and failure matrix existed.
3. The matrix was absent because acceptance tests did not define the lifecycle before coding.
4. Local fixes missed related paths because controls existed in routes, triggers, migrations, and seed logic.
5. Reviews started before the candidate satisfied one approved acceptance-test set.

### Contributing Causes

1. The specification did not define all `DRAFT`, `PUBLISHED`, and `WITHDRAWN` rules.
2. The specification did not define invalid conclusion and action records equally.
3. Upgrade tests did not start with real Phase 6A and Phase 6B1 database shapes.
4. Seed logic used historical event identifiers as lifecycle evidence.
5. Route logic silently hid invalid entries after publication.
6. Database rules did not reject all invalid entries before publication.
7. Publication attribution rules grew through several review cycles.
8. Approval events did not initially bind identity, version, content, actor, and time.
9. Tests followed reviewer findings instead of preceding the implementation.
10. One test explicitly permitted an unchecked conclusion with the wrong version.
11. Initial schema and upgrade rules used more than one control path.
12. The test module grew beyond 4,000 lines through correction-by-correction additions.
13. Codex reviewed several unstable heads instead of one frozen candidate.
14. Pull request records became stale while the branch continued to change.

### Lessons Applied To Phase 6B2

1. Freeze all lifecycle rules before coding.
2. Use one state matrix for actions and conclusions.
3. Test invalid records before testing successful publication.
4. Use server-generated actors and canonical UTC times.
5. Use one transaction for each lifecycle command.
6. Use the package status as lifecycle authority.
7. Keep seed data separate from production lifecycle behaviour.
8. Treat database upgrades as product behaviour.
9. Fail publication when any entry is invalid.
10. Do not silently omit an invalid entry from a published response.
11. Reuse one release assembly and validation seam.
12. Freeze the exact candidate before Codex review.
13. Request Codex once on that stable candidate.
14. Update the pull request record before merge approval.

## Problem Statement

ACE has a protected client release view. Phase 6B1 adds approved actions to that view.

ACE does not yet have a controlled auditor process for new client release versions.

An auditor needs to create, check, preview, publish, and withdraw a release safely.

The process must preserve old releases and their audit history.

The client must see only the current published release.

## Solution

Phase 6B2 will add a controlled client release lifecycle for the auditor.

The auditor will create one complete immutable draft snapshot from approved source records.

The auditor will preview that draft with the same presentation used by the client view.

The auditor will publish the draft through one controlled transaction.

Publication will withdraw the prior current release in the same transaction.

The auditor can withdraw the current release with a required reason.

The client remains read-only. The client sees only the current `PUBLISHED` release.

## User Stories

1. As an auditor, I want to create a release draft from approved records, so that I can prepare client information.
2. As an auditor, I want the system to reject invalid sources, so that a draft contains only approved information.
3. As an auditor, I want one complete draft snapshot, so that its content cannot change without a new draft.
4. As an auditor, I want to preview the draft, so that I can check the client presentation.
5. As an auditor, I want the preview marked as a draft, so that I cannot confuse it with published information.
6. As an auditor, I want the system to recheck the draft before publication, so that stale approval cannot reach the client.
7. As an auditor, I want publication to use one transaction, so that the client never sees partial change.
8. As an auditor, I want a new release version, so that previous client information remains traceable.
9. As an auditor, I want the prior release withdrawn automatically, so that only one current release exists.
10. As an auditor, I want to withdraw the current release, so that incorrect information is no longer visible.
11. As an auditor, I want a withdrawal reason, so that the audit history explains the action.
12. As an auditor, I want safe repeated requests, so that a retry cannot create duplicate releases or events.
13. As an auditor, I want each lifecycle event recorded, so that the release history remains complete.
14. As an auditor, I want invalid operations to change nothing, so that failure cannot damage release history.
15. As a client, I want to see only published information, so that draft material cannot cause confusion.
16. As a client, I want consistent conclusion and action details, so that the release is clear.
17. As a client, I want no write controls, so that I cannot change controlled audit information.
18. As AuditCo, I want G0 enforced, so that real client information cannot enter the pilot.
19. As AuditCo, I want separate auditor and client access, so that each user has the correct authority.
20. As a maintainer, I want safe database upgrades, so that existing releases remain unchanged.
21. As a maintainer, I want one validation seam, so that rules do not differ between code paths.
22. As a reviewer, I want acceptance-test identifiers, so that each rule has objective evidence.
23. As an approver, I want one frozen candidate, so that the review result applies to the merged code.

## Client And Auditor Screens

### Client Screen

Keep the current protected client page.

The page shows these fields:

- Engagement name.
- Review status.
- Release version.
- Published date and time.
- Approved conclusion title.
- Approved conclusion summary.
- Approved evidence reference.
- Agreed action description.
- Agreed action owner.
- Agreed action target date.
- Agreed action delivery status.
- Fictional pilot notice.

The page shows no edit, upload, approval, decision, delete, publish, or withdrawal control.

The page shows no `DRAFT` or `WITHDRAWN` release.

### Auditor Screen

Add one authenticated Client Releases screen to the workbench.

The screen shows these items:

- Current published release.
- Existing draft releases.
- Withdrawn release history.
- Release version and status.
- Created, published, and withdrawn attribution.
- Selected conclusion and action records.
- Validation result for each source.
- Draft preview link.
- Publish control for an eligible draft.
- Withdraw control for the current release.

The screen must not edit a draft entry. A changed selection creates a new draft.

### Draft Preview

The preview uses the same release response and renderer as the client page.

The preview adds this visible banner:

> Draft Preview — Not Visible To The Client

The approved HTML example must cover desktop and mobile widths.

## Routes And Contracts

### Read Routes

- `GET /workbench/client-releases` returns the auditor lifecycle screen.
- `GET /workbench/client-releases/{release_id}/preview` returns the protected draft preview.
- `GET /client` remains the protected client page.
- `GET /client/api/v1/release/current` remains the protected client API.

### Create Draft

`POST /workbench/api/v1/client-releases` creates one complete draft snapshot.

The request contains:

- Engagement identifier.
- One idempotency key.
- A non-empty list of source record references.
- Each source type, identifier, and version.

The server gets the actor and time from the authenticated request and server clock.

The server does not accept lifecycle actors or times from the request.

The first successful request returns `201 Created`.

An exact repeat returns the original result with `200 OK`.

Reuse of the key with different content returns `409 Conflict`.

### Publish Draft

`POST /workbench/api/v1/client-releases/{release_id}/publish` publishes one eligible draft.

The request contains one idempotency key. The server supplies the actor and canonical UTC time.

The command rechecks every source, snapshot, approval event, version, and time.

The command withdraws the prior current release and publishes the draft in one transaction.

An exact repeat returns the original result. It does not create another event.

### Withdraw Release

`POST /workbench/api/v1/client-releases/{release_id}/withdraw` withdraws the current release.

The request contains one idempotency key and one trimmed withdrawal reason.

The server supplies the actor and canonical UTC time.

An exact repeat returns the original result. It does not create another event.

## Implementation Decisions

1. Start from the confirmed pull request 52 merge commit.
2. Create a new feature branch from that exact commit.
3. Confirm that approved source identity, version, and content are immutable on that baseline.
4. Reuse the existing workbench store as the single lifecycle transaction seam.
5. Keep the existing client response as the single client presentation seam.
6. Build a complete draft and all entries in one transaction.
7. Roll back the complete transaction when any source is invalid.
8. Keep draft entries immutable after creation.
9. Assign each release version from the engagement history inside the transaction.
10. Add a unique engagement and release-version constraint.
11. Store separate creation, publication, and withdrawal attempt keys.
12. Add unique partial indexes for non-null attempt keys.
13. Use server-generated canonical UTC timestamps with the `Z` suffix.
14. Use the authenticated actor. Do not accept actor fields from a form.
15. Permit only `DRAFT` to `PUBLISHED` and `PUBLISHED` to `WITHDRAWN` transitions.
16. Do not permit `DRAFT` to `WITHDRAWN` in this phase.
17. Do not permit any transition from `WITHDRAWN`.
18. Publish only the highest release version for the engagement.
19. Withdraw the previous current release before publishing the new release in the same transaction.
20. Record `RELEASE_CREATED`, `RELEASE_PUBLISHED`, and `RELEASE_WITHDRAWN` events in the command transaction.
21. Require each source approval event to match its canonical record identifier, engagement, actor, and approval time.
22. Recheck all source rules when the draft is published.
23. Reject publication when the draft contains no entries.
24. Reject publication when one entry is invalid.
25. Do not let the client renderer silently omit an invalid published entry.
26. Return a generic `503` response when a published package fails integrity validation.
27. Record the detailed integrity fault only in the protected auditor log.
28. Keep the client route read-only.
29. Keep seed creation separate from production lifecycle commands.
30. Do not drop a protection trigger to support seed repair.
31. Use package state, not event identifier text, to select lifecycle behaviour.
32. Use one trigger creation path for fresh and upgraded databases.
33. Preserve all existing package, entry, source, and audit rows during upgrade.
34. Return generic access errors. Do not disclose record existence before authentication.
35. Escape all dynamic HTML values.
36. Use parameterised database statements.

## Database Changes

Add these nullable columns to existing release packages:

- Creation attempt key.
- Publication attempt key.
- Withdrawal attempt key.

Existing package rows keep null attempt keys during upgrade.

Add these indexes:

- One unique release version for each engagement.
- One unique non-null creation attempt key.
- One unique non-null publication attempt key.
- One unique non-null withdrawal attempt key.

Keep the existing package, entry, conclusion, action, and audit tables.

Strengthen the existing transition and entry controls through one trigger creation path.

Do not rebuild or rewrite historical package, entry, source, or audit rows.

Do not add default release entries during an upgrade.

## Source Eligibility Rules

A conclusion is eligible only when all these conditions are true:

- The conclusion exists.
- The conclusion belongs to the release engagement.
- Its status is `APPROVED`.
- Its version equals the requested version.
- Its title, summary, and evidence reference are non-blank.
- Its approval actor and time are valid and non-blank.
- One matching immutable `CONCLUSION_APPROVED` event exists.
- The event identifier names the conclusion and matches the engagement, actor, and approval time.

An action is eligible only when all these conditions are true:

- The action exists.
- The action belongs to the release engagement.
- Its approval status is `APPROVED`.
- Its version equals the requested version.
- Its description and owner are trimmed and non-blank.
- Its target date is a valid canonical calendar date.
- Its delivery status is `OPEN` or `COMPLETE`.
- Its approval actor and time are valid and non-blank.
- One matching immutable `ACTION_APPROVED` event exists.
- The event identifier names the action and matches the engagement, actor, and approval time.

Approved source content cannot change in place. A content change needs a new approved version.

## State Matrix

| Start State | Source State | Operation | Expected State | Client Result | Audit Result | Repeat Result |
|---|---|---|---|---|---|---|
| None | All valid | Create draft | `DRAFT` | Existing published release stays visible | One creation event | Same key returns same draft |
| None | Any invalid | Create draft | No new package | No change | No event | Same failure and no change |
| `DRAFT` | All valid | Preview | `DRAFT` | No draft visibility | No event | Same preview |
| `DRAFT` | All valid | Publish highest version | `PUBLISHED` | New release visible | Publish event; prior release withdrawal event | Same key returns same publication |
| `DRAFT` | Any invalid | Publish | `DRAFT` | Existing published release stays visible | No event | Same failure and no change |
| `DRAFT` | Empty package | Publish | `DRAFT` | Existing published release stays visible | No event | Same failure and no change |
| `DRAFT` | All valid | Add, update, or delete entry | `DRAFT` | No change | No event | Operation rejected |
| `DRAFT` | All valid | Withdraw | `DRAFT` | No change | No event | Operation rejected |
| `PUBLISHED` | Snapshot valid | Client read | `PUBLISHED` | Package visible | No event | Same response |
| `PUBLISHED` | Source later changes | Client read | `PUBLISHED` | Stored snapshot stays visible | No event | Same response |
| `PUBLISHED` | Any | Publish again with same key | `PUBLISHED` | Same package visible | No duplicate event | Same result |
| `PUBLISHED` | Any | Publish with different key | `PUBLISHED` | Same package visible | No event | Operation rejected |
| `PUBLISHED` | Any | Withdraw with valid reason | `WITHDRAWN` | No current release, unless a replacement publishes atomically | One withdrawal event | Same key returns same withdrawal |
| `PUBLISHED` | Any | Add, update, or delete content | `PUBLISHED` | Stored snapshot stays visible | No event | Operation rejected |
| `WITHDRAWN` | Any | Client read | `WITHDRAWN` | Package hidden | No event | Same response |
| `WITHDRAWN` | Any | Withdraw with same key | `WITHDRAWN` | Package hidden | No duplicate event | Same result |
| `WITHDRAWN` | Any | Publish | `WITHDRAWN` | Package hidden | No event | Operation rejected |
| `WITHDRAWN` | Any | Add, update, or delete content | `WITHDRAWN` | Package hidden | No event | Operation rejected |

Invalid source states include these cases:

- Missing record.
- Candidate record.
- Wrong engagement.
- Wrong version.
- Snapshot mismatch.
- Missing approval actor.
- Missing approval time.
- Missing approval event.
- Mismatched approval event.
- Blank required content.
- Invalid action date.
- Invalid action delivery status.
- Publication before package creation.
- Publication before source approval.
- Approved content changed without a new version.

## Upgrade Matrix

| Starting Database | Required Check | Required Result |
|---|---|---|
| Fresh | Initialise once | Current schema, controls, and fictional seed load correctly |
| Fresh | Initialise twice | No duplicate package, entry, attempt key, or event |
| Phase 6A | Upgrade once | Existing conclusion releases and audit events remain byte-for-byte equivalent |
| Phase 6A | Upgrade twice | No second mutation and no duplicate event |
| Phase 6A | Publish valid legacy draft | Publish succeeds only after all current rules pass |
| Phase 6A | Publish invalid legacy draft | Publish fails with no package or audit mutation |
| Phase 6B1 | Upgrade once | Existing conclusions, actions, packages, snapshots, and events remain unchanged |
| Phase 6B1 | Upgrade twice | No second mutation and no duplicate event |
| Phase 6B1 | Create and publish new release | New lifecycle works without changing historical packages |
| All | Migration failure | Complete rollback leaves the prior database usable |

Upgrade fixtures must represent their historical schema. They must not use the current initializer.

Tests must compare package rows, entry rows, and audit rows before and after each upgrade.

## Testing Decisions

### Test Seam

Use authenticated HTTP requests as the primary acceptance-test seam.

This seam covers the route, lifecycle transaction, database controls, response, and audit result.

Use direct database tests only for immutable constraints and historical upgrade fixtures.

Do not test private helper functions.

### Acceptance-Test Catalogue

#### Baseline

- `6B2-BASE-001`: Pull request 52 has a confirmed merge commit.
- `6B2-BASE-002`: The feature branch starts from that exact commit.
- `6B2-BASE-003`: The complete Phase 6B1 suite passes before 6B2 changes.
- `6B2-BASE-004`: Approved source identity, version, and content cannot change on the baseline.

#### Draft Creation

- `6B2-DRAFT-001`: Valid approved sources create one complete draft.
- `6B2-DRAFT-002`: A repeated key returns the same draft.
- `6B2-DRAFT-003`: A reused key with changed content returns conflict.
- `6B2-DRAFT-004`: One invalid source rolls back the complete command.
- `6B2-DRAFT-005`: A draft is not visible through client routes.
- `6B2-DRAFT-006`: Draft entries cannot change after creation.
- `6B2-DRAFT-007`: Concurrent creation assigns unique release versions.

#### Source Validation

- `6B2-SOURCE-001`: Missing action and conclusion records are rejected.
- `6B2-SOURCE-002`: Candidate action and conclusion records are rejected.
- `6B2-SOURCE-003`: Cross-engagement action and conclusion records are rejected.
- `6B2-SOURCE-004`: Wrong action and conclusion versions are rejected.
- `6B2-SOURCE-005`: Snapshot mismatches are rejected.
- `6B2-SOURCE-006`: Missing and mismatched approval events are rejected.
- `6B2-SOURCE-007`: Blank required fields are rejected.
- `6B2-SOURCE-008`: Invalid dates and delivery states are rejected.
- `6B2-SOURCE-009`: Approved content mutation without a new version is rejected.

#### Publication

- `6B2-PUBLISH-001`: A valid highest-version draft publishes.
- `6B2-PUBLISH-002`: Publication creates one matching audit event.
- `6B2-PUBLISH-003`: Publication uses server actor and canonical UTC time.
- `6B2-PUBLISH-004`: Publication withdraws the prior current release atomically.
- `6B2-PUBLISH-005`: The client sees either the old release or the new release.
- `6B2-PUBLISH-006`: The client never sees two current releases.
- `6B2-PUBLISH-007`: An empty package cannot publish.
- `6B2-PUBLISH-008`: One invalid entry blocks the complete publication.
- `6B2-PUBLISH-009`: Failed publication creates no event.
- `6B2-PUBLISH-010`: Publication cannot precede creation or approval.
- `6B2-PUBLISH-011`: A repeated key creates no duplicate event.
- `6B2-PUBLISH-012`: A stale lower-version draft cannot publish.

#### Withdrawal

- `6B2-WITHDRAW-001`: A current release withdraws with a trimmed reason.
- `6B2-WITHDRAW-002`: Withdrawal creates one matching audit event.
- `6B2-WITHDRAW-003`: A withdrawn release is not client-visible.
- `6B2-WITHDRAW-004`: A repeated key creates no duplicate event.
- `6B2-WITHDRAW-005`: A blank reason is rejected with no change.
- `6B2-WITHDRAW-006`: A draft or withdrawn release cannot withdraw.

#### Immutability And Repeat Execution

- `6B2-IMM-001`: Published package content cannot change.
- `6B2-IMM-002`: Withdrawn package content cannot change.
- `6B2-IMM-003`: Published and withdrawn entries cannot be inserted, updated, or deleted.
- `6B2-IMM-004`: Reopening the database changes no historical release.
- `6B2-IMM-005`: Repeating each successful command returns one stable result.
- `6B2-IMM-006`: Repeating each failed command changes nothing.

#### Client Visibility

- `6B2-CLIENT-001`: The client sees only the highest current published release.
- `6B2-CLIENT-002`: The client sees approved conclusion fields.
- `6B2-CLIENT-003`: The client sees agreed action fields.
- `6B2-CLIENT-004`: The client sees no private approval fields or identifiers.
- `6B2-CLIENT-005`: Dynamic HTML is escaped.
- `6B2-CLIENT-006`: Client routes expose no write method.
- `6B2-CLIENT-007`: Invalid published data causes an integrity failure, not silent omission.

#### Security And G0

- `6B2-SEC-001`: Auditor routes require auditor authentication.
- `6B2-SEC-002`: Client credentials do not grant auditor access.
- `6B2-SEC-003`: Auditor credentials do not grant client access.
- `6B2-SEC-004`: Missing credential configuration fails closed.
- `6B2-SEC-005`: Non-fictional engagement data fails G0 before any write.
- `6B2-SEC-006`: An access failure does not disclose record existence.

#### Upgrades

- `6B2-UPGRADE-001`: A fresh database passes first and repeated initialization.
- `6B2-UPGRADE-002`: A Phase 6A database keeps all historical release data.
- `6B2-UPGRADE-003`: A Phase 6B1 database keeps all historical release data.
- `6B2-UPGRADE-004`: Invalid legacy drafts cannot publish.
- `6B2-UPGRADE-005`: Valid legacy drafts pass all current validation.
- `6B2-UPGRADE-006`: Migration failure rolls back completely.

### Test Sequence

1. Pocock approves this catalogue.
2. Add the historical database fixtures.
3. Write the acceptance tests.
4. Confirm that new behaviour tests fail on the merged Phase 6B1 baseline.
5. Confirm that protection tests pass or fail for the expected reason.
6. Start implementation only after this evidence exists.

## Security Rules

1. G0 permits fictional, public, or AuditCo-owned information only.
2. Phase 6B2 does not permit real client information.
3. Auditor lifecycle routes use the existing auditor authentication boundary.
4. Client routes use the existing independent client authentication boundary.
5. No client route writes data.
6. The server gets actors from authenticated identity.
7. The server gets lifecycle times from its UTC clock.
8. Error responses do not disclose a protected record before authentication.
9. HTML output escapes all dynamic values.
10. Logs exclude passwords, client evidence, and private auditor notes.
11. No external provider receives repository or client data.
12. No Production deployment occurs in this phase.

## Failure Rules

1. An invalid request returns a controlled error and changes nothing.
2. A database error rolls back the complete lifecycle command.
3. An audit event failure rolls back the state transition.
4. A prior-release withdrawal failure blocks new publication.
5. A new-publication failure rolls back the prior withdrawal.
6. An idempotency conflict does not repeat or change the first command.
7. A migration failure leaves the old schema and data usable.
8. An invalid published record produces an auditor integrity error.

## Out Of Scope

- Real client information.
- Production deployment.
- Client edits or comments.
- Client acknowledgements.
- Client approval or acceptance.
- Evidence upload.
- Action approval.
- Conclusion approval.
- Action delivery updates.
- Email notifications.
- Release PDF or Word export.
- Public links.
- Application sign-in changes.
- New providers or dependencies.
- Changes to the existing audit decision authority.
- Database engine replacement.
- Repair of historical records through seed logic.

## Delivery Gates

1. Merge pull request 52.
2. Record its confirmed merge commit.
3. Approve this specification.
4. Approve the state and upgrade matrices.
5. Pocock approves every acceptance-test identifier.
6. Approve the desktop and mobile HTML example.
7. Give Vorflux one complete bounded instruction.
8. Write and verify acceptance tests before implementation.
9. Complete implementation and focused tests.
10. Run the complete suite once on the final candidate.
11. Inspect the complete diff.
12. Run required Pocock and controlled project reviews.
13. Freeze the exact candidate head.
14. Request Codex review only on that head.
15. Apply accepted safe fixes and repeat the required verification.
16. Obtain approval for the exact ready pull request head.
17. Merge only that approved head.
18. Confirm the GitHub merge commit.
19. Complete the linked issue only after merge confirmation.

## Bounded Implementation Instruction Requirements

The Vorflux instruction must include these items:

- Confirmed baseline branch and commit.
- Feature branch name.
- Approved specification link.
- Allowed modules.
- Acceptance-test identifiers.
- Time estimate and hard limit.
- High-cost commands.
- G0 and data controls.
- Exclusions.
- Stop conditions.
- Required evidence.
- Exact final-head reporting.

Vorflux must stop for architecture, security, schema, or public-interface expansion.

## Further Notes

This scope is deliberately narrow. It adds lifecycle control around the existing client release view.

It does not add more client content. It makes the existing conclusion and action release process safe.

The local specification must link to the Linear implementation issue before implementation starts.

Apply the `ready-for-agent` label only after Pocock and human specification approval.
