# Vorflux Master Instruction: Phase 6B2 Read-Only Client Release Projection

## Document Status

Status: Draft For Human Approval

This file does not authorise implementation.

It becomes implementation authority only after the human approves this exact file.

## Authority

After approval, Vorflux must manage understanding, specification, tests,
implementation, verification, review, and completion evidence.

Use a fresh Codex task for implementation. Invoke
`$sol-advisor:orchestration` for all code changes.

Continue automatically while work stays inside this instruction. Ask the
human only at the listed stop conditions.

This instruction does not authorise commit, push, pull-request, merge, or
Production actions. Obtain the required authority before each action.

## Required Delivery Sequence

Use this sequence:

**Understand → Specify → Test → Build → Verify → Freeze → Review → Release**

A step cannot start until the prior exit gate passes.

## Goal

Create one transport-neutral, read-only client release projection.

The projection must prepare the existing release data for a future mobile
adapter. It must not create a mobile application or mobile route.

Keep the existing client API and HTML output unchanged.

## Baseline

Use the latest remote head of `codex/ace-sprint-1`.

Confirm that the baseline contains:

- PR 54 head `7e67ee62ffabdc7e54fbb07f91d509f6ebc72c94`.
- PR 54 merge `48829602b6147885573854b9907edd92ddc08656`.
- PR 55 head `761b0cb9941c52e90c8db7ad806cee49d0531732`.
- PR 55 merge `6f88ce3ddd6fa9dc6f1fc33e35aecc624b939437`.
- PR 56 head `2887c0ce0782910e648860b8157d2d2a966172a2`.
- PR 56 merge `a2f8a3083ed81d22a5af766d74da1da6634f7f64`.
- PR 57 head `727243d890738f103b94ca6926fd0ae299b0a001`.
- PR 57 merge `57a669a63fdbff6b49586682a3f87967a5d8a3a9`.
- PR 58 head `e1404eaf72212f71e10c7ef81e1013b9ab3a10d9`.
- PR 58 merge `3726793e1c0c6d8c3799cbde2456e72b9b05a3c5`.
- A clean, isolated worktree.

Record the exact baseline commit before work starts.

Stop if the baseline does not contain these records.

## Required Source Documents

Read these files before design work:

- `AGENTS.md`.
- `DEV_STATE.md`.
- `ACE_PROGRESS_GUIDE.html`.
- `docs/specs/phase6-stage1-release-service-boundary.md`.
- `docs/specs/phase6-stage2-release-workflow.md`.
- `docs/specs/phase6-stage3-release-trigger-decisions.md`.

Use this instruction as the sole authority for the Phase 6B2 read-only slice.

The local `docs/specs/2026-08-22-phase-6b2-controlled-client-release-lifecycle.md`
draft remains reference material only. Its write routes and schema changes are
outside this instruction.

## User Outcomes

The completed slice must give future users these benefits:

- Web and future mobile consumers use the same projected release information.
- The client sees only the current published release.
- Published conclusion and action snapshots remain fixed.
- Information cannot cross engagements.
- The projection exposes no internal approval or audit details.
- Current client authentication and G0 controls remain active.
- The work creates no new client write path.

## Approved Architecture

Create one pure `ClientReleaseProjection` adapter.

The adapter must:

- Accept current-release and engagement data supplied by the caller.
- Return the existing `ClientReleaseResponse` model.
- Perform no SQL.
- Open no database connection.
- Perform no database write.
- Preserve current conclusion and action projection rules.
- Preserve current empty-state behaviour.
- Preserve deterministic release-entry ordering.

Keep these ownership rules:

- `ClientReleaseService` remains the release workflow authority.
- `ClientReleaseStorage` remains the release SQL owner.
- The route opens one SQLite connection.
- The route passes that connection through all service reads.
- The route keeps HTTP, authentication, G0, and error translation.
- `WorkbenchStore` remains migration and trigger-installation owner.

The future mobile adapter can use the same projection contract. This phase
does not add that adapter.

## Mobile-Facing Domain Rules

| Condition | Required Result |
|---|---|
| Current fictional `PUBLISHED` release | Return the existing client response fields. |
| No current published release | Return the existing unavailable response. |
| `DRAFT` release only | Exclude it from the client projection. |
| `WITHDRAWN` release only | Exclude it from the client projection. |
| Valid conclusion snapshot | Return its title, summary, and evidence reference. |
| Valid action snapshot | Return description, owner, target date, and delivery status. |
| More than one valid action | Keep the stored release-entry order. |
| Missing action owner or target date | Preserve current exclusion behaviour. |
| Invalid action date or delivery status | Preserve current exclusion behaviour. |
| Unknown source record type | Preserve current exclusion behaviour. |
| Missing engagement record | Preserve the current client response. |
| Non-fictional engagement | Return the current generic unavailable error. |
| Cross-engagement request | Return no information from another engagement. |
| Missing or invalid client credentials | Preserve current access behaviour. |
| Successful read | Leave package, entry, source, and audit rows unchanged. |

Expose only these existing fields:

- Engagement name.
- Review status.
- Release version.
- Published time.
- Conclusion title.
- Conclusion summary.
- Conclusion evidence reference.
- Action description.
- Action owner.
- Action target date.
- Action delivery status.

Keep internal identifiers, approval attribution, audit events, release
history, and withdrawal details outside the projection.

## Database And Transaction Rules

Pass one caller-owned SQLite connection through service and storage calls.

This read-only slice must not call `begin_release_write()`.

Preserve all 18 retained release triggers.

Preserve the documented direct-SQL withdrawal boundary. This slice does not
strengthen or relax that behaviour.

## Improvement Authority

Vorflux can apply an internal improvement when it:

- Preserves every user outcome.
- Preserves the existing API model and HTML output.
- Reduces projection duplication.
- Stays inside the allowed files.
- Changes no route, schema, trigger, migration, or authentication boundary.
- Adds no dependency name.
- Passes the state matrix and final gates.

Before an improvement, record:

- The current problem.
- The proposed improvement.
- Why it is safer or simpler.
- The affected allowed files.
- The proving tests.

Stop for human approval when an improvement needs:

- A different architecture.
- A security-boundary change.
- A public API or schema change.
- A route change.
- A trigger or migration change.
- A new dependency.
- A user-visible behaviour change.
- Work beyond the hard limit.

## Allowed Files

Only these files can change:

- `docs/specs/phase6b2-read-only-client-release-projection.md`.
- `src/ace/workbench/client_release_projection.py`.
- `src/ace/workbench/client_routes.py`.
- `tests/test_client_release_projection.py`.
- `tests/test_client_release.py`.

Stop before changing another file.

## Work Boundaries

The approved work includes:

- Current client projection characterisation.
- A transport-neutral projection contract.
- A pure projection adapter.
- Existing route delegation to that adapter.
- Focused projection and compatibility tests.
- The approved design specification.

The approved work excludes:

- Mobile application code.
- A mobile route or endpoint.
- A new public API field.
- Client editing or comments.
- Release creation, publication, or withdrawal controls.
- Database schema or migration changes.
- Trigger changes.
- Authentication changes.
- Real client information.
- Paid providers.
- New dependencies.
- Production actions.
- Unrelated cleanup.

## Programme Limits

Planning estimate: 45 minutes.

Hard limit: 60 minutes.

This is one pilot implementation stage. Production hardening needs a separate
instruction.

Report progress every 15 minutes during active work.

Each report must state:

- Elapsed time.
- Current delivery step.
- Completed work.
- Active test or review.
- Blocker, if present.
- Estimated remaining time.

Stop after two failed correction attempts for one fault.

Preserve completed work when a stop occurs.

## High-Cost Work

Treat these actions as high-cost:

- The complete client release test module.
- The complete test suite.
- Pocock review.
- One controlled Greptile review.
- Fresh Sol review.
- Exact-head Codex review.

Use focused tests during development.

Run the complete suite once on the final candidate head.

Run each external review once on the frozen candidate head.

If an accepted review fix changes code:

1. Run affected focused tests.
2. Run one new complete suite.
3. Freeze the new head.
4. Repeat the required exact-head reviews.

## Stage 1: Read-Only Projection Pilot

### Understand

Use CodeGraph first when the repository contains `.codegraph`.

Map current release projection behaviour across:

- `ClientReleaseResponse` and its nested models.
- `ClientReleaseService` current-release reads.
- `ClientReleaseStorage` queries and ordering.
- Client authentication.
- G0 checks.
- Client API output.
- Client HTML output.
- Empty and unavailable responses.
- Existing release tests.

Create a projection-state matrix. Include every condition in this instruction.

Record a source reference and test reference for every rule. Record test gaps
before design work.

#### Understand Exit Gate

- Every domain rule has a source reference.
- Every domain rule has a test reference or recorded gap.
- Every state-matrix cell has an expected result.
- The current API and HTML output are recorded.
- No material behaviour remains unknown.

### Specify

Write the transport-neutral projection contract.

Define:

- Adapter inputs and output.
- Domain filtering rules.
- Ordering rules.
- Empty-state rules.
- G0 and authentication ownership.
- Service, adapter, and route responsibilities.
- Compatibility rules.
- Error ownership.

Publish the contract in
`docs/specs/phase6b2-read-only-client-release-projection.md`.

#### Specify Exit Gate

- The specification covers every matrix cell.
- Each rule has one owner.
- The adapter performs no SQL or connection management.
- The service remains the release authority.
- Existing client behaviour remains the acceptance contract.
- No excluded change is required.

### Test

Add characterisation tests before route refactoring.

Add failing tests for the new projection adapter.

Tests must prove:

- Exact API response compatibility.
- Exact HTML output compatibility.
- Current published-release selection.
- Draft and withdrawn exclusion.
- Conclusion projection.
- Action projection and ordering.
- Existing invalid-entry exclusion behaviour.
- Unknown entry-type exclusion.
- G0 rejection.
- Authentication compatibility.
- Engagement isolation.
- One route-owned connection.
- No database or audit mutation during reads.
- Exact retention of all 18 release triggers.

#### Test Exit Gate

- Characterisation tests pass on baseline behaviour.
- New adapter tests fail for the expected missing boundary.
- Protection tests pass on the baseline.
- Tests use fictional information only.

### Build

Add `ClientReleaseProjection` in the approved new module.

Move only projection logic from `client_routes.py` into the adapter.

Keep route authentication, G0, connection, HTTP, and error responsibilities.

Keep the existing response model and HTML renderer unchanged.

#### Build Exit Gate

- The adapter is pure and transport-neutral.
- The route opens exactly one connection.
- Routes and the adapter contain no release SQL.
- Client API output remains unchanged.
- Client HTML output remains unchanged.
- Focused tests pass.

## Common Final-Gate Procedure

### Verify

Inspect the complete diff.

Run:

- Focused projection tests.
- The complete client release tests.
- API compatibility tests.
- HTML compatibility tests.
- G0 and authentication tests.
- Trigger-inventory tests.
- The complete suite once.
- `git diff --check`.

Compare release packages, entries, and audit rows before and after read tests.

#### Verify Exit Gate

- All required checks pass.
- Only allowed files changed.
- The branch contains only approved work.
- No route, schema, trigger, migration, authentication, or dependency changed.
- All database snapshots remain exact after reads.

### Freeze

Record the exact candidate commit SHA.

Stop code changes on that candidate.

Record all verification evidence against that exact SHA.

#### Freeze Exit Gate

- One exact head is the review candidate.
- The worktree is clean.
- All reported checks belong to that exact head.

### Review

Run these reviews on the frozen head:

- Pocock standards review.
- Pocock specification review.
- One controlled Greptile review when pull-request authority exists.
- Fresh Sol review.
- Exact-head Codex review.

Resolve valid in-scope findings.

Close all review threads when pull-request authority exists.

Any code change cancels the freeze.

#### Review Exit Gate

- All required reviews approve the same exact head.
- No valid in-scope finding remains.
- Zero review threads remain open when a pull request exists.
- All checks apply to the same exact head.

### Release

Release means ready for human delivery approval.

It does not mean commit, push, pull request, or merge authority.

Report:

- Exact candidate head.
- Exact target branch.
- Changed files.
- Focused and complete test totals.
- API and HTML compatibility results.
- Trigger and database snapshot results.
- Review results.
- Elapsed time.
- Open risks.

Request the next required human approval.

## Safety Controls

Use fictional, public, or AuditCo-owned information only.

Keep G0 active.

Keep existing client authentication and engagement isolation unchanged.

Use immutable release snapshots as the presentation source.

Keep client access read-only.

Keep all 18 release triggers active.

Keep `WorkbenchStore` as migration and trigger owner.

Keep the direct-SQL withdrawal limitation documented and unchanged.

## Human Stop Conditions

Stop and ask the human for:

- A material architecture change.
- A security-boundary change.
- A public API or schema change.
- A route change.
- A database migration or trigger change.
- A new dependency or provider.
- A user-visible behaviour change.
- A file outside the allowed list.
- Real client information.
- A Production action.
- An irreversible deletion.
- Work beyond the 60-minute limit.
- Commit, push, pull-request, or merge authority.

Handle normal technical findings inside the approved boundary.

## Documentation

The approved specification is the only documentation file in this slice.

Update `DEV_STATE.md` and `ACE_PROGRESS_GUIDE.html` only through a separate
documentation instruction after confirmed merge.

## Final Completion Criteria

The slice is complete only when:

- One pure projection adapter exists.
- The existing route uses that adapter.
- `ClientReleaseService` remains the release authority.
- One caller-owned connection serves all release and engagement reads.
- API and HTML behaviour remain unchanged.
- Authentication, G0, and engagement isolation remain unchanged.
- Release packages, entries, and audit history remain unchanged by reads.
- All 18 release triggers remain active.
- No route, schema, migration, trigger, dependency, or mobile code entered scope.
- Focused and complete tests pass.
- Required reviews approve one exact candidate head.
- The final report identifies all changed files and evidence.

