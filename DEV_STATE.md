# Development State

## Controlled Branch

The current delivery branch is `codex/sqe-pivot-integration`.
Its baseline is the sanitised SQE Platform repository root.

## Current Controls

G0 blocks client data. Use fictional, public, or AuditCo-owned test data only.
The accountable auditor makes final decisions.

Do not run DeepSec without new approval and an approved isolation design.
Do not deploy to Production. Do not merge without separate approval.

## Verified Platform

The Python core records assessment, planning, review, and approval controls.
The web workbench records controlled evidence review work.
The iOS client source is a read-only, controlled snapshot.

The release service and release projection retain their approved ownership boundaries.
See [Approved Specifications](docs/specs/) and [Architecture Decisions](docs/adr/).

## Current Delivery Goal

The Platform Pivot prepares one protected integration branch for final review.
It does not change client data, Production, schema, queries, or evidence records.

## Source Of Truth

Code and approved specifications control when records differ.
Provider records, Linear, GitHub, and test outputs record delivery evidence.
Generated artefacts remain outside version control.
