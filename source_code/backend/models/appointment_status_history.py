from sqlalchemy import Column, DateTime, ForeignKey, Text, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from backend.database import Base


class AppointmentStatusHistory(Base):
    """Append-only audit trail (NFR-018). No update/delete repository method
    should ever target this model."""

    __tablename__ = "appointment_status_history"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    appointment_id = Column(UUID(as_uuid=True), ForeignKey("appointments.id"), nullable=False)
    from_status = Column(Text, nullable=True)
    to_status = Column(Text, nullable=False)
    # Not a FK: the HMS users/identity module does not exist in this workspace
    # yet (see artifacts/database/HMS-6-database-design.md, Key Design Decisions #4).
    actor_id = Column(UUID(as_uuid=True), nullable=False)
    reason = Column(Text, nullable=True)
    changed_at = Column(DateTime(timezone=True), nullable=False, server_default=text("now()"))

    appointment = relationship("Appointment", back_populates="status_history")
