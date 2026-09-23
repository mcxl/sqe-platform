# ACE iOS Implementation And Verification Plan — Approved

Approved by Alan Richardson on 14 September 2026 through the instruction “PLEASE IMPLEMENT THIS PLAN”. This record preserves the accepted implementation plan and its limits. Runtime status belongs in IMPLEMENTATION_STATUS.md, not in this plan.

## Result And Authority

Deliver a verified, read-only fictional pilot on the approved iPhone 15 Pro Max using the approved private ACE service. Windows controls work and reviews results; source, builds and bulk evidence remain on the Mac. No manual transfers are required. Retain the current layout and defer Copy-confirmation lifetime changes.

The user's earlier “proceed unbounded with all approvals” replaces the ten-working-day limit for this task. Existing phone identification, installation and testing instructions provide the physical-device approval. Scope, data, security and merge restrictions remain. The eight-hour image-review threshold below controls expansion, not total task duration.

Mac worktree: LOCAL_HOME/Developer/sqe-platform-release-layout, branch codex/mcx19b-release-layout, base 7dc7cee7654ae8cc002da54324c3d1475a8494e6. At approval, four files were modified: ACEClientAppApp.swift, DebugScenario.swift, Views.swift and ACEClientAppUITests.swift in the iOS module. Windows remains on codex/mcx-19-live-evidence-harness with six modified and four untracked paths. Preserve that separate work.

## Implementation Order

1. Verify both required simulators execute: iPhone 17 and iPhone 17 Pro Max on iOS 26.4.1. Confirm phone access, signing, effective Keychain access group, storage and private evidence retrieval before dependent work. Obtain the approved private service address, certificate details and fictional account. Continue independent simulator work while these inputs are absent. Resolve the missing historical baseline without claiming unverified ancestry.
2. Diagnose the four retained failures before corrective source changes: light post-scroll (eight contrast, two inaccessible-text findings), maximum-text post-scroll (five contrast), no actions (one unidentified-element contrast), no conclusion (six Copy contrast, two inaccessible-text findings). Retrieve exact assertions and native evidence. State each diagnostic question, selected test and expected evidence; change one relevant variable. Separate app, test and environment faults. Pause correction of one fault after two failed corrective attempts. Preserve unsuccessful attempts. Do not add guessed waits, hide content, cap text or filter audits.
3. Carry forward earlier evidence with its actual candidate: shifted release crops recovered text at 21:1, without proving the complete mechanism; four of five noConclusion shifted crops were white-only; only Action description recovered partial content. The historical -56 timeout belongs to noActions. The plain-button diagnostic failed and was reversed. Callback-time positions do not establish sample-time positions. Earlier passes are historical evidence.
4. Add only necessary local support: a small Python standard-library runner and Apple tools, using generic build-for-testing, the generated xctestrun and test-without-building. Support preflight, selected tests, pilot and full coverage. Bind results to commit, source hashes, tools, device and observed settings. Preserve native bundles, assertions, images, process exit and test counts. Reject missing evidence, unexpected skips and incomplete runs. Restore simulator settings. Resume only an unchanged candidate and inputs. Use native Settings controls where command-line support is absent; verify effective settings inside the app. Repeat the deliberate failure/pass evidence gate after relevant runner changes; otherwise reuse valid checks. No new runtime dependency or snapshot framework.
5. Complete focused functional checks before broad visual work: sign-in, relaunch, refresh, sign-out, values and order, empty states, errors, cancellation, late responses, all eleven Copy values, Keychain lifecycle and rejected configuration. Existing 65 unit/contract tests include the 42 contract tests; do not count them twice or treat pending-record checks as runtime acceptance. No public API, schema or endpoint change.

## Coverage And Acceptance

Use all 18 existing states and both required simulators. Use all twelve system text sizes. The five complex states are signIn, release, noConclusion, noActions and copyConfirmation. Bold Text, Reduce Motion and Increase Contrast are off unless explicitly enabled.

| Group | Selection | Additional Unique Cases |
| --- | --- | ---: |
| Standard | 18 states, two devices, two orientations, two appearances, default text, all toggles off | 144 |
| Text sizes | 18 states, twelve sizes, two devices, portrait/light; remove standard overlaps | 396 |
| Difficult layouts | Five complex states, extra-large and maximum text, both devices/orientations/appearances; remove overlaps | 60 |
| Individual settings | All states, each toggle on separately, both devices/appearances, portrait/default text | 216 |
| Combined settings | Five complex states, all toggles on, maximum text, landscape, both devices/appearances | 20 |
| Total | Unique state/configuration cases | 836 |

Run unrestricted accessibility audits for 512 cases. The other 324 are layout-only cases at nine intermediate sizes. Retain all nine existing UI regression selectors and map their overlap. Unit tests, physical checks and additional viewports are separate counts. Update the specification's coverage record and superseded counts before the final candidate.

Every required automated check must pass. Native audit failures remain visible and prevent acceptance. A suspected Apple defect requires reproduction, contrary evidence and an explanation; screenshots alone are insufficient. Any proposed exception requires the user's specific decision. Never convert a failed native result into a pass. Manual image and physical accessibility checks remain required.

## Pilot And Resources

After implementation and runner checks, freeze a clean candidate. Run 22 pilot cases: five complex states on both devices at (A) default/portrait/light/all toggles off and (B) maximum/landscape/dark/all toggles on, plus release at medium/portrait/light on each device without full audit. Count the pilot toward 836 only when candidate and environment remain unchanged.

Measure execution, collection, storage, image inspection and waiting separately. Expansion requires all pilot cases passing, expected counts, observed settings, complete inspected/retrievable evidence, private access and retention checks, and the following resource gates:

- Mac free space covers twice projected remaining raw evidence, remaining build/scratch space and a 20 GiB reserve.
- Windows requires 5 GiB free before new evidence exports; stop exports below 2 GiB. Preserve existing work. Compact status records are distinct from bulk evidence exports.
- If projected image inspection exceeds eight active hours, revise capture/review arrangements before full execution. Do not silently reduce the 836 cases.

Estimate conservatively from the largest observed pilot case and image counts. Keep bulk evidence privately on the Mac for at least 30 days, with verified archives and retrieval. Windows receives compact records. Inspect exact SHA-256 duplicates once within an unchanged candidate, retaining every case association. Different hashes require inspection. Contact sheets aid navigation; inspect required images at full resolution. Keep per-case native audits/settings. Stop new batches at the first unresolved failure or evidence loss, then isolate the affected case.

## Physical Verification And Delivery

Use the approved iPhone 15 Pro Max. Complete eight VoiceOver journeys: sign-in recovery, release reading order, empty states, no conclusion/actions, failure recovery, all Copy controls, app-switcher privacy cover and failed Keychain deletion during sign-out.

Verify eleven clipboard values, announcements, local-only behaviour and five-minute expiry; actual maximum text size, both orientations/appearances; signed Keychain and specified locked-device checks; privacy cover and normal screenshots; approved-service sign-in/refresh/sign-out without fixture overrides; GET-only requests, required negative network checks and separate server compatibility evidence. Give one manual phone step at a time, then restore preferences.

Continue free signing. Check profile validity before installation/delivery. Current profile expires 21 September 2026 at 12:37:21 Sydney time. Rebuild, sign and reinstall before expiry, recording new product/profile identities and repeating affected signed-device checks. Keep the iPhone 16e simulator smoke check separate from mandatory coverage. Physical iPhone 16e behaviour remains untested.

Final gates: record approved plan changes; commit only task files; obtain required Pocock review; complete the programme on one clean unchanged candidate; inspect the complete diff, images and evidence; obtain a fresh Sol review; retain earlier Greptile evidence with its actual reviewed commit; reconcile every requirement as passed, failed, pending or blocked; install and launch the verified signed build. Application/test/runner/workflow changes create a new candidate and renew its required final programme. Historical results remain historical.

Delivery requires native, manual, service, signing and review evidence. An installed fixture alone is not completion. Exclusions: Codemagic, paid membership, TestFlight, App Store submission, new server development, real client data, Production deployment and automatic merge.
