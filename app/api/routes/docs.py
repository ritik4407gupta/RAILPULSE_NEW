from fastapi import APIRouter

router = APIRouter()


@router.get("/capabilities")
async def get_capability_catalog():
    return {
        "available": [
            "live_train_state",
            "prediction_history",
            "eta_prediction",
            "model_health",
            "simulation_state_separation",
        ],
        "future_data_required": [
            "upcoming_station_eta",
            "delay_propagation",
            "operational_risk",
            "network_alert_generation",
        ],
        "data_contract_note": (
            "Future-data capabilities expose typed response envelopes and return no inferred records "
            "until route schedules, station sequences, or live network feeds are connected."
        ),
    }
