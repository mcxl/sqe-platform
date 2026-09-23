# ACE D2 Fresh Simulator Recovery — 18 September 2026

The single approved recovery reached the test but stopped on a genuine Copy contrast finding. The deliberate-failure gate remains incomplete. No retry or further D2 execution was started.

## Result

- Native test: `ACEClientAppUITests/testCopyReflowCheck()`. Exit 65; one test, one failure, zero skips; no timeout.
- Exact failure: `Contrast failed`, at `LOCAL_HOME/Developer/sqe-platform-d2-reflow-20260917/ios/ACEClientApp/ACEClientAppUITests/ACEClientAppUITests.swift:94`.
- Expected: records 0, 1 and 2, followed only by `D2 deliberate harness failure`.
- Actual: records 0 and 1; call 1 reported Copy contrast and stopped. The deliberate assertion was not reached.
- Call 0: unrestricted initial audit; no recorded findings or native failure delta.
- Call 1: all audits except Dynamic Type; `Copy action`, contrast audit raw value 1. Frame changed from `(32, 622, 144, 58)` to `(32, 685.6667, 144, 58)`; downward difference 63.6667 points.
- Observed app settings: light, large text, portrait, Bold Text off, Reduce Motion off, Increase Contrast off.

## What This Establishes

A fresh simulator got past the previous startup failure in this attempt. That does not prove the earlier simulator was defective.

Copy contrast and a position change occurred in call 1 without the Dynamic Type audit. Excluding Dynamic Type from that call did not prevent either observation. Call 0 remained unrestricted, so carry-over effects are not excluded. This short harness is not a completed X/Y comparison and proves no root cause.

Four distinct PNG images were viewed. The callback image and native app screenshot are byte-identical. The element crop contains the complete Copy action label. These images do not establish the rendering sampled by the checker. The native screen recording is retained but has not been inspected continuously.

## Environment Finding

During startup, two older simulators' `mediaanalysisd` processes used 574.5% and 488.3% CPU in one sample, roughly 10.6 core equivalents on a 16-logical-CPU Mac. A second sample recorded 483.5% and 325.0%. Memory free percentage was 48%. This is evidence of competing CPU activity, not proof that it caused a timeout or contrast finding. Raw observations are retained in `live-startup-resources.json` and `high-load-followup.json`.

## Preservation And Timing

- Failed candidate `52b212aca02190ee0e742debe383fa6016fe36b9`; existing app and diagnostic test bundle hashes reverified before and after. No rebuild, source change, commit or push.
- New simulator `7D5FC194-1F43-41DA-94B8-6A32FCD9F584`: iPhone 17, iOS 26.4.1, build 23E254a.
- Native command: 399.778 seconds including startup and finalisation. Test method: 81.087 seconds. These are elapsed measurements, not active engineering time.
- Recovery started at 00:03:27 Sydney. Execution and restoration finished at 00:18:34 Sydney; final review followed within the 00:23:27 limit.
- Settings restored; fresh simulator shut down and retained. Existing simulator boot states unchanged. No xcodebuild remained at the final check. Delivery worktree remained clean.
- The previously truncated Windows D2 report was restored from the retained Mac copy, verified SHA-256 `0310ae03d4358f9347c3f12e292125f6899651bfbbd746e113d774ed896db7ae`.

## Evidence And Next Decision

Mac evidence root:
`LOCAL_HOME/ace-private/mcx19b-orientation-repair-20260915/15-fresh-simulator-recovery-20260918`

Native result: `result.xcresult`. Exact assertion and calls: `native.log`. Machine records: `recovery.json`, `native-summary.json`, `native-tests.json`, `review.json`. Attachment hashes and inspection limitations are in `review.json`.

The approved rule requires stopping when a genuine finding blocks the harness demonstration. Copy remains unresolved; P0, the pilot, coverage, device/service verification and ancestry decisions are unchanged. No automatic rerun is warranted. Fable can review the new call-1 finding and retained recording before proposing the next bounded diagnostic. Separately, reduce competing simulator activity before any approved next run; do not treat that as a Copy correction.
