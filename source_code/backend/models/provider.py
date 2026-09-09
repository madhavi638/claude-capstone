from sqlalchemy import Column, DateTime, String, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from backend.database import Base


class Provider(Base):
    """Placeholder model — owned by the (not-yet-built) HMS provider module.

    Minimal stand-in so `appointments` has a valid FK target. Do not treat as
    the authoritative provider schema; reconcile when the real module exists.
    """

    __tablename__ = "providers"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    full_name = Column(String, nullable=False)
    specialty = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=text("now()"))

    appointments = relationship("Appointment", back_populates="provider")
