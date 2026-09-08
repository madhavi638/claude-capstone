import uuid

import pytest
from fastapi import HTTPException

from backend.auth.principal import get_current_principal


def test_missing_header_raises_401():
    with pytest.raises(HTTPException) as exc_info:
        get_current_principal(authorization=None)
    assert exc_info.value.status_code == 401


def test_malformed_scheme_raises_401():
    with pytest.raises(HTTPException) as exc_info:
        get_current_principal(authorization="Basic abc123")
    assert exc_info.value.status_code == 401


def test_malformed_token_raises_401():
    with pytest.raises(HTTPException) as exc_info:
        get_current_principal(authorization="Bearer not-a-valid-token")
    assert exc_info.value.status_code == 401


def test_unknown_role_raises_401():
    user_id = uuid.uuid4()
    with pytest.raises(HTTPException) as exc_info:
        get_current_principal(authorization=f"Bearer {user_id}:superadmin")
    assert exc_info.value.status_code == 401


def test_valid_token_resolves_principal():
    user_id = uuid.uuid4()
    principal = get_current_principal(authorization=f"Bearer {user_id}:patient")
    assert principal.user_id == user_id
    assert principal.role == "patient"
