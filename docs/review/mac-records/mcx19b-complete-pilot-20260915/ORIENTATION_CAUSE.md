# Why The Pilot Stopped

## Confirmed Cause Of The Latest Failure

The test places an Xcode frame-reading request inside a five-second timer.
Xcode gives its own query 30 seconds. The outer timer expired first and cancelled that query.
The helper then reported an orientation failure without a completed frame reading.

The detailed native session log proves this sequence:

- Line 1926: the outer orientation waiter starts with five seconds.
- Lines 1940–1942: the frame query starts with its own 30-second limit.
- Lines 1946–1952: the outer watchdog interrupts that query after 4.238 seconds.
- Line 1952: XCTest reports error 1001, “Interrupted by waiter”.
- Lines 2107–2109: the outer waiter reports TimedOut after 5.352 seconds.
- Lines 2111–2112: snapshot responses arrive later.

The recording shows Current Release upright near the failure.
The failure is a cancelled frame-reading check. It does not prove that the app was in the wrong orientation.
The failed test is testConfigureAccessibilitySettings. The assertion is at ACEClientAppUITests.swift:352.
The five-second wrapper is at lines 165–171.

## What Remains Unknown

We have not proved why the native frame query was slow.
The Mac has Low Power Mode enabled. A later read showed CPU_Speed_Limit 39.
Three simulators were booted during the pilot. These are possible contributors, not proved causes.
The earlier release-final accessibility-audit timeout remains separate and unresolved.
A repair of this orientation check would not, by itself, prove that audit timeout fixed.

## Concrete Next Correction

1. Read and record the actual frame without an outer timer cancelling the native query.
2. Report a failed frame reading separately from a measured orientation mismatch.
3. Preserve the independent in-app orientation and accessibility-setting checks.
4. Use a small focused check to prove portrait and landscape pass and a deliberate mismatch fails.
5. Test environmental changes separately. Use one required simulator at a time; assess Low Power Mode separately.
6. Freeze the corrected candidate and refresh the affected checks before the full pilot.

These steps keep the app design and native accessibility checks intact.
No source correction, power change or further native test has been made in this diagnosis.
The current pilot remains failed: zero of 22 screen cases executed.

## Retained Evidence

Mac stage: LOCAL_HOME/ace-private/mcx19b-complete-pilot-20260915.
ORIENTATION_CAUSE.json and orientation-log-excerpt.txt contain the cause evidence.
RESULT.json retains the run outcome. Its earlier unknown-waiter statement is superseded by this diagnostic addendum.
The native archive contains 1,077 files. Every file hash passed verification.
Authenticated archive retrieval passed without a bulk file on Windows.
Both simulators returned to their original settings and boot states. The source remains unchanged.
