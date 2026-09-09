# Requirement Coverage Matrix

## Ticket: HMS-6

## Summary

Traced every FR/NFR/BR named in `artifacts/requirements/HMS-6-problem-spec.md` to its
implementation in `source_code/backend/**` and its test in `tests/**`, cross-checked against
`artifacts/implementation/HMS-6-implementation-log.md`, `artifacts/implementation/HMS-6-impl-manifest.md`,
and `artifacts/review/HMS-6-review-notes.md` (including its post-review Remediation Addendum). No
code or tests were modified as part of this verification — validation and reporting only.

11 of 15 requirements are fully covered by both implementation and a written test. 4 are partially
covered — three (FR-020, NFR-001, part of FR-021/BR-013) by design/scope, one because of this
sandbox's inability to run the integration suite against a live database. No requirement is
entirely missing.

## Traceability Matrix

| Requirement ID | Requirement Description | Implementation Status | Test Coverage | Overall Status | Notes |
|---|---|---|---|---|---|
| FR-016 | Appointment booking | Done — `AppointmentService.book_appointment`, `POST /api/v1/appointments` | `test_patient_can_book_own_appointment`, `test_book_appointment_happy_path`, `test_double_booking_*` | Full | Written tests not executed live (see Regression Risks) |
| FR-017 | Appointment rescheduling | Done — `reschedule_appointment`, `PATCH /appointments/{id}/reschedule`, BR-011 guard | `test_reschedule_and_cancel_each_enqueue_one_notification`, `test_reschedule_cancelled_appointment_is_rejected`, `test_reschedule_completed_appointment_is_rejected` | Full | Regression tests added post Phase-7 remediation |
| FR-018 | Appointment cancellation | Done — `cancel_appointment`, `POST /appointments/{id}/cancel`, reason captured | `test_cancel_then_complete_is_rejected_by_state_machine`, `test_reschedule_and_cancel_each_enqueue_one_notification` | Full | |
| FR-019 | Status lifecycle | Done — `appointment_state_machine.py` transition table + `change_status` | `tests/unit/test_state_machine.py` (39/39, **executed**), `test_cancel_then_complete_is_rejected_by_state_machine` | Full | Only requirement whose tests actually ran (DB-free unit tests) |
| FR-020 | Visibility by role/date range/status | Partial — role-scoped listing (`list_for_patient`/`list_for_provider`) and status filter exist; **no date-range query parameter anywhere in the router/service/repository** | `test_patient_forbidden_from_listing_other_patient`, `test_provider_cannot_access_other_providers_appointment`, `test_listing_*` | **Partial** | Date-range filtering named explicitly in the requirement text but not implemented; confirmed missing by grep across `source_code/backend` |
| FR-021 | Stakeholder notifications | Partial — durable outbox enqueue on book/reschedule/cancel is complete; `NotificationDispatcher._default_send` is an explicit placeholder returning `False` (no real email/SMS/push channel wired) | `test_enqueue_is_durable_within_same_transaction`, `test_dispatcher_marks_sent_on_successful_delivery` (with injected `send_fn`), `test_dispatcher_marks_failed_after_max_attempts` | **Partial** | Documented as intentional in `dispatcher.py`; matches the problem spec's own Constraints section ("notification mechanism... not yet confirmed") |
| NFR-001 | Performance under load | Partial — paginated listing (`DEFAULT_PAGE_SIZE=20`/`MAX=100`), no eager-loading of `status_history` | None (no load/perf test exists) | **Partial** | Structural choices support the NFR; no measurement was ever taken to confirm it's met |
| NFR-002 | Availability/reliability (notification failure must not block booking) | Done — outbox `enqueue()` only flushes; dispatcher delivery is a separate, decoupled step; booking commits regardless of delivery outcome | `test_enqueue_is_durable_within_same_transaction` | Full | |
| NFR-014 | No double-booking under concurrency | Done — DB-level `excl_appointments_no_overlap` EXCLUDE constraint (`database/schema.sql:53-58`), safe under concurrent transactions (not app-level check-then-act) | `test_overlapping_active_booking_raises_slot_conflict`, `test_double_booking_same_provider_raises_conflict`, `test_double_booking_returns_409` | Full | Constraint-based design is correct even for true concurrent race conditions |
| NFR-018 | Auditability of lifecycle transitions | Done — append-only `appointment_status_history` (actor_id + changed_at on every row) | `test_create_writes_history_row`, `test_update_status_writes_history_row` | Full | |
| BR-009 | No double-booking same provider/slot | Done — same EXCLUDE constraint as NFR-014 | Same as NFR-014 | Full | |
| BR-010 | Only patient(own)/staff(any) may book/reschedule/cancel; provider may not | Done — `_authorize_write_new` + `_authorize_write_existing`, distinct from the read-authorization gate | `test_patient_cannot_book_for_another_patient`, `test_provider_cannot_book_appointment`, `test_provider_cannot_reschedule_own_appointment`, `test_provider_cannot_cancel_own_appointment` | Full | Was the Phase 7 **High** finding; fixed and now regression-tested |
| BR-011 | Cancelled/completed appointment cannot be rescheduled | Done — `NOT_RESCHEDULABLE_STATUSES` check in `reschedule_appointment` | `test_reschedule_cancelled_appointment_is_rejected`, `test_reschedule_completed_appointment_is_rejected` | Full | Was the Phase 7 **Critical** finding; fixed and now regression-tested |
| BR-012 | Status transitions follow the defined state machine only | Done — single authoritative `TRANSITIONS` table, enforced in `change_status`/`cancel_appointment` | `tests/unit/test_state_machine.py` (39/39, executed) | Full | |
| BR-013 | Patient + assigned provider notified on any change | Partial — same outbox/dispatcher gap as FR-021 | Same as FR-021 | **Partial** | |

## Fully Covered Requirements

FR-016, FR-017, FR-018, FR-019, NFR-002, NFR-014, NFR-018, BR-009, BR-010, BR-011, BR-012

## Partially Covered Requirements

- **FR-020** — role/status filtering implemented; date-range filtering (explicitly named in the
  requirement) is not. Not flagged in any prior phase artifact — this is a new gap identified
  during verification.
- **FR-021 / BR-013** — durable enqueue mechanism complete; actual delivery channel to
  patient/provider is an explicit stub (`_default_send` always returns `False`), consistent with
  the problem spec's own Constraints section. Also see Code Review Maintainability finding #2
  (reschedule notification payload omits new start/end time).
- **NFR-001** — supported structurally (pagination, no eager-loading) but never measured; no
  performance/load test exists in the suite.

## Missing Requirements

None. Every FR/NFR/BR referenced on the epic has at least a partial implementation.

## Missing Test Coverage

- Malformed time-range rejection (`start_time >= end_time`) — the validator exists
  (`backend/schemas/appointment.py`) and is enforced at both the Pydantic and DB (`chk_appointments_time_order`)
  layers, but no test exercises it. Already tracked as a non-blocking residual in the Phase 7
  Remediation Addendum (Testing Gap #4).
- No test for FR-020's date-range visibility, because the feature itself doesn't exist (see
  Partial Requirements above) — not a test gap so much as a feature gap.
- No performance/load test for NFR-001.
- No test exercises the real notification-delivery channel for FR-021/BR-013, because no real
  channel exists yet to test against.

## Regression Risks

- **Environment blocker (carried through Phases 6 and 7, unchanged):** all 24 integration tests
  (`tests/integration/**`) are statically verified to collect/import cleanly (`pytest --collect-only`
  succeeds) but have never been executed against a live Postgres in this sandbox. No Docker is
  installed, and the only reachable Postgres on `localhost:5432` is an unrelated instance —
  connecting fails with `password authentication failed for user "hms6_user"`, confirmed again
  during this phase. **This means the state of "tests pass" for anything beyond the 44 unit tests
  is asserted by static/logical review, not by an actual test run.** This is the single largest
  regression risk in the ticket and should be resolved (spin up `database/docker-compose.yml`
  against real credentials) before this code is considered production-ready, independent of the
  PR/merge step in Phase 9.
- Unit tests (44/44, DB-free: state machine + auth stub) were re-executed in this verification pass
  and pass, confirming no regression from the Phase 7 remediation changes.
- The pre-existing High-risk auth stub (`backend/auth/principal.py`, unsigned client-supplied role
  claim) remains unchanged since Phase 4/TASK-003 — not a regression, but still an open risk that
  BR-010's enforcement is only as trustworthy as the identity layer beneath it.

## Final Verification Status

**PASS WITH RISKS**

All in-scope FR/NFR/BR items have at least partial coverage, the two Phase 7 blocking findings
(BR-011 Critical, BR-010 High) are fixed and regression-tested, and all 44 executable (unit) tests
pass. The "risks" qualifier reflects: (1) the integration suite has never run against a live
database in this environment, (2) FR-020's date-range filtering is unimplemented, and (3)
FR-021/BR-013's actual notification delivery is a stub pending a real channel — all three are
pre-existing/scope-boundary conditions rather than new defects introduced in this phase.
