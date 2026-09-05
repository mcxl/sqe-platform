# Evidence Review Workflow

## Status

Approved for fictional implementation. G0 blocks client data.

## Purpose

The auditor records source context and review status for one Evidence Item.

## Required Inputs

- Authenticated auditor session.
- Active Engagement and one Evidence Item.
- Original source or exact source reference.

## Actions

1. Show the Evidence ID, Engagement, and source reference.
2. Record provider, origin, date or version, location, and freshness.
3. Record limitations and Evidence Gaps.
4. Propose relevance to zero or more Audit Questions.
5. Set the item to `REVIEWED` after the auditor confirms the review.

## Controls

`REVIEWED` confirms inspection only. Relationship Review approves proposed links.
