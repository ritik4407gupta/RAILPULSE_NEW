from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class PredictionResponse(BaseModel):
    train_number: str
    predicted_eta: datetime
    predicted_remaining_minutes: float
    predicted_delay_minutes: float
    eta_lower: datetime
    eta_upper: datetime
    delay_category: str
    confidence: float
    model_version: str

class StationETA(BaseModel):
    station_name: str
    predicted_eta: datetime

class StationsPredictionResponse(BaseModel):
    train_number: str
    upcoming_stations: List[StationETA]
    model_version: str
