# MCX19B Local Completion Checkpoint

Updated: 14 September 2026. Phone launch confirmed at approximately 12:45 AEST; release-screen revision now active.

## Authority And Order

User approved continued work without a time limit and with all current-task approvals. No Codemagic, Production, merge, real client data, or public raw evidence.

Accepted order: verify access and candidate; prove local build and retained failure/pass evidence; settle coverage; reproduce and compare; make demonstrated corrections; add only necessary tools; verify one clean final candidate.

## Source And Environment

- Mac: ace-mac, LOCAL_HOME/Developer/sqe-platform.
- Baseline: 7dc7cee7654ae8cc002da54324c3d1475a8494e6, codex/mcx-19-live-evidence-harness.
- Xcode 26.4.1 (17E202), macOS 26.6.2 (25G83), Intel x86_64.
- iOS 26.4.1 simulator runtime supports x86_64. iPhone 17 UUID: 2EB0863C-470E-467D-A0C6-CD216DA70C67.
- iPhone 15 Pro Max connected, iOS 26.6.1. Developer Mode enabled; DDI services available. The signed private pilot app is installed and launched. The user confirmed Fictional Engagement and supplied a screen image.
- Windows source edits remain untouched. Mac diagnostic UI and container patches are retained privately but not applied.
- The specification's historical baseline 6b0160befc9191dbccd527bdd385b891782ddad8 is absent from both local Git object stores. Ancestry is unknown, not failed.

## Current Source Change

The deliberate pilot assertion at ACEClientAppTests.swift:59 was restored to GET after its native failure report was retrieved. The Mac source is clean at the baseline. No application source changed. The earlier line-68 note was incorrect; native evidence and numbered source confirm line 59.

Restore only with the checked reverse of pilot-intentional-failure.patch. Do not reset other work. The patch is in this folder and LOCAL_HOME/ace-private/mcx19b-setup-20260914.

## Evidence Gate

Private Mac evidence: LOCAL_HOME/ace-private/mcx19b-local-20260914.

- build-baseline: exit 65, missing ACE_PREVIEW_ORIGIN. Exact script phase error retained in log and xcresult. Environment input fault.
- build-configured: PASS, exit 0. Existing fixture inputs ACE_PREVIEW_ORIGIN=https://preview.example.invalid and ACE_BUNDLE_IDENTIFIER=com.example.aceclientapp supplied. Native log and xcresult retained.
- pilot-fail: exit 70 before XCTest, destination rejected.
- pilot-fail-intel: exit 70 before XCTest, ARCHS=x86_64 added.
- pilot-fail-simulator: exit 70 before XCTest, simulator SDK added.
- Additional concrete-destination attempts (booted, explicit destination architecture, build-for-testing) also exited 70 before XCTest. Booting the simulator and specifying x86_64 did not correct that route.
- Generic simulator build-for-testing PASSED, exit 0. Job 1789352128271-ace-mac-pilot-build-generic-652770de, 02:15:28–02:17:23 UTC. It generated ACEClientApp_iphonesimulator26.4-x86_64.xctestrun.
- Direct test-without-building from that generated file executed exactly one deliberate failing XCTest. Job 1789352346937-ace-mac-pilot-native-fail-5edf74c9, exit 65, 02:19:06–02:20:47 UTC. Test execution was 2.049 seconds; total job time includes startup and collection.
- Native failure: ACEClientAppTests/testRequestIsGETAndHasNoCache(), source line 59. Expected POST (deliberate incorrect expectation), actual GET. Native result has one failed test, no unexpected failures. Retrieved summary, test tree, and test details confirm the assertion. No media attachments are expected for this unit assertion.
- Retained evidence: pilot-native-fail.log, pilot-native-fail.xcresult, pilot-native-fail-details.json, pilot-native-fail-source.swift, pilot-native-fail-products.sha256, and pilot-build-generic-source.patch in the private Mac run directory.
- Restored-source build PASSED, exit 0, job 1789352512451-ace-mac-pilot-build-restored-a6b44579, 02:21:52–02:22:16 UTC.
- The same test PASSED, exit 0, job 1789352667809-ace-mac-pilot-native-pass-dfd5b937, 02:24:27–02:24:38 UTC. Native summary: one passed test, zero failed or skipped. Test execution was 0.019 seconds. Mac source remained clean at 7dc7cee7654ae8cc002da54324c3d1475a8494e6.
- The build and native failure/pass evidence gate is PASSED. The private archive pilot-gate-native-evidence.tar.gz contains both native result bundles and supporting records. Its SHA-256 matches on Mac and Windows: fa9e78288e743099528b20a5f5a2ed30d5cdeec64b6c580026d1283a29246300.
- Read-only checks list the exact simulator UUID and accept it in showBuildSettings. The rejection cause remains unknown. No project correction is justified.
- Simulator boot PASSED: job 1789351341633-ace-mac-boot-iphone17-736a5fb2, exit 0, 02:02:21–02:05:51 UTC. No selected-device crash was found. Native test execution now independently proves runtime access.

## Remaining Deliverables

- The minimal build and deliberate failure/pass checks are complete. Reuse their retained evidence while the relevant inputs and environment remain unchanged.
- Record coverage from the accepted specification. Do not use unverified 252 or 3456 totals.
- Reproduce retained noConclusion, noActions, release, and confirmation findings on an identified private diagnostic candidate.
- Correct only demonstrated defects, then create and verify a clean final candidate under the required review gates.
- Complete required simulator, physical VoiceOver, signing/Keychain, server, privacy, and manual visual checks. Access-dependent checks remain pending.
- Reconcile deliverables against retained evidence before completion.

## Compatibility Question

User intends later use on iPhone 16e. Project minimum iOS is 26.0, iPhone family. Apple lists iPhone 16e as iOS 26 compatible. This supports expected compatibility; this device has not been tested.

## Apple Account Decision

User first requested enrolment, then asked about paid benefits, then instructed: continue without paid. No membership purchase or enrolment submission occurred. Apple enrolment page was queued in Codex only. Use free Personal Team testing. Apple documents a seven-day provisioning limit for this route.

The user added their Apple account. Xcode now lists one account. The user created an Apple Development certificate. It runs from 14 September 2026 to 14 September 2027. Do not request or store passwords, verification codes, or private keys.

## Phone Installation Evidence

- Initial identity evaluation: one matching identity, zero valid identities. The public certificate passed a separate native trust check. Login and System keychains had the expired WWDR certificate.
- Downloaded Apple's G3 intermediate from https://www.apple.com/certificateauthority/AppleWWDRCAG3.cer. Native certificate verification passed against the existing Apple root. SHA-256: dcf21878c77f4198e4b4614f03d696d89c66c66008d4244e1b99161aac91601f. Added this intermediate to the login keychain without changing trust settings. Identity evaluation then found one valid identity.
- phone-pilot-build.sh compiled the app and created a free provisioning profile. The SSH build exited 65 at CodeSign with errSecInternalComponent. Native build failure and exact command are retained. securityd recorded an unlock attempt at the signing time.
- The same codesign command ran in the Mac's desktop Terminal session and passed. Strict signature verification passed. This proves the desktop route works; the precise keychain restriction on the SSH route remains unknown. No private key was exported.
- phone-pilot-build-on-mac.command then completed the same Xcode build in the desktop session. Native result: succeeded, zero errors, two existing warnings. Source remained clean at 7dc7cee7654ae8cc002da54324c3d1475a8494e6. Run: 02:40:45–02:40:51 UTC.
- Private pilot inputs: Debug/arm64, team 85SMJXHMJ5, bundle com.alanrichardson.aceclientapp, origin https://preview.example.invalid. These are diagnostic inputs, not approved final live-service configuration.
- phone-product-check.json confirms the app identifier, phone inclusion in the profile, profile expiry, and strict signature verification. Executable SHA-256: 5172fbedfde8ab38252518c60387a4275e2c37000f98760cbf791be8f125b0ba. Profile expires 21 September 2026 at 02:37:21 UTC. Signed Keychain behaviour remains pending.
- Native devicectl installation succeeded at 02:41:39 UTC. Evidence: phone-pilot-install.json and .log. App display name: ACE Client.
- First launch requested ACE_UI_TEST_SCENARIO=release to show fictional data. It exited 1. Native nested error: FBSOpenApplicationErrorDomain code 3, Security; invalid signature, inadequate entitlements, or profile not explicitly trusted. Local signature verification passed. Next check is the Developer App trust entry on the physical iPhone. Do not claim the app has opened or passed physical acceptance.
- No app source, project configuration, tests, or workflow files changed for this phone pilot. No Codemagic or paid membership was used.

- After the user trusted their developer account, the same native launch succeeded at 02:45:24 UTC, process ID 875. The launch JSON confirms the release fixture environment. User visual confirmation: Yes, I can see it. Evidence: phone-pilot-launch-trusted.json and .log.

## Current User Steering

The user then asked: How do we fix what the user sees? Their physical screenshot is retained as phone-before-layout.jpg, SHA-256 909fa06a3cc4fcc2c676f5cb3a326f44409d39c35e3db325638a60b38b16964a.

The current work is a focused release-screen revision in an isolated Mac worktree: LOCAL_HOME/Developer/sqe-platform-release-layout, branch codex/mcx19b-release-layout. The original Mac checkout and Windows source remain unchanged. UI_CHANGE_PLAN.md defines scope and native acceptance checks. The main app completion objective remains active; this new UI candidate must not inherit historical matrix passes.

The revised preview was built, signed, installed and launched on the iPhone 15 Pro Max at 03:34 UTC. The user confirmed the new layout. Four files remain changed only in the isolated Mac worktree. UI_CHANGE_STATUS.md and UI_RUN_RESULTS.json contain the current exact results. The fresh source review found no actionable defect. Dark-mode focused checks passed. Light, maximum-text, no-actions and no-conclusion audits still have unresolved findings. Status: UNVERIFIED — UI QA INCOMPLETE. No final release, commit, push or merge is claimed.
