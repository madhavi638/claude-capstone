-- Migration 003: ADR-001 — DB-level provider slot exclusivity (BR-009 / NFR-014)
ALTER TABLE appointments
    ADD CONSTRAINT excl_appointments_no_overlap
    EXCLUDE USING gist (
        provider_id WITH =,
        tstzrange(start_time, end_time) WITH &&
    ) WHERE (status IN ('SCHEDULED', 'CONFIRMED', 'IN_PROGRESS'));

CREATE INDEX idx_appointments_patient_start ON appointments (patient_id, start_time);
CREATE INDEX idx_appointments_provider_start ON appointments (provider_id, start_time);
