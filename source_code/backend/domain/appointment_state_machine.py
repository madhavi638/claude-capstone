"""Explicit appointment status transition table (BR-012).

See artifacts/review/HMS-6-design-review.md (Maintainability Review, Medium
risk) and artifacts/implementation/HMS-6-impl-manifest.md (TASK-004). This is
the single authoritative source of legal transitions — no other module may
duplicate or reinterpret this table.
"""

from backend.domain.errors import InvalidStatusTransitionError
from backend.models.enums import AppointmentStatus

TRANSITIONS: dict[AppointmentStatus, frozenset[AppointmentStatus]] = {
    AppointmentStatus.SCHEDULED: frozenset(
        {AppointmentStatus.CONFIRMED, AppointmentStatus.CANCELLED, AppointmentStatus.NO_SHOW}
    ),
    AppointmentStatus.CONFIRMED: frozenset(
        {AppointmentStatus.IN_PROGRESS, AppointmentStatus.CANCELLED, AppointmentStatus.NO_SHOW}
    ),
    AppointmentStatus.IN_PROGRESS: frozenset(
        {AppointmentStatus.COMPLETED, AppointmentStatus.CANCELLED}
    ),
    AppointmentStatus.COMPLETED: frozenset(),
    AppointmentStatus.CANCELLED: frozenset(),
    AppointmentStatus.NO_SHOW: frozenset(),
}


def is_transition_allowed(from_status: AppointmentStatus, to_status: AppointmentStatus) -> bool:
    return to_status in TRANSITIONS.get(from_status, frozenset())


def validate_transition(from_status: AppointmentStatus, to_status: AppointmentStatus) -> None:
    if not is_transition_allowed(from_status, to_status):
        raise InvalidStatusTransitionError(from_status.value, to_status.value)
