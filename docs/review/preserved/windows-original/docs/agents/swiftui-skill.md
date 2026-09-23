# SwiftUI Skill Use

## Scope

Use `$swiftui-pro` when reading, writing or reviewing ACE SwiftUI code.
Use it for the native read-only client and later approved SwiftUI work.
Load only the reference files needed for the task.

Use the existing iOS skills for builds, simulator checks, performance measurement and device checks.
Use SwiftUI Pro to check APIs, views, data flow, navigation, accessibility and performance.
Keep findings limited to problems supported by the code.
Report the file, line, effect and proposed correction.

## Installation Record

- Installed on: 6 September 2026.
- Skill: `swiftui-pro`, version `1.1`.
- Source: <https://github.com/twostraws/SwiftUI-Agent-Skill>.
- Fixed source commit: `be297ff80dddec529af1f9b1f1f114aab6c9d11c`.
- Local location: `LOCAL_HOME/.codex/skills/swiftui-pro`.
- Installation method: the Codex skill-installer helper, using the fixed source commit.

The skill contains agent instructions. It is not an application dependency.
Other build workspaces need access to the skill and these usage instructions.

## Project Authority

Keep the approved specification, deployment target and Swift version authoritative.
The skill defaults to iOS 26 and Swift 6.2 or later.
Do not change project versions solely to meet these defaults.
Keep the read-only client boundary and Apple-framework requirements.

Follow the existing implementation workflow and approval rules for code changes.
SwiftUI Pro does not replace Pocock, Sol, security, automated, simulator or physical-device checks.
Installing the skill does not approve a candidate or complete a pending evidence item.

## Current Use

The local progress guide records an iOS candidate in a separate repository.
This workspace contains no Swift source files for that candidate.
Apply the skill in the approved application workspace during the next SwiftUI task.
Record review findings and focused verification there.
