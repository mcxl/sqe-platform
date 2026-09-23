# Mobile Field Capture Workbench Specification

## Problem Statement

The auditor needs a private workbench that works on an iPhone during site work.
The first build must capture a fictional photo or scanned page, give it an
evidence ID, show it on the laptop workbench and allow auditor review.

The client has not accepted the review. Real client evidence is out of scope.

## Solution

Extend the local FastAPI ACE application with a responsive auditor workbench.
Use private Wi-Fi for the first phone path. Store original media and SQLite
records in a sibling `sqe-local-data` folder outside the source workspace.

Show a large Capture Evidence action, a small progress guide, recent captures
and pending review items. Require one local auditor account before opening the
workbench.

## User Stories

1. As an auditor, I want to open the workbench in iPhone Safari, so that I can
   work during a site visit.
2. As an auditor, I want one large capture action, so that I can take a photo
   or scan a page quickly.
3. As an auditor, I want the capture to receive an evidence ID, so that I can
   refer to it in the review.
4. As an auditor, I want the original media stored outside the source folder,
   so that evidence does not enter the code repository.
5. As an auditor, I want to see the captured item on the laptop, so that I can
   review the same record after capture.
6. As an auditor, I want to mark an item reviewed, so that its status is clear.
7. As an auditor, I want to see captured, pending and reviewed counts, so that
   I know the next work action.
8. As an auditor, I want the first case to use fictional records, so that the
   build does not use client evidence.
9. As an auditor, I want the workbench to require a password, so that a phone
   on the private network does not give open access.

## Implementation Decisions

- Extend the existing FastAPI application. Do not create a separate React or
  native iPhone application for this slice.
- Serve one responsive workbench page from the ACE application.
- Use HTTP Basic authentication with username `auditor` and the
  `ACE_AUDITOR_PASSWORD` environment variable. Do not provide a default real
  password.
- Accept the first capture as a raw image request. Use the browser camera input
  with `capture="environment"`; document scan means clear page photos first.
- Create evidence IDs at capture time. Store original files below the external
  data directory. Store only metadata and the path in SQLite.
- Use SQLite tables for engagements, obligations, risks, controls, owners,
  evidence, relationships, reviews and audit events.
- Seed one fictional relationship chain:
  `Obligation -> Risk -> Control -> Owner -> Evidence -> MATE -> Conclusion`.
- New media starts as `PENDING_REVIEW`. A review action changes it to `REVIEWED`
  and records reviewer, time and notes. Review does not approve a conclusion.
- Keep the progress guide as a separate build roadmap. The mini guide reads
  live workbench counts.
- Do not implement hosted mode, offline protected drafts, audio, video, OCR,
  LangExtract, Neo4j, LangGraph, client access or Vorflux integration in this
  slice.

## Testing Decisions

- Test the public HTTP interface with FastAPI `TestClient`.
- Test unauthenticated workbench requests are rejected.
- Test the fictional chain and counts are visible after authentication.
- Test an image capture returns an evidence ID and stores the original below
  the configured external data directory.
- Test the captured item appears as pending review.
- Test the review action changes status and records the reviewer.
- Keep the existing evaluator and approval tests passing.

## Out Of Scope

- Real client evidence.
- Public hosting or public tunnels.
- Full authentication and user administration.
- Offline queue and protected phone storage.
- Audio recording, video recording, OCR and transcript processing.
- Automated extraction or approval.
- Graph database integration.
- Client-facing access.

## Further Notes

The next slice can add a protected offline queue after the online local path
works. The later workbench must keep candidate, reviewed, approved and rejected
states separate.
