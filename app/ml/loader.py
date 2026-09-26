import joblib
import os
import logging
from app.core.config import get_settings
from app.ml.features import FEATURE_COLUMNS

logger = logging.getLogger(__name__)
settings = get_settings()

_model_bundle = None

def load_models():
    global _model_bundle
    if _model_bundle is None:
        try:
            if not os.path.exists(settings.MODEL_PATH):
                raise FileNotFoundError(settings.MODEL_PATH)
            logger.info("Loading ML models from %s", settings.MODEL_PATH)
            bundle = joblib.load(settings.MODEL_PATH)
            metadata = bundle.get("metadata", {})
            if not all(bundle.get(name) is not None for name in ("eta_pipeline", "delay_pipeline")):
                raise ValueError("Model bundle is missing required pipelines")
            if metadata.get("features") != FEATURE_COLUMNS:
                raise ValueError("Model feature metadata does not match the inference contract")
            if metadata.get("version") != settings.MODEL_VERSION:
                raise ValueError("Model artifact version does not match MODEL_VERSION")
            _model_bundle = bundle
        except Exception:
            logger.exception("Unable to load a valid model artifact from %s", settings.MODEL_PATH)
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


def get_uncertainty_metadata():
    return get_model_metadata().get("uncertainty", {})


def is_model_ready() -> bool:
    bundle = load_models()
    return bool(bundle.get("eta_pipeline") and bundle.get("delay_pipeline") and bundle.get("metadata"))
