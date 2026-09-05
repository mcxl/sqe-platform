# Relationship Review Workflow

## Status

Approved for fictional implementation. G0 blocks client data.

## Purpose

The auditor decides one current Relationship Version.

## Required Inputs

- Authenticated auditor session.
- Active Engagement and current Proposed Relationship.
- Linked records, source support, rationale, and version history.
- Visible gaps and contradictions.

## Actions

1. Show the highest risk waiting proposal first.
2. Show both records, relationship type, rationale, and source support.
3. The auditor saves a draft or records a decision.
4. Record `APPROVED`, `REJECTED`, or `CHANGES_REQUIRED` with a reason.
5. Create an Approved Relationship only after approval.

## Controls

An approval applies only to the displayed current version.
A change request creates no automatic replacement.
