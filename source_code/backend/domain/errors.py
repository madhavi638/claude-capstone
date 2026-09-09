class SlotConflictError(Exception):
    """Raised when the excl_appointments_no_overlap constraint is violated."""


class InvalidStatusTransitionError(Exception):
    """Raised when a requested status change is not in the transition table."""

    def __init__(self, from_status: str, to_status: str):
        self.from_status = from_status
        self.to_status = to_status
        super().__init__(f"Cannot transition from {from_status!r} to {to_status!r}")


class AuthorizationError(Exception):
    """Raised when a principal is not permitted to act on an appointment."""


class NotFoundError(Exception):
    """Raised when a referenced appointment does not exist."""
