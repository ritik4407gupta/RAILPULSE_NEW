from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache
import os

class Settings(BaseSettings):
    MONGODB_URI: str = "mongodb://localhost:27017"
    MONGODB_DB: str = "railpulse"
    MODEL_PATH: str = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "models", "railpulse_eta_model.pkl")
    MODEL_VERSION: str = "eta-v2"
    ENVIRONMENT: str = "development"
    API_PREFIX: str = "/api/v1"
    JWT_SECRET_KEY: str = "change-this-development-secret-key-32"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=60, gt=0, le=1440)
    ADMIN_USERNAME: str = "admin"
    ADMIN_PASSWORD: str = "change-me-admin"
    STAFF_USERNAME: str = "staff"
    STAFF_PASSWORD: str = "change-me-staff"
    CORS_ORIGINS: str = ""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def cors_origins(self) -> list[str]:
        configured = [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]
        if configured:
            return configured
        return [
            "http://localhost:3000",
            "http://127.0.0.1:3000",
            "http://localhost:8080",
            "http://127.0.0.1:8080",
            "http://localhost:4173",
            "http://127.0.0.1:4173",
        ]

    @model_validator(mode="after")
    def validate_production_secrets(self):
        if self.ENVIRONMENT.lower() == "production":
            if self.JWT_SECRET_KEY == "change-this-development-secret-key-32":
                raise ValueError("JWT_SECRET_KEY must be changed in production")
            if self.ADMIN_PASSWORD.startswith("change-me-") or self.STAFF_PASSWORD.startswith("change-me-"):
                raise ValueError("Seed account passwords must be changed in production")
            if len(self.JWT_SECRET_KEY) < 32:
                raise ValueError("JWT_SECRET_KEY must be at least 32 characters")
        return self

@lru_cache()
def get_settings():
    return Settings()
