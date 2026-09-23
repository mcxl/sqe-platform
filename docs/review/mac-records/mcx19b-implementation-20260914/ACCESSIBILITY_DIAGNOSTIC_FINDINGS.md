# Accessibility Diagnostic Findings

Status: UNRESOLVED. Native failures block acceptance. No exception is requested or approved.

## Current Question

Why does the unrestricted native audit report contrast and inaccessible-text failures after scrolling, when retained images show readable text?

## Evidence Carried Forward

| Check | Observed result | What it establishes |
| --- | --- | --- |
| Current release, source hashes matching 7fee853 | Seven Copy contrast and two inaccessible-text findings; native exit 65 | The current app still fails this required check |
| Reduced private view | Eight Copy contrast and two inaccessible-text findings; initial audit passed | The reduced layout can reproduce the failure without network, Keychain, session actions, Refresh or Sign out |
| Reduced view, stability observation and same-build control | Both later runs passed | A passing retry does not prove a timing correction |
| Initial-audit sequence pair | Control: one unidentified contrast finding. Omitted initial audit: seven Copy contrast and two inaccessible-text findings | The initial audit is not necessary for the later failure |
| Existing phone-preview option omits diagnostic label | One unidentified contrast finding, plus the two expected missing-label assertions | The diagnostic label is not necessary for every native failure |

Sequence-pair and metadata runs use Xcode 26.4.1 (17E202), iPhone 17 Pro Max simulator, iOS 26.4.1 (23E254a), macOS 26.6.2, default large text, portrait and light appearance. Relevant settings were restored. The actual repository and app source remained unchanged.

## Contrary Evidence And Limits

The sequence-pair result contains seven byte-identical native Copy crops. The inspected crop contains black text and icon on grey RGB (198,198,203). Its measured solid-colour contrast is 12.341:1 in sRGB. The crop is 278 by 174 pixels. See `release-audit-sequence-pair/native-crop-colours.json` and its command record.

This is contrary evidence to the reported Copy contrast failures. It does not identify the pixels used internally by the audit. Full-screen captures before the audit and native failure images have different vertical content positions. The retained video also shows text-size changes during unrestricted auditing. None of those observations establishes internal sample times.

The unidentified contrast finding does not name an element. The inaccessible-text findings do not identify their text regions. Default blue controls remain a separate observation because rendered font size and weight have not been established. Do not change them based on an unidentified failure.

The older no-conclusion white-only crops and historical no-actions -56 timeout remain separate historical evidence.

## Inspection And Provenance

- `release-current-build/`: 29 PNG files, five distinct hashes, inspected; selected video frames inspected.
- `release-audit-sequence-pair/`: 43 PNG files, 13 distinct hashes, inspected at original resolution. Both native commands exited 65.
- `release-metadata-omitted/`: 14 PNG files, six distinct hashes, inspected at original resolution. Native command exited 65.
- `minimal-audit-repro/`: earlier private source copy, with its own source hashes and results. It is not the final candidate.

Each diagnostic directory retains command inputs, native result bundle, assertions, logs and attachments. Use those source identities. Do not relabel earlier candidates as final results.

## Decision

No demonstrated app correction emerged from these comparisons. Keep the product layout and unrestricted audit unchanged. Pause broad coverage. Continue independent functional checks.

The retained reduced reproduction can support a report to Apple after review. This file is a private draft; no report was sent. Do not submit private raw artifacts without checking their contents and obtaining authority for that external submission.

Any future diagnostic must identify a new observable mechanism. Repeating the same native run alone will not resolve this fault. An exception needs a separate, specific user decision under the approved plan.
