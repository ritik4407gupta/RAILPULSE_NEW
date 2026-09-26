from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


CapabilityStatus = Literal["available", "future_data_required"]


class PredictionHistoryResponse(BaseModel):
    train_number: str
    total: int
    predictions: list[dict[str, Any]]


class UpcomingStationETA(BaseModel):
    station_name: str
    predicted_eta: datetime
    confidence: float | None = None


class UpcomingStationETAResponse(BaseModel):
    train_number: str
    status: CapabilityStatus
    data_source: str
    upcoming_stations: list[UpcomingStationETA] = Field(default_factory=list)
    limitation: str


class DelayPropagationResponse(BaseModel):
    train_number: str
    status: CapabilityStatus
    data_source: str
    affected_trains: list[dict[str, Any]] = Field(default_factory=list)
    limitation: str


class OperationalRiskResponse(BaseModel):
    train_number: str
    status: CapabilityStatus
    data_source: str
    risks: list[dict[str, Any]] = Field(default_factory=list)
    limitation: str


class AlertResponse(BaseModel):
    alert_id: str
    train_number: str | None = None
    alert_type: str
    severity: str
    message: str
    created_at: datetime
    acknowledged: bool = False


class AlertsResponse(BaseModel):
    status: CapabilityStatus
    data_source: str
    alerts: list[AlertResponse] = Field(default_factory=list)
    limitation: str | None = None


class LiveStateUpdateResponse(BaseModel):
    status: str
    train_number: str
    updated_at: datetime
    source: str


class SimulationStateResponse(BaseModel):
    status: str
    train_number: str
    simulated_at: datetime
    source: str = "simulation"
    message: str | None = None
