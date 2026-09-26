from typing import Any

from app.db.mongodb import db


async def list_alerts(train_number: str | None, limit: int) -> list[dict[str, Any]]:
    query = {"train_number": train_number} if train_number else {}
    cursor = db.db["alerts"].find(query).sort("created_at", -1).limit(limit)
    alerts = await cursor.to_list(length=limit)
    for alert in alerts:
        alert.pop("_id", None)
    return alerts
