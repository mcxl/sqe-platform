# Phase 6.1 Evidence Register

This public G0 register is planning-only. It is not release evidence. It does not
run, collect, publish, or accept client evidence.

Use `mcxl/sqe-platform`. A reviewed record must name the executing Git head. Historical
commit text is not an active control.

`RuntimeEvidencePlan.json` owns the controlled package-to-identifier mapping.
`Phase6_1EvidenceRegister.json` contains the checked register mapping. It has 44
pending entries in ten pending packages. Each result uses its controlled schema. It
includes package and entry.

An approved reviewer can mark an entry reviewed only when these fields are complete:

- Repository, commit, package, entry, device, software, operator, date, result,
  artifact, and reviewer.
- Status: reviewed.

The repository must be `mcxl/sqe-platform`. The commit must be the executing Git head.
The package and entry must match the controlled mapping. The artifact must be below the
controlled artifact root. A pending package and entry keep all result fields blank.

Do not change `releaseEvidence` from `false`. Reviewed public records do not become
release evidence.

Use `ace-ios-evidence-preflight-manual` only after approval. The workflow has no
automatic trigger. Use fictional data only.

For simulator preparation, select one exact device type and the highest available iOS
26.x runtime. Use one 30-second monotonic deadline for creation and polling. Give each
`simctl create` or `simctl list -j` command only the remaining time. Fail on a command
timeout, missing type, duplicate UUID, wrong runtime, or unavailable device. Do not
create the target again.

Keep logs, result bundles, and fictional images below
`ios/ACEClientApp/build/phase6-1/`. Review them before record acceptance. Do not record
passwords, authorisation values, Keychain secrets, or client data.
