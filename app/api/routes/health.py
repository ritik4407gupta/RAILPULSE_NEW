from fastapi import APIRouter
from app.db.mongodb import db
from app.ml.loader import get_model_metadata, is_model_ready
from app.core.config import get_settings
import os

router = APIRouter()

@router.get("/")
async def health_check():
    # Check Mongo
    mongo_status = "ok"
    try:
        await db.db.command("ping")
    except Exception:
        mongo_status = "error"
        
    # Check Model
    settings = get_settings()
    metadata = get_model_metadata()
    artifact_exists = os.path.exists(settings.MODEL_PATH)
    model_status = "ok" if metadata and artifact_exists and is_model_ready() else "error"
    
    return {
        "status": "ok" if mongo_status == "ok" and model_status == "ok" else "degraded",
        "mongodb": mongo_status,
        "model": model_status,
        "model_version": metadata.get("version", "unknown"),
        "model_details": {
            "artifact_exists": artifact_exists,
            "features": metadata.get("features", []),
            "metrics": metadata.get("metrics", {}),
            "uncertainty": metadata.get("uncertainty", {}),
        }
    }
