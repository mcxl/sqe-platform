# MCX-19 Evidence Matrix Audit

Generated 2026-08-27. Covers 197 identifiers mapped across 42 acceptance-evidence test names. The complete unit suite has 65 XCTest methods. The separate UI-test scheme is available for approved runtime work. No runtime UI evidence is recorded here.

This is a public G0 audit. It is not release evidence. It records no pull request or
runtime evidence. The 44 pending identifiers remain public and pending.

The manual `ace-ios-evidence-preflight-manual` workflow validates public record
structure only. The separate `ace-ios-live-evidence-manual` workflow has no automatic
trigger. Its only proposed live command is
`python3 tools/run_tests.py live-evidence --component ios --artifact-root /private/tmp/mcx-19-live-evidence --expected-commit "$ACE_LIVE_EVIDENCE_APPROVED_COMMIT"`.
Use it only after approval.

The live gate binds `mcxl/sqe-platform`, the exact executing Git head, clean-tree
state, and ancestry from `7da6228dc87ad970aa8d44365fbc3823c58020da`. The separately
approved `ACE_LIVE_EVIDENCE_APPROVED_COMMIT` must equal `CM_COMMIT` and Git HEAD.
`CM_BRANCH` must equal `codex/mcx-19-live-evidence-harness`. `CM_BUILD_ID`, `CM_BUILD_DIR`, and the
exact workflow variable must identify `ace-ios-live-evidence-manual`. `CM_TRIGGER_SOURCE`
must equal `api` and `CM_BUILD_STARTED_BY` must identify the operator. It stores raw
artifacts only outside the Git tree. This audit and its JSON records never become
runtime or release evidence.

## Coverage Summary

| Evidence Dimension | Count | Meaning |
|----------|-------|---------------|
| Behavioural complete | 99 | Complete runtime assertions (Keychain, network, model, state-machine) |
| Source-scan complete | 46 | Complete source checks for privacy, UI, and boundary requirements |
| UI hints complete | 8 | Complete source checks for accessibility labels and traits |
| Complete automated evidence | 153 | Identifiers with complete behavioural or source-scan evidence |
| Runtime pending | 44 | Require approved runtime or controlled-evidence review (see Phase6_1EvidenceRegister.json) |
| Partial automated evidence | 22 | Pending identifiers with automated guard or source evidence |
| Any automated evidence | 175 | Complete automated evidence plus pending partial evidence |
| Uncovered | 0 | Every catalogue identifier has automated or pending evidence |
| **Catalogue** | **197** | Evidence dimensions overlap; do not add the rows. |

The 153 complete identifiers and 44 pending identifiers form the exclusive readiness status. Twenty-two pending identifiers have partial automated evidence. The 175 identifiers with any automation include complete and partial evidence.

## Known Limitations (7 identifiers)

| Identifier | Test Method | Issue |
|-----------|-------------|-------|
| IOS-NET-010 | testStateGeneration | Suspended-repository unit proof exists. Device-level cancellation timing still needs approved runtime validation. |
| IOS-NET-011 | testStateGeneration | Suspended-repository unit proof exists. Device-level late-response timing still needs approved runtime validation. |
| IOS-AUTH-009 | testStateGeneration | Suspended-repository unit proof exists. Device-level sign-out timing still needs approved runtime validation. |
| IOS-AUTH-010 | testStateGeneration | Suspended-repository unit proof exists. Device-level credential-change timing still needs approved runtime validation. |
| IOS-STATE-007 | testStateGeneration | Suspended-repository unit proof exists. Device-level refresh timing still needs approved runtime validation. |
| IOS-NET-007 | trustHandlingSourceInspection | Delegate unit check only. Real untrusted-certificate rejection needs an approved endpoint. |
| IOS-NET-008 | trustHandlingSourceInspection | Delegate unit check only. Real hostname-mismatch rejection needs an approved endpoint. |

The first five retain device-level risk after deterministic suspended-repository tests. The last two remain pending network validation.

## Full Identifier-to-Test Mapping

### IOS-BASE (6 identifiers)
| ID | Method | Type | Status |
|----|--------|------|--------|
| IOS-BASE-001 | projectConfiguration | Partial source-tree manifest + runtime pending | ◐ Deterministic sanitized-manifest evidence only. An approved review of `mcxl/sqe-platform` at the executing Git head remains required. |
| IOS-BASE-002 | projectConfiguration | Source-scan | ✅ iPhone + iOS 26 target |
| IOS-BASE-003 | projectConfiguration | Source-scan | ✅ Production imports are limited to Apple frameworks |
| IOS-BASE-004 | projectConfiguration | Source-scan | ✅ Project has no package reference or linked third-party framework |
| IOS-BASE-005 | sourceBoundaryInspection | Source-tree manifest | ✅ Server-source path audit and approved server-contract digest |
| IOS-BASE-006 | sourceBoundaryInspection | Source-scan | ✅ No Production address |

### IOS-MODEL (18 identifiers)
| ID | Method | Type | Status |
|----|--------|------|--------|
| IOS-MODEL-001 | releaseValidation | Behavioural | ✅ Valid release decoding |
| IOS-MODEL-002 | releaseValidation | Behavioural | ✅ Null conclusion |
| IOS-MODEL-003 | decodingFailsClosed | Behavioural | ✅ Missing top-level field |
| IOS-MODEL-004 | decodingFailsClosed | Behavioural | ✅ Missing nested field |
| IOS-MODEL-005 | decodingFailsClosed | Behavioural | ✅ Missing actions array |
| IOS-MODEL-006 | releaseValidation | Behavioural | ✅ Empty actions |
| IOS-MODEL-007 | releaseValidation | Behavioural | ✅ Action order preserved |
| IOS-MODEL-008 | releaseValidation | Behavioural | ✅ YYYY-MM-DD dates |
| IOS-MODEL-009 | decodingFailsClosed | Behavioural | ✅ Invalid dates fail |
| IOS-MODEL-010 | releaseValidation | Behavioural | ✅ UTC publication times |
| IOS-MODEL-011 | decodingFailsClosed | Behavioural | ✅ Invalid publication times |
| IOS-MODEL-012 | decodingFailsClosed | Behavioural | ✅ Unknown fields ignored |
| IOS-MODEL-013 | releaseValidation | Behavioural | ✅ releaseVersion > 0 |
| IOS-MODEL-014 | releaseValidation | Behavioural | ✅ Empty sentinels |
| IOS-MODEL-015 | releaseValidation | Behavioural | ✅ Table-driven coverage of every rejected regular and sentinel validation predicate |
| IOS-MODEL-016 | releaseValidation | Behavioural | ✅ Invalid action status |
| IOS-MODEL-017 | stateMatrix | Behavioural | ✅ Exact no-conclusion notice |
| IOS-MODEL-018 | stateMatrix | Behavioural | ✅ Exact no-actions notice |

### IOS-NET (30 identifiers)
| ID | Method | Type | Status |
|----|--------|------|--------|
| IOS-NET-001 | requestConstruction | Behavioural | ✅ GET only |
| IOS-NET-002 | requestConstruction | Behavioural | ✅ Correct path |
| IOS-NET-003 | requestConstruction | Behavioural | ✅ Basic auth |
| IOS-NET-004 | originValidation | Behavioural | ✅ HTTPS origin only |
| IOS-NET-005 | redirectDelegate | Behavioural | ✅ Reject HTTP redirect |
| IOS-NET-006 | redirectDelegate | Behavioural | ✅ Reject cross-host |
| IOS-NET-007 | trustHandlingSourceInspection | Static delegate evidence + runtime pending | ◐ Approved endpoint still required |
| IOS-NET-008 | trustHandlingSourceInspection | Static delegate evidence + runtime pending | ◐ Approved endpoint still required |
| IOS-NET-009 | repositoryResponseMapping | Behavioural | ✅ Wrong content type |
| IOS-NET-010 | stateGeneration | Behavioural | ✅ Suspended stale-response test |
| IOS-NET-011 | stateGeneration | Behavioural | ✅ Suspended late-response test |
| IOS-NET-012 | repositoryResponseMapping | Behavioural | ✅ Timeout handling |
| IOS-NET-013 | repositoryResponseMapping | Behavioural | ✅ Direct controlled-transport count is one for both 403 authentication and secure-connection failures. |
| IOS-NET-014 | requestConstruction | Behavioural | ✅ No write methods |
| IOS-NET-015 | originValidation | Static build-phase checks + stateMatrix behavioural evidence + runtime pending | ◐ Source asserts the missing-input check. `testStateMatrix` proves zero Keychain reads and repository calls. Controlled Xcode build remains required. |
| IOS-NET-016 | originValidation | Static build-phase checks + stateMatrix behavioural evidence + runtime pending | ◐ Direct cases reject leading-dot, double-dot, and illegal-character hosts. `testStateMatrix` proves zero Keychain reads and repository calls. Controlled Xcode build remains required. |
| IOS-NET-017 | sessionConfiguration | Behavioural | ✅ urlCache = nil |
| IOS-NET-018 | sessionConfiguration | Behavioural | ✅ Bypass cache |
| IOS-NET-019 | sessionConfiguration | Behavioural | ✅ No cookies |
| IOS-NET-020 | sessionConfiguration | Behavioural | ✅ No credential storage |
| IOS-NET-021 | redirectDelegate | Behavioural | ✅ Direct nil-request assertion for same-origin path |
| IOS-NET-022 | redirectDelegate | Behavioural | ✅ Direct nil-request assertion for changed port |
| IOS-NET-023 | redirectDelegate | Behavioural | ✅ Direct nil-request assertion for changed host |
| IOS-NET-024 | redirectDelegate | Behavioural | ✅ Direct nil-request assertion for clear-text redirect |
| IOS-NET-025 | redirectDelegate | Behavioural | ✅ Direct nil-request assertion with an Authorization-bearing redirect request |
| IOS-NET-026 | repositoryResponseMapping | Behavioural | ✅ Unexpected status |
| IOS-NET-027 | originValidation | Behavioural | ✅ Non-HTTPS fails |
| IOS-NET-028 | trustHandlingSourceInspection | Static delegate evidence + runtime pending | ◐ Approved endpoint still required |
| IOS-NET-029 | projectConfiguration | Source-scan | ✅ Decoded `Info.plist` has no `NSAppTransportSecurity`; project checks remain |
| IOS-NET-030 | trustHandlingSourceInspection | Source-scan | ✅ Default trust only |

### IOS-AUTH (70 identifiers)
| ID | Method | Type | Status |
|----|--------|------|--------|
| IOS-AUTH-001 through IOS-AUTH-003 | keychainLifecycle | Behavioural | ✅ Sign-in/store/load/sign-out |
| IOS-AUTH-004 | keychainQueries | Behavioural | ✅ HTTP 403 through repository and SessionState deletes via CredentialStore |
| IOS-AUTH-005 | stateErrorHandling | Behavioural | ✅ 503 retains Keychain |
| IOS-AUTH-006, IOS-AUTH-007 | privacySourceInspection | Source-scan | ✅ Direct production logging-surface scan; no credential logging surface |
| IOS-AUTH-008 | sessionConfiguration | Behavioural | ✅ No cookie/session |
| IOS-AUTH-009, IOS-AUTH-010 | stateGeneration | Behavioural | ✅ Suspended sign-out and credential-change tests |
| IOS-AUTH-011 through IOS-AUTH-014, IOS-AUTH-016 | keychainQueries | Behavioural | ✅ Query attributes |
| IOS-AUTH-015 | keychainLifecycle | Behavioural | ✅ `errSecDuplicateItem` updates the exact account and only password data |
| IOS-AUTH-017 | keychainLifecycle | Behavioural | ✅ errSecItemNotFound |
| IOS-AUTH-018 through IOS-AUTH-022 | stateErrorHandling | Behavioural | ✅ Error handling |
| IOS-AUTH-023 | physicalDevicePending | Pending | ⏳ Needs physical device |
| IOS-AUTH-024, IOS-AUTH-025 | keychainLifecycle | Behavioural | ✅ Direct missing-delete and different-account replacement-call assertions |
| IOS-AUTH-027, IOS-AUTH-028 | keychainLifecycle | Behavioural | ✅ Replacement deletion and add failures |
| IOS-AUTH-029 | keychainSerialisation | Behavioural | ✅ Serialised concurrent saves |
| IOS-AUTH-030 | keychainQueries | Behavioural | ✅ Reset, replacement, sign-out, and 403 paths use exact class, service, and synchronisation-any deletion queries |
| IOS-AUTH-031 through IOS-AUTH-033 | signInUITest | Source-scan | ✅ Sign-in field privacy |
| IOS-AUTH-034, IOS-AUTH-035 | safeInterfaceUITest | Source-scan | ✅ No authentication details in the interface |
| IOS-AUTH-036, IOS-AUTH-037 | evidencePrivacyInspection | Runtime pending | ⏳ Approved controlled-evidence review required |
| IOS-AUTH-026 | keychainValidation; stateErrorHandling | Behavioural | ✅ Multiple inventory items, a synchronised item, and invalid attributes return unsafe. An unsafe item with failed reset keeps zero network requests. |
| IOS-AUTH-038 | keychainValidation | Partial guard evidence + runtime pending | ◐ Individual guard cases are direct. The test does not cover every inventory and exact-read required-attribute rule. Approved signed validation remains required. |
| IOS-AUTH-039 | keychainValidation | Behavioural | ✅ Valid creation and modification `CFDate` values return the credential. |
| IOS-AUTH-040 | keychainValidation | Behavioural | ✅ An Apple-defined label returns the unchanged credential. |
| IOS-AUTH-041 | keychainValidation | Behavioural | ✅ An unknown returned key returns the unchanged credential. |
| IOS-AUTH-042 | keychainValidation | Behavioural | ✅ An absent account returns unsafe. |
| IOS-AUTH-043 | keychainValidation | Behavioural | ✅ A non-`CFString` account returns unsafe. |
| IOS-AUTH-044 | keychainValidation | Behavioural | ✅ An empty account returns unsafe. |
| IOS-AUTH-045 | keychainValidation | Behavioural | ✅ An exact read without secret data returns unsafe. |
| IOS-AUTH-046 | keychainValidation | Behavioural | ✅ An exact read with non-`CFData` secret data returns unsafe. |
| IOS-AUTH-047 | keychainValidation | Behavioural | ✅ An exact read with empty secret data returns unsafe. |
| IOS-AUTH-048 | keychainValidation | Behavioural | ✅ An exact read with invalid UTF-8 secret data returns unsafe. |
| IOS-AUTH-049 | keychainValidation | Behavioural | ✅ More than one inventory item returns unsafe. |
| IOS-AUTH-050 | keychainValidation | Behavioural | ✅ A synchronised inventory item returns unsafe. |
| IOS-AUTH-052 | keychainValidation | Behavioural | ✅ An absent, wrong-type, or mismatched service value returns unsafe. |
| IOS-AUTH-054 | keychainValidation | Behavioural | ✅ An absent, wrong-type, or true synchronisation value returns unsafe. |
| IOS-AUTH-055 | keychainValidation | Behavioural | ✅ An unexpected inventory member or exact-read result type returns unsafe. |
| IOS-AUTH-056 | keychainValidation | Behavioural | ✅ An exact-read account different from inventory returns unsafe. |
| IOS-AUTH-053 | keychainValidation | Partial guard evidence + runtime pending | ◐ Wrong-type and mismatched access groups fail closed. Approved signed access-group positive test remains required. |
| IOS-AUTH-051 | keychainQueries | Behavioural | ✅ Inventory and exact-read class assertions |
| IOS-AUTH-057 through IOS-AUTH-060, IOS-AUTH-062, IOS-AUTH-063 | stateErrorHandling | Behavioural | ✅ Deletion-only recovery |
| IOS-AUTH-061 | keychainQueries | Behavioural | ✅ Direct recovery-deletion service-query assertions |
| IOS-AUTH-064 | keychainQueries | Behavioural | ✅ Direct exact-read query assertions |
| IOS-AUTH-065 | keychainSourceInspection | Behavioural | ✅ No migration/repair |
| IOS-AUTH-066 | keychainValidation | Behavioural | ✅ A non-`CFDate` creation or modification date returns unsafe. |
| IOS-AUTH-067 | keychainValidation | Behavioural | ✅ An absent, wrong-type, or mismatched accessibility value returns unsafe. |
| IOS-AUTH-068 | keychainValidation | Behavioural | ✅ A successful inventory result that is not an array returns unsafe. |
| IOS-AUTH-069 | keychainValidation | Behavioural | ✅ An exact-read `errSecItemNotFound` after inventory success returns unsafe. |
| IOS-AUTH-070 | keychainValidation | Behavioural | ✅ A successful empty inventory array returns unsafe. |

### IOS-STATE (18 identifiers)
| ID | Method | Type | Status |
|----|--------|------|--------|
| IOS-STATE-001 | releaseScreenUITest | Source-scan | ✅ FICTIONAL PILOT label |
| IOS-STATE-002 through IOS-STATE-006 | stateErrorHandling | Behavioural | ✅ Error states |
| IOS-STATE-007 | stateGeneration | Behavioural | ✅ Suspended single-active-result test |
| IOS-STATE-008 | stateErrorHandling | Behavioural | ✅ Error recovery |
| IOS-STATE-009, IOS-STATE-010 | privacyCoverUITest | Static cover evidence + runtime pending | ◐ Simulator callback validation required |
| IOS-STATE-011 through IOS-STATE-014 | stateMatrix | Behavioural | ✅ Direct state-machine assertions for the complete executable State Matrix |
| IOS-STATE-015 | safeInterfaceUITest | Source-scan | ✅ No auth in UI |
| IOS-STATE-016 | stateErrorHandling | Behavioural | ✅ Error state |
| IOS-STATE-017, IOS-STATE-018 | stateErrorHandling | Controlled error evidence + runtime pending | ◐ Approved network validation required |

### IOS-COPY (9 identifiers)
| ID | Method | Type | Status |
|----|--------|------|--------|
| IOS-COPY-001 | copyControlsUITest | Source-scan | ✅ Labelled copy controls |
| IOS-COPY-002, IOS-COPY-003 | clipboardContract | Behavioural | ✅ localOnly + expiry |
| IOS-COPY-004 | copyControlsUITest | Source-scan | ✅ Production Swift source contains no `Link(` navigation control |
| IOS-COPY-005 through IOS-COPY-007 | copyControlsUITest | Static source + UI test | ✅ Visible copy confirmation, one typed copy-control implementation, and exact UI allowlist prove accessible confirmation and no unapproved copy control. |
| IOS-COPY-008, IOS-COPY-009 | clipboardContract | Behavioural | ✅ Privacy + URL exclusion |

### IOS-SHOT (10 identifiers)
| ID | Method | Type | Status |
|----|--------|------|--------|
| IOS-SHOT-001 | screenshotPolicyInspection | Static source evidence + runtime pending | ◐ No screenshot detection API. Approved fictional simulator screenshot remains required. |
| IOS-SHOT-002 | screenshotPolicyInspection | Source-scan | ✅ No detection API |
| IOS-SHOT-003 | privacyCoverUITest | Static cover evidence + runtime pending | ◐ App-switcher validation required |
| IOS-SHOT-004 through IOS-SHOT-006 | sceneDelegateTest | Static cover evidence + runtime pending | ◐ Simulator callback validation required |
| IOS-SHOT-007 | manualAppSwitcherPending | Pending | ⏳ Needs manual test |
| IOS-SHOT-008, IOS-SHOT-009 | sceneDelegateTest | Static cover evidence + runtime pending | ◐ Simulator callback validation required |
| IOS-SHOT-010 | signInUITest | Static source evidence + runtime pending | ◐ Source checks the visible sign-in fields. Approved fictional simulator screenshot remains required. |

### IOS-PRIV (9 identifiers)
| ID | Method | Type | Status |
|----|--------|------|--------|
| IOS-PRIV-001 | privacySourceInspection | Source-scan | ✅ No file/db writes |
| IOS-PRIV-002, IOS-PRIV-003 | sessionConfiguration | Behavioural | ✅ No cache/cookies |
| IOS-PRIV-004 | projectConfiguration | Source-scan | ✅ Scene plist has no restoration configuration; project has no entitlement setting |
| IOS-PRIV-005 | projectConfiguration | Source-scan | ✅ Project has no widget or notification extension, framework, or plist value |
| IOS-PRIV-006 | privacySourceInspection | Source-scan | ✅ No background refresh |
| IOS-PRIV-007 | privacySourceInspection | Source-scan | ✅ Direct production logging-surface scan; no release or authentication logging surface |
| IOS-PRIV-008 | evidencePrivacyInspection | Source-scan | ✅ Production Swift source has no checked provider, analytics, advertising, or crash-reporting connection markers |
| IOS-PRIV-009 | sceneDelegateTest | Source-scan | ✅ Cover on resign |

### IOS-ACC (19 identifiers)
| ID | Method | Type | Status |
|----|--------|------|--------|
| IOS-ACC-001 | voiceOverOrderUITest | Static UI hints + runtime pending | ◐ VoiceOver validation required |
| IOS-ACC-002 | accessibilityLabelsUITest | Static UI hints + UI audit harness + runtime pending | ◐ The UI-test harness calls `performAccessibilityAudit` for configuration, sign-in, and secure-connection states. Full simulator audit remains required. |
| IOS-ACC-003 | dynamicTypePending | Pending | ⏳ Needs simulator |
| IOS-ACC-004 | boldTextPending | Pending | ⏳ Needs simulator |
| IOS-ACC-005 | reduceMotionPending | Pending | ⏳ Needs simulator |
| IOS-ACC-006 | contrastPending | Pending | ⏳ Needs simulator |
| IOS-ACC-007 | layoutMatrixPending | Pending | ⏳ Needs simulator |
| IOS-ACC-008 | accessibilityAuditPending | Pending | ⏳ Needs simulator |
| IOS-ACC-009 | manualVoiceOverPending | Pending | ⏳ Needs manual test |
| IOS-ACC-010 | simulatorMatrixPending | Pending | ⏳ Needs simulator |
| IOS-ACC-011 | accessibilityAuditPending | Pending | ⏳ Needs simulator |
| IOS-ACC-012 | dynamicTypePending | Pending | ⏳ Needs simulator |
| IOS-ACC-013 through IOS-ACC-015 | contrastPending | Pending | ⏳ Needs simulator |
| IOS-ACC-016, IOS-ACC-017 | manualVoiceOverPending | Pending | ⏳ Needs manual test |
| IOS-ACC-018, IOS-ACC-019 | contrastPending | Pending | ⏳ Needs simulator |

### IOS-BOUND (8 identifiers)
| ID | Method | Type | Status |
|----|--------|------|--------|
| IOS-BOUND-001 | requestConstruction | Behavioural | ✅ Approved GET only |
| IOS-BOUND-002 through IOS-BOUND-005 | sourceBoundaryInspection | Complete source enumeration | ✅ Approved source-file and request-method allowlists retain the read-only boundary. |
| IOS-BOUND-006 | serverCompatibilityExternal | Pending | ⏳ Separate record |
| IOS-BOUND-007 | sourceBoundaryInspection | Source-scan | ✅ Server auth owned |
| IOS-BOUND-008 | fixtureInspection | Complete DEBUG literal allowlist | ✅ All controlled-scenario string literals match the approved fictional fixture set. |

## State Matrix Coverage (31 Rows)

`testStateMatrix` gives direct `SessionState` evidence for every executable row.
It completes each tested retry. `testReleaseValidation` distinguishes empty sentinels.

| Row | Condition | Classification | Evidence |
|-----|-----------|----------------|----------|
| 1 | Missing or invalid Preview configuration | Direct behavioural + source | Configuration state, no store path, and exact configuration text |
| 2 | No Keychain credential | Direct behavioural | Sign-in state with no release result |
| 3 | Keychain read failure | Direct behavioural | Exact message and `keychainRead` retry |
| 4 | Unsafe Keychain inventory | Direct behavioural | Reset-only deletion-pending state and zero requests |
| 5 | Deletion-only reset succeeds | Direct behavioural | Complete reset returns to sign-in |
| 6 | Deletion-only reset fails | Direct behavioural | Exact deletion-pending message and deletion retry path |
| 7 | Valid credential and valid release | Direct behavioural | Complete release, no notices, and completed refresh with the original credential |
| 8 | Initial or replacement add failure | Direct behavioural | Exact sign-in save-failure message and no release |
| 9 | Same-account update failure and successful cleanup | Direct behavioural | Exact sign-in save-failure result after cleanup contract |
| 10 | Same-account update failure and cleanup failure | Direct behavioural | Exact deletion-pending result and no release |
| 11 | Different-account replacement deletion failure | Direct behavioural | Exact deletion-pending result and no release |
| 12 | No published release | Direct behavioural + model validation | Empty state clears the release. Completed refresh retains the credential. |
| 13 | Missing Engagement response | Direct behavioural + model validation | Empty state clears the release. Completed refresh retains the credential. |
| 14 | No conclusion | Direct behavioural | Exact no-conclusion notice on a valid release |
| 15 | No actions | Direct behavioural | Exact no-actions notice on a valid release |
| 16 | HTTP 403 and successful deletion | Direct behavioural | Exact re-sign-in message after deletion |
| 17 | HTTP 403 and deletion failure | Direct behavioural | Exact deletion-pending result blocks access |
| 18 | HTTP 503 | Direct behavioural | Exact unavailable message, refresh, and retained credential |
| 19 | Unexpected HTTP status | Direct behavioural | Exact unavailable message and completed refresh with the original credential |
| 20 | No network | Direct behavioural | Exact connection message and completed refresh with the original credential |
| 21 | Timeout | Direct behavioural | Exact timeout message and completed refresh with the original credential |
| 22 | Untrusted server certificate | Direct error mapping; runtime pending source | Exact secure-connection result. Real trust endpoint remains pending. |
| 23 | Server hostname mismatch | Direct error mapping; runtime pending source | Exact secure-connection result. Real mismatch endpoint remains pending. |
| 24 | Wrong content type | Direct behavioural | Exact unavailable result and completed refresh with the original credential |
| 25 | Invalid or partial JSON | Direct behavioural | Exact unavailable result and completed refresh with the original credential |
| 26 | Invalid release or action value | Direct behavioural | Exact unavailable result and completed refresh with the original credential |
| 27 | New refresh starts | Direct behavioural | One loading state rejects the old result |
| 28 | Sign-out and successful deletion | Direct behavioural | Deletion returns to sign-in with no release |
| 29 | Sign-out and deletion failure | Direct behavioural | Exact deletion-pending result blocks access |
| 30 | Application enters inactive state | Source + runtime pending | `privacyCoverUITest` checks cover installation. UIKit callback needs simulator evidence. |
| 31 | Application becomes active | Source + runtime pending | `privacyCoverUITest` checks delayed cover removal. UIKit callback needs simulator evidence. |

## Pending Items (44 identifiers)

All require an approved runtime environment or controlled-evidence review. The manual `ace-ios-evidence-preflight-manual` workflow and `Phase6_1EvidenceRegister.json` control this work. Its preparation resolves one exact device type and a canonical UUID before it accepts a target. A same-name wrong-type device is ignored. An invalid matching UUID fails the workflow. It selects one highest available iOS 26.x runtime before target resolution. It ignores exact targets in older runtimes. It accepts one exact available target only in the selected runtime and fails if that runtime has more than one. Otherwise, it creates the target once in the selected runtime. It then polls unfiltered `simctl list devices -j` snapshots for no more than 30 seconds at one-second intervals. Each poll subprocess receives only the remaining verification time. A timed-out poll keeps its partial snapshot and final verification log, then fails closed. The returned UUID must occur once with the selected runtime key, exact target name, exact device type, and `isAvailable` true. Missing or temporarily unavailable records can continue until the deadline. Duplicate UUIDs and wrong runtime, name, or device type records fail immediately. It keeps controlled device-type, runtime, pre-creation device, creation, poll snapshot, final verification, and resolution logs. This preparation does not accept evidence.

| Group | Count | Identifiers | Blocker |
|-------|-------|-------------|---------|
| Accessibility audit + matrix | 16 | ACC-001 through ACC-008, ACC-010-015, ACC-018-019 | iOS 26 simulator runtime |
| Manual device journeys | 5 | AUTH-023, ACC-009, ACC-016, ACC-017, SHOT-007 | Approved physical device |
| Repository ancestry validation | 1 | BASE-001 | Manual Phase 6.1 workflow and approved review of `mcxl/sqe-platform` at the executing Git head |
| Signed returned-attribute validation | 1 | AUTH-038 | Approved signed iPhone with the approved access group |
| Signed access-group validation | 1 | AUTH-053 | Approved signed iPhone with the approved access group |
| Controlled evidence privacy review | 2 | AUTH-036, AUTH-037 | Approved controlled evidence package |
| Network validation | 5 | NET-007, NET-008, NET-028, STATE-017, STATE-018 | Approved Preview endpoint + certificate |
| Controlled Xcode build validation | 2 | NET-015, NET-016 | macOS with Xcode 26.4.1 |
| Simulator screenshot validation | 2 | SHOT-001, SHOT-010 | Approved fictional iOS 26 simulator screenshots |
| Cover + server review | 9 | STATE-009, STATE-010, SHOT-003-006, SHOT-008, SHOT-009, BOUND-006 | Security + Pocock approval |

## Verdict

- **153 identifiers** have complete automated behavioural or source-scan evidence
- **44 identifiers** are pending runtime evidence; **22** also have partial automated evidence
- **175 identifiers** have any automated evidence, including complete and partial evidence
- **7 identifiers** have stated residual limitations; these overlap automated and pending evidence where noted
- **0 identifiers** are uncovered or unmapped
- Catalogue, static evidence, runtime-pending evidence, and residual limitations are reported as separate dimensions
