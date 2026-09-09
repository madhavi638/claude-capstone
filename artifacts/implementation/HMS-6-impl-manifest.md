# Implementation Manifest — HMS-6 (Appointment Management)

**Source:** artifacts/architecture/HMS-6-design-spec.md, artifacts/architecture/adr/HMS-6-ADR-001.md,
artifacts/review/HMS-6-design-review.md, artifacts/database/HMS-6-database-design.md,
artifacts/database/HMS-6-orm-spec.md, database/schema.sql

## Executive Summary

This manifest decomposes the approved HMS-6 architecture (Phase 2, APPROVED) and design review
(Phase 4, APPROVED WITH CONCERNS) into 10 implementation-ready tasks. Per the design review's
Final Assessment, **Recommendations 1–4 are carried forward as explicit tasks** rather than left
as unresolved concerns: TASK-003 (auth contract), TASK-006 (durable notification outbox),
TASK-004 (explicit status transition table), and TASK-008 (pagination defaults) directly address
them. Recommendations 5–6 (placeholder table reconciliation; legacy-data-migration confirmation)
are carried as tracked items in **Blockers/Risks**, not implementation tasks, per the review's own
classification of them as follow-ups rather than blockers.

## Implementation Strategy

- Build bottom-up: session/config → models → cross-cutting concerns (auth stub, state machine,
  notification outbox) → repository → service → router → tests → docs.
- The database phase already produced `schema.sql` and migrations 001–004; this plan **adds one
  new additive migration (005)** for the notification outbox table, required by TASK-006. This is
  a direct, traceable consequence of Design Review Recommendation 2 (raised after the Database
  phase was approved) — not an unrelated schema change. It follows the same conventions
  (snake_case, UUID PK, `pgcrypto`) as migrations 001–004.
- No existing code, architecture, or approved schema is altered — only extended.
- Each task below is independently reviewable and individually testable.

## Task Breakdown

### TASK-001

**Name:** Database Session, Config & Migration Wiring

**Description:** Create the SQLAlchemy engine/session factory and app configuration (DB URL
sourced from environment variables, consistent with `database/docker-compose.yml`'s
`HMS6_DB_*` variables). Provide a FastAPI dependency (`get_db`) yielding a scoped session per
request. Document how migrations 001–005 are applied (via the existing Docker
`docker-entrypoint-initdb.d` mechanism for local dev, or manually against a pre-existing
Postgres instance) — no migration runner/ORM auto-create is introduced, consistent with the
Database Agent's non-responsibility for application code.

**Dependencies:** None (foundational).

**Deliverables:**
- `source_code/backend/database.py` (engine, `SessionLocal`, `get_db` dependency)
- `source_code/backend/config.py` (settings loaded from env)
- `configs/.env.example` (documents required DB env vars, mirrors `HMS6_DB_*` naming)

**Test Plan:** Unit test that `get_db` yields a session and closes it on teardown (using a test
SQLite or ephemeral Postgres fixture).

**Acceptance Validation:** App can open and cleanly close a DB session against a running
`hms6-postgres` container without connection leaks.

---

### TASK-002

**Name:** SQLAlchemy ORM Models

**Description:** Implement `Patient`, `Provider`, `Appointment`, and `AppointmentStatusHistory`
models exactly per `artifacts/database/HMS-6-orm-spec.md`'s Entity → Model Mapping and
Relationships sections, including the `AppointmentStatus` Python enum
(`SCHEDULED, CONFIRMED, IN_PROGRESS, COMPLETED, CANCELLED, NO_SHOW`) and the
`Appointment.status_history` relationship (non-eager-loaded by default, per FR-020 lean-listing
guidance).

**Dependencies:** TASK-001 (needs declarative base/engine).

**Deliverables:**
- `source_code/backend/models/patient.py`, `provider.py`, `appointment.py`,
  `appointment_status_history.py`
- `source_code/backend/models/enums.py` (`AppointmentStatus`)

**Test Plan:** Unit tests instantiating each model and asserting column/relationship mappings
match `schema.sql` column names and types.

**Acceptance Validation:** Models can be used to insert/query rows against the seeded
`hms6-postgres` database (`database/seed_data.sql`) without schema mismatch errors.

---

### TASK-003

**Name:** Auth Principal Contract & Role-Based Authorization Dependency

*(Addresses Design Review Recommendation 1 — High risk.)*

**Description:** Define a concrete, minimal `AuthPrincipal` contract (`user_id: UUID`,
`role: Literal["patient","provider","staff"]`) and a FastAPI dependency
(`get_current_principal`) that extracts it from the request (e.g. a bearer-token/header stub,
clearly marked as a placeholder for the real HMS identity module referenced in the design spec).
This unblocks concrete authorization scoping in TASK-007/TASK-008 instead of leaving it
undefined. Explicitly document that `actor_id` for `appointment_status_history` **must** be
derived server-side from this principal, never accepted as client input (per the design review's
Security Review finding).

**Dependencies:** None (independent of DB models; can run in parallel with TASK-001/002).

**Deliverables:**
- `source_code/backend/auth/principal.py` (`AuthPrincipal` model, `get_current_principal`
  dependency)
- Inline documentation flagging this as a stub pending the real identity module (tracked as a
  Risk below, not silently presented as production-ready).

**Test Plan:** Unit tests verifying the dependency rejects missing/malformed credentials and
correctly resolves `user_id`/`role` from a valid stub token.

**Acceptance Validation:** Any endpoint using `get_current_principal` returns 401 without
credentials and a populated `AuthPrincipal` with valid ones.

---

### TASK-004

**Name:** Appointment Status State Machine (Explicit Transition Table)

*(Addresses Design Review Recommendation 3 — Medium risk.)*

**Description:** Implement an explicit, enumerated transition table for BR-012, resolving the
ambiguity the design review flagged (e.g. whether `NO_SHOW` is reachable from `SCHEDULED` or only
from `CONFIRMED`). Proposed table, to be implemented as the authoritative source:

| From | Allowed To |
|---|---|
| `SCHEDULED` | `CONFIRMED`, `CANCELLED`, `NO_SHOW` |
| `CONFIRMED` | `IN_PROGRESS`, `CANCELLED`, `NO_SHOW` |
| `IN_PROGRESS` | `COMPLETED`, `CANCELLED` |
| `COMPLETED` | *(terminal — no transitions out)* |
| `CANCELLED` | *(terminal — no transitions out)* |
| `NO_SHOW` | *(terminal — no transitions out)* |

Any transition not in this table must raise a domain `InvalidStatusTransitionError`. This table
lives in the service layer per the ORM spec, not the model or database.

**Dependencies:** None (pure logic; can run in parallel with TASK-001–003).

**Deliverables:**
- `source_code/backend/domain/appointment_state_machine.py` (transition table + validator
  function)

**Test Plan:** Parametrized unit tests covering every legal transition (must succeed) and a
representative set of illegal transitions (must raise), including all terminal-state attempts.

**Acceptance Validation:** 100% of the transition table's legal/illegal pairs are covered by
passing tests.

---

### TASK-005

**Name:** AppointmentRepository

**Description:** Implement `AppointmentRepository` exposing exactly the methods specified in
`artifacts/database/HMS-6-orm-spec.md`'s Repository Expectations: `create`, `get_by_id`,
`list_for_patient`, `list_for_provider`, `update_status`, `reschedule`. Catch `IntegrityError`
from the `excl_appointments_no_overlap` constraint in `create`/`reschedule` and re-raise as a
domain `SlotConflictError` (never let it propagate as a generic 500). Every status-changing method
must write the corresponding `AppointmentStatusHistory` row in the same transaction (never a bare
`UPDATE` without history, per NFR-018).

**Dependencies:** TASK-002 (models), TASK-001 (session).

**Deliverables:**
- `source_code/backend/repositories/appointment_repository.py`
- `source_code/backend/domain/errors.py` (`SlotConflictError`)

**Test Plan:** Integration tests against a real Postgres instance (using
`database/docker-compose.yml`) that: (a) book two overlapping slots for the same provider and
assert the second raises `SlotConflictError`; (b) verify every status change produces exactly one
new history row; (c) verify cancelling and rebooking the same slot succeeds (exclusion is
correctly scoped to active statuses).

**Acceptance Validation:** All repository methods pass their integration tests against the
containerized database with no raw SQL outside this module.

---

### TASK-006

**Name:** Notification Outbox Migration + Durable Dispatcher

*(Addresses Design Review Recommendation 2 — High risk.)*

**Description:** Replace the design's originally-described "log-and-drop" async notification call
with a durable outbox pattern: an `appointment_notification_outbox` row is written in the **same
transaction** as the triggering appointment change (booking/reschedule/cancellation), and a
separate dispatcher worker polls/consumes the outbox, attempts delivery, and marks each row
`PENDING → SENT` or `PENDING → FAILED` with a retry count and backoff, never deleting a row on
failure. This guarantees BR-013 is actually satisfied (durable, retryable) rather than merely
attempted, while still not blocking the booking transaction on delivery (preserving NFR-002).

**Dependencies:** TASK-001, TASK-002 (needs session/base for the new table).

**Deliverables:**
- `database/migrations/005_create_appointment_notification_outbox.sql` (new additive migration:
  `id UUID PK`, `appointment_id UUID NOT NULL REFERENCES appointments`, `event_type TEXT`,
  `payload JSONB`, `status TEXT CHECK IN ('PENDING','SENT','FAILED')`, `attempt_count INT DEFAULT 0`,
  `created_at`, `last_attempted_at`, `delivered_at`)
- `source_code/backend/models/appointment_notification_outbox.py`
- `source_code/backend/notifications/dispatcher.py` (poll/retry/backoff worker)
- Update to `database/docker-compose.yml`'s init mount list is **not** required (init scripts run
  once from `schema.sql`; migration 005 is appended to `schema.sql` and to the migrations
  directory for consistency, following the same pattern as 001–004)

**Test Plan:** Unit tests for the dispatcher's retry/backoff logic (simulated delivery failures);
integration test confirming an outbox row is created in the same transaction as a booking and
survives even if the in-process notification call would have failed.

**Acceptance Validation:** No notification failure path results in a silently dropped BR-013
event — every outbox row reaches a terminal `SENT` state or is visibly `FAILED` with a retry count
for observability/alerting.

---

### TASK-007

**Name:** AppointmentService

**Description:** Implement `AppointmentService`, orchestrating booking, reschedule, cancellation,
and query operations. Uses TASK-004's state machine to validate every status change, TASK-005's
repository for persistence, TASK-006's outbox for notification side-effects, and TASK-003's
`AuthPrincipal` for authorization scoping (a `patient` role may only see/act on their own
appointments; `provider`/`staff` scoping per the design spec's assumption, flagged as an
assumption pending the real identity module).

**Dependencies:** TASK-003, TASK-004, TASK-005, TASK-006.

**Deliverables:**
- `source_code/backend/services/appointment_service.py`

**Test Plan:** Unit tests (repository/dispatcher mocked) covering: successful booking; booking
conflict → `SlotConflictError` surfaced; illegal status transition → `InvalidStatusTransitionError`
surfaced; authorization denial for cross-patient access; successful reschedule/cancel each
producing exactly one outbox event.

**Acceptance Validation:** Service methods never call the repository or dispatcher directly from
outside the state-machine/authorization checks — verified by test coverage on every branch.

---

### TASK-008

**Name:** FastAPI Appointment Router (with Pagination)

*(Pagination addresses Design Review Recommendation 4 — Medium risk.)*

**Description:** Implement the REST endpoints from the design spec: `POST /api/v1/appointments`,
`PATCH /api/v1/appointments/{id}/reschedule`, `POST /api/v1/appointments/{id}/cancel`,
`GET /api/v1/appointments` (patient/provider-scoped listing), `GET /api/v1/appointments/{id}`,
`GET /api/v1/appointments/{id}/history`. The listing endpoint must default to `page_size=20`,
`max page_size=100`, and reject larger requests with `422`, closing the design review's
unbounded-listing gap. `SlotConflictError` maps to `409`; `InvalidStatusTransitionError` maps to
`409`; authorization denial maps to `403`.

**Dependencies:** TASK-007.

**Deliverables:**
- `source_code/backend/routers/appointment_router.py`
- `source_code/backend/main.py` (FastAPI app wiring, router registration)

**Test Plan:** API-level integration tests (FastAPI `TestClient`) covering each endpoint's happy
path, the pagination boundary (page_size > 100 → 422), the 409 conflict path, and the 403
authorization-denial path.

**Acceptance Validation:** All endpoints from the design spec's API Design Approach section exist,
return the documented status codes, and listing never returns more than `max page_size` rows.

---

### TASK-009

**Name:** Automated Test Suite Consolidation

**Description:** Consolidate and ensure full execution of the unit/integration tests defined
across TASK-002 through TASK-008 (model mapping, state machine, repository conflict/audit
behavior, outbox durability, service authorization/orchestration, router contract/pagination) into
a single runnable suite with a documented command.

**Dependencies:** TASK-002, TASK-004, TASK-005, TASK-006, TASK-007, TASK-008.

**Deliverables:**
- `tests/` directory (unit + integration subfolders)
- `tests/README.md` (how to run: unit tests standalone; integration tests require
  `docker compose -f database/docker-compose.yml up`)

**Test Plan:** N/A (this task *is* the test plan for prior tasks); acceptance is a green run.

**Acceptance Validation:** `pytest` exits 0 for the full suite against a freshly provisioned
`hms6-postgres` container.

---

### TASK-010

**Name:** Implementation Log & API Documentation

**Description:** Produce the Implementation Execution Agent's required `implementation_log_template`
output summarizing what was built, and a brief API reference (endpoints, request/response shapes,
status codes) for the appointment module.

**Dependencies:** TASK-001 through TASK-009 (documents the completed implementation).

**Deliverables:**
- `artifacts/implementation/HMS-6-implementation-log.md`
- `docs/HMS-6-api-reference.md`

**Test Plan:** N/A (documentation task); reviewed for completeness against the actual endpoints
implemented in TASK-008.

**Acceptance Validation:** Every endpoint and status code in TASK-008 is documented; every task
TASK-001–009 is listed with its outcome.

## Dependency Graph

```
TASK-001 ──┬─> TASK-002 ──┬─> TASK-005 ──┐
           │              └─> TASK-006 ──┤
TASK-003 ──┼──────────────────────────────┼─> TASK-007 ─> TASK-008 ─> TASK-009 ─> TASK-010
TASK-004 ──┘                              │
                                          (TASK-005, TASK-006 also feed TASK-007 directly)
```

## Critical Path

`TASK-001 → TASK-002 → TASK-005 → TASK-007 → TASK-008 → TASK-009 → TASK-010`

TASK-003, TASK-004, and TASK-006 are off the longest chain but must all complete before TASK-007
starts — none may slip past TASK-007's start without blocking it.

## Blockers

- **TASK-003 depends on an auth contract that is a stub, not the real HMS identity module** (which
  does not exist in this workspace). This unblocks implementation but does not resolve the
  underlying integration risk — tracked in Risks below, and previously flagged in the design
  review as a High risk.
- Design Review Recommendation 5 (reconcile placeholder `patients`/`providers` tables with the
  real HMS modules) and Recommendation 6 (confirm legacy-data-migration/compliance scope with a
  business stakeholder) are **not** implementation tasks in this manifest — they require decisions
  outside engineering scope and are carried forward as tracked follow-ups, consistent with the
  design review's own classification of them as non-blocking.

## Risks

- **High:** TASK-003's auth stub, if not swapped for the real identity module before production
  deployment, leaves authorization permanently mocked. Must be tracked as a hard follow-up, not
  forgotten once the stub "works."
- **Medium:** TASK-006 introduces migration 005 after the Database phase was already approved.
  Scoped narrowly (one additive table, same conventions) and directly traceable to an approved
  design-review recommendation, but flagged here for visibility since it technically extends the
  Phase 3 database surface after that phase's approval.
- **Medium:** GiST exclusion-constraint write cost under concurrent load (design review's
  Scalability Review) is not addressed by any task above — recommend a follow-up load test after
  TASK-005 lands, not blocking initial implementation.
- **Low:** Placeholder `patients`/`providers` models (TASK-002) will need rework when real modules
  exist — already flagged in the database design as a known follow-up.

## Recommended Execution Order

1. TASK-001 (Database Session, Config & Migration Wiring)
2. TASK-002 (ORM Models) — parallel with TASK-003 and TASK-004
3. TASK-003 (Auth Principal Contract)
4. TASK-004 (Status State Machine)
5. TASK-005 (AppointmentRepository) — parallel with TASK-006
6. TASK-006 (Notification Outbox + Dispatcher)
7. TASK-007 (AppointmentService)
8. TASK-008 (FastAPI Router)
9. TASK-009 (Automated Test Suite Consolidation)
10. TASK-010 (Implementation Log & API Documentation)
