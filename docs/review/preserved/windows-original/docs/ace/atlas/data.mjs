// The single project-specific source for the ACE System Atlas pilot.
// Run: node docs/ace/atlas/build.mjs

export const META = {
  title: 'ACE System Atlas — Historical Snapshot',
  sourcePath: 'docs/ace/atlas/data.mjs',
  buildCmd: 'node docs/ace/atlas/build.mjs',
  stats: [{ k: 'Standing', v: 'historical map' }, { k: 'Current record', v: 'SQE Development Hub' }],
  intro: '**Historical architecture snapshot; not current acceptance evidence.** Status annotation updated 23 September 2026. The preserved nodes and flows describe the earlier fictional pilot. Current code and evidence index: LOCAL_HOME/Documents/sqe-platform/docs/ace/CODE-AND-EVIDENCE-INDEX.md. Full Vortex brief: LOCAL_HOME/sqe-private/handoffs/2026-09-23-vortex-full-review-brief.md.',
  onePara: 'This map preserves an earlier ACE pilot architecture. Its planned-client descriptions are historical: client web routes and release services were implemented in August. The owner has now reopened mobile alternatives for investigation. Consult the current SQE Development Hub and code/evidence index; this map proves neither current integration nor acceptance.',
  costModel: ['This pilot has no external runtime service, telemetry, or client data flow.'],
  platformGives: 'FastAPI routes, local SQLite access, and local media handling for the fictional workbench slice.',
  weOwn: 'The audit method, trace rules, evidence review, auditor decisions, and any future filtered client output.',
  filesystem: `docs/ace/atlas/
  data.mjs       editable architecture source
  build.mjs      offline generator
  template.html  offline renderer template
  SYSTEM.md      generated system definition
  atlas.html     generated interactive atlas`,
};

export const DECISIONS = [
  { axis: 'Professional authority', decision: 'Only the auditor approves relationships and conclusions.', adr: 'Current ACE rule' },
  { axis: 'Pilot data', decision: 'Use fictional, public, or AuditCo-owned material only. Do not use client evidence.', adr: 'G0 boundary' },
  { axis: 'Evidence storage', decision: 'Keep SQLite data and media outside the source tree.', adr: 'Current workbench design' },
  { axis: 'Client view', decision: 'The filtered client view is planned and not operational.', adr: 'Deferred output' },
];

export const GROUPS = [
  { id: 'external', title: 'External Boundary' },
  { id: 'current', title: 'Current Fictional Pilot' },
  { id: 'planned', title: 'Planned Or Deferred' },
];

// Each item uses only representative fictional packets. No client material is in this file.
export const NODES = [
  { id: 'SRC', code: 'S', name: 'Source Material', short: 'SOURCE', group: 'external', state: 'external', gx: 1.2, gy: 8.0, w: 2.3, d: 2, h: 34, kind: 'cards',
    one: 'The external input boundary for fictional, public, or AuditCo-owned material.',
    what: 'It identifies the original document, photograph, or other source material before ACE creates an evidence item.',
    how: 'The current pilot accepts fictional image capture. Real client evidence is outside the authorised pilot boundary.',
    steps: [['Select material', 'The auditor selects permitted fictional material.'], ['Identify source', 'ACE records the source reference and date.']],
    cond: [{ q: 'What secure design is required before real client evidence can enter ACE?', to: 'Approved secure data design before any real engagement work.' }] },
  { id: 'WB', code: 'W', name: 'Field Capture Workbench', short: 'WORKBENCH', group: 'current', state: 'current', gx: 5.0, gy: 5.8, w: 3, d: 2.5, h: 48, kind: 'screen',
    one: 'FastAPI workbench routes provide local, authenticated fictional image capture.',
    what: 'The workbench shows the current fictional engagement, receives an image, and shows its review state.',
    how: 'FastAPI routes call the controlled engagement service and local store. The workbench does not approve evidence or conclusions.',
    steps: [['Open workbench', 'The auditor opens the local workbench.'], ['Capture image', 'The workbench accepts an image for the current fictional engagement.'], ['Show review state', 'ACE displays PENDING_REVIEW or REVIEWED.']],
    cond: [{ q: 'When can protected offline drafts be added?', to: 'After an approved secure data design.' }] },
  { id: 'STORE', code: 'L', name: 'Local Evidence Store', short: 'LOCAL STORE', group: 'current', state: 'current', gx: 9.7, gy: 7.8, w: 3, d: 2.4, h: 30, kind: 'store',
    one: 'Local SQLite records and media storage keep the fictional capture outside the source tree.',
    what: 'The store gives each captured item an evidence ID, media type, local media reference, status, and audit event.',
    how: 'Workbench storage validates media paths and keeps the SQLite database and media directory outside the repository.',
    steps: [['Write item', 'The store records an evidence ID and review status.'], ['Write media', 'The media file is written into the controlled local data area.'], ['Record event', 'ACE records the capture event for traceability.']],
    cond: [{ q: 'Which approved secure data design will govern real evidence?', to: 'Open until professional and security approval.' }] },
  { id: 'SCOPE', code: 'Q', name: 'Engagement And Audit Questions', short: 'SCOPE + QUESTIONS', group: 'current', state: 'current', gx: 13.5, gy: 4.4, w: 3.2, d: 2.5, h: 44, kind: 'cards',
    one: 'Engagement scope and audit questions define what the auditor must answer.',
    what: 'An engagement has defined authority, purpose, scope, exclusions, dates, and an accountable auditor. Questions focus review work.',
    how: 'The engagement service blocks real-client setup and allows capture only for a ready, current fictional engagement.',
    steps: [['Create draft', 'Record the fictional engagement details.'], ['Activate', 'The auditor confirms the complete fictional setup.'], ['Select current', 'ACE permits capture only for the selected ready engagement.']],
    cond: [] },
  { id: 'TRACE', code: 'T', name: 'Governance Trace', short: 'GOVERNANCE TRACE', group: 'current', state: 'current', gx: 4.0, gy: 13.1, w: 3.6, d: 3.1, h: 62, kind: 'tall',
    one: 'A trace links a binding obligation to a risk, control, accountable role, and MATE assessment.',
    what: 'The trace gives review work a clear governance path. It does not make a relationship approved by itself.',
    how: 'Current ACE domain and engine structures model the planning chain. Each relationship still needs the auditor decision gate.',
    steps: [['Bind obligation', 'Identify the applicable obligation.'], ['Define risk', 'Link the risk under review.'], ['Identify control', 'State the governance measure.'], ['Set accountable role', 'Use a stable role, not a named person.'], ['Assess MATE', 'Record mandate, accountability, trigger, and escalation.']],
    cond: [{ q: 'How will many-to-many relationship views be presented?', to: 'Future risk relationship view.' }] },
  { id: 'REVIEW', code: 'R', name: 'Evidence Review', short: 'EVIDENCE REVIEW', group: 'current', state: 'current', gx: 10.2, gy: 13.8, w: 3.2, d: 2.6, h: 46, kind: 'cards',
    one: 'The auditor records relevance, gaps, contradictions, and sufficiency for each audit question.',
    what: 'Reviewed evidence does not automatically approve a relationship or conclusion. Gaps and contradictions remain visible.',
    how: 'The current capture slice records review status. Full evidence relevance and sufficiency records are the next workbench capability.',
    steps: [['Inspect item', 'The auditor reviews the source and evidence item.'], ['Record relevance', 'Record support, weakness, or contradiction.'], ['Record limits', 'Record gaps, conflicts, and sufficiency.']],
    cond: [{ q: 'When will full evidence review records be built?', to: 'Phase 1 workbench foundation.' }] },
  { id: 'GATES', code: 'G', name: 'MATE And CONTRA Gates', short: 'METHOD GATES', group: 'current', state: 'current', gx: 15.0, gy: 12.7, w: 2.8, d: 2.6, h: 52, kind: 'gate',
    one: 'MATE checks control design and CONTRA challenges conflicting evidence and assumptions.',
    what: 'These gates make method checks visible before approval. They do not replace professional judgement.',
    how: 'MATE is the deterministic assessment method. CONTRA is a recorded challenge that the auditor considers before approval.',
    steps: [['Apply MATE', 'Check mandate, accountability, trigger, and escalation.'], ['Apply CONTRA', 'Expose conflicting evidence or weak assumptions.'], ['Prepare decision', 'Send the reviewed proposal to the auditor.']],
    cond: [] },
  { id: 'DECIDE', code: 'A', name: 'Auditor Decision Gate', short: 'AUDITOR GATE', group: 'current', state: 'current', gx: 19.0, gy: 8.3, w: 3, d: 2.7, h: 58, kind: 'gate',
    one: 'Only the auditor can approve, reject, or request a change to a proposed relationship or conclusion.',
    what: 'The decision is recorded against the same version of the proposal. Technology can organise and check information only.',
    how: 'ACE approval records keep proposal versions and auditor decisions distinct. No automated approval path exists.',
    steps: [['Review proposal', 'The auditor reviews evidence, limits, and method checks.'], ['Record decision', 'Approve, reject, or request a change.'], ['Keep version', 'Keep the decision with the proposal version.']],
    cond: [{ q: 'Who can approve a conclusion?', r: 'Only the accountable auditor. Current ACE rule (2026-08-24).' }] },
  { id: 'APPROVED', code: 'P', name: 'Approved Records', short: 'APPROVED RECORDS', group: 'current', state: 'current', gx: 23.1, gy: 12.6, w: 3.4, d: 2.8, h: 40, kind: 'store',
    one: 'Accepted relationships and auditor-approved conclusions become the controlled records.',
    what: 'A substantive conclusion needs sufficient evidence with no unresolved material gap or contradiction. Otherwise the auditor can approve Not Determined.',
    how: 'Approved relationship and conclusion records stay separate from suggestions, reviewed items, and unapproved versions.',
    steps: [['Accept relationship', 'Store the accepted relationship and auditor decision.'], ['Accept conclusion', 'Store an approved conclusion or Not Determined.'], ['Preserve trace', 'Keep source, version, decision, and limitation visible.']],
    cond: [] },
  { id: 'CLIENT', code: 'C', name: 'Filtered Client View', short: 'CLIENT VIEW', group: 'planned', state: 'planned', ghost: true, gx: 27.8, gy: 7.8, w: 3.2, d: 2.5, h: 38, kind: 'screen',
    one: 'Planned only: a view that could show approved information to a client.',
    what: 'It must show filtered, approved records only. It is not operational and it has no current client data path.',
    how: 'This deferred output needs scope, security, and professional approval before implementation. It is shown as a dashed structure.',
    steps: [['Select approved records', 'Use only records accepted by the auditor.'], ['Apply filter', 'Apply the approved client disclosure rules.'], ['Present view', 'Show the permitted output.']],
    cond: [{ q: 'What client disclosure rules are approved?', to: 'Not decided. This feature is planned only.' }] },
];

export const FLOWS = [
  { id: 'capture', name: 'Fictional Field Capture', hops: [
    ['SRC', 'WB', 'fictional image', { source: 'Fictional site image', type: 'image/jpeg' }, 'yx'],
    ['WB', 'STORE', 'capture record', { evidenceId: 'EVI-FIC-0001', status: 'PENDING_REVIEW' }, 'xy'],
    ['STORE', 'REVIEW', 'review state', { evidenceId: 'EVI-FIC-0001', status: 'PENDING_REVIEW' }, 'xy'],
  ] },
  { id: 'planning', name: 'Planning Trace', hops: [
    ['SCOPE', 'TRACE', 'obligation → risk → control → role', { obligationId: 'OBL-FIC-01', riskId: 'RSK-FIC-01', controlId: 'CTL-FIC-01', roleId: 'ROLE-FIC-01' }, 'yx'],
    ['TRACE', 'GATES', 'MATE assessment', { controlId: 'CTL-FIC-01', mate: 'recorded' }, 'xy'],
    ['GATES', 'DECIDE', 'reviewed proposal', { proposalId: 'REL-FIC-01', contra: 'considered' }, 'yx'],
  ] },
  { id: 'conclusion', name: 'Evidence To Conclusion', hops: [
    ['STORE', 'REVIEW', 'evidence item', { evidenceId: 'EVI-FIC-0001' }, 'xy'],
    ['REVIEW', 'GATES', 'review result', { sufficiency: 'assessed', gaps: 0, contradictions: 0 }, 'yx'],
    ['GATES', 'DECIDE', 'decision pack', { conclusionId: 'CON-FIC-01' }, 'xy'],
    ['DECIDE', 'APPROVED', 'approved conclusion', { result: 'Not Determined', auditor: 'fictional auditor' }, 'xy'],
  ] },
  { id: 'client', name: 'Planned Client Output', hops: [
    ['APPROVED', 'CLIENT', 'approved records only', { records: 2, state: 'planned' }, 'yx'],
  ] },
];

export const CH = [
  { id: 'boundary', title: 'Permitted Input', reveal: ['SRC', 'WB'],
    lede: 'ACE begins at an <mark>external input boundary</mark>. The current workbench accepts fictional image capture only.',
    story: '<p>The source stays identifiable. The workbench helps the auditor capture it locally. It cannot approve it.</p>',
    flow: [['SRC', 'WB', 'fictional image', { source: 'Fictional site image' }]] },
  { id: 'local', title: 'Local Review Context', reveal: ['STORE', 'SCOPE'],
    lede: 'The pilot keeps capture data local and defines the engagement and questions before work starts.',
    story: '<p>The data store is outside the source tree. A ready fictional engagement is required before capture.</p>',
    flow: [['WB', 'STORE', 'capture record', { evidenceId: 'EVI-FIC-0001' }], ['SCOPE', 'WB', 'current engagement', { fictional: true }]] },
  { id: 'method', title: 'Trace And Method Checks', reveal: ['TRACE', 'REVIEW', 'GATES'],
    lede: 'The trace, evidence review, and <mark>method gates</mark> prepare material for an auditor decision.',
    story: '<p>MATE checks design. CONTRA exposes challenge. Evidence review keeps gaps and contradictions visible.</p>',
    flow: [['SCOPE', 'TRACE', 'obligation → risk → control → role', { obligationId: 'OBL-FIC-01' }], ['STORE', 'REVIEW', 'evidence item', { evidenceId: 'EVI-FIC-0001' }], ['REVIEW', 'GATES', 'review result', { sufficiency: 'assessed' }]] },
  { id: 'authority', title: 'Professional Authority', reveal: ['DECIDE', 'APPROVED'],
    lede: 'The <mark>auditor decision gate</mark> is the only approval path to controlled records.',
    story: '<p>ACE can organise information and check method steps. The auditor approves a relationship or conclusion, including Not Determined.</p>',
    flow: [['GATES', 'DECIDE', 'reviewed proposal', { proposalId: 'REL-FIC-01' }], ['DECIDE', 'APPROVED', 'auditor decision', { decision: 'approved' }]] },
  { id: 'planned', title: 'Deferred Client Output', reveal: ['CLIENT'],
    lede: 'The filtered client view is <mark>planned only</mark>. The dashed structure is not switched on.',
    story: '<p>Only approved records could enter it. Scope, security, and professional approval are still required.</p>',
    flow: [['APPROVED', 'CLIENT', 'planned output', { state: 'not operational' }]] },
  { id: 'all', title: 'Whole Atlas', reveal: [],
    lede: 'All structures are shown. Use the flow picker to inspect each representative fictional flow.',
    story: '<p>Hover a structure to read it. Click to pin it. Use Go inside to see its steps. Dashed structures are planned and not operational.</p>',
    flow: null },
];

export const HOW_HTML = `<div class="eyebrow">ACE System Atlas · fictional pilot</div><h1 class="t">How It Is Built</h1><div class="sub">one editable data source builds both review outputs</div>
<h3 class="sec">Editable Source</h3><p><code>data.mjs</code> holds the architecture data. It has no client evidence or private source text.</p>
<h3 class="sec">Offline Output</h3><p><code>build.mjs</code> writes SYSTEM.md and atlas.html. The HTML embeds its data and script. It loads no network asset.</p>
<h3 class="sec">Professional Boundary</h3><p>Technology organises and checks information. The auditor approves relationships and conclusions.</p>`;
