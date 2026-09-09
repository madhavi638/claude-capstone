-- HMS-6 (EPIC-004 Appointment Management) — PostgreSQL schema
-- Generated for Phase 3 (Database) of the Agentic SDLC workflow.
-- See artifacts/database/HMS-6-database-design.md for rationale.

CREATE EXTENSION IF NOT EXISTS "pgcrypto";   -- gen_random_uuid()
CREATE EXTENSION IF NOT EXISTS "btree_gist"; -- required for the EXCLUDE constraint below

-- ---------------------------------------------------------------------------
-- Placeholder/stub tables.
-- patients and providers are owned by other HMS modules that do not yet
-- exist in this workspace. These minimal stand-ins exist only so the
-- appointments schema is self-consistent and runnable in isolation.
-- Replace with the real module's tables (do not merge blindly — reconcile
-- columns) once those modules are implemented.
-- ---------------------------------------------------------------------------

CREATE TABLE patients (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    full_name   TEXT NOT NULL,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE providers (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    full_name   TEXT NOT NULL,
    specialty   TEXT,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ---------------------------------------------------------------------------
-- appointments
-- ---------------------------------------------------------------------------

CREATE TABLE appointments (
    id                   UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    patient_id           UUID NOT NULL REFERENCES patients(id),
    provider_id          UUID NOT NULL REFERENCES providers(id),
    start_time           TIMESTAMPTZ NOT NULL,
    end_time             TIMESTAMPTZ NOT NULL,
    status               TEXT NOT NULL DEFAULT 'SCHEDULED'
                         CHECK (status IN ('SCHEDULED', 'CONFIRMED', 'IN_PROGRESS',
                                            'COMPLETED', 'CANCELLED', 'NO_SHOW')),
    cancellation_reason  TEXT,
    created_at           TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at           TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT chk_appointments_time_order CHECK (end_time > start_time)
);

-- ADR-001: enforce provider slot exclusivity at the database layer.
-- No two appointments in an "active" status may overlap for the same provider.
-- Scoped to active statuses only, so a cancelled/completed appointment never
-- permanently blocks its former slot.
ALTER TABLE appointments
    ADD CONSTRAINT excl_appointments_no_overlap
    EXCLUDE USING gist (
        provider_id WITH =,
        tstzrange(start_time, end_time) WITH &&
    ) WHERE (status IN ('SCHEDULED', 'CONFIRMED', 'IN_PROGRESS'));

CREATE INDEX idx_appointments_patient_start ON appointments (patient_id, start_time);
CREATE INDEX idx_appointments_provider_start ON appointments (provider_id, start_time);

-- ---------------------------------------------------------------------------
-- appointment_status_history
-- Append-only audit trail of every lifecycle transition (NFR-018).
-- ---------------------------------------------------------------------------

CREATE TABLE appointment_status_history (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    appointment_id  UUID NOT NULL REFERENCES appointments(id),
    from_status     TEXT CHECK (from_status IN ('SCHEDULED', 'CONFIRMED', 'IN_PROGRESS',
                                                  'COMPLETED', 'CANCELLED', 'NO_SHOW')),
    to_status       TEXT NOT NULL CHECK (to_status IN ('SCHEDULED', 'CONFIRMED', 'IN_PROGRESS',
                                                         'COMPLETED', 'CANCELLED', 'NO_SHOW')),
    actor_id        UUID NOT NULL, -- references the HMS users module; not FK'd (that table doesn't exist in this workspace)
    reason          TEXT,
    changed_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_appointment_status_history_appointment
    ON appointment_status_history (appointment_id, changed_at);

-- ---------------------------------------------------------------------------
-- appointment_notification_outbox
-- Added in Phase 6 (migration 005) to satisfy Design Review Recommendation 2:
-- durable, retryable BR-013 notification delivery instead of "log-and-drop".
-- See artifacts/database/migrations/005_create_appointment_notification_outbox.sql.
-- ---------------------------------------------------------------------------

CREATE TABLE appointment_notification_outbox (
    id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    appointment_id    UUID NOT NULL REFERENCES appointments(id),
    event_type        TEXT NOT NULL,
    payload           JSONB NOT NULL,
    status             TEXT NOT NULL DEFAULT 'PENDING'
                       CHECK (status IN ('PENDING', 'SENT', 'FAILED')),
    attempt_count      INTEGER NOT NULL DEFAULT 0,
    created_at         TIMESTAMPTZ NOT NULL DEFAULT now(),
    last_attempted_at  TIMESTAMPTZ,
    delivered_at       TIMESTAMPTZ
);

CREATE INDEX idx_appointment_notification_outbox_status
    ON appointment_notification_outbox (status, created_at);

CREATE INDEX idx_appointment_notification_outbox_appointment
    ON appointment_notification_outbox (appointment_id);
