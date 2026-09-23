# Pocock Specification Review

Candidate: 7fee853aef52e85a813368a51d833c134710186d.
Previous reviewed candidate: b9ba714d99862e9ef5572b7eb2a1b1d6471d0932.

Result: The original P1 specification finding is closed. No new material specification defect was found in this delta.

I inspected the pinned Git diff. It changes only tools/ace_ios_local.py and tools/tests/test_ace_ios_local.py. I reused the unchanged source review from b9ba714. I did not inspect the concurrent temporary worktree probe as candidate source.

The runner now measures case-linked images separately from unmapped native images. Its projection uses maximum case captures per remaining case, plus maximum unmapped images per remaining batch. It no longer applies a five-case image count to every remaining case.

The review gate includes every retained PNG/JPG image hash. It retains case associations while permitting one inspection for duplicate hashes. It accepts a measured revised review arrangement with candidate identity, pilot identity, complete image coverage, and evidence hashes.

This implements the plan clause: "If projected image inspection exceeds eight active hours, revise the capture and review arrangement before the complete programme. Do not reduce the 836 cases."

The raw evidence calculation uses the largest pilot batch as a stated conservative upper bound per remaining case. It preserves the two-times evidence allowance, scratch allowance, and 20 GiB reserve.

I reviewed the retained primary check record. It reports 24 passing Python checks and a passing diff check. The added tests cover the full 22-case pilot gate, changed images, unreviewed native images, and a revised review arrangement. I did not run tests or native commands.

This is source review approval for the inspected delta. It is not delivery acceptance. Native failure/pass evidence, unresolved native faults, private service inputs, historical baseline acceptance, the pilot and complete programme, manual and physical checks, and final Sol review remain subject to their required evidence.
