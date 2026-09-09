import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from backend.auth.principal import AuthPrincipal, get_current_principal
from backend.database import get_db
from backend.domain.errors import (
    AuthorizationError,
    InvalidStatusTransitionError,
    NotFoundError,
    SlotConflictError,
)
from backend.models.enums import AppointmentStatus
from backend.schemas.appointment import (
    DEFAULT_PAGE_SIZE,
    MAX_PAGE_SIZE,
    AppointmentCancelRequest,
    AppointmentCreateRequest,
    AppointmentListResponse,
    AppointmentRescheduleRequest,
    AppointmentResponse,
    AppointmentStatusHistoryResponse,
)
from backend.services.appointment_service import AppointmentService

router = APIRouter(prefix="/api/v1/appointments", tags=["appointments"])

_ERROR_STATUS_MAP = {
    SlotConflictError: status.HTTP_409_CONFLICT,
    InvalidStatusTransitionError: status.HTTP_409_CONFLICT,
    AuthorizationError: status.HTTP_403_FORBIDDEN,
    NotFoundError: status.HTTP_404_NOT_FOUND,
}


def _service(db: Session = Depends(get_db)) -> AppointmentService:
    return AppointmentService(db)


def _as_http_error(exc: Exception) -> HTTPException:
    return HTTPException(status_code=_ERROR_STATUS_MAP[type(exc)], detail=str(exc))


@router.post("", response_model=AppointmentResponse, status_code=status.HTTP_201_CREATED)
def book_appointment(
    body: AppointmentCreateRequest,
    principal: AuthPrincipal = Depends(get_current_principal),
    service: AppointmentService = Depends(_service),
):
    try:
        return service.book_appointment(
            principal, body.patient_id, body.provider_id, body.start_time, body.end_time
        )
    except (SlotConflictError, AuthorizationError) as exc:
        raise _as_http_error(exc)


@router.get("/{appointment_id}", response_model=AppointmentResponse)
def get_appointment(
    appointment_id: uuid.UUID,
    principal: AuthPrincipal = Depends(get_current_principal),
    service: AppointmentService = Depends(_service),
):
    try:
        return service.get_appointment(principal, appointment_id)
    except (AuthorizationError, NotFoundError) as exc:
        raise _as_http_error(exc)


@router.get("", response_model=AppointmentListResponse)
def list_appointments(
    patient_id: uuid.UUID | None = None,
    provider_id: uuid.UUID | None = None,
    status_filter: AppointmentStatus | None = Query(default=None, alias="status"),
    offset: int = Query(default=0, ge=0),
    page_size: int = Query(default=DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE),
    principal: AuthPrincipal = Depends(get_current_principal),
    service: AppointmentService = Depends(_service),
):
    if not patient_id and not provider_id:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Either patient_id or provider_id is required",
        )
    try:
        if patient_id:
            items = service.list_for_patient(principal, patient_id, status_filter, offset, page_size)
        else:
            items = service.list_for_provider(principal, provider_id, status_filter, offset, page_size)
    except AuthorizationError as exc:
        raise _as_http_error(exc)

    return AppointmentListResponse(items=items, page_size=page_size, offset=offset)


@router.patch("/{appointment_id}/reschedule", response_model=AppointmentResponse)
def reschedule_appointment(
    appointment_id: uuid.UUID,
    body: AppointmentRescheduleRequest,
    principal: AuthPrincipal = Depends(get_current_principal),
    service: AppointmentService = Depends(_service),
):
    try:
        return service.reschedule_appointment(principal, appointment_id, body.start_time, body.end_time)
    except (SlotConflictError, InvalidStatusTransitionError, AuthorizationError, NotFoundError) as exc:
        raise _as_http_error(exc)


@router.post("/{appointment_id}/cancel", response_model=AppointmentResponse)
def cancel_appointment(
    appointment_id: uuid.UUID,
    body: AppointmentCancelRequest,
    principal: AuthPrincipal = Depends(get_current_principal),
    service: AppointmentService = Depends(_service),
):
    try:
        return service.cancel_appointment(principal, appointment_id, body.reason)
    except (InvalidStatusTransitionError, AuthorizationError, NotFoundError) as exc:
        raise _as_http_error(exc)


@router.get("/{appointment_id}/history", response_model=list[AppointmentStatusHistoryResponse])
def get_appointment_history(
    appointment_id: uuid.UUID,
    principal: AuthPrincipal = Depends(get_current_principal),
    service: AppointmentService = Depends(_service),
):
    try:
        return service.get_history(principal, appointment_id)
    except (AuthorizationError, NotFoundError) as exc:
        raise _as_http_error(exc)
