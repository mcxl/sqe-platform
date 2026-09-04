# Runtime Evidence Plan

This public G0 plan is not release evidence. The manual preflight checks only public
record structure and current repository paths. It does not run, collect, publish, or
accept client evidence. Pending records fail closed as not-release-evidence.

Run these checks only on the approved macOS host.

Phase 6.1 uses [Phase6_1EvidenceRegister.md](Phase6_1EvidenceRegister.md).
It maps 44 pending identifiers into 10 work packages.
Use the manual `ace-ios-evidence-preflight-manual` workflow only after approval.
It accepts evidence-preparation commit `5f88563248650f263b4b0fc6c333731868114a25`, one direct correction child, one UI-test platform correction child of `b0eaaa74fa45f60e1ccbda6c3b4ec6faa5e07982`, one UI-test product-name correction child of `ffa73729ab1c45e947ec13d6db00a7b709143b3a`, one app-plist correction child of `d9aacced1d451c64649a08ac3f2012df43b7f27d`, one debug-fixture correction child of `e90efc6123537633dcc8fcb7c27b5bdf2627c3d3`, one copy-control query correction child of `f0cb10b68cce137826c44327f9f433e6b60d3361`, one app launch-screen correction child of `4650a614032d227054bf7f143f409eb7e66e0a38`, or one screenshot-path pilot child of `ddace288d47766172aa8a6fa6b3e5a3e500e0bc6`.
It also accepts one UI readiness correction child of `ff0556229f17d3ee05487391c9c4e26da346fea4`.
It also accepts one screenshot absolute-path correction child of `921d38e096ad4214f44f0f9c32cdad96ab1a49cf`.
The evidence-preparation commit parent must be protected candidate `cdc4f458bfd3ede385844b31eed117d3c06e854d`.
The simulator-destination correction `b36f89c7fee9e37f1014933408fea78bd9eb80a1` must have the evidence-preparation commit as its first parent.
The UI-test platform correction `b0eaaa74fa45f60e1ccbda6c3b4ec6faa5e07982` must have the simulator-destination correction as its first parent.
The controlled gate correction `ffa73729ab1c45e947ec13d6db00a7b709143b3a` must have the UI-test platform correction as its first parent.
The UI-test product-name correction `d9aacced1d451c64649a08ac3f2012df43b7f27d` must have the controlled gate correction as its first parent.
The app-plist correction `e90efc6123537633dcc8fcb7c27b5bdf2627c3d3` must have the UI-test product-name correction as its first parent.
The debug-fixture correction `f0cb10b68cce137826c44327f9f433e6b60d3361` must have the app-plist correction as its first parent.
The copy-control query correction `4650a614032d227054bf7f143f409eb7e66e0a38` must have the debug-fixture correction as its first parent.
The screenshot-path pilot parent `ddace288d47766172aa8a6fa6b3e5a3e500e0bc6` must have the copy-control query correction as its first parent.
The UI readiness correction parent `ff0556229f17d3ee05487391c9c4e26da346fea4` must have the screenshot-path pilot parent as its first parent.
The screenshot absolute-path correction parent `921d38e096ad4214f44f0f9c32cdad96ab1a49cf` must have the UI readiness correction parent as its first parent.
The evidence-preparation and direct correction routes must contain only the six Phase 6.1 preparation files.
The UI-test platform and product-name correction children must contain exactly the six preparation files and `ios/ACEClientApp/ACEClientApp.xcodeproj/project.pbxproj`.
The app-plist correction child must contain exactly these eight files: `codemagic.yaml`, `ios/ACEClientApp/RuntimeEvidencePlan.md`, `ios/ACEClientApp/RuntimeEvidencePlan.json`, `ios/ACEClientApp/evidence-matrix-audit.md`, `ios/ACEClientApp/Phase6_1EvidenceRegister.md`, `ios/ACEClientApp/Phase6_1EvidenceRegister.json`, `ios/ACEClientApp/ACEClientApp.xcodeproj/project.pbxproj`, and `ios/ACEClientApp/ACEClientApp/Info.plist`.
The debug-fixture correction child must contain the same eight files.
The copy-control query correction child must contain those eight files and `ios/ACEClientApp/ACEClientAppUITests/ACEClientAppUITests.swift`.
The app launch-screen correction child must contain the same nine files.
The screenshot-path pilot child must contain the same nine files.
The UI readiness correction child must contain the same nine files.
The screenshot absolute-path correction child must contain the same nine files.
The app launch-screen correction is a pending hypothesis. It does not prove a clipping cure.
The published screenshot-path pilot shows absolute screenshot destinations succeed. The full corrected native capture remains pending.
The UI readiness correction published 20 UI tests and 0 failures at build `6a991338f7568a30a248dc76`. All 44 evidence identifiers remain pending.
Its stated base is `f0ca3f958334af7b6727742460ed060cf9c077aa`.
Record the protected source candidate in the result commit field.
Record evidence-preparation commit `5f88563248650f263b4b0fc6c333731868114a25` in that field.
For a correction child, record the exact build commit.

- `accessibility-audit`: Run `performAccessibilityAudit` for each listed state.
- `dynamic-type`, `bold-text`, `reduce-motion`, `contrast`, and `layout`: Run the approved simulator matrix.
- `simulator-matrix`: Use iPhone SE (3rd generation) and iPhone 16 Pro Max in iOS 26.
- `simulator-provisioning`: Resolve one exact device type before device selection. An existing or created device must have that type identifier and a canonical simulator UUID. A same-name wrong-type device does not qualify. Select one highest available iOS 26.x runtime before target resolution. Ignore exact targets in older runtimes. Accept one exact available target only in the selected runtime. Fail if that runtime has more than one exact available target. Otherwise, create the target once from the exact device type in the selected runtime. Then poll unfiltered `simctl list devices -j` snapshots for no more than 30 seconds at one-second intervals. Give each poll subprocess only the remaining verification time. On a poll timeout, keep its partial snapshot and final verification log, then fail closed. Find the returned canonical UUID across all runtime records. It must occur once with the selected runtime key, exact target name, exact device type, and `isAvailable` true. A missing or temporarily unavailable record can continue until the deadline. A duplicate UUID or wrong runtime, name, or device type fails immediately. Do not create the target again. Keep the device-type, runtime, pre-creation device, creation, poll snapshots, final verification, and resolution logs as pending controlled artifacts.
- `voiceover`, `locked-device`, and `app-switcher`: Run the listed manual device journeys.
- `server-compatibility`: Use the separate server-owned compatibility record. Do not run against an unapproved host.

All runtime evidence remains pending in the Windows implementation stage.
The workflow commands prepare evidence only. They do not record runtime evidence.
