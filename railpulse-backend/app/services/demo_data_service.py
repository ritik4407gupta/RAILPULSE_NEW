from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from app.db.mongodb import db
from app.schemas.train import TrainStateRequest

DEMO_TRAIN_SPECS: dict[str, dict[str, Any]] = {
    "12301": {
        "train_type": "Rajdhani",
        "source": "New Delhi",
        "destination": "Mumbai Central",
        "current_station": "Mathura",
        "current_section": "Mathura–Agra",
        "distance_remaining_km": 640.0,
        "current_speed_kmph": 78.0,
        "current_delay_minutes": 18.0,
        "scheduled_travel_time_minutes": 920.0,
        "elapsed_travel_time_minutes": 420.0,
        "historical_route_delay_minutes": 15.0,
        "historical_station_delay_minutes": 9.0,
        "historical_section_time_minutes": 118.0,
        "dwell_time_minutes": 8.0,
        "track_occupancy": 0.68,
        "junction_congestion": 0.52,
        "platform_availability": 0.91,
        "trains_in_section": 4,
        "season": "MONSOON",
        "run_frequency": "DAILY",
    },
    "12951": {
        "train_type": "Rajdhani",
        "source": "Mumbai Central",
        "destination": "New Delhi",
        "current_station": "Kota",
        "current_section": "Kota–Mathura",
        "distance_remaining_km": 488.0,
        "current_speed_kmph": 71.0,
        "current_delay_minutes": 11.0,
        "scheduled_travel_time_minutes": 860.0,
        "elapsed_travel_time_minutes": 360.0,
        "historical_route_delay_minutes": 12.0,
        "historical_station_delay_minutes": 7.0,
        "historical_section_time_minutes": 104.0,
        "dwell_time_minutes": 7.0,
        "track_occupancy": 0.63,
        "junction_congestion": 0.48,
        "platform_availability": 0.88,
        "trains_in_section": 3,
        "season": "SUMMER",
        "run_frequency": "DAILY",
    },
    "12002": {
        "train_type": "Shatabdi",
        "source": "New Delhi",
        "destination": "Bhopal",
        "current_station": "Jhansi",
        "current_section": "Jhansi–Bhopal",
        "distance_remaining_km": 240.0,
        "current_speed_kmph": 92.0,
        "current_delay_minutes": 5.0,
        "scheduled_travel_time_minutes": 390.0,
        "elapsed_travel_time_minutes": 230.0,
        "historical_route_delay_minutes": 6.0,
        "historical_station_delay_minutes": 4.0,
        "historical_section_time_minutes": 75.0,
        "dwell_time_minutes": 5.0,
        "track_occupancy": 0.55,
        "junction_congestion": 0.36,
        "platform_availability": 0.94,
        "trains_in_section": 2,
        "season": "AUTUMN",
        "run_frequency": "DAILY",
    },
    "12952": {
        "train_type": "Rajdhani",
        "source": "Mumbai Central",
        "destination": "New Delhi",
        "current_station": "Vadodara",
        "current_section": "Vadodara–Delhi",
        "distance_remaining_km": 760.0,
        "current_speed_kmph": 68.0,
        "current_delay_minutes": 22.0,
        "scheduled_travel_time_minutes": 980.0,
        "elapsed_travel_time_minutes": 500.0,
        "historical_route_delay_minutes": 17.0,
        "historical_station_delay_minutes": 11.0,
        "historical_section_time_minutes": 126.0,
        "dwell_time_minutes": 9.0,
        "track_occupancy": 0.72,
        "junction_congestion": 0.58,
        "platform_availability": 0.84,
        "trains_in_section": 5,
        "season": "MONSOON",
        "run_frequency": "DAILY",
    },
    "12259": {
        "train_type": "Duronto",
        "source": "Sealdah",
        "destination": "New Delhi",
        "current_station": "Bhopal",
        "current_section": "Bhopal–Patna",
        "distance_remaining_km": 540.0,
        "current_speed_kmph": 86.0,
        "current_delay_minutes": 14.0,
        "scheduled_travel_time_minutes": 740.0,
        "elapsed_travel_time_minutes": 330.0,
        "historical_route_delay_minutes": 10.0,
        "historical_station_delay_minutes": 8.0,
        "historical_section_time_minutes": 92.0,
        "dwell_time_minutes": 6.0,
        "track_occupancy": 0.6,
        "junction_congestion": 0.44,
        "platform_availability": 0.9,
        "trains_in_section": 3,
        "season": "WINTER",
        "run_frequency": "WEEKLY",
    },
}


def _demo_timestamp(offset_minutes: int = 0, base_time: datetime | None = None) -> datetime:
    base = base_time or datetime.now(timezone.utc)
    return base + timedelta(minutes=offset_minutes)


def _build_demo_state(train_number: str, base_time: datetime | None = None, delay_shift: int = 0) -> dict[str, Any]:
    spec = DEMO_TRAIN_SPECS[train_number]
    current_ts = base_time or datetime.now(timezone.utc)
    scheduled_arrival = current_ts + timedelta(minutes=int(spec["scheduled_travel_time_minutes"] - spec["elapsed_travel_time_minutes"]))
    reduced_delay = max(0.0, float(spec["current_delay_minutes"]) + float(delay_shift))
    return {
        "train_number": train_number,
        "train_type": spec["train_type"],
        "train_priority": 3,
        "current_timestamp": current_ts,
        "current_station": spec["current_station"],
        "current_section": spec["current_section"],
        "destination": spec["destination"],
        "distance_remaining_km": float(spec["distance_remaining_km"]),
        "current_speed_kmph": float(spec["current_speed_kmph"]),
        "current_delay_minutes": reduced_delay,
        "scheduled_arrival": scheduled_arrival,
        "scheduled_travel_time_minutes": float(spec["scheduled_travel_time_minutes"]),
        "elapsed_travel_time_minutes": float(spec["elapsed_travel_time_minutes"]),
        "historical_route_delay_minutes": float(spec["historical_route_delay_minutes"]),
        "historical_station_delay_minutes": float(spec["historical_station_delay_minutes"]),
        "historical_section_time_minutes": float(spec["historical_section_time_minutes"]),
        "dwell_time_minutes": float(spec["dwell_time_minutes"]),
        "track_occupancy": float(spec["track_occupancy"]),
        "junction_congestion": float(spec["junction_congestion"]),
        "platform_availability": float(spec["platform_availability"]),
        "trains_in_section": int(spec["trains_in_section"]),
        "source": spec["source"],
        "season": spec["season"],
        "run_frequency": spec["run_frequency"],
        "data_source": "DEMO",
        "state_source": "live",
        "updated_at": current_ts,
    }


def generate_demo_train_state(train_number: str, current_timestamp: datetime | None = None, delay_shift: int = 0) -> TrainStateRequest:
    payload = _build_demo_state(train_number, current_timestamp, delay_shift)
    return TrainStateRequest(**payload)


def generate_demo_trains(current_timestamp: datetime | None = None) -> list[TrainStateRequest]:
    base = current_timestamp or datetime.now(timezone.utc)
    return [
        generate_demo_train_state(train_number, base, delay_shift=(index * 2))
        for index, train_number in enumerate(DEMO_TRAIN_SPECS.keys())
    ]


async def seed_demo_trains(current_timestamp: datetime | None = None) -> dict[str, Any]:
    base = current_timestamp or datetime.now(timezone.utc)
    collection = db.db["live_train_state"]
    created_count = 0
    updated_count = 0
    trains: list[str] = []

    for train_number in DEMO_TRAIN_SPECS:
        existing = await collection.find_one({"train_number": train_number})
        payload = _build_demo_state(train_number, base)
        document = {**payload, "train_number": train_number}
        await collection.update_one({"train_number": train_number}, {"$set": document}, upsert=True)
        trains.append(train_number)
        if existing:
            updated_count += 1
        else:
            created_count += 1

    total_count = len(trains)
    return {
        "success": True,
        "created_count": created_count,
        "updated_count": updated_count,
        "seeded_count": total_count,
        "total_count": total_count,
        "trains": trains,
        "message": "Demo live train data seeded successfully",
    }


async def refresh_demo_trains(current_timestamp: datetime | None = None) -> dict[str, Any]:
    base = current_timestamp or datetime.now(timezone.utc)
    collection = db.db["live_train_state"]
    refreshed: list[str] = []

    for index, train_number in enumerate(DEMO_TRAIN_SPECS):
        existing = await collection.find_one({"train_number": train_number, "data_source": "DEMO"})
        if not existing:
            continue
        payload = _build_demo_state(train_number, base, delay_shift=(index + 2) * 3)
        await collection.update_one({"train_number": train_number}, {"$set": {**payload, "train_number": train_number}}, upsert=True)
        refreshed.append(train_number)

    return {
        "success": True,
        "updated_count": len(refreshed),
        "trains": refreshed,
        "message": "Demo live train data refreshed successfully",
    }


async def reset_demo_trains() -> dict[str, Any]:
    collection = db.db["live_train_state"]
    result = await collection.delete_many({"data_source": "DEMO"})
    deleted_count = getattr(result, "deleted_count", 0) or 0
    return {
        "success": True,
        "deleted_count": deleted_count,
        "message": "Demo data cleared successfully",
    }


async def list_live_trains(limit: int = 1000) -> list[dict[str, Any]]:
    collection = db.db["live_train_state"]
    documents = await collection.find({}).sort("train_number", 1).to_list(length=limit)
    results: list[dict[str, Any]] = []
    for document in documents:
        item = dict(document)
        item.pop("_id", None)
        if not item.get("train_number"):
            continue
        sanitized = {
            "train_number": item.get("train_number"),
            "train_type": item.get("train_type"),
            "source": item.get("source"),
            "destination": item.get("destination"),
            "current_station": item.get("current_station"),
            "current_section": item.get("current_section"),
            "current_delay_minutes": item.get("current_delay_minutes", 0),
            "current_speed_kmph": item.get("current_speed_kmph", 0),
            "distance_remaining_km": item.get("distance_remaining_km"),
            "scheduled_arrival": item.get("scheduled_arrival"),
            "data_source": item.get("data_source", "LIVE"),
            "updated_at": item.get("updated_at"),
        }
        results.append(sanitized)
    return results
