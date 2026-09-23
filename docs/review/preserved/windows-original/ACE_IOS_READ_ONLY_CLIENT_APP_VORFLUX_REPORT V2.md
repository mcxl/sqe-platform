# ACE iOS Read-Only Client Application — Investigation Report

**Report:** `ACE_IOS_READ_ONLY_CLIENT_APP_VORFLUX_REPORT V2.md`  
**Status:** Revised draft for local Codex, auditor, Security, Legal, and user review  
**Revision:** 24 August 2026 — incorporated final local Codex evidence corrections and user selections for iPhone-only iOS 26 support, Keychain sign-in, normal screenshots, controlled copy buttons, and the implementation hard limit  
**Access date for external evidence:** 23–24 August 2026 (UTC)  
**Investigation boundary:** Research, comparison, and design planning only; no implementation, repository access or change, project creation, installation, download, build, test, deployment, account creation, or hosted demonstration occurred.

## Decision legend

- **recommended** — bounded design recommendation for the proposed specification.
- **user selected** — the user selected the product option; required Security or technical approval can remain open.
- **needs human decision** — approval or information is required before implementation.
- **blocked** — must not proceed under the current instruction.

## 1. Executive Summary

**Decision — user selected:** Build Phase 1 as a small native SwiftUI read-only release viewer that calls only `GET /client/api/v1/release/current` through `URLSession`, decodes a hand-written `Codable` response, holds the fetched release in memory, and renders it without editing, provider access, analytics, or persistent offline release storage.

**Decision — recommended:** Keep ACE authoritative and preserve existing client authentication and G0. The app must neither bypass those controls nor send a write request. A mobile failure must be unable to alter an ACE record.

**Decision — user selected:** Use the current Xcode iOS App template with SwiftUI and Apple frameworks only. Add no third-party runtime package. For one endpoint, React Native/Expo adds a JavaScript/native dependency and build layer, while a wrapped web view adds web-session and navigation concerns without reducing the ACE boundary. Both remain outside this slice.

**Decision — user selected:** Keep the user signed in between app launches. Store the existing Basic credentials in iOS Keychain. Sign-out or HTTP `403` must delete the exact Keychain item and clear all release data. Security must approve device-only storage, availability while unlocked, synchronisation off, backup behaviour, deletion, migration, and recovery. Never store passwords in source, logs, `UserDefaults`, fixtures, or plain-text files.

**Decision — recommended:** Interpret “no persistent offline release storage” broadly. Use an ephemeral `URLSessionConfiguration`, disable response caching and cookie storage, and exclude credentials and release content from scene restoration, application state restoration, logs, notifications, widgets, and application-switcher snapshots.[E5]

**Confirmed fact:** The inspected ACE client release route uses stateless HTTP Basic authentication. It validates credentials against environment configuration and does not create a cookie-backed or server-side session for that route. Missing or invalid credentials return HTTP `403`.[C1]

**Decision — recommended:** Use Swift Testing for model, client, and state tests; retain XCTest UI testing for the end-to-end user journey. Apple’s current testing guidance distinguishes code-level Swift Testing from XCTest UI automation.[E10][E11]

**Decision — user selected:** Phase 1 supports iPhone only and requires iOS 26 or later. iPad-specific design and testing are outside this slice.

**Decision — blocked:** Auditor workflows, combined client/auditor roles, new authentication, provider-backed screens, writes, local release persistence, Production, TestFlight, App Store submission, and implementation are outside this investigation.

## 2. Evidence And Versions

### 2.1 Controlled hand-off facts

The following are **confirmed only as supplied hand-off facts**. They were not independently verified because this investigation forbids repository and Git-history access:

- Repository named by the hand-off: `mcxl/agentic-os-workspace`.
- Fixed controlled target: `6b0160befc9191dbccd527bdd385b891782ddad8`.
- Current endpoint: `GET /client/api/v1/release/current`.
- Compatibility response: HTTP `200`, `application/json`, `599` bytes, SHA-256 `5e19bc98c09286a2eb8181650462cfb5ae6952eb342da080643d54a8ab6856af`.
- Response fields are limited to the engagement name, review/release/published metadata, conclusion fields, and action fields listed in the instruction.
- Internal identifiers, approval attribution, audit history, and withdrawal details are excluded.
- The inspected ACE client release route uses stateless HTTP Basic authentication, with expected credentials supplied by environment configuration. That route does not create a cookie-backed or server-side session. Missing or invalid credentials return HTTP `403`.[C1]
- Missing server configuration returns HTTP `503` through the client authentication path; G0 rejection returns HTTP `503` through the client route.[C1]
- Action dates use `YYYY-MM-DD`; publication times use UTC `YYYY-MM-DDTHH:MM:SSZ`.[C2]
- Release entries are ordered by `release_entry_id`; the identifier controls server ordering but is not exposed in the client response.[C3]

**Decision — blocked:** If local Codex reports a controlled remote target other than `6b0160befc9191dbccd527bdd385b891782ddad8`, stop before implementation planning is accepted.

### 2.2 Current external evidence

| Evidence | Current/applicable version observed | Material use in this report |
|---|---:|---|
| Apple Xcode support matrix [E2] | Xcode 26 family; current matrix observed 23 Aug 2026 | Confirms supported SDK/deployment ranges are separate and informs the minimum-OS decision. |
| Xcode 26 release notes [E1] | Xcode 26 | Current SwiftUI template and testing context. |
| SwiftUI and Xcode project guidance [E3][E4] | Current web documentation | Native project and adaptive declarative UI baseline. |
| Apple Keychain guidance [E7] | Current Security documentation | Credential persistence option. |
| URLSession documentation [E5] | Current Foundation documentation | First-party HTTPS client. |
| ATS guidance [E6] | Current Security documentation | HTTPS and fail-closed transport baseline. |
| Swift Testing/XCTest guidance [E10][E11] | Xcode 26 context | Unit/state tests versus UI automation. |
| Swift OpenAPI Generator [E12][E13] | `1.13.0`, current release confirmed 23 Aug 2026 | Generated-client comparison; pin and recheck the selected version before any later adoption. |
| Expo documentation [E14][E15] | SDK 57 surfaced; iOS 16.4+ / Xcode 26.4+ surfaced | Cross-platform comparison only; no package is approved. |
| XcodeGen [E16] | `2.46.0`, current repository release confirmed 24 Aug 2026 | Optional project generation comparison. |
| Tuist [E17] | Release page surfaced 4.49.1, but repository activity/version channels were ambiguous | Reference only; exact current CLI version is **unknown** and must be rechecked if later considered. |
| Composable Architecture [E18] | Release results surfaced 1.26.0 and 1.26.1 inconsistently | Reference only; exact current release is **unknown** and dependency is not justified here. |

### 2.3 Evidence limitations

- No supplied Phase 6B2 specification extract or `ACE_PROGRESS_GUIDE.html` extract was available beyond the instruction itself.
- Vorflux did not inspect the repository, source, OpenAPI document, server configuration, or a real response body. Authentication/status/date/order facts added in this revision were confirmed by local Codex against the fixed controlled target and cited to its controlled local review.[C1][C2][C3]
- The response is data-minimised relative to ACE, but it is not necessarily non-sensitive: engagement names, conclusions, actions, owners, dates, and evidence references can still disclose client information. Security classification remains open.
- Search rate limits prevented confirmation of a small number of current-version details. In accordance with the instruction, ambiguous current versions are reported as unknown rather than inferred.
- Apple sample/tutorial licensing must be checked against the terms attached to each downloaded sample before reuse; no sample was downloaded or inspected during this investigation.[E20]

## 3. Product Boundary

| Interpretation | Fit | Boundary result |
|---|---|---|
| Read-only client release viewer | Directly maps to one existing endpoint and the supplied release projection. No approval or editing authority is required. | **recommended** for Phase 1. |
| Full auditor field application | Requires auditor identity, approval authority, evidence capture, offline/field behaviour, conflict handling, audit history, and likely write APIs. | **blocked** pending a separate specification, threat model, API contract, and approvals. |
| Combined client and auditor application | Adds role separation, cross-role navigation, authority confusion, broader data exposure, and distribution/access-control questions. | **blocked** pending a separate product and security decision. |

The recommended product answers one question: **“What is the current ACE client release I am authorised to see?”** It does not become a mobile ACE system of record.

## 4. Approach Comparison

Scores are relative to this one-endpoint, read-only slice.

| Criterion | Native SwiftUI | React Native with Expo | Responsive web / wrapped web view |
|---|---|---|---|
| One-endpoint fit | Excellent; `URLSession`, `Codable`, and SwiftUI suffice. | Good functionally, but platform/runtime layers exceed need. | Good if an approved web client already exists; none is established in the hand-off. |
| iPhone/iPad | Native adaptive controls and navigation.[E3] | Supported through React Native/Expo; current SDK has its own OS/Xcode floor.[E14] | Browser-responsive layout possible; wrapped navigation and keyboard/safe-area behaviour need explicit handling. |
| Accessibility | Direct Apple semantics, Dynamic Type, VoiceOver, contrast, and system settings.[E8][E9] | Accessibility APIs exist but require cross-layer verification. | Depends on web semantics plus WebKit wrapper integration. |
| Tests | Swift Testing plus XCTest UI.[E10][E11] | JavaScript tests plus native/E2E tool choices. | Web tests plus wrapper/device tests if packaged. |
| Credential handling | Security framework/Keychain available directly.[E7] | Secure storage normally adds an Expo/native module. | Cookie/session storage and web credential behaviour require a separate decision. |
| Dependency count | Zero third-party dependencies required. | Node, Expo/React Native, modules, package lock, native build outputs. | Web stack and possibly wrapper tooling; server/web deployment dependencies. |
| Build/signing | Standard Xcode app. | Expo/EAS or native prebuild plus Xcode signing. | Web deployment plus optional native wrapper signing. |
| Maintenance | Smallest surface and direct Apple lifecycle. | Cross-platform upgrades and package compatibility add work. | Web/browser compatibility plus wrapper lifecycle if distributed as an app. |
| Offline-data risk | Can be explicitly memory-only. | Cache/storage modules must be controlled. | Browser and WebKit caches need explicit control/evidence. |
| TestFlight/App Store | Normal native process, but out of scope. | Supported, with Expo/Xcode version coupling.[E15] | Native wrapper still undergoes review; a pure web app is not an App Store app. |
| Local Build iOS Apps compatibility | Direct fit with SwiftUI/Xcode capabilities named in the hand-off. | Possible but adds React Native/Expo setup. | Limited value unless a native wrapper is approved. |

**Decision — recommended:** Native SwiftUI from the current Xcode iOS App template.

**Decision — blocked:** Expo or a web wrapper must not be introduced without a separate dependency/tool/product decision. Neither is needed to satisfy the current contract.

## 5. Recommended Architecture

```text
SwiftUI views
  -> ReleaseViewModel / observable screen state
  -> CurrentReleaseRepository (read-only protocol)
  -> ACEClient using URLSession
  -> HTTPS GET /client/api/v1/release/current
  -> existing client authentication and G0
  -> existing ClientReleaseService / ClientReleaseStorage
  -> ClientReleaseProjection
  -> existing ClientReleaseResponse
```

### Controls

| Control | Design evidence expected later |
|---|---|
| Cannot bypass ACE authentication or G0 | Every request to the inspected client release route uses its existing stateless HTTP Basic authentication over HTTPS. HTTP `403` maps to generic access failure; client-route G0 HTTP `503` maps to generic unavailable.[C1][E6] |
| Cannot access provider/database credentials | App configuration contains neither provider nor database connection material; dependency and string scans are clean. |
| Sends no write request | Transport API exposes only a `fetchCurrentRelease()` GET operation; mock-transport tests reject any non-GET method. |
| Is not a second authoritative record | No edit, approval, export-as-record, background sync, or persistent release database; UI identifies ACE as source. |
| Failure cannot change ACE | No mutation route exists in client code or configuration; cancellation, decoding failure, and crashes only discard in-memory state. |
| Fails closed | Decode and validation complete before replacing the visible release; invalid/partial responses show a generic unavailable state. |
| Does not persist implicitly | Ephemeral URL session, disabled URL cache and cookie storage, no scene restoration of sensitive state, and no release data in logs/widgets/notifications.[E5] |
| Rejects stale completions | Each request has a generation identity; results from a cancelled, superseded, or signed-out client session are discarded. |

**Decision — recommended:** Use protocol boundaries for transport and repository seams, but avoid a framework, global dependency container, or elaborate domain layer.

### Sift-KG and OpenViking boundary

**Confirmed boundary:** Sift-KG and OpenViking are not prerequisites for this application. Sift-KG may supply server-side proposals and an exploratory graph only; OpenViking may supply server-side context search only after its own gates pass. The iOS application calls neither provider, stores no provider credential, presents no provider screen, and cannot be blocked by provider completion. Any provider-backed mobile capability requires a separate ACE API specification and approval.

## 6. External Template Review

| Source | Owner / URL | Version/applicability | Accessed | Useful pattern | Unneeded features | Licence | Dependency/tool impact | Decision |
|---|---|---|---|---|---|---|---|---|
| Xcode iOS App template with SwiftUI | Apple [E1][E4] | Xcode 26 family | 23 Aug 2026 | Minimal app lifecycle, SwiftUI and test targets | Persistence template options and non-fictional sample data | Apple Xcode terms; Legal confirmation before distribution | Xcode only; no third-party runtime | **use** |
| Develop in Swift | Apple [E19] | Current tutorial collection; verify with installed Xcode | 23 Aug 2026 | Introductory SwiftUI composition and state | Teaching scaffolding and tutorial domain | Apple site/sample terms; attached sample terms control reuse | Reference only; no runtime dependency | **reference** |
| Scrumdinger | Apple [E21] | Exact current compatibility not conclusively confirmed | 23 Aug 2026 | Small SwiftUI navigation/state example | Meeting, audio, history, and tutorial-domain features | Attached Apple sample terms require local Legal review | Reference only; **outdated/compatibility warning** | **reference** |
| Food Truck | Apple [E22] | Current sample catalogue; exact Xcode compatibility must be checked before use | 23 Aug 2026 | Adaptive iPhone/iPad navigation and layout | Multiplatform, ordering, location, and business flows | Attached Apple sample terms require local Legal review | Reference only; sample must not become a dependency | **reference** |
| Keychain guidance/examples | Apple [E7] | Current Security documentation | 23 Aug 2026 | Internet-password lifecycle and deletion | Synchronisation/sharing not required | Apple documentation/sample terms | Security framework only; Keychain implementation is selected and needs Security approval | **use** |
| Swift Testing and XCTest UI | Apple [E10][E11] | Xcode 26 context | 23 Aug 2026 | Parameterised model/state tests and accessibility-backed UI journeys | Broad performance/load suites outside this slice | Apple toolchain terms | Built into Xcode; no package | **use** |
| Swift OpenAPI Generator | Apple / Swift project [E12][E13] | `1.13.0` current release | 23 Aug 2026 | Typed generation from reviewed OpenAPI | Generator/runtime/transport packages for one endpoint | Apache-2.0 | SwiftPM build plugin, packages, and generated-source review | **defer** |
| XcodeGen | yonaskolb [E16] | `2.46.0` current release | 24 Aug 2026 | Reproducible YAML project generation | Separate generator/configuration for a small app | MIT | Installed generation tool and generated project workflow | **defer** |
| Tuist | Tuist [E17] | Exact current CLI version unknown because release channels were ambiguous | 23 Aug 2026 | Larger modular workspace generation | Server, cache, module, and tool lifecycle | MIT | CLI/configuration and possible service concerns | **reject** |
| Composable Architecture | Point-Free [E18] | Exact current release unknown; 1.26.0/1.26.1 results conflicted | 23 Aug 2026 | Explicit state/effect/test patterns | Framework concepts for three screens and one endpoint | MIT | Swift package and ongoing upgrade surface | **reject** |

**Decision — recommended:** Start from Apple’s template and use samples as pattern references only. Do not import tutorial architecture wholesale.

## 7. API Contract And Client Decision

### Contract

- Method/path: `GET /client/api/v1/release/current`.
- Success must be HTTP `200` with `application/json`.
- Existing stateless HTTP Basic authentication on the inspected client release route and G0 remain unchanged. Missing/invalid credentials return HTTP `403`; missing server configuration returns HTTP `503` through client authentication, and G0 rejection returns HTTP `503` through the client route.[C1]
- Action target dates are `YYYY-MM-DD`; publication times are UTC `YYYY-MM-DDTHH:MM:SSZ`; response actions preserve server order derived from `release_entry_id`.[C2][C3]
- Required top-level fields are `engagement_name` (`String`), `review_status` (`String`), `release_version` (`Int`), and `published_at` (`String`).
- `conclusion` is the only optional field. When present, its `title`, `summary`, and `evidence_reference_id` fields are required strings.
- `actions` is always an array. Each action requires string values for `description`, `owner`, `target_date`, and `status`.
- Existing empty responses use required sentinel values: `Release unavailable` or `Engagement not found`, empty strings, release version `0`, `conclusion: null`, and an empty `actions` array.
- The compatibility records and exclusion of internal identifiers remain unchanged.
- No mobile-specific backend route, schema, migration, trigger, or response extension is approved.
- Evidence references must remain inert text. The app must not open them as URLs or file paths. An explicit copy button can copy an approved visible value after Security approves the clipboard policy.
- Published and target dates must preserve the API’s meaning. Parsing, time-zone assumptions, and locale formatting require confirmation from the sanitised contract; the client must not silently reinterpret a date-only value as a timestamp.

### Client approaches

| Item | Hand-written URLSession/Codable | Swift OpenAPI Generator |
|---|---|---|
| Benefit for one endpoint | High clarity; little code; direct mock-transport seam. | Contract-generated models/client reduce drift as API breadth grows. |
| Dependencies | Apple Foundation only.[E5] | Generator plugin, OpenAPI runtime, and URLSession transport packages.[E12][E13] |
| Build effect | Normal compilation. | Build-tool plugin/code generation and generated-source diagnostics. |
| Contract source | Manually model the reviewed response. | Requires a stable, reviewed OpenAPI document and generation policy. |
| Maintenance | Manual updates for contract changes. | Generator/package/version updates and generated-code review policy. |

**Decision — recommended:** Use a small `URLSession` client with hand-written `Codable` models for Phase 1.

**Decision — recommended:** Defer Swift OpenAPI Generator until endpoint count or contract churn makes generation materially cheaper than manual models. A later adoption decision must pin versions, review generated output, and confirm the FastAPI OpenAPI document exposes no internal routes or schemas to the client target.

## 8. Authentication And Credential Decision

**Confirmed fact:** The inspected ACE client release route uses stateless HTTP Basic authentication for its requests. Expected credentials come from environment configuration. The inspected route does not create a cookie session or server-side session-expiry process. Missing or invalid credentials return HTTP `403`.[C1]

The iOS application must construct the standard Basic authorization value only in memory. It must send it with the first request to the approved HTTPS origin. The current endpoint returns `403` instead of a `401` Basic challenge when credentials are absent. Therefore, challenge-driven submission cannot work without a blocked server-authentication change. The application must not log the authorization value, persist it in URL credential storage, or introduce a token, identity provider, or new sign-in flow.[C1][E6]

| Criterion | Session-only memory | Validated Internet password in Keychain |
|---|---|---|
| User experience | Re-entry after launch/sign-out; simplest and explicit. | Faster repeat access. |
| Device-loss risk | Credential disappears when process/session ends. | Credential may remain available on a lost unlocked device; accessibility/synchronisation class matters. |
| Sign-out | Clear variables, cancel tasks, discard release; no server logout exists. | Also delete the exact Keychain item and clear memory; no server logout exists. |
| Error recovery | Re-enter credentials. | On rejection, remove/replace only after user action; avoid loops. |
| App switcher/screenshots | Hide credentials and release content in the app-switcher preview. Normal iPhone screenshots remain allowed. | Same while UI is visible. |
| Logging | Redact all auth values and challenge details. | Same; never log Keychain query values. |
| Testability | Inject fictional credentials directly into mock transport. | Wrap Security APIs; integration behaviour requires device/simulator checks. |

Apple documents Keychain as the protected store for user secrets and `URLSession` as the first-party networking API.[E5][E7]

**Decision — user selected:** Store the existing Basic credentials in iOS Keychain so the user remains signed in between app launches. Load them into memory only when required for an approved request. No server session is created.[C1][E7]

**Decision — recommended:** On sign-out, HTTP `403`, or an authentication-context change, cancel requests and immediately clear the visible release, the exact Keychain credential, in-memory authorization values, and view-model history. On HTTP `503`, clear the visible release and cancel requests, but retain the Keychain credential unless Security approves a stricter rule. A late response from an old client session must never repopulate the screen. This is client-side clearing, not server-session expiry.[C1]

**Decision — needs human decision (Security):** Approve Keychain storage as device-only, available only while the device is unlocked, and excluded from synchronisation. Approve backup behaviour, deletion, migration, and recovery.

**Decision — blocked:** Plain-text storage, source-code secrets, `UserDefaults` passwords, a new token/identity provider, or a new sign-in method.

## 9. Network And Environment Plan

| Environment | Plan | Data rule |
|---|---|---|
| Unit tests | Mock transport; no socket. | Fictional fixtures only. |
| Xcode previews | Inject deterministic view states. | Fictional fixtures only; no credentials. |
| Simulator | Local ACE server only after separate implementation approval and baseline confirmation. | Fictional ACE records. |
| Physical development device | Approved private Preview or approved local endpoint only after separate pilot approval. | Fictional pilot records. |

**Decision — user selected:** Connect only to one fixed, private, non-Production test server. Use fictional information only. Users cannot change the server address. Security and ACE operations must approve the exact address and certificate before device testing.

### Network controls

- **HTTPS/ATS:** Use HTTPS with valid hostname and certificate. ATS enforces secure transport for `URLSession`; do not add broad ATS exceptions.[E5][E6]
- **Session configuration:** Use an ephemeral `URLSessionConfiguration`; set `urlCache = nil`, disable cookie storage, avoid shared URL credential storage, and use a cache policy that reloads from origin. The inspected client release route does not use a cookie session.[C1][E5]
- **Local server:** If simulator host bridging or physical-device local-network discovery/access triggers platform privacy requirements, add only the narrowly justified local-network declaration and explanatory text. Do not ship a broad release exception.
- **Timeouts:** Define finite request/resource timeouts in the specification; preliminary values: 15-second request and 30-second resource ceiling, subject to local network evidence.
- **Cancellation:** Cancel in-flight work when the user signs out or initiates a newer refresh; ignore stale completions.
- **Retry:** No automatic retry for authentication, G0, certificate, hostname, or invalid-response failures. Allow one user-triggered retry for timeout/no-network/server-unavailable states. Avoid retry storms.
- **Trust failures:** Never offer “continue anyway.” Show a generic unavailable state and retain no partial release.
- **Certificate pinning:** Do not add certificate/public-key pinning by default. Standard platform trust plus controlled hostnames is the smaller design; pinning needs a separate rotation and outage-recovery specification.
- **Configuration:** Build configuration selects an allow-listed non-Production base URL. The UI must not accept arbitrary base URLs.
- **Redirects:** Reject cross-host redirects and any HTTPS-to-HTTP downgrade. Confirm whether same-host redirects are expected before allowing them.
- **Backgrounding:** Do not initiate background refresh. Cancel or suspend foreground requests according to the approved session policy and cover sensitive UI before the application-switcher snapshot is captured.
- **Production:** No Production URL is proposed or approved.

**Decision — recommended:** Send Basic authorization pre-emptively with the first request to the approved HTTPS origin. The current endpoint does not provide a `401` Basic challenge.[C1]

**Decision — needs human decision (Security/ACE owner):** Approve the Preview hostname, certificate chain, physical-device local-network permission, and final timeout values. The authentication scheme remains unchanged.[C1]

## 10. Screen And State Matrix

### Information structure

1. **Credential entry/sign-in:** server identity is configured, not user-editable; fields match existing authentication only.
2. **Current release:** engagement, review/release metadata, conclusion, ordered actions, refresh, and generic error/empty states.
3. **Settings/sign-out:** include only if needed for credential/session clearing and non-sensitive build/environment identification.

| Condition | Visible result | Data/control behaviour |
|---|---|---|
| Valid fictional published release | Show all approved release fields. | Replace UI atomically after full decode/validation. |
| No published release | `No current release is available.` | No stale prior release. |
| Missing Engagement | `No current release is available.` | Do not expose configuration details. |
| No conclusion | Existing empty conclusion state. | Do not fabricate text. |
| No actions | Existing empty action state. | Do not hide conclusion. |
| Several actions | Display in API order. | No client sorting; server order is derived from `release_entry_id`.[C3] |
| Missing credentials | Request credentials without configuration details. | No request until required values exist. |
| Invalid credentials | Generic access failure. | Delete the Keychain credential, clear the active field, and show no authentication detail. |
| Missing server configuration | Generic unavailable state. | No editable base URL. |
| G0 rejection | Generic unavailable state. | Clear visible release data. Retain session credentials unless Security requires clearing. Do not identify G0 or its reason. |
| No network | Explain that ACE could not be reached. | Safe user-triggered retry. |
| Timeout | Explain timeout and offer safe retry. | Cancel prior request before retry. |
| Invalid response | Generic unavailable state. | Fail closed; show no partial/stale release. |
| Refresh in progress | Progress indicator plus accessible status. | Disable duplicate refresh; honour Reduce Motion. |
| Sign-out | Return to credential entry. | Cancel request and clear credential/release state. |
| Previously accepted credentials later return `403` | Generic access failure, then credential entry. | Delete the Keychain credential, clear visible release and memory, and reject late responses. No server session expiry is implied.[C1] |
| App enters background | Cover sensitive release content if Security requires it. | No background refresh or state restoration of release data. |
| Redirect to another host or clear text | Generic unavailable state. | Reject redirect; disclose no destination or trust detail. |

Do not display internal identifiers, HTTP traces, stack traces, host configuration, raw response text, authentication details, G0 internals, approval attribution, withdrawal details, or provider information. Colour must never be the only state signal.

## 11. Accessibility Plan

Apple’s accessibility guidance covers VoiceOver descriptions, larger text/Dynamic Type, and contrast; UI automation can perform accessibility audits but does not replace manual VoiceOver use.[E8][E9][E23]

### Acceptance criteria

- Every control and non-decorative image has a concise VoiceOver label, value, hint only where useful, and correct trait.
- Reading order follows: screen title, release identity/status, published time, conclusion, actions, controls.
- Dynamic Type supports all accessibility sizes without clipping, overlap, hidden actions, or horizontal text scrolling; long fields wrap.
- Text and meaningful icons meet current Apple contrast guidance in light and dark appearance.[E8]
- Status uses text and semantics in addition to colour or iconography.
- Reduce Motion removes nonessential animation; loading remains understandable without motion.
- Bold Text does not clip or obscure content.
- Portrait and landscape work on the smallest supported iPhone in the approved device matrix.
- iPad is outside Phase 1 and requires a separate scope decision.
- Errors receive appropriate focus/announcement without repeatedly interrupting VoiceOver.
- Dates and statuses have natural spoken forms. Each approved copy button has a clear VoiceOver label and confirmation.
- Automated accessibility audits pass for the main screens, followed by manual VoiceOver and large-text checks on simulator and the approved physical pilot device.[E23]

**Decision — user selected:** Support iPhone only with a minimum version of iOS 26. Test portrait and landscape on the approved iPhone device matrix. iPad support is outside Phase 1.

## 12. Security And Privacy Review

| Threat | Control | Evidence required | Residual risk | Owner |
|---|---|---|---|---|
| Credential exposure | Keychain storage; device-only and synchronisation off after Security approval; secure fields; no logs | Log review, Keychain lifecycle tests, UI inspection | Compromised/unlocked device | Security |
| Transport interception | HTTPS, ATS, valid hostname/certificate, no bypass | ATS config and negative trust tests | Compromised trust store/server | Security / ACE ops |
| Cross-Engagement information | Existing ACE auth/G0; no user-selected engagement ID; endpoint only returns authorised current release | Fictional cross-engagement denial fixture and ACE compatibility evidence | Server-side authorisation defect | ACE owner |
| Stale/partial response | Atomic decode/validation; clear on auth/context errors; no persistent cache | Invalid/truncated/race tests | User may remember old information | App owner |
| Sensitive logging | Structured allow-list logs; no bodies, headers, credentials, names, or evidence references | Debug/release log capture review | OS/network metadata outside app | App owner / Security |
| Clipboard exposure | Explicit copy buttons only for Security-approved visible fields; never copy credentials or technical details | UI action inventory and clipboard tests | Other applications or devices can read copied data | Product / Security |
| App-switcher snapshots | Always cover release content before background snapshots; clear content after sign-out or credential rejection | Screenshot evidence | OS timing window | Security |
| Backup/local persistence | Ephemeral network session, no response cache, cookie store, shared URL credentials, or release-state restoration; approved Keychain storage only | File/container, cache, Keychain, and relaunch inspection in later tests | OS-managed transient memory/snapshots | Security |
| Screenshots | Allow normal iPhone screenshots; do not block, detect, warn about, upload, or share them automatically | Pilot policy and UI review | Users control captured images outside the app | User / Security |
| Debug config in release | Separate configuration, allow-listed base URL, no debug menus/secrets | Build-setting and binary/config review | Mis-signing or pipeline error | App owner / Release owner |
| Base URL substitution | Compile-time/config-file allow-list; no editable URL; signed release configuration | Negative configuration tests | Compromised build pipeline | Release owner |
| Provider credential exposure | No provider SDK, endpoint, secret, screen, or configuration | Dependency/string/config inspection | Future scope creep | ACE owner / Security |
| Redirect/base-host escape | Allow-listed HTTPS host; reject cross-host and downgrade redirects | Redirect tests and request capture | Approved host compromise | Security / ACE ops |
| Data shown after credential rejection | Clear release atomically on HTTP `403`, sign-out, G0 HTTP `503`, or context change; reject late responses | Race, rejection, background, and relaunch tests | Brief display before a new request detects rejection | App owner / Security |

**Decision — needs human decision:** Security must approve the selected Keychain policy, copied fields, clipboard handling, physical-device transport, base URL management, local-network permission, and release logging before a pilot. The app-switcher cover is required.

**Decision — user selected:** Allow normal iPhone screenshots. Hide release content only in the app-switcher preview. Add explicit copy buttons for visible release information. Never copy credentials or technical details. Evidence references remain text and must not open as URLs or files.

**Decision — user selected:** Classify all Phase 1 release information as `FICTIONAL PILOT — CONTROLLED`. Real client information remains prohibited and requires a new classification and separate approval.

**Decision — needs human decision:** Legal must review any copied sample code licence and eventual distribution/privacy statements. This report gives no legal conclusion.

## 13. Test And Evidence Plan

### Layers

1. **Model decoding (Swift Testing):** exact valid fixture, missing optional values, missing required values, invalid types, invalid dates, extra fields, truncated JSON, empty arrays, and action-order preservation.
2. **API client (mock transport):** exact HTTPS GET path, correctly formed in-memory HTTP Basic authorization, no leaked authorization, content type/status handling, timeout, cancellation, no network, certificate/hostname mapping, HTTP `403` generic access failure, HTTP `503` generic unavailable, and invalid body.[C1]
3. **Write-proof test:** fail the test on any method other than GET and assert exactly the versioned current-release path is requested.
4. **Persistence-boundary tests:** verify ephemeral networking, disabled response cache and cookies, approved Keychain storage, sign-in after relaunch, Keychain deletion after sign-out and HTTP `403`, Keychain retention after HTTP `503`, no release-state restoration, no background refresh, and no sensitive logs.
5. **View-model state:** idle/loading/success/empty/auth/unavailable/timeout/invalid-response, stale-response race, retry, later HTTP `403`, background/foreground transition, and sign-out clearing.
6. **SwiftUI view checks:** fictional previews for every state and large accessibility sizes; snapshot tooling is not required unless separately approved.
7. **XCTest UI:** credential entry → successful current release → refresh → sign-out; invalid credential; HTTP `503` unavailable; timeout/retry; empty conclusion/actions; later HTTP `403` while content is visible; background cover and relaunch clearing.
8. **Accessibility:** automated audit plus manual VoiceOver order, Dynamic Type, Bold Text, Reduce Motion, contrast, light/dark, orientation, and keyboard checks where iPad applies.[E23]
9. **Simulator:** approved local ACE environment using fictional records only.
10. **Physical-device pilot:** one approved device/environment after separate approval; no Production.
11. **Server compatibility suite — remains ACE-owned and separate from the mobile target:** preserve the existing HTTP `200`, `application/json`, `599`-byte, SHA-256 `5e19bc98c09286a2eb8181650462cfb5ae6952eb342da080643d54a8ab6856af`, and HTML compatibility records against controlled target `6b0160befc9191dbccd527bdd385b891782ddad8`. The iOS test target must not recreate or replace this byte-hash suite.
12. **Mobile semantic suite:** decode all required top-level and nested fields; accept only optional `conclusion`; require an `actions` array; parse action dates as `YYYY-MM-DD`; parse publication times as UTC `YYYY-MM-DDTHH:MM:SSZ`; preserve API action order; map HTTP `403` and `503` correctly; and reject invalid content type/body.[C1][C2][C3] This suite must not assert response byte count or SHA-256 because mobile correctness is semantic, while exact byte/hash compatibility is server-owned.
13. **Redirect/trust tests:** reject cross-host and downgrade redirects, untrusted certificates, and hostname mismatches without exposing technical detail or offering bypass.

### Required fixtures

Use fictional names such as **“Harbour Lantern Review”**, fictional people such as **“Casey Example”**, and non-real evidence references. Include success, no release, missing engagement, no conclusion, no actions, several actions, missing/invalid credentials, G0 rejection, no network, timeout, server unavailable, malformed JSON, wrong content type, and partial response.

### Pilot evidence package

- Controlled baseline hash confirmation from local Codex.
- Complete implementation diff inspected locally.
- Raw unit/UI test output with counts and failures.
- Request-capture evidence proving only GET to the approved endpoint.
- Raw **server-owned** compatibility output for status/content type/size/SHA-256, supplied from the controlled ACE verification rather than generated by the iOS test target.
- Separate **mobile-owned** semantic-contract output covering field decoding, optionality, HTTP `403`/`503` mapping, `YYYY-MM-DD` action dates, UTC publication timestamps, content type, and preservation of API action order.[C1][C2][C3]
- Persistence inspection showing only the approved Keychain credential. Confirm no response cache, cookie store, shared URL credential entry, restored release state, or sensitive logs after background, termination, and relaunch.
- Accessibility audit output and manual checklist.
- Simulator screenshots for success, empty, generic failure, and large text using fictional data.
- Release configuration review showing no Production URL, debug menu, provider SDK, analytics, crash reporter, database, or embedded credential.
- Physical-device pilot record after separate approval.

## 14. Proposed File Structure

This is a **proposal only**; no project or file was created.

```text
ACEClientApp/
├── ACEClientApp.xcodeproj/
├── Configuration/
│   ├── Debug.xcconfig
│   ├── Preview.xcconfig
│   └── Release.xcconfig
├── ACEClientApp/
│   ├── App/
│   │   ├── ACEClientApp.swift
│   │   └── AppConfiguration.swift
│   ├── Domain/
│   │   ├── ClientRelease.swift
│   │   └── ReleaseState.swift
│   ├── Networking/
│   │   ├── ACEClient.swift
│   │   ├── HTTPTransport.swift
│   │   ├── URLSessionTransport.swift
│   │   └── ClientReleaseResponse.swift
│   ├── Features/
│   │   ├── SignIn/
│   │   │   ├── SignInView.swift
│   │   │   └── SignInViewModel.swift
│   │   ├── CurrentRelease/
│   │   │   ├── CurrentReleaseView.swift
│   │   │   ├── CurrentReleaseViewModel.swift
│   │   │   ├── ReleaseSummaryView.swift
│   │   │   └── ActionRow.swift
│   │   └── Settings/
│   │       └── SettingsView.swift
│   ├── Security/
│   │   ├── BasicAuthorization.swift
│   │   ├── SessionCredentialStore.swift
│   │   └── KeychainCredentialStore.swift
│   ├── Support/
│   │   ├── Accessibility.swift
│   │   └── RedactedLogger.swift
│   ├── PreviewContent/
│   │   └── FictionalReleaseFixtures.swift
│   ├── Assets.xcassets/
│   └── Info.plist
├── ACEClientAppTests/
│   ├── Fixtures/
│   │   └── FictionalReleaseJSON.swift
│   ├── ClientReleaseDecodingTests.swift
│   ├── ACEClientTests.swift
│   ├── CurrentReleaseViewModelTests.swift
│   ├── NoWriteRequestTests.swift
│   ├── ApprovedPersistenceBoundaryTests.swift
│   └── CredentialRejectionRaceTests.swift
└── ACEClientAppUITests/
    ├── MainJourneyUITests.swift
    └── AccessibilityUITests.swift
```

**Decision — user selected:** Include `KeychainCredentialStore.swift`. Implement it only after Security approves the exact Keychain policy. Do not add database, provider, analytics, crash-reporting, OpenAPI-generated, or third-party architecture folders.

## 15. Bounded Implementation Stages

Each stage belongs to a fresh local Codex task invoking `$sol-advisor:orchestration`; this report does not begin that work.

1. **Gate and contract confirmation:** verify controlled hash, inspect the sanitised specification, confirm stateless pre-emptive HTTP Basic behaviour, required and optional fields, date formats, ordering, empty-state sentinels, and fictional fixtures. Stop on mismatch.[C1][C2][C3]
2. **Project skeleton:** current Xcode SwiftUI template, approved bundle/deployment/device settings, no third-party packages.
3. **Models and transport:** hand-written `Codable`, mockable `URLSession` transport, GET-only endpoint, finite timeout/cancellation, redacted errors.
4. **Keychain-backed authentication:** use only the existing stateless HTTP Basic behaviour. Load credentials from the approved Keychain item for requests. Add no cookie or server session. Delete the Keychain item during sign-out and after HTTP `403`.[C1][E7]
5. **State and UI:** three-screen maximum, atomic state transitions, complete matrix, fictional previews.
6. **Accessibility/adaptation:** VoiceOver, Dynamic Type, contrast, system settings, orientation, approved iPad behaviour.
7. **Automated verification with the installed Build iOS Apps capabilities:** use `ios-debugger-agent` for build/run checks and `ios-simulator-browser` for simulator visual evidence. Keep server byte/hash compatibility evidence separate from mobile semantic tests.
8. **Local review:** the primary session inspects the complete diff and reruns relevant verification. Use `swiftui-ui-patterns` for SwiftUI structure and run `swiftui-performance-audit` only after the main flow works and only if locally justified. App Intents, Liquid Glass, and memory analysis are not required for this slice.
9. **Pilot gate:** Security/auditor/user approval, approved private environment, one physical device, no Production/TestFlight/App Store.

## 16. Estimate And Hard Limit

### Investigation

- Hard limit: **four hours**.
- Output: this single report.
- No builds, tests, installations, downloads, sample runs, scans, or implementation were performed.

### Later implementation estimate (not approval)

| Stage | Indicative effort |
|---|---:|
| Contract/auth confirmation and fictional fixture review | 0.5–1 day |
| Native skeleton, models, GET-only client, session auth | 1–2 days |
| UI/state/accessibility implementation | 1.5–2.5 days |
| Automated tests and compatibility evidence | 1.5–2.5 days |
| Review corrections and approved device pilot | 1–2 days |
| **Total** | **5.5–10 working days** |

The range excludes API/auth changes, Production, TestFlight/App Store, new identity, iPad-specific redesign, provider features, and legal/security review lead time. Keychain implementation is inside the estimate. Waiting for its Security approval is outside active effort.

**Decision — user selected — implementation hard limit:** Cap the later bounded implementation at **10 working days of active implementation and verification effort** through the local pilot gate. If the approved slice cannot meet its acceptance criteria within that limit, stop and return a variance report; do not add dependencies, weaken controls, change authentication, widen the API, or expand product scope to recover schedule.

**Decision — user selected:** The 10-working-day implementation hard limit and variance-stop rule are approved. Calendar waiting time for Security, Legal, auditor, certificate, device, or environment decisions is excluded, but blocked time must be reported.

## 17. Open Decisions

| Decision | Owner | Required before |
|---|---|---|
| Approve read-only release viewer as the Phase 1 product | Auditor / user | Specification acceptance |
| Confirm fixed remote target and Phase 6B2 contract | Local Codex / ACE owner | Any implementation |
| Approve client-side sign-out clearing and the HTTP `503` credential-retention rule | ACE owner / Security | Authentication and network design freeze |
| Approve the exact Keychain device, synchronisation, backup, deletion, migration, and recovery policy | Security | Authentication implementation |
| Approve private Preview/local hostname, trust chain, and local-network handling | Security / ACE ops | Device networking |
| Approve clipboard handling for visible release fields and the app-switcher cover implementation | Security / Legal | Pilot |
| Confirm date-only versus timestamp semantics and display time zone | ACE owner / Product | Model and UI acceptance |
| Confirm timeout values and retry wording | ACE ops / Product | UI acceptance |
| Review sample-code and future distribution licences | Legal | Any copying/distribution |
| Approve fictional physical-device pilot | Auditor / Security / user | Device testing |
| Approve final iOS specification | User | Implementation task |

## 18. Stop Conditions

Stop and report before:

- Any controlled-target mismatch.
- Requesting or receiving real client, personal, Engagement, source-evidence, audit, or credential information.
- Repository/Git-history upload or external transmission of source, database, environment, temporary, or audit files.
- Installation, cloning, downloading, or running a tool/sample.
- Project or code creation, dependency addition, build, test, scan, deployment, account creation, or hosted demonstration.
- Any write endpoint, database/provider connection, new auth method, offline release persistence, analytics/tracking/crash service, paid provider, or Production URL.
- Sift-KG/OpenViking work or mobile provider screens.
- TestFlight/App Store submission.
- Architecture/security boundary change without a separate decision request.
- A legal conclusion.
- More than two failed attempts to confirm one material technical fact; record it as unknown.
- Exceeding the investigation hard limit.

## 19. Pilot Readiness

### Gate checklist

- [ ] Controlled target equals `6b0160befc9191dbccd527bdd385b891782ddad8`.
- [ ] Auditor/user approve the bounded product and final specification.
- [x] Native SwiftUI with Apple frameworks only is approved; no third-party runtime package is allowed.
- [ ] Security approves credential, transport, storage, app-switcher, clipboard, logging, and device policies.
- [ ] Legal reviews applicable sample/distribution licences where needed.
- [ ] Existing authentication and G0 behaviour are documented without changing them.
- [x] The inspected client release route’s stateless HTTP Basic behaviour, absence of route-created cookie/server sessions, HTTP `403`, HTTP `503`, date formats, and server action ordering are confirmed against the controlled target.[C1][C2][C3]
- [x] Pre-emptive Basic submission is selected because the endpoint does not provide a `401` Basic challenge.[C1]
- [ ] Security approves client-side sign-out clearing and the HTTP `503` credential-retention rule.
- [ ] The exact private non-Production address, certificate, and fictional data set are approved and available.
- [x] Product policy allows normal iPhone screenshots, requires an app-switcher cover, and requires copy buttons for visible release information.
- [x] Phase 1 release information is classified as `FICTIONAL PILOT — CONTROLLED`; real client information remains prohibited.
- [ ] Security approves clipboard handling and the app-switcher cover implementation.
- [ ] Complete state matrix and accessibility criteria pass.
- [ ] Raw mobile semantic/UI/accessibility test evidence passes.
- [ ] Separate server-owned byte/hash compatibility evidence remains unchanged.
- [ ] GET-only request evidence passes; no writes are possible.
- [ ] Persistence evidence confirms approved Keychain behaviour and no cache, restored release state, unapproved storage, background refresh, or sensitive logging.
- [ ] HTTP `403`/sign-out/race evidence confirms stale or late responses cannot repopulate cleared content.
- [ ] Complete local diff/configuration review finds no database, provider credential/SDK, analytics, crash reporting, offline release store, debug release setting, or Production URL.
- [ ] One physical-device pilot has separate approval.

**Current readiness — blocked:** Ready for the remaining specification decisions and final approval, but not ready for implementation or pilot. Security decisions, the exact test-server address and certificate, and final user approval remain open.

## 20. Recommended Next Action

**Decision — recommended:** Local Codex and the auditor should retain the confirmed API facts and user selections. They should resolve the exact Keychain policy, clipboard handling, and the exact private test-server address and certificate. They should then produce the final bounded iOS specification for Pocock review and user approval.[C1][C2][C3]

Only after that approval should a **fresh local Codex task** invoke `$sol-advisor:orchestration` and begin Stage 1. No implementation is authorised by this report.

---

## External Evidence References

- **[C1]** Local Codex controlled-target review, fixed target `6b0160befc9191dbccd527bdd385b891782ddad8`: `sqe/src/ace/workbench/client_auth.py`, line 18, confirms the inspected client route’s stateless HTTP Basic authentication, environment-configured expected credentials, no route-created cookie/server session, HTTP `403` for missing/invalid credentials, and HTTP `503` for missing server configuration; `sqe/src/ace/workbench/client_routes.py` confirms G0 rejection returns HTTP `503`. Controlled local references supplied by Codex: `/C:/tmp/sqe-phase6b2-controlled-target/sqe/src/ace/workbench/client_auth.py:18` and `/C:/tmp/sqe-phase6b2-controlled-target/sqe/src/ace/workbench/client_routes.py` (review supplied 23 Aug 2026).
- **[C2]** Local Codex controlled-target review, fixed target `6b0160befc9191dbccd527bdd385b891782ddad8`: `sqe/src/ace/workbench/client_release_projection.py` confirms action-date validation as `YYYY-MM-DD`; `sqe/src/ace/workbench/client_release_service.py` confirms publication-time validation as UTC `YYYY-MM-DDTHH:MM:SSZ`. Controlled local references supplied by Codex: `/C:/tmp/sqe-phase6b2-controlled-target/sqe/src/ace/workbench/client_release_projection.py` and `/C:/tmp/sqe-phase6b2-controlled-target/sqe/src/ace/workbench/client_release_service.py` (review supplied 23 Aug 2026).
- **[C3]** Local Codex controlled-target review, `sqe/src/ace/workbench/release_storage.py`, line 31, fixed target `6b0160befc9191dbccd527bdd385b891782ddad8`; confirms release entries use `release_entry_id` order. Controlled local reference supplied by Codex: `/C:/tmp/sqe-phase6b2-controlled-target/sqe/src/ace/workbench/release_storage.py:31` (review supplied 23 Aug 2026).

- **[E1]** Apple, “Xcode 26 Release Notes,” https://developer.apple.com/documentation/xcode-release-notes/xcode-26-release-notes (accessed 23 Aug 2026).
- **[E2]** Apple, “Xcode — Support / supported SDKs and deployment targets,” https://developer.apple.com/support/xcode/ (accessed 23 Aug 2026).
- **[E3]** Apple, “SwiftUI,” https://developer.apple.com/swiftui/ (accessed 23 Aug 2026).
- **[E4]** Apple, “Creating an Xcode project for an app,” https://developer.apple.com/documentation/xcode/creating-an-xcode-project-for-an-app (accessed 23 Aug 2026).
- **[E5]** Apple, “URLSession,” https://developer.apple.com/documentation/foundation/urlsession (accessed 23 Aug 2026).
- **[E6]** Apple, “Preventing Insecure Network Connections,” https://developer.apple.com/documentation/security/preventing-insecure-network-connections (accessed 23 Aug 2026).
- **[E7]** Apple, “Using the Keychain to Manage User Secrets,” https://developer.apple.com/documentation/security/using-the-keychain-to-manage-user-secrets (accessed 23 Aug 2026).
- **[E8]** Apple, “Human Interface Guidelines — Accessibility,” https://developer.apple.com/design/human-interface-guidelines/accessibility (accessed 23 Aug 2026).
- **[E9]** Apple, “Human Interface Guidelines — VoiceOver,” https://developer.apple.com/design/human-interface-guidelines/voiceover (accessed 23 Aug 2026).
- **[E10]** Apple, “Testing,” https://developer.apple.com/documentation/xcode/testing (accessed 23 Aug 2026).
- **[E11]** Apple, “Adding tests to your Xcode project,” https://developer.apple.com/documentation/xcode/adding-tests-to-your-xcode-project (accessed 23 Aug 2026).
- **[E12]** Apple, “swift-openapi-generator releases,” current release `1.13.0`, https://github.com/apple/swift-openapi-generator/releases (accessed 23 Aug 2026).
- **[E13]** Swift.org, “Introducing Swift OpenAPI Generator,” https://swift.org/blog/introducing-swift-openapi-generator/ (accessed 23 Aug 2026).
- **[E14]** Expo, “Expo SDK reference — latest,” https://docs.expo.dev/versions/latest/ (accessed 23 Aug 2026).
- **[E15]** Expo, “Apple SDK minimum requirements,” https://expo.dev/blog/apple-sdk-minimum-requirements (accessed 23 Aug 2026).
- **[E16]** XcodeGen maintainers, “XcodeGen,” current release `2.46.0`, https://github.com/yonaskolb/XcodeGen/releases and MIT licence https://github.com/yonaskolb/XcodeGen/blob/master/LICENSE (accessed 24 Aug 2026).
- **[E17]** Tuist maintainers, “Tuist releases,” https://github.com/tuist/tuist/releases and MIT licence https://github.com/tuist/tuist/blob/main/LICENSE.md (accessed 23 Aug 2026).
- **[E18]** Point-Free, “The Composable Architecture,” https://github.com/pointfreeco/swift-composable-architecture and releases https://github.com/pointfreeco/swift-composable-architecture/releases (accessed 23 Aug 2026).
- **[E19]** Apple, “Develop in Swift — Hello, SwiftUI,” https://developer.apple.com/tutorials/develop-in-swift/hello-swiftui (accessed 23 Aug 2026).
- **[E20]** Apple, “Terms of Use,” https://www.apple.com/legal/internet-services/terms/site.html (accessed 23 Aug 2026); exact sample-attached licence remains subject to local Legal review.
- **[E21]** Apple, “SwiftUI tutorials / sample apps,” https://developer.apple.com/tutorials/swiftui and https://developer.apple.com/tutorials/sample-apps (accessed 23 Aug 2026); exact current Scrumdinger compatibility/version was not conclusively confirmed.
- **[E22]** Apple, “Sample Code,” https://developer.apple.com/documentation/samplecode (accessed 23 Aug 2026); Food Truck is used as an adaptive-layout reference only.
- **[E23]** Apple, “Performing accessibility audits for your app,” https://developer.apple.com/documentation/accessibility/performing-accessibility-audits-for-your-app (accessed 23 Aug 2026).
