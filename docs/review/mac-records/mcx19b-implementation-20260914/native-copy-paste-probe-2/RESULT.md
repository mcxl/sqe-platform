# Native Copy And Paste Probe

PASS: one native UI test, no failures or skips, native exit 0.

The app copied Engagement name. Its visible confirmation appeared. After relaunch into the sign-in fixture, the native Paste command inserted exactly `Fictional Engagement` into the empty text field. No sign-in was submitted.

The only change from the failed probe is the Paste query. It now uses the exact label across element types. The app source remains unchanged. All three distinct PNG images were inspected at original resolution.

This establishes focused simulator behaviour. The final eleven-field test will include stale-clipboard protection. Real VoiceOver announcements, local-only handling, exact expiry bounds and physical behaviour remain separate checks.

Source parent: `7fee853aef52e85a813368a51d833c134710186d`. Use `source-provenance.json` and `build-identity.json` for the private test source and products. See `copy-paste/summary.json`, `native.log`, `result.xcresult` and `attachments/`.
