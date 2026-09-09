import uuid
from datetime import datetime

from sqlalchemy.orm import Session

from backend.auth.principal import AuthPrincipal
from backend.domain.appointment_state_machine import validate_transition
from backend.domain.errors import AuthorizationError, InvalidStatusTransitionError, NotFoundError
from backend.models.appointment import Appointment
from backend.models.enums import AppointmentStatus
from backend.notifications.dispatcher import enqueue
from backend.repositories.appointment_repository import AppointmentRepository

# BR-011: a cancelled or completed appointment cannot be rescheduled; a new
# appointment must be created instead.
NOT_RESCHEDULABLE_STATUSES = frozenset({AppointmentStatus.CANCELLED, AppointmentStatus.COMPLETED})


class AppointmentService:
    """Orchestrates booking/reschedule/cancellation/query. Never calls the
    repository or notification outbox from outside this class's authorization
    and state-machine checks (see artifacts/implementation/HMS-6-impl-manifest.md
    TASK-007)."""

    def __init__(self, db: Session):
        self.db = db
        self.repository = AppointmentRepository(db)

    def _authorize_read(self, principal: AuthPrincipal, appointment: Appointment) -> None:
        """FR-020 visibility scope: staff see any; patient/provider see only their own."""
        if principal.role == "staff":
            return
        if principal.role == "patient" and appointment.patient_id == principal.user_id:
            return
        if principal.role == "provider" and appointment.provider_id == principal.user_id:
            return
        raise AuthorizationError("Principal is not permitted to access this appointment")

    def _authorize_write_new(self, principal: AuthPrincipal, patient_id: uuid.UUID) -> None:
        """BR-010: only staff (any) or the patient themselves may book an
        appointment. Providers are not authorized to book."""
        if principal.role == "staff":
            return
        if principal.role == "patient" and patient_id == principal.user_id:
            return
        raise AuthorizationError("Principal is not permitted to book this appointment")

    def _authorize_write_existing(self, principal: AuthPrincipal, appointment: Appointment) -> None:
        """BR-010: only staff (any) or the owning patient may reschedule/cancel
        an appointment. Providers are not authorized to write, only read."""
        if principal.role == "staff":
            return
        if principal.role == "patient" and appointment.patient_id == principal.user_id:
            return
        raise AuthorizationError("Principal is not permitted to modify this appointment")

    def _get_or_404(self, appointment_id: uuid.UUID) -> Appointment:
        appointment = self.repository.get_by_id(appointment_id)
        if appointment is None:
            raise NotFoundError(f"Appointment {appointment_id} not found")
        return appointment

    def _enqueue_and_commit(self, appointment_id: uuid.UUID, event_type: str, payload: dict) -> None:
        enqueue(self.db, appointment_id=appointment_id, event_type=event_type, payload=payload)
        self.db.commit()

    def book_appointment(
        self,
        principal: AuthPrincipal,
        patient_id: uuid.UUID,
        provider_id: uuid.UUID,
        start_time: datetime,
        end_time: datetime,
    ) -> Appointment:
        self._authorize_write_new(principal, patient_id)

        appointment = self.repository.create(
            patient_id=patient_id,
            provider_id=provider_id,
            start_time=start_time,
            end_time=end_time,
            actor_id=principal.user_id,
        )
        self._enqueue_and_commit(
            appointment.id, "APPOINTMENT_BOOKED", {"appointment_id": str(appointment.id)}
        )
        return appointment

    def get_appointment(self, principal: AuthPrincipal, appointment_id: uuid.UUID) -> Appointment:
        appointment = self._get_or_404(appointment_id)
        self._authorize_read(principal, appointment)
        return appointment

    def list_for_patient(
        self,
        principal: AuthPrincipal,
        patient_id: uuid.UUID,
        status_filter: AppointmentStatus | None,
        offset: int,
        page_size: int,
    ) -> list[Appointment]:
        if principal.role == "patient" and patient_id != principal.user_id:
            raise AuthorizationError("Patients may only list their own appointments")
        return self.repository.list_for_patient(patient_id, status_filter, offset, page_size)

    def list_for_provider(
        self,
        principal: AuthPrincipal,
        provider_id: uuid.UUID,
        status_filter: AppointmentStatus | None,
        offset: int,
        page_size: int,
    ) -> list[Appointment]:
        if principal.role == "provider" and provider_id != principal.user_id:
            raise AuthorizationError("Providers may only list their own appointments")
        return self.repository.list_for_provider(provider_id, status_filter, offset, page_size)

    def reschedule_appointment(
        self,
        principal: AuthPrincipal,
        appointment_id: uuid.UUID,
        new_start: datetime,
        new_end: datetime,
    ) -> Appointment:
        appointment = self._get_or_404(appointment_id)
        self._authorize_write_existing(principal, appointment)

        current_status = AppointmentStatus(appointment.status)
        if current_status in NOT_RESCHEDULABLE_STATUSES:
            raise InvalidStatusTransitionError(current_status.value, "RESCHEDULED")

        updated = self.repository.reschedule(appointment_id, new_start, new_end, principal.user_id)
        self._enqueue_and_commit(
            updated.id, "APPOINTMENT_RESCHEDULED", {"appointment_id": str(updated.id)}
        )
        return updated

    def cancel_appointment(
        self,
        principal: AuthPrincipal,
        appointment_id: uuid.UUID,
        reason: str | None,
    ) -> Appointment:
        appointment = self._get_or_404(appointment_id)
        self._authorize_write_existing(principal, appointment)

        current_status = AppointmentStatus(appointment.status)
        validate_transition(current_status, AppointmentStatus.CANCELLED)

        updated = self.repository.update_status(
            appointment_id, AppointmentStatus.CANCELLED, principal.user_id, reason
        )
        self._enqueue_and_commit(
            updated.id,
            "APPOINTMENT_CANCELLED",
            {"appointment_id": str(updated.id), "reason": reason},
        )
        return updated

    def change_status(
        self,
        principal: AuthPrincipal,
        appointment_id: uuid.UUID,
        new_status: AppointmentStatus,
        reason: str | None = None,
    ) -> Appointment:
        appointment = self._get_or_404(appointment_id)
        self._authorize_write_existing(principal, appointment)

        current_status = AppointmentStatus(appointment.status)
        validate_transition(current_status, new_status)

        updated = self.repository.update_status(appointment_id, new_status, principal.user_id, reason)
        self._enqueue_and_commit(
            updated.id,
            f"APPOINTMENT_STATUS_CHANGED_{new_status.value}",
            {"appointment_id": str(updated.id)},
        )
        return updated

    def get_history(self, principal: AuthPrincipal, appointment_id: uuid.UUID):
        appointment = self._get_or_404(appointment_id)
        self._authorize_read(principal, appointment)
        return appointment.status_history
