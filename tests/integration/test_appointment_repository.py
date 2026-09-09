import uuid
from datetime import datetime, timedelta, timezone

import pytest

from backend.domain.errors import SlotConflictError
from backend.models.enums import AppointmentStatus
from backend.repositories.appointment_repository import AppointmentRepository


def _slot(hours_from_now=1, duration_minutes=30):
    start = datetime.now(timezone.utc) + timedelta(hours=hours_from_now)
    end = start + timedelta(minutes=duration_minutes)
    return start, end


def test_create_and_get_by_id(db_session, patient, provider, staff_actor_id):
    repo = AppointmentRepository(db_session)
    start, end = _slot()
    appt = repo.create(patient.id, provider.id, start, end, staff_actor_id)
    db_session.commit()

    fetched = repo.get_by_id(appt.id)
    assert fetched is not None
    assert fetched.status == AppointmentStatus.SCHEDULED.value


def test_create_writes_history_row(db_session, patient, provider, staff_actor_id):
    repo = AppointmentRepository(db_session)
    start, end = _slot()
    appt = repo.create(patient.id, provider.id, start, end, staff_actor_id)
    db_session.commit()

    history = appt.status_history
    assert len(history) == 1
    assert history[0].from_status is None
    assert history[0].to_status == AppointmentStatus.SCHEDULED.value


def test_overlapping_active_booking_raises_slot_conflict(db_session, patient, provider, staff_actor_id):
    repo = AppointmentRepository(db_session)
    start, end = _slot()
    repo.create(patient.id, provider.id, start, end, staff_actor_id)
    db_session.commit()

    other_patient_id = uuid.uuid4()
    with pytest.raises(SlotConflictError):
        repo.create(other_patient_id, provider.id, start, end, staff_actor_id)


def test_cancelled_slot_can_be_rebooked(db_session, patient, provider, staff_actor_id):
    repo = AppointmentRepository(db_session)
    start, end = _slot()
    appt = repo.create(patient.id, provider.id, start, end, staff_actor_id)
    db_session.commit()

    repo.update_status(appt.id, AppointmentStatus.CANCELLED, staff_actor_id, reason="test")
    db_session.commit()

    # Same slot, same provider, should now succeed since the exclusion
    # constraint is scoped to active statuses only.
    rebooked = repo.create(patient.id, provider.id, start, end, staff_actor_id)
    db_session.commit()
    assert rebooked.status == AppointmentStatus.SCHEDULED.value


def test_update_status_writes_history_row(db_session, patient, provider, staff_actor_id):
    repo = AppointmentRepository(db_session)
    start, end = _slot()
    appt = repo.create(patient.id, provider.id, start, end, staff_actor_id)
    db_session.commit()

    updated = repo.update_status(appt.id, AppointmentStatus.CONFIRMED, staff_actor_id)
    db_session.commit()

    assert updated.status == AppointmentStatus.CONFIRMED.value
    assert len(updated.status_history) == 2
    assert updated.status_history[-1].to_status == AppointmentStatus.CONFIRMED.value
