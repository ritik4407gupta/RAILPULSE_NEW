from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import get_settings
import logging

logger = logging.getLogger(__name__)
settings = get_settings()

class MongoDB:
    client: AsyncIOMotorClient = None
    db = None

db = MongoDB()

async def connect_to_mongo():
    logger.info("Connecting to MongoDB...")
    db.client = AsyncIOMotorClient(
        settings.MONGODB_URI,
        serverSelectionTimeoutMS=5000,
        connectTimeoutMS=5000,
        socketTimeoutMS=10000,
    )
    db.db = db.client[settings.MONGODB_DB]
    await db.db.command("ping")
    logger.info("Connected to MongoDB.")

async def ensure_indexes():
    if db.db is None:
        return
    await db.db["users"].create_index("username", unique=True)
    await db.db["live_train_state"].create_index("train_number", unique=True)
    await db.db["simulation_states"].create_index("train_number", unique=True)
    await db.db["predictions"].create_index([("train_number", 1), ("timestamp", -1)])
    await db.db["alerts"].create_index([("train_number", 1), ("created_at", -1)])
    await db.db["alerts"].create_index("acknowledged")

async def close_mongo_connection():
    logger.info("Closing MongoDB connection...")
    if db.client:
        db.client.close()
        db.client = None
        db.db = None
    logger.info("MongoDB connection closed.")
