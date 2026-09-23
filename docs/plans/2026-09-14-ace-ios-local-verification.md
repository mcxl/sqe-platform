# ACE iOS Local Verification

## Status And Scope

Status: Current task record. This record implements the approved 14 September 2026 plan.

The user authority quote is `proceed unbounded with all approvals`.

The user already approved the iPhone 15 Pro Max for physical verification.

It does not report a completed verification gate.

The current verified worktree base is `7dc7cee7654ae8cc002da54324c3d1475a8494e6`.

The historical baseline `6b0160befc9191dbccd527bdd385b891782ddad8` is located in the original Windows repository. It is unavailable on the Mac and separate clones.

The 23-file iOS controlled source import from `91818a476c7ddb81c48aba63c76b11cfbcb70df4` to `d1507336ca6be5f6ae5f90227a66f10dffa83728` is proven by matching Git blob identifiers. Direct ancestry from the historical baseline to the imported harness fails with no common ancestor.

Baseline-dependent acceptance remains BLOCKED for review. Do not transfer history, infer ancestry, or treat the required baseline as waived.

The application remains a fictional, read-only GET client. Keychain, security, privacy, and no-Production controls remain unchanged.

## Approved Copy Design Change — 15 September 2026

The user confirmed one Copy button for a complete action record. This supersedes individual-field Copy controls. All eleven field types remain readable. Each action card contains one `Copy action` button below its four values. Release details and conclusion fields have no Copy controls.

The exact copied record is the visible `Action N` heading, then Description, Owner, Target date and Status with their values. Use LF separators and no trailing LF. The specification owns the exact text contract. Keep native UTF-8 plain text, device-only handling, five-minute expiry, visible confirmation and the accessibility announcement.

This is an approved product change. It is not evidence that the earlier native accessibility failures are corrected. Keep the earlier eleven-field test results as historical evidence.

Focused acceptance checks are exact complete-action copying, selection of the correct record when two actions exist, repeated copying, preserved displayed values, absence of individual-field Copy controls, and no Copy control when no actions exist. Use a DEBUG-only multiline native Paste destination if needed to verify LF preservation. Such support fixtures do not extend the mandatory eighteen-state catalogue.

Inspect affected release, no-conclusion, no-actions and Copy-confirmation screens at default and maximum text in both appearances. Run unrestricted native audits before acceptance. Existing failures remain visible. Keep the 836-case decision and all unrelated privacy, signing, service, baseline and review gates.

## Environment And Devices

Observed toolchain: Xcode 26.4.1 (`17E202`) and iOS 26.4.1 runtime (`23E254a`).

Required simulators are iPhone 17 and iPhone 17 Pro Max on iOS 26.4.1.

The approved physical device is iPhone 15 Pro Max.

The iPhone 16e simulator is optional compatibility evidence. It is not part of required coverage.

Free-signing profiles are valid for seven days. Local signing evidence records expiry at `2026-09-21 12:37:21 AEST`. Before installation or delivery, check the profile expiry. Renew before expiry by re-signing with the same approved bundle and signing team. Then repeat affected signed-device checks.

## Discovery Transition — 17 September 2026

The user approved closing the D1 positioning experiment as incomplete and proceeding to P0 runner work.
The [discovery candidate record](2026-09-17-ace-ios-discovery-candidate.md) defines the change, bounded work block and planned verification.
This does not waive the unresolved Copy finding or reduce final acceptance requirements.

Discovery runs each pilot case independently and preserves every native failure.
It stops on lost evidence, unexpected or incomplete native execution, failed launch, infrastructure faults or failed restoration.
A completed discovery run with failures is not acceptance. The default acceptance pilot still requires every gate to pass.
No D1 diagnostic procedure enters the application or committed UI tests under this transition.

## Local Runner And Evidence

Use a Python standard-library local runner and Apple tools only.

Use generic `build-for-testing`, the generated `xctestrun`, and `test-without-building`.

The current inventory contains 68 unit and contract tests, including 43 contract tests. The retained action-Copy run confirms these counts on its earlier candidate. Run the required current-candidate checks. Do not count the subset twice.

Record each test count and its evidence inside the native result bundle.

The earlier one-command-per-unit retention workflow is historical. It does not control current execution.

Retain raw evidence privately for at least 30 days. Verify authorised retrieval and unauthorised denial. Windows receives compact records only.

Inspect exact SHA-256 duplicate images once while the candidate remains unchanged. Retain every case association. Inspect images with different hashes at full resolution.

Every required automated check must pass. No native audit exception is assumed.

A proposed proven tool-defect exception requires the user’s specific decision. Never convert a failed native result into a pass.

## Coverage Matrix

Use `DEFAULT` for default text, `EXL` for extra-large text, and `MAX` for accessibility extra-extra-extra-large text.

| Group | Configuration And Deduplication | Native Audits | Layout Only | Unique Cases |
| --- | --- | ---: | ---: | ---: |
| Standard | 18 states; two devices; portrait and landscape; light and dark; default text; all toggles off | 144 | 0 | 144 |
| Text sweep | 18 states; all twelve text sizes; two devices; portrait; light; all toggles off; remove 36 default-text overlaps from Standard | 72 additional audits at `EXL` and `MAX`; `DEFAULT` is audited in Standard | 324 at the other nine sizes | 396 |
| Difficult layouts | Five complex states; `EXL` and `MAX`; two devices; both orientations; both appearances; remove 20 portrait-light overlaps from Text sweep | 60 | 0 | 60 |
| Individual settings | 18 states; each setting on separately; two devices; portrait; default text; both appearances | 216 | 0 | 216 |
| Combined settings | Five complex states; all three settings on; `MAX`; landscape; two devices; both appearances | 20 | 0 | 20 |
| Total |  | 512 | 324 | 836 |

The five complex states are sign-in, release, no conclusion, no actions, and copy confirmation.

Retain the nine existing UI regression selectors and record their overlap.

## Pilot And Resource Gates

Run 22 pilot cases on one unchanged candidate.

The approved plan permits independent simulator work while service checks are blocked. The simulator pilot uses built-in fictional fixtures. Its private-input record must identify these fixtures, their source hashes, and private evidence access. Confirm that fixture launch skips service startup. Do not record the missing approved service address, certificate, account, phone access, or signed-device checks as passed. Those inputs remain required before their dependent checks and final delivery.

Record the pilot readiness scope explicitly as simulator fixtures and private evidence. This does not waive the historical baseline, security, service, physical-device, or final review gates.

For every complex state and required simulator, run A at `DEFAULT`, portrait, light appearance, and all toggles off. Run B at `MAX`, landscape, dark appearance, and all toggles on.

Run release at medium text, portrait, and light appearance on both simulators without a full audit.

Expand only if all 22 cases pass. Confirm expected counts, observed settings, complete inspected retrievable artifacts, private access, and retention controls.

Mac free space must cover twice the projected remaining raw evidence, required build and scratch space, and a 20 GiB reserve.

Windows must have 5 GiB free before a new evidence export. Stop exports below 2 GiB.

If projected image inspection exceeds eight active hours, revise the capture and review arrangement before the complete programme. Do not reduce the 836 cases.

## Historical Diagnostics

The current retained failures need diagnosis before correction: light post-scroll has eight contrast and two inaccessible-text findings; maximum-text post-scroll has five contrast findings; no actions has one unidentified-element contrast finding; no conclusion has six Copy contrast and two inaccessible-text findings.

Historical shifted release crops recovered text at 21:1. This does not prove the complete mechanism.

Four of five historical no-conclusion shifted crops were white-only. Only the Action description recovered partial content.

The historical `-56` timeout belongs to no actions. The plain-button diagnostic failed and was reversed. Callback-time positions do not establish sample-time positions.

## Final Candidate Gates

1. Run focused checks and retain diagnostic evidence.
2. Freeze a clean candidate commit.
3. Obtain Pocock review on that candidate.
4. Run the 22-case pilot and complete programme on the unchanged candidate.
5. The primary session inspects the complete diff, native evidence, and images.
6. Obtain a fresh Sol review on that inspected unchanged head.
7. Reconcile every requirement as passed, failed, pending, or blocked.
8. Install and launch the verified signed build.
9. Obtain exact-head merge approval only before any later merge. Do not merge automatically.

Renew steps 2 through 8 after any relevant application, test, runner, workflow, or documentation change.

The earlier Greptile result remains historical evidence for its reviewed commit only.
