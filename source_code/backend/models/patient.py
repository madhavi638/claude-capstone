from sqlalchemy import Column, DateTime, String, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from backend.database import Base


class Patient(Base):
    """Placeholder model — owned by the (not-yet-built) HMS patient module.

    Minimal stand-in so `appointments` has a valid FK target. Do not treat as
    the authoritative patient schema; reconcile when the real module exists.
    """

    __tablename__ = "patients"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    full_name = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=text("now()"))

    appointments = relationship("Appointment", back_populates="patient")
