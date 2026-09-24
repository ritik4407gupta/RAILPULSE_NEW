from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class TrainStateRequest(BaseModel):
    train_number: str
    train_type: Optional[str] = None
    train_priority: Optional[int] = None
    current_timestamp: datetime
    current_station: Optional[str] = None
    current_section: Optional[str] = None
    destination: str
    distance_remaining_km: Optional[float] = None
    current_speed_kmph: Optional[float] = None
    current_delay_minutes: float = 0.0
    scheduled_arrival: Optional[datetime] = None
    scheduled_travel_time_minutes: Optional[float] = None
    elapsed_travel_time_minutes: Optional[float] = None
    historical_route_delay_minutes: Optional[float] = None
    historical_station_delay_minutes: Optional[float] = None
    historical_section_time_minutes: Optional[float] = None
    dwell_time_minutes: Optional[float] = None
    track_occupancy: Optional[float] = None
    junction_congestion: Optional[float] = None
    platform_availability: Optional[float] = None
    trains_in_section: Optional[int] = None
    source: Optional[str] = None
    season: Optional[str] = None
    run_frequency: Optional[str] = None
