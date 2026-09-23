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
