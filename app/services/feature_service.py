from app.schemas.train import TrainStateRequest

def build_feature_vector(request: TrainStateRequest) -> dict:
    # Match the features expected by the training pipeline
    features = {
        'train_number': request.train_number,
        'train_type': request.train_type or "Unknown",
        'source': request.source or "Unknown",
        'destination': request.destination or "Unknown",
        'distance_remaining_km': request.distance_remaining_km if request.distance_remaining_km is not None else 0.0,
        'current_speed_kmph': request.current_speed_kmph if request.current_speed_kmph is not None else 0.0,
        'current_delay_minutes': request.current_delay_minutes,
        'scheduled_arrival_hour': request.scheduled_arrival.hour if request.scheduled_arrival else 0,
        'season': request.season or "Unknown",
        'run_frequency': request.run_frequency or "Unknown"
    }
    return features
