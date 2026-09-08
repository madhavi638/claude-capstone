"""Auth principal contract for the appointment module.

STUB IMPLEMENTATION — see artifacts/review/HMS-6-design-review.md (Security
Review, High risk) and artifacts/implementation/HMS-6-impl-manifest.md
(TASK-003). No HMS identity/user module exists in this workspace yet. This
module defines the minimal contract the Appointment service needs from
whatever identity provider eventually replaces it (a `user_id` and a `role`),
and provides a placeholder extraction mechanism so authorization logic can be
built and tested now. This MUST be replaced before production deployment —
tracked as a High risk follow-up, not treated as a finished integration.
"""

import uuid
from dataclasses import dataclass
from typing import Literal

from fastapi import Header, HTTPException, status

Role = Literal["patient", "provider", "staff"]

_VALID_ROLES = {"patient", "provider", "staff"}


@dataclass(frozen=True)
class AuthPrincipal:
    user_id: uuid.UUID
    role: Role


def get_current_principal(authorization: str = Header(default=None)) -> AuthPrincipal:
    """Extracts an AuthPrincipal from a stub bearer token of the form
    `Bearer <user_id>:<role>`.

    This is a placeholder for the real identity module's token verification.
    It intentionally does not perform signature validation — it exists only
    to give downstream code (TASK-007/TASK-008) a concrete, testable contract
    to authorize against.
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing or malformed Authorization header")

    token = authorization[len("Bearer "):]
    parts = token.split(":", 1)
    if len(parts) != 2:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Malformed stub token")

    raw_user_id, raw_role = parts
    try:
        user_id = uuid.UUID(raw_user_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Malformed user id in token")

    if raw_role not in _VALID_ROLES:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unknown role in token")

    return AuthPrincipal(user_id=user_id, role=raw_role)  # type: ignore[arg-type]
