# Field Evidence Capture Workflow

## Status

Approved for fictional implementation. G0 blocks client data.

## Purpose

The workflow creates one controlled Evidence Item from an approved source.

## Required Inputs

- Authenticated auditor session.
- Active Engagement.
- Available controlled evidence store.
- Fictional, public, or AuditCo-owned material.

## Actions

1. Show the active Engagement.
2. Capture or select one source item.
3. Validate the source type and size.
4. Create one Evidence ID with an idempotency key.
5. Store the source outside the repository.
6. Set the Evidence Item to `PENDING_REVIEW`.

## Controls

Capture does not approve evidence, relationships, or conclusions.
