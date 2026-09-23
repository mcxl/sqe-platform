# Swift Agent Skills And App Creator Review Matrix

**Review date:** 10 September 2026  
**Reviewed archive:** `LOCAL_HOME/OneDrive - AuditCo/__Alan's downloads/2026-02-23-app-creator-v-0.9.8.zip`  
**Review method:** Read-only inspection of archive text, scripts and templates. No archive script was executed.

## Use Matrix

| Resource | Type | Local status | MCX-15 value | Decision |
|---|---|---|---|---|
| [SwiftUI Pro](https://github.com/twostraws/SwiftUI-Agent-Skill) | Paul Hudson agent skill | Installed, v1.1 | Modern SwiftUI APIs, view structure, state, accessibility and performance | Use for every SwiftUI code review. |
| [Swift Concurrency Pro](https://github.com/twostraws/Swift-Concurrency-Agent-Skill) | Paul Hudson agent skill | Not installed | Reviews `Task`, actors, `Sendable`, cancellation and Swift 6 migration | Use only for concurrency changes or a focused audit. |
| [Swift Testing Pro](https://github.com/twostraws/Swift-Testing-Agent-Skill) | Paul Hudson agent skill | Not installed | Helps migrate XCTest and design parameterised tests | Use only when the test framework changes. |
| [SwiftData Pro](https://github.com/twostraws/SwiftData-Agent-Skill) | Paul Hudson agent skill | Not installed | SwiftData models, queries and migrations | Not relevant to the current Keychain and HTTP client. |
| [SwiftUI Expert](https://github.com/AvdLee/SwiftUI-Agent-Skill) | Community agent skill | Not installed | Overlaps SwiftUI Pro. Adds broad state, performance and Liquid Glass guidance | Do not add a second overlapping skill without a defined gap. |
| Swift Concurrency Expert | Community agent skill | Not installed | Alternative concurrency guidance | Keep as an alternative reference. Do not load both by default. |
| Swift Testing Expert | Community agent skill | Not installed | Alternative Swift Testing guidance | Keep as an alternative reference. Do not load both by default. |
| [Core Data Expert](https://github.com/AvdLee/Core-Data-Agent-Skill) | Community agent skill | Not installed | Core Data stack, threading and migrations | Not relevant unless persistence changes to Core Data. |
| Xcode Build Optimization | Community agent skill | Not installed | Build settings and compilation time | Consider for a separate build-performance task. |
| OpenAI Build iOS Apps skills | First-party plugin skills | Available | UI patterns, Liquid Glass, performance, view refactor, simulator debugging and App Intents | Prefer these for implementation work in this workspace. |
| `swiftui-ui-patterns` | OpenAI plugin skill | Available | Screen composition, state and navigation | Use for new or changed SwiftUI screens. |
| `swiftui-performance-audit` | OpenAI plugin skill | Available | Code-first performance review and profiling intake | Use only when a performance symptom or trace exists. |
| `swiftui-view-refactor` | OpenAI plugin skill | Available | Small view types and Observation ownership | Use only inside an approved refactor scope. |
| `swiftui-liquid-glass` | OpenAI plugin skill | Available | iOS 26 Liquid Glass adoption | Use only for a Liquid Glass feature. It is not needed for MCX-15 evidence work. |
| `ios-debugger-agent` | OpenAI plugin skill | Available | Build, launch and inspect iOS Simulator apps | Use for an approved simulator task. It does not replace controlled evidence review. |
| `ios-app-intents` | OpenAI plugin skill | Available | Siri, Shortcuts, widgets and system actions | Not relevant to the current client release flow. |
| [Swift Agent Skills directory](https://github.com/twostraws/swift-agent-skills) | Community index | Reference only | Finds additional skills by topic | Use for discovery. Read each linked skill before use. |
| [Inject](https://github.com/krzysztofzablocki/Inject) | Swift package and InjectionIII workflow | External dependency | Fast local SwiftUI iteration during prototyping | Use only in a disposable development branch. Do not add it to the controlled MCX-15 candidate without approval. |
| `general.md` and `rule-loading.md` | Project rule pattern | Not installed in this repository | Loads small, relevant rules on demand | Adapt the pattern to existing `AGENTS.md` and skills. Do not copy conflicting rules. |
| Progressive documentation CLI idea | Workflow pattern | No tool name supplied | Reduces broad document loading by reading only relevant files | Apply through existing skills and targeted reads. Select a CLI only after its name and trust are known. |
| `app-creator` | Archive skill | Reviewed only | Scaffolds or adopts XcodeGen projects | Useful for new disposable projects. Review findings below before adoption. |
| `xcode-makefiles` | Archive subskill | Reviewed only | Adds build, test, run and per-agent paths | Useful after the overwrite and isolation findings are corrected. |
| `simple-tasks` | Archive subskill | Reviewed only | Adds a local Markdown task list and task CLI | Useful for one agent after locking and ownership checks are corrected. |
| Build macOS Apps plugin | External plugin reference | Not available in the current skill set | macOS AppKit, signing and packaging | Keep as a future option. It is outside MCX-15. |

The Paul Hudson skills describe agent review guidance and support Codex. The community directory is an index, not an approval of every linked project. citeturn31view0turn43view0turn46view0turn45view0

## Archive Findings

| ID | Severity | Component and evidence | Finding | Effect | Recommended action |
|---|---|---|---|---|---|
| AC-01 | High | `xcode-makefiles/scripts/install.sh:114-154` | Install mode checks only the Makefile. It then copies toolkit scripts into an existing `scripts/` directory. | An adopt operation can overwrite existing project scripts without an explicit upgrade request. | Check every destination before copying. Refuse install when any target exists. Use upgrade only after an explicit request. |
| AC-02 | High | `simple-tasks/scripts/task.sh:917-924`, `:957-969` | `claim` overwrites an existing claim. `done` does not check claim ownership. | Two agents can take or complete the same task. The task record cannot prove ownership. | Add an atomic claim lock and reject claims owned by another agent. Require the same owner for `done`, with an explicit handover path. |
| AC-03 | High | `simple-tasks/scripts/task.sh:254-296`, `:298-307` | `write_tasks` writes the canonical file directly. `plan` calculates the next number without a lock. | Concurrent plans can create duplicate IDs. Concurrent writes can truncate or corrupt `TASKS.md`. | Lock the task store. Write a temporary file, validate it, then rename it atomically. Allocate IDs while holding the lock. |
| AC-04 | High | `app-creator/scripts/stabilize_project.sh:119-137` | Multi-agent mode falls back to `CODEX` when the name lock helper is absent. | Separate agents can share build, log and temporary paths. | Fail closed in multi-agent mode when a unique name cannot be allocated. |
| AC-05 | High | `app-creator/scripts/stabilize_project.sh:162-180`; `scaffold_app.sh` auto-commit path | Baseline commit uses `git add -A`. It also writes a default local Git identity when none exists. | Unrelated files can enter the commit. The command changes repository configuration without a separate approval. | Stage only files created by this run. Never set Git identity automatically. Report missing identity and stop the commit. |
| AC-06 | Medium | `simple-tasks/scripts/task.sh:338-357` | A stored `Detail:` value is joined directly to `PROJECT_ROOT`. No containment check exists. | A crafted task file can write detail files outside the project. | Resolve the path and require it to remain below `PROJECT_ROOT/tasks/details`. |
| AC-07 | Medium | `simple-tasks/scripts/task.sh:893-903`, `:937-947`, `:991-1008` | Several task commands silently skip unknown options. | A misspelled option can report success while ignoring user intent. | Reject unknown options and require values for options such as `--note`. |
| AC-08 | Medium | `simple-tasks/scripts/task.sh:254-296` | Scope, files and notes are written into Markdown without newline or control-character validation. | A note can change the task record structure or create misleading metadata. | Reject control characters and escape or encode multiline values. |
| AC-09 | Medium | `xcode-makefiles/templates/toolkit/scripts/xcbuild.sh:60-68` | Archive names use second-level timestamps. | Two runs in one second can replace an earlier archived log or result bundle. | Add nanoseconds or a collision check before `mv`. |
| AC-10 | Medium | `xcode-makefiles/templates/toolkit/scripts/move_to_trash.sh:20-24` | The AppleScript fallback concatenates a path into source code. | A path containing AppleScript syntax can alter the command. | Pass paths through a safe AppleScript argument mechanism, or use a safe trash tool and fail when it is absent. |
| AC-11 | Medium | `xcode-makefiles/templates/toolkit/scripts/xcbuild.sh:108-117` | Builds add `-Xfrontend -disable-sandbox`. | Compiler sandbox protection is disabled for every toolkit build. | Document the reason, scope it to the required target, and make it an explicit opt-in. |
| AC-12 | Medium | `xcode-makefiles/templates/toolkit/scripts/run_app_ios_sim.sh:72-76` | `--background` changes a message only. It still calls `simctl launch` in the normal way. | The target does not provide a distinct background launch mode. | Rename the option or implement and test the intended background behaviour. |
| AC-13 | Medium | `app-creator/templates/xcodegen/ios-swiftui/Sources/ContentView.swift` and the macOS equivalent | The starter views use fixed font sizes and a timer publisher. | The generated app starts with weak Dynamic Type support and older lifecycle patterns. | Use Dynamic Type styles and a cancellable `.task` loop or another current API. |
| AC-14 | Medium | `app-creator/templates/xcodegen/*/project.yml` | App name and bundle ID placeholders are inserted without input validation or YAML quoting. | Special characters can produce invalid XcodeGen files or source. | Validate identifiers and escape template values before rendering. |
| AC-15 | Low | `xcode-makefiles/scripts/install.sh:92` and `scaffold_app.sh` | Temporary render directories have no cleanup trap on every failure path. | Failed runs can leave temporary directories. | Add `trap` cleanup. Keep recovery copies only when the user asks for them. |
| AC-16 | Low | Archive root | The archive contains skill folders and macOS metadata, but no clear root README or license file. | Future users lack a distribution-level usage and licence record. | Add a root README, licence references and a version manifest. |

## Positive Controls

- Shell scripts use `set -euo pipefail` in the main orchestration and build paths.
- The Xcode toolkit keeps per-agent DerivedData, logs, cache and temporary paths.
- Installers support `--dry-run` and refuse to overwrite the main Makefile in install mode.
- `xcbuild.sh` preserves logs and result bundles after a build.
- The templates enable strict Swift concurrency and warnings as errors.
- The SwiftUI starter uses `foregroundStyle()` and a `#Preview`.

These controls reduce risk. They do not resolve the high-severity findings above.

## Adoption Order

1. Correct AC-01 through AC-05 before using the archive on an existing or shared project.
2. Correct AC-06 through AC-12 before using the task or build tools with concurrent agents.
3. Correct AC-13 and AC-14 before using generated starter apps as a SwiftUI quality baseline.
4. Use SwiftUI Pro and the OpenAI iOS skills for current MCX-15 code work.
5. Use Concurrency Pro or Testing Pro only when the change needs that specialist review.
6. Keep SwiftData, Core Data, App Intents, Liquid Glass and Inject outside the current MCX-15 scope.

## MCX-10 Applicability

MCX-10 is the isolated, fictional Relationship Review web pilot. Its approved stack is Next.js, Convex and Vercel Preview. It is not a Swift or Xcode project.

| Reviewed resource | MCX-10 use | Decision |
|---|---|---|
| SwiftUI Pro, Concurrency Pro, Testing Pro, SwiftData Pro | No direct use in the Next.js and Convex pilot | Do not load for MCX-10 work. |
| AvdLee Swift skills and Core Data Expert | No direct use | Keep outside the pilot. |
| OpenAI Build iOS Apps skills | No direct use | Use the web, Convex or Vercel guidance that matches the changed module. |
| Inject | No direct use | Do not add it to the pilot. |
| `app-creator`, `xcode-makefiles` and `simple-tasks` archive | Xcode and shell tooling, outside the web pilot | Do not adopt for MCX-10. |
| Merowing progressive rule-loading pattern | General documentation pattern | Apply only through existing `AGENTS.md` and targeted skill reads. |

For MCX-10, the useful review controls are strict Convex validators, indexed query paths, fictional-record guards, isolated development and Preview deployments, protected Preview access, and no public write, approval or production actions. The existing pilot specification defines these controls in [convex-vercel-fictional-relationship-view-pilot.md](docs/specs/convex-vercel-fictional-relationship-view-pilot.md).

### MCX-10 Verification Record

On 11 September 2026, the pilot passed 13 tests, TypeScript typecheck, lint with zero errors, and the Next.js production build at commit `809a4576fb03d35eea52d0a2fe174151e3fc2949`. Lint reported five warnings in generated Convex files. No pilot source change was made.

The protected Vercel Preview is `https://relationship-review-pilot-du6kr3jbz-mcxl1.vercel.app/`. Vercel Authentication is enabled for the project. Live checks passed with fictional data only: the queue showed Orchid Works, Juniper Field and Cedar Advisory; the Orchid detail showed versions, evidence, gaps, contradictions and review notes; `?relationship=missing-id` showed `Relationship Not Found`. The blocked boundary is covered by the Convex query test because public queue data contains fictional records only.

MCX-10 acceptance is complete. No client data, secrets, public writes, approvals, Production actions or architecture changes were used.

## MCX-15 Boundary

This matrix is a tooling and guidance review. It does not change the controlled register, evidence state, source code, signing, simulator results or formal acceptance. Inject and the archive installers are development aids. They cannot prove physical-device journeys, callback timing, privacy review or approval gates.
