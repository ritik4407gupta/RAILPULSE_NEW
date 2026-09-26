from datetime import datetime, timezone
from typing import Any

from app.db.mongodb import db


async def upsert_live_state(train_number: str, state: dict[str, Any]) -> datetime:
    updated_at = datetime.now(timezone.utc)
    document = {**state, "train_number": train_number, "state_source": "live", "updated_at": updated_at}
    await db.db["live_train_state"].update_one(
        {"train_number": train_number}, {"$set": document}, upsert=True
    )
    return updated_at


async def get_live_state(train_number: str) -> dict[str, Any] | None:
    document = await db.db["live_train_state"].find_one({"train_number": train_number})
    if document:
        document.pop("_id", None)
    return document


async def upsert_simulation_state(train_number: str, state: dict[str, Any]) -> datetime:
    simulated_at = datetime.now(timezone.utc)
    document = {
        **state,
        "train_number": train_number,
        "state_source": "simulation",
        "simulated_at": simulated_at,
    }
    await db.db["simulation_states"].update_one(
        {"train_number": train_number}, {"$set": document}, upsert=True
    )
    return simulated_at
