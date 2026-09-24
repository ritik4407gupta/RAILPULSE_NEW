import joblib
import os
import logging
from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

_model_bundle = None

def load_models():
    global _model_bundle
    if _model_bundle is None:
        if os.path.exists(settings.MODEL_PATH):
            logger.info(f"Loading ML models from {settings.MODEL_PATH}")
            _model_bundle = joblib.load(settings.MODEL_PATH)
        else:
            logger.warning(f"Model file not found at {settings.MODEL_PATH}. Inference will fail.")
            _model_bundle = {}
    return _model_bundle

def get_eta_pipeline():
    bundle = load_models()
    return bundle.get("eta_pipeline")

def get_delay_pipeline():
    bundle = load_models()
    return bundle.get("delay_pipeline")

def get_model_metadata():
    bundle = load_models()
    return bundle.get("metadata", {})
