from app.schemas.train import TrainStateRequest
from app.ml.features import build_inference_features

def build_feature_vector(request: TrainStateRequest) -> dict:
    return build_inference_features(request)
