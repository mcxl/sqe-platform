# Initial-Audit Sequence Comparison

Status: BOTH RUNS FAILED — DIAGNOSTIC ONLY.

Parent source commit: `7fee853aef52e85a813368a51d833c134710186d`. A private test copy adds one flag around the first audit. Both runs use the same build products.

Question: Is the initial unrestricted audit necessary for the later post-scroll failure?

Control: one post-scroll contrast finding without an identified element. Initial audit passed.

Initial audit omitted: seven Copy contrast findings and two potentially inaccessible-text findings at private test line 575.

Both native commands exited 65. Each ran one test, with one failure and no skips. Products, repository source and relevant simulator settings remained unchanged.

The first audit is not necessary for the post-scroll failure. No correction is demonstrated. Do not remove it from the actual regression selector. Full-resolution review of all retained distinct images is recorded separately; incomplete inspection remains pending.

Evidence: `source-provenance.json`, `build-identity.json`, `diagnostic.json`, `control/`, `omit-initial/`.
