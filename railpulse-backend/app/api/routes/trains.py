from fastapi import APIRouter, Depends, HTTPException, Query
from app.api.dependencies import get_current_user, require_roles
from app.db.repositories.prediction_repository import (
    get_latest_prediction as get_latest_prediction_record,
    list_predictions,
)
from app.db.repositories.train_repository import get_live_state, upsert_live_state
from app.db.mongodb import db
from app.schemas.capabilities import (
    PredictionHistoryResponse,
    LiveStateUpdateResponse,
    UpcomingStationETAResponse,
)
from app.schemas.train import TrainListResponse, TrainStateRequest
from datetime import datetime, timezone

router = APIRouter()


@router.get("")
async def list_trains(current_user: dict = Depends(get_current_user)):
    documents = await db.db["live_train_state"].find({}).sort("train_number", 1).to_list(length=1000)
    trains = []
    for document in documents:
        item = dict(document)
        item.pop("_id", None)
        trains.append({
            "train_number": item.get("train_number"),
            "train_type": item.get("train_type"),
            "source": item.get("source"),
            "destination": item.get("destination"),
            "current_station": item.get("current_station"),
            "current_section": item.get("current_section"),
            "current_delay_minutes": item.get("current_delay_minutes", 0),
            "current_speed_kmph": item.get("current_speed_kmph", 0),
            "distance_remaining_km": item.get("distance_remaining_km"),
            "scheduled_arrival": item.get("scheduled_arrival"),
            "data_source": item.get("data_source", "LIVE"),
            "updated_at": item.get("updated_at"),
        })
    return TrainListResponse(count=len(trains), trains=trains)


@router.get("/{train_number}/state")
async def get_train_state(train_number: str, current_user: dict = Depends(get_current_user)):
    state = await get_live_state(train_number)
    if not state:
        raise HTTPException(status_code=404, detail="Train state not found")
    
    return state

@router.get("/{train_number}/predictions/latest")
async def get_latest_prediction(train_number: str, current_user: dict = Depends(get_current_user)):
    prediction = await get_latest_prediction_record(train_number)
    if not prediction:
        raise HTTPException(status_code=404, detail="No predictions found for this train")
        
    return prediction


@router.get("/{train_number}/predictions", response_model=PredictionHistoryResponse)
async def get_prediction_history(
    train_number: str,
    limit: int = Query(default=20, ge=1, le=100),
    skip: int = Query(default=0, ge=0),
    current_user: dict = Depends(get_current_user),
):
    predictions, total = await list_predictions(train_number, limit, skip)
    return PredictionHistoryResponse(
        train_number=train_number,
        total=total,
        predictions=predictions,
    )


@router.put("/{train_number}/state", response_model=LiveStateUpdateResponse)
async def update_live_train_state(
    train_number: str,
    request: TrainStateRequest,
    current_user: dict = Depends(require_roles("STAFF", "ADMIN")),
):
    updated_at = await upsert_live_state(train_number, request.model_dump(mode="json"))
    return LiveStateUpdateResponse(
        status="accepted",
        train_number=train_number,
        updated_at=updated_at,
        source="live",
    )


@router.get("/{train_number}/upcoming-stations", response_model=UpcomingStationETAResponse)
async def get_upcoming_station_etas(
    train_number: str,
    current_user: dict = Depends(get_current_user),
):
    return UpcomingStationETAResponse(
        train_number=train_number,
        status="future_data_required",
        data_source="route_schedule_and_live_network_feed_required",
        limitation=(
            "Station sequence and station-level observations are not present in the current dataset; "
            "no station ETA is fabricated."
        ),
    )
