# Vorflux Master Instruction: Phase 6 Release-Engine Refactor

## Authority

This instruction approves the internal release-engine refactor described below.

Vorflux must manage research, design, specification, testing, implementation, verification, review and documentation.

Use a fresh Codex task for each implementation stage. Invoke `$sol-advisor:orchestration` for all code changes.

Continue automatically while work stays inside this instruction. Ask the human only at the listed stop conditions.

Do not merge a pull request without approval for its exact head.

## Required Delivery Sequence

Use this sequence for each stage:

**Understand → Specify → Test → Build → Verify → Freeze → Review → Release**

A stage cannot skip a step. Each step must meet its exit gate.

## Goal

Refactor the current client release engine into one clear application service.

Web and future mobile clients must use the same service contract.

Preserve all Phase 6B1 behaviour, published snapshots, withdrawn releases and audit history.

This work prepares Phase 6B2. It does not implement Phase 6B2 or the mobile app.

## Baseline

Use the latest remote head of `codex/ace-sprint-1`.

Confirm that the baseline contains:

- Pull request 52.
- Phase 6B1 head `1d832a54065b7446df21346c79fe2b6270716eed`.
- Merge commit `1898e34716145a254ab876615360d1e6c7d02766`.
- A clean worktree.

Stop if the baseline does not contain these records.

Record the exact baseline commit before work starts.

## User Outcomes

The completed refactor must give users these benefits:

- Web and mobile show the same information.
- Releases work the same way on each device.
- Published records stay fixed.
- Withdrawn records remain available in history.
- Information cannot cross client engagements.
- Errors are easier to find and correct.
- New client features are easier to add.
- Updates have less risk of breaking releases.

## Approved Architecture

Create one `ClientReleaseService`.

The service must own these operations:

- `build_draft()`
- `validate_release()`
- `publish_release()`
- `withdraw_release()`
- `get_current_release()`
- `get_release_history()`

The service must control:

- Release eligibility.
- Approval verification.
- Audit-event verification.
- Source and snapshot matching.
- Engagement isolation.
- Version selection.
- Publication chronology.
- Withdrawal rules.
- Release assembly.
- Client-safe queries.

Keep essential protection in the database:

- Primary keys.
- Foreign keys.
- `NOT NULL` rules.
- Valid status values.
- Unique release versions.
- Terminal release immutability.
- Essential source relationships.

Move workflow decisions out of SQLite triggers.

Keep existing API and HTML behaviour unchanged.

Do not remove a trigger until equivalent service tests pass.

## Improvement Authority

Vorflux must actively find simpler and safer ways to achieve the approved goal.

Vorflux can automatically apply an improvement when it:

- Preserves all user outcomes.
- Preserves published and withdrawn history.
- Keeps the shared web and mobile service goal.
- Reduces complexity, duplication or maintenance cost.
- Stays inside the approved security and data boundaries.
- Adds no dependency name or external platform.
- Changes no public API or public schema.
- Passes the complete state matrix and final gates.

Vorflux can change:

- Internal class structure.
- Internal method names.
- Storage-adapter design.
- Transaction design.
- Test structure.
- Migration implementation.
- Pull-request boundaries.
- The order of internal implementation work.

Before applying an improvement, record:

- The current problem.
- The proposed improvement.
- Why it is simpler or safer.
- The affected files and rules.
- The tests that will prove it.

Apply the improvement automatically when it stays inside this authority.

Stop for human approval when an improvement requires:

- A different product architecture.
- A security-boundary change.
- A public API or public schema change.
- A new dependency or platform.
- A change to user-visible behaviour.
- A change to published history.
- More than the approved time limit.

## Work Boundaries

The approved work includes:

- Release-service code.
- Release storage adapters.
- Existing client routes that must call the service.
- Release-domain models where required.
- Release tests.
- Migration tests.
- Required internal documentation.

The approved work excludes:

- Phase 6B2 features.
- Mobile application code.
- New public API behaviour.
- Authentication changes.
- Security-boundary changes.
- Production deployment.
- Real client information.
- Payload, Directus or another platform.
- New dependency names.
- Unrelated cleanup.

## Programme Limits

Planning estimate: 30 to 45 engineering hours.

Token planning budget: three million Codex tokens.

Programme hard limit: 45 engineering hours.

Use three implementation stages. Use a separate pull request for each stage.

Report progress every 15 minutes during active work.

Each report must state:

- Elapsed time.
- Current step.
- Completed work.
- Active test or review.
- Blocker, if present.
- Estimated remaining time.

Stop after two failed correction attempts for the same fault.

Preserve completed work when a stop occurs.

## High-Cost Work

Treat these actions as high-cost:

- The complete test suite.
- The complete migration matrix.
- Browser verification.
- Pocock review.
- Greptile review.
- Fresh Sol review.
- Exact-head Codex review.

Use focused tests during development.

Run each high-cost check once on a final candidate head.

If a review fix changes code, run affected focused tests first.

Then run one new complete suite on the changed final head.

## Stage 1: Service Boundary And Characterisation

This is the pilot stage.

### Understand

Use CodeGraph first when the repository contains `.codegraph`.

Map current release behaviour across:

- Domain models.
- Client routes.
- Storage functions.
- SQLite tables.
- SQLite triggers.
- Seed logic.
- Legacy migrations.
- Audit events.
- API responses.
- HTML views.
- Tests.

Create a release-state matrix.

The matrix must include:

- Draft packages.
- Published packages.
- Withdrawn packages.
- Fresh databases.
- Phase 6A databases.
- Phase 6B1 databases.
- Approved actions.
- Approved conclusions.
- Invalid sources.
- Cross-engagement sources.
- Changed sources.
- Missing approval data.
- Missing audit events.
- Invalid dates.
- Empty required values.
- Repeated database startup.
- Version collisions.
- Null identifiers.

Record each current rule and its test evidence.

#### Understand Exit Gate

- Every current rule has a source reference.
- Every current rule has a test reference or a recorded test gap.
- Every matrix cell has an expected result.
- No material unknown remains.

### Specify

Write the internal service contract.

Define:

- Service inputs and outputs.
- Service errors.
- Transaction boundaries.
- Storage adapter responsibilities.
- Route responsibilities.
- Database responsibilities.
- Migration compatibility rules.
- History-protection rules.

Publish the design in the pull-request description or an approved design document.

Continue automatically if the design matches this instruction.

Stop if the design needs a public interface, schema or security change.

#### Specify Exit Gate

- The specification covers every matrix cell.
- The service and database have separate responsibilities.
- Existing client behaviour remains the acceptance contract.
- No excluded change is required.

### Test

Add characterisation tests for current behaviour.

Add failing tests for the new service boundary.

Add missing state-matrix tests before moving rules.

#### Test Exit Gate

- Characterisation tests pass against the baseline behaviour.
- New service tests fail for the correct reason.
- Migration fixtures represent all approved database states.

### Build

Add the `ClientReleaseService` boundary.

Route existing release operations through the service facade.

Keep current database triggers active.

Make no client-visible behaviour change.

#### Build Exit Gate

- The service is the documented release entry point.
- Existing behaviour remains unchanged.
- Focused tests pass.

### Verify, Freeze, Review And Release

Use the common final-gate procedure below.

Request human merge approval for the exact ready head.

After GitHub confirms the approved merge, continue to Stage 2.

## Stage 2: Move Release Workflow

### Understand

Confirm the merged Stage 1 baseline.

Identify each workflow rule that still runs in a trigger or route.

#### Understand Exit Gate

- Every rule has one planned service location.
- Every affected trigger and route has a replacement test.

### Specify

Specify service behaviour for:

- Draft creation.
- Eligibility validation.
- Approval validation.
- Audit-event validation.
- Publication.
- Withdrawal.
- Release assembly.
- Current-release queries.
- Release-history queries.

#### Specify Exit Gate

- Each rule has one owner.
- Transaction and rollback behaviour is defined.
- Compatibility behaviour is defined.

### Test

Add failing service tests before moving each rule group.

Add tests that prove routes cannot bypass the service.

Add tests for fresh and legacy databases.

#### Test Exit Gate

- Each moved rule has positive and negative tests.
- Published and withdrawn history has protection tests.
- Cross-engagement access has rejection tests.

### Build

Move release workflow into the service.

Make web routes use the service only.

Preserve existing public responses and HTML output.

Keep required database protection active.

#### Build Exit Gate

- Routes do not implement release rules.
- Routes do not write release tables directly.
- Service tests and route tests pass.
- Existing databases remain compatible.

### Verify, Freeze, Review And Release

Use the common final-gate procedure below.

Request human merge approval for the exact ready head.

After GitHub confirms the approved merge, continue to Stage 3.

## Stage 3: Reduce Trigger Complexity

### Understand

List every remaining release trigger and constraint.

Classify each item as:

- Essential database integrity.
- Workflow already owned by the service.
- Legacy migration support.
- Obsolete.

#### Understand Exit Gate

- Every trigger and constraint has one classification.
- Every removal has equivalent service protection.

### Specify

Specify the final database protection set.

Specify the stable internal contract for future web and mobile clients.

Do not create mobile application code.

#### Specify Exit Gate

- The final trigger set is explicit.
- Migration steps are explicit.
- The future mobile contract uses the same service.

### Test

Add migration tests for the reduced trigger set.

Test all release-state matrix cells again.

Test repeated startup and upgrade paths.

#### Test Exit Gate

- Removed triggers have equivalent service tests.
- Essential constraints have direct database tests.
- Fresh and legacy database tests pass.

### Build

Remove workflow triggers that the service replaces.

Keep essential database constraints.

Complete the storage adapter boundary.

Document the future mobile integration contract.

#### Build Exit Gate

- One service owns release workflow.
- The database protects essential integrity only.
- Web routes use the service.
- Future mobile work has one stable internal contract.

### Verify, Freeze, Review And Release

Use the common final-gate procedure below.

Request human merge approval for the exact ready head.

## Common Final-Gate Procedure

### Verify

Inspect the complete diff.

Run:

- Focused release tests.
- The complete test suite.
- API checks.
- HTML checks.
- Fresh-database tests.
- Phase 6A migration tests.
- Phase 6B1 migration tests.
- Published-package tests.
- Withdrawn-package tests.
- Repeated-startup tests.
- `git diff --check`.

Verify that published snapshots and audit counts do not change.

#### Verify Exit Gate

- All required checks pass.
- The worktree is clean.
- The branch contains only approved work.
- The pull request contains only approved files and commits.

### Freeze

Record the exact commit SHA.

Stop code changes on that candidate.

Update the pull-request description with all evidence.

#### Freeze Exit Gate

- One exact head is the review candidate.
- All reported checks belong to that exact head.
- The branch is clean.

### Review

Run these reviews on the frozen head:

- Pocock standards review.
- Pocock specification review.
- One controlled Greptile review.
- Fresh Sol review.
- Exact-head Codex review.

Resolve all valid in-scope findings.

Close all review threads.

Any code change cancels the freeze.

After a code change:

1. Run affected focused tests.
2. Run one new complete suite.
3. Freeze the new exact head.
4. Repeat required exact-head reviews.

#### Review Exit Gate

- All reviews approve the same exact head.
- Zero review threads remain open.
- All checks apply to the same exact head.

### Release

Release means ready for human merge approval.

It does not mean automatic merge.

Report:

- Exact approved head.
- Exact target branch.
- Changed files.
- Test totals.
- Migration results.
- API and HTML results.
- Review results.
- Open risks.

Request human merge approval for that exact head.

A changed head cancels merge approval.

After GitHub confirms the exact merge:

- Record the merge commit.
- Update the related issue.
- Continue to the next approved stage.

## Safety Controls

Use fictional, public or AuditCo-owned information only.

Keep G0 active.

Keep the existing auditor approval authority.

Keep authentication and engagement isolation unchanged.

Use Preview only when browser hosting is necessary.

Preserve all published and withdrawn history.

Do not deploy to Production.

Do not add a dependency name.

Do not adopt a new platform.

Do not rewrite Git history.

Do not force-push.

Do not merge without exact-head approval.

## Human Stop Conditions

Stop and ask the human only for:

- A material change to the approved architecture.
- A security-boundary change.
- A public API change.
- A public schema change.
- A new dependency name.
- A new platform.
- Real client information.
- A Production action.
- An irreversible deletion.
- Work beyond the 45-hour limit.
- Exact-head merge approval.

Handle normal technical findings inside the approved boundary.

Do not ask the human to select each technical fix.

## Documentation

Update these files after Stage 3 reaches its final ready head:

- `DEV_STATE.md`
- `ACE_PROGRESS_GUIDE.html`

Record:

- The final architecture.
- Service responsibilities.
- Remaining database controls.
- Migration evidence.
- Test results.
- Review results.
- Pull requests and exact heads.
- Merge commits after approval.
- Lessons learned.
- The mobile integration contract.
- Remaining Phase 6B2 work.

## Final Completion Criteria

The refactor is complete only when:

- One service owns the release workflow.
- Web routes use that service.
- A documented contract exists for the future mobile app.
- Published and withdrawn history remains unchanged.
- Fresh and legacy database tests pass.
- All state-matrix tests pass.
- API and HTML behaviour remains unchanged.
- Essential database protection remains active.
- Workflow triggers are removed or justified.
- All required reviews pass.
- All review threads are closed.
- Documentation is current.
- All approved pull requests are merged at their approved exact heads.
- No Phase 6B2 feature or mobile application work entered this scope.

At completion, report final merge records and recommend the next Phase 6B2 instruction.
