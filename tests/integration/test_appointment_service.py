import uuid
from datetime import datetime, timedelta, timezone

import pytest

from backend.auth.principal import AuthPrincipal
from backend.domain.errors import AuthorizationError, InvalidStatusTransitionError, SlotConflictError
from backend.models.enums import AppointmentStatus
from backend.services.appointment_service import AppointmentService


def _slot():
    start = datetime.now(timezone.utc) + timedelta(hours=1)
    return start, start + timedelta(minutes=30)


def test_patient_can_book_own_appointment(db_session, patient, provider):
    service = AppointmentService(db_session)
    principal = AuthPrincipal(user_id=patient.id, role="patient")
    start, end = _slot()

    appt = service.book_appointment(principal, patient.id, provider.id, start, end)
    assert appt.status == AppointmentStatus.SCHEDULED.value


def test_patient_cannot_book_for_another_patient(db_session, patient, provider):
    service = AppointmentService(db_session)
    principal = AuthPrincipal(user_id=uuid.uuid4(), role="patient")
    start, end = _slot()

    with pytest.raises(AuthorizationError):
        service.book_appointment(principal, patient.id, provider.id, start, end)


def test_double_booking_same_provider_raises_conflict(db_session, patient, provider, staff_actor_id):
    service = AppointmentService(db_session)
    staff = AuthPrincipal(user_id=staff_actor_id, role="staff")
    start, end = _slot()

    service.book_appointment(staff, patient.id, provider.id, start, end)
    with pytest.raises(SlotConflictError):
        service.book_appointment(staff, uuid.uuid4(), provider.id, start, end)


def test_cancel_then_complete_is_rejected_by_state_machine(db_session, patient, provider, staff_actor_id):
    service = AppointmentService(db_session)
    staff = AuthPrincipal(user_id=staff_actor_id, role="staff")
    start, end = _slot()

    appt = service.book_appointment(staff, patient.id, provider.id, start, end)
    service.cancel_appointment(staff, appt.id, reason="patient request")

    with pytest.raises(InvalidStatusTransitionError):
        service.change_status(staff, appt.id, AppointmentStatus.COMPLETED)


def test_provider_cannot_access_other_providers_appointment(db_session, patient, provider):
    service = AppointmentService(db_session)
    staff = AuthPrincipal(user_id=uuid.uuid4(), role="staff")
    start, end = _slot()
    appt = service.book_appointment(staff, patient.id, provider.id, start, end)

    other_provider = AuthPrincipal(user_id=uuid.uuid4(), role="provider")
    with pytest.raises(AuthorizationError):
        service.get_appointment(other_provider, appt.id)


def test_reschedule_cancelled_appointment_is_rejected(db_session, patient, provider, staff_actor_id):
    """BR-011 regression: a CANCELLED appointment must not be reschedulable
    (Phase 7 Code Review, Compliance finding #1 — Critical)."""
    service = AppointmentService(db_session)
    staff = AuthPrincipal(user_id=staff_actor_id, role="staff")
    start, end = _slot()
    appt = service.book_appointment(staff, patient.id, provider.id, start, end)
    service.cancel_appointment(staff, appt.id, reason="patient request")

    new_start = start + timedelta(hours=2)
    new_end = end + timedelta(hours=2)
    with pytest.raises(InvalidStatusTransitionError):
        service.reschedule_appointment(staff, appt.id, new_start, new_end)


def test_reschedule_completed_appointment_is_rejected(db_session, patient, provider, staff_actor_id):
    """BR-011 regression: a COMPLETED appointment must not be reschedulable
    (Phase 7 Code Review, Compliance finding #1 — Critical)."""
    service = AppointmentService(db_session)
    staff = AuthPrincipal(user_id=staff_actor_id, role="staff")
    start, end = _slot()
    appt = service.book_appointment(staff, patient.id, provider.id, start, end)
    service.change_status(staff, appt.id, AppointmentStatus.CONFIRMED)
    service.change_status(staff, appt.id, AppointmentStatus.IN_PROGRESS)
    service.change_status(staff, appt.id, AppointmentStatus.COMPLETED)

    new_start = start + timedelta(hours=2)
    new_end = end + timedelta(hours=2)
    with pytest.raises(InvalidStatusTransitionError):
        service.reschedule_appointment(staff, appt.id, new_start, new_end)


def test_provider_cannot_book_appointment(db_session, patient, provider):
    """BR-010 regression: provider is not an authorized actor for booking
    (Phase 7 Code Review, Compliance finding #2 — High)."""
    service = AppointmentService(db_session)
    provider_principal = AuthPrincipal(user_id=uuid.uuid4(), role="provider")
    start, end = _slot()

    with pytest.raises(AuthorizationError):
        service.book_appointment(provider_principal, patient.id, provider.id, start, end)


def test_provider_cannot_reschedule_own_appointment(db_session, patient, provider, staff_actor_id):
    """BR-010 regression: provider is not an authorized actor for
    rescheduling, even an appointment where provider_id == principal.user_id
    (Phase 7 Code Review, Compliance finding #2 — High)."""
    service = AppointmentService(db_session)
    staff = AuthPrincipal(user_id=staff_actor_id, role="staff")
    start, end = _slot()
    appt = service.book_appointment(staff, patient.id, provider.id, start, end)

    provider_principal = AuthPrincipal(user_id=provider.id, role="provider")
    new_start = start + timedelta(hours=2)
    new_end = end + timedelta(hours=2)
    with pytest.raises(AuthorizationError):
        service.reschedule_appointment(provider_principal, appt.id, new_start, new_end)


def test_provider_cannot_cancel_own_appointment(db_session, patient, provider, staff_actor_id):
    """BR-010 regression: provider is not an authorized actor for
    cancelling, even an appointment where provider_id == principal.user_id
    (Phase 7 Code Review, Compliance finding #2 — High)."""
    service = AppointmentService(db_session)
    staff = AuthPrincipal(user_id=staff_actor_id, role="staff")
    start, end = _slot()
    appt = service.book_appointment(staff, patient.id, provider.id, start, end)

    provider_principal = AuthPrincipal(user_id=provider.id, role="provider")
    with pytest.raises(AuthorizationError):
        service.cancel_appointment(provider_principal, appt.id, reason="not allowed")


def test_reschedule_and_cancel_each_enqueue_one_notification(db_session, patient, provider, staff_actor_id):
    from backend.models.appointment_notification_outbox import AppointmentNotificationOutbox

    service = AppointmentService(db_session)
    staff = AuthPrincipal(user_id=staff_actor_id, role="staff")
    start, end = _slot()
    appt = service.book_appointment(staff, patient.id, provider.id, start, end)

    new_start = start + timedelta(hours=2)
    new_end = end + timedelta(hours=2)
    service.reschedule_appointment(staff, appt.id, new_start, new_end)
    service.cancel_appointment(staff, appt.id, reason="test")

    count = (
        db_session.query(AppointmentNotificationOutbox)
        .filter(AppointmentNotificationOutbox.appointment_id == appt.id)
        .count()
    )
    # book + reschedule + cancel = 3 outbox events
    assert count == 3
