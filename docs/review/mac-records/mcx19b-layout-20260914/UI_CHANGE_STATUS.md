# Release Screen Change Status

Updated 14 September 2026, 13:21 AEST. Private diagnostic candidate. UI QA is incomplete.

Base commit: 7dc7cee7654ae8cc002da54324c3d1475a8494e6.
Mac worktree: LOCAL_HOME/Developer/sqe-platform-release-layout.
Branch: codex/mcx19b-release-layout. Four uncommitted files; original Mac checkout remains unchanged.

## Completed

- Added normal content margins to the fixture screen, release cards, section headings, and compact Copy controls.
- Kept exact displayed and copied values, field-specific VoiceOver labels, 44-point minimum targets, and Dynamic Type.
- Added an explicit manual-preview flag to hide the debug appearance label. Automated audits retain the label.
- Applied the retained standalone copy-confirmation container correction. Its prior failure/pass/reversal evidence is retained.
- Native UI build passed. Source diff inspection and git diff --check passed.
- Inspected native light/default screenshots. Rejected one premature Home Screen capture.

## First Revision Test

Job: 1789355270930-ace-layout-release-light-audit-bda03b91. Exit 65.
Native selector: ACEClientAppUITests/testFictionalReleaseHasApprovedCopyControls().
Environment: iPhone 17 simulator, iOS 26.4.1, light, default content size (large), Increase Contrast disabled.
Result: one failed test. Native log contains 21 failures and a three-minute execution allowance exceeded message.

- Line 123: expected unrestricted accessibility audit pass. Actual: seven label contrast findings, “Contrast nearly passed”.
- Line 135: expected post-scroll audit pass. Actual: eight contrast failures, one nearly passed finding, and two potentially inaccessible text findings.
- Line 144: expected copied confirmation audit pass. Actual: two nearly passed findings; one identifies Copied Engagement name.
- Line 145: termination failed after the execution allowance expired.

Native result: LOCAL_HOME/ace-private/mcx19b-layout-20260914/release-light-audit.xcresult.
Log and exported attachments are also retained in this Windows record folder.
The native issue images confirm grey label/confirmation text. A measured label colour pair was RGB 133/133/139 on 242/242/247, about 3.287:1.
Copy issue images show black text on grey. These reports remain unexplained; they do not establish a button colour defect.
Action 1 and OPEN frames shifted 22.333 points between the audit-start record and later records. Callback frames are not sample-time proof.

## Demonstrated Correction And Current Check

Changed only label and confirmation foreground styles from secondary to primary. No font size cap or audit filter.
Native build v2 passed: job 1789355916463-ace-layout-ui-build-v2-7f2ac911.
Views.swift SHA256: 656af6f4d152dcb4a8ea6cd88fae829907255c9237f3f51df7cafc3c1a78e84e.
Full source hashes: LOCAL_HOME/ace-private/mcx19b-layout-20260914/ui-build-v2-source.sha256.
Current release rerun: job 1789355972962-ace-layout-release-light-v2-011e5acc.
The private runner now gives the same focused test five minutes. All assertions and unrestricted audits remain.

## Pending

- Final result and evidence from the colour correction check.
- Dark and maximum accessibility-size native views and relevant audits.
- No-conclusion and no-actions focused checks.
- Fresh read-only review after primary inspection and native checks.
- Signed phone preview installation and user comparison.
- Broader original completion-plan acceptance remains pending, including coverage agreement, physical VoiceOver, live server, signed Keychain and final clean candidate.

The phone still has the previous baseline app. Do not report the new layout installed or accepted.

## Light Correction Result

Completed job 1789355972962-ace-layout-release-light-v2-011e5acc, native exit 65. The one test ran for 131.329 seconds without timeout.
Initial release audit and copied-confirmation audit passed. Eleven approved control/value checks and minimum targets had no assertions fail.
Post-scroll audit at line 135 still failed: eight contrast reports and two potentially inaccessible text reports. Cause remains unknown.
Result bundle: LOCAL_HOME/ace-private/mcx19b-layout-20260914/release-light-v2.xcresult.
Root inspected the updated initial-screen and copied-confirmation screenshots. Both retain the expected values and clear text.
The first-revision Copy failure crop contains RGB 0/0/0 text on RGB 198/198/203. This observation does not establish the native audit's cause.
Dark check is running as job 1789356213549-ace-layout-dark-v2-a05a5246. Fresh read-only Sol review is running in /root/layout_review.

## Dark Check And Native Views

Job 1789356213549-ace-layout-dark-v2-a05a5246 passed, exit 0, one test, zero failures or skips. Native result: release-dark-v2.xcresult in the Mac layout evidence directory.
Root inspected light initial, light copied confirmation, dark initial and dark scrolled release images. Text, values, headings and Copy controls are visible at default text size.
The largest accessibility text check uses existing testNormalDeviceSettings, verified normal simulator appearance and content-size assertions, and unrestricted initial/post-scroll audits. Job 1789356376050-ace-layout-max-text-v2-32e23e7c is running.
Phone availability was rechecked: iPhone 15 Pro Max is connected. Original Mac source checkout remains clean.
The first-revision Copy crop's dominant text/background pair measures approximately 12.341:1. The native report's cause remains unresolved; this measurement alone does not override the audit.

## Largest Text Check

Job 1789356376050-ace-layout-max-text-v2-32e23e7c completed with exit 65. Native testNormalDeviceSettings ran 101.709 seconds without timeout.
The normal-device appearance/content-size assertions passed. All eleven complete-value visibility checks and target-size checks passed. The initial unrestricted audit passed.
The post-scroll unrestricted audit at line 260 failed with five contrast findings: Engagement name, Review status, Release version and two Copy nodes. No value was missing and no layout assertion failed.
Root inspected native maximum-text images for engagement name, published date and action status. Values wrap and Copy controls sit below their values. The text is not capped.
Native result: LOCAL_HOME/ace-private/mcx19b-layout-20260914/release-max-text-v2.xcresult.
No-actions focused check is running: job 1789356575526-ace-layout-no-actions-v2-f68412f4.

## Phone Preview Installed And Confirmed

14 September 2026, 13:34 AEST: the signed phone build passed. Strict code-signature verification passed. The bundle identifier, team, app identifier, phone inclusion and unexpired development profile checks passed.
The revised app was installed on the connected iPhone 15 Pro Max and launched successfully as process 1047. Launch settings selected the fictional release scenario and omitted the debug appearance indicator.
The user confirmed: “Yes, I see the new layout”. This is a manual confirmation of the visible layout, not full accessibility acceptance.
Phone records: phone-layout-v2-build.xcresult, phone-layout-v2-signing-check.json, phone-layout-v2-install.json and phone-layout-v2-launch.json in the Mac layout evidence directory.
The phone profile expires 21 September 2026 at 02:37:21 UTC.

## Final Focused Status

- Source review: no actionable defect found. Full primary diff inspection and git diff --check passed.
- Simulator and physical phone builds: passed.
- Phone installation and launch: passed; user confirmed the new layout.
- Default dark release test: passed, including unrestricted audits, values, targets and copied confirmation.
- Default light initial and copied-confirmation audits: passed. Post-scroll audit failed with 8 contrast and 2 inaccessible-text findings.
- Maximum accessibility text: all eleven values, wrapping and target checks passed. Post-scroll audit failed with 5 contrast findings.
- No actions: the notice became visible and target checks passed. One contrast finding without an identified element failed the audit at line 171.
- No conclusion: the notice became visible and target checks passed. Six Copy contrast findings and two inaccessible-text findings failed the audit at line 171.
- Root inspected the native no-actions and no-conclusion failure images; they show the expected notices and complete visible values. No source cause was established.
- Current revision orientation, full matrix, physical VoiceOver, signed Keychain and live-server acceptance remain pending. This focused work does not replace those gates.

Status: UNVERIFIED — UI QA INCOMPLETE. The improved private preview is on the phone. No commit, push, merge, paid service or Production action occurred. The original Mac source checkout remains clean; Windows source work was not changed.
All selected test processes completed. The phone and simulator preview apps remain open. Review agent /root/layout_review completed.

Private UI evidence archive verified on Mac and Windows. SHA256: f2a859e480a0ee7f355d066bbfd5bb7fa5413442d4c334f9332b495af7bd35f1. All eleven required result bundles and records are present. Derived caches are excluded. Archive: LOCAL_HOME\Documents\Codex\2026-09-14\ace-mac-setup\mcx19b-layout-evidence-20260914.tar.gz

A later one-variable plain-button diagnostic failed (3 contrast and 2 inaccessible-text findings). It was reversed, the exact v2 source hash was restored, and a restored native build passed. See COPY_STYLE_DIAGNOSTIC.md. The phone layout remains unchanged; manual Copy confirmation is pending.


## Phone Copy Confirmation

14 September 2026: the user answered yes when asked whether "Copied Engagement name." appears on the iPhone 15 Pro Max. Record the visible confirmation as manually confirmed for the installed v2 preview.
The pasted clipboard value and VoiceOver announcement remain pending. The next manual check is to tap Copy again and paste into Notes on the same iPhone. The expected text is exactly "Fictional Engagement". Clipboard source sets localOnly and a 300-second expiry; these settings are source observations, not completed phone checks.
Overall status remains UNVERIFIED - UI QA INCOMPLETE.


## Phone Clipboard Value Confirmed

14 September 2026: the user confirmed that copying Engagement name and pasting into Notes on the same iPhone produces exactly "Fictional Engagement". Manual result: PASS for this field in the installed v2 fictional preview on iPhone 15 Pro Max.
This confirms the visible confirmation and this clipboard value. Other fields, VoiceOver announcement, expiry and cross-device restrictions remain unverified on the phone. Overall accessibility acceptance remains incomplete.


## Phone Text Clipping Check

14 September 2026: after instructions to turn the iPhone sideways and scroll to the bottom, the user reported "no text cut off". Record no clipping observed by the user in this manual check of the installed v2 preview on iPhone 15 Pro Max.
The response did not separately confirm that the app rotated. Do not count this report as complete orientation or accessibility acceptance. The next manual check is dark appearance readability.


## Phone Dark Appearance Readability

14 September 2026: the user answered yes after instructions to select Dark in iPhone Settings, return to ACE Client and scroll through the screen. The user confirmed all text was clear and easy to read in the installed v2 fictional preview on iPhone 15 Pro Max.
Manual readability result: PASS for this observation. This does not establish measured contrast, all accessibility states, VoiceOver or full matrix acceptance. The phone's exact text size was not recorded for this check. The next manual check is the largest accessibility text size.


## Phone Largest Text In Dark Appearance

14 September 2026: the user answered yes after instructions to keep Dark appearance, enable Larger Accessibility Sizes, move the slider fully right, and scroll through ACE Client. The user confirmed all text was readable and every Copy button was reachable in the installed v2 fictional release preview on iPhone 15 Pro Max.
Manual result: PASS for reported readability and button reachability in this state. This does not verify each button's clipboard value or establish VoiceOver, measured contrast or full matrix acceptance. Largest-text readability in Light appearance is the next manual check. Restore the user's original text settings after these checks.


## Phone Light Readability And Repeated Copy Question

14 September 2026: the user confirmed readable text and reachable Copy buttons after the Light appearance instructions. The attached image shows the fictional release screen in Light appearance and several visible field-specific copy confirmations.
Windows image: attachment folder CE97B636-A679-485C-BE7E-0DA25E16009D, 1-Pasted-Image-1.jpg, in task 01a09d4d-171e-7870-b315-01c387761f73.
Record reported readability as confirmed. Maximum accessibility text size remains unconfirmed: the image shows Copy beside each value, while current ValueRow code places Copy below the value when dynamicTypeSize.isAccessibilitySize is true. The image alone does not establish its capture settings or time. Do not count it as verified maximum-size evidence; the earlier Dark maximum-size report also lacks independent settings evidence.
The user asked whether tapping Copy again should hide Fictional Engagement. Current Views.swift lines 249-305 always display the source value. Each tap writes the same value and assigns a field-specific confirmation; there is no toggle or expiry for that visible confirmation. Spec lines 340 and 1062 require a short, accessible confirmation, without specifying a dismissal interval. Clipboard expiry at five minutes is separate from visible confirmation lifetime.
No app source changed. A temporary confirmation is a possible presentation improvement, not an established requirement or implemented correction. Full accessibility acceptance remains incomplete.
