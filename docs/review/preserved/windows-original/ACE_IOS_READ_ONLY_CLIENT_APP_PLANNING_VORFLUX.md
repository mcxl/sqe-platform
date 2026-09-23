# Vorflux Investigation: ACE Read-Only iOS Client Application

## Document Status

Status: Draft For Human Approval.

This instruction permits research, comparison, and design planning only.

It does not permit implementation, installation, deployment, or repository changes.

Vorflux must return one report for local Codex and auditor review.

## Authority

Vorflux can review current official technical sources.

Vorflux can compare implementation approaches and prepare a bounded design recommendation.

Vorflux must not create code, an Xcode project, an account, or a deployment.

Vorflux must not install, clone, download, or run a tool or sample application.

Vorflux must not send repository files to a model, provider, or hosted demonstration.

## Goal

Define the smallest safe iOS application that reads the current ACE client release.

The first application must remain read-only and use the existing ACE API.

The report must define the product, architecture, security, user experience, tests, and pilot gates.

The report must prepare a later local implementation task. It must not start that task.

## Baseline

Use this controlled repository baseline:

- Repository: `mcxl/agentic-os-workspace`.
- Branch: `origin/codex/ace-sprint-1`.
- Controlled target: `6b0160befc9191dbccd527bdd385b891782ddad8`.
- Phase 6B2 implementation head: `ddd1b69d84cdc36cb7a28f3aed6ae83a5119b0dd`.
- Phase 6B2 implementation merge: `a1d52c6148b64106ed1a4516aec8e72aea4ef666`.
- Phase 6B2 documentation head: `759cfa0fab3b8cb423bc0f2808f4f2289710c54b`.
- Phase 6B2 documentation merge: `6b0160befc9191dbccd527bdd385b891782ddad8`.

Treat this baseline as fixed for the investigation.

Stop if local Codex reports a different controlled remote target.

## Sanitised Hand-Off Pack

Local Codex can supply reviewed copies of these records:

- `docs/specs/phase6b2-read-only-client-release-projection.md`.
- Relevant extracts from `ACE_PROGRESS_GUIDE.html`.
- This instruction.

Do not send the repository or its Git history.

Do not send source code, database files, credentials, environment files, or temporary files.

Do not send `DEV_STATE.md`, client records, source evidence, or audit records.

Do not send real names, personal information, or real Engagement information.

Use fictional examples in every diagram, fixture, and response example.

## Current Phase 6B2 Contract

The existing client endpoint is:

`GET /client/api/v1/release/current`

The successful compatibility response has these records:

- HTTP status: `200`.
- Content type: `application/json`.
- Size: `599` bytes.
- SHA-256: `5e19bc98c09286a2eb8181650462cfb5ae6952eb342da080643d54a8ab6856af`.

The response exposes only:

- Engagement name.
- Review status.
- Release version.
- Published time.
- Conclusion title.
- Conclusion summary.
- Conclusion evidence reference.
- Action description.
- Action owner.
- Action target date.
- Action delivery status.

The API excludes internal identifiers, approval attribution, audit history, and withdrawal details.

## Locked Boundaries

- ACE remains the authoritative audit system.
- The auditor remains the approval authority.
- The iOS application calls only a versioned ACE API.
- The application does not connect to SQLite or another database.
- The application does not call Sift-KG or OpenViking.
- The application contains no provider credential.
- The application creates no audit, release, decision, approval, or client record.
- Client access remains read-only.
- Existing client authentication remains unchanged for the first slice.
- G0 remains active.
- Use fictional information only.
- Do not use real client information.
- Do not add client editing.
- Do not add a new authentication method.
- Do not add analytics, advertising, tracking, or crash-reporting services.
- Do not add a paid provider.
- Do not add a backend route, schema, migration, or trigger.
- Do not deploy to Production.
- Do not submit to the App Store or TestFlight.
- Do not add persistent offline release storage without a separate decision.

Do not recommend a boundary change without a separate decision request.

## Required Architecture Flow

Review this logical flow:

```text
iOS application
      -> HTTPS ACE client API
      -> client authentication and G0
      -> ClientReleaseService and ClientReleaseStorage
      -> ClientReleaseProjection
      -> existing ClientReleaseResponse
      -> read-only SwiftUI presentation
```

Confirm these controls:

- The application cannot bypass ACE authentication or G0.
- The application cannot access provider or database credentials.
- The application sends no write request.
- The application does not become a second authoritative record.
- An application failure cannot change an ACE record.

## Product Decision

Compare these product interpretations:

1. A read-only client release viewer.
2. A full auditor field application.
3. A combined client and auditor application.

Use the first interpretation as the recommended Phase 1 boundary.

Explain why the other interpretations need separate specifications and controls.

## Implementation Approach Review

Compare these approaches:

1. Native SwiftUI from the current Xcode iOS App template.
2. React Native with Expo.
3. A responsive web application or wrapped web view.

For each approach, assess:

- Fit for one read-only endpoint.
- iPhone and iPad support.
- Accessibility.
- Test support.
- Credential handling.
- Dependency count.
- Build and signing complexity.
- Long-term maintenance.
- Offline-data risk.
- App Store and TestFlight implications.
- Compatibility with the local Build iOS Apps plugin.

Recommend one approach. Do not create it.

Prefer the smallest design that meets the locked boundaries.

## External Template Review

Review these current official or maintainer-controlled sources:

- Xcode iOS App template with SwiftUI.
- Apple Develop in Swift and Scrumdinger materials.
- Apple Food Truck sample for adaptive iPhone and iPad navigation.
- Apple Keychain examples for Internet passwords.
- Apple Swift Testing and XCTest UI guidance.
- Apple Swift OpenAPI Generator.
- XcodeGen and Tuist project templates.
- The Composable Architecture examples.

For each source, record:

- Owner and URL.
- Current version or applicable Xcode release.
- Access date.
- Useful pattern.
- Unneeded features.
- Licence.
- Dependency or tool impact.
- Recommendation: use, reference, defer, or reject.

Do not rely on an outdated tutorial without a visible warning.

Do not recommend a third-party dependency when Apple frameworks meet the need.

## API Client Decision

Compare two API-client approaches:

1. A small `URLSession` client with hand-written `Codable` models.
2. A generated client from the FastAPI OpenAPI document.

Assess the benefit for one current endpoint.

Record the dependency and build effect of Swift OpenAPI Generator.

Recommend whether to defer generation until more endpoints exist.

The report must not change the existing API contract.

## Authentication And Credential Review

The first slice must reuse existing client authentication.

Compare these credential choices:

1. Keep credentials only in memory for the application session.
2. Store a validated Internet password in iOS Keychain.

For each choice, assess:

- User experience.
- Device-loss risk.
- Sign-out behaviour.
- Error recovery.
- Screenshot and application-switcher exposure.
- Logging risk.
- Testability.

Do not recommend plain-text storage, source-code secrets, or user defaults for passwords.

A new token, identity provider, or sign-in method is outside this instruction.

## Network And Environment Review

Define a non-Production network plan.

Review these environments:

- Unit tests with a mock transport.
- Xcode previews with fictional fixtures.
- iOS Simulator against a local ACE server.
- A physical development device against an approved private Preview or local server.

Address:

- HTTPS requirements.
- App Transport Security.
- Local-network permission where applicable.
- Timeouts and cancellation.
- Retry behaviour.
- Certificate and hostname errors.
- No-network behaviour.
- Server-unavailable behaviour.

Do not propose a Production endpoint.

## User Experience And State Matrix

Design a small SwiftUI information structure.

The first slice should need no more than these screens:

1. Client sign-in or credential entry.
2. Current release.
3. Settings or sign-out, only when required.

Define the visible result for each condition:

| Condition | Required Result |
|---|---|
| Valid fictional published release | Show the current release fields. |
| No published release | Show `Release unavailable`. |
| Missing Engagement | Show `Engagement not found`. |
| No conclusion | Show the existing empty conclusion state. |
| No actions | Show the existing empty action state. |
| Several actions | Preserve API order. |
| Missing credentials | Request credentials without revealing configuration details. |
| Invalid credentials | Show a generic access failure. |
| Missing server configuration | Show a generic unavailable state. |
| G0 rejection | Show a generic unavailable state. |
| No network | Explain that ACE could not be reached. |
| Timeout | Offer a safe retry. |
| Invalid response | Fail closed and show no partial release. |

Do not show internal identifiers or error traces.

Do not let colour alone communicate state.

## Accessibility And Device Review

Define acceptance criteria for:

- VoiceOver labels and reading order.
- Dynamic Type, including accessibility sizes.
- Sufficient contrast.
- Reduce Motion.
- Bold Text.
- Light and dark appearance.
- Portrait and landscape layouts.
- Small supported iPhone screens.
- iPad layout when iPad enters scope.
- Keyboard navigation when iPad enters scope.

Recommend the minimum iOS version from current official evidence.

Do not select a minimum version only for a visual effect.

## Sift-KG And OpenViking Boundary

Sift-KG and OpenViking are not prerequisites for the first read-only iOS slice.

Keep these rules:

- Sift-KG can supply server-side proposals and an exploratory graph only.
- OpenViking can supply server-side context search only after its gates pass.
- The iOS application calls neither provider.
- The iOS application stores no provider credential.
- Provider completion cannot block the read-only release viewer.
- A later provider-backed mobile feature needs a separate ACE API specification.

Do not include provider screens in the first iOS slice.

## Security And Privacy Review

Prepare a small threat and control table.

Include:

- Credential exposure.
- Transport interception.
- Cross-Engagement information.
- Stale or partial response display.
- Sensitive logging.
- Clipboard exposure.
- Application-switcher snapshots.
- Device backup and local persistence.
- Screenshot policy.
- Debug configuration entering a release build.
- Base URL substitution.
- Provider credential exposure.

For each threat, record the control, evidence, residual risk, and owner.

Do not give a legal conclusion.

## Test And Evidence Plan

Define these test layers:

- Pure model-decoding tests.
- API-client tests with a mock transport.
- View-model state tests.
- SwiftUI view tests where supported.
- XCTest UI tests for the main user journey.
- Accessibility checks.
- Simulator verification.
- One physical-device pilot after separate approval.
- Existing ACE API compatibility checks.
- Proof that the application sends no write request.

Use fictional fixtures only.

Include success, empty, authentication, G0, network, timeout, and invalid-response fixtures.

Preserve the current ACE API and HTML compatibility records.

## Local Implementation Workflow

The later implementation must use a fresh Codex task.

The local task must invoke `$sol-advisor:orchestration`.

Use the installed Build iOS Apps capabilities where applicable:

- `swiftui-ui-patterns` for SwiftUI structure.
- `ios-debugger-agent` for build and run checks.
- `ios-simulator-browser` for simulator visual checks.
- `swiftui-performance-audit` only after the main flow works.

Do not require App Intents, Liquid Glass, or memory analysis in the first slice.

The primary local session must inspect the complete diff and rerun relevant verification.

## Required Planning Output

Return one Markdown report named:

`ACE_IOS_READ_ONLY_CLIENT_APP_VORFLUX_REPORT.md`

Use these sections:

1. Executive Summary.
2. Evidence And Versions.
3. Product Boundary.
4. Approach Comparison.
5. Recommended Architecture.
6. External Template Review.
7. API Contract And Client Decision.
8. Authentication And Credential Decision.
9. Network And Environment Plan.
10. Screen And State Matrix.
11. Accessibility Plan.
12. Security And Privacy Review.
13. Test And Evidence Plan.
14. Proposed File Structure.
15. Bounded Implementation Stages.
16. Estimate And Hard Limit.
17. Open Decisions.
18. Stop Conditions.
19. Pilot Readiness.
20. Recommended Next Action.

For each material technical claim, cite current official evidence.

Mark each decision as `recommended`, `needs human decision`, or `blocked`.

The report must separate confirmed facts from design recommendations.

## Planning Limits

Use a four-hour hard limit for this investigation.

Use no more than one final report.

Do not run builds, tests, sample applications, package managers, or security scans.

Do not use a public hosted demonstration.

Do not create an Apple, provider, or developer account.

Stop after two failed attempts to confirm one material technical fact.

Report the unresolved fact as unknown.

## Acceptance Criteria

- The report recommends one bounded read-only iOS slice.
- The report keeps ACE and auditor authority unchanged.
- The report keeps the iOS application on the ACE API only.
- The report treats Sift-KG and OpenViking as separate server-side candidates.
- The report compares SwiftUI, Expo, and web-wrapper approaches.
- The report assesses reusable templates from current official evidence.
- The report defines authentication and credential options.
- The report defines all required user-visible states.
- The report defines accessibility acceptance criteria.
- The report defines security, privacy, and network controls.
- The report defines a test and pilot evidence plan.
- The report names all open human decisions.
- The report adds no implementation, dependency, tool, or repository change.

## Stop Conditions

Stop and report the issue before:

- Requesting or receiving real client information.
- Uploading the repository or Git history.
- Sending source code, credentials, or client records externally.
- Installing, cloning, downloading, or running a tool or sample application.
- Creating an Apple or provider account.
- Starting an implementation.
- Creating an Xcode project.
- Changing an architecture or security boundary.
- Recommending a new authentication method as approved.
- Adding persistent offline storage as approved.
- Making a remote model call with supplied content.
- Starting Sift-KG or OpenViking.
- Deploying to Preview or Production.
- Submitting to TestFlight or the App Store.
- Giving a legal conclusion.
- Exceeding the hard limit.

## Local Acceptance

Local Codex must inspect the returned report and all citations.

The auditor must decide product, method, and approval questions.

Security must decide credential, transport, and device-storage questions.

Legal must decide licence and distribution questions where applicable.

The user must approve the final iOS specification before implementation.

The user must approve any later dependency, tool, deployment, or provider work.
