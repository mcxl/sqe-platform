# Minimal Native Audit Reproduction

This private fixture tests whether the observed native audit result survives without release data, network access, Keychain work, session state, notices, refresh, or sign-out actions.

It retains the relevant visual structure:

- DEBUG RootView padding and the existing diagnostic safe-area inset.
- One ScrollView with the current 20-point stack spacing.
- The current secondary-background rounded cards.
- The current ValueRow implementation, including Dynamic Type, black primary text, combined field accessibility node, bordered Copy button, primary tint, and 44-point target.
- Eight rows across a release-details card and an action card.

The fixture adds only minimalAuditRepro, MinimalAuditReproView, and two UI-test selectors. See SOURCE_PROVENANCE.md.

testMinimalAuditReproAllAudits performs initial unrestricted .all, scrolls to the bottom sentinel, then repeats unrestricted .all.

testMinimalAuditReproContrastOnlyAfterScroll performs the same scroll and then a contrast-only audit. It does not run .all.

Commands have now run. See results-minimal-audit-repro/ and all-image-review.json for retained native results and source identities. The original command files remain part of the historical record.

Interpretation:

- Initial .all passes and post-scroll .all fails: the reduced structure is sufficient for the observed audit result. This does not prove an Apple-tool defect.
- Both .all audits pass: the selected run did not reproduce the finding. This alone cannot identify a necessary component or prove the application source is correct.
- Contrast-only passes after scrolling while post-scroll .all fails: the audit mask or its processing affects the result. This does not identify an undocumented mechanism.
- Contrast-only also fails: inspect the retained issue nodes and screenshots before any source correction.

A result from this fixture cannot accept, reject, or release the product candidate.
