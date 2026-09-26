from copy import deepcopy
from datetime import datetime, timedelta, timezone

import jwt
import pytest

from fastapi.testclient import TestClient

from app.core.config import Settings, get_settings
from app.core.security import decode_access_token, hash_password, verify_password
from app.db.mongodb import db
from app.main import app


class FakeUsersCollection:
    def __init__(self):
        self.documents = {}

    async def find_one(self, query):
        return deepcopy(self.documents.get(query["username"]))

    async def insert_one(self, document):
        self.documents[document["username"]] = deepcopy(document)


class FakeDatabase:
    def __init__(self):
        self.users = FakeUsersCollection()

    def __getitem__(self, name):
        if name == "users":
            return self.users
        raise AssertionError(f"Unexpected collection: {name}")


def test_authentication_flow(monkeypatch):
    fake_database = FakeDatabase()
    monkeypatch.setattr(db, "db", fake_database)
    client = TestClient(app)

    registration = client.post(
        "/api/v1/auth/register",
        json={"username": "passenger1", "password": "correct-password"},
    )
    assert registration.status_code == 201
    assert registration.json()["role"] == "PASSENGER"
    assert "password" not in registration.json()

    login = client.post(
        "/api/v1/auth/login",
        json={"username": "passenger1", "password": "correct-password"},
    )
    assert login.status_code == 200
    token = login.json()["access_token"]
    assert login.json()["user"]["role"] == "PASSENGER"

    me = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200
    assert me.json()["username"] == "passenger1"


def test_authentication_rejects_invalid_credentials(monkeypatch):
    fake_database = FakeDatabase()
    fake_database.users.documents["passenger1"] = {
        "username": "passenger1",
        "password_hash": hash_password("correct-password"),
        "role": "PASSENGER",
        "full_name": None,
    }
    monkeypatch.setattr(db, "db", fake_database)
    client = TestClient(app)

    response = client.post(
        "/api/v1/auth/login",
        json={"username": "passenger1", "password": "wrong-password"},
    )
    assert response.status_code == 401


def test_rbac_blocks_passenger_from_simulation(monkeypatch):
    fake_database = FakeDatabase()
    fake_database.users.documents["passenger1"] = {
        "username": "passenger1",
        "password_hash": hash_password("correct-password"),
        "role": "PASSENGER",
        "full_name": None,
    }
    monkeypatch.setattr(db, "db", fake_database)
    client = TestClient(app)

    login = client.post(
        "/api/v1/auth/login",
        json={"username": "passenger1", "password": "correct-password"},
    )
    token = login.json()["access_token"]
    response = client.post(
        "/api/v1/simulation/update",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "train_number": "12345",
            "current_timestamp": "2026-09-24T12:00:00Z",
            "destination": "TestStation",
        },
    )
    assert response.status_code == 403


def test_protected_train_endpoint_requires_authentication(monkeypatch):
    fake_database = FakeDatabase()
    monkeypatch.setattr(db, "db", fake_database)
    client = TestClient(app)

    response = client.get("/api/v1/trains/12345/state")
    assert response.status_code == 401


def test_passwords_are_hashed_with_argon2():
    hashed = hash_password("correct-password")
    assert hashed.startswith("$argon2")
    assert verify_password("correct-password", hashed)
    assert not verify_password("wrong-password", hashed)


def test_expired_tokens_are_rejected():
    settings = get_settings()
    token = jwt.encode(
        {
            "sub": "passenger1",
            "role": "PASSENGER",
            "exp": datetime.now(timezone.utc) - timedelta(minutes=1),
        },
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )
    with pytest.raises(Exception) as error:
        decode_access_token(token)
    assert error.value.status_code == 401


def test_production_rejects_development_secrets():
    with pytest.raises(ValueError):
        Settings(ENVIRONMENT="production")


def test_cors_origins_are_parsed_from_configuration():
    settings = Settings(CORS_ORIGINS="https://railpulse.example, http://localhost:3000")
    assert settings.cors_origins == ["https://railpulse.example", "http://localhost:3000"]
