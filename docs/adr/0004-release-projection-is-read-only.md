# ADR 0004: Release Projection Is Read-Only

## Status

Accepted.

## Decision

The client release projection reads immutable release snapshots.
It does not modify release data, approval data, or live work records.

## Consequences

The release service owns lifecycle validation and writes.
The projection stays transport-neutral and retains its existing response contract.
