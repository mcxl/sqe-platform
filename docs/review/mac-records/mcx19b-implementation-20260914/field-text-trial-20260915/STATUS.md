# Single Text Field Trial Result

The simple text change did not clear every native audit failure. It remains an isolated trial.

Maximum text passed on iPhone 17 Pro Max with iOS 26.4.1. Both empty states passed at default light settings. All eleven field checks passed.

The light release test failed at lines 697 and 708. Native audits reported two Copy action findings and one Copied Action 1. finding. Expected: no native findings. Actual: three contrast findings. Native exit 65; runner exit 2. No skips.

All maximum and focused PNG evidence was inspected. Native Copy and confirmation crops show complete text. Images alone do not explain internal audit sampling or authorise an exception.

The complete three-file source diff passed fresh Sol source review. Source review is not native acceptance.

The main Mac branch remains clean at 1b38b90e9a949b7e73965602612c11be6f19e9fc. No new phone installation occurred. No build or test process remains active.

Corrective design trials are paused under the approved two-attempt rule. No broad batch started. See RESULT.json, focused-fault.json, both image-review records and SOL_THREE_FILE_SOURCE_REVIEW.md.
