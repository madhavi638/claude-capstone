-- HMS-6 seed data — for local development / demo only.

INSERT INTO patients (id, full_name) VALUES
    ('11111111-1111-1111-1111-111111111111', 'Asha Rao'),
    ('22222222-2222-2222-2222-222222222222', 'Ben Carter');

INSERT INTO providers (id, full_name, specialty) VALUES
    ('33333333-3333-3333-3333-333333333333', 'Dr. Meera Nair', 'General Medicine'),
    ('44444444-4444-4444-4444-444444444444', 'Dr. Sam Whitfield', 'Cardiology');

INSERT INTO appointments (id, patient_id, provider_id, start_time, end_time, status) VALUES
    ('55555555-5555-5555-5555-555555555555',
     '11111111-1111-1111-1111-111111111111',
     '33333333-3333-3333-3333-333333333333',
     '2026-09-02 09:00:00+00', '2026-09-02 09:30:00+00', 'SCHEDULED'),
    ('66666666-6666-6666-6666-666666666666',
     '22222222-2222-2222-2222-222222222222',
     '44444444-4444-4444-4444-444444444444',
     '2026-09-02 10:00:00+00', '2026-09-02 10:45:00+00', 'CONFIRMED');

INSERT INTO appointment_status_history (appointment_id, from_status, to_status, actor_id, reason) VALUES
    ('55555555-5555-5555-5555-555555555555', NULL, 'SCHEDULED',
     '11111111-1111-1111-1111-111111111111', 'Initial booking'),
    ('66666666-6666-6666-6666-666666666666', NULL, 'SCHEDULED',
     '22222222-2222-2222-2222-222222222222', 'Initial booking'),
    ('66666666-6666-6666-6666-666666666666', 'SCHEDULED', 'CONFIRMED',
     '44444444-4444-4444-4444-444444444444', 'Provider confirmed slot');
