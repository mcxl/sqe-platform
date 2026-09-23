# ACE iOS Implementation Status

Started: 14 September 2026, approximately 16:47 Sydney time. Authority: user approval of IMPLEMENTATION_PLAN_APPROVED.md. Overall: UNVERIFIED — UI QA INCOMPLETE.

## Current Checkpoint — 19:25 Sydney Time

Current result: implementation and focused checks have progressed. Delivery remains unverified.

- The runner retained the deliberate POST expectation failure and the corrected GET pass. Both used runner SHA-256 `66e3a013ff91370393aa32f419604b71525d4385ae7680d89404de910399da4b`. Only the deliberate test expectation differed. See `runner-failure-pass-gate-diagnostic.json`.
- All 66 unit and contract tests passed, including 43 contract tests. No skips or expected failures occurred. Native execution took 13.103 seconds. This result predates the later sign-in prompt colour change. See `functional-all-current/functional-evidence.json`.
- One sign-in coverage integration passed with actual settings, a full native audit, matched images and setting restoration. Two images had one identical SHA-256. This was diagnostic work, with no credit towards the final 836 cases.
- The native no-conclusion contrast diagnostic retained 16 images. All five distinct image hashes were inspected at original resolution. The six native Copy crops contain black text against grey, with a measured colour-pair contrast of 12.341:1. Native audit findings remain failures.
- The private reduced-view test reproduced eight contrast and two inaccessible-text findings after scrolling. Its initial full audit passed. A comparison with the same initial audit and scroll steps passed when its final audit checked contrast alone. Test binaries differ only because the comparison setup was aligned. This is evidence of inconsistent audit behaviour, not an approved exception.
- The private pixel-stability diagnostic passed. The same-build control also passed without that observation. Neither result establishes a cause or correction. The audit changed the captured viewport even on the passing run. No delay or audit filter was added to the repository. See `results-minimal-audit-repro/minimal-audit-repro-pixel-stable.xcresult` and `minimal-audit-repro-control-current.xcresult` in that directory.
- Manual inspection found a separate sign-in prompt defect despite a passing native audit. Username and Password measured 1.723:1 in light mode. The first attempted correction compiled and passed native light/dark audits, but its images still measured 1.723:1 and 2.478:1. That correction failed the manual check.
- The second prompt correction passed native audits and full-resolution image inspection in both appearances. The prompts now measure 21:1 in light mode and 17.015:1 in dark mode. The four images form two identical-hash groups. See `signin-prompt-colours-attempt-2.json` and `signin-prompts-after-2/integration.json`. Views.swift SHA-256 is `fd198b1845d32ec20cc00e9c550a16e0b1b436de640f5252c54bd061b9fec662`. This is a focused simulator result, not phone or full-size acceptance.
- Native Reduce Motion, Increase Contrast and orientation controls are under focused integration. Each setting changes alone and is restored. See `remaining-settings-integration/` when complete.
- Source inspection found that several sample empty/error states omit controls from production screens. A read-only review is identifying the smallest shared-rendering correction before coverage. No correction has been made yet.
- Pocock review is available through the installed Matt Pocock code-review skill. It has not run on a clean final commit. Final Sol review remains pending.
- No final commit, pilot, full coverage programme, new phone install, push or merge has occurred.

Older observations below remain historical. Use the current results above where status differs.

Latest results supersede the earlier running-test entries below:

- Four focused functional checks passed. These include the composed credential/session lifecycle check. Native record: `contracts-after.xcresult`; four passed, zero failed or skipped.
- Native setting read passed. The first Bold Text change failed because the test tapped the centre of the Settings row. The switch was at the right edge. The retained event coordinates and full-resolution video frame establish this test-control fault.
- The first correction changed that tap location. Bold Text then switched on successfully. A separate test restored Bold Text to off. Both tests passed with actual app observations. Reduce Motion and Increase Contrast remained off. Orientation remained portrait.
- Relevant records: `settings-bold-integration/`, `settings-tap-source.json`, `settings-bold-corrected.xcresult`, and `settings-bold-restored.xcresult`.
- Runner source review repairs and 14 Python checks passed. Preflight passed. Native failure/pass integration remains in progress. Do not treat this implementation review as the required final candidate review.
- The deliberate runner probe changes only one test expectation from GET to POST. The source will return to its original bytes after the run. The corrected pass follows review of the retained failure.
- A smaller private audit fixture is prepared. It is separate from the app candidate. Its full audit has not run yet.
- No pilot or full coverage case has been accepted. Four native app audit failures still prevent acceptance.

The entries below retain earlier observations. Where they report a running test, use the completed results above.

- Mac SSH and Xcode 26.4.1 (17E202): rechecked, passed.
- Simulator runtime: 26.4.1 (23E254a), verified from native JSON. The list display shortens its name to iOS 26.4.
- iPhone 15 Pro Max: connected by cable, paired, Developer Mode enabled, iOS 26.6.1.
- Mac branch/base and visible app layout remain as approved. Temporary audit probes were restored exactly. New DEBUG setting observations and coverage tests are under native integration. Specification and plan files record the approved coverage.
- Atomic: unavailable on Windows and Mac; native Apple tools remain the working execution route.
- Windows C: 1.85 GiB free; new bulk evidence exports blocked. Mac has approximately 242 GiB free.
- Four current native failures remain unresolved. The new no-conclusion diagnostic passed its initial full audit. After scrolling, contrast alone passed, then the full audit reported six Copy contrast and two inaccessible-text findings.
- This result narrows the cause to the audit mask or its processing. It does not prove an Apple defect. No app-source correction is justified by this evidence.
- Approved service inputs remain missing. Historical commit 6b0160befc9191dbccd527bdd385b891782ddad8 was found in the original Windows repository. All 23 imported iOS file blobs match the later import source. However, the historical baseline and that import source have no common ancestor. Baseline-dependent acceptance remains blocked. See BASELINE_PROVENANCE.json.
- No broad suite, app-source correction, commit, push, merge, paid action or Production action has occurred in this implementation turn.
- The contrast diagnostic first failed compilation because its callback lacked an explicit Sendable declaration. The corrected diagnostic compiled. Both records remain private.
- A temporary run-file preparation command used the wrong plist format. It failed before testing. The corrected command uses the generated file's observed format. The failed shell launch returned 127; it did not run a test.
- Pro Max visible-state test passed: one test, both appearances, no skips. The two retained images were inspected at full resolution.
- Corrected source-contract checks and a composed credential/session lifecycle test compiled successfully. Four focused checks are running as job 1789372822770-ace-contracts-after-cd6b0da2. Their result is not yet known.
- Local runner review found run-file relocation, selector discovery, and evidence-gate defects. A second focused correction is in progress. Do not use broad runner modes until native integration and retained deliberate failure/pass checks pass.

## Remaining Deliverables

| Deliverable | Status |
| --- | --- |
| Execute app on both required simulators | Passed; Pro Max settled visible-state test and both full-resolution images retained |
| Approved service inputs and historical ancestry | Service inputs missing; baseline/import ancestry mismatch established and blocked for review |
| Resolve four native accessibility failures | Pending |
| Necessary local runner and deliberate failure/pass check | 14 Python checks and native deliberate failure/pass passed; one native coverage integration passed; broader support remains under verification |
| Functional tests and observed settings | 66 native unit/contract tests passed before prompt correction; Bold Text on/off passed; remaining setting combinations pending |
| Manual sign-in prompt contrast | Second correction passed native light/dark audits and original-resolution inspection; other sizes and phone remain pending |
| Specification coverage amendment and clean candidate | Documents updated; primary arithmetic/197-ID checks passed; clean final candidate pending |
| 22-case pilot and resource decision | Pending |
| 836-case programme and image inspection | Pending |
| Physical VoiceOver, Keychain, clipboard and privacy checks | Pending |
| Live-service and separate server compatibility checks | Blocked pending approved service |
| Required final reviews and verified phone delivery | Pending |

Raw evidence will remain under LOCAL_HOME/ace-private/mcx19b-implementation-20260914. Each later checkpoint must record exact commands, results, hashes and evidence locations. Estimates remain unknown until faults and pilot measurements establish remaining work. Elapsed, active, test and waiting time must remain separate.

## Retained Results

All following relative paths refer to the private Mac directory above.

| Record | Observed Result |
| --- | --- |
| initial-audit-build.xcresult | Generic build-for-testing passed, exit 0 |
| no-conclusion-initial-diagnostic.xcresult | One failed test, no skips; initial full audit passed; post-scroll full audit had eight findings; test duration 46.129 seconds |
| contrast-only-build.xcresult | Build failed, exit 65; non-Sendable audit callback at UI-test line 176 |
| contrast-only-build-2.xcresult | Corrected diagnostic compiled, exit 0; app source unchanged |
| no-conclusion-contrast-diagnostic.xcresult | One failed test, no skips; initial full audit and post-scroll contrast-only audit passed; subsequent full audit had eight findings at UI-test line 182; test duration 58.623 seconds |
| primary-doc-validation.json | Same 197 requirement IDs; unique groups 144/396/60/216/20; total 836; 512 audits; 324 layout-only; 22 pilot cases |

The contrast diagnostic UI-test SHA-256 is `aeeee9381dc99a3c978d8879aa353a13434ea3bdffd3b4485976535b0b9bc2b7`.

The private archive `preflight-build-evidence.tar.gz` has SHA-256 `c60fef63af680d0d731544861fb387e1467ce8a1e717ea98e15dde85d2e6f027`. Authenticated retrieval into memory matched this hash. No archive was saved on Windows. A connection with all authentication methods disabled returned permission denied. This proves access control now; it does not prove future availability.

The focused native source-contract run retrieved three failed tests and five exact assertions before correction. The Copy source checks expected the old button and confirmation syntax. Two document checks expected the old specification hash. These source checks now match the approved layout and specification. They remain source checks, not runtime UI proof. The new composed test joins sign-in, stored credentials, relaunch and sign-out across new session instances using a fake SecItem adapter. Signed phone Keychain behaviour remains pending.

Native enumeration confirmed 65 original unit/contract tests, including 42 contract tests and three catalogue tests. The new source adds one contract test: expected total 66, including 43 contract tests. This is a source inventory until the new native enumeration and execution confirm it.

Elapsed time at this checkpoint is approximately 158 minutes. Build/test timestamps remain in native job records. Human active work and waiting have not been measured separately. Remaining execution time is unknown until faults and pilot measurements establish it.

