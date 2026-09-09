# HMS-6 Appointment API Reference

Base path: `/api/v1/appointments`

## Authentication

Every endpoint requires an `Authorization` header of the form:

```
Authorization: Bearer <user_id>:<role>
```

where `<user_id>` is a UUID and `<role>` is one of `patient`, `provider`, `staff`.

**This is a stub authentication contract** (Design Review Recommendation 1) pending a real
identity/session module. It exists so the authorization logic in the service layer can be built
and tested now; it must be replaced before production use. Missing header, malformed scheme,
malformed token, or an unrecognized role all return `401 Unauthorized`.

## Authorization rules

- `staff` — unrestricted read/write access to all appointments.
- `patient` — may book/read/reschedule/cancel only appointments where `patient_id` matches their
  own `user_id`.
- `provider` — may read only appointments where `provider_id` matches their own `user_id`.

Violations return `403 Forbidden`.

## Endpoints

### `POST /api/v1/appointments`

Book a new appointment.

**Request body**

```json
{
  "patient_id": "uuid",
  "provider_id": "uuid",
  "start_time": "2026-09-01T10:00:00Z",
  "end_time": "2026-09-01T10:30:00Z"
}
```

**Responses**

| Status | Meaning |
|---|---|
| 201 | Created. Body is the `AppointmentResponse` (status `SCHEDULED`). |
| 401 | Missing/invalid auth. |
| 403 | Patient booking for a different patient. |
| 409 | Slot conflict — the provider already has an appointment overlapping this time range (enforced at the database level via a GiST exclusion constraint). |
| 422 | Malformed body. |

### `GET /api/v1/appointments/{appointment_id}`

Fetch a single appointment.

| Status | Meaning |
|---|---|
| 200 | `AppointmentResponse`. |
| 401 | Missing/invalid auth. |
| 403 | Requester does not own this appointment (patient/provider scoping). |
| 404 | No such appointment. |

### `GET /api/v1/appointments`

List appointments. Exactly one of `patient_id` or `provider_id` is required as a query parameter.

**Query parameters**

| Name | Type | Default | Notes |
|---|---|---|---|
| `patient_id` | uuid | — | Mutually exclusive with `provider_id`. |
| `provider_id` | uuid | — | Mutually exclusive with `patient_id`. |
| `status` | enum | — | Optional filter: `SCHEDULED`, `CONFIRMED`, `IN_PROGRESS`, `COMPLETED`, `CANCELLED`, `NO_SHOW`. |
| `offset` | int ≥ 0 | 0 | Pagination offset. |
| `page_size` | int | 20 | 1–100; requests above 100 are rejected. |

**Responses**

| Status | Meaning |
|---|---|
| 200 | `AppointmentListResponse` — `{ items, page_size, offset }`. History is not eager-loaded on list items (FR-020 lean-listing requirement). |
| 403 | Requester does not own the requested `patient_id`/`provider_id` scope. |
| 422 | Neither `patient_id` nor `provider_id` given, or `page_size` out of range (1–100). |

### `PATCH /api/v1/appointments/{appointment_id}/reschedule`

**Request body**

```json
{
  "start_time": "2026-09-01T14:00:00Z",
  "end_time": "2026-09-01T14:30:00Z"
}
```

| Status | Meaning |
|---|---|
| 200 | `AppointmentResponse` with the new times. |
| 403 | Not the owning patient/provider, or not staff. |
| 404 | No such appointment. |
| 409 | New slot conflicts with another appointment for the same provider. |

### `POST /api/v1/appointments/{appointment_id}/cancel`

**Request body**

```json
{ "reason": "patient request" }
```

`reason` is optional.

| Status | Meaning |
|---|---|
| 200 | `AppointmentResponse` with status `CANCELLED`. |
| 403 | Not authorized to cancel this appointment. |
| 404 | No such appointment. |
| 409 | Appointment is in a terminal state (`COMPLETED`, `CANCELLED`, `NO_SHOW`) and cannot be cancelled (state machine, BR-012). |

### `GET /api/v1/appointments/{appointment_id}/history`

Returns the append-only status-change history for an appointment, oldest first.

| Status | Meaning |
|---|---|
| 200 | `list[AppointmentStatusHistoryResponse]`. |
| 403 | Not authorized to view this appointment. |
| 404 | No such appointment. |

## Response schemas

**AppointmentResponse**

```json
{
  "id": "uuid",
  "patient_id": "uuid",
  "provider_id": "uuid",
  "start_time": "datetime",
  "end_time": "datetime",
  "status": "SCHEDULED | CONFIRMED | IN_PROGRESS | COMPLETED | CANCELLED | NO_SHOW",
  "cancellation_reason": "string | null",
  "created_at": "datetime",
  "updated_at": "datetime"
}
```

**AppointmentStatusHistoryResponse**

```json
{
  "id": "uuid",
  "from_status": "string | null",
  "to_status": "string",
  "actor_id": "uuid",
  "reason": "string | null",
  "changed_at": "datetime"
}
```

## Status lifecycle (BR-012)

```
SCHEDULED   -> CONFIRMED, CANCELLED, NO_SHOW
CONFIRMED   -> IN_PROGRESS, CANCELLED, NO_SHOW
IN_PROGRESS -> COMPLETED, CANCELLED
COMPLETED   -> (terminal)
CANCELLED   -> (terminal)
NO_SHOW     -> (terminal)
```

Any transition not listed above is rejected with `409 Conflict`.

## Notifications

Every booking, reschedule, and cancellation enqueues a row in the
`appointment_notification_outbox` table within the same database transaction as the appointment
change (Design Review Recommendation 2). Delivery is handled out-of-band by
`NotificationDispatcher`, which retries up to 5 attempts before marking a notification `FAILED`
(never deleted). This endpoint surface does not expose the outbox directly; it is an internal
durability mechanism.
