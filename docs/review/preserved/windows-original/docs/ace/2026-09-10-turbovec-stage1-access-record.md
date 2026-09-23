# Turbovec Stage 1 Access Record

This is the initial access-check record. Later [Windows component checks](2026-09-10-turbovec-windows-component-results.md) provide partial evidence.

The missing iOS access and test evidence remain unresolved.

## Result

Blocked — Required Mac Access Is Unavailable.

The user approved autonomous Stage 1 execution on 10 September 2026.

Preflight started at 19:27:39 AEST. The network check completed at 19:29:31 AEST.

The approved limit is 60 minutes. Work stopped at the required-access gate.

## Scope And Baseline

- [Approved Stage 1 Scope](2026-09-10-turbovec-pilot-proposal.md).
- Reviewed turbovec version: `1.0.0`.
- Reviewed upstream commit: `ccab9f325e6ce2a270a87daf01ae4e443bcf2d49`.
- This attempt did not download or build the crate.
- This attempt did not change the SQE application or its dependencies.

## Access Evidence

| Check | Result |
| --- | --- |
| Current environment | Windows with PowerShell. |
| Connected Codex projects | Local Windows projects only; no connected Mac host was returned. |
| `Get-Command ssh,cargo,rustc,swift,xcodebuild` | SSH, Cargo and Rust proxy commands were found. Swift and Xcode were not found. |
| User SSH client configuration | No configuration was available at the checked user path. |
| System SSH client configuration | No configuration was available at the checked system path. |
| Saved Mac address | The project record identifies `192.168.86.97` from an earlier workbench session. |
| Initial TCP port 22 check | The sandbox denied socket access. This did not establish host availability. |
| Network-enabled TCP port 22 check | The connection timed out after five seconds. |
| Mac authentication and identity | Not verified. |

The timeout does not prove that the Mac is switched off. Its address or connection may have changed.

## Local Rust Diagnostic

The Cargo and Rust proxy commands attempted to obtain their configured stable toolchain information.

Both reported an access-denied error when Rustup tried to create a temporary file under the user profile.

No Rust version or successful toolchain installation was established. No tool installation was requested or completed by this task.

This is an environment diagnostic. It is not an application test failure.

## Tests And Work Not Run

- Minimal iOS simulator build.
- Deliberate failing assertion and corrected passing assertion.
- Swift-to-Rust bridge implementation and test.
- Stable ID, allowlist, deletion and restart checks.
- iOS device-target compilation.
- Independent implementation review.

No pilot acceptance criterion passed. The implementation stage did not start.

## Evidence Location

The machine-readable access record is:

`LOCAL_HOME\AppData\Local\Temp\sqe-turbovec-stage1-20260910-192739\preflight.json`

The temporary directory contains diagnostic evidence only. It contains no client material or credentials.

## Process State

All diagnostic commands completed. No build, test, remote session or background process remains active from this attempt.

No commit, push, merge, deployment or paid build occurred.

## Next Required Input

Provide an existing, working Mac connection with Xcode and compatible Rust tools.

Confirm the connection and tools before resuming the approved Stage 1 checks.

No further approval is needed for work within the approved scope. Mac access remains necessary.

Stage 2 remains blocked until Stage 1 provides the required build and test evidence.
