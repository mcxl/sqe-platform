# Autonomous Delivery Workflow Repair

## Purpose

This repair makes the Autonomous Delivery Workflow safe for one approved autonomous
implementation task. The detailed rules are only in
[workflows/codex-autonomous-delivery.md](../../workflows/codex-autonomous-delivery.md).

## Required Result

- Use `Autonomous Delivery Workflow`, `pull request`, and `Fresh Sol review` as the
  canonical terms.
- Create the draft pull request before final validation.
- Treat each head change as a new validation candidate.
- Remove stale readiness and evidence after each head change.
- Finish safe CI, conflict and review fixes before final validation.
- Run Pocock code review, the complete suite and Fresh Sol review in that order.
- Do not change code after Fresh Sol review returns `ship`.
- Bind merge approval to the exact ready head.
- Keep direct commit authority outside the workflow.
- Block real client information at G0.
- Set the issue to `Done` only after GitHub confirms that exact approved head merged.

## Out Of Scope

- Application code, architecture, security-boundary, schema, interface or dependency
  changes.
- A pull request merge without the user's exact-head approval.
- Real client information or DeepSec.
