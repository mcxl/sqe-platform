# Pocock Specification Review

Candidate: b9ba714d99862e9ef5572b7eb2a1b1d6471d0932.
Base: 7dc7cee7654ae8cc002da54324c3d1475a8494e6.
Both objects were verified. The merge base matches the stated base. The worktree is clean.

## Finding

[P1] The full-programme image gate cannot pass with the implemented pilot captures.

In tools/ace_ios_local.py:866-878, image_maximums counts attachments for a complete pilot batch. The calculation then uses this batch count for each remaining case.

Each five-case pilot batch retains at least 36 explicit images: release 13, noConclusion 10, noActions 9, signIn 2, copyConfirmation 2. See ios/ACEClientApp/ACEClientAppUITests/ACEClientAppUITests.swift:123-134, 188-253 and 275-285. The pilot retains 22 reusable cases. Thus the minimum projected count is 814 x 36 = 29,304 images.

tools/ace_ios_local.py:900-906 rounds measured seconds per image up to an integer. It requires a positive value. Its smallest projection is therefore 29,304 seconds, above the fixed 28,800-second limit. Every otherwise valid full-run request is blocked.

The plan requires: "If projected image inspection exceeds eight active hours, revise the capture and review arrangement before the complete programme. Do not reduce the 836 cases." It also requires expansion after all pilot gates pass.

Calculate the remaining image count from per-case captures or remaining batches. Preserve associations when duplicate image hashes share one inspection. Provide a recorded revised review arrangement when needed. Verify the gate with retained pilot-shaped records.

## Scope And Limits

The source defines the approved 836 cases, 512 audit cases, 324 layout-only cases, and 22-case pilot. It retains layout and Copy changes. It checks observed settings, native results, candidate identity, and restoration.

No native build or test was run for this review. This is a source review, not delivery acceptance.

The four native faults, private inputs, historical baseline decision, native programme, physical checks, and final Sol review remain open. This finding is separate from those pending gates.
