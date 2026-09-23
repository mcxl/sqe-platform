# ACE iOS D2 Result — 17 September 2026

D2 stopped during its first native invocation. XCTest could not initialise its Accessibility service. The selected test method never began. The harness gate is incomplete. Neither comparison arm ran. No retry was made.

## Result And Evidence

Approved instruction SHA-256: `f7147730b09e0b4daf5d18090abc29d38f780962479dc55a49631af20c1f2179`.

| Check | Result |
|---|---|
| Single compilation | Passed, exit 0, 87.09 seconds |
| App source identity | All nine files match failed candidate `52b212aca02190ee0e742debe383fa6016fe36b9` |
| First invocation | Native exit 65 after 348.53 seconds |
| Required method | `ACEClientAppUITests/testCopyReflowCheck()` did not execute |
| Required deliberate failure | Not reached |
| Audit call records | 0; expected calls 0, 1 and 2 |
| Corrected pass, arm X, arm Y | Not executed |
| Evidence | Native log, readable result bundle, native summary and test tree retained |
| Callback screenshots | None generated; image inspection is not applicable |
| Restoration | Settings readback exact; original simulator boot states restored |
| Delivery checkout | Clean at `40bae2640b23eb05496a093d09a4c20186403879` |
| Commit, push, app changes | None |
| Active build or test processes | None at final check |

Exact native failure:

> The test runner failed to initialize for UI testing. (Underlying Error: Timed out while loading Accessibility.)

The native log records `com.apple.dt.XCTest.XCTFuture Code=1000` at line 11 and the final failure at line 24. No Swift assertion line applies: the method did not enter. The native summary's one failed entry names `ACEClientAppUITests-Runner (73015) encountered an error`; it does not establish an executed D2 test.

Xcode exited naturally. A cancellation was considered afterwards, but no signal was sent. The external launcher returned exit 2 because the required gate was not satisfied.

## Retained Locations

Mac evidence root:

`LOCAL_HOME/ace-private/mcx19b-orientation-repair-20260915/14-copy-reflow-check-20260917/`

Root result: `d2-result.json` under that root.

Result SHA-256: `5856820bdba421e954115d9a667307f2ac35dd52410505b5292ce9b02e6b94d9`.

First invocation: `01-harness-failure/execution.json`, `native.log`, `result.xcresult`, `native-summary.json`, `native-tests.json`, `artifact-manifest.json`, and `image-inspection.json` under that root. The manifest hashes 939 retained files, including native bundle contents.

Temporary test patch SHA-256: `9f04805f6aea4244c53057747182087b8810b903eda5736dfe569513a6dc05a4`.

Temporary diagnostic checkout:

`LOCAL_HOME/Developer/sqe-platform-d2-reflow-20260917`

Only its UI-test source is modified. The delivery checkout and existing D1 diagnostic checkout remain preserved.

## Preparation And Limits

The primary agent inspected the complete test diff. A fresh Sol review identified an optional attachment-name compile risk, corrected before the single successful build. Launcher review found schema, hash, settings-read timing, continuation-gate and log-retention issues. These were corrected before the native invocation. A read-only Python import check failed once, was corrected, and then passed the build/source identity check.

The test's offscreen call-0 frame read remains an untested observation risk. That code was not reached and did not cause this startup error.

The approved block began at 11:52:02 Sydney time. The original record was prepared around 12:26, approximately 34 minutes later. Build time was 87.09 seconds, the native command took 348.53 seconds, and simulator boot/readiness took 52.22 seconds. Active model work was not independently timed.

The immediate blocker is XCTest's Accessibility initialisation timeout. Its underlying cause remains unresolved. The Copy contrast question was not tested; this is not a non-reproduction result. There is no acceptance or pilot credit, no colour clearance, and no demonstrated Apple defect. P0 and the discovery pilot remain blocked on their existing terms.

The approved instruction's sections 6 and 7 require stopping when an execution cannot complete and provide no retry. Further native execution needs new authority. No further execution was started.

## Saved-Log Follow-Up

The runner started its 70-second Accessibility timer at 12:20:20.487. The simulator's testmanagerd service received that request at 12:20:27.928 and began its 65-second ready-notification wait at 12:20:47.983.

SpringBoard logged its Accessibility runtime starting at 12:20:51.921. The test runner logged its runtime starting at 12:20:55.791. The runner nevertheless timed out at 12:21:32.017. At 12:21:53.629, testmanagerd recorded **Error 18: Timed out waiting for AX loaded notification**.

This identifies the failed startup step. Why the notification was missing remains unknown. Simulator boot completion did not establish UI-testing readiness. The power log shows Xcode held a sleep-prevention assertion during this session; no sleep event appears in the inspected window.

Detailed finding: `startup-log-review/startup-finding.json` under the Mac evidence root. The session log, extracted service log and power-window evidence are linked there.

## Proposed Next Experiment

Not yet authorised: one execution of the existing compiled short harness on a fresh temporary iPhone 17 simulator profile with iOS 26.4.1. Limit: 20 minutes, one native invocation, no rebuild or retry. Preserve existing simulators, retain evidence, and shut down the temporary simulator afterwards. Success requires the selected method, three call records, and only the deliberate assertion failure. This tests whether simulator-profile state contributes to startup failure. It does not establish a Copy correction.

## Windows Report Recovery

Windows reached zero free space during this follow-up. Updating the compact Windows report failed and truncated that report to zero bytes. This Mac copy restores its recorded content and adds the follow-up. Native evidence and the original Mac result JSON were unaffected.

Automatic approval review rejected removal of two task-created temporary files whose identical copies were verified on the Mac. Its only stated reason was "blocked by policy". No files were deleted. Compression of the task scratch files could not free space. Restoring the Windows report remains pending available Windows disk space.
