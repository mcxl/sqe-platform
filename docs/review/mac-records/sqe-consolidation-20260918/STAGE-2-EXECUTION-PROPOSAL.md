# SQE Stage 2 Execution Proposal

**Date:** 18 September 2026
**Status:** Proposed bounded execution scope. Awaiting user approval.
**Predecessor:** Stage 1 inventory under `LOCAL_HOME/ace-private/sqe-consolidation-20260918/inventory`.

## Objective

Establish how the Windows destination and Mac delivery histories and complete committed trees differ.
Produce a reviewed-baseline recommendation without changing either source repository or choosing a branch automatically.

## Fixed Inputs

| Source | Commit |
|---|---|
| `LOCAL_HOME\Documents\sqe-platform` | `478a7d8cd9c97d0bc43bd4d41ea460d589d4003a` |
| `LOCAL_HOME/Developer/sqe-platform-release-layout` on `ace-mac` | `40bae2640b23eb05496a093d09a4c20186403879` |

Record current HEAD, refs, index and working-change identities before dependent operations.
Stop the affected comparison if either fixed input changed; do not silently substitute a newer commit.
Use Stage 1's preservation register for all other locations. Do not import the parent monorepo or its unrelated work.

## Storage And Isolation

Use these Mac-local paths:

- Records: `LOCAL_HOME/ace-private/sqe-consolidation-20260918/stage2`
- Bundles: `LOCAL_HOME/ace-private/sqe-consolidation-20260918/bundles`
- Isolated bare repository: `LOCAL_HOME/ace-private/sqe-consolidation-20260918/comparison.git`

These paths were absent when checked. Refuse to overwrite an unexpected existing location.
The private parent is on the Mac's internal APFS disk, outside the observed cloud-storage roots.
The latest read-only check reported approximately 210 GiB available.

Cap Stage 2 output and temporary space at 2 GiB, while retaining at least 20 GiB free on the Mac.
This is an operating cap, not an assertion that the complete job will fit.
Check reachable object sizes and expected temporary use before generating a bundle.
Stop before transfer if the measured projection exceeds the cap. Do not raise it automatically.

Stream Windows bundle bytes directly over SSH with bounded buffers and concurrent SHA-256 calculation.
Write no Windows bundle, recovery copy, cache or temporary pack.
If the available Git path cannot stream without C: scratch storage, stop and report the limitation.
Do not use Google Drive, the T: mapping, GitHub or a cloud upload as a transport.

## Execution Sequence

1. Recheck SSH access, source identities, Mac capacity and Stage 1 record retrieval.
2. Enumerate the exact outgoing refs, reachable object sizes and historical file paths for the two fixed histories.
3. Review the outgoing history scope for restricted data and credentials before any source-history transfer.
4. Stop on confirmed restricted material or unresolved candidate material. Do not rewrite, redact or filter source history.
5. Create private bundles only after that review and storage gate pass.
6. Record each advertised ref, tip, byte count and SHA-256 at the producing and receiving ends.
7. Run `git bundle verify` and confirm every prerequisite is available before import.
8. Import into separate named refs in the isolated bare repository. Leave source refs and remotes unchanged.
9. Determine the merge base or explicitly record that none exists.
10. Compare complete trees, including Windows-only, Mac-only, changed, renamed and deleted paths.
11. Inspect relevant source differences and propose a disposition for every differing path.
12. Check the proposal against the Stage 1 unfinished-work register.
13. Retrieve the final report over SSH, verify its hash, and recheck source identities.

Do not display secret values or copy restricted content into the report.
A filename review alone cannot establish that history contains no secrets.
Use existing checks and bounded inspection. Do not install scanners or claim exhaustive security certification.
If the content review cannot be completed within scope, report the precise unresolved set and stop transfer.

## Preservation

Original repositories, dirty files, ignored evidence, branches and worktrees remain in place.
A bundle covers committed objects only. It is not a backup of staged, unstaged or untracked files.
Stage 1's two missing registrations and five inaccessible directories remain open.
No retirement, pruning, cleanup or deletion is authorised.
Full recovery copies are not part of this comparison block; they remain required before later operations could overwrite source work.
No missing or inaccessible item may be classified as disposable.

## Acceptance Evidence

- Exact source commits and pre/post identity checks.
- Recorded outgoing-history scope and review result, including any unresolved concerns.
- Measured space, transfer sizes, bundle hashes, refs and native verification results.
- Separate imported refs and the merge-base result, or its documented absence.
- Complete path-level tree comparison with proposed retain, reconcile or exclude-from-active-source dispositions.
- Links to preserved unfinished work and explicit unresolved decisions.
- A baseline recommendation with reasons; no baseline or consolidation branch created.
- Retrievable Markdown report and file manifest under the private records path.

The result may be a blocked transfer report if the history or storage gate fails.
That outcome does not establish a completed comparison.

## Time, Commands And Stops

**Planning estimate:** 30–60 minutes if history review and transfer checks pass.
Content-review exceptions, access recovery and conflict resolution have no established estimate and are excluded.
**Hard limit:** 60 minutes from the first approved execution command, including waiting.

Potentially expensive commands include `git rev-list`, batch object-size inspection, `git bundle create`, bundle verification, isolated fetch and full-tree diff.
Bound each operation and preserve completed evidence. A running command is not a failure.
No builds, tests, dependency installs, new repository tools, external scans or deployment commands are authorised.

Stop at the hard limit, storage cap, unavailable access, unexpected source changes or restricted-data gate.
Stop after two failed corrective attempts for one fault. Do not expand scope to continue.
Report commands, results, evidence, remaining work and active processes at any stop.
Give progress updates, including elapsed time, during execution.

## Exclusions And Next Decision

No application edits, branch switching, source imports into the destination, commits, pushes, merge, Production action or iOS acceptance testing.
Do not change approved Revision 5 or D2 instruction bytes.
Do not treat the existing iOS ancestry requirement as satisfied solely by this comparison.

After this block, the user reviews the baseline and dispositions before Stage 3 is proposed.
This proposal does not authorise Stage 3 or the showcase implementation.
