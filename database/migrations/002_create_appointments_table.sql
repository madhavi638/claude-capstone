-- Migration 002: appointments table
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
