from fastapi import APIRouter, HTTPException
from app.db.mongodb import db

router = APIRouter()

@router.get("/{train_number}/state")
async def get_train_state(train_number: str):
    state = await db.db["live_train_state"].find_one({"train_number": train_number})
    if not state:
        raise HTTPException(status_code=404, detail="Train state not found")
    
    # Remove MongoDB ID
    state.pop("_id", None)
    return state

@router.get("/{train_number}/predictions/latest")
async def get_latest_prediction(train_number: str):
    prediction = await db.db["predictions"].find_one(
        {"train_number": train_number},
        sort=[("timestamp", -1)]
    )
    if not prediction:
        raise HTTPException(status_code=404, detail="No predictions found for this train")
        
    prediction.pop("_id", None)
    return prediction
