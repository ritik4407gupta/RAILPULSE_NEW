from fastapi import APIRouter
from app.db.mongodb import db
from app.ml.loader import get_model_metadata

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
    metadata = get_model_metadata()
    model_status = "ok" if metadata else "error"
    
    return {
        "status": "ok" if mongo_status == "ok" and model_status == "ok" else "degraded",
        "mongodb": mongo_status,
        "model": model_status,
        "model_version": metadata.get("version", "unknown")
    }
