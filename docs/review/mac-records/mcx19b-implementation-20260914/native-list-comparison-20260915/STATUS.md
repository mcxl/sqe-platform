# Native List Comparison Result

15 September 2026. The comparison is complete. The proposed List correction failed.

Main source remains clean at 1b38b90e9a949b7e73965602612c11be6f19e9fc.
Only detached control and trial copies were changed. No phone installation, push or merge occurred.

Both minimal builds passed. Both runs used identical tests and tools on iPhone 17 Pro Max, iOS 26.4.1, light appearance.
The control reported 12 native contrast findings at UI test lines 692 and 703.
The List trial reported 43 native findings at lines 675, 692 and 703: five contrast, 36 text-size, two clipping.
All three trial audits ran. No other assertion failed. Each run had one failed test and zero skipped tests.
The primary agent inspected all 48 distinct PNG images across both runs. All 137 PNG artifacts remain private on the Mac.

Do not promote the List trial. Keep the current layout and complete-action Copy.
The underlying native accessibility failure is unresolved. Screenshots do not establish an Apple defect.
Broader List test support and viewport audit coverage also remain incomplete, as recorded by the source review.

Read COMPARISON_RESULT.json, control-fault.json, trial-fault.json, source-comparison.json,
control-image-review.json, trial-image-review.json and SOL_TRIAL_REVIEW.json for source hashes, commands and results.
The retained test command records include exit codes and durations.
No trial process remains active. Observed simulator text size after the run is large, matching the starting value.

Overall delivery remains incomplete. Phone access, private service inputs and baseline resolution remain missing.
Physical checks, the 22-case pilot, 836-case coverage and final acceptance reviews remain pending.
