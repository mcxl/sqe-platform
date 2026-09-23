# SQE Sprint 3.5 Reference Learning Review

**Date:** 28 July 2026
**Status:** Approved reference guidance
**Approval scope:** May inform Sprint 4 design only
**Implementation authority:** None

## Objective

This review identifies useful, publicly documented patterns that can inform the
next SQE design without allowing an external technology, schema or product to
replace the SQE assurance methodology.

The governing principle remains:

> Technology should support the methodology without becoming the methodology.

This review does not approve a Sprint 4 scope. It does not approve installation,
integration, data migration, persistence, retrieval, GraphRAG, artificial
intelligence or external sharing.

## Current SQE Baseline

The completed local SQE foundation provides:

- deterministic MATE control-design assessment;
- MATE meaning only Mandate, Accountability, Trigger and Escalation;
- controlled evidence review for MATE;
- explicit human auditor decisions;
- evidence provenance and basic contradiction blocking;
- one accepted obligation-risk-control-accountable-role planning trace;
- matching of that trace to the approved MATE assessment and rating;
- controlled construction of accepted trace records;
- deterministic forward and reverse trace views; and
- fictional, local and private operation.

The wider Connected Assurance platform is not implemented. In particular, SQE
does not yet provide implementation or effectiveness assessment, full CONTRA
challenge, findings, actions, historical replay, persistent formal records,
client segregation, retrieval or graph projection.

## Public References Reviewed

### NIST OSCAL

Primary sources:

- [OSCAL Layers And Models](https://pages.nist.gov/OSCAL/learn/concepts/layer/)
- [OSCAL Assessment Results Model](https://pages.nist.gov/OSCAL/learn/concepts/layer/assessment/assessment-results/)
- [OSCAL Plan Of Action And Milestones Model](https://pages.nist.gov/OSCAL/learn/concepts/layer/assessment/poam/)
- [OSCAL Model Overview And Identifiers](https://pages.nist.gov/OSCAL/learn/concepts/layer/overview/)
- [NIST OSCAL Repository](https://github.com/usnistgov/OSCAL)

OSCAL separates:

1. control catalogues and profiles;
2. system and component implementation descriptions;
3. assessment plans;
4. assessment results, observations, evidence, risks and findings; and
5. remediation tracking through plans of action and milestones.

It uses structured identifiers, UUIDs, metadata, document versions,
last-modified timestamps, references and common back-matter resources.

OSCAL is an information-exchange language. It does not define the SQE
methodology, MATE rules or SQE auditor decision gates.

### Auditree

Primary sources:

- [Auditree Design Principles](https://complianceascode.github.io/auditree-framework/design-principles.html)
- [Auditree Quick Start And Signed Evidence](https://complianceascode.github.io/auditree-framework/quick-start.html)
- [Auditree Framework Repository](https://github.com/ComplianceAsCode/auditree-framework)

Auditree separates:

1. evidence fetching;
2. evidence storage;
3. deterministic checking;
4. reporting; and
5. optional fixing and notification.

Its evidence model distinguishes raw, derived, temporary, external and report
evidence. Evidence can have a time-to-live, an explicit empty state, partitioning
and signature verification. Its evidence locker uses Git history and can use
signed commits.

Auditree is oriented towards automated compliance checks. Its check outcome is
not a substitute for an SQE auditor decision.

### CISO Assistant

Primary sources:

- [CISO Assistant Core Concepts](https://intuitem.gitbook.io/ciso-assistant/product-docs/introduction/core-concepts)
- [CISO Assistant Compliance Model](https://intuitem.gitbook.io/ciso-assistant/model/compliance)
- [CISO Assistant Organisation And Domains](https://intuitem.gitbook.io/ciso-assistant/model/organization)
- [CISO Assistant IAM Model](https://intuitem.gitbook.io/ciso-assistant/model/organization/understanding-the-iam-model)
- [CISO Assistant Repository](https://github.com/intuitem/ciso-assistant-community)

CISO Assistant provides connected GRC objects including frameworks,
requirements, reference controls, applied controls, risks, evidence, audits,
findings, follow-up and tasks.

Its organisation model uses domains and perimeters. Domains provide access
boundaries and role-based permissions. Its public documentation describes
authentication, approver roles, audit logs and controlled machine access.

CISO Assistant is a broad GRC platform. Its compliance statuses, automatic
mapping and product workflows do not replace SQE assessments or decisions.

## Comparison Matrix

| SQE Topic | OSCAL Contribution | Auditree Contribution | CISO Assistant Contribution | SQE Decision | Reason |
|---|---|---|---|---|---|
| Methodology ownership | Neutral exchange models | Automated check framework | Configurable GRC workflows | Reject substitution | SQE remains the assurance method |
| Layered assurance records | Control, implementation and assessment layers | Fetch, evidence, check and report separation | Reference and applied controls, audits and follow-up | Adopt the separation | Prevents design, implementation and effectiveness from being confused |
| Identifiers | Human-readable IDs, UUIDs and references | Stable evidence paths | URNs and linked objects | Adapt | Retain readable SQE IDs and add durable internal identity only when needed |
| Record revision | Metadata, versions, UUIDs and timestamps | Git history | Object revisions and audit log | Adapt | SQE needs immutable decisions and explainable change history |
| Evidence provenance | Evidence links and back matter | Raw evidence retained separately | Evidence linked to controls and assessments | Adopt | Every conclusion must remain traceable to its source |
| Raw and derived evidence | Observations can reference evidence | Explicit raw and derived evidence types | Evidence can support controls or requirements | Adopt | Derived analysis must never be mistaken for original evidence |
| Evidence freshness | Assessment result expiry is representable | Time-to-live and stale-evidence blocking | Lifecycle attributes | Adapt | SQE should use explicit current, stale and superseded states rather than hidden defaults |
| Evidence completeness | Structured observations and findings | Explicit empty-state handling | Assessment progress and statuses | Adapt | Missing evidence must remain visible and must not silently become a pass |
| Deterministic checks | Schemas support validation | Checks run separately from fetching | Consistency and workflow checks | Adopt with limits | Checks may flag issues but must not approve material audit conclusions |
| Auditor approval | Roles and attestations are representable | Review of evidence transformations is recommended | Approver roles and approval workflows | Retain SQE approach | Explicit SQE decisions remain the controlling gate |
| Findings | Structured findings linked to observations and risks | Report evidence | Findings and follow-up objects | Adapt later | Findings should be reconstructed from approved facts and evidence |
| Corrective actions | POA&M remediation and disposition | Optional fixers | Applied controls, tasks and follow-up | Adapt later | SQE actions require owners, due dates, evidence and effectiveness review |
| Automatic remediation | Not the purpose of the models | Optional fixers | Workflow actions | Reject for audit decisions | SQE must not change client systems or close findings automatically |
| Client-data segregation | Not an application access model | Locker configuration is deployment-specific | Domains, hierarchical RBAC and audit logging | Learn before persistence | Real client data requires enforceable isolation and access control |
| Reporting | Assessment results and POA&M exchange | Reports generated from checks | Dashboards and reports | Adapt later | Generated content must remain a controlled draft until auditor approval |
| Interoperability | XML, JSON and YAML standard models | Python and evidence-file conventions | API-first object model | Preserve an OSCAL mapping option | SQE should not adopt a full external schema prematurely |
| Retrieval | References and links, not a retrieval engine | Git and evidence paths | Application search and API | Defer | Formal records and security must exist before retrieval is introduced |
| Graph technology | Not required | Not required | Linked application objects | Reject as a starting point | Accepted relationships can later support a rebuildable projection |

## Adopt

SQE should adopt the following principles:

1. **Separate assurance layers.** Control design, implementation and operating
   effectiveness require different evidence and different conclusions.
2. **Separate evidence acquisition from assessment.** Collecting evidence must
   not contain conclusion logic.
3. **Preserve raw evidence.** Any transformation or summary must identify its
   source and remain distinguishable from the source.
4. **Make freshness explicit.** Stale, expired, superseded and missing evidence
   must remain visible.
5. **Use stable identity and references.** Records and relationships must retain
   durable identities across revisions.
6. **Connect observations, findings and actions.** Later lifecycle records
   should reference the approved records from which they arose.
7. **Design security boundaries before real data.** Client scope, roles,
   permissions and audit logging must be designed before persistence.

## Adapt

The following public patterns are useful only after adaptation:

1. **OSCAL compatibility:** use OSCAL as a possible interchange mapping, not as
   the internal SQE methodology or an immediate full schema.
2. **Auditree evidence types:** use the raw-versus-derived and freshness
   distinctions, but store future formal records in an approved client-data
   architecture rather than automatically using a Git evidence locker.
3. **Automated checks:** treat automated results as proposed signals requiring
   auditor review when they affect a material conclusion.
4. **CISO Assistant domains:** learn from scoped RBAC and audit logging, but
   design SQE segregation around actual AuditCo client and engagement
   requirements.
5. **Findings and actions:** preserve the useful record relationships while
   retaining SQE-specific finding approval and effectiveness requirements.

## Reject

SQE should reject:

- replacing MATE with an external compliance status;
- treating compliance automation as audit judgement;
- allowing evidence collection code to decide conclusions;
- automatically accepting mapped controls or relationships;
- automatically closing findings or changing client systems;
- adopting a large all-in-one GRC platform before the method is proven;
- storing real client evidence in a general Git repository by default;
- building API, user-interface, vector or graph infrastructure before formal
  records and security boundaries are approved;
- importing an entire external schema when a small mapping boundary is enough;
  and
- treating an external product's object names as the SQE methodology.

## Implications For The Next SQE Design

The next design should remain a single fictional-chain pilot. It should consider:

1. an `AuditQuestion` record that states one precise review question;
2. decomposition into answerable sub-questions;
3. an evidence matrix that separates design, implementation and effectiveness;
4. explicit raw, derived and auditor-authored evidence classifications;
5. evidence source, collection time, validity period and status;
6. explicit evidence gaps and contradictions;
7. proposed implementation and effectiveness conclusions;
8. independent human approval of those conclusions; and
9. retention of MATE solely for control-design assessment.

The next design should not yet add:

- PostgreSQL or Supabase;
- full-text or vector retrieval;
- graph projection or GraphRAG;
- automated evidence collection from client systems;
- findings, report generation or corrective actions;
- real client evidence; or
- a production user interface.

CONTRA should follow once the broader evidence matrix and the distinction
between design, implementation and effectiveness are stable.

## Recommended Sequence

1. Approve this reference learning review.
2. Design Sprint 4 as one fictional Evidence-to-Conclusion pilot.
3. Keep Sprint 4 local, deterministic and human-controlled.
4. Test the methodology with fictional evidence.
5. Design CONTRA only after the evidence model is stable.
6. Design persistence, security and client segregation before any real data.
7. Add retrieval only after formal records exist.
8. Consider graph projection only after accepted relationships exist at useful
   scale.

## Decisions Not Made

This review deliberately does not decide:

- the Sprint 4 record names or exact fields;
- a database product or hosting model;
- whether OSCAL import or export will be implemented;
- a client tenancy model;
- an evidence file-storage mechanism;
- a retrieval or embedding model;
- a report format;
- a GraphRAG product; or
- production deployment.

Each requires a later, separately approved design.

## Review Conclusion

The public projects confirm that SQE should not invent basic information
management patterns from scratch. They also confirm that no external project
should be adopted as the SQE method.

The safest direction is:

> OSCAL-informed records, Auditree-informed evidence discipline and
> CISO-Assistant-informed access boundaries, governed throughout by SQE
> methodology and explicit auditor decisions.
