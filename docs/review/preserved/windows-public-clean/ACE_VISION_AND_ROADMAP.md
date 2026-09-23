# SQE Platform Vision And Roadmap

## Purpose

SQE Platform helps an accountable auditor review controlled safety information.
It keeps evidence, decisions, limits, and approval history visible.

## North Star

The platform must give the auditor a clear, traceable basis for each decision.
Automation can organise information. It cannot approve professional decisions.

## Delivery Order

See the [Developer Roadmap](DEVELOPER_ROADMAP.md) for the whole capability map, current work, dependencies, code locations, and evidence links.
Open the [Development Hub](SQE_DEVELOPER_HUB.html) for Whole Picture, Development State, Milestones, and Evidence And Updates.

1. Keep G0 and decision controls active.
2. Maintain the controlled web workbench and release boundaries.
3. Keep the iOS client read-only and provider-isolated.
4. Use only approved fictional-data pilots for future retrieval tools.
5. Add new capabilities only after a separate approved specification.

## Decision Gates

Do not use client data without an approved data boundary.
Do not deploy to Production without separate approval.
Do not add an external provider, schema change, or security boundary without approval.

## Current Evidence — 9 September 2026

MCX19-A is Done at 3259048186916941bf3557d55503e7375e432c57. The M4 run finished in 7m 54s: three native tests passed, none failed or skipped, and no accessibility issues were reported.
UNVERIFIED — UI QA INCOMPLETE: screenshots, dark mode, large Dynamic Type, and normal device-setting behaviour remain unverified for this candidate.
Next: MCX19-B full candidate verification, then MCX19-C readiness review. G0 remains in force.
See the [M4 Native Run Report](../Codex/2026-09-08/mcx19-functional-accessibility/M4-NATIVE-RUN.md) and [Developer Roadmap](DEVELOPER_ROADMAP.md).
