# Problem Specification

**Ticket:** HMS-6
**Original Backlog ID:** EPIC-004
**Title:** Appointment Management
**Backlog Level:** Epic (Jira Issue Type: Workstream)
**Priority:** Critical (Jira: Highest)
**Status:** To Do
**Reporter:** madhavi
**Labels:** backlog-epic, epic-id-epic-004, hms-backlog-import

## Executive Summary

HMS-6 is the "Appointment Management" epic for the Hospital Management System (HMS). Its
purpose, as stated on the ticket, is to **coordinate appointment booking, lifecycle changes,
visibility, and stakeholder notifications**. It is the umbrella workstream under which
appointment-related functional requirements, non-functional requirements, and business rules
are delivered.

No child stories/sub-tasks were found linked to HMS-6 in Jira at the time of this analysis, and
the referenced FR/NFR/BR items exist only as ID references on the epic (no expanded text was
retrievable from Jira). The scope below is therefore derived from the epic's stated purpose and
the referenced requirement IDs, and is flagged for validation in the Open Issues section.

## Traceability References (from Jira)

| Type | IDs |
|---|---|
| Functional Requirements | FR-016, FR-017, FR-018, FR-019, FR-020, FR-021 |
| Non-Functional Requirements | NFR-001, NFR-002, NFR-014, NFR-018 |
| Business Rules | BR-009, BR-010, BR-011, BR-012, BR-013 |

## Functional Requirements (inferred scope, pending validation)

- **FR-016 — Appointment Booking:** Patients/staff can create a new appointment, selecting
  provider, department, date/time slot, and appointment type.
- **FR-017 — Appointment Rescheduling:** An existing appointment can be moved to a new date/time
  or provider, with prior slot released and new slot validated for availability.
- **FR-018 — Appointment Cancellation:** An appointment can be cancelled by an authorized actor
  (patient or staff), with a reason captured and the slot released.
- **FR-019 — Appointment Status Lifecycle:** Appointments progress through defined states
  (e.g., Scheduled → Confirmed → In Progress → Completed / Cancelled / No-Show), and every
  transition is recorded.
- **FR-020 — Appointment Visibility:** Authorized users (patient, provider, front-desk/admin
  staff) can view appointments relevant to them, filtered by role, date range, and status.
- **FR-021 — Stakeholder Notifications:** Patients and providers are notified of appointment
  creation, changes, and cancellations through the system's notification channel(s).

## Non-Functional Requirements (inferred scope, pending validation)

- **NFR-001 — Performance:** Appointment booking/lookup operations return within an acceptable
  response time under expected concurrent load.
- **NFR-002 — Availability/Reliability:** Appointment scheduling is a critical-path capability
  and must be resilient to partial failures (e.g., notification delivery failure must not block
  booking).
- **NFR-014 — Data Integrity/Consistency:** No double-booking of the same provider/slot;
  concurrent booking attempts on the same slot must be handled safely.
- **NFR-018 — Auditability:** All appointment lifecycle transitions (create, reschedule, cancel)
  must be traceable to an actor and timestamp.

## Business Rules (inferred scope, pending validation)

- **BR-009:** An appointment cannot be booked into a slot that is already occupied by another
  active appointment for the same provider.
- **BR-010:** Only authorized roles (patient for their own appointments; staff/admin for any)
  may reschedule or cancel an appointment.
- **BR-011:** A cancelled or completed appointment cannot be rescheduled; a new appointment must
  be created instead.
- **BR-012:** Appointment status changes must follow the defined lifecycle state machine (no
  arbitrary transitions, e.g. Completed → Scheduled is not permitted).
- **BR-013:** Stakeholders (patient and assigned provider) must be notified on any change to an
  appointment they are party to.

## Constraints

- Must integrate with existing HMS provider/patient/user identity and role model (exact model
  not yet confirmed — see Open Issues).
- Must integrate with whatever notification mechanism the HMS platform already uses or defines
  (email/SMS/in-app — not yet confirmed).
- No child stories were available to confirm scope boundaries (e.g., whether recurring
  appointments, waitlists, or multi-provider appointments are in scope).

## Assumptions

- "Stakeholder" in FR-021/BR-013 is assumed to mean the patient and the assigned provider only,
  not third parties (e.g., billing), unless corrected during architecture/review.
- A single appointment is assumed to be tied to exactly one provider and one patient (no
  group/multi-patient appointments) unless corrected.
- Notification delivery is assumed to be asynchronous/best-effort and must not block the
  booking transaction (supports NFR-002).

## Acceptance Criteria

1. A user with appropriate role can create an appointment for a valid provider/slot/date-time,
   and the system rejects booking into an already-occupied slot (BR-009).
2. A user with appropriate role can reschedule an active (non-cancelled, non-completed)
   appointment; the prior slot is released and the new slot is validated (FR-017, BR-011).
3. A user with appropriate role can cancel an active appointment with a captured reason; the
   slot is released (FR-018).
4. Every appointment exposes its current lifecycle status, and status transitions are restricted
   to the defined state machine (FR-019, BR-012).
5. Patients see only their own appointments; providers/staff see appointments per their role's
   visibility rules (FR-020).
6. On booking, reschedule, or cancellation, the patient and assigned provider receive a
   notification (FR-021, BR-013).
7. All lifecycle transitions are recorded with actor and timestamp (NFR-018).
8. Concurrent booking attempts against the same provider/slot cannot both succeed (NFR-014).

## Open Issues

- **No child stories/sub-tasks found under HMS-6 in Jira.** The FR/NFR/BR items above are
  inferred from ID references and the epic's one-line purpose only — they should be validated
  against the full HMS backlog specification (or by expanding HMS-6 into child stories) before
  architecture proceeds on unconfirmed assumptions.
- Identity/role model and notification channel are not yet confirmed against the existing HMS
  codebase (no source code exists in this workspace yet to cross-check).
- Recurring appointments, waitlisting, and multi-party appointments are out of scope unless
  stated otherwise — needs business confirmation.

## Source

Retrieved from Jira: `HMS-6` at `rambhamadhavi5.atlassian.net` (project key `HMS`), issue type
"Workstream", via Jira REST API.
