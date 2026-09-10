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
approved lower-case SHA in `ACE_LIVE_EVIDENCE_APPROVED_COMMIT`. Immediately before a
separately approved API start, an authorised operator sets
`ACE_LIVE_EVIDENCE_APPROVED_COMMIT` in the dedicated `mcx19_live_evidence` Codemagic
variable group to the exact approved lower-case SHA. The group supplies the value at
run time. The repository must not store or hard-code the SHA. The operator removes the
group value after the build completes or stops. It must equal `CM_COMMIT` and Git HEAD.
`CM_BRANCH` must equal `codex/mcx-19-live-evidence-harness`. `CM_BUILD_ID` and
`CM_BUILD_DIR` must identify the current Codemagic build. The trigger source must be
`api`, and `CM_BUILD_STARTED_BY` must identify the operator. The workflow variable
`ACE_LIVE_EVIDENCE_WORKFLOW` must equal `ace-ios-live-evidence-manual`. The runner
rejects another context. Do not run the command locally or from a push, pull request,
tag, schedule, or another workflow.

The artifact root is an absolute path outside the Git tree. The runner rejects an
existing root, a symlink, a path escape, a missing artifact, a changed checksum, or a
secret or redaction finding. It does not print environment values or raw command output.
It writes only controlled metadata, result bundles, logs, summaries, and checksums to
that external root.

## MCX19-B Private Diagnostic Records (Pending)

Public artifacts still prohibit raw Xcode logs and result bundles. For approved fictional
MCX19-B tests only, original diagnostic records may be retained in verified authenticated
storage. Retrieval is limited to authorised project operators. Records expire after 30
days. Proof of authorised retrieval and unauthorised denial is required before a paid
suite.

Generate the private inventory exactly from the planned command set. Do not publish an
unrestricted directory glob. Each started XCTest command has one generated `.xcresult`, with
complete or incomplete state recorded. Retain exported summaries, individual failures, and
attachment inventories. Retain compiler, test, simulator-setting, export, and packaging
output only from approved commands. Retain candidate and build identity, relative path,
producing command, size, SHA-256, and collection state. Existing checked JSON and allowed
fictional PNG images remain controlled review records, separately.

Do not retain environment dumps, confirmed credentials, Keychain contents, signing material, caches,
source exports, unrelated machine files, or real client information. Keep raw records out of
Git, PR comments, public links, and public artifact downloads. Do not put temporary
authenticated download URLs in reports, logs, commits, or messages. Do not use public
bearer-link access. Check paths, links, types, sizes, and producing commands. Reject
unexpected files. Stop on a confirmed secret or real client information finding. Apply only
the narrow unresolved-match exception below.

For planned `.xcresult/Data/*` members from approved fictional XCTest commands only,
permit unresolved `credential-prefix` byte matches with `neighbourhoodShape=non-utf8`
in the existing authenticated private storage. Preserve exact bytes, provenance and
hashes. Record `quarantined-pending-review`. The match can be a real credential. This
status does not establish scanner clearance, collection acceptance or release acceptance.
Keep all other matchers and all text, decoded-data, metadata and path checks unchanged.
Resolve a record only after mapping the match to its object and reading and classifying
all required children. Missing mapping, read errors or partial coverage remain pending.
Keep raw matched bytes, object identifiers and command errors private. Stop collection
if a genuine credential or real client information is confirmed.

Before the next paid run, verify authenticated retrieval of an existing approved fictional
artifact, unauthorised denial and effective 30-day retention. The first focused run must
then prove original-bundle retrieval before the corrected case or complete suite. Do not
bypass a blocked download. Keep the candidate unverified while any record is unresolved.

The 31 planned commands, 135 XCTest cases, 200 named fictional review images, and
`releaseEvidence: false` remain unchanged. Original bundle, approved Mac, provider
retention, provider interruption, retrieval, and denial evidence remain PENDING.

The gate resolves exact simulator device types and the highest available iOS 26.x
runtime. It accepts canonical unique UUIDs for existing devices only. It does not
create a simulator in the normal workflow. It gives inventory and readiness checks
one 180-second monotonic deadline. Each test command has a 600-second limit.
It fails on a wrong runtime or type, duplicate or invalid UUID, timeout, unavailable
device, non-zero result, missing summary, skipped test, failed test, or wrong count.

The runner checks 65 unit tests, 24 one-test UI commands across two named simulators
and two forced appearances, 42 acceptance-contract tests, four normal-setting UI
commands, and one negative configuration rejection. These 31 commands require 135
executed XCTest cases. Normal-setting commands verify system appearance and content
size without the app appearance override and record setting restoration. The runner
uses the existing schemes and selectors with controlled fictional inputs.

These collection counts do not establish a complete visual or manual acceptance pass.
The candidate must also satisfy the MCX19-B Acceptance Matrix in the iOS specification.

Do not add client data, passwords, authorisation values, Keychain secrets, credentials,
private notes, release claims, or evidence records to the repository.
