from fastapi import APIRouter, Depends, HTTPException
from app.api.dependencies import get_current_user
from app.schemas.train import TrainStateRequest
from app.schemas.prediction import PredictionResponse
from app.services.eta_service import calculate_eta
from app.db.repositories.prediction_repository import prediction_timestamp, save_prediction
from app.db.repositories.train_repository import upsert_live_state
import logging
from datetime import datetime

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/eta", response_model=PredictionResponse)
async def predict_eta(request: TrainStateRequest, current_user: dict = Depends(get_current_user)):
    try:
        response = await calculate_eta(request)
        
        # Save prediction and input to MongoDB
        prediction_doc = {
            "train_number": request.train_number,
            "timestamp": prediction_timestamp(),
            "model_version": response.model_version,
            "input_snapshot": request.model_dump(mode="json"),
            "predicted_eta": response.predicted_eta,
            "predicted_remaining_minutes": response.predicted_remaining_minutes,
            "predicted_delay_minutes": response.predicted_delay_minutes,
            "delay_category": response.delay_category
        }
        await save_prediction(prediction_doc)
        await upsert_live_state(request.train_number, request.model_dump(mode="json"))
        
        return response
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        logger.error(f"Internal error during prediction: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
