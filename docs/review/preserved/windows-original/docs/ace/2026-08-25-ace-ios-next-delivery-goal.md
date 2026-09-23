# ACE iOS Next Delivery Goal

## Authorities

The user authorizes one documentation-only commit and push to the existing feature branch.

Do not merge, deploy, build the application, or upload material to a provider.

## Current State

PR #62 is open and has a clean merge state.

Its recorded head is `9944e5a923cff012d464190eb0e50709c7905e8e`.

The controlled Security worktree contains an unexplained specification change and hash mismatch.

## Locked Decisions

- Use native Swift and SwiftUI.
- Use Apple frameworks only.
- Keep the iOS client read-only.
- Keep the ACE API as the source of truth.
- Use Codemagic for builds and automated tests.
- Give Revyl only the compiled simulator application.
- Keep Sift-KG and OpenViking as separate fictional-data pilots.

## Mandatory Changes

- Confirm the exact specification artifact.
- Complete exact-artifact Pocock and Security reviews.
- Reconcile the Codemagic and Revyl path into the tracked progress page.
- Update PR #62 and report all remaining implementation gates.

## Optional Or Out Of Scope

- Do not implement the application.
- Do not upgrade the Mac.
- Do not configure Codemagic, Revyl, TestFlight, or Apple signing.
- Do not create another pull request.

## Dependencies And Environment

The approved Mac needs a supported macOS version and Xcode 26.

The final build needs iOS 26 simulator evidence.

Physical-device evidence will use an iPhone 15 Pro or a later model.

## Dirty Worktree Warnings

The main workspace contains unrelated changes.

Use only `C:\tmp\sqe-ios-spec-state-sync` for the delivery work.

The temporary Security worktree is dirty. Do not assume its current file has approval.

## Verification Criteria

- Verify the exact commit, SHA-256, Git blob, and PR head.
- Verify all 197 acceptance-test identifiers.
- Use official Apple sources for Keychain claims.
- Repeat an approval if its reviewed artifact changes.

## Unresolved Matters

- Private test server and certificate approval.
- Exact bundle identifier.
- Apple signing team and entitlements.
- Codemagic and Revyl transfer approvals.
- Exact Xcode 26 host evidence.
- iOS 26 simulator evidence.
- MCX-15 implementation approval.

## Redacted Continuation Prompt

```text
research

First, create a goal with this objective:

Finalize and freeze the ACE iOS specification delivery record on PR #62. Obtain exact-artifact Pocock and Security evidence. Reconcile the development path. Report every remaining implementation gate. Do not implement the application.

Do not set a token budget.

Authority

I authorize one documentation-only commit and push for this goal.

Limit the commit to these three tracked files:

C:\tmp\sqe-ios-spec-state-sync\sqe\ACE_PROGRESS_GUIDE.html
C:\tmp\sqe-ios-spec-state-sync\sqe\DEV_STATE.md
C:\tmp\sqe-ios-spec-state-sync\sqe\docs\specs\2026-08-24-ace-ios-read-only-client-application.md

Update the existing PR only:

https://github.com/mcxl/agentic-os-workspace/pull/62

Do not merge.
Do not create another pull request.
Do not deploy.
Do not build the application.
Do not upload source or binaries to a provider.
Do not change application code.
Do not add dependencies.
Do not change the architecture or security boundary.

Workspace

Use only this Git worktree:

C:\tmp\sqe-ios-spec-state-sync

Expected branch:

codex/ios-spec-state-sync

Expected starting head:

9944e5a923cff012d464190eb0e50709c7905e8e

Read the applicable AGENTS.md instructions before work.

Preserve all unrelated user changes.

Current tracked files

The expected modified tracked files are:

sqe/ACE_PROGRESS_GUIDE.html
sqe/DEV_STATE.md
sqe/docs/specs/2026-08-24-ace-ios-read-only-client-application.md

Stop if another tracked file enters the commit.

Controlled Security worktree

Inspect this complete worktree and its complete diff:

LOCAL_HOME\AppData\Local\Temp\ace-ios-spec-pocock-17c7e71a

Expected Git HEAD:

17c7e71a207d248979b9601b4cf4a9dfc71f548d

Expected parent:

6b0160befc9191dbccd527bdd385b891782ddad8

The original review request specified:

SHA-256:
D5BBFDF92281E8AF750608E1D7D381E3FFFC99FF5525AD3E7242482C257985AB

Git blob:
e0191839221043dc995a71fc53442a2d553bf74f

The current dirty file previously calculated as:

SHA-256:
D30C24502BAF1B849A4CE7778C213F8D464D8A975FD4E4CBB932258690A1E3BC

Git blob:
5e0df37037aef24bb55ef9cbafd670d601410de0

Do not infer which artifact is authoritative.

Inspect the complete diff and repository records.

Resolve the exact artifact identity before an approval, edit, commit, or push.

Stop and report the mismatch if reliable evidence cannot resolve it.

Security review

Run a new, independent Security review of the exact final specification.

Keep private repository content local.

Use official Apple sources for Apple Keychain claims.

Report findings first.

Give each finding a priority and exact line.

State APPROVED if no finding exists.

Otherwise, state CHANGES REQUIRED.

Review these Keychain outcomes:

- Only initial inventory errSecItemNotFound maps to no credential.
- Successful inventory requires a non-empty array.
- An empty successful array enters deletion-only recovery.
- One array member proceeds to complete validation.
- Multiple members enter deletion-only recovery.
- A successful non-array result enters deletion-only recovery.
- Exact-read errSecItemNotFound enters deletion-only recovery.
- IOS-AUTH-017, IOS-AUTH-069, and IOS-AUTH-070 have consistent outcomes.
- Deletion-only recovery blocks network access and clears usable credentials.

Verify these catalogue checks:

- 197 acceptance-test identifiers.
- 197 unique identifiers.
- No duplicates.
- No missing sequence identifiers.
- IOS-AUTH-001 through IOS-AUTH-070 are complete.
- No conflicting zero-result outcomes.

Pocock review

Run the required independent Pocock review against the same exact final artifact.

Record its exact commit, SHA-256, Git blob, findings, and verdict.

If the specification changes after either review, that approval becomes stale.

Repeat each affected review against the new artifact.

Progress page

Reconcile the Codemagic and Revyl development path into the tracked progress page.

Use this untracked page only as a wording source:

LOCAL_HOME\Documents\agentic-os-workspace\sqe\ACE_PROGRESS_GUIDE.html

Do not copy that page wholesale.

Match the tracked page's existing design and structure.

Record this approved path:

- Codemagic receives approved private source only after provider approval.
- Codemagic performs Xcode builds and automated tests.
- Revyl receives only the compiled simulator .app.
- Revyl provides iOS 26 simulator evidence.
- Final device evidence uses the approved Mac and an iPhone 15 Pro or later.
- Sift-KG and OpenViking remain separate fictional-data pilots.
- They are not build dependencies.
- Do not transfer PII, client evidence, passwords, certificates, production credentials, or usable tokens.

Required final checks

Inspect the complete final diff.

Run git diff --check.

Mechanically verify all catalogue identifiers.

Verify the exact staged file list.

Verify all upstream-to-HEAD commits and changed files.

Stop if unrelated work exists.

Commit and push the three authorized documentation files only.

Do not force-push or rewrite history.

Final report

Report:

- The exact final commit.
- The exact specification SHA-256.
- The exact specification Git blob.
- The exact PR head.
- The three changed files.
- Catalogue totals and sequence results.
- Pocock findings and verdict.
- Security findings and verdict.
- Tests and checks completed.
- The remaining implementation gates.
- Whether MCX-15 is ready for implementation.

Mark the goal complete only when all authorized deliverables are complete.
```
