# Runtime Evidence Plan

This public G0 plan is planning only. It is not release evidence. It does not run,
collect, publish, or accept client evidence. All repository records remain public and
pending. `releaseEvidence` remains `false`.

The controlled repository is `mcxl/sqe-platform`. The live gate checks the exact Git
head, clean tree, approved remote, and ancestry from
`7da6228dc87ad970aa8d44365fbc3823c58020da`. It records the exact executing commit
only in the external artifact manifest.

`RuntimeEvidencePlan.json` owns the independent package-to-identifier mapping.
`Phase6_1EvidenceRegister.json` contains the checked register mapping. They map 44
identifiers to ten pending packages. Pending result fields remain blank.

The only proposed live command is:

`python3 tools/run_tests.py live-evidence --component ios --artifact-root /private/tmp/mcx-19-live-evidence --expected-commit "$ACE_LIVE_EVIDENCE_APPROVED_COMMIT"`

Run it only in the manual `ace-ios-live-evidence-manual` Codemagic workflow, after
approval. That workflow has no trigger. The operator must supply the separately
approved lower-case SHA in `ACE_LIVE_EVIDENCE_APPROVED_COMMIT`. It must equal
`CM_COMMIT` and Git HEAD. `CM_BRANCH` must equal `codex/mcx-19-live-evidence-harness`.
`CM_BUILD_ID` and `CM_BUILD_DIR` must identify the current Codemagic build. The
workflow variable `ACE_LIVE_EVIDENCE_WORKFLOW` must equal
`ace-ios-live-evidence-manual`. The runner rejects another context. Do not run the command locally or from a push,
pull request, tag, schedule, or another workflow.

The artifact root is an absolute path outside the Git tree. The runner rejects an
existing root, a symlink, a path escape, a missing artifact, a changed checksum, or a
secret or redaction finding. It does not print environment values or raw command output.
It writes only controlled metadata, result bundles, logs, summaries, and checksums to
that external root.

The gate resolves exact simulator device types and the highest available iOS 26.x
runtime. It accepts canonical unique UUIDs only. It gives simulator creation and
polling one 30-second monotonic deadline. Each test command has a 600-second limit.
It fails on a wrong runtime or type, duplicate or invalid UUID, timeout, unavailable
device, non-zero result, missing summary, skipped test, failed test, or wrong count.

The approved scope is 65 unit tests, twenty one-test UI selectors across two named
simulators and two appearances, 42 acceptance-contract tests, and one negative
configuration rejection. The gate checks 127 executed XCTest cases. It uses only the
existing schemes and selectors with controlled fictional inputs.

Do not add client data, passwords, authorisation values, Keychain secrets, credentials,
private notes, release claims, or evidence records to the repository.
