import pandas as pd
import math
from app.ml.features import FEATURE_COLUMNS
from app.ml.loader import get_eta_pipeline, get_delay_pipeline

def predict_eta_and_delay(features: dict):
    eta_pipeline = get_eta_pipeline()
    delay_pipeline = get_delay_pipeline()
    
    if eta_pipeline is None or delay_pipeline is None:
        raise ValueError("Model pipelines are not loaded.")

    missing = [column for column in FEATURE_COLUMNS if column not in features]
    extra = [column for column in features if column not in FEATURE_COLUMNS]
    if missing or extra:
        raise ValueError(f"Inference feature mismatch: missing={missing}, extra={extra}")

    df = pd.DataFrame([[features[column] for column in FEATURE_COLUMNS]], columns=FEATURE_COLUMNS)
    
    remaining_minutes = eta_pipeline.predict(df)[0]
    delay_minutes = delay_pipeline.predict(df)[0]
    if not all(math.isfinite(float(value)) for value in (remaining_minutes, delay_minutes)):
        raise ValueError("Model returned a non-finite prediction.")
    remaining_minutes = max(0.0, float(remaining_minutes))
    delay_minutes = max(0.0, float(delay_minutes))
    
    return remaining_minutes, delay_minutes

def classify_delay(delay_minutes: float) -> str:
    if delay_minutes <= 5:
        return "ON_TIME"
    elif delay_minutes <= 15:
        return "MINOR"
    elif delay_minutes <= 60:
        return "MODERATE"
    elif delay_minutes <= 120:
        return "MAJOR"
    else:
        return "SEVERE"
