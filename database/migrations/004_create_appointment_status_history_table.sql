-- Migration 004: append-only lifecycle audit trail (NFR-018)
CREATE TABLE appointment_status_history (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    appointment_id  UUID NOT NULL REFERENCES appointments(id),
    from_status     TEXT CHECK (from_status IN ('SCHEDULED', 'CONFIRMED', 'IN_PROGRESS',
                                                  'COMPLETED', 'CANCELLED', 'NO_SHOW')),
    to_status       TEXT NOT NULL CHECK (to_status IN ('SCHEDULED', 'CONFIRMED', 'IN_PROGRESS',
                                                         'COMPLETED', 'CANCELLED', 'NO_SHOW')),
    actor_id        UUID NOT NULL,
    reason          TEXT,
    changed_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_appointment_status_history_appointment
    ON appointment_status_history (appointment_id, changed_at);
