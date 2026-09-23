# Complete 22-Case Pilot — 15 September 2026

The full pilot command ran on clean commit `464671562cfb0249e859ffc8905a8f8c5ef17e55`.
It stopped at a failed prerequisite. **None of the 22 screen cases ran.**

- Build: passed in 91.377 seconds.
- Initial settings reads: passed on both required simulators.
- First settings set check: failed on iPhone 17; native exit 65.
- Both simulator restorations: passed. Original boot states restored.
- Runner: exit 2 after 904.280 seconds (15 minutes 4 seconds).
- Source, tests and runner: unchanged. No corrective change or diagnostic rerun.

## Exact Failure

Test: `ACEClientAppUITests/ACEClientAppUITests/testConfigureAccessibilitySettings`.
Assertion: `ACEClientAppUITests.swift:352`; orientation predicate: lines 165–171.

Expected: the app frame height exceeds its width and the five-second expectation completes.
Actual: **“App frame did not reach requested portrait orientation”.**

The native log shows repeated target-application lookup. It does not retain numeric frame values or the waiter result.
The saved recording shows Current Release upright near the failure. Three distinct frames were inspected at original resolution.
These images do not prove the frame value that Xcode read. The cause remains unresolved.

This is a settings/frame-observation test failure. It does not demonstrate an application orientation defect.
The earlier release-final accessibility timeout remains a separate unresolved failure.
This run did not execute an accessibility audit.

## Evidence And Remaining Work

Native log, result bundle, assertions, recording and restoration records remain on the private Mac.
The RESULT.json file records exact commands, times, source identity and evidence locations.
The final-state.json file confirms a clean unchanged candidate, restored simulators and no running xcodebuild.

Next: diagnose the smallest settings check. Any test correction creates a new candidate and needs affected checks.
The approved stop-at-first-failure rule prevented the 22-case screen programme from starting.
The 836-case programme and phone, service, signing and final delivery checks remain pending.
No pilot storage or image-review projection is valid from zero executed screen cases.
