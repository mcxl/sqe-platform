# Development State

ACE is a private, deterministic WHS auditor workbench for the Squadron Energy engagement. This file is the verified development handover. `ACE_PROGRESS_GUIDE.html` is the visual roadmap. Code, provider records, Linear, and test evidence control when records disagree.

## Current Controls

The client has not accepted the review. G0 blocks real client information. Use only fictional, public, or AuditCo-owned information. The auditor remains the only approval authority. Interface code must use the existing domain gates. Do not run DeepSec without new approval and an approved isolation design.

## Repository State

The current remote Phase 2 branch is `origin/codex/ace-sprint-1`. It points to merge commit `1742cb0f750bb3f2ee0720846a8c1d7a5aaff7db`.

This local checkout remains at `9cdae92`. It has 18 local-only commits and 44 remote-only commits. The wider workspace also contains existing user changes and untracked files. Do not reset, merge, or clean this checkout without a separate scope check.

## Verified Core

The tested Python core covers ratings, MATE approval, planning traces, evidence conclusions, Engagement setup, image capture, and evidence review. The FastAPI workbench uses authentication, external storage, immutable decisions, version-specific approvals, and unique retry keys. Core files are `src/ace/app.py`, `src/ace/domain/assessment.py`, `src/ace/engine/approval.py`, and `src/ace/workbench/`.

The last recorded Python suite ran on 15 August 2026. Python 3.12.13 and pytest 8.4.2 passed all 357 tests. One Starlette TestClient deprecation warning remained.

## Mobile Workbench Proof

On 18 August 2026, the workbench ran on a MacBook at `192.168.86.97:8000` and opened in iPhone Safari over the local Wi-Fi network. A fictional image was captured successfully. The evidence preview displayed in Safari. The item was marked reviewed. The workbench showed one reviewed item, zero pending items and zero open conflicts.

Protected offline drafts and full record review are now verified. Do not use real client information. Use fictional, public or AuditCo-owned material only.

## Phase 2 Delivery

MCX-1 through MCX-4 are Linear onboarding tasks. They are not delivery issues.

MCX-5, MCX-6, MCX-7, and MCX-8 are complete in Linear. MCX-6 added Relationship Review navigation to the authenticated Python workbench. Pull request 32 merged as `dcd7e74c55b25bffeec08de7e43e377fa0509048`.

MCX-8 added an isolated, read-only Relationship Review pilot. It uses Next.js, Convex, fictional records, and a protected Vercel Preview. It does not change Python controls, G0, decisions, or approvals.

Pull request 33 merged the approved head `f80e60efb4c57c1a6c138b7e488920099ec4f926`. The merge commit is `1742cb0f750bb3f2ee0720846a8c1d7a5aaff7db`. The final suite passed 12 tests. Typecheck, lint, build, browser navigation, URL validation, and protected Preview checks passed. All review threads closed. Fresh Sol returned `ship`.

MCX-9 preserves the earlier failed physical iPhone Safari evidence and is `Canceled`, not `Done`. A later MacBook-hosted test passed on 18 August 2026; see Mobile Workbench Proof. MCX-10 exists in `Todo` with the title `[SQE] Decide Relationship Review Pilot Next Phase`.

MCX-10 records the approved decisions. Continue the Convex and Vercel pilot. Keep application sign-in optional. An Australian data location is acceptable. Keep provider cost at zero. Keep real client use and Production excluded. The next approved slice was the read-only Relationship Details view.

On 17 August 2026, the Relationship Details slice was added to the existing pilot. A user can select one fictional relationship and view its owner, status, evidence, gaps, and review notes. The view has no edit, delete, upload, approval, decision, form, or public write action. The labels are: Owner (engagement name, no ID), Status ("Waiting For Review"), Evidence (was "Source Support"), and Review Notes (was "Earlier Decisions", restructured to show decision, basis, and recordedOn with empty-state "None recorded.").

The pilot suite passed all 13 tests. Typecheck, lint, production build, local browser checks, and protected Preview browser checks passed. The final Preview returned `READY`. An unauthenticated request redirected to Vercel SSO. An authorised provider request returned `200`. Three rounds of Pocock review returned clean. Three rounds of Fresh Sol review returned clean. The automatic Greptile review for pull request 37 was consumed (COMMENTED). The Codex P2 comment about the Owner label was informational only and did not authorise a label change; the Owner label matches the approved acceptance criteria.

The current protected Preview is https://relationship-review-pilot-du6kr3jbz-mcxl1.vercel.app. It was deployed from the repository root using the sqe Vercel token and the existing project configuration. The deployment targeted Preview. No Production deployment exists. Vercel Git integration remains disconnected.

## Known Limits

The pilot uses fictional information only. It has no approval, decision, edit, delete, upload, or public write action. Physical iPhone Safari capture, preview and review remain outside the completed Phase 1 scope. G0 approval is required before real client use.

The Relationship Details source is committed on branch `alanrichardson/mcx-11-relationship-details-final`. Pull request 37 targets `codex/ace-sprint-1`. The final head is `373b84d843043f202b021a63c1524303e1f4be31`. The validated base is `1742cb0f750bb3f2ee0720846a8c1d7a5aaff7db`. It changes the two approved pilot files and the separately approved root `greptile.json` file.

Focused tests passed 8 of 8. The complete pilot suite passed 13 of 13 (8 workbench + 5 Convex integration). Typecheck and production build passed. Lint had zero errors with five existing generated-file warnings. Three rounds of Pocock review returned clean. Three rounds of Fresh Sol review returned clean. One authorised automatic Greptile review was consumed on pull request 37 (COMMENTED at 2026-08-17T12:12:25Z). No further Greptile triggers.

The approved `.greptile/config.json` attempt did not prevent an automatic ready-state review on a new pull request. The second and final corrective attempt moved the same settings to root `greptile.json`. The two-corrective-attempt stop rule now applies. All later Greptile reviews must remain manual-only. Do not make a third repository-configuration attempt.

The Codex P2 comment suggesting "Owner" be changed to "Linked Engagement" was informational only and did not authorise a label change. The Owner label was briefly changed and then restored. The acceptance criteria require Owner. All re-validation after the restore passed cleanly.

Pull requests 34, 35, and 36 remain draft. Pull request 37 was marked ready for review on 17 August 2026 after exact-head final validation completed. The protected Preview https://relationship-review-pilot-du6kr3jbz-mcxl1.vercel.app was deployed and verified. MCX-11 Linear labels: `sqe`, `approved`, `ready-to-merge`.

Pull request 37 was merged on 17 August 2026 at 23:54 UTC. The merge commit is `d71693a3`. The exact pair was head `373b84d843043f202b021a63c1524303e1f4be31` and base `1742cb0f750bb3f2ee0720846a8c1d7a5aaff7db`. MCX-11 was updated to `merged` in Linear. The issue is now `Done`.

## Protected Offline Drafts

Pull request 38 was merged into `codex/ace-sprint-1` on branch `vorflux/offline-drafts`. The merged head is `17587f8` and the merge commit is `4ba9a8a`. It adds protected fictional offline Engagement drafts, IndexedDB storage, reconnect sync, and the `POST /workbench/api/v1/engagements/sync` endpoint. Real-client data is blocked by client-side and server-side G0 checks.

On 18 August 2026, the focused PR test set passed 29 of 29 tests. A live browser test also passed: a fictional draft saved to IndexedDB while Chrome was offline, remained pending, then synced to the local server with HTTP `201 Created` after network restoration. The pending offline draft was cleared after reload. The browser test used reference `ENG-OFFLINE-002` and fictional data only. The final PR suite passed 365 of 365 tests across 7 changed files.

The browser test initially used a URL with embedded Basic Authentication credentials. Chrome rejected relative fetch requests from that URL. Reopening the same page without embedded credentials allowed the saved Basic Authentication session to send the sync request. Use `http://127.0.0.1:8000/workbench/engagements/new` after authentication, not a URL that embeds the credentials.

Pull request 38 is merged. The exact merged head `17587f8` was revalidated before merge. No Production deployment occurred.

## Engagement Control Summary

The current Phase 2 feature is `GET /workbench/engagement/summary`. It shows engagement details, evidence counts, open review items, relationship conflicts, recent activity, and the recommended next action.

The recommendation order is `DRAFT`, no evidence, pending review, conflicts, then gaps. Relationship conflicts appear only when linked evidence has `is_capture=1`. Recent activity can be empty for seeded engagements with no audit events. Recommendations are rule-based, not AI-driven.

Pull request 39 added the Engagement Control Summary. The merged head is `a4fd72e` and the merge commit is `bcc5db6`. The full test suite passed 378 of 378 tests. Browser verification passed. Phase 2 is complete.

## Phase 6B1 Approved Client Actions

Phase 6B1 is complete. Pull request 52 merged on 23 August 2026. The exact head was `1d832a54065b7446df21346c79fe2b6270716eed`. The merge commit was `1898e34716145a254ab876615360d1e6c7d02766`.

The release engine now gives the client a fixed view of approved conclusions and actions. It keeps published snapshots unchanged. It keeps withdrawn releases. It checks the source, engagement, version, approval data, audit event, owner, date, status and publication data before release.

The pull request had 40 commits and changed four files. It added 8,654 lines and removed 147 lines. Tests supplied approximately 82 per cent of the added lines.

Final verification passed:

- Focused tests: 289 passed.
- Full suite: 762 passed with one warning.
- API and HTML checks: 27 passed.
- Document tool check: passed.
- `git diff --check`: clean.
- Pocock standards review: no findings.
- Pocock specification review: no findings.
- Fresh Sol review: `SHIP`.
- Exact-head Codex review: no major issues.
- Review threads: 31 closed and zero open.

### Root Cause And Lessons

Phase 6B1 started as a client-view feature. It became a publication and record-integrity engine. The full release rules were not fixed before the build started.

The design mixed seed work, database migration and normal release work. It also put many business rules in SQLite triggers. Each review then found another state that the original plan did not cover. Review became part of requirements discovery.

Use these lessons for Phase 6B2:

- Define the complete release-state matrix before code changes.
- Separate seed, migration and normal application work.
- Put business workflow in one application service.
- Keep only essential integrity rules in the database.
- Test draft, published, withdrawn and legacy states before review.
- Start an architecture review when the first review finds a design-wide fault.
- Use one shared service for web and mobile clients.

## Phase 6B2 Architecture Gate

Do not start Phase 6B2 implementation until one short architecture review is approved. The review must compare three options:

1. Keep the current trigger-based engine.
2. Refactor the current engine into one release application service.
3. Adopt Payload, Directus or another existing platform.

The recommended option is to refactor the current engine. A `ClientReleaseService` should control draft creation, validation, publication, withdrawal, current-release queries and release history. Web and mobile clients should use the same service. The database should keep essential keys, status checks, version rules and terminal-state protection.

Estimate the refactor at 30 to 45 engineering hours, or four to six working days. Use a planning budget of 40 hours and three million Codex tokens. This estimate includes implementation, migration checks, tests and review.

This is a decision gate. It does not approve a rewrite, a new platform or Phase 6B2 implementation.

## MCX-15 Native iOS Read-Only Client

At the protected-candidate checkpoint, pull request 1 was a draft at exact head `cdc4f458bfd3ede385844b31eed117d3c06e854d`. The local, remote and pull request heads matched. GitHub reported a clean merge state. The separate evidence-branch record below does not replace or approve this protected candidate.

Codemagic ran the Release `-O` suite on the exact head. All 65 tests passed with Xcode 26.4.1 and Swift 6.0. Pocock Specification and Pocock Standards approved the exact head with no findings. Fresh Sol returned `ship` with no findings. The primary review found no repository change from the reviews.

The Phase 6.1 readiness check has a conditional hold. All 197 acceptance identifiers have unique mappings. The [evidence matrix](https://github.com/mcxl/ace-iphone-fictional-test/blob/cdc4f458bfd3ede385844b31eed117d3c06e854d/sqe/ios/ACEClientApp/evidence-matrix-audit.md) records 153 complete identifiers and 44 pending identifiers. Twenty-two pending identifiers have partial automated evidence. No identifier is uncovered. Seven identifiers have stated known limitations.

The 44 pending identifiers need approved runtime or controlled evidence. The [runtime evidence plan](https://github.com/mcxl/ace-iphone-fictional-test/blob/cdc4f458bfd3ede385844b31eed117d3c06e854d/sqe/ios/ACEClientApp/RuntimeEvidencePlan.json) records each required check. No exact-head merge approval exists.

Do not add a readiness label or merge the pull request yet. No Production action occurred.

### Historical Phase 6.1 Simulator Correction And Bundle Diagnosis — 3 September 2026

This subsection preserves the earlier diagnosis checkpoint. Its proposed work and approval limits describe that checkpoint, not the current state. The successful build and review record below supersedes its next steps.

The protected candidate remains `cdc4f458bfd3ede385844b31eed117d3c06e854d`. The separate evidence branch is `codex/mcx-15-phase6-1-simulator-probe-v2` in `mcxl/ace-iphone-fictional-test`. Its verified head at this checkpoint was `ffa73729ab1c45e947ec13d6db00a7b709143b3a`. The worktree is `C:\tmp\sqe-mcx-15-phase6-1-simulator-probe-v2`. Keep this worktree separate from the shared checkout and its existing changes.

The simulator correction started from `b36f89c7fee9e37f1014933408fea78bd9eb80a1`. [Codemagic build 6a976d0efc75f66daa13f375](https://codemagic.io/app/6a8d159f213e726dd243b4fb/build/6a976d0efc75f66daa13f375) passed all 65 Release XCTest tests on iPhone SE. Its UI-test step rejected `com.apple.platform.iphonesimulator`.

Commit `b0eaaa74fa45f60e1ccbda6c3b4ec6faa5e07982` added `SUPPORTED_PLATFORMS = "iphoneos iphonesimulator"` to UI Debug and Release. It changed only `sqe/ios/ACEClientApp/ACEClientApp.xcodeproj/project.pbxproj`. Commit `ffa73729ab1c45e947ec13d6db00a7b709143b3a` then corrected the controlled ancestry gate and its evidence-control text. Both commits are pushed. No merge occurred.

The gate verification passed six mechanical cases: the new valid route, both historical routes, and rejection of missing, extra, and unrelated-parent cases. Fresh Sol returned `ship` for the reviewed gate change. The primary session inspected the complete diff and reran the focused checks.

The authorised [Codemagic build 6a98a72a2b2190ef76443c3c](https://codemagic.io/app/6a8d159f213e726dd243b4fb/build/6a98a72a2b2190ef76443c3c) fetched exact head `ffa73729ab1c45e947ec13d6db00a7b709143b3a`. Its ancestry gate passed. Release XCTest passed 65 tests with zero failures. The unsupported-platform error did not recur.

The UI-test step then failed during build planning with exit code 65. Xcode reported duplicate output at `Debug-iphonesimulator/-Runner.app/PlugIns/.xctest`. No UI test ran. The build completed with failure; no build remains active.

The approved read-only diagnosis used Terra and a Fresh Sol review. Both UI-test configurations omit `PRODUCT_NAME`. Neither inherits a project-level value or an xcconfig value. The target and scheme name the correct product. All four UI commands select Debug and have no product-name override. This strongly supports the missing-name diagnosis.

The smallest proposed target correction is `PRODUCT_NAME = "$(TARGET_NAME)";` in UI Debug and Release, at project lines 83 and 84. This correction is not implemented or approved. No evidence justifies changes to Swift, test source, dependencies, security controls, or architecture settings.

Fresh Sol returned `ship` for the diagnosis only. Windows inspection does not prove Xcode's resolved settings or successful execution. A later authorised check must inspect native `-showBuildSettings` and run a focused UI build. The host did not enforce read-only review. Before-and-after hashes of all 26 tracked worktree files matched, and the worktree stayed clean.

A normal new child of `ffa73729` would fail the current ancestry gate. Any later Codemagic run therefore needs a separately approved, exact ancestry update and matching control text. Do not treat the diagnosis approval as permission to implement, commit, push, merge, or run Codemagic again.

All 44 evidence identifiers remain pending. The protected candidate is unchanged. No Greptile, CodeRabbit, or DeepSec scan ran for this correction. Temporary validator files remain outside the repository because host policy blocked cleanup: `C:\tmp\mcx15-parent-gate-resume.sh` and `C:\tmp\mcx15-parent-gate-resume.idfJpI`.

### Current Phase 6.1 Build And Artifact Review — 3 September 2026

The latest verified evidence-branch head is `91818a476c7ddb81c48aba63c76b11cfbcb70df4`. Its first parent is `921d38e096ad4214f44f0f9c32cdad96ab1a49cf`. The branch remains `codex/mcx-15-phase6-1-simulator-probe-v2`. Its remote is `vorflux-harness` in the separate worktree above. The normal commit and push completed under the user's approval. No merge occurred. The protected candidate remains unchanged.

The last correction made screenshot destinations absolute. It changed exactly four files: `codemagic.yaml`, `RuntimeEvidencePlan.json`, `RuntimeEvidencePlan.md`, and `Phase6_1EvidenceRegister.md`. The three evidence documents are under `sqe/ios/ACEClientApp/`. That correction did not change Swift, tests, dependencies, security controls, or repository tools.

The installed Terra lane implemented that correction. Fresh Sol returned `ship` for preparation only, with no required correction. The primary session inspected the complete diff. Focused checks passed 36 ancestry cases and 10 screenshot destinations, including failure propagation. Native capture was still pending at that review; the later build supplied the execution evidence below.

The single authorised [Codemagic build 6a992d72df4f3e11bdebb36c](https://codemagic.io/app/6a8d159f213e726dd243b4fb/build/6a992d72df4f3e11bdebb36c) completed successfully. Its checkout matched `91818a476c7ddb81c48aba63c76b11cfbcb70df4`. The GitHub check also reported `completed/success`. Xcode was 26.4.1, build `17E202`. The Xcode result summaries reported iOS Simulator 26.4.1.

The saved logs and user-supplied Xcode summary photos confirm these results:

| Result Bundle | Device And Appearance | Passed | Failed |
|---|---|---|---|
| `iphone-se-release-xctest.xcresult` | iPhone SE (3rd generation), Release XCTest | 65 | 0 |
| `iphone-se-ui-audits-light.xcresult` | iPhone SE (3rd generation), light | 5 | 0 |
| `iphone-se-ui-audits-dark.xcresult` | iPhone SE (3rd generation), dark | 5 | 0 |
| `iphone-16-pro-max-ui-audits-light.xcresult` | iPhone 16 Pro Max, light | 5 | 0 |
| `iphone-16-pro-max-ui-audits-dark.xcresult` | iPhone 16 Pro Max, dark | 5 | 0 |

This is 65 Release tests and 20 UI test executions, with zero failures. The 20 UI executions repeat five tests across four configurations. The iPhone 16 Pro Max light photos also show the passed controlled-scenarios test and its reset-message check. All four UI summaries show 54 build warnings. Passing tests do not resolve or approve those warnings.

The build published [ace-iphone-fictional-test_13_artifacts.zip](https://api.codemagic.io/artifacts/612ccdf9-7e37-4428-9e09-4fd6e72563b1/49281ea8-0eb4-4c89-b534-f5c378217a10/ace-iphone-fictional-test_13_artifacts.zip). The downloaded archive SHA-256 is `A26CFF0239EAB0CBC2935DFAFF86271969ADCA4405BF6D0F7694A6C6EAA3EFDF`.

The retained local review folder is `C:\tmp\mcx15-artifact-review-6ab5cfa9570848c3807070a12ad9e278`. It contains the original ZIP and extracted files. ZIP path and CRC checks passed. All 377 extracted files matched the archive. The five result bundles contain readable metadata and their root data files. These structural checks do not replace a full content review.

The primary session visually checked all 12 PNG files: 10 planned captures and two path-pilot images. All opened and showed content. Device dimensions were 750 by 1334 pixels for iPhone SE and 1320 by 2868 for iPhone 16 Pro Max. Light and dark captures matched their labels. Sign-in fields were empty. Release and privacy views showed the fictional-pilot banner. No visible credentials or real client data were found in these PNGs. The two path-pilot images matched the iPhone SE light sign-in image exactly.

The release captures show only the upper content at the large text setting. The iPhone SE capture ends at the Review status heading. The iPhone 16 Pro Max capture ends part-way through the Release version value. These still images do not prove lower-field visibility or scrolling. They do not establish a new text-clipping fault. The privacy-view captures do not prove app-switcher protection.

The user opened all five saved result bundles in Xcode on a Mac. Photos confirmed every test-summary pass count. Selected activity details were inspected for the iPhone 16 Pro Max light controlled-scenarios test. This was a summary and selected-activity review, not a full inspection of every result-bundle attachment or log. Full prohibited-data and redaction review remains pending. No new tests or builds ran during this review.

#### Remaining Evidence Work

All 44 evidence identifiers and all 10 packages remain `pending`. P01, P02, P03, both P08 rows, both P09 rows, and all nine P10 rows now contain reviewed partial results. The existing plan and register define the remaining scope:

| Package | Remaining Work Before Acceptance |
|---|---|
| P01 | The local ancestry, file-scope, and sanitised-manifest checks passed. Formal approval remains pending. |
| P02 | Saved tests and source show partial returned-attribute guards. Complete the matrix on an approved signed iPhone with the approved access group. |
| P03 | Saved tests and source show partial access-group guards. Run matching and mismatched cases on an approved signed iPhone. |
| P04 | Map the saved audit results to identifiers. Complete the required accessibility and orientation states not established by this build. |
| P05 | Complete the specified VoiceOver, locked-device, and app-switcher journeys. |
| P06 | Complete approved review of all logs, screenshots, and result-bundle contents for prohibited data and redaction. |
| P07 | Complete network validation using an approved Preview endpoint and certificate. |
| P08 | Both saved negative builds failed at the input check. Formal approval and complete privacy review remain pending. |
| P09 | Saved normal screenshots and four sign-in images were reviewed. The sign-in fields are visible and empty. Evidence of a populated visible username, complete privacy review, and formal approval remain pending. |
| P10 | The three PNG files exist. The locked server compatibility test passed. Runtime callback timing and formal approval remain pending. |

An approved operator must record each result. Record the artifact, device, software, operator, date, and all required commit references. An independent reviewer must check the evidence and applicable approvals before acceptance. Test passes and summary photos cannot accept an identifier automatically.

#### Manual App-Switcher Pilot Result — 4 September 2026

Alan Richardson completed the approved simulator capture on a MacBook Pro.
The simulator was an iPhone 16 Pro Max.
Its UUID was `6D2FD18F-22B3-4403-ADFA-A5FB76F3C874`.
Xcode was 26.4.1. The simulator runtime was iOS 26.4.1.

The app was a local Debug simulator build from source commit `91818a476c7ddb81c48aba63c76b11cfbcb70df4`.
It used bundle identifier `com.example.aceclientapp`.
It used the approved fictional release scenario.
The build completed with `** BUILD SUCCEEDED **` before this capture.

The operator confirmed this sequence:

1. The active app showed the fictional release information.
2. The app-switcher card showed the white privacy cover.
3. The cover showed only `ACE Client` and `FICTIONAL PILOT — CONTROLLED`.
4. The cover showed no release information.
5. The fictional release information returned after the operator selected the app card.

The three original simulator PNG files are in this folder on the operator's Mac:
`LOCAL_HOME/Desktop/MCX15-privacy-cover-2026-09-04`.

| Original PNG | SHA-256 |
|---|---|
| `01-active.png` | `05751860bdd140ba5b589b3dad60db9e0f1e1d436646a237d55996796efb2661` |
| `02-app-switcher-cover.png` | `010d82c29fdb662080270073373f2fe67e90d018178930085f293d84032a7b57` |
| `03-restored-active.png` | `a47e9853892ffb43b10e0987d6cc2d2ea8683b420d1c913c62930d6c9d8d3b49` |

The `shasum -a 256` command completed for all three files.
The supplied photos also show successful simulator writes for all three paths.

This evidence confirms the visible state sequence.
Still images do not prove the exact inactive-callback or active-callback order.
A fresh read-only Codex technical review returned `ship`.
It confirmed the file count, dimensions, sizes, hashes, and visible state sequence.
It found no visible credentials, personal information, or real client data.
Alan Richardson designated Codex as the independent technical reviewer on 4 September 2026.
This review is not a human or organisational signature.
Controlled registration is complete for all nine P10 rows.
The server compatibility test passed in the locked environment.
Runtime callback timing and formal approval remain pending.
All 44 identifiers and all 10 packages remain pending.

The controlled branch worktree now contains the three PNG files, review records, and two register changes.
No acceptance status, issue label, or approval gate changed.
No commit, push, merge, new Codemagic run, Greptile, CodeRabbit, or DeepSec scan occurred during this update.

## Goal History And Next Action

### MCX-15 Manual Evidence Preparation

The user requested a goal and its completion on 3 September 2026. The bounded goal is to prepare and check the next manual evidence handoff. It does not include new runtime work or formal evidence acceptance.

[MCX15_MANUAL_EVIDENCE_HANDOFF.md](MCX15_MANUAL_EVIDENCE_HANDOFF.md) maps all 44 pending identifiers into their existing 10 packages. It records source procedures, saved evidence, missing checks, and approval dependencies. It now records the completed simulator pilot.

The preparation goal is complete. The primary session read the full handoff and inspected the dev-state changes. Mechanical checks passed for identifier coverage, package membership, artifact paths, archive hash, Markdown tables, and local source links. All four controlled-source hashes remained unchanged. The evidence worktree stayed clean. The earlier dev-state sections remain unchanged.

Read-only checks found both saved negative Preview-input build logs. They contain the expected origin-rejection messages and build-failure markers. P08 therefore starts with review of existing evidence, not an automatic rerun. The accessibility-settings log is empty; its presence does not prove settings coverage. The artifact package contains no `.app` directory. A result bundle is not a live application for manual capture.

Use successful build `6a992d72df4f3e11bdebb36c` as the current saved Codemagic evidence.
The manual capture used the local Debug build recorded above.
The controlled register now records reviewed partial results for all nine P10 identifiers.
The controlled artifact path is `sqe/ios/ACEClientApp/build/phase6-1/manual-app-switcher-2026-09-04/`.
The callback review path is `sqe/ios/ACEClientApp/build/phase6-1/callback-evidence-review-2026-09-04/`.
The server review path is `sqe/ios/ACEClientApp/build/phase6-1/server-compatibility-2026-09-04/`.
The next step is approved runtime callback-timing evidence and formal review.
Keep every status pending until the formal acceptance gates pass.

The completed capture does not complete the remaining content, runtime timing, or formal review.
All 44 evidence identifiers and all 10 packages remain pending.
No repository code, commit, push, merge, or Production action formed part of the capture.

### MCX-15 P10 Follow-On Evidence Review — 4 September 2026

Goal: Find and review existing callback-timing and server-compatibility evidence.
Record only verified results. Keep every acceptance status pending unless all formal gates pass.

The locked server test ran at controlled baseline `6b0160befc9191dbccd527bdd385b891782ddad8`.
It used Python 3.12.13 and pytest 8.4.2 in an external `uv` environment.
The focused test passed with one existing Starlette deprecation warning.
It confirmed the API and HTML status, content type, byte size, and SHA-256 values.

The callback review checked the exact source, the saved Release XCTest log, and the three manual PNG files.
The saved log records 65 passed tests and 0 failed tests.
`testPrivacyCoverUITest` and `testSceneDelegateTest` passed.
These tests inspect source text. They do not measure runtime callback timing.
No runtime trace or timestamped callback log was present in the reviewed evidence.

The controlled register now contains partial results for all nine P10 identifiers.
All nine identifiers and package P10 remain pending.
No commit, push, merge, or Production action occurred.
This bounded follow-on evidence goal is complete.

### MCX-15 P01 Repository Ancestry Review — 4 September 2026

Goal: Validate the controlled repository ancestry and approved file scope.
Record only verified P01 evidence. Keep all acceptance states pending.

The stated base `f0ca3f958334af7b6727742460ed060cf9c077aa` is an ancestor of protected candidate `cdc4f458bfd3ede385844b31eed117d3c06e854d`.
All 12 controlled first-parent links matched the runtime evidence plan.
The preparation commit changed exactly the six approved preparation files.
The protected-candidate-to-build route changed exactly the nine approved files.

The normalised sanitised-manifest SHA-256 matched the approved value.
The saved Release XCTest log records 65 tests and zero failures.
Its project-configuration and source-boundary tests passed.

The controlled P01 record is `sqe/ios/ACEClientApp/build/phase6-1/repository-ancestry-2026-09-04/evidence-record.md`.
The P01 result row now contains the verified commit, device, software, operator, date, result, artifact, and reviewer fields.
`IOS-BASE-001` and package P01 remain pending because formal approval gates did not pass in this review.
All 44 identifiers and all 10 packages remain pending.
No commit, push, merge, build, simulator run, or Production action occurred.
This bounded P01 goal is complete.

### MCX-15 P08 Negative Preview Input Review — 4 September 2026

Goal: Review the existing P08 negative Preview-input build evidence.
Do not run a new build. Keep all acceptance states pending.

The retained build 13 archive matched SHA-256 `a26cff0239eab0cbc2935dfaff86271969adca4405bf6d0f7694a6c6eaa3efdf`.
Its build record identifies exact commit `91818a476c7ddb81c48aba63c76b11cfbcb70df4`.

The missing-origin log ran `Validate Preview Inputs` once.
It returned the approved-HTTPS-origin error and one `BUILD FAILED` marker.
The invalid-origin log ran the same build phase once.
It returned the invalid-host error and one `BUILD FAILED` marker.
Neither log contains a line that starts with `SwiftCompile`.

The saved Release XCTest log records 65 tests and zero failures.
Its state-matrix test passed.
That test checks zero Keychain reads and repository calls for both configuration errors.

The execution logs do not echo the exact input values.
The saved build source identifies the removed variable and fictional invalid value.
The source definition is not independent execution evidence.
Full privacy review and formal approval remain pending.

The controlled P08 record is `sqe/ios/ACEClientApp/build/phase6-1/negative-preview-review-2026-09-04/evidence-record.md`.
Both P08 result rows now contain reviewed partial results.
Both identifiers and package P08 remain pending.
All 44 identifiers and all 10 packages remain pending.
No build, simulator run, commit, push, merge, or Production action occurred.
This bounded P08 goal is complete.

### MCX-15 P09 Simulator Screenshot Review — 4 September 2026

Goal: Review the existing P09 simulator screenshot and UI-test evidence.
Do not run a new build or simulator test. Keep all acceptance states pending.

The retained build 13 archive matched SHA-256 `a26cff0239eab0cbc2935dfaff86271969adca4405bf6d0f7694a6c6eaa3efdf`.
Its build record identifies exact commit `91818a476c7ddb81c48aba63c76b11cfbcb70df4`.

The capture log records ten planned PNG files across two devices and two appearances.
Four saved UI-test logs each record five tests and zero failures.
Each log records `TEST SUCCEEDED`.
The secure-password-field test passed in each configuration.

Codex inspected the four sign-in PNG files.
Each image shows the Username field, Password field, and Sign in control.
Both fields are empty. No username value or password value is visible.
The images do not prove that a populated username can appear.

The controlled P09 record is `sqe/ios/ACEClientApp/build/phase6-1/simulator-screenshot-review-2026-09-04/evidence-record.md`.
Both P09 result rows now contain reviewed partial results.
Both identifiers and package P09 remain pending.
All 44 identifiers and all 10 packages remain pending.
Complete result-bundle privacy review and formal approval remain pending.
No build, simulator run, commit, push, merge, or Production action occurred.
This bounded P09 goal is complete.

### MCX-15 P02 Returned-Attribute Review — 4 September 2026

Goal: Review the existing saved evidence for P02 and `IOS-AUTH-038`.
Do not run a build, simulator, signed-device, or network test.

The saved Release XCTest log records 65 tests and zero failures.
The Keychain validation test passed.
Four focused inventory and exact-read tests also passed.

The copied test source contains simulated checks for required inventory attributes.
It also checks exact-read result type, account, secret data, and read failures.
The application source applies the account validation function to both returned dictionaries.

The tests use Keychain test doubles.
They do not prove the attributes returned by an approved signed iPhone.
No positive approved signed access-group case exists in the saved tests.
The saved tests do not run every required invalid attribute case against the exact-read dictionary.

The controlled P02 record is `sqe/ios/ACEClientApp/build/phase6-1/returned-attribute-review-2026-09-04/evidence-record.md`.
The P02 result row now contains reviewed partial results.
`IOS-AUTH-038` and package P02 remain pending.
All 44 identifiers and all 10 packages remain pending.
No build, simulator run, signed-device test, network test, commit, push, merge, or Production action occurred.
This bounded P02 goal is complete.

### MCX-15 P03 Access-Group Review — 4 September 2026

Goal: Review the existing saved evidence for P03 and `IOS-AUTH-053`.
Do not run a build, simulator, signed-device, or network test.

The saved Release XCTest log records 65 tests and zero failures.
The Keychain validation test passed.
The command disabled code signing and used an iOS Simulator.

The saved test uses a wrong-type group and a string group without a configured expected value.
Both cases must enter the unsafe state.
The application source requires a present group to be a matching `CFString`.
The configuration source maps the expected group from the build setting.

The saved tests do not configure an expected access group.
They do not test a matching value or a configured mismatch.
The evidence does not contain approved signing inputs, effective entitlements, or a signed-iPhone result.

The controlled P03 record is `sqe/ios/ACEClientApp/build/phase6-1/access-group-review-2026-09-04/evidence-record.md`.
The P03 result row now contains reviewed partial results.
`IOS-AUTH-053` and package P03 remain pending.
All 44 identifiers and all 10 packages remain pending.
No build, simulator run, signed-device test, network test, commit, push, merge, or Production action occurred.
This bounded P03 goal is complete.

The Phase 6B2 architecture review remains a separate decision gate. Select one engine option before that implementation starts. Keep real client information and Production excluded. Do not merge, rewrite or adopt a new platform without separate approval.

### MCX-15 P04 Accessibility And Orientation Review — 4 September 2026

Goal: Review only the saved P04 accessibility and orientation evidence.
Record verified partial results and explicit gaps.
Keep all acceptance states pending.

The retained build 13 archive matched the recorded SHA-256.
Its build record identifies exact commit `91818a476c7ddb81c48aba63c76b11cfbcb70df4`.

The saved Release XCTest log records 65 tests and zero failures.
Its accessibility-label and VoiceOver-order source checks passed.
These checks inspect source text and do not perform a VoiceOver journey.

Four saved UI suites each record five passed tests and zero failures.
This gives 20 UI test executions and zero failures.
The runs cover both named simulators in light and dark labelled configurations.

Each suite passed the controlled-scenarios accessibility-audit test.
That test audits 19 controlled scenarios.
Each suite also passed the release orientation hook.
The hook checks only the fictional-pilot banner after landscape and portrait changes.

Codex reviewed the ten saved PNG files.
They match their light and dark labels and visibly use large text.
The controlled accessibility-settings log contains zero bytes.
It does not prove Dynamic Type, Bold Text, Reduce Motion, or Increase Contrast settings.

The other screens and states still need the required orientation matrix.
Runtime VoiceOver order and formal approval remain pending.
Complete result-bundle privacy review also remains pending.

The controlled P04 record is `sqe/ios/ACEClientApp/build/phase6-1/accessibility-orientation-review-2026-09-04/evidence-record.md`.
All 16 P04 result rows now contain reviewed partial results.
All 16 identifiers and package P04 remain pending.
All 44 identifiers and all 10 packages remain pending.

No new build, simulator, signed-device, network, or test run occurred.
No code or architecture changed.
No file was staged.
No commit, push, merge, deployment, or Production action occurred.
The Phase 6B2 architecture review remains a separate decision gate.
