from fastapi import APIRouter
from app.schemas.train import TrainStateRequest
from app.db.mongodb import db
from datetime import datetime

router = APIRouter()

@router.post("/update")
async def update_simulation(request: TrainStateRequest):
    # Upsert simulated state
    doc = request.model_dump(mode="json")
    doc["simulated_at"] = datetime.utcnow().isoformat()
    
    await db.db["live_train_state"].update_one(
        {"train_number": request.train_number},
        {"$set": doc},
        upsert=True
    )
    
    return {"status": "success", "message": f"Simulated state updated for train {request.train_number}"}
