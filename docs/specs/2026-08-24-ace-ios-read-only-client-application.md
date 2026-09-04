# ACE iOS Read-Only Client Application

## Document Status

Status: Draft Revised From Security Findings

Date: 24 August 2026

Controlled baseline branch: `origin/codex/ace-sprint-1`

Controlled baseline commit: `6b0160befc9191dbccd527bdd385b891782ddad8`

Phase 6B2 implementation merge: `a1d52c6148b64106ed1a4516aec8e72aea4ef666`

Linear implementation issue: [MCX-15](https://linear.app/mcxi-co/issue/MCX-15/sqe-implement-ace-ios-read-only-client-application)

This specification does not authorise implementation.

Pocock must approve this revised specification and its acceptance-test catalogue before coding starts.

The user must approve the reviewed specification before coding starts.

Security must approve the Keychain, clipboard, app-switcher, and network controls before implementation starts.

A separately authorised commit and push must track this specification before final exact-commit review.

## Approved Product Decisions

The user selected these product decisions:

- Build a native SwiftUI application with Apple frameworks only.
- Support iPhone only.
- Require iOS 26 or later.
- Keep the user signed in with iOS Keychain storage.
- Use the existing HTTP Basic authentication method.
- Send Basic credentials with the first request.
- Connect to one fixed, private, non-Production test server.
- Use fictional information only.
- Classify all release information as `FICTIONAL PILOT — CONTROLLED`.
- Allow normal iPhone screenshots.
- Hide release information in the app-switcher preview.
- Provide copy buttons for visible release information.
- Never copy credentials or technical details.
- Show `No current release is available.` for all empty results.
- Use a ten-working-day active implementation hard limit.

## Problem Statement

ACE has a protected read-only client release API.

It does not have a native iPhone application for that release.

The client needs a simple iPhone view of the current authorised release.

The application must not become another system of record.

It must not change ACE information or bypass ACE controls.

## Solution

Build a small native SwiftUI application for iPhone and iOS 26 or later.

The application reads only `GET /client/api/v1/release/current`.

It uses `URLSession`, hand-written `Codable` models, and iOS Keychain.

It shows the current conclusion and ordered actions from ACE.

It stores no release response, history, database, or offline copy.

It keeps credentials in one approved Keychain item.

It sends no write request and contains no write transport method.

## User Stories

1. As a fictional pilot client, I want to sign in once, so that I can return without entering credentials again.
2. As a fictional pilot client, I want a clear sign-in screen, so that I know which credentials to enter.
3. As a fictional pilot client, I want the current release, so that I can read approved information.
4. As a fictional pilot client, I want the Engagement name, so that I can identify the release.
5. As a fictional pilot client, I want the review status, so that I understand its state.
6. As a fictional pilot client, I want the release version, so that I can identify the displayed release.
7. As a fictional pilot client, I want the publication time, so that I know when ACE published it.
8. As a fictional pilot client, I want the conclusion title and summary, so that I can understand the approved conclusion.
9. As a fictional pilot client, I want the evidence reference, so that I can copy its visible value.
10. As a fictional pilot client, I want ordered actions, so that I see the ACE order without client sorting.
11. As a fictional pilot client, I want action owners and dates, so that responsibilities are clear.
12. As a fictional pilot client, I want action status, so that I can distinguish open and complete work.
13. As a fictional pilot client, I want copy buttons, so that I can copy visible release information.
14. As a fictional pilot client, I want normal screenshots, so that I can use standard iPhone capture.
15. As a fictional pilot client, I want a hidden app-switcher preview, so that background previews do not show release information.
16. As a fictional pilot client, I want a clear empty message, so that missing information does not look like an error.
17. As a fictional pilot client, I want clear access failure wording, so that technical details remain hidden.
18. As a fictional pilot client, I want a safe refresh control, so that I can request the current ACE release again.
19. As a fictional pilot client, I want sign-out, so that I can remove my stored credentials.
20. As a fictional pilot client, I want large text support, so that I can read the complete release.
21. As a VoiceOver user, I want ordered labels, so that I can understand the release without sight.
22. As an ACE owner, I want all mobile reads to use the existing endpoint, so that ACE remains authoritative.
23. As an ACE owner, I want no mobile write method, so that an application fault cannot change ACE.
24. As an ACE owner, I want G0 to remain server-owned, so that the application cannot bypass it.
25. As an ACE owner, I want one fixed server address, so that users cannot redirect credentials.
26. As an ACE owner, I want no provider access, so that mobile use does not expose provider credentials.
27. As Security, I want protected credential storage, so that credentials are not stored as plain text.
28. As Security, I want response caching disabled, so that release content does not remain in an application cache.
29. As Security, I want technical details excluded, so that errors and copied text reveal no internal information.
30. As Security, I want old requests rejected, so that a late response cannot restore cleared information.
31. As an auditor, I want the application to remain read-only, so that approval authority stays in ACE.
32. As a reviewer, I want named acceptance tests, so that every product rule has evidence.
33. As an approver, I want one fixed candidate, so that each review applies to exact code.
34. As a maintainer, I want Apple frameworks only, so that the application has no third-party runtime upgrade path.
35. As a maintainer, I want separate server and mobile tests, so that mobile tests do not replace ACE compatibility tests.

## Existing ACE Contract

### Ownership Boundary

- `ClientReleaseProjection` owns read-only construction of `ClientReleaseResponse`.
- `ClientReleaseService` remains release workflow authority.
- `ClientReleaseStorage` remains the only release SQL owner.
- `WorkbenchStore` remains migration and trigger-installation owner.
- The server route retains authentication, G0, HTTP behaviour, one SQLite connection, errors, and HTML rendering.
- The iOS application calls the JSON API only.
- The iOS application never connects to SQLite.
- The iOS application never calls Sift-KG or OpenViking.

### Endpoint

- Method: `GET`.
- Path: `/client/api/v1/release/current`.
- Success status: HTTP `200`.
- Success content type: `application/json`.
- Missing or invalid credentials: HTTP `403`.
- Missing server authentication configuration: HTTP `503`.
- G0 rejection: HTTP `503`.
- No mobile endpoint, API field, schema, migration, or trigger change is permitted.

### Response Contract

| Field | Type | Rule |
|---|---|---|
| `engagement_name` | String | Required. It can contain an existing empty-state sentinel. |
| `review_status` | String | Required. It can be empty in an existing empty response. |
| `release_version` | Integer | Required. Existing empty responses use `0`. |
| `published_at` | String | Required. Valid releases use canonical UTC `YYYY-MM-DDTHH:MM:SSZ`. |
| `conclusion` | Object or null | The only optional response value. |
| `conclusion.title` | String | Required when `conclusion` is present. |
| `conclusion.summary` | String | Required when `conclusion` is present. |
| `conclusion.evidence_reference_id` | String | Required when `conclusion` is present. |
| `actions` | Array | Required. It can be empty. |
| `actions[].description` | String | Required for each action. |
| `actions[].owner` | String | Required for each action. |
| `actions[].target_date` | String | Required. Exact calendar date `YYYY-MM-DD`. |
| `actions[].status` | String | Required. Existing values are `OPEN` or `COMPLETE`. |

The application preserves the API action order.

It does not sort actions by owner, date, description, or status.

It ignores no required field.

It rejects an invalid success body before replacing visible information.

### Response Validation

A valid current release has these values:

- `release_version` is an integer greater than zero.
- `engagement_name`, `review_status`, and `published_at` are not empty.
- Each present conclusion string is not empty.
- Each action string is not empty.
- Each action status is exactly `OPEN` or `COMPLETE`.
- Each date and time follows the formats in the response contract.

The application accepts only these two empty sentinel combinations:

| Condition | Engagement Name | Review Status | Version | Published At | Conclusion | Actions |
|---|---|---|---:|---|---|---|
| No published release | `Release unavailable` | Empty | `0` | Empty | `null` | Empty array |
| Missing Engagement | `Engagement not found` | Empty | `0` | Empty | `null` | Empty array |

The application maps both combinations to `No current release is available.`

It rejects every other zero, negative, sentinel, or empty-field combination.

It rejects an action with any status other than `OPEN` or `COMPLETE`.

An invalid success body shows `ACE is unavailable. Try again later.`

### Server Compatibility Record

The existing server-owned API record is:

- HTTP `200`.
- Content type `application/json`.
- Size `599` bytes.
- SHA-256 `5e19bc98c09286a2eb8181650462cfb5ae6952eb342da080643d54a8ab6856af`.

The existing server-owned HTML record is:

- HTTP `200`.
- Content type `text/html; charset=utf-8`.
- Size `3,156` bytes.
- SHA-256 `017f19c4e4ebf5e98cb2c9493deec789a5bbf2107a39f6326c6d4fb8b0788e3d`.

Mobile tests do not replace these server compatibility records.

## Screen And State Contract

### Sign-In Screen

The sign-in screen contains:

- Username.
- Password with secure text entry.
- Sign-in control.
- Generic validation text.
- No editable server address.
- No Production option.
- No server, stack, or authentication details.

The username field remains readable during normal sign-in.

A visible username can appear in a normal user-created screenshot.

The password field must never show its value as readable text.

The interface must never show a password, HTTP `Authorization` value, or Keychain secret.

After successful access, the application stores the credentials in Keychain.

### Current Release Screen

The current release screen contains:

- Engagement name.
- Review status.
- Release version.
- Published date and time.
- Conclusion title, summary, and evidence reference.
- Ordered action description, owner, target date, and status.
- Refresh control.
- Sign-out control.
- Copy controls for visible release values.
- A visible fictional pilot notice.

Evidence references remain text.

The application must not open evidence references as URLs or files.

### State Matrix

| Condition | Exact Visible Result | Credential Result | Release Result | Retry Result |
|---|---|---|---|---|
| Missing or invalid Preview configuration | `This app is not configured for access.` | Do not read or change Keychain. | Show none. | No retry control. |
| No Keychain credential | Show sign-in. | None stored. | Show none. | Sign-in is available. |
| Keychain read failure | `Saved sign-in could not be read. Try again.` | State is unknown. | Clear immediately. | Retry Keychain read only. |
| Multiple stored service items, a synchronised item, or invalid returned attributes or secret data | `Saved sign-in must be reset before access.` | Retain items for deletion only. | Clear immediately. | `Reset saved sign-in` only. |
| Deletion-only reset succeeds | Show sign-in. | Delete all matching service items. | Keep clear. | Sign-in is available. |
| Deletion-only reset fails | `Saved sign-in could not be removed. Try again.` | Keep deletion pending. | Keep clear. | Retry Keychain deletion only. |
| Valid credential and valid release | Show the complete release. | Retain approved Keychain item. | Replace state after complete validation. | Refresh is available. |
| Initial or replacement add failure | `Sign-in could not be saved. Try again.` | Store no credential item. | Clear immediately. | Return to sign-in. |
| Same-account update failure and successful cleanup | `Sign-in could not be saved. Try again.` | Delete all service items. | Clear immediately. | Return to sign-in. |
| Same-account update failure and cleanup failure | `Saved sign-in could not be removed. Try again.` | Keep deletion pending. | Clear immediately. | Retry Keychain deletion only. |
| Different-account replacement deletion failure | `Saved sign-in could not be removed. Try again.` | Keep old item. Do not add the new item. | Clear immediately. | Retry Keychain deletion only. |
| No published release | `No current release is available.` | Retain credential. | Clear prior release. | Refresh is available. |
| Missing Engagement response | `No current release is available.` | Retain credential. | Clear prior release. | Refresh is available. |
| No conclusion | `No conclusion is available.` | Retain credential. | Show valid metadata and actions. | Refresh is available. |
| No actions | `No actions are available.` | Retain credential. | Show valid metadata and conclusion. | Refresh is available. |
| HTTP `403` and successful deletion | `Access denied. Sign in again.` | Delete Keychain item. | Clear immediately. | Sign-in is available. |
| HTTP `403` and deletion failure | `Saved sign-in could not be removed. Try again.` | Keep deletion pending. | Clear immediately. | Retry Keychain deletion only. |
| HTTP `503` | `ACE is unavailable. Try again later.` | Retain Keychain item. | Clear immediately. | Manual retry is available. |
| Unexpected HTTP status | `ACE is unavailable. Try again later.` | Retain Keychain item. | Clear immediately. | Manual retry is available. |
| No network | `ACE could not be reached. Check your connection and try again.` | Retain Keychain item. | Clear prior release. | Manual retry is available. |
| Timeout | `The request timed out. Try again.` | Retain Keychain item. | Clear prior release. | Manual retry is available. |
| Untrusted server certificate | `ACE could not establish a secure connection. Try again later.` | Retain Keychain item. | Clear immediately. | Manual retry only. No bypass. |
| Server hostname mismatch | `ACE could not establish a secure connection. Try again later.` | Retain Keychain item. | Clear immediately. | Manual retry only. No bypass. |
| Wrong content type | `ACE is unavailable. Try again later.` | Retain Keychain item. | Clear prior release. | Manual retry is available. |
| Invalid or partial JSON | `ACE is unavailable. Try again later.` | Retain Keychain item. | Clear prior release. | Manual retry is available. |
| Invalid release or action value | `ACE is unavailable. Try again later.` | Retain Keychain item. | Clear prior release. | Manual retry is available. |
| New refresh starts | Show one progress state. | No change. | Reject the old request result. | No second retry control. |
| Sign-out and successful deletion | Show sign-in. | Delete Keychain item. | Clear immediately. | Sign-in is available. |
| Sign-out and deletion failure | `Sign-out could not be completed. Try again.` | Keep deletion pending. | Clear immediately. | Retry Keychain deletion only. |
| Application enters inactive state | Show a plain privacy cover. | Retain Keychain item. | Keep release in memory only. | None. |
| Application becomes active | Remove the privacy cover after activation. | Retain Keychain item. | Show the current in-memory state. | None. |

No error state can show an old release as current.

No state reports successful sign-out while Keychain deletion has failed.

A pending deletion blocks network access until deletion succeeds.

The deletion-only reset state also blocks network access until deletion succeeds.

## Implementation Decisions

1. Use the current Xcode iOS App template.
2. Use SwiftUI for all application screens.
3. Use Swift and Apple frameworks only.
4. Add no third-party runtime package.
5. Target iPhone only with iOS 26 as the minimum version.
6. Use hand-written `Codable` response models.
7. Use one read-only repository protocol as the primary application seam.
8. Use one HTTP transport protocol behind that repository.
9. Use `URLSessionConfiguration.ephemeral`.
10. Set `urlCache` to `nil`.
11. Set `requestCachePolicy` to `.reloadIgnoringLocalCacheData`.
12. Set each request cache policy to `.reloadIgnoringLocalCacheData`.
13. Set `httpCookieStorage` to `nil`.
14. Set `httpShouldSetCookies` to `false`.
15. Set `urlCredentialStorage` to `nil`.
16. Expose only one transport operation: fetch the current release.
17. Permit only the approved HTTPS origin and endpoint.
18. Reject every redirect through the session task delegate.
19. Return `nil` from the redirect completion handler.
20. Use standard platform certificate and hostname validation.
21. Add no certificate pinning without a separate specification.
22. Send HTTP Basic credentials with the first request.
23. Build the authorization value in memory for each request.
24. Store credentials in one approved Keychain item after successful access.
25. Use the exact Keychain contract in this specification.
26. Delete matching synchronised and non-synchronised service items after sign-out or HTTP `403`.
27. Retain the Keychain item after HTTP `503`.
28. Create no server session and no mobile session token.
29. Keep decoded release information in memory only.
30. Add no file, database, object store, state restoration, widget, notification, or background release copy.
31. Complete decoding and validation before updating the visible release.
32. Give each request a generation identity.
33. Ignore results from cancelled, older, signed-out, or rejected credential contexts.
34. Use one observable screen-state owner.
35. Keep the user interface to sign-in and current-release screens.
36. Put sign-out on the current-release screen.
37. Install the privacy cover synchronously and without animation before the inactive callback returns.
38. Remove the cover only after the scene becomes active.
39. Allow normal iPhone screenshots.
40. Do not detect, block, warn about, upload, share, or force an exit because of screenshots.
41. Add explicit copy controls for the approved visible release values.
42. Use the exact clipboard contract in this specification.
43. Copy no password, authorization value, host, error trace, or other technical detail.
44. Keep evidence references inert and copyable only as visible text.
45. Show a short confirmation after a copy operation.
46. Use structured allow-list logging with no release values, usernames, passwords, or authorization values.
47. Add no analytics, tracking, advertising, or crash-reporting service.
48. Add no provider SDK, provider endpoint, or provider credential.
49. Keep Sift-KG and OpenViking outside the mobile application.
50. Keep server code, API contracts, schemas, migrations, and triggers unchanged.
51. Use fictional fixtures, previews, screenshots, and device-test records only.
52. Add no Production configuration.
53. Keep the server address outside user-editable controls.
54. Fail the build and startup checks when the approved Preview address is absent or invalid.
55. Use the Build iOS Apps capabilities for approved build, simulator, and SwiftUI checks.
56. Treat those capabilities as development tools, not application dependencies.
57. Use default ATS protection with no `NSAppTransportSecurity` dictionary.
58. Use system default server-trust and hostname handling only.
59. Run every Keychain lifecycle operation through one serial credential-store actor.
60. Use the exact inventory, read, update, add, and deletion queries in this specification.
61. Block network access during every Keychain deletion-only state.

### Exact Keychain Contract

The application uses one generic-password item with these values:

| Key | Exact Value |
|---|---|
| Item class | `kSecClassGenericPassword` |
| Service | `com.auditco.ace.client.authentication` |
| Account | The exact entered username as a Swift `String` |
| Secret data | The exact entered password as UTF-8 `Data` |
| Access group | Omitted. The application has no Keychain sharing entitlement. |
| Accessibility | `kSecAttrAccessibleWhenUnlockedThisDeviceOnly` |
| Synchronisation | `kSecAttrSynchronizable = false` |

The application uses the exact username and password for HTTP Basic authentication.

It does not normalise, trim, log, or copy either value.

The service can contain only one account item for this application.

One credential-store actor owns all Keychain lifecycle operations.

It runs add, inventory, read, update, replacement, and deletion operations one at a time.

Inventory-and-read, add-or-update, replacement, reset, sign-out, and HTTP `403` cleanup are complete lifecycle operations.

One complete lifecycle operation must finish before another one starts.

Actor re-entry must not overlap or interleave their internal Keychain calls.

It starts each read with this inventory query:

| Query Key | Exact Value |
|---|---|
| `kSecClass` | `kSecClassGenericPassword` |
| `kSecAttrService` | `com.auditco.ace.client.authentication` |
| `kSecAttrSynchronizable` | `kSecAttrSynchronizableAny` |
| `kSecMatchLimit` | `kSecMatchLimitAll` |
| `kSecReturnAttributes` | `true` |
| `kSecReturnData` | `false` |

The inventory query requests no password data.

Apple defines a multiple-match result as an array of individually formatted results.

Only `errSecItemNotFound` from the initial inventory maps to no credential.

After the initial inventory returns `errSecSuccess`, the adapter requires the result to be a non-empty array.

An empty successful array enters deletion-only recovery.

One array member proceeds to complete inventory dictionary validation.

More than one array member enters deletion-only recovery.

An `errSecSuccess` inventory result that is not an array enters deletion-only recovery.

The Apple result-shape and attribute-type statements in this section are platform requirements.

All validation, recovery, and unknown-key rules are ACE project decisions.

A synchronised item enters the deletion-only reset state.

The adapter validates the one inventory dictionary with this contract:

| Returned Key | Required Result |
|---|---|
| `kSecAttrService` | Present as `CFString` and equal to `com.auditco.ace.client.authentication`. |
| `kSecAttrAccount` | Present as `CFString` and bridge losslessly to a non-empty Swift `String`. An empty string is malformed. |
| `kSecAttrAccessible` | Present as `CFString` and equal to `kSecAttrAccessibleWhenUnlockedThisDeviceOnly`. |
| `kSecAttrSynchronizable` | Present as `CFBoolean` and equal to `false`. |
| `kSecAttrAccessGroup` | Optional. Absence is valid. When present, it is `CFString`. After signing inputs are approved, it equals the signed application's approved default access group. |

The fixed inventory and exact-read queries use `kSecClassGenericPassword` as the item-class invariant.

The adapter does not require `kSecClass` in a returned attribute dictionary.

The exact bundle identifier, signing team, and signed entitlements remain external gates.

The signed application's effective first access group is the expected value.

The approved signed build and its effective entitlements establish this value.

The bundle identifier and signing team do not establish this value by themselves.

An implementation cannot pass access-group tests until that expected value is available.

Apple defines the access group as one item attribute.

Apple also assigns the application's first access group when an add omits this attribute.

The access group is system-selected in this application because the add omits it.

ACE validates it when the platform returns it.

The following Apple-defined, system-managed attributes are permitted when returned:

| Returned Key | Permitted Result | ACE Handling |
|---|---|---|
| `kSecAttrCreationDate` | `CFDate` | Ignore after type validation. |
| `kSecAttrModificationDate` | `CFDate` | Ignore after type validation. |

Absence of either date is valid.

A present date with another type enters deletion-only recovery.

The adapter also permits other Apple-defined attributes that apply to generic-password items.

It does not use those attributes to select, authenticate, display, log, or retain a credential.

The reviewed Apple documentation does not provide a closed, exhaustive set of returned attribute keys.

Therefore, ACE ignores an unknown returned key without reading or converting its value.

This unknown-key rule is an ACE project decision. It is not an Apple requirement.

The adapter still validates every key in the required-result table.

An ignored or unknown key cannot replace a required key or change a required value.

Any missing, wrong-type, malformed, or mismatched required attribute enters deletion-only reset.

Network access remains blocked in that state.

For one inventory result, the adapter reads its exact account with this query:

| Query Key | Exact Value |
|---|---|
| `kSecClass` | `kSecClassGenericPassword` |
| `kSecAttrService` | `com.auditco.ace.client.authentication` |
| `kSecAttrAccount` | Exact account from the inventory result |
| `kSecAttrSynchronizable` | `false` |
| `kSecMatchLimit` | `kSecMatchLimitOne` |
| `kSecReturnAttributes` | `true` |
| `kSecReturnData` | `true` |

The adapter validates the returned attributes before it returns the credential.

Apple defines the combined attribute-and-data result as one dictionary.

The adapter requires one dictionary for the exact read.

It applies the complete inventory attribute table to that dictionary.

The returned account must also equal the exact account from the inventory result.

The returned `kSecValueData` must be present as `CFData`.

It must contain at least one byte and decode as one valid UTF-8 Swift `String`.

The adapter does not normalise, trim, log, copy, or display the decoded password.

An absent, wrong-type, empty, or invalid UTF-8 `kSecValueData` enters deletion-only reset.

An unexpected result type enters deletion-only reset.

The application returns no credential until all required attributes and secret data pass validation.

### Deletion-Only Recovery Contract

Any unsafe or ambiguous inventory or exact-read result enters deletion-only recovery.

Entry clears all release information immediately.

Entry cancels active requests and blocks all new network access.

Entry removes every usable username, password, `Authorization` value, and credential object from application memory.

The interface offers only `Reset saved sign-in`.

The reset uses the service deletion query with `kSecAttrSynchronizableAny`.

It deletes all matching service items across synchronised and non-synchronised classes.

The state remains deletion pending after every result other than `errSecSuccess` or `errSecItemNotFound`.

Sign-in remains unavailable while deletion is pending.

Sign-in becomes available only after deletion reports `errSecSuccess` or `errSecItemNotFound`.

No Keychain migration, repair, attribute rewrite, or credential salvage is authorised.

The add dictionary contains every exact item value in the Keychain table.

A same-account update uses class, service, exact account, and synchronisation in its query.

That update changes the password data only.

`errSecDuplicateItem` starts this same-account update path only.

If the update fails, the adapter tries to delete all matching service items.

A successful cleanup returns to sign-in with no credential.

A failed cleanup enters the deletion-pending state and blocks network access.

A different successful account uses delete-before-add replacement.

The delete query contains class, service, and `kSecAttrSynchronizableAny`.

It contains no account, return, or match-limit key.

`SecItemDelete` therefore targets matching synchronised and non-synchronised service items.

Apple's synchronisation documentation states that deletion of a synchronisable item affects all copies of that item.

This deletion is the required reset, replacement, sign-out, and HTTP `403` result.

Security must accept this synchronised-copy deletion consequence before implementation starts.

The adapter adds the new account only after deletion succeeds or returns `errSecItemNotFound`.

It does not add the new account when deletion fails.

That failure enters the deletion-pending state and blocks network access.

If the later add fails, no credential item remains.

That add failure clears release information and returns to sign-in.

Sign-out and HTTP `403` use the same all-service-item deletion query.

They report successful deletion only after `errSecSuccess` or `errSecItemNotFound`.

After replacement, the inventory query returns the new account item only.

Keychain operations use `SecItemAdd`, `SecItemCopyMatching`, `SecItemUpdate`, and `SecItemDelete`.

The Keychain adapter keeps each returned `OSStatus` inside the security boundary.

The user interface receives only the safe state from the state matrix.

Only `errSecItemNotFound` from the initial inventory maps to no credential.

`errSecItemNotFound` from the exact read after a successful inventory is unsafe and enters deletion-only recovery.

It completes deletion when an absent item meets the deletion goal.

All other non-success values cause the specified Keychain failure state.

A locked-device result is a controlled failure. The code does not depend on one exact locked-device status.

Sign-out completes only after `SecItemDelete` reports `errSecSuccess` or `errSecItemNotFound`.

### Exact Network Session Contract

The build supplies one `ACEPreviewOrigin` value through the approved Preview configuration.

The value is an absolute HTTPS origin with one scheme, host, and optional fixed port.

It contains no user information, path other than `/`, query, or fragment.

The application appends only `/client/api/v1/release/current`.

The value is not user-editable.

The build contains no Production origin.

Missing, malformed, non-HTTPS, or unapproved values fail closed before Keychain access or network access.

The application creates one ephemeral foreground session.

It applies all configuration values before it creates the session.

It uses no background session.

It uses standard platform handling for server trust and hostname validation.

A failed trust challenge cancels the request.

The application offers no certificate exception, acceptance override, or alternate endpoint.

It rejects all HTTP redirects through `URLSessionTaskDelegate`.

The delegate passes `nil` to the redirect completion handler for every redirect.

This rule includes changed schemes, hosts, ports, paths, and unchanged-origin paths.

The redirect target must receive no request from this application.

The redirect target must receive no `Authorization` header.

### Exact ATS And Trust Contract

Phase 1 uses default App Transport Security protection.

The processed application `Info.plist` must not contain an `NSAppTransportSecurity` dictionary.

The same rule applies to every allowed build configuration and embedded target.

The build must contain none of these weakening keys:

- `NSAllowsArbitraryLoads`.
- `NSAllowsArbitraryLoadsForMedia`.
- `NSAllowsArbitraryLoadsInWebContent`.
- `NSAllowsLocalNetworking`.
- `NSExceptionDomains`.
- `NSExceptionAllowsInsecureHTTPLoads`.
- `NSExceptionMinimumTLSVersion`.
- `NSExceptionRequiresForwardSecrecy`.

The application permits no equivalent future ATS weakening control.

An ATS strengthening control needs a separate specification and Security approval.

Phase 1 adds no ATS strengthening setting.

The application uses system default server-trust and hostname handling only.

It implements no custom server-trust acceptance or hostname evaluation.

It does not create `URLCredential(trust:)`.

It never returns `.useCredential` for a server-trust challenge.

It does not use manual `SecTrust` evaluation or custom anchor certificates.

If an authentication-challenge delegate receives server trust, it returns `.performDefaultHandling` only.

The system handles every rejected trust challenge as a failed request.

The application then uses the exact trust-failure state in the state matrix.

### Exact Clipboard Contract

Each copy control copies one visible value only.

The approved copyable values are:

- Engagement name.
- Review status.
- Release version.
- Published date and time.
- Conclusion title.
- Conclusion summary.
- Conclusion evidence reference identifier.
- Action description.
- Action owner.
- Action target date.
- Action status.

`conclusion.evidence_reference_id` is an approved visible reference.

No other internal identifier is visible or copyable.

Each copy operation uses `localOnly = true`.

Each copy operation uses `expirationDate = current time plus five minutes`.

Security must approve these two exact clipboard values before implementation starts.

### Exact App-Switcher Contract

The privacy cover contains the application name and `FICTIONAL PILOT — CONTROLLED` only.

The application installs the cover from `sceneWillResignActive(_:)` on the main actor.

It installs the cover synchronously and without animation.

Installation completes before the scene inactive callback returns.

The application removes the cover from `sceneDidBecomeActive(_:)` only after foreground activation.

The application does not remove the cover during an inactive transition.

The callback timing is a project control. It is not an Apple snapshot-timing guarantee.

## Repository And Environment Boundary

The implementation can add only the new ACE iOS application module and its tests.

The intended repository boundary is `sqe/ios/ACEClientApp`.

Server source, Python tests, database files, migrations, and existing web routes are excluded.

Documentation can change only for the approved specification and required delivery records.

Implementation requires an approved macOS host with Xcode 26.

The host must provide an iOS 26 simulator before implementation tests start.

The current Windows workspace cannot provide the required Xcode build evidence.

The exact bundle identifier and signing team must be approved before a physical-device build.

The exact private test-server address and certificate must be approved before network or device testing.

## Security And Privacy Decisions

1. G0 remains active on the ACE server.
2. Use fictional information only.
3. Classify displayed information as `FICTIONAL PILOT — CONTROLLED`.
4. Treat this as a handling label. The existing ACE G0 classification remains `FICTIONAL`.
5. Do not use real client information.
6. Store only the approved Basic credential in Keychain.
7. Store no release content in Keychain.
8. Store no credential in source, configuration, fixtures, logs, or `UserDefaults`.
9. Send credentials only to the approved HTTPS origin.
10. Users cannot edit the server address.
11. Normal user-created iPhone screenshots are allowed.
12. The application does not detect, block, warn about, upload, share, or force an exit because of screenshots.
13. The app-switcher preview hides release content.
14. Copy controls include visible release information only.
15. Use `localOnly = true` for each clipboard write.
16. Remove copied values after five minutes with `expirationDate`.
17. Security must approve these exact clipboard values.
18. Do not copy credentials, hosts, errors, logs, or unapproved internal identifiers.
19. Log no response body, release field, username, password, credential, or authorization value.
20. Start no background refresh or network transfer.
21. Keep no response cache, cookie store, or restored release state.
22. Add no provider, analytics, advertising, or crash-reporting connection.
23. Do not deploy to Production.
24. Keep every Keychain lifecycle operation serial.
25. Block network access when Keychain inventory is invalid or deletion is pending.
26. Use default ATS with no exception dictionary or weakening value.
27. Use system default server-trust and hostname handling only.
28. Inventory and delete both Keychain synchronisation classes.
29. Add, read, and update the approved credential with synchronisation disabled.
30. Keep the username readable during normal sign-in.
31. Use secure text entry for the password and never show it as readable text.
32. Never show an HTTP `Authorization` value or Keychain secret in the interface.
33. Redact usernames from controlled test, review, and delivery evidence.
34. Put no password, `Authorization` value, or Keychain secret in controlled evidence.
35. Keep the approved release-information screenshot and app-switcher rules unchanged.

## Accessibility Decisions

1. Every control has a concise VoiceOver label.
2. Reading order follows release metadata, conclusion, actions, and controls.
3. All text supports every iOS 26 Dynamic Type size.
4. Long text wraps without horizontal text scrolling.
5. Colour is never the only status signal.
6. Light and dark appearances meet current Apple contrast guidance.
7. Bold Text does not hide or clip information.
8. Reduce Motion removes nonessential movement.
9. Errors receive one useful announcement without repeated interruption.
10. Copy controls state the copied field in their label.
11. Portrait and landscape work on the approved iPhone matrix.
12. iPad behaviour is outside this specification.

### Accessibility Test Matrix

The required simulator devices are:

- iPhone SE (3rd generation) with iOS 26.
- iPhone 16 Pro Max with iOS 26.

The approved Xcode 26 host must contain both simulator destinations.

Run each screen and state in portrait and landscape.

Run each screen and state in light and dark appearance.

Run Dynamic Type at default, extra large, and accessibility extra-extra-extra large.

The automated layout suite also checks every iOS 26 Dynamic Type size.

Run Bold Text off and on.

Run Reduce Motion off and on.

Run Increase Contrast off and on in both appearances.

Text through 17 points must have a contrast ratio of at least `4.5:1`.

Text at 18 points or more must have a contrast ratio of at least `3:1`.

Bold text must have a contrast ratio of at least `3:1`.

Meaningful non-text elements must have a contrast ratio of at least `3:1`.

The matrix covers these screens and states:

- Sign-in.
- Loading.
- Valid release.
- No published release.
- Missing Engagement.
- No conclusion.
- No actions.
- HTTP `403`.
- HTTP `503`.
- Unexpected HTTP status.
- No network.
- Timeout.
- Invalid response.
- Keychain read failure.
- Keychain write failure.
- Keychain deletion failure.
- Copy confirmation.
- Privacy cover.

Run `performAccessibilityAudit` for every listed screen and state.

No unresolved automated accessibility audit failure is permitted.

### Manual VoiceOver Journeys

Run these journeys on the approved physical pilot iPhone:

1. Sign in, correct a validation error, and open a valid release.
2. Read metadata, conclusion, actions, copy controls, refresh, and sign-out in that order.
3. Read both empty sentinels and their common message.
4. Read the no-conclusion and no-actions states.
5. Read each safe failure message and use its permitted retry control.
6. Copy each approved field and hear one field-specific confirmation.
7. Enter the app switcher, confirm the cover, return, and continue reading.
8. Cause a Keychain deletion failure and confirm that sign-out does not report success.

VoiceOver must reach every visible element.

It must announce each label, value, trait, state, and validation result clearly.

## Testing Decisions

### Primary Test Seam

Use the read-only repository with a controlled HTTP transport as the primary mobile test seam.

This seam covers request construction, response validation, error mapping, cancellation, and visible state.

Use direct Keychain tests only for credential lifecycle behaviour.

Use XCTest UI for complete user journeys and accessibility audits.

Do not test private Swift helper functions.

Do not reproduce the server byte-hash suite in the iOS test target.

### Test Quality

Good tests check visible behaviour and boundary effects.

They do not depend on private types, timing sleeps, or live Production services.

Every fixture uses fictional names and values.

Each network test uses a controlled transport or approved private test server.

### Acceptance-Test Catalogue

#### Baseline And Project

- `IOS-BASE-001`: The branch starts at `6b0160befc9191dbccd527bdd385b891782ddad8`.
- `IOS-BASE-002`: The project targets iPhone and iOS 26 or later.
- `IOS-BASE-003`: The application uses SwiftUI and Apple frameworks only.
- `IOS-BASE-004`: The dependency graph contains no third-party runtime package.
- `IOS-BASE-005`: Server source and contracts are unchanged.
- `IOS-BASE-006`: The build contains no Production server address.

#### Response Models

- `IOS-MODEL-001`: A valid current release decodes every required field.
- `IOS-MODEL-002`: A null conclusion decodes successfully.
- `IOS-MODEL-003`: A missing required top-level field fails closed.
- `IOS-MODEL-004`: A missing required nested field fails closed.
- `IOS-MODEL-005`: A missing actions array fails closed.
- `IOS-MODEL-006`: An empty actions array decodes successfully.
- `IOS-MODEL-007`: Action order matches the API order.
- `IOS-MODEL-008`: Exact `YYYY-MM-DD` action dates are accepted.
- `IOS-MODEL-009`: Invalid action dates fail closed.
- `IOS-MODEL-010`: Canonical UTC publication times are accepted.
- `IOS-MODEL-011`: Invalid publication times fail closed.
- `IOS-MODEL-012`: Unknown extra response fields do not become visible.
- `IOS-MODEL-013`: A valid release requires `release_version` greater than zero.
- `IOS-MODEL-014`: Each exact empty sentinel combination is accepted.
- `IOS-MODEL-015`: Every other zero, negative, sentinel, or empty-field combination fails closed.
- `IOS-MODEL-016`: An action status other than `OPEN` or `COMPLETE` fails closed.
- `IOS-MODEL-017`: No conclusion shows `No conclusion is available.`
- `IOS-MODEL-018`: No actions shows `No actions are available.`

#### Request And Network

- `IOS-NET-001`: The client sends only `GET`.
- `IOS-NET-002`: The client requests only `/client/api/v1/release/current`.
- `IOS-NET-003`: The client sends Basic authorization with the first request.
- `IOS-NET-004`: The client sends credentials only to the approved HTTPS origin.
- `IOS-NET-005`: The client rejects an HTTPS-to-HTTP redirect.
- `IOS-NET-006`: The client rejects a cross-host redirect.
- `IOS-NET-007`: Standard platform validation rejects an untrusted certificate without a bypass.
- `IOS-NET-008`: Standard platform validation rejects a hostname mismatch without a bypass.
- `IOS-NET-009`: The client rejects the wrong content type.
- `IOS-NET-010`: The client cancels an older refresh.
- `IOS-NET-011`: A late cancelled response cannot change visible state.
- `IOS-NET-012`: Timeout and no-network failures show safe retry controls.
- `IOS-NET-013`: Authentication and trust failures do not retry automatically.
- `IOS-NET-014`: No request uses a write method.
- `IOS-NET-015`: Missing Preview configuration fails the build check and startup check before Keychain or network access.
- `IOS-NET-016`: Invalid Preview configuration fails the build check and startup check before Keychain or network access.
- `IOS-NET-017`: The session uses `urlCache = nil`.
- `IOS-NET-018`: The session and each request bypass local cache data.
- `IOS-NET-019`: The session uses `httpCookieStorage = nil` and `httpShouldSetCookies = false`.
- `IOS-NET-020`: The session uses `urlCredentialStorage = nil`.
- `IOS-NET-021`: The delegate rejects a same-origin path redirect.
- `IOS-NET-022`: The delegate rejects a changed-port redirect.
- `IOS-NET-023`: The delegate rejects a changed-host redirect.
- `IOS-NET-024`: The delegate rejects a clear-text redirect.
- `IOS-NET-025`: Each rejected redirect target receives no request and no authorization value.
- `IOS-NET-026`: Every unexpected HTTP status shows the exact safe unavailable state.
- `IOS-NET-027`: A non-HTTPS or unapproved Preview origin fails before Keychain and network access.
- `IOS-NET-028`: A trust failure sends no HTTP request or authorization value to the rejected endpoint.
- `IOS-NET-029`: Every processed application plist contains no ATS dictionary or weakening value.
- `IOS-NET-030`: Source and challenge tests prove system default server-trust handling only.

#### Credentials

- `IOS-AUTH-001`: A successful sign-in stores one approved Keychain item.
- `IOS-AUTH-002`: Relaunch uses the approved Keychain item and returns to the release screen.
- `IOS-AUTH-003`: Sign-out deletes matching synchronised and non-synchronised service items.
- `IOS-AUTH-004`: HTTP `403` deletes matching synchronised and non-synchronised service items.
- `IOS-AUTH-005`: HTTP `503` retains the Keychain item.
- `IOS-AUTH-006`: Logs contain no username, password, or HTTP `Authorization` value. Passwords, `Authorization` values, and Keychain secrets enter no fixture, screenshot, copied text, or controlled evidence. Controlled evidence redacts usernames.
- `IOS-AUTH-007`: No credential enters URL credential storage or `UserDefaults`.
- `IOS-AUTH-008`: No cookie or server-session assumption exists.
- `IOS-AUTH-009`: A late response cannot restore data after sign-out.
- `IOS-AUTH-010`: A changed credential context rejects the old response.
- `IOS-AUTH-011`: A Keychain add uses the exact class, service, account, and secret encoding.
- `IOS-AUTH-012`: A Keychain add uses the exact accessibility, synchronisation, and access-group values.
- `IOS-AUTH-013`: Inventory finds both synchronisation classes, then one exact query returns the approved non-synchronised credential.
- `IOS-AUTH-014`: A same-account update query changes only the exact item password.
- `IOS-AUTH-015`: `errSecDuplicateItem` starts the approved same-account update path.
- `IOS-AUTH-016`: The all-service deletion query removes matching items from both synchronisation classes.
- `IOS-AUTH-017`: The initial inventory returning `errSecItemNotFound` maps to no credential.
- `IOS-AUTH-018`: A locked-device Keychain result causes the safe read-failure state.
- `IOS-AUTH-019`: Each other Keychain `OSStatus` causes its specified safe failure state.
- `IOS-AUTH-020`: A Keychain write failure does not report successful sign-in.
- `IOS-AUTH-021`: A Keychain deletion failure does not report successful sign-out.
- `IOS-AUTH-022`: A deletion-pending state permits no network request.
- `IOS-AUTH-023`: A physical locked-device check confirms that the item is unavailable while locked.
- `IOS-AUTH-024`: A missing delete maps `errSecItemNotFound` to completed deletion.
- `IOS-AUTH-025`: A different successful account replaces the old item and leaves one service item.
- `IOS-AUTH-026`: Multiple items, a synchronised item, or invalid attributes enter deletion-only reset. Network stays blocked after failed deletion.
- `IOS-AUTH-027`: A replacement deletion failure does not add the new account.
- `IOS-AUTH-028`: A replacement add failure leaves no credential or release information.
- `IOS-AUTH-029`: Controlled evidence records each complete lifecycle operation start and completion. Actor re-entry cannot overlap or interleave internal calls. Concurrent requests leave one matching service item.
- `IOS-AUTH-030`: Reset, replacement, sign-out, and HTTP `403` use service deletion with `kSecAttrSynchronizableAny` and delete all matching synchronised and non-synchronised copies.
- `IOS-AUTH-031`: The username field remains readable during normal sign-in.
- `IOS-AUTH-032`: The password field uses secure text entry.
- `IOS-AUTH-033`: A password never appears as readable interface text.
- `IOS-AUTH-034`: An HTTP `Authorization` value never appears in the interface.
- `IOS-AUTH-035`: A Keychain secret never appears in the interface.
- `IOS-AUTH-036`: Controlled test, review, and delivery evidence redacts every username.
- `IOS-AUTH-037`: Controlled evidence contains no password, `Authorization` value, or Keychain secret.
- `IOS-AUTH-038`: Each inventory result validates every required attribute and exact rule in the returned-attribute table.
- `IOS-AUTH-039`: Valid system-managed creation and modification dates do not invalidate a credential.
- `IOS-AUTH-040`: An additional Apple-defined generic-password attribute does not invalidate a credential or affect its use.
- `IOS-AUTH-041`: An unknown returned key is ignored and cannot replace or change a required value.
- `IOS-AUTH-042`: An absent account attribute enters deletion-only recovery.
- `IOS-AUTH-043`: A non-`CFString` account attribute enters deletion-only recovery.
- `IOS-AUTH-044`: An empty account enters deletion-only recovery.
- `IOS-AUTH-045`: Absent secret data enters deletion-only recovery.
- `IOS-AUTH-046`: Secret data that is not `CFData` enters deletion-only recovery.
- `IOS-AUTH-047`: Empty secret data enters deletion-only recovery.
- `IOS-AUTH-048`: Secret data that is not valid UTF-8 enters deletion-only recovery.
- `IOS-AUTH-049`: More than one inventory item enters deletion-only recovery.
- `IOS-AUTH-050`: A synchronised inventory item enters deletion-only recovery.
- `IOS-AUTH-051`: Inventory and exact-read queries use `kSecClassGenericPassword`. Returned dictionaries do not require `kSecClass`.
- `IOS-AUTH-052`: An absent, wrong-type, or mismatched service value enters deletion-only recovery.
- `IOS-AUTH-053`: A returned access-group attribute with a wrong type or value enters deletion-only recovery.
- `IOS-AUTH-054`: An absent, wrong-type, or true synchronisation value enters deletion-only recovery.
- `IOS-AUTH-055`: An unexpected inventory array member type or exact-read result type enters deletion-only recovery.
- `IOS-AUTH-056`: An exact-read account that differs from the inventory account enters deletion-only recovery.
- `IOS-AUTH-057`: Entry to deletion-only recovery clears release information immediately.
- `IOS-AUTH-058`: Entry to deletion-only recovery cancels active requests and blocks all network access.
- `IOS-AUTH-059`: Deletion-only recovery retains no usable credential in application memory.
- `IOS-AUTH-060`: Deletion-only recovery offers only `Reset saved sign-in`.
- `IOS-AUTH-061`: Recovery deletion uses the service query with `kSecAttrSynchronizableAny` and removes all matching copies.
- `IOS-AUTH-062`: A failed recovery deletion stays deletion pending and keeps network and sign-in blocked.
- `IOS-AUTH-063`: Sign-in becomes available only after recovery deletion returns `errSecSuccess` or `errSecItemNotFound`.
- `IOS-AUTH-064`: Exact credential reads use `kSecAttrSynchronizable = false` and cannot select a synchronised item.
- `IOS-AUTH-065`: No Keychain migration, repair, attribute rewrite, or credential salvage path exists.
- `IOS-AUTH-066`: A creation or modification date with a non-`CFDate` value enters deletion-only recovery.
- `IOS-AUTH-067`: An absent, wrong-type, or mismatched accessibility value enters deletion-only recovery.
- `IOS-AUTH-068`: `errSecSuccess` with an inventory result that is not an array enters deletion-only recovery.
- `IOS-AUTH-069`: Exact-read `errSecItemNotFound` after a successful inventory enters deletion-only recovery.
- `IOS-AUTH-070`: `errSecSuccess` with an empty inventory array enters deletion-only recovery.

#### Screen States

- `IOS-STATE-001`: A valid release replaces the screen atomically and shows the exact `FICTIONAL PILOT — CONTROLLED` handling label.
- `IOS-STATE-002`: No release shows `No current release is available.`
- `IOS-STATE-003`: Missing Engagement shows `No current release is available.`
- `IOS-STATE-004`: HTTP `403` shows `Access denied. Sign in again.` after successful deletion.
- `IOS-STATE-005`: HTTP `503` shows `ACE is unavailable. Try again later.`
- `IOS-STATE-006`: Invalid JSON shows no partial or old release.
- `IOS-STATE-007`: A refresh permits only one active result.
- `IOS-STATE-008`: Sign-out returns to sign-in and clears release data.
- `IOS-STATE-009`: Background entry shows the privacy cover.
- `IOS-STATE-010`: Foreground return removes the privacy cover.
- `IOS-STATE-011`: Each state shows the exact safe text in the state matrix.
- `IOS-STATE-012`: Each state has only the retry control in the state matrix.
- `IOS-STATE-013`: Each state has the credential result in the state matrix.
- `IOS-STATE-014`: Each state has the release result in the state matrix.
- `IOS-STATE-015`: An unexpected status does not show server or authentication details.
- `IOS-STATE-016`: A Keychain read, write, or deletion failure shows no old release.
- `IOS-STATE-017`: An untrusted certificate matches every result in its trust-failure row.
- `IOS-STATE-018`: A hostname mismatch matches every result in its trust-failure row.

#### Copy And Screenshot Behaviour

- `IOS-COPY-001`: Each approved visible value has a labelled copy control.
- `IOS-COPY-002`: A copy control copies only its visible value.
- `IOS-COPY-003`: No copy control exposes credentials or technical details.
- `IOS-COPY-004`: Evidence references copy as text and never open as links.
- `IOS-COPY-005`: A copy action gives accessible confirmation.
- `IOS-COPY-006`: Only the eleven named field types have copy controls.
- `IOS-COPY-007`: No unapproved internal identifier has a copy control.
- `IOS-COPY-008`: Every clipboard write uses `localOnly = true`.
- `IOS-COPY-009`: Every clipboard write expires five minutes after the write.
- `IOS-SHOT-001`: Normal iPhone screenshots remain allowed.
- `IOS-SHOT-002`: The application does not detect, block, warn about, upload, share, or force an exit because of screenshots.
- `IOS-SHOT-003`: The app-switcher preview shows the privacy cover.
- `IOS-SHOT-004`: The inactive callback returns only after synchronous cover installation.
- `IOS-SHOT-005`: Cover installation and removal use no animation.
- `IOS-SHOT-006`: The application removes the cover only after active foreground state.
- `IOS-SHOT-007`: A manual app-switcher capture shows no release information.
- `IOS-SHOT-008`: `sceneWillResignActive(_:)` installs the cover on the main actor.
- `IOS-SHOT-009`: `sceneDidBecomeActive(_:)` removes the cover after activation.
- `IOS-SHOT-010`: A visible username can appear in a normal user-created screenshot.

#### Persistence And Privacy

- `IOS-PRIV-001`: Release responses are not written to files or databases.
- `IOS-PRIV-002`: The network session has no response cache.
- `IOS-PRIV-003`: The network session stores no cookies.
- `IOS-PRIV-004`: Scene restoration contains no release information.
- `IOS-PRIV-005`: Widgets and notifications contain no release information.
- `IOS-PRIV-006`: The application starts no background refresh.
- `IOS-PRIV-007`: Logs contain no release field, username, password, credential, or HTTP `Authorization` value.
- `IOS-PRIV-008`: The application contains no provider, analytics, advertising, or crash-reporting connection.
- `IOS-PRIV-009`: The app-switcher cover contains only the application name and the exact `FICTIONAL PILOT — CONTROLLED` handling label.

#### Accessibility And Device

- `IOS-ACC-001`: VoiceOver reads the main screen in the approved order.
- `IOS-ACC-002`: All controls have useful VoiceOver labels and traits.
- `IOS-ACC-003`: All iOS 26 Dynamic Type sizes show complete information.
- `IOS-ACC-004`: Bold Text causes no clipping.
- `IOS-ACC-005`: Reduce Motion retains clear loading feedback.
- `IOS-ACC-006`: Light and dark appearances meet approved contrast rules.
- `IOS-ACC-007`: Portrait and landscape pass on the smallest approved iPhone.
- `IOS-ACC-008`: The automated accessibility audit reports no unresolved failure.
- `IOS-ACC-009`: Manual VoiceOver checks pass on the approved pilot device.
- `IOS-ACC-010`: Both named iOS 26 simulator devices pass the matrix.
- `IOS-ACC-011`: Every listed screen and state passes an automated accessibility audit.
- `IOS-ACC-012`: Default, extra-large, and accessibility XXXL text pass the full matrix.
- `IOS-ACC-013`: Increase Contrast passes in light and dark appearance.
- `IOS-ACC-014`: Text through 17 points has at least `4.5:1` contrast.
- `IOS-ACC-015`: Text from 18 points has at least `3:1` contrast.
- `IOS-ACC-016`: Each manual VoiceOver journey follows the specified spoken order.
- `IOS-ACC-017`: VoiceOver reaches every visible element and announces its state.
- `IOS-ACC-018`: Bold text has at least `3:1` contrast.
- `IOS-ACC-019`: Meaningful non-text content has at least `3:1` contrast.

#### ACE Boundary

- `IOS-BOUND-001`: Request capture shows only the approved GET endpoint.
- `IOS-BOUND-002`: The application contains no ACE database connection.
- `IOS-BOUND-003`: The application contains no Sift-KG or OpenViking call.
- `IOS-BOUND-004`: The application contains no provider credential or SDK.
- `IOS-BOUND-005`: The application contains no edit, approval, upload, delete, or write control.
- `IOS-BOUND-006`: Server compatibility evidence remains unchanged.
- `IOS-BOUND-007`: G0 and server authentication remain server-owned and unchanged.
- `IOS-BOUND-008`: The application contains only fictional fixtures and previews.

### Verification Sequence

1. Pocock approves this catalogue.
2. Security approves the Keychain, clipboard, app-switcher, and network controls.
3. Confirm an approved macOS and Xcode 26 environment.
4. Confirm the exact private server address and certificate.
5. Confirm the exact bundle identifier and simulator destination.
6. Create the project from the approved Xcode template.
7. Write model, repository, transport, Keychain, and state tests first.
8. Confirm new behaviour tests fail for the expected missing implementation.
9. Implement the smallest passing code.
10. Run focused tests after each safe fix.
11. Run simulator UI and accessibility checks.
12. Before draft pull request creation, verify that Greptile automatic reviews are manual-only. Verify that review retriggers are off.
13. Inspect the task diff before the initial commit. Confirm that it contains only the approved task.
14. Make the initial normal task commit and push.
15. Create the draft pull request for that head.
16. Complete CI and conflict checks before Greptile.
17. Start one controlled Greptile review with one manual `@greptileai` pull request comment.
18. Use official `check-pr` to inspect the Greptile result.
19. Apply permitted Greptile fixes and run focused tests.
20. Commit and push the changed head. Update the draft pull request.
21. After a permitted Greptile fix, use current-head `check-pr` to confirm resolution and current checks.
22. Run final Pocock review on the current head.
23. Apply permitted Pocock fixes and run focused tests.
24. Commit and push that changed head. Update the draft pull request.
25. Return to step 22 after a Pocock-driven head change.
26. Run the complete suite once on the unchanged Pocock-approved head.
27. The primary session inspects the complete diff and all evidence.
28. Run one Fresh Sol review on that exact head.

If Fresh Sol needs no fix, the candidate can proceed to exact-head merge approval.

One permitted Fresh Sol fix changes the candidate head.

After that fix, use this exact sequence:

1. Run focused tests for the fix.
2. Commit and push the changed head.
3. Update the draft pull request.
4. Run Pocock review on the changed head.
5. Run the complete suite on the unchanged Pocock-approved head.
6. The primary session inspects the complete diff and all evidence.
7. Run one new Fresh Sol review on that exact head.

Do not run Greptile again after the permitted Fresh Sol fix.

Record the earlier Greptile review as historical evidence under the controlled workflow.

## Failure Rules

1. A configuration without the approved HTTPS server fails closed.
2. An invalid credential changes no ACE record and removes stored access after HTTP `403`.
3. HTTP `503` clears visible release data but retains the approved Keychain credential.
4. A network or decoding error clears prior release data.
5. A cancelled or old request cannot update current state.
6. A trust failure offers no bypass.
7. A redirect cannot send credentials to another host.
8. A copy operation cannot include a hidden field.
9. A Keychain failure uses the exact safe state in the state matrix.
10. A test failure blocks the candidate.
11. A baseline mismatch stops implementation.
12. A required Security decision blocks the affected implementation.
13. A redirect target receives no request and no authorization value.
14. A Keychain deletion failure blocks successful sign-out.
15. Multiple Keychain service items block network access and permit deletion only.
16. A replacement deletion failure cannot add the new credential.
17. A later replacement add failure leaves no credential.
18. An ATS weakening value blocks the candidate.
19. Custom server-trust acceptance blocks the candidate.

## Out Of Scope

- Real client information.
- Production configuration or deployment.
- TestFlight or App Store submission.
- iPad support.
- Android support.
- Web or React Native wrappers.
- Client edits, comments, approvals, acknowledgements, or decisions.
- Evidence upload or capture.
- Offline release storage.
- Background refresh.
- Push notifications or widgets.
- Client export files.
- Opening evidence references.
- New server authentication.
- Server sessions or mobile tokens.
- New ACE API endpoints or fields.
- Server source, schema, migration, or trigger changes.
- Sift-KG or OpenViking mobile integration.
- Provider access, analytics, advertising, or crash reporting.
- Third-party runtime packages.
- Certificate pinning.
- Production hardening.

## Delivery Gates

1. The user authorises one specification-only commit and push.
2. That commit tracks this specification and no unrelated file.
3. Pocock approves the exact specification commit and every acceptance-test identifier.
4. Security approves the exact specification commit and Keychain policy.
5. Security approves clipboard behaviour and the app-switcher cover.
6. Security and ACE operations approve the exact private test server and certificate.
7. The user approves the Pocock-reviewed specification.
8. A Linear implementation issue records the approved baseline, scope, tests, limit, and exclusions.
9. The issue receives the correct approval state under repository rules.
10. A fresh Codex task invokes `$sol-advisor:orchestration`.
11. The implementation task uses an isolated worktree at the approved baseline.
12. The implementation task records the allowed iOS module and tests.
13. The implementation task confirms an approved Mac, Xcode 26, and iOS 26 simulator.
14. The implementation task records high-cost build, simulator, UI, and device commands.
15. The implementation task stops before any architecture, security, API, dependency, or Production expansion.
16. CI and conflict checks pass.
17. One controlled Greptile review runs under the approved delivery workflow.
18. Permitted Greptile fixes pass focused tests.
19. Pocock approves the unchanged implementation head.
20. The complete suite passes on that unchanged head.
21. The primary session inspects the complete diff and all evidence.
22. A Fresh Sol review approves that exact head.
23. A permitted Sol fix renews the gates in the stated post-fix sequence.
24. The exact pull request head receives separate merge approval.
25. No automatic merge or Production deployment occurs.

## Bounded Implementation

The active implementation and verification hard limit is ten working days.

Waiting for Security, Legal, device, certificate, environment, or human decisions does not count.

Blocked time must be visible in status reports.

Stop at the hard limit and return a variance report.

Do not add dependencies, reduce controls, widen the API, or increase scope to meet the limit.

The pilot covers simulator verification and one separately approved physical iPhone.

Production hardening is a separate phase.

High-cost operations include:

- Complete Xcode builds.
- Complete unit and UI test suites.
- Simulator boot and visual evidence capture.
- Accessibility audits.
- Physical-device builds and tests.
- Controlled external reviews.

## Required Delivery Evidence

- Exact baseline, branch, and final head.
- Exact changed-file list.
- Complete implementation diff inspection.
- Focused test output.
- Complete final test output.
- Request capture proving GET-only behaviour.
- Keychain lifecycle evidence.
- Persistence-boundary evidence.
- App-switcher privacy-cover evidence.
- Normal screenshot evidence.
- Copy-control evidence.
- Accessibility audit and manual checklist.
- Fictional simulator screenshots.
- Separate server compatibility evidence.
- Pocock specification and code-review records.
- Controlled Greptile record.
- Fresh Sol record.
- Exact-head human merge approval.

## Further Notes

This application is a read-only adapter to ACE.

ACE remains authoritative for authentication, G0, release selection, and released information.

Sift-KG and OpenViking are not prerequisites.

The installed Build iOS Apps capabilities support later build and simulator work.

They do not add code or dependencies to the application.

The exact private server address, certificate, bundle identifier, signing team, and Mac remain required delivery inputs.

This specification links to its Linear implementation issue:
[MCX-15](https://linear.app/mcxi-co/issue/MCX-15/sqe-implement-ace-ios-read-only-client-application).

Do not apply a ready state until Pocock, Security, and the user approve the required gates.

## Evidence Limitations

Apple's reviewed Keychain pages do not give publication dates.

They do not guarantee one complete returned-key list for every generic-password result.

They do not specify whether an application must accept or reject an unknown returned key.

ACE resolves this gap with the explicit ignore rule in the Exact Keychain Contract.

The application still rejects every missing, wrong-type, malformed, or mismatched required value.

No unresolved Apple evidence gap prevents this specification from defining a testable project contract.

## Evidence Sources

- `DEV_STATE.md` at controlled target `6b0160befc9191dbccd527bdd385b891782ddad8`.
- `ACE_PROGRESS_GUIDE.html` at the same controlled target.
- Existing `ClientReleaseResponse`, client route, authentication, projection, and storage-order contracts.
- Existing release-focused tests and Phase 6B2 compatibility records.
- Apple SwiftUI documentation: <https://developer.apple.com/swiftui/>.
- Apple URLSession documentation: <https://developer.apple.com/documentation/foundation/urlsession>.
- Apple URLSession configuration documentation: <https://developer.apple.com/documentation/foundation/urlsessionconfiguration>.
- Apple redirect delegate documentation: <https://developer.apple.com/documentation/foundation/urlsessiontaskdelegate/urlsession(_:task:willperformhttpredirection:newrequest:completionhandler:)>.
- Apple server-trust guidance: <https://developer.apple.com/documentation/foundation/performing-manual-server-trust-authentication>.
- Apple authentication-cancellation documentation: <https://developer.apple.com/documentation/foundation/urlsession/authchallengedisposition/cancelauthenticationchallenge>.
- Apple Keychain documentation: <https://developer.apple.com/documentation/security/using-the-keychain-to-manage-user-secrets>.
- Apple Keychain attribute documentation: <https://developer.apple.com/documentation/security/item-attribute-keys-and-values>.
- Apple Keychain item-class key documentation: <https://developer.apple.com/documentation/security/ksecclass>.
- Apple generic-password documentation: <https://developer.apple.com/documentation/security/ksecclassgenericpassword>.
- Apple Keychain account attribute documentation: <https://developer.apple.com/documentation/security/ksecattraccount>.
- Apple Keychain service attribute documentation: <https://developer.apple.com/documentation/security/ksecattrservice>.
- Apple Keychain access-group attribute documentation: <https://developer.apple.com/documentation/security/ksecattraccessgroup>.
- Apple Keychain creation-date attribute documentation: <https://developer.apple.com/documentation/security/ksecattrcreationdate>.
- Apple Keychain modification-date attribute documentation: <https://developer.apple.com/documentation/security/ksecattrmodificationdate>.
- Apple Keychain match-limit documentation: <https://developer.apple.com/documentation/security/ksecmatchlimit>.
- Apple Keychain synchronisation documentation: <https://developer.apple.com/documentation/security/ksecattrsynchronizable>.
- Apple all-synchronisation query value: <https://developer.apple.com/documentation/security/ksecattrsynchronizableany>.
- Apple Keychain query documentation: <https://developer.apple.com/documentation/security/secitemcopymatching(_:_:)>.
- Apple Keychain deletion documentation: <https://developer.apple.com/documentation/security/secitemdelete(_:)>.
- Apple Keychain return-key documentation: <https://developer.apple.com/documentation/security/item-return-result-keys>.
- Apple Keychain update and deletion documentation: <https://developer.apple.com/documentation/security/updating-and-deleting-keychain-items>.
- Apple Keychain access-group guidance: <https://developer.apple.com/documentation/security/sharing-access-to-keychain-items-among-a-collection-of-apps>.
- Apple Keychain accessibility documentation: <https://developer.apple.com/documentation/security/restricting-keychain-item-accessibility>.
- Apple selected Keychain accessibility value: <https://developer.apple.com/documentation/security/ksecattraccessiblewhenunlockedthisdeviceonly>.
- Apple DTS `SecItem` property-group guidance: <https://developer.apple.com/forums/thread/724023>.
- Apple pasteboard option documentation: <https://developer.apple.com/documentation/uikit/uipasteboard/optionskey>.
- Apple lifecycle guidance: <https://developer.apple.com/documentation/uikit/managing-your-app-s-life-cycle>.
- Apple ATS guidance: <https://developer.apple.com/documentation/security/preventing-insecure-network-connections>.
- Apple ATS configuration documentation: <https://developer.apple.com/documentation/bundleresources/information-property-list/nsapptransportsecurity>.
- Apple ATS exception-domain documentation: <https://developer.apple.com/documentation/bundleresources/information-property-list/nsapptransportsecurity/nsexceptiondomains>.
- Apple default trust-handling documentation: <https://developer.apple.com/documentation/foundation/urlsession/authchallengedisposition/performdefaulthandling>.
- Apple testing documentation: <https://developer.apple.com/documentation/xcode/testing>.
- Apple accessibility audit documentation: <https://developer.apple.com/documentation/accessibility/performing-accessibility-audits-for-your-app>.
- Apple VoiceOver documentation: <https://developer.apple.com/documentation/uikit/supporting-voiceover-in-your-app>.
- Apple accessibility guidance: <https://developer.apple.com/design/human-interface-guidelines/accessibility/>.
- Apple iOS 26 device list: <https://support.apple.com/en-in/guide/iphone/iphe3fa5df43/26/ios/26>.

Official Apple sources were checked on 24 August 2026.
