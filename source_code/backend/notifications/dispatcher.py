"""Durable notification outbox (Design Review Recommendation 2).

`enqueue()` writes an outbox row using the caller's existing session and does
NOT commit — the caller is responsible for committing it in the same
transaction as the triggering appointment change, which is what makes
delivery durable rather than best-effort.

`NotificationDispatcher.run_once()` is a separate, decoupled step (intended
to run in a background worker/cron, not inline with a request) that attempts
delivery for PENDING rows and marks each SENT or FAILED with a retry count.
Rows are never deleted on failure, so failed deliveries stay visible/alertable.

Pending rows are selected with `SELECT ... FOR UPDATE SKIP LOCKED` so that
multiple dispatcher instances/workers can run `run_once()` concurrently
without double-delivering the same row (Phase 7 Code Review, Maintainability
finding #1).
"""

import uuid
from datetime import datetime, timezone
from typing import Callable

from sqlalchemy.orm import Session

from backend.models.appointment_notification_outbox import AppointmentNotificationOutbox
from backend.models.enums import NotificationOutboxStatus

MAX_ATTEMPTS = 5

SendFn = Callable[[AppointmentNotificationOutbox], bool]


def _default_send(_row: AppointmentNotificationOutbox) -> bool:
    """Placeholder delivery channel — replace with the real notification
    integration (email/SMS/push) when it exists. Returns False (never
    silently claims success) so failures are visible until a real channel
    is wired in."""
    return False


def enqueue(
    db: Session,
    appointment_id: uuid.UUID,
    event_type: str,
    payload: dict,
) -> AppointmentNotificationOutbox:
    row = AppointmentNotificationOutbox(
        appointment_id=appointment_id,
        event_type=event_type,
        payload=payload,
        status=NotificationOutboxStatus.PENDING.value,
    )
    db.add(row)
    db.flush()
    return row


class NotificationDispatcher:
    def __init__(self, db: Session, send_fn: SendFn = _default_send):
        self.db = db
        self.send_fn = send_fn

    def run_once(self) -> int:
        """Attempts delivery for every PENDING row. Returns count processed."""
        pending = (
            self.db.query(AppointmentNotificationOutbox)
            .filter(AppointmentNotificationOutbox.status == NotificationOutboxStatus.PENDING.value)
            .with_for_update(skip_locked=True)
            .all()
        )
        for row in pending:
            self._attempt(row)
        self.db.commit()
        return len(pending)

    def _attempt(self, row: AppointmentNotificationOutbox) -> None:
        row.attempt_count += 1
        row.last_attempted_at = datetime.now(timezone.utc)
        delivered = self.send_fn(row)
        if delivered:
            row.status = NotificationOutboxStatus.SENT.value
            row.delivered_at = datetime.now(timezone.utc)
        elif row.attempt_count >= MAX_ATTEMPTS:
            row.status = NotificationOutboxStatus.FAILED.value
        # else: stays PENDING for the next retry pass (backoff is enforced by
        # the caller's polling interval, not by this method).
