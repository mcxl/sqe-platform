# Current Release Audit Fault

Status: unresolved. This record does not approve an exception.

Reviewed commit: `7fee853aef52e85a813368a51d833c134710186d`.
Execution: retained UI build and pinned b9ba714 diagnostic runner. The coordinator verified all relevant iOS source hashes and retained product hashes. The current app source was unchanged. This focused run earns no final coverage credit.

Test: `ACEClientAppUITests/ACEClientAppUITests/testFictionalReleaseHasApprovedCopyControls`.
Source: `ios/ACEClientApp/ACEClientAppUITests/ACEClientAppUITests.swift:571`.
Expected: the unrestricted native accessibility audit reports no failure.
Actual: seven Copy contrast findings and two potentially inaccessible-text findings. Native exit 65. One test failed; none passed or skipped.

Exact contrast description: `Contrast failed for SwiftUI.AccessibilityNode`.
Exact text description: `This element appears to display text that should be represented using the accessibility API.`
The two text findings do not identify an accessible element.

## Evidence

- `diagnostic.json`: retained build identity and source-hash comparison.
- `summary.json`, `command.json`, `native.log`, `result.xcresult`: native outcome and command.
- `attachments/manifest.json`: native evidence associations.
- `image-review.json`: all 29 native PNG files; five distinct hashes inspected at full resolution.
- `video-frames/frames.json` and `video-frames/image-review.json`: selected retained recording frames and inspection.

## Established Observations

The Copy crops show readable black text on grey. The recording shows smaller and larger text during the full audit. Text then returns to its original size. The recorded Action 1 and OPEN positions move down by about 22.333 points between the pre-audit and post-audit logs. The native failure screenshot has Sign out partly outside the viewport.

These are observations at recorded times. They do not establish the native contrast or text-detection sample times. They do not prove the failures are Apple defects. The screen recording alone cannot justify a pass or an exception.

A private reduced view also reproduced full-audit failures. Contrast-only and later full-audit controls passed on some runs. A passing control does not establish a correction. No delay, hidden content, text-size limit or finding filter was added to the application or acceptance tests.

## Work That Remains

Identify the failing audit's actual sampling state and the two undetected text regions. Keep application defects, test faults and environment faults separate. A repeat run needs a new diagnostic question and the smallest useful scope. Do not start the pilot or further UI batches while this fault remains unresolved.

Acceptance still requires unrestricted native passes. Any proposed exception needs a specific user decision supported by reproduction, contrary evidence and a clear explanation.
