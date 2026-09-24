from pydantic_settings import BaseSettings
from functools import lru_cache
import os

class Settings(BaseSettings):
    MONGODB_URI: str = "mongodb://localhost:27017"
    MONGODB_DB: str = "railpulse"
    MODEL_PATH: str = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "models", "railpulse_eta_model.pkl")
    MODEL_VERSION: str = "eta-v1"
    ENVIRONMENT: str = "development"
    API_PREFIX: str = "/api/v1"

    class Config:
        env_file = ".env"

@lru_cache()
def get_settings():
    return Settings()
