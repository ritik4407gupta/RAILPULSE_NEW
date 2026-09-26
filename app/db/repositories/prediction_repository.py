from datetime import datetime, timezone
from typing import Any

from app.db.mongodb import db


async def save_prediction(document: dict[str, Any]) -> None:
    await db.db["predictions"].insert_one(document)


async def list_predictions(train_number: str, limit: int, skip: int) -> tuple[list[dict[str, Any]], int]:
    collection = db.db["predictions"]
    cursor = collection.find({"train_number": train_number}).sort("timestamp", -1).skip(skip).limit(limit)
    predictions = await cursor.to_list(length=limit)
    for prediction in predictions:
        prediction.pop("_id", None)
    total = await collection.count_documents({"train_number": train_number})
    return predictions, total


async def get_latest_prediction(train_number: str) -> dict[str, Any] | None:
    prediction = await db.db["predictions"].find_one(
        {"train_number": train_number}, sort=[("timestamp", -1)]
    )
    if prediction:
        prediction.pop("_id", None)
    return prediction


def prediction_timestamp() -> datetime:
    return datetime.now(timezone.utc)
