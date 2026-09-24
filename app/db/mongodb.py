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
    db.client = AsyncIOMotorClient(settings.MONGODB_URI)
    db.db = db.client[settings.MONGODB_DB]
    logger.info("Connected to MongoDB.")

async def close_mongo_connection():
    logger.info("Closing MongoDB connection...")
    if db.client:
        db.client.close()
    logger.info("MongoDB connection closed.")
