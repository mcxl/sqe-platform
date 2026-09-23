# SQE, ACE And MATE — Vortex Review Brief

Prepared: 23 September 2026, Australia/Sydney.
Purpose: Independent review and sequencing recommendation. This brief does not authorise implementation or testing.

**Updated Owner Direction — Mobile Alternatives Reopened**

The owner now explicitly requests an independent investigation of other mobile delivery options. Continuing Swift is no longer a predetermined recommendation. This direction supersedes earlier review restrictions against considering Expo, Bolt or another mobile approach. It authorises investigation and recommendations only, not rebuilding or transferring private source to a provider.

Use the focused mobile investigation brief at `LOCAL_HOME\sqe-private\handoffs\2026-09-23-vortex-mobile-alternatives-investigation.md` as the current task. Retain this document as background evidence. Options 1 and 2 remain relevant to the shared web/backend direction.

## Authorities

The owner wants to take these two options into Vortex:

1. Finish the existing Python SQE web workbench.
2. Develop the newer Next.js interface around existing capabilities.

The owner also asks Vortex to evaluate a third option: finish iPhone verification first.

Evaluate all three against the work already done. Recommend an order and one bounded next deliverable. Do not assume a rebuild is needed, or assume the web-first recommendation is correct.

The owner is frustrated by repeated diagnostics, fragmented workspaces, and explanations that understate previous delivery. Be direct about completed work, uncertainty and avoidable rework. Base completion claims on evidence, not document headings or test counts alone.

Current owner direction: use Zauner as the sample engagement. The owner has authorised use of supplied Zauner material and public publication of the showcase. Do not restart blanket fictional-only discussions for that approved showcase. Distinguish this authority from a technical change to the operational application's existing data controls. Identify any such change precisely rather than silently bypassing it.

The owner asked for creative freedom. Use it in presentation and narrative structure. Treat documented events, proposed content and unverified outcomes distinctly in this review; do not report invented client decisions as evidence.

Apply applicable repository instructions. This is read-only review authority: no source edits, new dependencies, tests, commits, pushes, deployments, messages, cleanup or workflow changes.

## Current State

### What The Names Mean

- SQE is the application project and repository.
- ACE is the Assurance Compass Engine implemented within SQE.
- MATE means Mandate, Accountability, Trigger and Escalation. It assesses control design using approved inputs.
- The ACE iPhone app reads released information; it is not the auditor workbench.
- The Zauner website is a separately published, read-only showcase. It is not currently the operational SQE database or application.

### Work Already Present

| Area | Inspected Implementation And Records | Evidence Limit |
|---|---|---|
| Engagement setup | Creation, activation, selection, scope and activity records in the Python workbench | Current complete browser journey not established |
| Evidence review | Capture, source context/version, audit questions, decisions, links and completion | Existing full-flow integration test is present; not rerun for this briefing |
| MATE and connected assurance | Approval gate, evaluator, planning traces and relationship review | Source and historical tests exist; do not imply live real-client acceptance |
| Auditor views | Engagement summary, pending evidence, gaps, conflicts, graph and recommendations | Historical browser acceptance applies to historical revisions |
| Change history | Immutable snapshots, change detection and export packages | Export runtime dependencies need reconciliation |
| Client release engine | Draft creation, validation, publication, withdrawal, history and immutable action/conclusion snapshots | Service functionality exists; verify how a user invokes the complete workflow |
| Client web view/API | Authenticated read-only HTML and current-release JSON | Existing route: GET /client/api/v1/release/current |
| Next.js pilot | Read-only relationship-review interface backed by Convex | Not a replacement for the complete Python workbench; live configuration not established here |
| Swift client | Network transport, session state, Keychain, models, views and native tests | Native acceptance remains unresolved in the records reviewed |
| Zauner showcase | Public presentation, findings, evidence stories, RFI index and dated correspondence histories | Static generated presentation; no live RFI submission, replies or database integration |

An earlier Codex answer described these as though most connections still needed to be built. That was inaccurate. The subsequent source review confirmed substantial existing implementation. Review reuse first.

### Historical Delivery And Verification

The development record reports 365 passing tests on 18 August, then 799 for the later Phase 6B2 release work. These are historical suite totals, not additive counts and not new verification of today's dirty tree.

The existing test `test_full_record_review_flow_capture_to_completion` exercises capture, context, questions, versions, decisions, links and review completion. This is stronger evidence than merely having separate models, but does not alone prove a browser-to-iPhone release journey.

August 20–23 records describe implemented client releases, approved actions, immutable snapshots, service extraction and transport-neutral projection. Local source inspection confirms those components exist.

The September history shows a controlled Swift source import on 4 September and substantial simulator, accessibility, evidence-retention and runner work through the second week. Later local work changed layout and Copy behaviour. Commit messages establish changes, not acceptance.

On 19 September, the consolidated Windows source passed startup, seven selected existing tests and five HTTP viewing checks. The follow-up also confirmed a populated source-version field over HTTP. Browser verification remained blocked, and neither run demonstrated the complete write-and-release journey. They used an isolated seed database; captured media and full review completion were not demonstrated by that run.

### Current Repository Identity — Checked 23 September

- Main Windows folder: `LOCAL_HOME\Documents\sqe-platform`
- Origin: `https://github.com/mcxl/sqe-platform.git`
- Local branch: `codex/sqe-workspace-consolidation`
- HEAD: `478a7d8cd9c97d0bc43bd4d41ea460d589d4003a`
- The old `LOCAL_HOME\Documents\agentic-os-workspace\sqe` belongs to the parent `agentic-os-workspace` repository.
- The local `mac-consolidation-source` remote is a private Git bundle, not GitHub.

Commands used: `git status --short`, `git rev-parse HEAD`, `git branch --show-current`, `git remote get-url origin`, local `git log --all`, source reads and retained-report reads. No live GitHub status refresh or new runtime tests were performed for this brief.

### Zauner Showcase

Public URL: https://zauner-ims-review.alan-richardson.chatgpt.site/

Current Site source commit: `8a06ae2756fa7034091937828667d3fd0c6210c1`, separate from SQE HEAD.

Version 3 published successfully on 23 September. Twenty-one focused content/rendering checks and a fresh review passed. These checks use DOM stubs; browser layout and accessibility remain unverified. Publication evidence is separate from SQE application acceptance.

## Locked Decisions

- Preserve the existing Swift app and evidence as the baseline. The owner has reopened alternative mobile approaches for investigation; no migration is authorised yet.
- Codemagic is excluded from the current iOS route. Historical documents still mention it; do not execute them as current instructions.
- Free signing is selected. Paid membership, TestFlight and App Store submission are outside the current approved iOS delivery.
- Approved physical device: iPhone 15 Pro Max. Current connection is unknown.
- Required simulator coverage: iPhone 17 and iPhone 17 Pro Max with the recorded iOS 26.4.1 environment. Verify actual availability before use.
- Current approved Copy design is one button for the complete action record. Earlier individual-field Copy results are historical.
- Failed native findings remain failed. Passing retries do not explain earlier failures.
- Diagnostic split audits and discovery results do not establish acceptance.
- Preserve existing work, raw evidence and failed attempts. No automatic merge or destructive consolidation.
- This review may recommend a scope change, but must distinguish recommendation from approved execution authority.

## Mandatory Changes

No implementation changes are authorised by this brief. The required deliverable is an independent assessment containing:

1. A capability map: implemented, historically tested, currently verified, missing, or unknown.
2. A comparison of the three options, showing reuse, dependencies, unresolved work and user-visible result.
3. A clear recommendation: web first, iPhone first, or a bounded parallel sequence.
4. An evidence-based judgement on whether iPhone-first is genuinely near completion.
5. One proposed next work block with deliverable, baseline, permitted changes, checks, stop conditions and required inputs.
6. Explicit corrections to this brief or earlier Codex statements where evidence warrants them.

Assess Option 2 as an interface decision, not an automatic backend rewrite. Determine which existing Python capabilities can be reused and whether an additional integration boundary is required. Do not silently choose a second source of truth.

For the RFI feature, separate existing audit questions and decisions from the newly requested correspondence history. The inspected Python source did not establish an operational feature matching the showcase's complete request/response trail. This is a scoped finding, not proof that no related implementation exists anywhere.

## Optional Or Out Of Scope

- Implementing a broad redesign, new framework, database migration, hosting change or orchestration tooling. Investigating mobile alternatives is now explicitly in scope.
- Full native test execution or another large verification programme before reviewing the retained evidence.
- Repeating successful checks whose files, inputs, tools and environment are unchanged.
- Publishing operational records, source emails, attachments, contact details, credentials or private evidence.
- Sending this brief or client documents to another service automatically. The owner will take the brief into Vortex.
- Repository cleanup, folder deletion, merging or discarding uncommitted work.

## Dependencies And Environment

### Native Work

Recorded Mac workspace: `LOCAL_HOME/Developer/sqe-platform-release-layout`

SSH alias: `ace-mac`

Recorded Mac branch: `codex/mcx19b-release-layout`

Last consolidation-verified candidate: `40bae2640b23eb05496a093d09a4c20186403879`. This is not a fresh Mac HEAD check.

Native evidence root: `LOCAL_HOME/ace-private/mcx19b-orientation-repair-20260915`

Read first:

- `08-copy-confirmation-diagnosis/discriminating-diagnostic-result.json` under that root.
- `13-p0-discovery-runner-20260917` under that root.
- The D2 instruction identifies the additional diagnostic records. Confirm actual execution and outcomes from retained files; this briefing did not inspect a final D2 result.

Recorded Xcode: 26.4.1 (`17E202`); iOS runtime: 26.4.1 (`23E254a`). Availability now is unverified.

Recorded signing profile expired on 21 September 2026 at 12:37:21 AEST. That recorded profile is now past expiry; whether a replacement exists is unknown. Do not describe device installation as immediately available without checking.

Windows and Mac working trees are not automatically synchronised.

### Evidence And Read-First Files

All paths below are local. A remote Vortex session cannot be assumed to access them. Report unavailable evidence rather than substituting summaries as proof.

| Purpose | Path |
|---|---|
| Development history and limits | `LOCAL_HOME\Documents\sqe-platform\DEV_STATE.md` |
| Workspace topology | `LOCAL_HOME\Documents\sqe-platform\WORKSPACE-GUIDE.md` |
| Evidence review service | `LOCAL_HOME\Documents\sqe-platform\src\ace\workbench\evidence_review.py` |
| Release lifecycle service | `LOCAL_HOME\Documents\sqe-platform\src\ace\workbench\client_release_service.py` |
| Web routes | `LOCAL_HOME\Documents\sqe-platform\src\ace\workbench\routes.py` |
| Client read routes | `LOCAL_HOME\Documents\sqe-platform\src\ace\workbench\client_routes.py` |
| Full evidence review test | `LOCAL_HOME\Documents\sqe-platform\tests\test_evidence_review.py` |
| Release tests | `LOCAL_HOME\Documents\sqe-platform\tests\test_client_release.py` |
| Next.js pilot boundary | `LOCAL_HOME\Documents\sqe-platform\apps\relationship-review-pilot\README.md` |
| Current iOS specification | `LOCAL_HOME\Documents\sqe-platform\docs\specs\2026-08-24-ace-ios-read-only-client-application.md` |
| Controlling local plan | `LOCAL_HOME\Documents\sqe-platform\docs\plans\2026-09-14-ace-ios-local-verification.md` |
| Discovery candidate | `LOCAL_HOME\Documents\sqe-platform\docs\plans\2026-09-17-ace-ios-discovery-candidate.md` |
| Revision 5 instruction | `LOCAL_HOME\Documents\sqe-platform\docs\ace\2026-09-16-ace-ios-swift-completion-instruction.md` |
| D2 fourth draft instruction | `LOCAL_HOME\Documents\sqe-platform\docs\ace\2026-09-17-ace-ios-copy-reflow-check-instruction.md` |
| Consolidation identity evidence | `LOCAL_HOME\sqe-private\consolidation-20260918\stage3\STAGE-3-EXECUTION-REPORT.md` |
| Recent web verification | `LOCAL_HOME\sqe-private\consolidation-20260918\stage4\STAGE-4-VERIFICATION-REPORT.md` |
| Source-version follow-up | `LOCAL_HOME\sqe-private\consolidation-20260918\stage4\followup-20260919\FOLLOWUP-REPORT.md` |
| Showcase source and verification | `LOCAL_HOME\sqe-private\zauner-example-20260919\public-site`; `correspondence\CONVERSATION-LAYOUT-20260923.md` under the same example root |

The two approved instruction hashes were rechecked on 23 September using SHA-256:

- Revision 5: `252aab6ba1115b72f1fcbd84c3d49f3429550c0845d96c2008088d15bdbbe629`
- D2 fourth draft: `f7147730b09e0b4daf5d18090abc29d38f780962479dc55a49631af20c1f2179`

## Dirty Worktree Warnings

The following already existed before this briefing. Preserve them; do not reset or overwrite them:

```text
 M DEV_STATE.md
 M docs/specs/2026-08-24-ace-ios-read-only-client-application.md
?? .snapshots/
?? SQE_DEVELOPER_HUB.html
?? WORKSPACE-GUIDE.md
?? docs/ace/
?? docs/plans/
?? ios/
?? tests/test_ios_accessibility_layout.py
?? tests/test_ios_action_targets.py
?? tools/
```

The new GitHub repository's existence does not establish that these imported files have been committed or pushed. Local HEAD remains the August 25 commit. The consolidation record reports 29 imported Mac files and two approved instruction copies; held variants remain elsewhere.

The workspace guide and development record contain dated statements superseded by later work, including the now-published Zauner showcase and its authorised real sample. Preserve their historical meaning without treating every old restriction or next step as current authority.

## Verification Criteria

For the review, identify the evidence supporting each material conclusion. Separate source presence, historical tests, current execution, browser acceptance and device acceptance.

For iPhone-first, account for all retained acceptance requirements:

- The 22-case acceptance pilot is separate from diagnostic/discovery runs.
- Full coverage is 836 cases: 512 unrestricted accessibility audits and 324 layout-only cases.
- Nine existing UI regression selectors remain in scope.
- Latest local plan lists 68 unit/contract tests, including the 43-test contract subset. Do not add the subset twice or substitute earlier counts.
- Physical VoiceOver, clipboard, Keychain, signed-device, privacy and approved-service checks remain required unless specifically changed by the owner.
- Historical baseline ancestry remains a recorded acceptance issue.
- Reviews and one clean candidate remain required by the controlling route.

Do not give a completion percentage based on commits, written tests or elapsed effort. Estimate remaining work only after inspecting actual candidate results and dependencies. Identify unknown durations explicitly.

For web-first, distinguish demonstrating existing functionality from new RFI integration, UI changes, environment fixes and operational deployment. The proposed next block should not bundle all four.

## Unresolved Matters

1. Copy accessibility root cause is not established in the reviewed records. A retained high-contrast rendering does not show what Apple's checker sampled. Repeated passes do not explain earlier failures.
2. D1 Arm C was closed as incomplete, not passed. D2's final execution result was not inspected for this briefing. Verify before recommending more diagnostics.
3. Earlier failures included real layout defects, test timing problems, invalid simulator operations and environmental faults. These are different causes; do not treat all as one app defect.
4. Current Mac HEAD, clean state, phone access, renewed signing and private-service configuration are unverified here.
5. Some Mac Python approval/G0 changes were held during consolidation. Determine their actual relationship to web completion before proposing replacements.
6. The September web environment report identified missing declared packages in the repository lock. An isolated environment was used; the repository lock was not repaired in that block.
7. Browser viewing was blocked during September verification. This does not establish an application defect. Do not bypass an explicit browser-policy restriction.
8. No currently accepted complete auditor-to-web-client-to-phone journey was found in the inspected evidence. That is an acceptance gap, not proof that every integration is absent.
9. The exact operational scope for Zauner data must be reconciled with existing application controls. Public-showcase authority does not automatically implement that change.

Codex's previous web-first recommendation is provisional. Vortex should challenge it if the retained evidence supports a lower-risk, more useful iPhone-first completion.

## Redacted Continuation Prompt

Review this brief and the accessible source/evidence. Do not implement or run tests yet.

I want to continue SQE using Zauner as the sample engagement. Substantial August work already implemented engagement setup, evidence review, MATE, relationship review, approved actions and client releases. September work added and verified parts of the Swift iPhone client but repeatedly stalled in accessibility and test-process diagnostics. The separate public Zauner site is a presentation, not the operational application.

Evaluate these options independently:

1. Finish the existing Python web workbench.
2. Develop the Next.js interface using existing capabilities.
3. Finish iPhone verification first.

The Windows repository is LOCAL_HOME\Documents\sqe-platform, branch codex/sqe-workspace-consolidation, HEAD 478a7d8cd9c97d0bc43bd4d41ea460d589d4003a, with preserved uncommitted imports. Do not discard them. The Mac workspace is LOCAL_HOME/Developer/sqe-platform-release-layout. Native evidence is under LOCAL_HOME/ace-private/mcx19b-orientation-repair-20260915. Verify access and current state; these paths are not proof that your environment can read them.

Start with a short verdict. Explain what is already built, what is actually missing, and which option provides the most useful result with the least repeated work. Recommend one bounded next deliverable. Identify missing evidence and any necessary owner decisions. Challenge Codex's previous conclusions when warranted. Do not invent a root cause, percentage complete, test result, client decision or completion estimate.

Remain read-only. Do not install a new stack or tooling, change code, run tests, commit, push, deploy, clean up, merge or send external messages. Do not restart Codemagic. Mobile alternatives, including Expo/Bolt, are now open for investigation under the focused brief. Preserve the existing Swift work while recommending any change for the owner's decision. Report inaccessible evidence plainly. Historical passing tests and a published showcase do not establish current operational acceptance.
