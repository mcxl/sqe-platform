# Turbovec Evidence Search Pilot Proposal

## Status

Stage 1 Approved — Windows Component Checks Passed; iOS Checks Pending.

The user approved autonomous Stage 1 execution on 10 September 2026.

The 60-minute limit and Stage 1 scope apply. Stages 2 and 3 remain future work.

The access check found no usable Mac connection. No iOS build or test ran.

After the user confirmed Windows, a focused check used the official Windows Python binding in an isolated temporary folder.

This supplies partial index evidence. It does not replace the Swift and iOS acceptance criteria below.

See the [Stage 1 Access Record](2026-09-10-turbovec-stage1-access-record.md).

See the [Windows Component Results](2026-09-10-turbovec-windows-component-results.md).

The Rust bridge, Swift wrapper and native harness are prepared. Native compilation and tests remain pending.

See the [Native Preparation Results](2026-09-10-turbovec-native-preparation-results.md).

## Intended Benefit

Help an auditor find relevant Sources for an Audit Question within one Engagement.

Show the Source, version and location with each result. The auditor completes the Evidence Review.

## Recommended Sequence

| Stage | Question To Answer | Scope |
| --- | --- | --- |
| 1 — Technical Feasibility | Can Swift use turbovec and recover saved data? | Isolated test harness with generated vectors. |
| 2 — Search Usefulness | Does meaning-based search find useful Sources that keyword search misses? | Fictional Sources, a selected local embedding model and auditor-labelled Audit Questions. |
| 3 — App Integration | Can SQE deliver useful offline search at the required scale? | Approved app changes, 5,000–20,000 chunks and physical-device checks. |

Only Stage 1 is approved for current work. Stages 2 and 3 need separate scopes and acceptance criteria.

## Stage 1 Goal

Prove the smallest Swift-to-Rust index path before developing document search or changing the SQE app.

Estimate: 45–60 minutes after host access is available.

Hard Limit: 60 minutes, including access checks and diagnosis. Stop at the limit and preserve the work.

Use an isolated temporary workspace. Do not add the pilot to the current app or its release branch.

## Baseline And Allowed Work

- Use turbovec version `1.0.0`, the version checked during the preceding review.
- The reviewed upstream commit is `ccab9f325e6ce2a270a87daf01ae4e443bcf2d49`.
- Pin the Cargo dependency and retain its resolved dependency lock.
- Permit the named crate and its resolved dependencies only within the isolated pilot.
- Use the installed Rust and Xcode tools. Record their exact versions.
- Create a minimal Rust bridge, C header, Swift test harness and focused build commands.
- Use `IdMapIndex`, caller-assigned `UInt64` IDs and 4-bit storage.
- Use 100 generated vectors with 768 dimensions. Do not use documents, client data, credentials or an embedding service.
- Run Astra Advisor with Terra implementation and a fresh Sol review, as required by the project.
- The primary agent must inspect all pilot changes and rerun relevant verification before accepting the review.

## Access Check

Confirm an accessible Mac, Xcode, compatible Rust tools and an iOS simulator before building.

The saved capability map records testing options. It does not confirm a connected device or working runner.

If required access or tools are missing, stop the affected work and report the exact gap.

Do not install tools, change device settings or start a paid build under this approval.

## Focused Test Plan

1. Build one minimal harness for the iOS simulator.
2. Deliberately fail one assertion. Retain its test name, source line, expected value, actual value and log.
3. Correct that assertion and prove that the same test passes. Do not change library behaviour to hide the failure.
4. Add generated vectors with stable IDs. Query the index from Swift.
5. Remove selected IDs. Confirm that every remaining ID still identifies the original vector.
6. Use an allowlist. Confirm that every result belongs to that set.
7. Test zero metadata matches. The Swift wrapper must return no results without broadening the search.
8. Save with `sync()`, end the harness process and load the index in a fresh process.
9. Confirm saved IDs, deletion state and filtered results after restart.
10. Build the bridge for the iOS device target. Record compilation only; do not claim physical-device operation.

Use serial index access. Convert errors into explicit Swift errors. Do not allow a failed open to replace saved data silently.

## Acceptance Criteria

- Swift calls the Rust bridge in an iOS simulator test process.
- The deliberate failure and corrected pass have accessible diagnostic evidence.
- The focused ID, filter and restart checks pass on the recorded final revision or file hashes.
- The bridge compiles for both the device and simulator targets.
- No app source, app dependency, production data or audit authority changes.
- The final report distinguishes passed checks, failed checks and checks that could not run.

A Stage 1 pass proves only this bridge and index path. It does not prove useful search, phone speed or production readiness.

## Commands With Material Cost

Cargo dependency downloads and release builds can use network access, CPU time and storage.

Xcode builds and simulator tests can use substantial CPU time and storage.

Run one minimal build before expanding checks. Reuse successful checks unless relevant inputs change.

No paid builds, hosted tests, external scans, source uploads or production actions are included.

## Stop Conditions

- The 60-minute limit expires.
- Required host access or diagnostic evidence is unavailable.
- Two corrective attempts fail for the same fault.
- Work needs an unapproved dependency, tool, architecture change or security change.
- Work needs app integration, real client data, signing changes or a paid service.

Preserve the pilot, report active processes and remaining work, and ask before resuming stopped work.

## Required Output

Return the isolated pilot location, files, hashes, tool versions, commands, test results and evidence locations.

Give a clear proceed, revise or stop recommendation for Stage 2.

Do not create a new Codex task, commit, push, merge or deploy under this proposal.

## Later Decisions

Stage 2 must select the on-device embedding model and define document extraction and chunking.

It must compare keyword search, exact vector search and compressed vector search on the same fictional Sources.

Stage 3 must preserve ACE authority and source provenance. It must define metadata/index recovery together.

It must also define Engagement isolation, backup rules, file protection, deletion and physical-device performance checks.

The current mobile design and Apple-framework requirements need explicit review before Rust enters the SQE app.

## References

- [Prior Retrieval Boundaries](../specs/2026-08-23-ace-provider-neutral-extraction-and-retrieval-boundaries.md)
- [SwiftUI Skill Rules](../agents/swiftui-skill.md)
- [Reviewed Turbovec Source](https://github.com/RyanCodrai/turbovec/tree/ccab9f325e6ce2a270a87daf01ae4e443bcf2d49)
