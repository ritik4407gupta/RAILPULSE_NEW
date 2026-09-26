from __future__ import annotations

from datetime import datetime
from typing import Mapping

import pandas as pd


NUMERIC_FEATURES = [
    "distance_remaining_km",
    "scheduled_travel_time_minutes",
    "scheduled_arrival_hour",
    "scheduled_arrival_minute",
    "departure_year",
    "departure_month",
    "departure_day_of_week",
]
CATEGORICAL_FEATURES = [
    "train_number",
    "train_type",
    "source",
    "destination",
    "season",
    "run_frequency",
]
FEATURE_COLUMNS = NUMERIC_FEATURES + CATEGORICAL_FEATURES


def parse_time_minutes(value: object) -> float:
    text = str(value).strip().split()[-1]
    try:
        parsed = datetime.strptime(text, "%H:%M:%S")
    except ValueError:
        try:
            parsed = datetime.strptime(text, "%H:%M")
        except ValueError:
            return 0.0
    return parsed.hour * 60 + parsed.minute + parsed.second / 60.0


def parse_datetime(value: object) -> datetime:
    parsed = pd.to_datetime(value, dayfirst=True, errors="coerce")
    if pd.isna(parsed):
        return datetime(2000, 1, 1)
    return parsed.to_pydatetime()


def engineer_features(row: Mapping[str, object]) -> dict:
    event_time = parse_datetime(row.get("event_time", row.get("Date")))
    scheduled_arrival = parse_time_minutes(
        row.get("scheduled_arrival", row.get("Sc_arr__time", "00:00:00"))
    )
    distance = float(row.get("distance_remaining_km", row.get("Distance(Km)", 0.0)) or 0.0)

    return {
        "distance_remaining_km": distance,
        "scheduled_travel_time_minutes": distance,
        "scheduled_arrival_hour": int(scheduled_arrival // 60),
        "scheduled_arrival_minute": int(scheduled_arrival % 60),
        "departure_year": event_time.year,
        "departure_month": event_time.month,
        "departure_day_of_week": event_time.weekday(),
        "train_number": str(row.get("train_number", row.get("Train_no", "Unknown"))),
        "train_type": str(row.get("train_type", "Express") or "Unknown"),
        "source": str(row.get("source", row.get("Source", "Unknown")) or "Unknown"),
        "destination": str(
            row.get("destination", row.get("Destitnation", "Unknown")) or "Unknown"
        ),
        "season": str(row.get("season", row.get("Season", "Unknown")) or "Unknown"),
        "run_frequency": str(
            row.get("run_frequency", row.get("Run_frequency", "Unknown")) or "Unknown"
        ),
    }


def build_inference_features(request) -> dict:
    scheduled_arrival = request.scheduled_arrival or request.current_timestamp
    return engineer_features(
        {
            "event_time": request.current_timestamp,
            "scheduled_arrival": scheduled_arrival,
            "distance_remaining_km": request.distance_remaining_km or 0.0,
            "train_number": request.train_number,
            "train_type": request.train_type or "Unknown",
            "source": request.source or "Unknown",
            "destination": request.destination,
            "season": request.season or "Unknown",
            "run_frequency": request.run_frequency or "Unknown",
        }
    )


def feature_frame(rows: list[Mapping[str, object]]) -> pd.DataFrame:
    frame = pd.DataFrame([engineer_features(row) for row in rows])
    return frame.loc[:, FEATURE_COLUMNS]
