import pytest

from backend.domain.appointment_state_machine import TRANSITIONS, validate_transition
from backend.domain.errors import InvalidStatusTransitionError
from backend.models.enums import AppointmentStatus

LEGAL_PAIRS = [
    (from_status, to_status)
    for from_status, allowed in TRANSITIONS.items()
    for to_status in allowed
]

ALL_STATUSES = list(AppointmentStatus)
ILLEGAL_PAIRS = [
    (from_status, to_status)
    for from_status in ALL_STATUSES
    for to_status in ALL_STATUSES
    if to_status not in TRANSITIONS.get(from_status, frozenset())
]


@pytest.mark.parametrize("from_status,to_status", LEGAL_PAIRS)
def test_legal_transitions_succeed(from_status, to_status):
    validate_transition(from_status, to_status)  # must not raise


@pytest.mark.parametrize("from_status,to_status", ILLEGAL_PAIRS)
def test_illegal_transitions_raise(from_status, to_status):
    with pytest.raises(InvalidStatusTransitionError):
        validate_transition(from_status, to_status)


@pytest.mark.parametrize(
    "terminal_status",
    [AppointmentStatus.COMPLETED, AppointmentStatus.CANCELLED, AppointmentStatus.NO_SHOW],
)
def test_terminal_states_have_no_outgoing_transitions(terminal_status):
    assert TRANSITIONS[terminal_status] == frozenset()
