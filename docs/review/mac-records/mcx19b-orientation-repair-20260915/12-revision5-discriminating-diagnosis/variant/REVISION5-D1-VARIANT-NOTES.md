# Revision 5 D1 Temporary UI-Test Variant

Prepared from source commit `52b212aca02190ee0e742debe383fa6016fe36b9`.
Only `ios/ACEClientApp/ACEClientAppUITests/ACEClientAppUITests.swift` changed in the detached worktree.
`Views.swift` remains SHA-256 `3635901a1aa80410bbfeb138a5dafd3b233c2b4b312b8c90ee6fd57a29aa10dd`.

## Environment Selection

The temporary path requires both values:

- `ACE_D1_ARM=B` or `ACE_D1_ARM=C`
- Non-empty `ACE_D1_REPETITION`

It rejects any D1 case other than one audited `copyConfirmation` case.
Without either D1 value, the original audit path remains selected.

## Arm B

For each existing copy-confirmation audit viewport, Arm B invokes the supported iPhoneSimulator 26.4 audit types in this fixed order:

1. `.contrast`
2. `.elementDetection`
3. `.hitRegion`
4. `.sufficientElementDescription`
5. `.dynamicType`
6. `.textClipped`
7. `.trait`

The sequence comes from `XCUIAccessibilityAuditTypes.h`, lines 15–34, in the installed iPhoneSimulator 26.4 XCUIAutomation framework.
The temporary test sets `continueAfterFailure = true` only while a D1 case runs.
Each issue handler returns `false`.
It records the native failure, but lets later approved audit calls run.
A native issue prevents `ACE_CASE_RESULT result=passed`.

## Arm C

Arm C keeps `.all`.
Before the copy-confirmation audit only, it moves `Copy action 1` until it is fully visible and its bottom is above the ScrollView midpoint.
It reads the frame twice with the approved 0.5-second interval.
It fails if either read differs.

## Diagnostic Records

`ACE_D1_A11Y_ISSUE` contains the arm, repetition, viewport, requested audit name, raw audit type bitmask, observed audit type, element, frame, audit-start uptime, and callback elapsed seconds.
Its attached `XCUIScreen.main.screenshot()` is callback-time evidence only.

`ACE_D1_AUDIT_CALL` reports each call with `returnedNormally` and its error value.
`ACE_D1_DIAGNOSTIC_COMPLETE` separates attempted calls from calls that returned normally and confirms both viewport groups.
The existing outer case marker still reports two audit viewports on a clean diagnostic pass.

## Evidence Gate Reuse

No `ACE_CAPTURE_GATE` selector exists in the current runner or retained diagnosis source searched for this task.
No selector was added and no gate execution was started.
The primary task retains the rehashed deliberate-failure bundle, assertion, PNG, and corrected passing evidence.
Those records must be cited by their retained path and hash in the D1 result.

## Verification And Limitations

Static checks completed: exact baseline head, original app-source hash, changed-file list, full diff inspection, and `git diff --check`.
The XCTest SDK declaration at `XCUIAutomation.swiftinterface:14` accepts a non-`@Sendable` issue handler; the D1 handler uses that signature to avoid a Sendable capture of the test case or mutable session.
No build, simulator launch, native test, commit, or runner edit occurred.

