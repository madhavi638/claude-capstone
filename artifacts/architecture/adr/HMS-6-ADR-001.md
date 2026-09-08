# ADR-001

## Title

Enforce provider slot exclusivity at the database layer using a uniqueness/exclusion constraint

## Status

Proposed

## Context

BR-009 requires that an appointment cannot be booked into a slot already occupied by another
active appointment for the same provider, and NFR-014 requires this to hold under concurrent
booking attempts. An application-layer "check-then-insert" approach (query for conflicts, then
insert if none found) is subject to a race condition: two concurrent requests can both pass the
check before either commits, resulting in a double-booking.

## Decision

Enforce slot exclusivity as a **database-level constraint** on the `appointments` table —
either:
- a unique constraint on `(provider_id, start_time)` for rows in an active status set, or
- a range-exclusion constraint over `(provider_id, [start_time, end_time))` if appointments have
  variable duration and must not overlap.

The application layer still performs a pre-check for a fast, user-friendly error, but the
database constraint is the source of truth. A constraint violation on insert/update is caught by
the service layer and surfaced as `409 Conflict`, not a generic `500`.

## Consequences

- Guarantees no double-booking even under concurrent load, without introducing distributed locks
  or application-level mutexes (positive — directly satisfies NFR-014).
- Cancelling/completing an appointment must exclude it from the exclusivity constraint's active
  set (e.g., via a partial/filtered unique index scoped to active statuses), otherwise a
  cancelled appointment would permanently block its former slot (implementation detail for the
  Database Agent to handle correctly).
- Slightly increases complexity of the migration (partial index or exclusion constraint instead
  of a plain unique index) — acceptable tradeoff given the correctness requirement is critical
  priority (BR-009 traces to a Critical-priority epic).

## Date

2026-08-31
