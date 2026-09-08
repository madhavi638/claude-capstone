import uuid
from datetime import datetime

from pydantic import BaseModel, Field, model_validator

from backend.models.enums import AppointmentStatus


class AppointmentCreateRequest(BaseModel):
    patient_id: uuid.UUID
    provider_id: uuid.UUID
    start_time: datetime
    end_time: datetime

    @model_validator(mode="after")
    def _check_time_range(self):
        if self.start_time >= self.end_time:
            raise ValueError("start_time must be before end_time")
        return self


class AppointmentRescheduleRequest(BaseModel):
    start_time: datetime
    end_time: datetime

    @model_validator(mode="after")
    def _check_time_range(self):
        if self.start_time >= self.end_time:
            raise ValueError("start_time must be before end_time")
        return self


class AppointmentCancelRequest(BaseModel):
    reason: str | None = None


class AppointmentResponse(BaseModel):
    id: uuid.UUID
    patient_id: uuid.UUID
    provider_id: uuid.UUID
    start_time: datetime
    end_time: datetime
    status: AppointmentStatus
    cancellation_reason: str | None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AppointmentStatusHistoryResponse(BaseModel):
    id: uuid.UUID
    from_status: AppointmentStatus | None
    to_status: AppointmentStatus
    actor_id: uuid.UUID
    reason: str | None
    changed_at: datetime

    class Config:
        from_attributes = True


class AppointmentListResponse(BaseModel):
    items: list[AppointmentResponse]
    page_size: int
    offset: int


DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100


class PaginationParams(BaseModel):
    offset: int = Field(default=0, ge=0)
    page_size: int = Field(default=DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE)
