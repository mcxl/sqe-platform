# ACE And MATE SQE Teaching Infographic

## Purpose

Create a seven-page, editable PowerPoint infographic with a PDF handout copy.
The artifact will teach AuditCo staff how ACE and MATE support the five-day SQE diagnostic and the later targeted pathways.

## Audience

The primary audience is the internal AuditCo team.
The content may also support later client explanation after review of its language.

The deck will use plain technical language.
It will explain the method without presenting the method as an automated audit or as a replacement for professional judgement.

## Core Content Position

ACE means Assurance Compass Engine.
It is the umbrella assurance method and connected evidence structure.

MATE means Mandate, Accountability, Trigger And Escalation.
It is the control-design test applied to each material control family.

The connected trace is:

> Requirement -> Risk -> Control -> Owner -> Evidence -> Verification -> Trigger or Escalation -> Decision -> Action

The final assurance boundary is Control Design Adequacy.
Operational Effectiveness is Not Assessed unless a separate scope is approved.

MATE results support the auditor's conclusion.
They do not replace agreed criteria, evidence challenge or professional judgement.

## Deliverables

1. Editable PowerPoint deck in the `output` directory.
2. PDF handout copy in the `output` directory.
3. Rendered slide images in a temporary QA directory only.

The PowerPoint is the editable master.
The PDF is a fixed presentation copy.

## Visual System

- Use a 16:9 landscape PowerPoint canvas.
- Use a clean AuditCo-inspired palette: dark navy, teal, green, amber and off-white.
- Use native PowerPoint shapes for simple diagrams.
- Use connectors before nodes in relationship diagrams.
- Use one main teaching diagram per page.
- Keep body text at or above 16 pt.
- Keep slide titles at or above 35 pt.
- Keep the title page simple.
- Use short labels and short paragraphs.
- Avoid stock imagery and external visual assets.
- Do not use dense dashboard styling.
- Keep the same footer treatment and page numbering on every page.

## Page Plan

### Page 1: ACE And MATE At A Glance

Teaching aim: establish the relationship between the two methods.

Content:

- ACE as the umbrella method.
- MATE as the control-design test inside ACE.
- A simple flow from evidence to decision and action.
- A short statement that ACE does not automate professional judgement.

### Page 2: ACE - The Connected Assurance Method

Teaching aim: show how the whole assurance picture connects.

Content:

- The nine-part connected assurance trace.
- The role of the Criteria-To-Control Matrix.
- The role of the Connected Assurance Register.
- The flow from planning through fieldwork, challenge, findings and reporting.
- A callout that the same approved record supports the work and the report.

### Page 3: MATE - Four Questions For Every Material Control

Teaching aim: make the control-design test easy to apply.

Content:

- Mandate: approved requirement linked to obligation and risk.
- Accountability: one named role with authority and oversight.
- Trigger: event, threshold, gateway or review condition.
- Escalation: formal route to management or CRCC oversight.
- ACE rating logic:
  - all dimensions pass: Adequate;
  - one failed Trigger or Escalation dimension: Partially Adequate;
  - Mandate or Accountability fails, or two or more dimensions fail: Inadequate.
- Note that evidence and auditor rationale support every answer.

### Page 4: The Five-Day Diagnostic

Teaching aim: show how the first engagement uses ACE and MATE without claiming final assurance.

Content:

- Day 1: scope, evidence, risks, criteria and critical gaps.
- Day 2: governance, risk methods, framework documents and Project Kraken.
- Day 3: Third-Party Risk Management and Safety In Design.
- Day 4: identification, escalation, monitoring, incidents and learning.
- Day 5: challenge, priorities and pathway recommendation.
- Inputs: controlled evidence, priority stakeholders and agreed scope.
- Outputs: preliminary trace, evidence-readiness view, preliminary MATE observations, immediate priorities and Phase 2 recommendation.
- Guardrail: Phase 1 is preliminary and does not provide a final rating.

### Page 5: From Diagnostic To Targeted Pathway

Teaching aim: show how the Flex Decision Gate turns early evidence into a specific work package.

Content:

- Phase 1 diagnostic feeds the Flex Decision Gate.
- The gate may proceed, refine, prioritise, seek specialist advice, defer incomplete validation or close after Phase 1.
- The selected pathway keeps the ACE trace and applies deeper MATE work to priority control families.
- Show three pathway choices:
  - Safety In Design;
  - Operations-Facing Controls;
  - another agreed priority area.
- Clarify that a single-area Phase 2 may require a written scope adjustment if it removes authorised scope areas.

### Page 6: Worked Example - Safety In Design

Teaching aim: demonstrate ACE and MATE in the SQE Safety In Design context.

Example control family: construction-to-operations handover of residual safety risk.

ACE trace example:

- Requirement: approved SiD and handover requirement.
- Risk: residual design risk is not understood by the receiving operations team.
- Control: controlled SiD and handover process.
- Owner: named design authority and receiving operational owner.
- Evidence: SiD register, residual-risk record, design review minutes, handover pack and change record.
- Verification: design gate or handover review.
- Trigger: unresolved residual risk or material design change.
- Escalation: design rejection or management approval route.
- Decision or action: accept, redesign, control, transfer or escalate.

MATE prompts:

- Is SiD and handover required?
- Is one role accountable for the decision?
- What starts the review?
- What happens when residual risk remains unresolved?

### Page 7: Worked Example - Operations-Facing Controls

Teaching aim: demonstrate the method in an operations-facing context without overstating the assurance.

Example control family: electrical isolation and energisation authority.

ACE trace example:

- Requirement: approved isolation and energisation standard.
- Risk: stored or live energy is not controlled before work.
- Control: isolation verification and energisation authority process.
- Owner: named switching or operational authority.
- Evidence: procedure, role delegation, isolation record, verification record and incident or deviation log.
- Verification: pre-work or pre-energisation check.
- Trigger: planned energisation, change, failed verification or control deviation.
- Escalation: operational management and critical-risk reporting route.
- Decision or action: stop, correct, approve, escalate or revise the control.

Include a boundary panel:

- The review assesses whether the control is designed clearly.
- It may use walkthroughs and selected records.
- It does not conclude that the control operates effectively across all sites.
- Broader operating-effectiveness testing requires separate agreement.

## Supporting Methods

The deck will show these supporting methods without making them equal to ACE or MATE:

- Connected Assurance Trace: the common evidence relationship.
- CONTRA: independent challenge of evidence, contrary evidence, limitations and alternatives.
- Gatekeeper: approval and readiness decisions at each stage.
- Reporting And Action Tracking: preserves the finding-to-action link.

## Source Basis

Use the current local project sources:

- `260723 EOI and Plan/AuditCo_Squadron_Energy_Delivery_Plan_Current.md`
- `tmp/issued-md/AuditCo_Squadron_Energy_Delivery_Plan_260727.md`
- `docs/superpowers/specs/2026-07-26-ace-sprint-1-design.md`
- `docs/superpowers/specs/2026-07-27-ace-sprint-2-controlled-evidence-design.md`
- `docs/superpowers/specs/2026-07-28-ace-sprint-3-connected-assurance-trace-design.md`
- `docs/superpowers/specs/2026-07-28-ace-sprint-4-evidence-to-conclusion-design.md`

The deck will include a `Sources` block in the speaker notes for each page.
No external research or external visual asset is required.

## Verification

- Render every PowerPoint page to PNG.
- Inspect each page at full size.
- Create a contact sheet to check narrative flow and visual consistency.
- Run the slide overflow and overlap checks.
- Confirm that no title wraps unexpectedly.
- Confirm that all ACE and MATE definitions match the controlled sources.
- Export the PDF and render every PDF page.
- Check that the final PDF contains all seven pages.

