-- HMS-6 — Migration 005: notification outbox
-- Added during Phase 6 (Implementation Execution) to satisfy Design Review
-- Recommendation 2 (durable, retryable BR-013 notification delivery instead
-- of a "log-and-drop" async call). See artifacts/implementation/HMS-6-impl-manifest.md
-- TASK-006 and artifacts/review/HMS-6-design-review.md Reliability Review.
--
-- Additive only: does not alter any table created in migrations 001-004.

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
