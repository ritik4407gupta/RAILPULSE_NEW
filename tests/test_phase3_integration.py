from copy import deepcopy
from datetime import datetime, timezone

from fastapi.testclient import TestClient

from app.core.security import hash_password
from app.db.mongodb import db
from app.main import app


class FakeCursor:
    def __init__(self, documents):
        self.documents = documents

    def sort(self, field, direction):
        self.documents.sort(key=lambda item: item.get(field, datetime.min), reverse=direction < 0)
        return self

    def skip(self, amount):
        self.documents = self.documents[amount:]
        return self

    def limit(self, amount):
        self.documents = self.documents[:amount]
        return self

    async def to_list(self, length):
        return deepcopy(self.documents[:length])


class FakeCollection:
    def __init__(self):
        self.documents = []

    async def find_one(self, query, sort=None):
        matches = [document for document in self.documents if all(document.get(k) == v for k, v in query.items())]
        if sort and matches:
            field, direction = sort[0]
            matches.sort(key=lambda item: item.get(field, datetime.min), reverse=direction < 0)
        return deepcopy(matches[0]) if matches else None

    async def insert_one(self, document):
        self.documents.append(deepcopy(document))

    async def update_one(self, query, update, upsert=False):
        existing = next((document for document in self.documents if all(document.get(k) == v for k, v in query.items())), None)
        if existing is None:
            if upsert:
                self.documents.append({**query, **deepcopy(update["$set"])})
        else:
            existing.update(deepcopy(update["$set"]))

    def find(self, query):
        return FakeCursor([
            document for document in self.documents if all(document.get(k) == v for k, v in query.items())
        ])

    async def count_documents(self, query):
        return len([document for document in self.documents if all(document.get(k) == v for k, v in query.items())])

    async def create_index(self, *args, **kwargs):
        return "index"


class FakeDatabase:
    def __init__(self):
        self.collections = {name: FakeCollection() for name in (
            "users", "live_train_state", "simulation_states", "predictions", "alerts"
        )}

    def __getitem__(self, name):
        return self.collections[name]

    async def command(self, command):
        return {"ok": 1}


def make_client(monkeypatch):
    fake_database = FakeDatabase()
    fake_database["users"].documents.append({
        "username": "staff1",
        "password_hash": hash_password("correct-password"),
        "role": "STAFF",
        "full_name": None,
    })
    monkeypatch.setattr(db, "db", fake_database)
    client = TestClient(app)
    login = client.post(
        "/api/v1/auth/login",
        json={"username": "staff1", "password": "correct-password"},
    )
    return client, fake_database, {"Authorization": f"Bearer {login.json()['access_token']}"}


def test_phase3_documented_and_future_capabilities(monkeypatch):
    client, _, headers = make_client(monkeypatch)

    catalog = client.get("/api/v1/docs/capabilities")
    assert catalog.status_code == 200
    assert "upcoming_station_eta" in catalog.json()["future_data_required"]

    station_etas = client.get("/api/v1/trains/12345/upcoming-stations", headers=headers)
    assert station_etas.status_code == 200
    assert station_etas.json()["status"] == "future_data_required"
    assert station_etas.json()["upcoming_stations"] == []

    propagation = client.get("/api/v1/network/trains/12345/delay-propagation", headers=headers)
    assert propagation.status_code == 200
    assert propagation.json()["status"] == "future_data_required"
    assert propagation.json()["affected_trains"] == []

    risk = client.get("/api/v1/network/trains/12345/operational-risk", headers=headers)
    assert risk.status_code == 200
    assert risk.json()["status"] == "future_data_required"


def test_simulation_is_separate_from_live_state(monkeypatch):
    client, fake_database, headers = make_client(monkeypatch)
    payload = {
        "train_number": "12345",
        "current_timestamp": "2026-09-25T12:00:00Z",
        "destination": "TestStation",
    }

    simulation = client.post("/api/v1/simulation/update", json=payload, headers=headers)
    assert simulation.status_code == 200
    assert len(fake_database["simulation_states"].documents) == 1
    assert fake_database["live_train_state"].documents == []


def test_prediction_history_is_paginated(monkeypatch):
    client, fake_database, headers = make_client(monkeypatch)
    timestamp = datetime.now(timezone.utc)
    fake_database["predictions"].documents.extend([
        {"train_number": "12345", "timestamp": timestamp, "predicted_delay_minutes": 2},
        {"train_number": "12345", "timestamp": timestamp, "predicted_delay_minutes": 7},
    ])

    response = client.get(
        "/api/v1/trains/12345/predictions?limit=1&skip=0",
        headers=headers,
    )
    assert response.status_code == 200
    assert response.json()["total"] == 2
    assert len(response.json()["predictions"]) == 1


def test_network_intelligence_requires_staff_or_admin(monkeypatch):
    fake_database = FakeDatabase()
    fake_database["users"].documents.append({
        "username": "passenger1",
        "password_hash": hash_password("correct-password"),
        "role": "PASSENGER",
        "full_name": None,
    })
    monkeypatch.setattr(db, "db", fake_database)
    client = TestClient(app)
    login = client.post(
        "/api/v1/auth/login",
        json={"username": "passenger1", "password": "correct-password"},
    )
    response = client.get(
        "/api/v1/network/trains/12345/operational-risk",
        headers={"Authorization": f"Bearer {login.json()['access_token']}"},
    )
    assert response.status_code == 403
