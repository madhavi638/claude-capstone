# Code Review Notes

Ticket: HMS-6

## Summary

Reviewed the Phase 6 implementation (`source_code/backend/**`, `database/migrations/005_*.sql`,
`database/schema.sql`) against `artifacts/implementation/HMS-6-impl-manifest.md`,
`artifacts/implementation/HMS-6-implementation-log.md`, `artifacts/architecture/HMS-6-design-spec.md`,
and the ADR. Code quality review and security scan were performed in parallel per the agent
workflow. The layered architecture (router → service → repository → PostgreSQL), the outbox
pattern, and the state-machine module are all implemented as specified and match their respective
design artifacts. However, the review surfaced **two business-rule violations** — one of them an
explicit, line-numbered step in the design spec's own data-flow description that the
implementation omits — plus several lower-severity gaps. No code was modified as part of this
review, per this agent's validation rules.

## Overall Result
**APPROVED WITH CHANGES**

## Code Quality Issues

1. **(Medium)** `appointment_router.py` catches the built-in `ValueError` to map to `404 Not Found`
   (`get_appointment`, `reschedule_appointment`, `cancel_appointment`, `get_appointment_history`).
   Every other domain failure in this codebase has a dedicated exception
   (`SlotConflictError`, `AuthorizationError`, `InvalidStatusTransitionError` in
   `backend/domain/errors.py`), but "not found" reuses a generic built-in. This is fragile: any
   unrelated `ValueError` raised deeper in the call stack (e.g., a future validation bug) would be
   silently mapped to a `404` instead of surfacing as a real error. Recommend adding a
   `NotFoundError` to `backend/domain/errors.py` and raising that instead of the bare `ValueError`
   in `AppointmentRepository`/`AppointmentService`.

2. **(Low)** `AppointmentService._authorize_read` is used to gate both read *and* write operations
   (`reschedule_appointment`, `cancel_appointment`, `change_status` all call it). The name implies
   read-only scope, which is misleading — and, as detailed under Compliance Issues below, using
   the same rule for both is also a functional bug, not just a naming issue.

3. **(Low)** `AppointmentRepository.reschedule()` writes a status-history row with
   `from_status == to_status` (both set to the appointment's unchanged status) to record the
   reschedule event. This works but overloads a column pair whose name implies a status
   transition for an event that isn't one. Consider a distinct `event` marker or at least a code
   comment explaining the convention (there isn't one currently).

## Security Issues

1. **(High — pre-existing, tracked, not a new finding)** `backend/auth/principal.py` trusts a
   client-supplied, unsigned `role` claim (`Bearer <user_id>:<role>`) with no signature
   verification. This was already identified and accepted as a High risk in
   `artifacts/review/HMS-6-design-review.md` and tracked as TASK-003's explicit stub scope — flagged
   here again only because it compounds finding #2 under Compliance Issues: since `role` is
   self-asserted, the `provider`-role write-access gap below is trivially exploitable by anyone who
   can set an HTTP header, not just a legitimate provider.
2. No SQL injection surface found — all queries go through the SQLAlchemy ORM/query builder with
   bound parameters; no raw string-interpolated SQL exists anywhere in `source_code/backend`.
3. No secrets are logged or returned in API responses.

## Performance Issues

None found. Listing queries are paginated (`DEFAULT_PAGE_SIZE=20`, `MAX_PAGE_SIZE=100`) and the
`status_history` relationship is deliberately not eager-loaded on `Appointment`, keeping list
queries lean per FR-020 as documented in `models/appointment.py`.

## Maintainability Issues

1. **(Medium)** `NotificationDispatcher.run_once()` (`backend/notifications/dispatcher.py`) selects
   all `PENDING` rows and processes them with no row-locking (e.g. `SELECT ... FOR UPDATE SKIP
   LOCKED`) and no other concurrency guard. If more than one dispatcher instance/worker ever runs
   `run_once()` concurrently — plausible in a real deployment (cron overlap, multiple workers) —
   the same row could be attempted and delivered twice. Not exercised by the current single-process
   test suite, so it wasn't caught there; call out for whoever wires up the real scheduling.
2. **(Low)** The reschedule notification payload (`AppointmentService.reschedule_appointment`) is
   `{"appointment_id": str(updated.id)}` — it omits the new `start_time`/`end_time`, unlike what a
   reschedule notification would actually need to tell the patient/provider. The booking and cancel
   payloads are similarly minimal. Consider enriching payloads before wiring a real notification
   channel (tracked already as a non-blocking follow-up per the Phase 5 manifest, but worth
   reiterating here since it affects FR-021 usefulness, not just delivery mechanics).

## Compliance Issues

1. **(Critical)** `AppointmentService.reschedule_appointment` does not check the appointment's
   current status before rescheduling. `artifacts/architecture/HMS-6-design-spec.md` (Data Flow,
   step 2) explicitly specifies: *"service verifies current status is reschedulable (not
   `CANCELLED`/`COMPLETED`, BR-011) → validates new slot free → updates row + appends history"*.
   The implementation skips that verification entirely and calls
   `self.repository.reschedule(...)` directly after only an ownership/authorization check — no call
   to `validate_transition` or any other guard exists in this method. As written, a `CANCELLED`,
   `COMPLETED`, or `NO_SHOW` appointment can still have its `start_time`/`end_time` silently
   changed via `PATCH /appointments/{id}/reschedule`, while its `status` stays terminal — directly
   violating BR-011 (*"A cancelled or completed appointment cannot be rescheduled; a new
   appointment must be created instead"*) and the design spec's own documented flow for this
   endpoint.
2. **(High)** BR-010 states: *"Only authorized roles (patient for their own appointments;
   staff/admin for any) may book/reschedule/cancel appointments."* — `provider` is not listed as an
   authorized actor for any of these three write operations. The implementation does not enforce
   this:
   - `book_appointment` only restricts the `patient` role (`principal.role == "patient" and
     patient_id != principal.user_id`); a `provider`-role principal can book an appointment for
     *any* patient/provider pair with no restriction at all.
   - `reschedule_appointment` and `cancel_appointment` both gate through `_authorize_read`, which
     grants a `provider` principal access whenever `appointment.provider_id == principal.user_id`
     — i.e., providers can reschedule/cancel their own appointments, which BR-010 does not
     authorize.
   Recommend a dedicated write-authorization check (distinct from `_authorize_read`) that permits
   only `staff` (any appointment) and `patient` (own appointment only) for `book_appointment`,
   `reschedule_appointment`, `cancel_appointment`, and `change_status`.
3. **(Medium)** Neither `AppointmentCreateRequest` nor `AppointmentRescheduleRequest`
   (`backend/schemas/appointment.py`) nor the service/repository layer validates that
   `start_time < end_time`. Nothing in the reviewed requirements/design artifacts explicitly names
   this as a numbered BR/FR, but it is implied by "appointment" as a concept and is worth a
   defensive check before this reaches a real client — a negative- or zero-duration appointment
   should never be persisted.

## Testing Gaps

1. No test exercises rescheduling a `CANCELLED`, `COMPLETED`, or `NO_SHOW` appointment — this gap
   is exactly why Compliance Issue #1 (BR-011) was not caught by the existing suite.
2. No test exercises a `provider`-role principal calling `book_appointment` for a patient/provider
   pair it does not own — this gap is why Compliance Issue #2's booking half was not caught.
3. No test asserts that a `provider`-role principal is *rejected* when calling
   `reschedule_appointment`/`cancel_appointment` on its own appointment (the existing
   `test_provider_cannot_access_other_providers_appointment` test only covers reading a
   *different* provider's appointment, not writing to its own) — this gap is why Compliance Issue
   #2's reschedule/cancel half was not caught.
4. No test asserts rejection of a malformed time range (`start_time >= end_time`) at either the
   schema or service layer.
5. As previously reported in the Phase 6 implementation log, the 19 integration tests that do exist
   are written and statically verified to import cleanly but have not been executed against a live
   Postgres in this environment — this review's findings above were identified by static reading of
   the code and cross-referencing against the design spec/business rules, not by running the suite.

## Recommendations

1. Add the BR-011 status check to `AppointmentService.reschedule_appointment` (e.g. reuse
   `validate_transition`-style logic, or a dedicated `is_reschedulable(status)` guard) before
   calling the repository, matching the design spec's documented flow.
2. Replace the shared `_authorize_read` gate on write paths with a dedicated write-authorization
   check that reflects BR-010's actual role matrix (staff: any; patient: own only; provider: none
   of book/reschedule/cancel).
3. Add `start_time < end_time` validation, most cheaply as a Pydantic model validator on
   `AppointmentCreateRequest`/`AppointmentRescheduleRequest` so it's rejected at the API boundary
   with `422` before reaching the service layer.
4. Introduce a `NotFoundError` domain exception to replace the bare `ValueError` currently used for
   "not found" across the repository/service/router.
5. Add the four missing test cases named above once the corresponding fixes land, so each fix has
   a regression test.
6. Note the dispatcher concurrency gap for whoever schedules `NotificationDispatcher.run_once()` in
   production; a `SELECT ... FOR UPDATE SKIP LOCKED` (or a single-worker deployment constraint)
   would close it if multiple workers are ever run.

## Action Items

- [x] Fix BR-011 enforcement gap in `reschedule_appointment` (Critical)
- [x] Fix BR-010 role-authorization gap in `book_appointment`/`reschedule_appointment`/`cancel_appointment` (High)
- [x] Add `start_time < end_time` validation (Medium)
- [x] Replace bare `ValueError` with a dedicated `NotFoundError` (Medium)
- [x] Document/mitigate the notification-dispatcher concurrency gap (Medium)
- [ ] Add the five test cases identified under Testing Gaps (partial — see Remediation Addendum)

## Remediation Addendum (post-review)

All Critical/High/Medium code findings above were fixed in `source_code/backend`
(confirmed by re-reading each file, not assumed from the manifest):

- **BR-011 (Critical):** `AppointmentService.reschedule_appointment` now checks
  `current_status` against `NOT_RESCHEDULABLE_STATUSES` (`CANCELLED`, `COMPLETED`)
  and raises `InvalidStatusTransitionError` before calling the repository,
  matching the design spec's documented data flow.
- **BR-010 (High):** The shared `_authorize_read` write-path gate was replaced
  with two dedicated checks — `_authorize_write_new` (book: staff any, patient
  own only, provider none) and `_authorize_write_existing` (reschedule/cancel:
  staff any, patient own only, provider none). `_authorize_read` is now used
  only for read paths (`get_appointment`, `get_history`), matching the earlier
  naming complaint's resolution too.
- **Medium — time-range validation:** `AppointmentCreateRequest` and
  `AppointmentRescheduleRequest` (`backend/schemas/appointment.py`) both gained
  a `model_validator` rejecting `start_time >= end_time` at the API boundary
  (`422`).
- **Medium — `NotFoundError`:** `backend/domain/errors.py` now defines
  `NotFoundError`; the repository, service, and router all raise/catch it
  instead of a bare `ValueError`.
- **Medium — dispatcher concurrency:** `NotificationDispatcher.run_once()` now
  selects pending rows with `SELECT ... FOR UPDATE SKIP LOCKED`, closing the
  double-delivery gap for concurrent workers.

**Regression tests added** to `tests/integration/test_appointment_service.py`
for the two highest-severity findings (Testing Gaps #1–#3):
`test_reschedule_cancelled_appointment_is_rejected`,
`test_reschedule_completed_appointment_is_rejected`,
`test_provider_cannot_book_appointment`,
`test_provider_cannot_reschedule_own_appointment`,
`test_provider_cannot_cancel_own_appointment`. Testing Gap #4 (malformed
time-range rejection test) was not added in this pass — tracked as a residual
follow-up, not blocking, since the validator itself is unit-testable and the
fix is already enforced at the schema layer.

**Verification status:** Unit tests re-run and pass (44/44). The updated
integration test file collects/imports cleanly (`pytest --collect-only`), but
— as previously reported for Phase 6 — could **not** be executed against a
live Postgres in this sandbox: no Docker is installed, and the only reachable
Postgres on `localhost:5432` is an unrelated instance whose credentials don't
match this project's (`password authentication failed for user
"hms6_user"`), left untouched and out of scope. Reported transparently rather
than claimed as run.

**Revised Result: APPROVED.** The Critical and High compliance findings that
blocked progression are remediated and confirmed present in the code. Medium
code-quality/maintainability items are also resolved. Residual: one Testing
Gap (malformed time-range test) and the pre-existing High auth-stub risk
(tracked since Phase 4/TASK-003, unchanged) carry forward as non-blocking
follow-ups.
