# MCX19B Acceptance Status

Specification: docs/specs/2026-08-24-ace-ios-read-only-client-application.md at 7dc7cee7654ae8cc002da54324c3d1475a8494e6. The accepted conversation corrections take precedence over the original local-plan proposal.

## Required Results

| Result | Status | Evidence Or Remaining Check |
| --- | --- | --- |
| Windows can operate the Mac project without manual file copying | Passed | SSH and saved ACE iOS Mac project verified. Source resides on the Mac. |
| Exact current source baseline identified | Passed | Mac and Windows HEAD match 7dc7cee7654ae8cc002da54324c3d1475a8494e6. Windows edits retained separately. |
| Historical specification baseline ancestry | Blocked | The stated historical commit is absent locally. Origin rejects fetch with `not our ref`. This does not invalidate the independently identified current HEAD. |
| Xcode and required simulator definitions available | Passed | Xcode 26.4.1; iOS 26.4.1 runtime; iPhone 17 and iPhone 17 Pro Max definitions. iPhone 17 executed the native pilot. Pro Max execution remains pending. |
| Minimal local app build | Passed | build-configured.log and build-configured.xcresult, exit 0, on the unchanged baseline. |
| Deliberate failing test and accessible native evidence | Passed | pilot-native-fail.xcresult: testRequestIsGETAndHasNoCache, line 59, expected POST, actual GET, one deliberate failure. Native bundle and supporting records backed up to Windows with a matching archive hash. |
| Same test passes after assertion restoration | Passed | pilot-native-pass.xcresult: same selector, one pass, zero failures or skips. Mac source clean at the baseline. |
| Coverage decision bound to a candidate | Pending | Obligations below are mapped. No total execution count is adopted. |
| Original findings reproduced and compared | Pending | Exact prior source snapshots, hashes, selected logs, and five matrix passes retained privately. |
| Corrections have observed causes and focused checks | Partial | The private release layout was revised and installed. A label contrast correction has focused native evidence. Light post-scroll and empty-state audit failures remain unresolved; see UI_CHANGE_STATUS.md. |
| One clean final candidate and complete native suite | Pending | Source, tests, runner, workflow, inputs, and environment must identify the tested candidate. |
| Manual image acceptance | Pending | Inspect the exact retained images and bind their hashes to the final candidate. |
| Physical iPhone access | Passed | iPhone 15 Pro Max, iOS 26.6.1, paired, Developer Mode enabled, DDI available. |
| Free signing and physical installation pilot | Passed | Valid signing identity; desktop Xcode build succeeded; strict code signature check passed; devicectl installation succeeded. Private fixture configuration only. |
| First physical app launch | Passed | After the user trusted their developer account, devicectl launched the fixture at 02:45:24 UTC. User confirmed Fictional Engagement. Native record: phone-pilot-launch-trusted.json. This establishes the pilot launch only. |
| Signed Keychain checks | Pending | Installation and local signature verification do not establish runtime Keychain acceptance. |
| Eight physical VoiceOver journeys | Pending | The real phone is available. No manual journey is claimed. |
| Approved server and negative network/privacy checks | Pending | Fixture success cannot replace these checks. |
| Required final reviews and delivery records | Pending | Review the exact final candidate. Historical reviews do not establish current acceptance. |

## Simulator Coverage Obligations

Both specified simulators: iPhone 17 and iPhone 17 Pro Max, on the approved iOS 26 runtime.

All 18 visual states: sign-in; loading; valid release; no published release; missing Engagement; no conclusion; no actions; HTTP 403; HTTP 503; unexpected HTTP status; no network; timeout; invalid response; Keychain read failure; Keychain write failure; Keychain deletion failure; copy confirmation; privacy cover.

For each screen and state, cover portrait and landscape and light and dark appearance. Cover default, extra large, and accessibility extra-extra-extra large text. The automated layout suite must additionally cover every iOS 26 Dynamic Type size. Cover Bold Text off/on, Reduce Motion off/on, and Increase Contrast off/on in both appearances. Retain the observed settings.

Run unrestricted performAccessibilityAudit for every listed screen and state. No unresolved automated accessibility finding is accepted. Confirm rendered text size and weight before selecting a contrast threshold. The specification includes a separate 3:1 bold-text rule.

The specification states these obligations but does not give an authoritative execution total. The relationship between complete combinations and separate setting sweeps remains a written coverage decision. Neither 252 nor 3456 is adopted here. Existing valid evidence must be assessed for reuse before running additional cases.

## Physical And Other Coverage

The eight VoiceOver journeys are sign-in/error recovery; release reading order; empty sentinels; no-conclusion/no-actions; failure/retry; every approved copy field; app-switcher cover/return; and failed Keychain deletion during sign-out.

Keep the 18 visual states separate from the specification's functional condition rows and requirement IDs. These are different coverage sets, not interchangeable test counts.

Keep native results, evidence collection, visual inspection, and final acceptance separate. Five prior native matrix passes remain historical evidence. Their relevance to a later candidate requires an explicit source and environment comparison.

## Evidence Locations

- Mac current run: LOCAL_HOME/ace-private/mcx19b-local-20260914.
- Mac setup and records: LOCAL_HOME/ace-private/mcx19b-setup-20260914.
- Windows current records: LOCAL_HOME/Documents/Codex/2026-09-14/ace-mac-setup.
- Retained prior evidence inventory: prior-evidence-inventory.json in both private locations.

Raw logs, source overlays, native result bundles, and private identifiers remain outside the public repository. No Codemagic run is authorised or planned.

## Release Layout Preview Update

The user confirmed the revised layout on the physical iPhone 15 Pro Max. Build, signature, installation and launch passed. This manual layout check does not establish final acceptance.
Current source is the private codex/mcx19b-release-layout worktree based on 7dc7cee7654ae8cc002da54324c3d1475a8494e6 plus four uncommitted files. UI_RUN_RESULTS.json identifies exact file hashes.
Dark release checks passed. Light post-scroll, maximum-text post-scroll, no-actions and no-conclusion audits failed. Detailed assertions, issue types, result bundles and source-review outcomes are in UI_CHANGE_STATUS.md and UI_REVIEW_RESULT.md.
The original full application acceptance checks above remain pending. No unresolved audit is accepted.


## Current Phone Checks And Next Work

The user confirmed the installed v2 layout, the Engagement name copy confirmation, and the exact pasted value Fictional Engagement. The user also reported no cut-off text and readable Light and Dark appearances.
Maximum accessibility text size is not established on the phone. The latest supplied image shows Copy beside each value; the reviewed implementation puts Copy below values at accessibility text sizes. Preserve the readability observations, but keep the effective size and complete orientation checks open.
The installed app still uses a fictional fixture. Sign-in, refresh, sign-out, approved service access, physical VoiceOver, privacy and signed Keychain behaviour are not accepted from these layout checks.
Next technical priority: examine retained native failures and distinguish app defects from audit or test faults before another source change. Current source inspection confirms that initial release audits pass while later audits follow a scroll through all fields. This is an observed sequence, not a proven cause. Keep the copy-confirmation timing improvement separate from required acceptance work.
Reuse existing passes where applicable. Do not run the full matrix before the coverage decision and final candidate are established. Overall result remains UNVERIFIED - UI QA INCOMPLETE.
