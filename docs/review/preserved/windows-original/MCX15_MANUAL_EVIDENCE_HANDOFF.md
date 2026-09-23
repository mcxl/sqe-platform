# MCX-15 Manual Evidence Handoff

Date: 3 September 2026. Updated: 4 September 2026.

This is a local preparation record. It does not replace the controlled register or grant approval.
All 44 identifiers and all 10 packages remain pending.
The 4 September update adds the completed manual simulator capture.

## Goal And Completion Criteria

Prepare the next manual evidence step from the saved successful build.
Map every pending identifier to its required check, available evidence, missing evidence, and approval dependency.
Define a small app-switcher capture pilot for an approved Mac operator.
Update `DEV_STATE.md` with the result and next action.

Preparation is complete only when these checks pass:

- The mapping contains exactly the register's 44 identifiers, once each, in the correct 10 packages.
- Every package has a source procedure, evidence reference, remaining check, and approval dependency.
- Saved artifact paths exist. The archive hash matches the recorded hash.
- The controlled register keeps all package and identifier states pending.
- A later verified update can add partial result fields without granting acceptance.
- The final document and dev-state changes pass a full read and mechanical checks.

This goal excludes code changes, new tools, new builds, signing, network tests, and new device captures.
It also excludes formal acceptance, commits, pushes, merges, and Production actions.
The user requested preparation and completion in the current session. This is not an unattended delivery authority.

## Source And Build Identity

The source directory is `C:/tmp/sqe-mcx-15-phase6-1-simulator-probe-v2/sqe/ios/ACEClientApp/`.
The source worktree started clean at the build commit below.
It now contains the controlled partial registration described in this handoff.

Use these existing controlled sources:

- [Phase6_1EvidenceRegister.json](C:/tmp/sqe-mcx-15-phase6-1-simulator-probe-v2/sqe/ios/ACEClientApp/Phase6_1EvidenceRegister.json): package membership, states, and result fields.
- [Phase6_1EvidenceRegister.md](C:/tmp/sqe-mcx-15-phase6-1-simulator-probe-v2/sqe/ios/ACEClientApp/Phase6_1EvidenceRegister.md): approvals, data limits, and acceptance rules.
- [RuntimeEvidencePlan.json](C:/tmp/sqe-mcx-15-phase6-1-simulator-probe-v2/sqe/ios/ACEClientApp/RuntimeEvidencePlan.json): exact procedures and expected results.
- [RuntimeEvidencePlan.md](C:/tmp/sqe-mcx-15-phase6-1-simulator-probe-v2/sqe/ios/ACEClientApp/RuntimeEvidencePlan.md): manual journeys and simulator limits.

The controlled documents describe preparation before the latest build. This handoff records later observations.
Only verified evidence can enter result fields. Keep all pending states until the formal gates pass.

| Reference | Value |
|---|---|
| Protected Candidate | `cdc4f458bfd3ede385844b31eed117d3c06e854d` |
| Stated Base | `f0ca3f958334af7b6727742460ed060cf9c077aa` |
| Evidence Preparation | `5f88563248650f263b4b0fc6c333731868114a25` |
| Exact Build Commit | `91818a476c7ddb81c48aba63c76b11cfbcb70df4` |
| Build Parent | `921d38e096ad4214f44f0f9c32cdad96ab1a49cf` |
| Build | `6a992d72df4f3e11bdebb36c` |
| Route | `screenshot-absolute-path-correction-child` |
| Xcode | 26.4.1, build `17E202` |
| Result Runtime | iOS Simulator 26.4.1 |

The saved build, parent, preparation, protected-candidate, and route records match this table.
A read-only Git check confirms that the protected candidate is an ancestor of the build commit.
This check does not complete the approved sanitised-manifest comparison.

## Saved Evidence Index

Archive: `ace-iphone-fictional-test_13_artifacts.zip`.
Size: 2,253,940 bytes.
SHA-256: `A26CFF0239EAB0CBC2935DFAFF86271969ADCA4405BF6D0F7694A6C6EAA3EFDF`.

The archive is in `C:/tmp/mcx15-artifact-review-6ab5cfa9570848c3807070a12ad9e278/`.
The extracted artifact root is that directory plus `extracted/sqe/ios/ACEClientApp/build/phase6-1/`.
Every path in the following table is relative to that artifact root.

The Mac photos show the user-selected extraction directory as `Downloads/sqe 3/ios/ACEClientApp/build/phase6-1/`.
Do not use the older `sqe 2` result bundles for this build.

| Evidence | Saved Paths | Verified Use And Limit |
|---|---|---|
| E01 | `logs/ancestry-route.txt`, `logs/build-commit.txt`, `logs/build-parent.txt`, `logs/preparation-commit.txt`, `logs/preparation-parent.txt`, `logs/protected-candidate.txt`, `logs/preparation-diff-files.txt` | The saved commit records supplied the source values for the local P01 review. Formal approval remains pending. |
| E02 | `results/iphone-se-release-xctest.xcresult`; four UI bundles listed below; matching files in `logs/` | Five Xcode summaries passed. Summary counts do not establish every manual state or every attachment's contents. |
| E03 | `logs/negative-preview-origin-missing.log`, `logs/negative-preview-origin-invalid.log` | Both logs contain `BUILD FAILED`. Their error messages reject a missing HTTPS origin and an invalid host. No line starts with `SwiftCompile `. E11 records the focused review. |
| E04 | `screenshots/` | Ten planned PNG captures exist. Two additional path-pilot PNGs exist in the artifact tree. Prior visual review found no visible credentials or real client data. Lower release fields and app-switcher timing remain unproved. |
| E05 | `logs/artifact-privacy-scan.log`, `logs/manual-screenshot-and-result-bundle-review-gate.txt`, all saved logs and result bundles | The review gate remains pending. A text scan cannot complete image or result-bundle review. |
| E06 | `logs/manual-privacy-cover-gate.txt`; `build/phase6-1/manual-app-switcher-2026-09-04/` | The gate file defines the manual check. The controlled folder contains three native PNG files and the review manifest. The files support visible states only. |
| E07 | `logs/controlled-accessibility-settings.log` | This file has zero bytes. Its presence does not prove any setting was applied. Other evidence needs review before settings coverage can be claimed. |
| E08 | `build/phase6-1/callback-evidence-review-2026-09-04/` | The folder contains the saved Release XCTest log and callback review record. Static source checks passed. No runtime timing trace exists. |
| E09 | `build/phase6-1/server-compatibility-2026-09-04/` | The locked focused server test passed at the exact controlled server baseline. Formal approval remains pending. |
| E10 | `build/phase6-1/repository-ancestry-2026-09-04/` | Local mechanical ancestry, parent-chain, file-scope, and normalised manifest checks passed. Formal approval remains pending. |
| E11 | `build/phase6-1/negative-preview-review-2026-09-04/` | The two copied negative-build logs and provenance files match the source artifact. The review record states the observed results and limits. |
| E12 | `build/phase6-1/simulator-screenshot-review-2026-09-04/` | The folder contains four reviewed sign-in PNG files, four UI-test logs, the capture log, provenance files, and the P09 review record. Both P09 results remain partial. |
| E13 | `build/phase6-1/returned-attribute-review-2026-09-04/` | The folder contains the saved Release XCTest log, three copied Swift source files, provenance files, and the P02 review record. The P02 result remains partial. |
| E14 | `build/phase6-1/access-group-review-2026-09-04/` | The folder contains the saved unsigned Release XCTest log, four copied source files, provenance files, and the P03 review record. The P03 result remains partial. |

| Result Bundle In `results/` | Passed | Failed |
|---|---|---|
| `iphone-se-release-xctest.xcresult` | 65 | 0 |
| `iphone-se-ui-audits-light.xcresult` | 5 | 0 |
| `iphone-se-ui-audits-dark.xcresult` | 5 | 0 |
| `iphone-16-pro-max-ui-audits-light.xcresult` | 5 | 0 |
| `iphone-16-pro-max-ui-audits-dark.xcresult` | 5 | 0 |

The 20 UI executions repeat five tests in four configurations. They are not 20 different tests.
All four UI summaries show 54 build warnings. The warnings still need separate review.
The latest screenshot review does not replace inspection of all logs and result-bundle attachments.

The extracted package contains 377 files, five result bundles, and 12 PNG files.
It contains no `.app` directory. A saved `.xcresult` is a test record, not a running application.
The next operator must confirm a live exact-build app on the approved Mac before capture.
Do not start a new build to supply that app without the required approval.

## Required Package Checks

The ten package descriptions below follow `RuntimeEvidencePlan.json` entries in their existing order.
The identifier table links each item to that package's full check. It does not invent separate acceptance rules.

### P01 — Repository Ancestry

Review E01 against the protected candidate, preparation commit, exact build commit, and stated base.
Compare the approved sanitised manifest. Record the approved ancestry and manifest result.
Available: E10 records the completed local mechanical checks and independent technical review.
Missing: evidence-host, Security, Pocock, and any required human organisation approval.
Dependency: approved repository evidence and the approved manifest record must be available.

### P02 — Signed Returned Attributes

Run the approved inventory and exact-read attribute matrix on the approved signed iPhone.
Include every required attribute rule and a valid signed access group.
Each case must pass or enter deletion-only recovery as specified in the approved matrix.
E13 records the completed review of saved guard evidence.
Available: the saved 65-test suite passed. The Keychain validation test and four focused guard tests passed. Source review found partial inventory and exact-read guards.
Missing: a positive approved signed access-group case, the complete exact-read attribute matrix, signed-device results, and formal approval.
Dependency: the signing, device, access-group, and applicable Security approvals must exist first.

### P03 — Signed Access Group

Store and load with the approved signed access group. Then check a mismatched access group.
The approved group must load. The mismatched group must fail closed.
E14 records the completed review of saved guard and source-wiring evidence.
Available: the unsigned 65-test suite passed. A wrong-type group and an unconfigured string group entered the unsafe state. Source wiring requires a matching `CFString`.
Missing: configured matching and mismatch tests, approved signing inputs, effective entitlements, signed-device results, and formal approval.
Dependency: approved signing, device, and access group. Do not create or change an access group here.

### P04 — Simulator Accessibility And Orientation

Map E02 to the recorded accessibility audits and release orientation hook on both devices in both appearances.
Review the exact states and settings represented by those results. E07 supplies no settings proof.
Complete the remaining orientation matrix for every other listed screen and state on both simulators.
Complete the required Dynamic Type, Bold Text, Reduce Motion, and Increase Contrast checks.
Use the approved state matrix. Do not replace missing state definitions with guesses.
Available: four passing UI bundles and selected large-text PNGs.
Missing: complete settings, state, and manual orientation records with independent review.
Dependency: approved macOS host, operator, iOS runtime, and complete state matrix.

### P05 — Physical Device Journeys

Use an approved iPhone 15 Pro or later with iOS 26 and fictional data.
Complete locked-device, VoiceOver, and app-switcher journeys.
Check that Keychain access is unavailable while locked. Check the required VoiceOver order.
Check that the app-switcher image contains no release information.
Available: simulator evidence does not satisfy these physical-device checks.
Missing: all required physical journey records.
Dependency: signing, device, and Security approvals. Never capture Keychain contents or credentials.

### P06 — Evidence Privacy Review

Inspect all approved logs, screenshots, and result-bundle content. Use E04 and E05 as the starting index.
Check visible user names, passwords, Authorization values, and Keychain secrets.
Every user name must be redacted. The other prohibited values must be absent.
Preserve controlled originals. Keep any permitted redacted review copies separate from them.
Available: prior visual review of all 12 PNGs and a limited review of Xcode summary photos.
Missing: full approved review of every log and result-bundle attachment.
Dependency: Pocock approval and an approved independent reviewer. Stop if prohibited data appears.

### P07 — Network Rejection

On the approved iPhone SE simulator, use only the approved Preview endpoint and certificate.
Run the controlled trust and hostname failure cases. Do not attempt a bypass.
Check the secure-connection message. Check that rejected endpoints receive no request or authorization value.
Available: passing controlled error-state UI tests do not prove real endpoint rejection.
Missing: approved network-case observations.
Dependency: ACE operations and Security must approve the endpoint and certificate first.

### P08 — Negative Preview-Input Builds

Review E03 first. The missing-input and invalid-input logs already exist in build 13.
Confirm the supplied values were fictional. Confirm `Validate Preview Inputs` caused each rejection before compilation completed.
Keep the full approved evidence reference and result for each case.
Available: E11 records both failure markers, origin-rejection messages, hashes, provenance, and completed partial result fields.
Missing: independent execution output for the exact input values, complete privacy review, and formal approval.
Dependency: approved macOS Xcode build validation and independent review.
Do not rerun these builds merely because this handoff leaves their acceptance pending.

### P09 — Normal Screenshots

The source procedure requires the approved simulator `make ui-test` check and normal fictional screenshots.
E12 records the completed review of existing E02 and E04 evidence.
Confirm normal screenshots remain available. The sign-in image must show no password.
The saved sign-in fields are empty. Record that limit instead of claiming a populated-field check.
Review all release fields. Existing still images do not prove lower-field visibility or scrolling.
Available: ten planned screenshots, four UI suites with five passes each, and four reviewed sign-in images. The images show the permitted fields and no password.
Missing: evidence of a populated visible username, complete result-bundle privacy review, and formal approval.
Dependency: approved evidence review and formal acceptance. Obtain any additional image only within an approved scope.

### P10 — Privacy Cover And Separate Server Record

On the approved iPhone 16 Pro Max simulator, verify active and inactive callbacks and cover timing.
Active SwiftUI content must remain visible. The cover must install before inactive return.
The cover must remove after activation. A still image alone does not prove callback order.
Review the separate server-owned compatibility record without changing it.
Available: E06 contains the visible-state evidence. E08 records the static callback review. E09 records the passing server test.
Missing: exact runtime callback-timing evidence and formal approval.
The Codex technical review does not replace a human review when governance requires one.
Dependency: Security and Pocock approval, the approved Mac and operator, and the server-owned record.
The completed simulator pilot covers only part of P10. It does not complete P05. E09 records the separate server review.

## Identifier Mapping

All rows remain pending. Each row inherits its package's required check, missing evidence, and approval dependency above.
The evidence column identifies review inputs only. `None` means this handoff supplies no direct runtime evidence.

| Package | Identifier | Evidence To Review |
|---|---|---|
| P01 | IOS-BASE-001 | E01, E10 |
| P02 | IOS-AUTH-038 | E13 |
| P03 | IOS-AUTH-053 | E14 |
| P04 | IOS-ACC-001 | E02, E04, E07 |
| P04 | IOS-ACC-002 | E02, E04, E07 |
| P04 | IOS-ACC-003 | E02, E04, E07 |
| P04 | IOS-ACC-004 | E02, E04, E07 |
| P04 | IOS-ACC-005 | E02, E04, E07 |
| P04 | IOS-ACC-006 | E02, E04, E07 |
| P04 | IOS-ACC-007 | E02, E04, E07 |
| P04 | IOS-ACC-008 | E02, E04, E07 |
| P04 | IOS-ACC-010 | E02, E04, E07 |
| P04 | IOS-ACC-011 | E02, E04, E07 |
| P04 | IOS-ACC-012 | E02, E04, E07 |
| P04 | IOS-ACC-013 | E02, E04, E07 |
| P04 | IOS-ACC-014 | E02, E04, E07 |
| P04 | IOS-ACC-015 | E02, E04, E07 |
| P04 | IOS-ACC-018 | E02, E04, E07 |
| P04 | IOS-ACC-019 | E02, E04, E07 |
| P05 | IOS-AUTH-023 | None |
| P05 | IOS-ACC-009 | None |
| P05 | IOS-ACC-016 | None |
| P05 | IOS-ACC-017 | None |
| P05 | IOS-SHOT-007 | None |
| P06 | IOS-AUTH-036 | E04, E05 |
| P06 | IOS-AUTH-037 | E04, E05 |
| P07 | IOS-NET-007 | None |
| P07 | IOS-NET-008 | None |
| P07 | IOS-NET-028 | None |
| P07 | IOS-STATE-017 | None |
| P07 | IOS-STATE-018 | None |
| P08 | IOS-NET-015 | E03, E11 |
| P08 | IOS-NET-016 | E03, E11 |
| P09 | IOS-SHOT-001 | E02, E04, E12 |
| P09 | IOS-SHOT-010 | E02, E04, E12 |
| P10 | IOS-STATE-009 | E06 |
| P10 | IOS-STATE-010 | E06 |
| P10 | IOS-SHOT-003 | E06 |
| P10 | IOS-SHOT-004 | E08 |
| P10 | IOS-SHOT-005 | E08 |
| P10 | IOS-SHOT-006 | E08 |
| P10 | IOS-SHOT-008 | E08 |
| P10 | IOS-SHOT-009 | E08 |
| P10 | IOS-BOUND-006 | E09 |

## Completed Pilot — Actual App-Switcher Cover

Alan Richardson completed the bounded simulator capture on 4 September 2026.
The run used an iPhone 16 Pro Max simulator on a MacBook Pro.
The simulator UUID was `6D2FD18F-22B3-4403-ADFA-A5FB76F3C874`.
Xcode was 26.4.1. The simulator runtime was iOS 26.4.1.

The operator used a local Debug simulator build.
Its source commit was `91818a476c7ddb81c48aba63c76b11cfbcb70df4`.
The bundle identifier was `com.example.aceclientapp`.
The app used only the approved fictional release scenario.

The observed sequence was:

1. The active app showed the fictional release information.
2. The app-switcher card showed the privacy cover.
3. The cover showed only `ACE Client` and `FICTIONAL PILOT — CONTROLLED`.
4. No release information was visible on the app-switcher card.
5. The fictional release information returned after the operator selected the app card.

The original simulator PNG files are in this folder on the operator's Mac:
`LOCAL_HOME/Desktop/MCX15-privacy-cover-2026-09-04`.

| Original PNG | SHA-256 |
|---|---|
| `01-active.png` | `05751860bdd140ba5b589b3dad60db9e0f1e1d436646a237d55996796efb2661` |
| `02-app-switcher-cover.png` | `010d82c29fdb662080270073373f2fe67e90d018178930085f293d84032a7b57` |
| `03-restored-active.png` | `a47e9853892ffb43b10e0987d6cc2d2ea8683b420d1c913c62930d6c9d8d3b49` |

The `shasum -a 256` command completed for all three files.
The supplied photos show successful simulator writes for the three paths.

This result confirms the visible state sequence.
It does not prove exact callback order.
The operator did not add instrumentation.

A fresh read-only Codex technical review returned `ship`.
It confirmed that the folder contains exactly three PNG files.
It confirmed each file's dimensions, size, and SHA-256 value.
It confirmed the active, covered, and restored visible states.
It found no visible credentials, personal information, or real client data.
The blurred app-switcher background contained no readable data.

Alan Richardson designated Codex as the independent technical reviewer on 4 September 2026.
Reviewer: `Codex — independent technical review only`.
This review is not a human or organisational signature.
Controlled registration is complete for all nine P10 rows.
The server compatibility test passed. Runtime callback timing and formal approval remain pending.

### Historical Approved Procedure

The approved estimate was 15–20 minutes, with a 30-minute hard limit. A later 15-minute recovery completed the named captures after the first folder-path fault.

High-cost commands were excluded. The scope permitted no package installation, external scan, or network test.

Before starting, the procedure required the operator, reviewer, host, simulator UUID, app provenance, and applicable approvals.
Confirm the exact-build app is already available. The downloaded result archive cannot supply that app.
If the app is absent, stop and prepare a separate native-build scope. Do not use an unrelated app installation.

After approval, the operator follows this sequence:

1. Open the exact-build app with the approved fictional release state.
2. Confirm active content is visible. Capture the active view without credentials or personal information.
3. Open the simulator app switcher. Capture the app card with its privacy cover.
4. Confirm the app card shows no release information.
5. Return to the app. Capture the active view after the cover disappears.
6. Preserve approved timing or callback evidence for the inactive and active transitions.
7. If existing evidence cannot prove callback order, record that gap. Do not add instrumentation in this pilot.
8. Record the actual observations, exact paths, device, software, operator, and capture date.
9. Give the controlled evidence to the approved reviewer. Keep every identifier pending until formal acceptance.

Keep the active, app-switcher, and restored-active images together with the transition record.
Use the controlled artifact tree specified by the existing register. Do not overwrite the downloaded build 13 evidence.
Stop for the hard limit, real data, missing approval, wrong app provenance, or scope expansion.
Stop after two failed corrective attempts for one fault. This pilot does not authorise a code correction.

Pilot acceptance still requires the required transition evidence, complete metadata, and formal review.
The three screenshots alone cannot complete P10. E09 separately records the server compatibility result.

## Operator And Reviewer Handoff

The operator records the protected candidate, preparation commit, and exact build commit in the result's commit field.
The existing fields are `commit`, `device`, `software`, `operator`, `date`, `result`, `artifact`, and `reviewer`.
Record observations, not intended commands. Reference the applicable approval records without inventing approvals.
The reviewer checks the artifact, data limits, redaction, device, software, date, and all required fields.
Only then can the controlled acceptance process change a pending item.

This handoff contains the completed operator capture result.
It contains no human reviewer signature or formal acceptance.
The immediate next action is approved runtime callback-timing evidence and formal review.
Keep every identifier pending until the formal acceptance gates pass.

## Preparation Verification

The preparation goal is complete. The primary session read the complete handoff and checked the dev-state changes.
Mechanical checks confirmed 44 unique identifiers, their correct 10 packages, and matching runtime-plan membership.
All referenced artifact paths and five result bundles exist. The recorded archive size and SHA-256 match.
Markdown tables, whitespace, and local source links passed checks.
The evidence worktree contains only the intended register changes and controlled evidence folders.
All 44 identifier states and 10 package states remain pending.
The P01, P02, and P03 rows, both P08 rows, both P09 rows, and all nine P10 rows contain reviewed partial results. All other result fields remain blank.
The later 4 September pilot added manual runtime evidence.
It did not grant formal acceptance.
