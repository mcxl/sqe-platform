# Mandatory AuditCo Document Rules

Apply these rules to every Word document in this workspace, with no exceptions.

- Use Capital Case for headings, running headers, table headers and footers.
- Use Australian English.
- Do not use Word text boxes. Move their text into paragraphs, lists or data tables.
- Keep each cover page editable. Do not flatten cover wording into an image.
- Use the retained AuditCo template as the visual authority. Recreate editable covers
  with Word-native paragraphs, table shading and rules.

## Default Writing And Presentation Quality

Apply these rules to SQE responses, documents, reports and website content without requiring a special prompt.

- Lead with the decision, finding or required action.
- Use plain English and focused paragraphs. Avoid walls of text.
- Remove filler, repetition, vague wording, decorative labels and unsupported claims of quality or certainty.
- Separate the summary and next actions from supporting detail and evidence.
- Use tables for comparisons, not as containers for long paragraphs.
- Keep headings short and descriptive. Avoid duplicate metrics and repeated citations within the same finding.
- Keep implementation details out of user-facing content unless they help the user act or decide.
- Preserve facts, source references, uncertainty and necessary safety or legal qualifications when shortening content.
- Before delivery, check readability, information hierarchy and repetition as well as formatting and technical correctness.
- For review-only requests, identify specific problems and their effects without rewriting or changing the draft.
- Treat `/no-ai-slop` as shorthand for this review-only check, not as an installed slash command.

## Astra Advisor Implementation Lane

Use Astra Advisor for substantial coding unless the user selects another workflow.
Keep Astra as the primary agent.
Continue in the current task when scope and isolation remain suitable.
Create a separate task only when the user requests one.

- Use the installed Terra lane for implementation and a fresh Sol review.
- Keep professional review, human decisions and these rules authoritative.
- Before accepting a Sol verdict, the primary session must inspect the complete final
  diff and rerun relevant verification.

## Codex Standard Operating Procedure: Testing and Diagnostics

1. **Require Evidence Before Action:** Never modify source code, UI, or configuration based on a test failure unless the exact failure assertion (Expected vs. Actual) and relevant visual or log evidence have been retrieved and reviewed. Never guess the cause of a failure.
2. **Verify Telemetry First:** Before executing any full, paid, or remote test suite (e.g., Codemagic), explicitly verify that artifact retention (result bundles, screenshots, logs) is working and accessible. If evidence downloads are blocked or missing, halt the task immediately and resolve the pipeline blockage. Do not proceed with paid runs blindly.
3. **Isolate to Diagnose:** If a full run fails, do not rerun the complete suite to test fixes. Isolate the specific failing test and reproduce it locally or via a minimal, targeted diagnostic run.
4. **Separate App vs. Environment Faults:** Explicitly categorize every failure as either an application defect (e.g., UI layout, hidden controls) or a test harness/environment error (e.g., simulator settings unavailable). Fix test harness errors before altering application code.
5. **Report Exact Details:** When reporting failures, you must state the failing test name, the exact source line, the expected outcome, and the actual outcome. Do not present incomplete progress reports as verification.

## Bounded Work Policy

Apply this policy to all Codex work in this repository.

For work that can take more than 30 minutes, state acceptance criteria, estimate,
hard limit, high-cost commands and pilot scope. Separate pilot work from production
hardening. Wait for approval. Use 60 minutes when the user gives no limit.

Give progress every 15 minutes. State elapsed time and estimated remaining time.
Stop at the hard limit. Stop after two failed corrective attempts for one fault. Stop
before an architecture or security change. Stop when scope needs expansion. Different
validation failures are separate faults. A running process is not failed. Only a completed
non-zero exit proves failure. Do not continue only because earlier work used much
time or tokens. Do not add controls, dependencies or repository tools without
approval. Add temporary official tools only under the approved workflow. Preserve work
when you stop. Do not clean non-temporary work, delete non-temporary data, merge or
rewrite history without approval.
After a stop, stop task commands, report completed work, active processes, blockers
and remaining steps, then ask before work resumes.

Review the test harness before use. Use focused tests during work. Keep generated
locks, caches, logs and outputs outside AI review context. Validate generated files
with mechanical tools where possible. Run each external scan and review once, unless
the approved workflow states a limited exception.

Reuse completed checks when relevant files, tools, inputs and environment are unchanged.
Record the checked revision or hashes, command, result and evidence location.
Repeat checks after relevant changes, missing evidence, or a required final gate.
Do not repeat a completed review merely to restate its result.

Do not use DeepSec without new, explicit approval, an approved isolation design and
a test harness. Run one real scan only after the harness passes review. Stop DeepSec
work at its first hard-limit or stop event.

## Commit And Push Controls

A direct `commit and push` request permits one normal task commit and push. An
approved Autonomous Delivery Flow permits required bounded task commits, pushes and
PR updates. Stage only current-task files. Verify the exact staged list and all
`upstream..HEAD` commits and files before push. Stop if either has unrelated work or
blocked data. Stop for unclear branch, remote, ownership or scope. Do not force-push
or rewrite history. Do not push secrets, restricted client information or environment
files. Do not ask for another commit or push approval when its scope checks pass.
Treat `anything` and `all` as current-task scope only. Push only to the approved
feature branch.

## Autonomous Delivery Flow

Use [workflows/codex-autonomous-delivery.md](workflows/codex-autonomous-delivery.md)
for the full procedure, including Greptile control, diagnostic probes, privacy and
credentials, safe fixes, retries and completion evidence.

One detailed approval starts one bounded Linear issue. It must state the issue, goal
and acceptance criteria. It must state the baseline, allowed files or modules and
tests. It must state the time limit, exclusions and data and security controls.

It authorises in-boundary implementation, diagnosis and safe recovery. It authorises
compatible version correction and focused verification. It authorises one complete
suite on the final candidate head. It authorises reviews, normal commits, pushes, PR
updates, monitoring and Linear updates.

It authorises bounded Preview deployment retries. It authorises temporary official
tools. Pin each tool version. Isolate each tool outside repository dependencies.
It authorises temporary exports of tracked files outside the repository. It authorises
automatic cleanup of task-created temporary files and temporary credentials. Do not
ask again for these in-bound actions.

Before opening a deployment URL, target Preview explicitly. Confirm that the provider
reports a Preview deployment.

Safe recovery can move generated dependency, cache or build folders to a recoverable
location outside source scan paths. It can then reinstall cleanly from the approved
lock. Do not delete these folders. Continue automatically when a safe in-bound remedy
exists. Do not ask again for this safe recovery.

A compatible version correction can change versions only for approved dependency
names. It needs direct compatibility evidence. Select the nearest supported stable
version. It can update the approved lock, configuration and tests inside the approved
file boundary. Do not ask again for this compatible correction.

This authority cannot add a dependency name or repository tool. It cannot change
architecture, security boundaries, schemas, public interfaces or production actions.
It cannot deploy to Production.

Stop for the hard limit, real client data and unavailable required access. Stop for
material scope expansion or irreversible deletion of non-temporary data. Stop before
architecture, security, public schema or public interface changes. Stop before a new
dependency name, non-temporary tool, Production target or Production deployment. Stop
for merge approval.

The required gates are primary diff inspection, Pocock review, one controlled
Greptile review with `check-pr`, and a fresh Sol review. Do not use `greploop`. Do
not request or trigger a second Greptile review without new approval. A permitted Sol
fix that changes code needs focused tests. Run one extra complete suite on its changed
head. Then get one fresh Sol review.

Ask for merge approval of the exact ready PR head. A changed head invalidates that
approval. Do not force-push, rewrite history, merge automatically or deploy to
production. After GitHub confirms that exact head merged, add `merged`, set Linear to
`Done`, and keep dependent issues blocked until completion.

## SQE Development Hub Command

When the user sends `/dev-hub`, reply with this link:

[Open SQE Development Hub](LOCAL_HOME/Documents/sqe-platform-public-clean/SQE_DEVELOPER_HUB.html)

Do not append this link to other replies unless the user requests it.
Treat `/dev-hub` as a conversation instruction, not a registered Codex slash command.

## Agent Skills

- Use `docs/agents/issue-tracker.md` for issue-tracker rules.
- Use `docs/agents/triage-labels.md` for triage labels.
- Use `docs/agents/domain.md` for domain-document locations.
- Use `docs/agents/swiftui-skill.md` for Swift and SwiftUI work. Apply `$swiftui-pro` within the approved task scope.
