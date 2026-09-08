import uuid
from datetime import datetime

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend.domain.errors import NotFoundError, SlotConflictError
from backend.models.appointment import Appointment
from backend.models.appointment_status_history import AppointmentStatusHistory
from backend.models.enums import AppointmentStatus


class AppointmentRepository:
    """Only module allowed to issue SQL for appointments/appointment_status_history.

    Per artifacts/database/HMS-6-orm-spec.md: no method may update
    `Appointment.status` without writing a corresponding history row in the
    same transaction (NFR-018), and `excl_appointments_no_overlap` violations
    must never propagate as a generic error.

    These methods flush but deliberately do NOT commit — the caller (the
    service layer) owns the transaction boundary so that the appointment
    change, its history row, and the TASK-006 notification outbox row all
    commit atomically together. Committing here would split that guarantee.
    """

    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        patient_id: uuid.UUID,
        provider_id: uuid.UUID,
        start_time: datetime,
        end_time: datetime,
        actor_id: uuid.UUID,
    ) -> Appointment:
        appointment = Appointment(
            patient_id=patient_id,
            provider_id=provider_id,
            start_time=start_time,
            end_time=end_time,
            status=AppointmentStatus.SCHEDULED.value,
        )
        self.db.add(appointment)
        try:
            self.db.flush()
        except IntegrityError as exc:
            self.db.rollback()
            raise SlotConflictError(
                f"Provider {provider_id} already has an overlapping active appointment"
            ) from exc

        history = AppointmentStatusHistory(
            appointment_id=appointment.id,
            from_status=None,
            to_status=AppointmentStatus.SCHEDULED.value,
            actor_id=actor_id,
        )
        self.db.add(history)
        self.db.flush()
        return appointment

    def get_by_id(self, appointment_id: uuid.UUID) -> Appointment | None:
        return self.db.get(Appointment, appointment_id)

    def list_for_patient(
        self,
        patient_id: uuid.UUID,
        status_filter: AppointmentStatus | None = None,
        offset: int = 0,
        limit: int = 20,
    ) -> list[Appointment]:
        return self._list_by_owner(Appointment.patient_id, patient_id, status_filter, offset, limit)

    def list_for_provider(
        self,
        provider_id: uuid.UUID,
        status_filter: AppointmentStatus | None = None,
        offset: int = 0,
        limit: int = 20,
    ) -> list[Appointment]:
        return self._list_by_owner(Appointment.provider_id, provider_id, status_filter, offset, limit)

    def _list_by_owner(
        self,
        owner_column,
        owner_id: uuid.UUID,
        status_filter: AppointmentStatus | None,
        offset: int,
        limit: int,
    ) -> list[Appointment]:
        query = self.db.query(Appointment).filter(owner_column == owner_id)
        if status_filter is not None:
            query = query.filter(Appointment.status == status_filter.value)
        return (
            query.order_by(Appointment.start_time)
            .offset(offset)
            .limit(limit)
            .all()
        )

    def update_status(
        self,
        appointment_id: uuid.UUID,
        new_status: AppointmentStatus,
        actor_id: uuid.UUID,
        reason: str | None = None,
    ) -> Appointment:
        appointment = self.db.get(Appointment, appointment_id)
        if appointment is None:
            raise NotFoundError(f"Appointment {appointment_id} not found")

        from_status = appointment.status
        appointment.status = new_status.value
        if reason is not None:
            appointment.cancellation_reason = reason

        history = AppointmentStatusHistory(
            appointment_id=appointment.id,
            from_status=from_status,
            to_status=new_status.value,
            actor_id=actor_id,
            reason=reason,
        )
        self.db.add(history)
        self.db.flush()
        return appointment

    def reschedule(
        self,
        appointment_id: uuid.UUID,
        new_start: datetime,
        new_end: datetime,
        actor_id: uuid.UUID,
    ) -> Appointment:
        appointment = self.db.get(Appointment, appointment_id)
        if appointment is None:
            raise NotFoundError(f"Appointment {appointment_id} not found")

        appointment.start_time = new_start
        appointment.end_time = new_end
        try:
            self.db.flush()
        except IntegrityError as exc:
            self.db.rollback()
            raise SlotConflictError(
                f"Requested reschedule overlaps another active appointment for provider "
                f"{appointment.provider_id}"
            ) from exc

        # from_status == to_status here is intentional: rescheduling doesn't
        # change lifecycle status, but still needs an audit row (NFR-018), so
        # the unchanged status is recorded on both sides as the reschedule
        # event marker rather than a real transition.
        history = AppointmentStatusHistory(
            appointment_id=appointment.id,
            from_status=appointment.status,
            to_status=appointment.status,
            actor_id=actor_id,
            reason="rescheduled",
        )
        self.db.add(history)
        self.db.flush()
        return appointment
