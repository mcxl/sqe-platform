# Revision 5 D1 Compiler Correction 1

The initial build failed at ACEClientAppUITests.swift:570. Expected: the diagnostic UI-test target compiles. Actual: sending issueHandler.some risks causing data races. Retained build.log lines 3815-3818 contain the exact diagnostic. This is a harness compiler fault.

The callback captured mutable session state and the test instance. Correction 1 uses an explicit @Sendable callback. It captures immutable values and a checked-Sendable counter backed by Synchronization.Mutex<Int>. All counter reads and writes hold the mutex. Other session bookkeeping stays outside the callback.

Static helpers preserve the issue payload and serialization. XCTContext.runActivity attaches the screenshot without capturing the test instance. Installed XCTest headers document activity attachments and require the main thread. The audit API is main-actor isolated and its callback is synchronous. The screenshot stays inside that callback, with the original name and keepAlways lifetime. Native execution must verify retention.

The original patch and failed build remain unchanged. The new full patch is ACEClientAppUITests.r5-d1.correction1.patch. The delta from the failed source is ACEClientAppUITests.r5-d1.correction1.delta.patch. Adjacent JSON records exact changed-line ranges, hashes, SDK evidence and checks.

Static checks passed: git diff --check, reverse application validation of the full patch, callback capture inspection and counter synchronization. These checks do not establish compilation.

No build, test, simulator command, compiler flag relaxation, warning suppression, broad actor annotation or application change was made. A first edit transport quoting error happened before mutation; corrected transport passed the original source hash guard. A notes tool submission failed before command execution.

Primary owns full diff review and pin updates. Luna owns build and native verification. Correction attempt 1 is prepared; its compiler outcome remains pending. D1 deadline remains 2026-09-16T15:47:44Z.
