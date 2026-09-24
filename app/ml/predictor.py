import pandas as pd
from datetime import timedelta
from app.ml.loader import get_eta_pipeline, get_delay_pipeline

def predict_eta_and_delay(features: dict):
    eta_pipeline = get_eta_pipeline()
    delay_pipeline = get_delay_pipeline()
    
    if not eta_pipeline or not delay_pipeline:
        raise ValueError("Model pipelines are not loaded.")
        
    df = pd.DataFrame([features])
    
    remaining_minutes = eta_pipeline.predict(df)[0]
    delay_minutes = delay_pipeline.predict(df)[0]
    
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
