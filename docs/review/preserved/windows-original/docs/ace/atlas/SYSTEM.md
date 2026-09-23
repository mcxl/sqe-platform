# ACE System Atlas — Historical Snapshot — System Definition

**Historical architecture snapshot; not current acceptance evidence.** Status annotation updated 23 September 2026. The preserved nodes and flows describe the earlier fictional pilot. Current code and evidence index: LOCAL_HOME/Documents/sqe-platform/docs/ace/CODE-AND-EVIDENCE-INDEX.md. Full Vortex brief: LOCAL_HOME/sqe-private/handoffs/2026-09-23-vortex-full-review-brief.md.

_Question status: **0 open · 6 routed · 1 resolved**._

## One paragraph

This map preserves an earlier ACE pilot architecture. Its planned-client descriptions are historical: client web routes and release services were implemented in August. The owner has now reopened mobile alternatives for investigation. Consult the current SQE Development Hub and code/evidence index; this map proves neither current integration nor acceptance.

## Decisions locked

| Axis | Decision | Authority |
|---|---|---|
| Professional authority | Only the auditor approves relationships and conclusions. | Current ACE rule |
| Pilot data | Use fictional, public, or AuditCo-owned material only. Do not use client evidence. | G0 boundary |
| Evidence storage | Keep SQLite data and media outside the source tree. | Current workbench design |
| Client view | The filtered client view is planned and not operational. | Deferred output |

## Cost model

This pilot has no external runtime service, telemetry, or client data flow.
## Reading order (the atlas chapters)

1. **Permitted Input** — ACE begins at an **external input boundary**. The current workbench accepts fictional image capture only. _(adds SRC, WB)_
2. **Local Review Context** — The pilot keeps capture data local and defines the engagement and questions before work starts. _(adds STORE, SCOPE)_
3. **Trace And Method Checks** — The trace, evidence review, and **method gates** prepare material for an auditor decision. _(adds TRACE, REVIEW, GATES)_
4. **Professional Authority** — The **auditor decision gate** is the only approval path to controlled records. _(adds DECIDE, APPROVED)_
5. **Deferred Client Output** — The filtered client view is **planned only**. The dashed structure is not switched on. _(adds CLIENT)_
6. **Whole Atlas** — All structures are shown. Use the flow picker to inspect each representative fictional flow.

## Structures

### External Boundary

#### S · Source Material

**Status.** external boundary.

**In one line.** The external input boundary for fictional, public, or AuditCo-owned material.

**What it does.** It identifies the original document, photograph, or other source material before ACE creates an evidence item.

**How it's built.** The current pilot accepts fictional image capture. Real client evidence is outside the authorised pilot boundary.

**Steps in execution.**

1. **Select material** — The auditor selects permitted fictional material.
2. **Identify source** — ACE records the source reference and date.

**Questions.**

- **Q-S1** What secure design is required before real client evidence can enter ACE? → _Approved secure data design before any real engagement work._

### Current Fictional Pilot

#### W · Field Capture Workbench

**Status.** current pilot.

**In one line.** FastAPI workbench routes provide local, authenticated fictional image capture.

**What it does.** The workbench shows the current fictional engagement, receives an image, and shows its review state.

**How it's built.** FastAPI routes call the controlled engagement service and local store. The workbench does not approve evidence or conclusions.

**Steps in execution.**

1. **Open workbench** — The auditor opens the local workbench.
2. **Capture image** — The workbench accepts an image for the current fictional engagement.
3. **Show review state** — ACE displays PENDING_REVIEW or REVIEWED.

**Questions.**

- **Q-W1** When can protected offline drafts be added? → _After an approved secure data design._

#### L · Local Evidence Store

**Status.** current pilot.

**In one line.** Local SQLite records and media storage keep the fictional capture outside the source tree.

**What it does.** The store gives each captured item an evidence ID, media type, local media reference, status, and audit event.

**How it's built.** Workbench storage validates media paths and keeps the SQLite database and media directory outside the repository.

**Steps in execution.**

1. **Write item** — The store records an evidence ID and review status.
2. **Write media** — The media file is written into the controlled local data area.
3. **Record event** — ACE records the capture event for traceability.

**Questions.**

- **Q-L1** Which approved secure data design will govern real evidence? → _Open until professional and security approval._

#### Q · Engagement And Audit Questions

**Status.** current pilot.

**In one line.** Engagement scope and audit questions define what the auditor must answer.

**What it does.** An engagement has defined authority, purpose, scope, exclusions, dates, and an accountable auditor. Questions focus review work.

**How it's built.** The engagement service blocks real-client setup and allows capture only for a ready, current fictional engagement.

**Steps in execution.**

1. **Create draft** — Record the fictional engagement details.
2. **Activate** — The auditor confirms the complete fictional setup.
3. **Select current** — ACE permits capture only for the selected ready engagement.

#### T · Governance Trace

**Status.** current pilot.

**In one line.** A trace links a binding obligation to a risk, control, accountable role, and MATE assessment.

**What it does.** The trace gives review work a clear governance path. It does not make a relationship approved by itself.

**How it's built.** Current ACE domain and engine structures model the planning chain. Each relationship still needs the auditor decision gate.

**Steps in execution.**

1. **Bind obligation** — Identify the applicable obligation.
2. **Define risk** — Link the risk under review.
3. **Identify control** — State the governance measure.
4. **Set accountable role** — Use a stable role, not a named person.
5. **Assess MATE** — Record mandate, accountability, trigger, and escalation.

**Questions.**

- **Q-T1** How will many-to-many relationship views be presented? → _Future risk relationship view._

#### R · Evidence Review

**Status.** current pilot.

**In one line.** The auditor records relevance, gaps, contradictions, and sufficiency for each audit question.

**What it does.** Reviewed evidence does not automatically approve a relationship or conclusion. Gaps and contradictions remain visible.

**How it's built.** The current capture slice records review status. Full evidence relevance and sufficiency records are the next workbench capability.

**Steps in execution.**

1. **Inspect item** — The auditor reviews the source and evidence item.
2. **Record relevance** — Record support, weakness, or contradiction.
3. **Record limits** — Record gaps, conflicts, and sufficiency.

**Questions.**

- **Q-R1** When will full evidence review records be built? → _Phase 1 workbench foundation._

#### G · MATE And CONTRA Gates

**Status.** current pilot.

**In one line.** MATE checks control design and CONTRA challenges conflicting evidence and assumptions.

**What it does.** These gates make method checks visible before approval. They do not replace professional judgement.

**How it's built.** MATE is the deterministic assessment method. CONTRA is a recorded challenge that the auditor considers before approval.

**Steps in execution.**

1. **Apply MATE** — Check mandate, accountability, trigger, and escalation.
2. **Apply CONTRA** — Expose conflicting evidence or weak assumptions.
3. **Prepare decision** — Send the reviewed proposal to the auditor.

#### A · Auditor Decision Gate

**Status.** current pilot.

**In one line.** Only the auditor can approve, reject, or request a change to a proposed relationship or conclusion.

**What it does.** The decision is recorded against the same version of the proposal. Technology can organise and check information only.

**How it's built.** ACE approval records keep proposal versions and auditor decisions distinct. No automated approval path exists.

**Steps in execution.**

1. **Review proposal** — The auditor reviews evidence, limits, and method checks.
2. **Record decision** — Approve, reject, or request a change.
3. **Keep version** — Keep the decision with the proposal version.

**Questions.**

- ~~**Q-A1** Who can approve a conclusion?~~ ✓ Only the accountable auditor. Current ACE rule (2026-08-24).

#### P · Approved Records

**Status.** current pilot.

**In one line.** Accepted relationships and auditor-approved conclusions become the controlled records.

**What it does.** A substantive conclusion needs sufficient evidence with no unresolved material gap or contradiction. Otherwise the auditor can approve Not Determined.

**How it's built.** Approved relationship and conclusion records stay separate from suggestions, reviewed items, and unapproved versions.

**Steps in execution.**

1. **Accept relationship** — Store the accepted relationship and auditor decision.
2. **Accept conclusion** — Store an approved conclusion or Not Determined.
3. **Preserve trace** — Keep source, version, decision, and limitation visible.

### Planned Or Deferred

#### C · Filtered Client View

**Status.** planned — not operational.

**In one line.** Planned only: a view that could show approved information to a client.

**What it does.** It must show filtered, approved records only. It is not operational and it has no current client data path.

**How it's built.** This deferred output needs scope, security, and professional approval before implementation. It is shown as a dashed structure.

**Steps in execution.**

1. **Select approved records** — Use only records accepted by the auditor.
2. **Apply filter** — Apply the approved client disclosure rules.
3. **Present view** — Show the permitted output.

**Questions.**

- **Q-C1** What client disclosure rules are approved? → _Not decided. This feature is planned only._

## Flows (representative packets)

Payload shapes are what the design implies, not measured traffic.

### Fictional Field Capture

| # | From → To | Packet | Representative payload |
|---|---|---|---|
| 1 | SRC → WB | fictional image | `{"source":"Fictional site image","type":"image/jpeg"}` |
| 2 | WB → STORE | capture record | `{"evidenceId":"EVI-FIC-0001","status":"PENDING_REVIEW"}` |
| 3 | STORE → REVIEW | review state | `{"evidenceId":"EVI-FIC-0001","status":"PENDING_REVIEW"}` |

### Planning Trace

| # | From → To | Packet | Representative payload |
|---|---|---|---|
| 1 | SCOPE → TRACE | obligation → risk → control → role | `{"obligationId":"OBL-FIC-01","riskId":"RSK-FIC-01","controlId":"CTL-FIC-01","roleId":"ROLE-FIC-01"}` |
| 2 | TRACE → GATES | MATE assessment | `{"controlId":"CTL-FIC-01","mate":"recorded"}` |
| 3 | GATES → DECIDE | reviewed proposal | `{"proposalId":"REL-FIC-01","contra":"considered"}` |

### Evidence To Conclusion

| # | From → To | Packet | Representative payload |
|---|---|---|---|
| 1 | STORE → REVIEW | evidence item | `{"evidenceId":"EVI-FIC-0001"}` |
| 2 | REVIEW → GATES | review result | `{"sufficiency":"assessed","gaps":0,"contradictions":0}` |
| 3 | GATES → DECIDE | decision pack | `{"conclusionId":"CON-FIC-01"}` |
| 4 | DECIDE → APPROVED | approved conclusion | `{"result":"Not Determined","auditor":"fictional auditor"}` |

### Planned Client Output

| # | From → To | Packet | Representative payload |
|---|---|---|---|
| 1 | APPROVED → CLIENT | approved records only | `{"records":2,"state":"planned"}` |

## Questions — index

Reference by ID. ✓ resolved (with date) · → routed · otherwise open.

- **Q-S1** (S) What secure design is required before real client evidence can enter ACE? → _Approved secure data design before any real engagement work._
- **Q-W1** (W) When can protected offline drafts be added? → _After an approved secure data design._
- **Q-L1** (L) Which approved secure data design will govern real evidence? → _Open until professional and security approval._
- **Q-T1** (T) How will many-to-many relationship views be presented? → _Future risk relationship view._
- **Q-R1** (R) When will full evidence review records be built? → _Phase 1 workbench foundation._
- ~~**Q-A1**~~ (A) ✓ Only the accountable auditor. Current ACE rule (2026-08-24).
- **Q-C1** (C) What client disclosure rules are approved? → _Not decided. This feature is planned only._

## What the platform gives vs what we own

**Platform gives:** FastAPI routes, local SQLite access, and local media handling for the fictional workbench slice.

**We own:** The audit method, trace rules, evidence review, auditor decisions, and any future filtered client output.

## Planned filesystem

```
docs/ace/atlas/
  data.mjs       editable architecture source
  build.mjs      offline generator
  template.html  offline renderer template
  SYSTEM.md      generated system definition
  atlas.html     generated interactive atlas
```

## How this file is maintained

Generated from `docs/ace/atlas/data.mjs` by `node docs/ace/atlas/build.mjs`, which also builds the interactive atlas (`atlas.html`). Edit the data file and rebuild. Do not edit this generated file directly.
