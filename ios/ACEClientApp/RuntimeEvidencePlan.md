# Runtime Evidence Plan

This public G0 plan is not release evidence. It does not run, collect, publish, or
accept client evidence. All records are pending.

Use `mcxl/sqe-platform`. A reviewed record must name the executing Git head. Do not
use an old commit as an active control.

The machine-readable plan is `RuntimeEvidencePlan.json`. The controlled register is
`Phase6_1EvidenceRegister.json`. They map 44 identifiers to ten pending packages.
Each result uses the controlled result-field schema. It includes package and entry.

Use `ace-ios-evidence-preflight-manual` only after approval. It prepares evidence. It
does not accept evidence or change `releaseEvidence`.

For each reviewed record, check these identity fields:

- Repository: `mcxl/sqe-platform`.
- Commit: the executing Git head.
- Package and entry: the registered package and identifier.
- Status, artifact, and reviewer.
- Device and software, when the package uses them.

Keep every pending result field blank. A pending record cannot claim review or release
evidence.

For simulator preparation, resolve exact device types and one highest available iOS
26.x runtime. Poll for no more than 30 seconds. Use the remaining monotonic time as
each `simctl list -j` timeout. Fail on a hang, missing type, duplicate UUID, wrong
runtime, or unavailable device. Do not create a target again.

Keep only controlled fictional artifacts. Do not record passwords, authorisation
values, Keychain secrets, or client data.
