from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.api.routes import alerts, auth, docs, network, predictions, health, trains, simulation
from app.db.mongodb import connect_to_mongo, close_mongo_connection, ensure_indexes
from app.db.repositories.user_repository import seed_default_users
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
    try:
        await ensure_indexes()
        await seed_default_users(settings)
    except Exception as exc:
        logger.warning("Authentication initialization skipped: %s", exc)
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

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT"],
    allow_headers=["Authorization", "Content-Type"],
)

# Routes
app.include_router(auth.router, prefix=settings.API_PREFIX + "/auth", tags=["Authentication"])
app.include_router(health.router, prefix=settings.API_PREFIX + "/health", tags=["Health"])
app.include_router(predictions.router, prefix=settings.API_PREFIX + "/predict", tags=["Predictions"])
app.include_router(trains.router, prefix=settings.API_PREFIX + "/trains", tags=["Trains"])
app.include_router(simulation.router, prefix=settings.API_PREFIX + "/simulation", tags=["Simulation"])
app.include_router(network.router, prefix=settings.API_PREFIX + "/network", tags=["Network Intelligence"])
app.include_router(alerts.router, prefix=settings.API_PREFIX + "/alerts", tags=["Alerts"])
app.include_router(docs.router, prefix=settings.API_PREFIX + "/docs", tags=["Capability Documentation"])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
