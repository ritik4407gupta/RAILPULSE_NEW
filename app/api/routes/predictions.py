from fastapi import APIRouter, HTTPException, Depends
from app.schemas.train import TrainStateRequest
from app.schemas.prediction import PredictionResponse
from app.services.eta_service import calculate_eta
from app.db.mongodb import db
import logging
from datetime import datetime

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/eta", response_model=PredictionResponse)
async def predict_eta(request: TrainStateRequest):
    try:
        response = await calculate_eta(request)
        
        # Save prediction and input to MongoDB
        prediction_doc = {
            "train_number": request.train_number,
            "timestamp": datetime.utcnow(),
            "model_version": response.model_version,
            "input_snapshot": request.model_dump(mode="json"),
            "predicted_eta": response.predicted_eta,
            "predicted_remaining_minutes": response.predicted_remaining_minutes,
            "predicted_delay_minutes": response.predicted_delay_minutes,
            "delay_category": response.delay_category
        }
        await db.db["predictions"].insert_one(prediction_doc)
        
        # Upsert live train state
        await db.db["live_train_state"].update_one(
            {"train_number": request.train_number},
            {"$set": request.model_dump(mode="json")},
            upsert=True
        )
        
        return response
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        logger.error(f"Internal error during prediction: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
