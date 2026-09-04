# Phase 6.1 Evidence Register

This public G0 register is planning-only. It is not release evidence. It does not
run, collect, publish, or accept client evidence.

Use `mcxl/sqe-platform`. A reviewed record must name the executing Git head. Historical
commit text is not an active control.

`Phase6_1EvidenceRegister.json` is the controlled mapping. It contains 44 pending
entries in ten pending packages. The JSON record is authoritative.
Each result uses its controlled schema. It includes package and entry.

An approved reviewer can mark an entry reviewed only when these fields are complete:

- Repository, commit, package, entry, status, artifact, and reviewer.
- Device and software, when the package uses them.
- Operator, date, and result.

The repository must be `mcxl/sqe-platform`. The commit must be the executing Git head.
The package and entry must match the controlled mapping. The artifact must be below the
controlled artifact root. A pending package and entry keep all result fields blank.

Do not change `releaseEvidence` from `false`. Reviewed public records do not become
release evidence.

Use `ace-ios-evidence-preflight-manual` only after approval. The workflow has no
automatic trigger. Use fictional data only.

For simulator preparation, select one exact device type and the highest available iOS
26.x runtime. Poll for no more than 30 seconds. Give each `simctl list -j` command the
remaining monotonic time. Fail on a command timeout, missing type, duplicate UUID,
wrong runtime, or unavailable device. Do not create the target again.

Keep logs, result bundles, and fictional images below
`ios/ACEClientApp/build/phase6-1/`. Review them before record acceptance. Do not record
passwords, authorisation values, Keychain secrets, or client data.
