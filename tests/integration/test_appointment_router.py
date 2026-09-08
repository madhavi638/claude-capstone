from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient

from backend.database import get_db
from backend.main import app


@pytest.fixture()
def client(db_session):
    def _override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


def _auth_header(user_id, role):
    return {"Authorization": f"Bearer {user_id}:{role}"}


def _slot():
    start = datetime.now(timezone.utc) + timedelta(hours=1)
    return start.isoformat(), (start + timedelta(minutes=30)).isoformat()


def test_book_appointment_happy_path(client, patient, provider):
    start, end = _slot()
    resp = client.post(
        "/api/v1/appointments",
        json={
            "patient_id": str(patient.id),
            "provider_id": str(provider.id),
            "start_time": start,
            "end_time": end,
        },
        headers=_auth_header(patient.id, "patient"),
    )
    assert resp.status_code == 201
    assert resp.json()["status"] == "SCHEDULED"


def test_book_appointment_missing_auth_returns_401(client, patient, provider):
    start, end = _slot()
    resp = client.post(
        "/api/v1/appointments",
        json={
            "patient_id": str(patient.id),
            "provider_id": str(provider.id),
            "start_time": start,
            "end_time": end,
        },
    )
    assert resp.status_code == 401


def test_double_booking_returns_409(client, patient, provider):
    start, end = _slot()
    body = {
        "patient_id": str(patient.id),
        "provider_id": str(provider.id),
        "start_time": start,
        "end_time": end,
    }
    headers = _auth_header(patient.id, "patient")
    first = client.post("/api/v1/appointments", json=body, headers=headers)
    assert first.status_code == 201

    second = client.post(
        "/api/v1/appointments",
        json={**body, "patient_id": str(patient.id)},
        headers=headers,
    )
    assert second.status_code == 409


def test_listing_rejects_page_size_over_max(client, patient):
    resp = client.get(
        f"/api/v1/appointments?patient_id={patient.id}&page_size=101",
        headers=_auth_header(patient.id, "patient"),
    )
    assert resp.status_code == 422


def test_listing_defaults_page_size(client, patient):
    resp = client.get(
        f"/api/v1/appointments?patient_id={patient.id}",
        headers=_auth_header(patient.id, "patient"),
    )
    assert resp.status_code == 200
    assert resp.json()["page_size"] == 20


def test_patient_forbidden_from_listing_other_patient(client, patient):
    other_patient_id = "00000000-0000-0000-0000-000000000000"
    resp = client.get(
        f"/api/v1/appointments?patient_id={other_patient_id}",
        headers=_auth_header(patient.id, "patient"),
    )
    assert resp.status_code == 403
