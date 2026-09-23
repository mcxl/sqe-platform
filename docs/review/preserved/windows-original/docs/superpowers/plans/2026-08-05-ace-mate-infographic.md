# ACE And MATE SQE Teaching Infographic Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build and verify a seven-page editable PowerPoint infographic and a PDF handout that teach ACE, MATE, the five-day SQE diagnostic and targeted pathways.

**Architecture:** Use one JavaScript ES module with `@oai/artifact-tool` to create the editable PowerPoint. Use shared theme helpers for page chrome, typography, colour, connectors, evidence-chain nodes and source notes. Export the PowerPoint to the final output directory, then render and export the PDF through the local presentation toolchain.

**Tech Stack:** Node.js ES modules, `@oai/artifact-tool`, PowerPoint rendering helpers, Poppler PDF rendering, PowerShell, local SQE Markdown source files.

## Global Constraints

- ACE means Assurance Compass Engine.
- MATE means Mandate, Accountability, Trigger And Escalation only.
- The connected trace is Requirement -> Risk -> Control -> Owner -> Evidence -> Verification -> Trigger or Escalation -> Decision -> Action.
- The final assurance boundary is Control Design Adequacy; Operational Effectiveness is Not Assessed unless separately agreed.
- MATE results support professional judgement and do not replace agreed criteria or evidence challenge.
- Use a 16:9 landscape PowerPoint canvas.
- Use at least 50 pt for deck titles, 35 pt for page titles, 24 pt for mid-level labels and 16 pt for body text.
- Use native PowerPoint shapes for simple diagrams and create connectors before nodes.
- Keep the deck audience-facing; do not expose build notes or internal planning commentary on the pages.
- Add a `Sources` block in speaker notes for every page.
- Do not use external visual assets or external research.
- Render and inspect every page before completion.
- Preserve unrelated user changes in the dirty worktree.

---

### Task 1: Prepare The Artifact-Tool Workspace

**Files:**
- Create: `tmp/ace_mate_infographic/source-notes.txt`
- Create: `tmp/ace_mate_infographic/build_ace_mate_infographic.mjs`
- Modify: none

**Interfaces:**
- Consumes: the approved design specification and the local source files listed in its Source Basis section.
- Produces: an executable ES module that can export the final `.pptx` to `output/AuditCo_ACE_MATE_SQE_Diagnostic_Pathways_Infographic.pptx`.

- [ ] **Step 1: Read the artifact-tool quick-start and API documentation.**

Run:

```powershell
Get-Content -Raw "$env:USERPROFILE\.codex\plugins\cache\openai-primary-runtime\presentations\26.802.11031\skills\presentations\artifact_tool_docs\API_QUICK_START.md"
Get-Content -Raw "$env:USERPROFILE\.codex\plugins\cache\openai-primary-runtime\presentations\26.802.11031\skills\presentations\artifact_tool_docs\api\API_DOCS.md"
```

Expected: the available presentation creation, notes, export and shape APIs are clear before code is written.

- [ ] **Step 2: Initialise the artifact-tool workspace.**

Run:

```powershell
node "$env:USERPROFILE\.codex\plugins\cache\openai-primary-runtime\presentations\26.802.11031\skills\presentations\container_tools\setup_artifact_tool_workspace.mjs" --workspace "tmp/ace_mate_infographic"
```

Expected: the temporary workspace contains the package setup required by the ES module.

- [ ] **Step 3: Record source provenance.**

Write `tmp/ace_mate_infographic/source-notes.txt` with these source paths and their use:

```text
260723 EOI and Plan/AuditCo_Squadron_Energy_Delivery_Plan_Current.md - delivery method, connected assurance trace, MATE and SQE examples
tmp/issued-md/AuditCo_Squadron_Energy_Delivery_Plan_260727.md - issued wording cross-check
docs/superpowers/specs/2026-07-26-ace-sprint-1-design.md - ACE name and deterministic rating logic
docs/superpowers/specs/2026-07-27-ace-sprint-2-controlled-evidence-design.md - controlled MATE assessment boundary
docs/superpowers/specs/2026-07-28-ace-sprint-3-connected-assurance-trace-design.md - connected trace structure
docs/superpowers/specs/2026-07-28-ace-sprint-4-evidence-to-conclusion-design.md - evidence-to-conclusion and reporting boundary
```

Expected: the provenance record contains no external sources or unsupported claims.

- [ ] **Step 4: Add the deck shell and shared theme helpers.**

The module must define:

```js
const FINAL_PPTX = path.resolve(process.cwd(), "output/AuditCo_ACE_MATE_SQE_Diagnostic_Pathways_Infographic.pptx");
const slideSize = { width: 13.333, height: 7.5 };
const palette = { navy, teal, green, amber, ink, muted, paper, line, white };
function addPageChrome(slide, pageNumber, sectionLabel) {}
function addTitle(slide, title, subtitle) {}
function addSourcesNotes(slide, sourcePaths) {}
function addConnector(slide, x1, y1, x2, y2, options) {}
function addTraceNode(slide, label, x, y, width, height, options) {}
```

Use exact artifact-tool types and method names from the API documentation. Create connectors before the nodes they connect.

Expected: the module can create a blank seven-page deck with consistent page chrome and source notes.

### Task 2: Build The ACE And MATE Teaching Pages

**Files:**
- Modify: `tmp/ace_mate_infographic/build_ace_mate_infographic.mjs`
- Modify: `tmp/ace_mate_infographic/source-notes.txt`
- Create: none

**Interfaces:**
- Consumes: shared theme helpers from Task 1.
- Produces: pages 1 to 3 with editable text, shapes, connectors and speaker notes.

- [ ] **Step 1: Build Page 1, ACE And MATE At A Glance.**

Create one large ACE circle or compass shape at the left, a nested MATE group at the centre, and a short evidence-to-action flow at the right. Use the exact labels:

```text
ACE
Assurance Compass Engine

MATE
Mandate | Accountability | Trigger | Escalation

ACE connects the assurance picture.
MATE tests each material control.
```

Add the design-only boundary as a small footer callout:

```text
Control Design Adequacy assessed | Operational Effectiveness Not Assessed
```

Expected: the relationship is understandable without speaker notes.

- [ ] **Step 2: Build Page 2, ACE - The Connected Assurance Method.**

Create a left-to-right connected trace with nine short nodes:

```text
Requirement
Risk
Control
Owner
Evidence
Verification
Trigger / Escalation
Decision
Action
```

Use a lower band to show how the trace is reused across `Plan`, `Fieldwork`, `Challenge`, `Findings` and `Reporting`. Add two side callouts for the Criteria-To-Control Matrix and Connected Assurance Register.

Expected: the page teaches that ACE is a common record, not a separate audit stage.

- [ ] **Step 3: Build Page 3, MATE - Four Questions For Every Material Control.**

Use four large quadrants with one question each:

```text
Mandate - Is the control required and linked to the obligation and risk?
Accountability - Is one named role accountable and authorised?
Trigger - What event, threshold, gateway or review condition activates it?
Escalation - What formal route applies when the risk or control fails?
```

Add a small rating ladder:

```text
All pass -> Adequate
One Trigger or Escalation failure -> Partially Adequate
Mandate or Accountability failure, or two failures -> Inadequate
```

Add a note that evidence and auditor rationale support each answer.

Expected: the page teaches both the questions and the decision logic without implying automated conclusions.

### Task 3: Build The Diagnostic And Pathway Pages

**Files:**
- Modify: `tmp/ace_mate_infographic/build_ace_mate_infographic.mjs`
- Modify: `tmp/ace_mate_infographic/source-notes.txt`
- Create: none

**Interfaces:**
- Consumes: shared theme helpers and pages 1 to 3.
- Produces: pages 4 and 5 with the five-day flow and post-diagnostic pathway decision.

- [ ] **Step 1: Build Page 4, The Five-Day Diagnostic.**

Create a five-step horizontal timeline with one day per step:

```text
Day 1 - Scope, evidence, risks, criteria and critical gaps
Day 2 - Governance, risk methods, framework and Project Kraken
Day 3 - TPRM and Safety In Design
Day 4 - Identification, escalation, monitoring, incidents and learning
Day 5 - Challenge, priorities and pathway recommendation
```

Place inputs above the timeline:

```text
Controlled evidence | Priority stakeholders | Agreed scope
```

Place outputs below the timeline:

```text
Preliminary ACE trace | Evidence readiness | Preliminary MATE observations | Immediate priorities | Phase 2 recommendation
```

Add a warning panel:

```text
Phase 1 is preliminary. It does not provide a final internal-audit rating.
```

Expected: the diagnostic is shown as a controlled bridge to a later decision, not as a compressed full audit.

- [ ] **Step 2: Build Page 5, From Diagnostic To Targeted Pathway.**

Create a central Flex Decision Gate node receiving the Page 4 diagnostic. Connect it to six possible decisions in a compact ring or branching diagram:

```text
Proceed | Refine | Prioritise | Obtain specialist advice | Defer validation | Close after Phase 1
```

Below the gate, show the three pathway options:

```text
Safety In Design
Operations-Facing Controls
Another agreed priority area
```

Add a small scope note:

```text
The selected pathway keeps the ACE trace and applies deeper MATE work to priority control families. Removing authorised scope areas requires written scope agreement.
```

Expected: the page explains how the client moves from early insight to specific work.

### Task 4: Build The SQE Worked Examples

**Files:**
- Modify: `tmp/ace_mate_infographic/build_ace_mate_infographic.mjs`
- Modify: `tmp/ace_mate_infographic/source-notes.txt`
- Create: none

**Interfaces:**
- Consumes: shared theme helpers, ACE trace nodes and MATE question components.
- Produces: pages 6 and 7 with editable SQE examples and the assurance boundary.

- [ ] **Step 1: Build Page 6, Worked Example - Safety In Design.**

Use the example control family `Construction-to-operations handover of residual safety risk`.
Show the ACE chain in a compact vertical flow:

```text
Requirement: approved SiD and handover requirement
Risk: residual design risk is not understood by operations
Control: controlled SiD and handover process
Owner: design authority and receiving operational owner
Evidence: SiD register, residual-risk record, review minutes, handover pack, change record
Verification: design gate or handover review
Trigger: unresolved residual risk or material design change
Escalation: design rejection or management approval route
Decision / action: accept, redesign, control, transfer or escalate
```

Place the four MATE questions beside the chain. Use amber for the trigger and escalation points to show where decisions change.

Expected: an internal reviewer can see how the abstract method becomes a SiD review procedure.

- [ ] **Step 2: Build Page 7, Worked Example - Operations-Facing Controls.**

Use the example control family `Electrical isolation and energisation authority`.
Show the ACE chain:

```text
Requirement: approved isolation and energisation standard
Risk: stored or live energy is not controlled before work
Control: isolation verification and energisation authority process
Owner: named switching or operational authority
Evidence: procedure, delegation, isolation record, verification record, incident or deviation log
Verification: pre-work or pre-energisation check
Trigger: planned energisation, change, failed verification or control deviation
Escalation: operational management and critical-risk reporting route
Decision / action: stop, correct, approve, escalate or revise the control
```

Add a boundary panel:

```text
The review assesses control design.
It may use walkthroughs and selected records.
It does not conclude that the control operates effectively across all sites.
Broader operating-effectiveness testing needs separate agreement.
```

Expected: the example is practical and does not overstate the current SQE assurance scope.

### Task 5: Render, Export And Verify

**Files:**
- Modify: `tmp/ace_mate_infographic/build_ace_mate_infographic.mjs` only if QA finds a defect.
- Create: `output/AuditCo_ACE_MATE_SQE_Diagnostic_Pathways_Infographic.pptx`
- Create: `output/AuditCo_ACE_MATE_SQE_Diagnostic_Pathways_Infographic.pdf`
- Create: `tmp/ace_mate_infographic/rendered/slide-1.png` through `slide-7.png`
- Create: `tmp/ace_mate_infographic/contact-sheet.png`

**Interfaces:**
- Consumes: the completed deck module from Tasks 1 to 4.
- Produces: verified editable and fixed-format deliverables.

- [ ] **Step 1: Run the deck builder.**

Run:

```powershell
node "tmp/ace_mate_infographic/build_ace_mate_infographic.mjs"
```

Expected: the final PowerPoint exists at the declared output path and contains seven pages.

- [ ] **Step 2: Render all PowerPoint pages.**

Run:

```powershell
python "$env:USERPROFILE\.codex\plugins\cache\openai-primary-runtime\presentations\26.802.11031\skills\presentations\container_tools\render_slides.py" "output/AuditCo_ACE_MATE_SQE_Diagnostic_Pathways_Infographic.pptx"
```

Expected: seven PNG pages are created in the renderer output directory.

- [ ] **Step 3: Run overflow and overlap checks.**

Run:

```powershell
python "$env:USERPROFILE\.codex\plugins\cache\openai-primary-runtime\presentations\26.802.11031\skills\presentations\container_tools\slides_test.py" "output/AuditCo_ACE_MATE_SQE_Diagnostic_Pathways_Infographic.pptx"
```

Expected: no unintended overflow or overlap warnings.

- [ ] **Step 4: Inspect each rendered page.**

Use the local image viewer on all seven pages. Check:

- no clipped text;
- no unexpected title wrapping;
- no broken connectors;
- no overlapping labels or nodes;
- readable body text;
- consistent page chrome;
- correct ACE and MATE definitions;
- correct SQE scope boundary.

Expected: each page is readable at full size and the seven-page narrative is coherent.

- [ ] **Step 5: Create the PDF copy and render it.**

Export the PowerPoint to `output/AuditCo_ACE_MATE_SQE_Diagnostic_Pathways_Infographic.pdf` using the pinned presentation toolchain. Render the PDF pages with Poppler.

Expected: the PDF contains seven pages and matches the PowerPoint layout.

- [ ] **Step 6: Run final source and artifact checks.**

Check that the final deck and PDF contain these exact terms:

```text
Assurance Compass Engine
Mandate, Accountability, Trigger And Escalation
Control Design Adequacy
Operational Effectiveness
Five-Day Diagnostic
Safety In Design
Operations-Facing Controls
```

Expected: all terms are present, `Map, Assess, Trace, Enhance` is absent, and only the intended final files were added.

- [ ] **Step 7: Commit the verified deliverables.**

Run:

```powershell
git add -- output/AuditCo_ACE_MATE_SQE_Diagnostic_Pathways_Infographic.pptx output/AuditCo_ACE_MATE_SQE_Diagnostic_Pathways_Infographic.pdf
git commit -m "build: add ACE and MATE SQE infographic"
```

Expected: the final deliverables are committed without staging unrelated user changes.

