# Phase 6.1 Evidence Register

This is a public G0 planning register. It is not release evidence. It does not run,
collect, publish, or accept client evidence. The 44 entries and ten packages remain
public and pending. Every pending result field remains blank.

`RuntimeEvidencePlan.json` owns the package-to-identifier mapping.
`Phase6_1EvidenceRegister.json` contains the checked copy.
`tools/run_tests.py evidence-check` rejects a changed map, non-pending status, completed result field, or
release claim.

The future MCX-19 live gate uses only the manual
`ace-ios-live-evidence-manual` Codemagic workflow. It has no automatic trigger. Its
one command is:

`python3 tools/run_tests.py live-evidence --component ios --artifact-root /private/tmp/mcx-19-live-evidence --expected-commit "$ACE_LIVE_EVIDENCE_APPROVED_COMMIT"`

An approved operator can use that command only after a separate approval. The command
checks the remote repository, exact current Git commit, approved baseline ancestry,
and clean Git tree. The operator input `ACE_LIVE_EVIDENCE_APPROVED_COMMIT` must exactly
match `CM_COMMIT` and the checked-out lower-case Git SHA. `CM_BRANCH` must equal
`codex/mcx-19-live-evidence-harness`. `CM_BUILD_ID` and `CM_BUILD_DIR` must identify the current build. The workflow variable
must equal `ace-ios-live-evidence-manual`. `CM_TRIGGER_SOURCE` must equal `api` and
`CM_BUILD_STARTED_BY` must identify the operator. It retains the commit in its external manifest. No repository file
becomes a live artifact or a release record.

The gate selects the highest available iOS 26.x runtime and exact simulator types. It
rejects a wrong runtime or type, an invalid or duplicate UUID, timeout, unavailable
device, non-zero command, missing artifact, changed checksum, secret, or redaction
failure. It records safe simulator metadata and result counts only. It does not echo
environment values, credentials, or raw command output.

Raw logs, result bundles, summaries, manifests, and checksums go only below the
absolute external root `/private/tmp/mcx-19-live-evidence`. The root must not exist before the
run. It must not be in the Git working tree or use a symlink. Use controlled fictional
inputs only. Do not record client data, passwords, authorisation values, Keychain
secrets, credentials, private notes, or release claims.

## MCX19-B Private Diagnostic Records (Pending)

Public artifacts still prohibit raw Xcode logs and result bundles. For approved fictional
MCX19-B tests only, original diagnostic records may be retained in verified authenticated
storage for authorised project operators. Records expire after 30 days. Prove authorised
retrieval and unauthorised denial before a paid suite.

Generate the private inventory exactly from the planned command set. Do not publish an
unrestricted directory glob. Each started XCTest command has one generated `.xcresult`, with
complete or incomplete state recorded. Retain exported summaries, individual failures, and
attachment inventories. Retain compiler, test, simulator-setting, export, and packaging
output only from approved commands. Retain candidate and build identity, relative path,
producing command, size, SHA-256, and collection state. Existing checked JSON and allowed
fictional PNG images remain controlled review records, separately.

Exclude environment dumps, credential files, Keychain contents, signing material, caches,
source exports, unrelated machine files, and real client information. Keep raw records out
of Git, PR comments, public links, and public artifact downloads. Do not put temporary
authenticated download URLs in reports, logs, commits, or messages. Do not use public
bearer-link bypass. Check paths, links, types, sizes, and producing commands. Reject
unexpected files. Stop on a secret or real client information finding.

The 31 planned commands, 135 XCTest cases, 200 named fictional review images, and
`releaseEvidence: false` remain unchanged. Original bundle, approved Mac, provider
retention, provider interruption, retrieval, and denial evidence remain PENDING.
