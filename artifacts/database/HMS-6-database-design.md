# Database Design — HMS-6 (Appointment Management)

**Source:** artifacts/architecture/HMS-6-design-spec.md, artifacts/architecture/adr/HMS-6-ADR-001.md
**Database:** PostgreSQL 16
**Generated artifacts:** `database/schema.sql`, `database/migrations/001-004`, `database/seed_data.sql`, `database/docker-compose.yml`

## Entities

| Table | Purpose |
|---|---|
| `patients` | **Placeholder/stub.** Owned by another HMS module that does not exist in this workspace yet. Minimal columns only, so `appointments` has a valid FK target. Do not treat as the real schema — reconcile with the actual patients module when it exists. |
| `providers` | **Placeholder/stub.** Same caveat as `patients`. |
| `appointments` | Core entity: one booking between one patient and one provider. |
| `appointment_status_history` | Append-only audit trail of every lifecycle transition. |

## Normalization

Schema is in 3NF: no repeating groups, no derived/redundant columns (e.g. duration is computed
from `start_time`/`end_time`, not stored), and status history is a separate table rather than a
denormalized log column on `appointments`.

## Key Design Decisions

1. **Provider slot exclusivity is enforced at the database layer (ADR-001).**
   `appointments` has an `EXCLUDE USING gist` constraint over `(provider_id, tstzrange(start_time, end_time))`,
   scoped to active statuses (`SCHEDULED`, `CONFIRMED`, `IN_PROGRESS`) via a partial `WHERE`
   clause. This directly satisfies BR-009 (no double-booking) and NFR-014 (safe under
   concurrent booking attempts) — two concurrent transactions attempting to book overlapping
   slots for the same provider will have one fail at commit with a constraint violation, which
   the service layer should translate to `409 Conflict`.
   - Requires the `btree_gist` extension (enabled in migration 001).
   - Scoping the exclusion to active statuses means a cancelled or completed appointment does
     **not** permanently block its former slot.
2. **Status is a `CHECK`-constrained value, not a free-text column** (BR-012): `SCHEDULED`,
   `CONFIRMED`, `IN_PROGRESS`, `COMPLETED`, `CANCELLED`, `NO_SHOW`. The database does not enforce
   *transition* validity (e.g. blocking `COMPLETED → SCHEDULED`) — that is a service-layer
   responsibility (the state machine), consistent with the Database Agent's non-responsibility
   for business logic.
3. **`appointment_status_history` is append-only** and satisfies NFR-018 (auditability):
   `actor_id` and `changed_at` are required on every row, and `from_status` is nullable only for
   the initial creation event.
4. **`actor_id` on `appointment_status_history` is intentionally not a foreign key** — the HMS
   users/identity module does not exist in this workspace, so there is no table to reference.
   This must be revisited (added as a proper FK) once that module exists.

## Indexes

| Index | Rationale |
|---|---|
| `excl_appointments_no_overlap` (GiST) | ADR-001 slot exclusivity |
| `idx_appointments_patient_start` | Supports patient-scoped visibility queries (FR-020), ordered/filtered by date |
| `idx_appointments_provider_start` | Supports provider-scoped visibility queries (FR-020) |
| `idx_appointment_status_history_appointment` | Supports fetching an appointment's full history in order |

## Migration Order

1. `001_create_extensions_and_stub_tables.sql` — extensions, `patients`, `providers`
2. `002_create_appointments_table.sql` — `appointments` (no exclusion constraint yet)
3. `003_add_appointment_exclusion_constraint_and_indexes.sql` — ADR-001 constraint + indexes
4. `004_create_appointment_status_history_table.sql` — audit table

Applied in this order, every foreign key references an already-existing table, and the
exclusion constraint is added only after `appointments` exists.

## Seed Data

`database/seed_data.sql` inserts 2 patients, 2 providers, 2 appointments (one `SCHEDULED`, one
`CONFIRMED` with a corresponding history row) — enough to exercise booking, visibility, and
history queries locally without hitting the exclusion constraint.

## Docker

`database/docker-compose.yml` runs `postgres:16-alpine`, auto-applying `schema.sql` then
`seed_data.sql` via the standard `docker-entrypoint-initdb.d` mechanism on first container start.
Credentials/port are overridable via `HMS6_DB_*` environment variables; insecure defaults are for
local dev only.

## Risks / Follow-ups

- `patients`/`providers` are placeholders. When the real HMS patient/provider modules exist,
  reconcile column names/types before merging — do not assume this stub schema is authoritative.
- `actor_id` should become a real FK to a `users` table once the identity module exists.
- If appointment durations are always fixed-length in practice, the exclusion constraint could be
  simplified to a plain partial unique index on `(provider_id, start_time)` — kept as a range
  exclusion here per ADR-001 to also cover variable-duration appointments.
