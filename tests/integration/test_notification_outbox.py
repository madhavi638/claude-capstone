from datetime import datetime, timedelta, timezone

from backend.models.appointment_notification_outbox import AppointmentNotificationOutbox
from backend.models.enums import NotificationOutboxStatus
from backend.notifications.dispatcher import NotificationDispatcher, enqueue
from backend.repositories.appointment_repository import AppointmentRepository


def _slot():
    start = datetime.now(timezone.utc) + timedelta(hours=1)
    return start, start + timedelta(minutes=30)


def test_enqueue_is_durable_within_same_transaction(db_session, patient, provider, staff_actor_id):
    """The outbox row must commit atomically with the appointment it belongs
    to — this is the whole point of Design Review Recommendation 2."""
    repo = AppointmentRepository(db_session)
    start, end = _slot()
    appt = repo.create(patient.id, provider.id, start, end, staff_actor_id)
    enqueue(db_session, appt.id, "APPOINTMENT_BOOKED", {"appointment_id": str(appt.id)})
    db_session.commit()

    rows = (
        db_session.query(AppointmentNotificationOutbox)
        .filter(AppointmentNotificationOutbox.appointment_id == appt.id)
        .all()
    )
    assert len(rows) == 1
    assert rows[0].status == NotificationOutboxStatus.PENDING.value


def test_dispatcher_marks_failed_after_max_attempts(db_session, patient, provider, staff_actor_id):
    repo = AppointmentRepository(db_session)
    start, end = _slot()
    appt = repo.create(patient.id, provider.id, start, end, staff_actor_id)
    enqueue(db_session, appt.id, "APPOINTMENT_BOOKED", {"appointment_id": str(appt.id)})
    db_session.commit()

    dispatcher = NotificationDispatcher(db_session, send_fn=lambda row: False)
    for _ in range(5):
        dispatcher.run_once()

    row = (
        db_session.query(AppointmentNotificationOutbox)
        .filter(AppointmentNotificationOutbox.appointment_id == appt.id)
        .one()
    )
    assert row.status == NotificationOutboxStatus.FAILED.value
    assert row.attempt_count == 5


def test_dispatcher_marks_sent_on_successful_delivery(db_session, patient, provider, staff_actor_id):
    repo = AppointmentRepository(db_session)
    start, end = _slot()
    appt = repo.create(patient.id, provider.id, start, end, staff_actor_id)
    enqueue(db_session, appt.id, "APPOINTMENT_BOOKED", {"appointment_id": str(appt.id)})
    db_session.commit()

    dispatcher = NotificationDispatcher(db_session, send_fn=lambda row: True)
    dispatcher.run_once()

    row = (
        db_session.query(AppointmentNotificationOutbox)
        .filter(AppointmentNotificationOutbox.appointment_id == appt.id)
        .one()
    )
    assert row.status == NotificationOutboxStatus.SENT.value
    assert row.delivered_at is not None


def test_failed_row_is_never_deleted(db_session, patient, provider, staff_actor_id):
    repo = AppointmentRepository(db_session)
    start, end = _slot()
    appt = repo.create(patient.id, provider.id, start, end, staff_actor_id)
    enqueue(db_session, appt.id, "APPOINTMENT_BOOKED", {"appointment_id": str(appt.id)})
    db_session.commit()

    dispatcher = NotificationDispatcher(db_session, send_fn=lambda row: False)
    for _ in range(5):
        dispatcher.run_once()

    count = (
        db_session.query(AppointmentNotificationOutbox)
        .filter(AppointmentNotificationOutbox.appointment_id == appt.id)
        .count()
    )
    assert count == 1
