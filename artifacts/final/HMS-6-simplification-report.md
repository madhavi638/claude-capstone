# Simplification Report: HMS-6 - Appointment Scheduling Feature

## Ticket: HMS-6

## Scope and Method

Per `.claude/agents/SDLC Simplify Agent.agent.md`, this phase reviewed every backend
source file (`source_code/backend/**`) for duplication, long methods, excessive
nesting, dead code, unused imports, poor naming, repeated queries, repeated API
logic, and error-handling consistency. Only behavior-preserving refactors were
applied: no business rule changed, no architecture redesigned, no feature added,
and all API/DB contracts and security controls (authorization checks, state-machine
enforcement, DB exclusion constraint) are untouched.

## Refactors Applied

### 1. `repositories/appointment_repository.py` — collapsed duplicate list methods

`list_for_patient` and `list_for_provider` were identical except for which column
they filtered on (`patient_id` vs `provider_id`). Extracted a private
`_list_by_owner(owner_column, owner_id, status_filter, offset, limit)` helper; both
public methods are now one-line wrappers with unchanged signatures, return types,
and query semantics (same filter, ordering, offset/limit).

### 2. `services/appointment_service.py` — extracted two repeated patterns

- **Fetch-or-404**: `get_by_id(...)` followed by `if appointment is None: raise
  NotFoundError(...)` was duplicated identically in `get_appointment`,
  `reschedule_appointment`, `cancel_appointment`, `change_status`, and
  `get_history` (5 call sites). Extracted `_get_or_404(appointment_id)`.
- **Enqueue-then-commit**: every mutating method (`book_appointment`,
  `reschedule_appointment`, `cancel_appointment`, `change_status`) called
  `enqueue(self.db, appointment_id=..., event_type=..., payload=...)` immediately
  followed by `self.db.commit()`. Extracted `_enqueue_and_commit(appointment_id,
  event_type, payload)`. Call order, arguments, and the single-commit-per-operation
  transaction boundary (self-identified during Phase 6, load-bearing for the
  outbox pattern) are unchanged.

Net effect: `appointment_service.py` shrank from 197 to 185 lines while removing
five duplicated 3-line blocks and four duplicated 6-line blocks.

### 3. `routers/appointment_router.py` — consolidated exception-to-HTTP mapping

Five of six endpoints repeated the same shape: catch a subset of
`{SlotConflictError, InvalidStatusTransitionError, AuthorizationError,
NotFoundError}` and raise `HTTPException(status_code=<fixed code>,
detail=str(exc))` for each, near-verbatim, 15 times total across the file.
Extracted a module-level `_ERROR_STATUS_MAP` (exception type -> HTTP status) and a
`_as_http_error(exc)` helper. Each endpoint's `except` clause now names exactly the
same exception types it caught before (no endpoint gained or lost a caught type)
and calls the shared helper. Status codes returned for every exception type are
unchanged: `SlotConflictError`/`InvalidStatusTransitionError` -> 409,
`AuthorizationError` -> 403, `NotFoundError` -> 404.

### 4. `repositories/appointment_repository.py` — clarifying comment (no behavior change)

`reschedule()` writes a history row with `from_status == to_status` (the unchanged
status recorded on both sides). This was flagged as a Low-severity code-review
observation (Phase 7) recommending the convention be documented. Added a one-line
comment explaining it is an intentional audit-event marker for NFR-018, not a
defect. No code path changed.

## Explicitly Left Alone

- **Auth stub** (`backend/auth/principal.py`) — pre-production placeholder, tracked
  as a High risk since Phase 4/TASK-003. Not in scope for simplification; changing
  it would be a feature/architecture change, not a refactor.
- **FR-020 date-range filtering gap** and **FR-021/BR-013 notification-delivery
  stub** — both are missing functionality, not simplification targets; adding them
  would violate the "do not introduce new features" rule for this phase.
- **`reschedule()`'s from_status==to_status pattern itself** — only documented, not
  changed, since altering it would change what's written to the audit trail
  (NFR-018), a business-behavior change out of scope here.
- Router/service/repository method signatures, response shapes, and status codes —
  all preserved exactly to protect the already-open PR's contract.

## Validation

- **Unit tests: 44/44 pass**, re-run after all refactors (`pytest tests/unit -q`).
- **Integration tests: 26 collected, 0 collection errors** (`pytest
  tests/integration --collect-only -q`) — confirms the refactored service/router
  still import cleanly and the test suite's expectations of their public
  interfaces are unbroken. Execution against a live database remains blocked in
  this sandbox (no Docker; local Postgres:5432 belongs to an unrelated project),
  consistent with every prior phase.

## Files Changed

- `source_code/backend/repositories/appointment_repository.py`
- `source_code/backend/services/appointment_service.py`
- `source_code/backend/routers/appointment_router.py`

## Final Status

**SIMPLIFICATION COMPLETE.** All identified duplication hotspots were reduced
without altering business behavior, API contracts, database contracts, or
security controls. No regressions in the 44 executable unit tests.
