# Phase 6.1 Evidence Register

This public G0 register is not release evidence. The manual preflight checks public
record structure and current repository paths only. It does not run, collect, publish,
or accept client evidence. Pending records fail closed as not-release-evidence.

This register controls MCX-15 Phase 6.1 evidence work.

- Protected source candidate: `cdc4f458bfd3ede385844b31eed117d3c06e854d`.
- Base: `f0ca3f958334af7b6727742460ed060cf9c077aa`.
- Controlled workflow: `ace-ios-evidence-preflight-manual`.
- The workflow has no automatic trigger. An approved operator starts it manually.
- The workflow accepts the evidence-preparation commit, one direct correction child, one UI-test platform correction child of `b0eaaa74fa45f60e1ccbda6c3b4ec6faa5e07982`, one UI-test product-name correction child of `ffa73729ab1c45e947ec13d6db00a7b709143b3a`, one app-plist correction child of `d9aacced1d451c64649a08ac3f2012df43b7f27d`, one debug-fixture correction child of `e90efc6123537633dcc8fcb7c27b5bdf2627c3d3`, one copy-control query correction child of `f0cb10b68cce137826c44327f9f433e6b60d3361`, one app launch-screen correction child of `4650a614032d227054bf7f143f409eb7e66e0a38`, or one screenshot-path pilot child of `ddace288d47766172aa8a6fa6b3e5a3e500e0bc6`.
- The workflow also accepts one UI readiness correction child of `ff0556229f17d3ee05487391c9c4e26da346fea4`.
- The workflow also accepts one screenshot absolute-path correction child of `921d38e096ad4214f44f0f9c32cdad96ab1a49cf`.
- The evidence-preparation commit must have the protected source candidate as its first parent.
- The simulator-destination correction `b36f89c7fee9e37f1014933408fea78bd9eb80a1` must have the evidence-preparation commit as its first parent.
- The UI-test platform correction `b0eaaa74fa45f60e1ccbda6c3b4ec6faa5e07982` must have the simulator-destination correction as its first parent.
- The controlled gate correction `ffa73729ab1c45e947ec13d6db00a7b709143b3a` must have the UI-test platform correction as its first parent.
- The UI-test product-name correction `d9aacced1d451c64649a08ac3f2012df43b7f27d` must have the controlled gate correction as its first parent.
- The app-plist correction `e90efc6123537633dcc8fcb7c27b5bdf2627c3d3` must have the UI-test product-name correction as its first parent.
- The debug-fixture correction `f0cb10b68cce137826c44327f9f433e6b60d3361` must have the app-plist correction as its first parent.
- The copy-control query correction `4650a614032d227054bf7f143f409eb7e66e0a38` must have the debug-fixture correction as its first parent.
- The screenshot-path pilot parent `ddace288d47766172aa8a6fa6b3e5a3e500e0bc6` must have the copy-control query correction as its first parent.
- The UI readiness correction parent `ff0556229f17d3ee05487391c9c4e26da346fea4` must have the screenshot-path pilot parent as its first parent.
- The screenshot absolute-path correction parent `921d38e096ad4214f44f0f9c32cdad96ab1a49cf` must have the UI readiness correction parent as its first parent.
- The evidence-preparation and direct correction routes must contain only the six Phase 6.1 preparation files.
- The UI-test platform and product-name correction children must contain exactly the six preparation files and `ios/ACEClientApp/ACEClientApp.xcodeproj/project.pbxproj`.
- The app-plist correction child must contain exactly these eight files: `codemagic.yaml`, `ios/ACEClientApp/RuntimeEvidencePlan.md`, `ios/ACEClientApp/RuntimeEvidencePlan.json`, `ios/ACEClientApp/evidence-matrix-audit.md`, `ios/ACEClientApp/Phase6_1EvidenceRegister.md`, `ios/ACEClientApp/Phase6_1EvidenceRegister.json`, `ios/ACEClientApp/ACEClientApp.xcodeproj/project.pbxproj`, and `ios/ACEClientApp/ACEClientApp/Info.plist`.
- The debug-fixture correction child must contain the same eight files.
- The copy-control query correction child must contain those eight files and `ios/ACEClientApp/ACEClientAppUITests/ACEClientAppUITests.swift`.
- The app launch-screen correction child must contain the same nine files.
- The screenshot-path pilot child must contain the same nine files.
- The UI readiness correction child must contain the same nine files.
- The screenshot absolute-path correction child must contain the same nine files.
- The app launch-screen correction is a pending hypothesis. It does not prove a clipping cure.
- The published screenshot-path pilot shows absolute screenshot destinations succeed. The full corrected native capture remains pending.
- The UI readiness correction published 20 UI tests and 0 failures at build `6a991338f7568a30a248dc76`. All 44 evidence identifiers remain pending.
- Every package and identifier is pending.

## Approval Gates

Do not run the workflow until the evidence host, Security, and Pocock approve it.
Run only evidence-preparation commit `5f88563248650f263b4b0fc6c333731868114a25`, one direct correction child, one UI-test platform correction child with first parent `b0eaaa74fa45f60e1ccbda6c3b4ec6faa5e07982`, one UI-test product-name correction child with first parent `ffa73729ab1c45e947ec13d6db00a7b709143b3a`, one app-plist correction child with first parent `d9aacced1d451c64649a08ac3f2012df43b7f27d`, one debug-fixture correction child with first parent `e90efc6123537633dcc8fcb7c27b5bdf2627c3d3`, one copy-control query correction child with first parent `f0cb10b68cce137826c44327f9f433e6b60d3361`, one app launch-screen correction child with first parent `4650a614032d227054bf7f143f409eb7e66e0a38`, or one screenshot-path pilot child with first parent `ddace288d47766172aa8a6fa6b3e5a3e500e0bc6`. The evidence-preparation commit first parent must be protected candidate `cdc4f458bfd3ede385844b31eed117d3c06e854d`. The simulator-destination correction `b36f89c7fee9e37f1014933408fea78bd9eb80a1` must have the evidence-preparation commit as its first parent. The UI-test platform correction `b0eaaa74fa45f60e1ccbda6c3b4ec6faa5e07982` must have the simulator-destination correction as its first parent. The controlled gate correction `ffa73729ab1c45e947ec13d6db00a7b709143b3a` must have the UI-test platform correction as its first parent. The UI-test product-name correction `d9aacced1d451c64649a08ac3f2012df43b7f27d` must have the controlled gate correction as its first parent. The app-plist correction `e90efc6123537633dcc8fcb7c27b5bdf2627c3d3` must have the UI-test product-name correction as its first parent. The debug-fixture correction `f0cb10b68cce137826c44327f9f433e6b60d3361` must have the app-plist correction as its first parent. The copy-control query correction `4650a614032d227054bf7f143f409eb7e66e0a38` must have the debug-fixture correction as its first parent. The screenshot-path pilot parent `ddace288d47766172aa8a6fa6b3e5a3e500e0bc6` must have the copy-control query correction as its first parent. The evidence-preparation and direct correction routes must contain exactly the six approved preparation files. The UI-test platform and product-name correction children must contain those six files and `ios/ACEClientApp/ACEClientApp.xcodeproj/project.pbxproj`. The app-plist and debug-fixture correction children must contain exactly these eight files: `codemagic.yaml`, `ios/ACEClientApp/RuntimeEvidencePlan.md`, `ios/ACEClientApp/RuntimeEvidencePlan.json`, `ios/ACEClientApp/evidence-matrix-audit.md`, `ios/ACEClientApp/Phase6_1EvidenceRegister.md`, `ios/ACEClientApp/Phase6_1EvidenceRegister.json`, `ios/ACEClientApp/ACEClientApp.xcodeproj/project.pbxproj`, and `ios/ACEClientApp/ACEClientApp/Info.plist`. The copy-control query, app launch-screen, and screenshot-path pilot children must contain those eight files and `ios/ACEClientApp/ACEClientAppUITests/ACEClientAppUITests.swift`. This does not change the protected candidate.
The workflow also accepts one UI readiness correction child with first parent `ff0556229f17d3ee05487391c9c4e26da346fea4`. This parent must have `ddace288d47766172aa8a6fa6b3e5a3e500e0bc6` as its first parent. It must contain the same nine files. The UI readiness correction published 20 UI tests and 0 failures at build `6a991338f7568a30a248dc76`. All 44 evidence identifiers remain pending.
The workflow also accepts one screenshot absolute-path correction child with first parent `921d38e096ad4214f44f0f9c32cdad96ab1a49cf`. This parent must have `ff0556229f17d3ee05487391c9c4e26da346fea4` as its first parent. It must contain the same nine files. The published screenshot-path pilot shows absolute screenshot destinations succeed. The full corrected native capture remains pending.
Use Xcode 26.4.1. Use iPhone SE (3rd generation) and iPhone 16 Pro Max in an iOS 26 runtime. The workflow resolves one exact device type and a canonical simulator UUID before it accepts a target. Existing and created devices must have that type identifier. A same-name wrong-type device is ignored. An invalid matching UUID fails the workflow. It selects one highest available iOS 26.x runtime before target resolution. It ignores exact targets in older runtimes. It accepts one exact available target only in the selected runtime. It fails when the selected runtime has more than one. Otherwise, it creates the target once from the exact device type in the selected runtime. It then polls unfiltered `simctl list devices -j` snapshots for no more than 30 seconds at one-second intervals. Each poll subprocess gets only the remaining verification time. A timed-out poll keeps its partial snapshot and final verification log, then fails closed. It finds the returned UUID across all runtime records. It accepts one record only with the selected runtime key, exact target name, exact device type, and `isAvailable` true. Missing or temporarily unavailable records can continue until the deadline. Duplicate UUIDs and wrong runtime, name, or device type records fail immediately. It fails on an absent or ambiguous device type, an invalid matching UUID, no available runtime, invalid or ambiguous highest-version selection, multiple exact available targets in the selected runtime, a creation failure, a poll timeout, an identity failure, a missing record at the deadline, an unavailable record at the deadline, or an ambiguous exact resolution. It does not create the target again.
The automated UI tests run accessibility audits and the release orientation hook in light and dark appearance.
An approved operator must run the pending orientation matrix for every other listed state on both simulators.
Use a signed physical device only after its signing and access-group approvals.
Use an approved Preview endpoint and certificate for network work.
Keep the server compatibility record separate and unchanged.

## Data And Privacy Controls

Use fictional data only. Do not record a password, an Authorization value, a Keychain secret, token, or real user name.
The workflow scans controlled text files and prints only a matching file name. It fails when it finds prohibited text.
Review all logs, result bundles, and screenshots before release. Redact visible user names and remove prohibited data.
An approved reviewer must inspect PNG screenshots and XCTest result bundles. The text scan cannot validate images or all result-bundle content.
Do not use a command definition as evidence. Do not change a pending state automatically.

## Artifact Controls

Store logs, XCTest result bundles, and fictional PNG files below `ios/ACEClientApp/build/phase6-1/`.
Keep the original files. Record the artifact path and review it before evidence acceptance.
Keep simulator device-type, runtime, pre-creation device, creation, poll snapshot, final verification, and resolution logs in the same controlled artifact tree. These logs prepare evidence only.
The privacy-view screenshots are controlled fictional-view captures. They do not replace the approved manual app-switcher privacy-cover capture.
Capture fictional release views in light and dark appearance. Terminate the app before each fictional scenario launch.

## Evidence Acceptance Rules

An approved operator records each result. The commit field records the protected source candidate.
It records evidence-preparation commit `5f88563248650f263b4b0fc6c333731868114a25`.
For a correction child, it records the exact build commit.
An independent reviewer checks the artifact, data limits, redaction, device, software, and date.
The reviewer accepts an item only after all result fields are complete and the relevant approval gates apply.
Until then, keep the package and identifier status as `pending`.

## Pending Mapping And Result Fields

Each row has blank result fields. The machine-readable copy is `Phase6_1EvidenceRegister.json`.

| Package | Identifier | Status | Commit | Device | Software | Operator | Date | Result | Artifact | Reviewer |
|---|---|---|---|---|---|---|---|---|---|---|
| P01 | IOS-BASE-001 | pending |  |  |  |  |  |  |  |  |
| P02 | IOS-AUTH-038 | pending |  |  |  |  |  |  |  |  |
| P03 | IOS-AUTH-053 | pending |  |  |  |  |  |  |  |  |
| P04 | IOS-ACC-001 | pending |  |  |  |  |  |  |  |  |
| P04 | IOS-ACC-002 | pending |  |  |  |  |  |  |  |  |
| P04 | IOS-ACC-003 | pending |  |  |  |  |  |  |  |  |
| P04 | IOS-ACC-004 | pending |  |  |  |  |  |  |  |  |
| P04 | IOS-ACC-005 | pending |  |  |  |  |  |  |  |  |
| P04 | IOS-ACC-006 | pending |  |  |  |  |  |  |  |  |
| P04 | IOS-ACC-007 | pending |  |  |  |  |  |  |  |  |
| P04 | IOS-ACC-008 | pending |  |  |  |  |  |  |  |  |
| P04 | IOS-ACC-010 | pending |  |  |  |  |  |  |  |  |
| P04 | IOS-ACC-011 | pending |  |  |  |  |  |  |  |  |
| P04 | IOS-ACC-012 | pending |  |  |  |  |  |  |  |  |
| P04 | IOS-ACC-013 | pending |  |  |  |  |  |  |  |  |
| P04 | IOS-ACC-014 | pending |  |  |  |  |  |  |  |  |
| P04 | IOS-ACC-015 | pending |  |  |  |  |  |  |  |  |
| P04 | IOS-ACC-018 | pending |  |  |  |  |  |  |  |  |
| P04 | IOS-ACC-019 | pending |  |  |  |  |  |  |  |  |
| P05 | IOS-AUTH-023 | pending |  |  |  |  |  |  |  |  |
| P05 | IOS-ACC-009 | pending |  |  |  |  |  |  |  |  |
| P05 | IOS-ACC-016 | pending |  |  |  |  |  |  |  |  |
| P05 | IOS-ACC-017 | pending |  |  |  |  |  |  |  |  |
| P05 | IOS-SHOT-007 | pending |  |  |  |  |  |  |  |  |
| P06 | IOS-AUTH-036 | pending |  |  |  |  |  |  |  |  |
| P06 | IOS-AUTH-037 | pending |  |  |  |  |  |  |  |  |
| P07 | IOS-NET-007 | pending |  |  |  |  |  |  |  |  |
| P07 | IOS-NET-008 | pending |  |  |  |  |  |  |  |  |
| P07 | IOS-NET-028 | pending |  |  |  |  |  |  |  |  |
| P07 | IOS-STATE-017 | pending |  |  |  |  |  |  |  |  |
| P07 | IOS-STATE-018 | pending |  |  |  |  |  |  |  |  |
| P08 | IOS-NET-015 | pending |  |  |  |  |  |  |  |  |
| P08 | IOS-NET-016 | pending |  |  |  |  |  |  |  |  |
| P09 | IOS-SHOT-001 | pending |  |  |  |  |  |  |  |  |
| P09 | IOS-SHOT-010 | pending |  |  |  |  |  |  |  |  |
| P10 | IOS-STATE-009 | pending |  |  |  |  |  |  |  |  |
| P10 | IOS-STATE-010 | pending |  |  |  |  |  |  |  |  |
| P10 | IOS-SHOT-003 | pending |  |  |  |  |  |  |  |  |
| P10 | IOS-SHOT-004 | pending |  |  |  |  |  |  |  |  |
| P10 | IOS-SHOT-005 | pending |  |  |  |  |  |  |  |  |
| P10 | IOS-SHOT-006 | pending |  |  |  |  |  |  |  |  |
| P10 | IOS-SHOT-008 | pending |  |  |  |  |  |  |  |  |
| P10 | IOS-SHOT-009 | pending |  |  |  |  |  |  |  |  |
| P10 | IOS-BOUND-006 | pending |  |  |  |  |  |  |  |  |
