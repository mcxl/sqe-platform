# Vorflux: Start Here

This is the current Windows SQE source snapshot prepared for independent review on 23 September 2026.
Select branch `codex/vorflux-review-20260923`, not `main`.

## Master Update

Read [MASTER_UPDATE.md](MASTER_UPDATE.md) first. It consolidates current state, earlier work, diagnostics, source identities and the access-gap register. This expanded export includes 6,328 Mac text records through deduplicated links, preserved Windows variants, 25 Mac worktree records, original approved instructions, showcase source and latest-failure images/video. Remaining raw bundles and execution access are explicitly unresolved.

## What To Review

After the master update, read [the Mac evidence update](docs/review/MAC-UPDATE.md), [the complete review brief](docs/review/VORFLUX-FULL-REVIEW-BRIEF.md), [development state](DEV_STATE.md) and [code and evidence index](docs/ace/CODE-AND-EVIDENCE-INDEX.md). Dated Mac-unavailable statements are superseded.
The separate [SQE options brief](docs/review/SQE-OPTIONS-AND-IOS-REVIEW.md) is also included. Its local reference in older records refers to this copy.

Recommend how to complete the existing work and which mobile delivery route to pursue. Compare Swift, Expo/React Native, mobile web/PWA and justified alternatives. Reuse the existing service and approval model where appropriate. Review only; do not implement, purchase, deploy or change acceptance rules without a further decision. The owner's later permission to publish this review snapshot supersedes the historical brief's prohibition on this upload only.

## Included Code

| Area | Location |
|---|---|
| Python service, approval rules and auditor workbench | `src/ace/` |
| Python tests | `tests/` |
| Next.js/Convex relationship pilot | `apps/relationship-review-pilot/` |
| Swift app, unit tests and UI tests | `ios/ACEClientApp/` |
| Local native runner and its tests | `tools/ace_ios_local.py`, `tools/tests/` |
| Specifications, approved diagnostic instructions and plans | `docs/` |

Every application, test and runner source file from the frozen Windows working snapshot is included byte-for-byte. No application source was repaired or tested for this publication. Documentation redactions and the exported README/Hub navigation differ; their source/export hashes are recorded in [the manifest](docs/review/EXPORT-MANIFEST.json).

The empty `.env.example` is omitted under the environment-file rule. The pilot setting it documents is `NEXT_PUBLIC_CONVEX_URL`; no working deployment URL or authentication is supplied.

## Saved Maps

- [Understand Anything graph](docs/review/maps/understand-anything/knowledge-graph.json): 145 analysed files, 1,100 nodes and 2,854 edges.
- [Graphify graph](docs/review/maps/graphify/graph.json) and [HTML viewer](docs/review/maps/graphify/graph.html): 2,894 nodes and 8,951 edges. Download the HTML to view it; GitHub displays its source. Four JSON files have no graph nodes; exclusions are retained.
- [CodeGraph portable index](docs/review/maps/codegraph/index.json): 91 indexed code files, 2,728 nodes and 8,627 edges. The database and local runtime are not required to read this export.

These maps were verified against the original Windows snapshot, not regenerated for sanitised document copies or this new review brief. Source code remains authoritative. Map line references into redacted documents may differ. Original validation hashes describe original files; export hashes describe published copies. No local dashboard, localhost address, installed skill or Mac filesystem becomes accessible through GitHub.

Code Atlas remains historical and is not included in the current map exports. Archify 2.17 is installed locally; no new SQE Archify diagram is claimed.

## Histories And Differences

The Windows base is `478a7d8cd9c97d0bc43bd4d41ea460d589d4003a`, plus the working-file changes in the manifest. The recorded imported Mac candidate is `40bae2640b23eb05496a093d09a4c20186403879`.

GitHub main is retained at `7da6228dc87ad970aa8d44365fbc3823c58020da`. The original local and GitHub-main histories have no common ancestor. This review commit uses GitHub main as its publication parent only; it does not establish native candidate ancestry or merge the unrelated local history.

The root tree intentionally represents the current Windows working source. [Reconciliation](docs/review/RECONCILIATION.md) lists files that differ or exist only on main. Those main files remain retrievable from the parent commit. Do not merge this snapshot into main without resolving them.

In particular, Windows Python approval/G0 and toolchain choices remain held differences. Historical CI, Codemagic, the provider runner and its Makefile are not activated. Publication is not a decision to delete those implementations from main or accept the older Windows behaviour.

## What Is Still Unavailable

This is not 100% of every device, private record or historical dirty worktree. It is the current Windows review snapshot and selected retained verification summaries.

- Mac access was restored after resolving a stale address. The clean delivery HEAD, tracked-source comparison and 6,328 indexed text records are included; see the master update. The original Mac update described the first 45-record selection.
- Selected native logs and machine summaries are included. Most raw result bundles and historical media remain on the Mac; latest-failure PNGs and video are included in the master update. Unexported local evidence paths are identifiers, not remote attachments.
- Real client records, signing material, service credentials, local viewer tokens, database contents and environment files are excluded.
- Current Mac variants are included as references. The master update now includes preserved variants and the 25 registered Mac worktree records; those are not merged application changes. Main and other public branches remain separate comparison sources.
- The public showcase is a separate presentation. Its published page source and checking scripts are now included. Original client correspondence remains outside this public export.

Report these limits explicitly. Do not infer a root cause, test pass or product readiness from inaccessible evidence.

## Known Delivery Status

The Copy accessibility finding remains unexplained in the inspected records. The complete native programme, physical checks, signing renewal, private service and ancestry decisions remain open. Historical suite counts and prior install success are not current acceptance. The recorded signing profile expired on 21 September; renewal is unknown.

## Integrity

The manifest records original and exported SHA-256 values. Credentials and local home-directory prefixes were removed from documentation/map exports. Sanitised approved-instruction copies are reference copies, not the original hash-approved files. Original instructions and source remain unchanged locally.

Publishing this branch does not automatically grant Vorflux a GitHub connector, select this branch or execute a review. Give Vorflux the branch URL and this file. Ask it to confirm the branch commit and report unreadable attachments before reviewing.
