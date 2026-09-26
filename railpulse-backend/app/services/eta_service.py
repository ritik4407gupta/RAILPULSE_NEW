from app.schemas.train import TrainStateRequest
from app.schemas.prediction import PredictionResponse
from app.services.feature_service import build_feature_vector
from app.ml.predictor import predict_eta_and_delay, classify_delay
from app.ml.loader import get_model_metadata, get_uncertainty_metadata
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)

async def calculate_eta(request: TrainStateRequest) -> PredictionResponse:
    features = build_feature_vector(request)
    
    try:
        remaining_minutes, delay_minutes = predict_eta_and_delay(features)
    except Exception as e:
        logger.error(f"Prediction failed: {e}")
        raise ValueError("Failed to predict ETA due to model error.")

    prediction_time = request.current_timestamp
    predicted_eta = prediction_time + timedelta(minutes=float(remaining_minutes))
    
    uncertainty = get_uncertainty_metadata()
    interval_minutes = uncertainty.get("eta_interval_minutes")
    calibration_coverage = uncertainty.get("eta_calibration_coverage")
    if interval_minutes is None or calibration_coverage is None:
        raise ValueError("Model uncertainty metadata is unavailable.")

    eta_lower = predicted_eta - timedelta(minutes=float(interval_minutes))
    eta_upper = predicted_eta + timedelta(minutes=float(interval_minutes))
    
    delay_category = classify_delay(delay_minutes)
    
    metadata = get_model_metadata()
    version = metadata.get("version", "unknown")
    
    return PredictionResponse(
        train_number=request.train_number,
        predicted_eta=predicted_eta,
        predicted_remaining_minutes=float(remaining_minutes),
        predicted_delay_minutes=float(delay_minutes),
        eta_lower=eta_lower,
        eta_upper=eta_upper,
        delay_category=delay_category,
        confidence=float(calibration_coverage),
        model_version=version
    )
