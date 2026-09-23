# Vorflux Investigation: ACE, Sift-KG And OpenViking

## Authority

This instruction permits research and design review only.

It does not permit implementation, installation, deployment or repository changes.

Vorflux must return a report for local Codex and auditor review.

## Goal

Investigate controlled ACE roles for Sift-KG and OpenViking.

Test the proposed boundaries against current official product evidence.

Identify facts, gaps, risks and decisions before any pilot implementation.

## Sanitised Hand-Off Pack

Send only locally reviewed copies of these files:

- `CONTEXT.md`
- `ACE_VISION_AND_ROADMAP.md`
- `docs/specs/2026-08-23-ace-provider-neutral-extraction-and-retrieval-boundaries.md`
- `docs/specs/2026-08-23-sift-kg-fictional-data-pilot.md`
- `docs/specs/2026-08-23-openviking-fictional-data-pilot.md`
- this instruction

Do not send the repository or its Git history.

Do not send `DEV_STATE.md`, client files, source evidence, credentials or temporary files.

Do not send real names, personal information or real Engagement records.

## Locked Boundaries

- ACE remains the authoritative audit system.
- The auditor remains the approval authority.
- Sift-KG supplies proposals and an exploratory graph only.
- Raw Sift-KG results enter ACE proposal queues.
- A Sift-KG graph merge is not approved data.
- OpenViking supplies context search only.
- OpenViking session memory stays disabled for the first pilot.
- The mobile app calls only the ACE API.
- Use fictional examples only.
- Use no public hosted demo.
- Treat every remote model call as an external data transfer.
- Add no dependency or tool.
- Require legal review for OpenViking AGPLv3.
- Show `○` for suggestions.
- Show `✓` only after auditor confirmation.

Do not recommend a change to these boundaries without a separate decision request.

## Research Method

Use current official repositories, documentation, licence files and release records.

Record the URL, version, commit or release, access date and supported claim.

Mark source-code inferences as inferences. Separate confirmed facts from assumptions.

Do not rely on a marketing page when code or product documentation answers the question.

Do not run, install, clone or deploy either product.

Do not create an account or send test content to a service.

## Sift-KG Questions

Confirm or refute these points:

1. How does Sift-KG accept source content?
2. Which model, embedding and storage services can receive source content?
3. Which components can run locally?
4. What raw extraction result can ACE import?
5. Does each candidate keep exact source locations?
6. What does a graph merge change?
7. Can ACE export raw results without accepting graph merges?
8. Which files, databases, caches, logs and indexes store source content?
9. How can one Engagement use a separate namespace or store?
10. How can the operator delete one Engagement without changing another?
11. Which telemetry, training, retention and subprocess rules apply?
12. What licence and dependency duties need review?

Map confirmed outputs to the provider-neutral extraction boundary.

Report each mapping gap. Do not invent a missing field.

## OpenViking Questions

Confirm or refute these points:

1. What context-search interfaces does OpenViking provide?
2. Which source types and source locations does it retain?
3. Which model, embedding and storage services can receive source content?
4. Which components can run locally?
5. How can session memory be disabled?
6. Can configuration and run evidence prove that memory stayed disabled?
7. Which stores hold session, context, index, cache and log data?
8. How can one Engagement use a separate namespace or store?
9. How can the operator delete one Engagement without changing another?
10. Can results return stable source identifiers and exact source locations?
11. Which telemetry, training, retention and subprocess rules apply?
12. What does AGPLv3 require for the proposed use?
13. Which legal questions remain for changes, network access and distribution?

Do not give a legal conclusion. Prepare questions for qualified legal review.

If session memory cannot be disabled, mark the first pilot as blocked.

## Architecture Review

Review this logical flow:

```text
Mobile or web client
      -> ACE API
      -> ACE provider adapter
      -> Sift-KG extraction or OpenViking context search
      -> unapproved provider result
      -> ACE workbench
      -> auditor decision where applicable
```

Confirm that provider credentials stay on the ACE server side.

Confirm that no provider can write an approved ACE record.

Confirm that Sift-KG and OpenViking can use separate pilot stores.

Identify any feature that would break these boundaries.

## Privacy And Data-Transfer Review

Create one data-flow table for each candidate.

For each step, record:

- data sent;
- source and destination;
- local or remote status;
- provider and subprocess provider;
- storage location;
- retention;
- logging and telemetry;
- training use;
- deletion control; and
- evidence gap.

Treat model, embedding, reranking, telemetry and hosted storage calls as transfers.

Use fictional data in all examples.

## Provenance Review

Check whether each candidate can preserve:

- Engagement identifier;
- source identifier and version;
- exact source location;
- source and selected-text hashes;
- provider, model and configuration versions;
- run identifier and time;
- raw output hash; and
- external-transfer status.

Classify each field as native, derivable, adapter-supplied or unavailable.

## Isolation And Deletion Review

Design two fictional Engagement tests with similar terms.

For each candidate, list every store that the deletion test must inspect.

Show how the test proves these results:

- Engagement A data is absent after deletion.
- Engagement B data remains complete.
- A queries return no deleted content.
- B queries return no A content.
- caches, sessions, logs and backups have a stated result.

Report any store that has no supported deletion method.

## Required Report

Return one Markdown report with these sections:

1. Executive Summary.
2. Evidence And Versions.
3. Sift-KG Findings.
4. OpenViking Findings.
5. Provider-Neutral Boundary Review.
6. Data-Transfer Maps.
7. Provenance Field Matrix.
8. Engagement Isolation Design.
9. Deletion Test Design.
10. Licence Facts And Legal Questions.
11. Open Decisions.
12. Pilot Readiness.
13. Recommended Next Action.

For each material claim, cite current official evidence.

Use `confirmed`, `inferred`, `unknown` or `conflict` for each finding.

Give Sift-KG and OpenViking separate readiness results.

Use `ready for specification`, `needs decision` or `blocked`.

## Acceptance Criteria

- The report keeps ACE and auditor authority unchanged.
- The report treats all Sift-KG outputs as proposals.
- The report treats OpenViking output as context only.
- The report proves or blocks disabled OpenViking session memory.
- The report identifies all known external transfers.
- The report maps provenance, isolation and deletion controls.
- The report separates product facts from legal questions.
- The report uses only official evidence for material technical claims.
- The report makes no implementation change.

## Stop Conditions

Stop and report the issue before:

- requesting or receiving real client information;
- uploading the repository;
- using a public hosted demo;
- installing or running a tool;
- making a remote model call with supplied content;
- creating an account or deployment;
- giving a legal conclusion;
- changing an architecture or security boundary; or
- starting implementation.

## Local Acceptance

Codex must inspect the returned report and all citations.

The auditor must decide all method and approval questions.

Legal must decide the OpenViking AGPLv3 questions.

The user must approve any later tool, dependency, transfer path or implementation task.
