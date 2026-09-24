from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.api.routes import predictions, health, trains, simulation
from app.db.mongodb import connect_to_mongo, close_mongo_connection
from app.ml.loader import load_models
from app.core.config import get_settings
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
settings = get_settings()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting up FastAPI application...")
    await connect_to_mongo()
    load_models()
    yield
    # Shutdown
    logger.info("Shutting down FastAPI application...")
    await close_mongo_connection()

app = FastAPI(
    title="RailPulse ETA Backend",
    description="FastAPI-only ML backend for RailPulse ETA prediction",
    version="1.0.0",
    lifespan=lifespan
)

# Routes
app.include_router(health.router, prefix=settings.API_PREFIX + "/health", tags=["Health"])
app.include_router(predictions.router, prefix=settings.API_PREFIX + "/predict", tags=["Predictions"])
app.include_router(trains.router, prefix=settings.API_PREFIX + "/trains", tags=["Trains"])
app.include_router(simulation.router, prefix=settings.API_PREFIX + "/simulation", tags=["Simulation"])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
