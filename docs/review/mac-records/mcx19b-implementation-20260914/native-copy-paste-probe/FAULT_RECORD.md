# Native Paste Selector Fault

Selected test: `testNativeCopyPasteProbe`, private test line 517.
Expected: a native Paste command is found. Actual: `destination.buttons["Paste"]` was absent. Native exit 65, one failed test, no skips.

The retained `Native Paste menu` screenshot visibly contains Paste. The failed query restricts its search to Button elements. This is a test selector fault, not evidence of an application Copy failure.

Corrective attempt 1 uses a type-independent exact-label query. It keeps the actual Copy, native Paste and exact-value assertions. No app source changes.
