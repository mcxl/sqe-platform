# ADR 0002: G0 Protects The Data Boundary

## Status

Accepted.

## Decision

G0 permits fictional, public, and AuditCo-owned test data only.
G0 blocks client data until an approved data boundary permits it.

## Consequences

The repository contains no client evidence, credentials, scan output, or local environment files.
Work stops when a task needs data outside this boundary.
