# ACE Vision And Roadmap

**Status:** Working internal roadmap  
**Date:** 13 August 2026  
**Last updated:** 7 September 2026  
**Client authority:** `LOCAL_HOME\OneDrive - AuditCo\SQE\SQE-EOI-Review-260810-V3.pdf`

**Current delivery state:** The five-day diagnostic EOI has been sent. The
client has not accepted the review proceeding. Until acceptance, use only
fictional, public or AuditCo-owned material for platform development.

## Purpose

The Assurance Compass Engine (ACE) will become a private auditor workbench.

The workbench will help the auditor to:

- collect controlled evidence;
- see links between risks, controls, owners and evidence;
- find gaps and conflicts;
- apply MATE and CONTRA;
- record the auditor's decision; and
- show the client only approved information.

The auditor remains responsible for professional judgement. Technology will
organise information. It will not make the audit decision.

## Current Position

The client-facing EOI and the MATE methodology remain the professional
authority. This roadmap explains how to build the private auditor workbench.
It does not change the EOI, MATE, CONTRA or evidence approval rules.

The earlier generated files are working material. The current EOI V3 is the
client authority. The ACE Sprint 4 design is the authority for the current
fictional software pilot.

The current ACE code is not yet a full risk register product. It contains a
small approved planning trace. That trace proves the relationship pattern:

```text
Obligation -> Risk -> Control -> Accountable Role -> MATE Rating
```

The future risk register engine will handle many risks, controls, owners,
triggers, evidence items, actions and review states.

The first mobile field-capture slice is now built for fictional local testing.
It provides an authenticated, responsive workbench page, image capture,
external SQLite and media storage, evidence IDs, review status and live counts.

This slice does not yet support protected offline drafts. It also uses HTTP on
private Wi-Fi. Do not use it for real client evidence. A physical iPhone test
and an approved secure data design remain required.

## North Star

For every important conclusion, the auditor can answer:

1. What was the question?
2. What evidence supports the answer?
3. What evidence conflicts with the answer?
4. Which risk, control and owner are involved?
5. Who approved the relationship?
6. Why is the conclusion allowed?

The answer must lead back to the source evidence and the approval record.

## Workspace Boundary

Use the [ACE Progress Guide](ACE_PROGRESS_GUIDE.html) to see the current
phase, gates and working checklist.

The active workspace contains source, tests, method documents and build
instructions. Generated temporary material is kept outside the active
workspace in the dated `sqe-quarantine-2026-08-12` folder. No file was deleted
during this cleanup.

Keep `ss` and older reference folders for a separate review. Do not move them
into a build or external hand-off pack until their status is known.

## One Simple Picture

```text
Source document
      |
      v
Possible facts and links
      |
      v
Auditor checks the source
      |
      v
Risk Register Engine checks the relationships
      |
      v
MATE and CONTRA approval gates
      |
      v
Approved records
      |
      +--> Auditor relationship view
      |
      +--> Filtered client view
```

The graph is a map. ACE is the control room. The approved record is the
authority.

## The Roles Of People And Tools

These are different roles. They must not be treated as one product.

| Person or tool | Plain-English job | It must not do |
| --- | --- | --- |
| Auditor | Makes the professional decision | Delegate approval to software |
| ACE and MATE | Apply the agreed assurance method | Invent evidence or change the method |
| CONTRA | Challenges evidence and proposed conclusions | Hide a conflict |
| Auditor Workbench | Gives the auditor one place to work | Become the source of truth by itself |
| Risk Register Engine | Checks and displays proposed links | Guess that a link is correct |
| LangExtract | Reads text and suggests facts, source locations and possible conflicts | Approve a fact or conclusion |
| Sift-KG | Suggests document entities and relationships, with links to source passages | Approve evidence, complete MATE or become the authoritative audit record |
| OpenViking | Deferred candidate that returns source-linked context to ACE | Store approval records, make audit decisions or provide session memory during the first pilot |
| Neo4j | Stores and displays approved relationships as a map | Decide that a relationship is valid |
| Semantica | Future candidate for a rebuildable relationship and provenance view | Replace ACE, store the authoritative audit record or approve a decision |
| LangGraph | May guide a later multi-step workflow | Replace the approval gates |
| Graphify | Helps us understand project files and documents | Store client evidence or approve audit records |
| Codex | Leads the local build, review and integration work | Send client evidence to an external builder |
| Pocock Skills | Give Codex a repeatable way to plan, model, build, grill and verify | Store data or make audit decisions |
| Vorflux | Optional external build or prototype helper | Become the project owner or receive client evidence by default |

### Codex

Codex is the local lead for this project.

Codex will:

- read the current project authority;
- keep the work aligned with MATE and CONTRA;
- use the approved local repository;
- apply the Pocock skills when useful;
- review work from any other builder;
- run tests and checks; and
- keep client data in the approved local data boundary.

Codex is not the auditor. The auditor remains the decision maker.

### Pocock Skills

The Pocock skills are a working method for Codex.

They help Codex to:

- ask hard questions before building;
- define the records and relationships;
- write a clear plan;
- build in small steps;
- test the result;
- review the code; and
- explain the result in plain English.

The skills are instructions for how to work. They are not part of the audit
data store. They do not replace the ACE approval gate.

### SwiftUI Pro

Use SwiftUI Pro for the native read-only client and later approved SwiftUI work.
It checks APIs, views, data flow, navigation, accessibility and performance.
The skill is installed locally at fixed source commit `be297ff80dddec529af1f9b1f1f114aab6c9d11c`.

Follow the [SwiftUI skill instructions](docs/agents/swiftui-skill.md).
Keep the approved app specification and platform versions authoritative.
Keep the existing review and release checks.
See the [Phase 7 progress map](ACE_PROGRESS_GUIDE.html#ios-development-path-title) for the recorded client candidate and evidence status.

### Vorflux

Vorflux is an optional second build lane.

Do not send the whole SQE repository to Vorflux. The repository contains
superseded documents, client-related material and temporary folders.

Create a small, deliberate hand-off pack instead. Include only the files that
the task needs, after a local review. Exclude client evidence, `tmp`,
`audit_work`, `output`, `ss`, Explorer material, credentials, generated files
and superseded documents unless a specific decision approves them.

Use it only for:

- prototypes;
- sanitised code;
- fictional records; or
- other material with an approved data-handling decision.

Codex remains the local project owner. Any Vorflux output is a proposal. It
must pass local review, tests and the project approval rules.

The safe hand-off sequence is:

```text
Select needed files
      -> remove sensitive and superseded material
      -> check the file list locally
      -> send the small pack only if approved
      -> review the returned work in Codex
```

Before using Vorflux with any sensitive material, confirm its:

- storage location;
- retention period;
- model and service providers;
- training-data rules;
- access controls; and
- deletion process.

Until these rules are approved, keep client evidence local.

The default is no client data and no whole-repository transfer.

### The Auditor Workbench

The workbench is the place where the auditor works. It should be ready for
LangExtract from the first design, even when manual entry is used first.

This means building a spare intake place for candidate facts. It does not mean
running AI extraction in Sprint 4.

```text
Manual fact entry now
        |
        +--> same candidate-fact review screen later
                         |
                         +--> LangExtract suggestions
```

The workbench must show the source words, the suggested fact, the confidence
or warning, the auditor's review and the final status.

Use `○` for each suggestion. Use `✓` only after the auditor confirms the same
proposal version. A provider result cannot set the confirmed state.

## Provider-Neutral Extraction And Retrieval Boundaries

ACE owns the audit records, proposal queues, decisions and approval gates.
Provider adapters can supply extraction results or context search results.
They cannot write approved records.

Use these logical boundaries:

```text
Selected source text
      -> extraction adapter
      -> raw provider result
      -> ACE proposal queue ○
      -> auditor decision
      -> confirmed ACE record ✓

ACE context request
      -> retrieval adapter
      -> source-linked context results
      -> auditor workbench
```

An extraction result must identify its engagement, source, source version,
source location, provider run and transformation version. ACE must preserve
the raw result before it maps any item into a proposal queue.

A retrieval result is context only. It must identify its engagement, source,
source version, source location, rank and provider run. It is not evidence,
a relationship, a conclusion or an approval.

The mobile app must call only the ACE API. It must not call Sift-KG,
OpenViking, a model provider or a graph store.

The controlled design is in
[Provider-Neutral Extraction And Retrieval Boundaries](docs/specs/2026-08-23-ace-provider-neutral-extraction-and-retrieval-boundaries.md).

## The Relationship Between The Tools

```text
Pocock Skills
      |
      v
Codex plans, builds and checks
      |
      +--> ACE method and approval gates
      |
      +--> Auditor Workbench
      |          |
      |          +--> LangExtract suggests facts
      |          +--> Sift-KG suggests facts and possible links
      |          +--> OpenViking returns source-linked context
      |          +--> Risk Register Engine checks links
      |          +--> Neo4j displays approved links
      |
      +--> Optional Vorflux prototype output
```

The safe rule is:

> LangExtract and Sift-KG suggest. OpenViking retrieves context. The Risk
> Register Engine checks. Neo4j shows. ACE governs. The auditor approves.

## Build Roadmap

### Phase 0 — Keep The Method Safe

**Current priority.**

Complete and verify ACE Sprint 4 as a fictional, domain-only pilot.

Keep these rules:

- MATE remains the deterministic rating authority;
- evidence, gaps and conflicts remain visible;
- human approval remains required;
- no real client evidence enters the demo; and
- no graph, extraction or external service enters Sprint 4.

The authority is the [ACE Sprint 4 Design](docs/superpowers/specs/2026-07-28-ace-sprint-4-evidence-to-conclusion-design.md).

### Phase 1 — Build The Auditor Workbench Foundation

Create the auditor's private working area.

**Current state:** Started. The first fictional mobile capture and review slice
is built. Full workbench records and protected offline drafts remain open.

It should support:

- an engagement;
- a selected scope;
- questions;
- evidence identifiers;
- source location and version;
- proposed facts;
- proposed relationships;
- gaps and conflicts;
- review status; and
- auditor decisions.

Build this with manual entry first. This proves the method without depending
on an AI tool.

From the outset, reserve the candidate-fact intake interface that LangExtract
will use later. Manual facts and extracted facts must use the same review path.

### Phase 2 — Build The Risk Relationship View

Show the main SQE chain:

```text
Obligation
  -> Risk
  -> Control
  -> Accountable Role
  -> Trigger
  -> Evidence
  -> Action
  -> MATE Assessment
  -> Approved Conclusion
```

The auditor must be able to move forward and backward through the chain.

Every relationship must show:

- its source;
- its status;
- its version;
- its reviewer; and
- its approval decision.

### Phase 3 — Add Controlled Evidence Intake

Add a controlled evidence store outside the code repository.

Do not place client evidence in the Explorer folder, `graphify-out`, `tmp`,
or source-control folders.

The same rule applies to any external build or research service. The
repository is not a safe upload pack. Select a small reviewed file set.

The workbench should receive an evidence reference as the auditor works. The
source file stays in the controlled evidence store. The workbench stores the
evidence ID, source details and links to the review records.

Each item needs:

- an evidence ID;
- source name and location;
- received date;
- version or freshness status;
- owner or provider;
- confidentiality status; and
- links to the questions and relationships that use it.

### Phase 4 — Add LangExtract As A Review Assistant

Design the workbench so that an extraction service can be connected later.

This does not mean adding LangExtract to Sprint 4. It means that the future
workbench has a place for candidate facts.

The future flow is:

```text
Document
   -> LangExtract suggests a fact
   -> Workbench shows the exact source words
   -> Auditor accepts, changes or rejects the fact
   -> Risk Register Engine checks the relationship
```

LangExtract may also raise a possible conflict. For example, two documents
may name different owners. The auditor must check the documents and decide
what the conflict means.

Examples of warnings include:

- two documents name different owners;
- two documents give different trigger dates;
- a control appears in one document but not another; or
- an evidence statement does not clearly support the proposed control.

These are warnings for review. They are not findings, ratings or approvals.

Sift-KG is another candidate for this review-assistant role. It can read a
document set, suggest entities and relationships, and link each suggestion to
its source passage. ACE must keep each output as a proposal until an auditor
accepts, changes or rejects it.

Sift-KG sends document text to the selected language model. If that model runs
online, client information can leave the local computer. The online provider
can then receive that information. LiteLLM connects Sift-KG to the selected
model. Do not send client information until the model and data controls have
approval.

The separate fictional pilot is in
[Sift-KG Fictional-Data Pilot](docs/specs/2026-08-23-sift-kg-fictional-data-pilot.md).

### Phase 5 — Add A Rebuildable Graph View

Only after approved records exist, test a graph projection.

The first approved-projection candidate is Neo4j, using fictional data first.
Semantica is another future candidate for relationship, provenance and conflict
views. Each projection tool must read approved records and build a visual map.
It must not write approval records or become the authoritative audit record.

Sift-KG can support a separate document-discovery and exploratory graph pilot.
That graph can use raw proposals. It must stay separate from approved graph
projections. A graph merge cannot change an ACE approval state.

Keep the interface provider-neutral. This allows a later comparison with
another graph tool without changing the ACE method.

#### Deferred Context Search Candidate — OpenViking

OpenViking is a deferred context-search candidate. Its first pilot must use
fictional data only. It must disable session memory. It must return context to
ACE without writing audit records. Legal review must address its AGPLv3
licence before installation, integration or distribution.

The separate fictional pilot is in
[OpenViking Fictional-Data Pilot](docs/specs/2026-08-23-openviking-fictional-data-pilot.md).

### Phase 6 — Add The Client View

Add a separate read-only client view after the auditor workbench is stable.

The client may see:

- approved findings or conclusions;
- approved supporting evidence references;
- agreed actions;
- owners and dates; and
- visible limitations.

The client must not see draft facts, rejected links, private auditor notes or
unapproved conclusions.

### iOS UI Style System — Planned

Record this work for the iOS app. Implementation needs a separate approved task
in the application repository. This item does not change app functions or delivery gates.

- [ ] Define shared SwiftUI values for type, colour, spacing, corners and shadows.
- [ ] Use Inter Tight titles: 22/28 points, Semi Bold, with -0.7-point tracking.
- [ ] Use Inter Tight section headers: 19/24 points, Semi Bold.
      Resolve tracking before implementation: the supplied +0.6 conflicts with negative tracking for every heading.
      The proposed section-header value is -0.3 points.
- [ ] Use Inter Tight body text and day labels: 14.5/18 points, Regular, with +0.3-point tracking.
- [ ] Check font availability and support text scaling.
- [ ] Use circular buttons, 38–46 points, with a minimum 44-point touch area.
      Use an inset highlight and soft drop shadow. Avoid flat fills.
      Define the supplied 6-point inset highlight before implementation.
- [ ] Use card corner radii of 12–18 points by depth, with layered shadows instead of borders.
- [ ] Map `--text`, `--muted` and `--strong` to primary text, secondary text and icons.
- [ ] Use thin dividers with the `--track` colour value. Do not add a separate visible border colour.
- [ ] Apply the system to one existing screen first, using fictional data.
- [ ] Check text scaling, contrast, touch areas and light and dark appearance on the pilot screen.
- [ ] Review the pilot before applying the shared styles across the app.

Acceptance: the pilot uses shared values and components. Text remains readable at
supported sizes. Controls remain usable. Record the final tracking and highlight values.
Keep existing navigation, app functions and data controls unchanged.

### Phase 7 — Consider A Native SwiftUI Auditor App

Keep the responsive FastAPI workbench as the current delivery path.

Consider a native iPhone app after the web workbench and shared API are stable.
Start with the Xcode iOS App template. Use SwiftUI and Swift.

The first native app should use these main areas:

- Home for engagement status and work counts;
- Work for review and approval queues;
- Capture for image evidence; and
- Map for approved evidence relationships.

The native app must use the same ACE records and approval gates. FastAPI and
the ACE domain engines remain the source of truth. The app must not keep a
second authoritative audit record.

Use a shared, versioned JSON API for the web workbench and future native app.
Use iOS Keychain storage for credentials. Use the system camera interface for
the first image-only capture function.

Do not start the native app until:

- the six approved auditor workflows are stable;
- the web workbench has stable API contracts;
- authentication and device-access rules are approved;
- secure hosting and storage rules are approved; and
- a fictional-data iPhone prototype has an approved test plan.

Do not add offline queues, audio, video, OCR or transcription to the first
native prototype. Real client use remains held at G0.

#### Phase 7 App Delivery Checklist

Use this checklist only after approval of the Phase 7 start gates. It does not
change the approved architecture or data controls.

Select the native SwiftUI path or the Expo path before technical setup. The
current roadmap selects native SwiftUI. Expo and JavaScript items apply only
after approval of an architecture change.

Use a database when shared records, backup, device sync or controlled access
need it. Use local device storage only when the app has no shared-data need.
The ACE auditor app must use the shared ACE API and authoritative records.

##### 1. Technical Setup

- [ ] Set up the project with the approved coding agent.
- [ ] Create the GitHub repository.
- [ ] Set up an Expo Go build, if the approved path uses Expo.
- [ ] Install the approved dependencies.
- [ ] Set up over-the-air updates for JavaScript fixes, if applicable.
- [ ] Integrate Sentry and Mixpanel.
- [ ] Integrate AppsFlyer, if attribution data is approved.
- [ ] Run the `apple-appstore-reviewer` repository checks.

###### Expo Over-The-Air Update Controls

Use EAS Update only if an approved architecture change selects Expo and React
Native. Native SwiftUI releases must use the App Store release process.

- [ ] Configure the approved EAS project URL and enable updates.
- [ ] Define and test runtime-version compatibility for each store build.
- [ ] Select the cold-start update check and cache fallback behaviour.
- [ ] Measure launch delay before use of a non-zero cache fallback timeout.
- [ ] Confirm that an update check occurs only at the intended app lifecycle event.
- [ ] Limit OTA content to JavaScript, TypeScript and compatible assets.
- [ ] Use a new store build for native modules, native settings and SDK upgrades.
- [ ] Do not use OTA updates to enable a function that App Review did not assess.
- [ ] Check the current App Store Review Guidelines before each release.
- [ ] Require a clean, committed working tree before publication.
- [ ] Link each EAS update identifier to its source commit and runtime version.
- [ ] Pin the approved EAS CLI version in the release procedure.
- [ ] Test the update against a production build before publication.
- [ ] Use a staged rollout for changes with material user impact.
- [ ] Monitor Sentry and approved product measures during the rollout.
- [ ] Increase the rollout only after the acceptance checks pass.
- [ ] Configure update code signing before production use.
- [ ] Test rollback to a prior update and the embedded app bundle.
- [ ] Record the release, test evidence, rollout result and rollback point.

An OTA update cannot change native code already installed on the device. A
native dependency, permission, icon, launch screen or SDK change needs a new
store build.

##### 2. Navigation And Foundation

- [ ] Integrate the native Liquid Glass navigation bar, if supported.
- [ ] Prepare language localisation.
- [ ] Add a responsive layout with safe areas and correct padding.

##### 3. App Store Connect Preparation

- [ ] Create the bundle identifier.
- [ ] Create the app in App Store Connect.

##### 4. Storage And Database

- [ ] Create a Supabase project or use approved local storage.
- [ ] Connect the code with controlled URLs and API keys.
- [ ] Enable row-level security when the app uses Supabase.
- [ ] Model the required tables.
- [ ] Add Apple Sign In or Google Sign In, if required.
- [ ] Show the paywall before sign-up when the approved flow requires it.
- [ ] Define the onboarding flow.
- [ ] Add an edge function to delete a user, if applicable.

##### 5. Onboarding

- [ ] Add the launch screen.
- [ ] Add the TikTok Ads SDK only if advertising data use is approved.
- [ ] Show the App Tracking Transparency prompt before SDK initialisation.
- [ ] Add the onboarding steps.
- [ ] Add the approved notification request.
- [ ] Add the rating prompt.
- [ ] Add the RevenueCat or Superwall paywall.
- [ ] Add sign-up and sign-in with clear progress-saving text.
- [ ] Set secure password field properties.
- [ ] Clear password fields before navigation.
- [ ] Add a short delay before navigation, if testing shows it is necessary.
- [ ] Complete the Mixpanel event integration.

##### 6. Purchases With RevenueCat

- [ ] Create the in-app products in App Store Connect.
- [ ] Create the RevenueCat project and add the app.
- [ ] Create the entitlement.
- [ ] Import or create products and link them to the entitlement.
- [ ] Create the default offering.
- [ ] Add the monthly, yearly and lifetime packages, as applicable.
- [ ] Initialise the SDK and fetch the offerings.
- [ ] Implement the purchase flow.
- [ ] Add Restore Purchases.
- [ ] Store the user entitlement in Supabase, if approved and required.
- [ ] Submit an unfinished build for review when it meets review requirements.
- [ ] Add a subscription guard to protected screens.
- [ ] Add a cancellation flow with an approved special offer, if applicable.

##### 7. App Store Connect Listing

- [ ] Add the app name, subtitle and keywords.
- [ ] Add iPhone and iPad screenshots.
- [ ] Add a benefit-focused description and promotional text.
- [ ] Add the privacy policy.
- [ ] Add the support URL.
- [ ] Add the listing localisations.
- [ ] Add the review notes.

##### 8. Additional Assets

- [ ] Translate all user text.
- [ ] Confirm that `CFBundleLocalizations` is in the final `Info.plist`.
- [ ] Add the app icon.
- [ ] Complete privacy, age-rating and other App Store Connect pages.
- [ ] Add widgets only when they are in the approved release scope.

##### 9. Build And Testing

- [ ] Create the release candidate build.
- [ ] Test sign-in and sign-out.
- [ ] Test purchases and purchase restoration.
- [ ] Test supported iPhone and iPad sizes, including Pro models.
- [ ] Create and test notifications.
- [ ] Test App Store review access and all review notes.

### Phase 8 — Add LangGraph Only If The Workflow Needs It

LangGraph may later coordinate steps such as:

```text
Receive evidence
  -> extract candidates
  -> wait for auditor review
  -> check relationships
  -> wait for approval
  -> prepare the next work item
```

LangGraph would conduct the workflow. It would not store the authoritative
audit record or replace MATE, CONTRA or the auditor.

## What To Build Now

Build now:

- ACE Sprint 4 verification;
- the workbench record model;
- manual evidence and relationship entry;
- the risk relationship view;
- proposed and approved status; and
- a controlled data-handling boundary.

Keep for later:

- LangExtract connection, while designing its intake boundary now;
- Sift-KG, as a fictional-data document-discovery and graph pilot;
- OpenViking, as a deferred fictional-data context-search pilot after legal review;
- Neo4j, while designing a provider-neutral graph boundary now;
- Semantica, as a later fictional-data graph and provenance experiment;
- a native SwiftUI auditor app, after the shared API and security rules are stable;
- LangGraph, only if the later workflow needs durable pause and resume;
- cloud builders;
- automated document collection; and
- client access.

## Site-Work Sequence

When the client approves the review and the data rules are ready:

1. Create the engagement and selected scope.
2. Record each received item in the controlled evidence store, not the
   Explorer folder.
3. Review the source and create facts or extraction candidates.
4. Mark gaps and possible conflicts.
5. Link risks, controls, owners, triggers and evidence.
6. Apply MATE and CONTRA.
7. Approve or reject each relationship.
8. Build the auditor relationship view.
9. Prepare the filtered client view.

## Decision Gates

Do not move to the next phase until the earlier gate is met.

| Gate | Question |
| --- | --- |
| G0 — Client And Data Readiness | Has the client accepted the review and are the data rules approved? If not, use only fictional, public or AuditCo-owned material. |
| G1 — Method | Does the work follow the current EOI, MATE and CONTRA method? |
| G2 — Evidence | Can every item keep its source, version and status? |
| G3 — Relationships | Can the auditor approve or reject each proposed link? |
| G4 — Graph | Does the graph rebuild from approved records only? |
| G4R — Retrieval | Does context search stay engagement-bound, source-linked and separate from approval? |
| G5 — Client View | Can the client see approved information only? |
| G6 — Native App | Does the app use ACE records and gates without creating a second source of truth? |

## Final Rule

The platform may help the auditor see more. It must never make the auditor
responsible for a decision that the auditor did not make.

The Vorflux investigation brief is
[ACE Sift-KG And OpenViking Investigation](ACE_SIFT_KG_OPENVIKING_INVESTIGATION_VORFLUX.md).
It permits research and design review only. It does not approve implementation.
