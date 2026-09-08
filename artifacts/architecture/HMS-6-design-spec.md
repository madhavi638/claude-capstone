# Design Specification

**Ticket:** HMS-6 — Appointment Management (EPIC-004)
**Source:** artifacts/requirements/HMS-6-problem-spec.md

## Overview

Design for the Appointment Management capability of the Hospital Management System (HMS):
booking, rescheduling, cancellation, lifecycle status tracking, role-based visibility, and
stakeholder notifications for appointments between patients and providers.

This workspace contains no existing source code, so this is a greenfield design for the
Appointment module. Stack choices below are inferred from the conventions already encoded in
this project's other SDLC agents (Database Agent assumes PostgreSQL; Implementation Execution
Agent assumes FastAPI + SQLAlchemy + a `frontend/` app) rather than from an inspected codebase,
since none exists yet — see Assumptions.

## Architecture Goals

- Prevent double-booking of a provider's time slot (BR-009, NFR-014).
- Make every lifecycle transition explicit, auditable, and restricted to a defined state
  machine (FR-019, BR-012, NFR-018).
- Keep notification delivery decoupled from the booking transaction so a notification failure
  never blocks a booking/reschedule/cancel operation (NFR-002).
- Enforce role-based visibility (patient sees own; provider/staff see per role) without
  duplicating authorization logic per endpoint (FR-020).

## Assumptions

- Backend: Python, **FastAPI**. ORM: **SQLAlchemy**. Database: **PostgreSQL** (matches the
  Database Agent's stated database and the Implementation Execution Agent's ORM integration
  rules in this project).
- Frontend: a single web frontend consumes the Appointment API; specific framework is not
  constrained by this design.
- An existing (or parallel) HMS module already owns `patients`, `providers`, and `users`/auth —
  Appointment Management references these entities by ID but does not own their schemas.
- Notification delivery mechanism (email/SMS/in-app) is abstracted behind a single interface;
  the concrete channel is an implementation detail, not an architectural decision here.
- Carried forward from the problem spec: one appointment = one patient + one provider (no
  group/multi-party appointments); no recurring appointments in this scope.

## Constraints

- Must not allow two active appointments to hold the same `(provider_id, start_time)` slot
  (BR-009).
- Status transitions must follow a fixed state machine; no direct field mutation that skips
  validation (BR-012).
- Every transition must record actor + timestamp (NFR-018) — required for audit, not optional.

## System Context

```
Patient/Staff UI --> Appointment API (FastAPI) --> Appointment DB (PostgreSQL)
                                |
                                +--> Notification Service (async, decoupled)
                                |
                                +--> Patient/Provider/User services (referenced by ID)
```

## High Level Architecture

- **Appointment API** — FastAPI service exposing REST endpoints for booking, reschedule,
  cancel, status query, and listing appointments by role-scoped filters.
- **Appointment Service (domain layer)** — owns the state machine, slot-conflict check, and
  orchestrates notification dispatch after a successful transaction commits.
- **Appointment Repository** — SQLAlchemy-backed persistence; all reads/writes to
  `appointments` and `appointment_status_history` go through this layer (per Database Agent's
  ORM handoff expectations).
- **Notification Dispatcher** — receives domain events (`AppointmentCreated`,
  `AppointmentRescheduled`, `AppointmentCancelled`) and delivers notifications asynchronously
  (e.g., outbox pattern or background task), so delivery failures are logged, not fatal to the
  triggering request.

## Application Components

| Component | Responsibility |
|---|---|
| `appointment_router` (API layer) | HTTP request/response, auth/role enforcement, input validation |
| `appointment_service` (domain layer) | State machine enforcement, slot-conflict check, transaction boundary |
| `appointment_repository` (data layer) | CRUD + status-history persistence via SQLAlchemy |
| `notification_dispatcher` | Async notification delivery on lifecycle events |
| `appointment_status_history` | Append-only audit log of every transition |

## Data Flow

1. **Booking:** Client → `POST /appointments` → service validates provider/patient exist,
   validates slot not already occupied (BR-009) → repository inserts `appointments` row
   (status=`SCHEDULED`) + history row in one transaction → on commit, emit
   `AppointmentCreated` event → dispatcher notifies patient + provider (FR-021).
2. **Reschedule:** Client → `PATCH /appointments/{id}/reschedule` → service verifies current
   status is reschedulable (not `CANCELLED`/`COMPLETED`, BR-011) → validates new slot free →
   updates row + appends history → emits `AppointmentRescheduled`.
3. **Cancel:** Client → `POST /appointments/{id}/cancel` → service verifies status is
   cancellable → updates status=`CANCELLED` with reason + appends history → emits
   `AppointmentCancelled`.
4. **Visibility/List:** Client → `GET /appointments` → service applies role-based filter
   (patient: own only; provider/staff: per role scope) → repository query with filters
   (date range, status).

## Database Design Approach

(Detailed schema is the Database Agent's responsibility — this section states the approach it
must follow.)

- `appointments` table: `id`, `patient_id` (FK), `provider_id` (FK), `start_time`, `end_time`,
  `status`, `created_at`, `updated_at`.
- A **unique constraint** on `(provider_id, start_time)` for appointments in an active status
  set (or an exclusion constraint over the time range) enforces BR-009/NFR-014 at the database
  level, not just in application code, to withstand concurrent requests.
- `appointment_status_history` table: append-only, `appointment_id` (FK), `from_status`,
  `to_status`, `actor_id`, `changed_at`, `reason` (nullable) — satisfies NFR-018.
- Status stored as a constrained enum/check constraint reflecting the defined state machine
  (BR-012).

## API Design Approach

- REST over HTTPS, JSON payloads, versioned under `/api/v1/appointments`.
- Every write endpoint requires an authenticated actor; role is derived from the auth context,
  not a client-supplied field.
- Idempotency: reschedule/cancel are conditional on current status (return `409 Conflict` if the
  requested transition is invalid per the state machine), preventing lost-update races.

## Security Design

- AuthN/AuthZ delegated to the existing HMS identity/user module (referenced, not re-implemented
  here — see Assumptions).
- Role-based access control at the service layer: patients may only act on/view their own
  appointments; providers/staff scope is enforced server-side, never trusted from the client.
- All state-changing endpoints log actor identity for every transition (NFR-018), which also
  supports security audit/forensics.

## Deployment Design

- Ships as part of the existing HMS backend deployment (FastAPI app + PostgreSQL), no separate
  service needed given the epic's scope. Notification dispatch runs as an async task/worker
  within the same deployment unit to avoid introducing new infrastructure for this epic.

## Scalability Considerations

- The `(provider_id, start_time)` uniqueness check is the main contention point; a DB-level
  constraint (not an app-level read-then-write check) avoids race conditions under concurrent
  booking load (NFR-014) and scales without external locking.
- Read-heavy visibility queries (FR-020) should be indexed on `(patient_id, start_time)` and
  `(provider_id, start_time)` to keep listing performant under load (NFR-001).

## Risks

- **High:** Exact identity/role model for patients/providers/staff is not confirmed (no existing
  codebase to validate against) — could require rework of the authorization approach.
- **Medium:** Notification channel is unspecified; if a specific provider (e.g., email vendor)
  is later mandated, the dispatcher's external integration will need revisiting.
- **Low:** Scope boundary (no recurring/group appointments) is an inferred assumption from the
  epic, not confirmed by a business stakeholder.

## Open Issues

- Confirm identity/role model integration point before implementation planning.
- Confirm notification channel(s) required for FR-021/BR-013.
- Confirm no in-scope requirement for recurring or multi-party appointments.
