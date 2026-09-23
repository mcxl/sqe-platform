# ACE iOS Release Timeout: Implementation And Verification Plan

Date: 15 September 2026. Status: Closed as non-reproduction. The original pilot remains failed.

## Result
Resolve or isolate the release-final accessibility timeout with evidence. Establish readiness for a fresh 22-case pilot. Do not run the 836-case programme in this work piece.

## Authority And Baseline
The user requested this plan and execution as a goal. Earlier unbounded time authority persists. Two failed corrective attempts per fault remain the stop rule. No new approval is required for the authorised work.
Base: 464671562cfb0249e859ffc8905a8f8c5ef17e55, clean codex/mcx19b-release-layout on the Mac. Preserve Windows and unrelated simulator work.

## Known Failure
Selector: ACEClientAppUITests/ACEClientAppUITests/testCoverageBatch.
Source: ios/ACEClientApp/ACEClientAppUITests/ACEClientAppUITests.swift:348.
iPhone 17, iOS 26.4.1, default large text, portrait, light, three accessibility settings off.
Expected: an unrestricted audit of release-final completes and passes.
Actual: Accessibility audit failed for release release-final: Audit failed to complete in time.
The native failure, log and full-resolution image are retained. The image shows readable content. It does not explain or excuse the timeout. The 68 functional tests and three focused Settings checks passed. Zero full pilot batches passed on this candidate.

## Execution
1. Verify clean source, tools, device state, storage, retained build and failure/pass evidence. Capture original simulator settings. Reuse valid unchanged evidence; do not rebuild only to restate status.
2. Run the unchanged coverage selector for signIn followed by release. This preserves the failing batch prefix and omits only scenarios never reached. Retain the same audit, scrolling, viewport and settings assertions. Capture native evidence and read-only resource observations.
3. Compare the exact outcome with the retained timeout. If it passes, record non-reproduction; do not call it a correction. Select one further discriminating experiment from evidence, such as release alone or temporary shutdown of an idle task-owned simulator. Change one relevant variable. Restore original states.
4. Implement only a demonstrated correction. Allowed files are the existing iOS UI test, local runner/tests, and app Views/AppApp/DebugScenario only if native evidence identifies an app cause. Use the Terra implementation lane for substantial changes. Keep probes and evidence outside source. No new dependencies, architecture, service, signing or public interface changes.
5. After changes, inspect the full diff, run affected Python/native checks, and obtain a fresh read-only Sol review. Repeat the deliberate failure/pass evidence check only if relevant evidence collection changed. Any changed source creates a new candidate.
6. Verify affected release checks on both required simulators. Include light, dark and maximum text if the app UI changes. Confirm settings, counts, unrestricted audit results, retained images and restoration. A passing retry cannot prove cause.
7. Reconcile each criterion and publish a compact record. If no source correction is justified, preserve the clean candidate and state remaining uncertainty. A fresh 22-case pilot is the next stage; no broad acceptance is claimed here.

## Acceptance
- Exact timeout mechanism is supported by evidence, or remaining uncertainty is explicitly recorded for a decision.
- Any correction has native pass evidence; no audit filters, guessed delays, hidden content, font caps or weakened assertions.
- Native results, observed settings, source/build hashes, screenshots and commands are retained and inspectable.
- Required reviews pass for any changed source. Temporary simulator changes are restored.
- Final status distinguishes verified correction, non-reproduction and blocked acceptance. An unresolved timeout keeps the wider programme blocked.

## Time, Cost And Stop Rules
The prior pilot took 16 minutes 10 seconds, including build, settings, failure and restoration. Its failing native test took 143 seconds. The prior build took 80 seconds; another observed build took 669 seconds. These are observations, not a reliable completion estimate. Initial diagnosis needs one focused native run; further duration depends on its result.
No overall time limit under existing authority. Stop corrective changes for this fault after two failed corrective attempts. Stop dependent work for missing evidence/access or scope expansion. Do not treat a running process as failed.
High-cost commands: xcodebuild build-for-testing/test-without-building and xcresult export. Run one native test process at a time using long-run. Store bulk evidence privately on the Mac. Current free space: approximately225GiB; keep the20GiB reserve. Do not export bulk evidence to low-space Windows.
No Codemagic, paid account, TestFlight, App Store, new server work, real client data, Production, merge or unrelated cleanup. Phone is not needed. Private-service and historical baseline acceptance remain blocked outside this work piece.
