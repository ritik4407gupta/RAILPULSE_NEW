import joblib

from app.ml.features import FEATURE_COLUMNS, build_inference_features
from app.ml.predictor import predict_eta_and_delay
from app.schemas.train import TrainStateRequest
from training.train import load_training_data, split_dataset


MODEL_PATH = "models/railpulse_eta_model.pkl"
DATA_PATH = "data/indian_railway_delay_data_.csv"


def test_training_features_have_no_target_derived_delay_fields():
    data = load_training_data(DATA_PATH)

    assert len(data) == 100
    assert list(data.loc[:, FEATURE_COLUMNS].columns) == FEATURE_COLUMNS
    assert "current_delay_minutes" not in FEATURE_COLUMNS
    assert "target_eta_minutes" not in FEATURE_COLUMNS
    assert "target_delay_minutes" not in FEATURE_COLUMNS


def test_splits_are_chronological_and_trip_group_disjoint():
    train, validation, test = split_dataset(load_training_data(DATA_PATH))

    assert train["event_date"].max() < validation["event_date"].min()
    assert validation["event_date"].max() < test["event_date"].min()
    assert set(train["trip_group"]).isdisjoint(validation["trip_group"])
    assert set(train["trip_group"]).isdisjoint(test["trip_group"])
    assert set(validation["trip_group"]).isdisjoint(test["trip_group"])


def test_inference_feature_contract_matches_saved_artifact():
    request = TrainStateRequest(
        train_number="12345",
        current_timestamp="2026-09-25T12:00:00Z",
        destination="TestStation",
        distance_remaining_km=100,
    )
    features = build_inference_features(request)
    bundle = joblib.load(MODEL_PATH)

    assert list(features) == FEATURE_COLUMNS
    assert bundle["metadata"]["features"] == FEATURE_COLUMNS
    assert bundle["metadata"]["uncertainty"]["eta_interval_minutes"] >= 1
    assert 0 < bundle["metadata"]["uncertainty"]["eta_calibration_coverage"] <= 1


def test_evaluation_contains_baseline_and_ml_metrics():
    metadata = joblib.load(MODEL_PATH)["metadata"]
    test_metrics = metadata["metrics"]["test"]

    assert set(test_metrics) == {
        "eta_baseline",
        "eta_ml",
        "delay_baseline",
        "delay_ml",
    }
    for metric_group in test_metrics.values():
        assert set(metric_group) == {"mae_minutes", "rmse_minutes", "r2"}


def test_saved_model_inference_is_finite_and_non_negative():
    request = TrainStateRequest(
        train_number="12238",
        current_timestamp="2026-09-25T12:00:00Z",
        destination="Jammu",
        distance_remaining_km=1260,
        source="Varanasi",
        train_type="Express",
        season="Winter",
        run_frequency="Daily",
    )
    prediction = predict_eta_and_delay(build_inference_features(request))
    assert all(value >= 0 for value in prediction)
    assert all(value == value for value in prediction)
