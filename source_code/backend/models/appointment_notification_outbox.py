from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, text
from sqlalchemy.dialects.postgresql import JSONB, UUID

from backend.database import Base


class AppointmentNotificationOutbox(Base):
    """Durable outbox row for BR-013 notification delivery (Design Review
    Recommendation 2). Written in the same transaction as the triggering
    appointment change; dispatched separately. Never deleted on failure."""

    __tablename__ = "appointment_notification_outbox"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    appointment_id = Column(UUID(as_uuid=True), ForeignKey("appointments.id"), nullable=False)
    event_type = Column(String, nullable=False)
    payload = Column(JSONB, nullable=False)
    status = Column(String, nullable=False, server_default="PENDING")
    attempt_count = Column(Integer, nullable=False, server_default="0")
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=text("now()"))
    last_attempted_at = Column(DateTime(timezone=True), nullable=True)
    delivered_at = Column(DateTime(timezone=True), nullable=True)
