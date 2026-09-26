from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from typing import Any

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from xgboost import XGBRegressor

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from app.ml.features import (
    CATEGORICAL_FEATURES,
    FEATURE_COLUMNS,
    NUMERIC_FEATURES,
    feature_frame,
    parse_datetime,
    parse_time_minutes,
)

DATA_PATH = os.path.join(BASE_DIR, "data", "indian_railway_delay_data_.csv")
MODEL_PATH = os.path.join(BASE_DIR, "models", "railpulse_eta_model.pkl")
RANDOM_STATE = 42
CALIBRATION_LEVEL = 0.90


def load_training_data(filepath: str) -> pd.DataFrame:
    raw = pd.read_csv(filepath)
    raw.columns = [column.strip() for column in raw.columns]

    rows: list[dict[str, Any]] = []
    for _, source_row in raw.iterrows():
        event_time = parse_datetime(source_row["Date"])
        distance = float(source_row["Distance(Km)"])
        scheduled_minutes = distance
        delay_minutes = parse_time_minutes(source_row["Dealy_min"])
        feature_row = {
            "event_time": event_time,
            "scheduled_arrival": source_row["Sc_arr__time"],
            "distance_remaining_km": distance,
            "train_number": source_row["Train_no"],
            "train_type": "Express",
            "source": source_row["Source"],
            "destination": source_row["Destitnation"],
            "season": source_row["Season"],
            "run_frequency": source_row["Run_frequency"],
        }
        rows.append(
            {
                **feature_row,
                "event_date": event_time,
                "trip_group": f"{source_row['Train_no']}|{event_time.date().isoformat()}",
                "target_eta_minutes": scheduled_minutes + delay_minutes,
                "target_delay_minutes": delay_minutes,
            }
        )

    features = feature_frame(rows)
    targets = pd.DataFrame(
        [
            {
                "event_date": row["event_date"],
                "trip_group": row["trip_group"],
                "target_eta_minutes": row["target_eta_minutes"],
                "target_delay_minutes": row["target_delay_minutes"],
            }
            for row in rows
        ]
    )
    return pd.concat([features.reset_index(drop=True), targets], axis=1)


def split_dataset(
    data: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    ordered_dates = sorted(data["event_date"].dt.date.unique())
    if len(ordered_dates) < 3:
        raise ValueError("At least three distinct event dates are required for splitting")

    test_date_count = max(1, int(np.ceil(len(ordered_dates) * 0.2)))
    validation_date_count = max(1, int(np.ceil(len(ordered_dates) * 0.2)))
    test_dates = set(ordered_dates[-test_date_count:])
    validation_dates = set(
        ordered_dates[-test_date_count - validation_date_count : -test_date_count]
    )

    train = data[~data["event_date"].dt.date.isin(test_dates | validation_dates)]
    validation = data[data["event_date"].dt.date.isin(validation_dates)]
    test = data[data["event_date"].dt.date.isin(test_dates)]

    train_groups = set(train["trip_group"])
    validation_groups = set(validation["trip_group"])
    test_groups = set(test["trip_group"])
    if train_groups & validation_groups or train_groups & test_groups or validation_groups & test_groups:
        raise ValueError("Trip groups overlap between train, validation, and test splits")
    if min(len(train), len(validation), len(test)) == 0:
        raise ValueError("Time split produced an empty partition")
    return train, validation, test


def create_pipeline() -> Pipeline:
    preprocessor = ColumnTransformer(
        transformers=[
            ("numeric", StandardScaler(), NUMERIC_FEATURES),
            ("categorical", OneHotEncoder(handle_unknown="ignore"), CATEGORICAL_FEATURES),
        ]
    )
    estimator = XGBRegressor(
        objective="reg:squarederror",
        n_estimators=150,
        max_depth=3,
        learning_rate=0.05,
        subsample=0.9,
        colsample_bytree=0.9,
        random_state=RANDOM_STATE,
        n_jobs=1,
    )
    return Pipeline([("preprocessor", preprocessor), ("model", estimator)])


def regression_metrics(actual: pd.Series, predicted: np.ndarray) -> dict[str, float]:
    return {
        "mae_minutes": float(mean_absolute_error(actual, predicted)),
        "rmse_minutes": float(np.sqrt(mean_squared_error(actual, predicted))),
        "r2": float(r2_score(actual, predicted)),
    }


def calibration_quantile(actual: pd.Series, predicted: np.ndarray) -> tuple[float, float]:
    absolute_errors = np.abs(actual.to_numpy() - predicted)
    quantile = float(np.quantile(absolute_errors, CALIBRATION_LEVEL, method="higher"))
    coverage = float(np.mean(absolute_errors <= quantile))
    return max(quantile, 1.0), coverage


def train_and_evaluate(
    data_path: str = DATA_PATH,
    model_path: str = MODEL_PATH,
) -> tuple[dict[str, Any], dict[str, Any]]:
    data = load_training_data(data_path)
    train, validation, test = split_dataset(data)

    train_features = train.loc[:, FEATURE_COLUMNS]
    validation_features = validation.loc[:, FEATURE_COLUMNS]
    test_features = test.loc[:, FEATURE_COLUMNS]

    eta_validation_pipeline = create_pipeline()
    delay_validation_pipeline = create_pipeline()
    eta_validation_pipeline.fit(train_features, train["target_eta_minutes"])
    delay_validation_pipeline.fit(train_features, train["target_delay_minutes"])

    eta_validation_predictions = eta_validation_pipeline.predict(validation_features)
    delay_validation_predictions = delay_validation_pipeline.predict(validation_features)
    eta_uncertainty, eta_coverage = calibration_quantile(
        validation["target_eta_minutes"], eta_validation_predictions
    )
    delay_uncertainty, delay_coverage = calibration_quantile(
        validation["target_delay_minutes"], delay_validation_predictions
    )

    final_train = pd.concat([train, validation], ignore_index=True)
    eta_pipeline = create_pipeline().fit(
        final_train.loc[:, FEATURE_COLUMNS], final_train["target_eta_minutes"]
    )
    delay_pipeline = create_pipeline().fit(
        final_train.loc[:, FEATURE_COLUMNS], final_train["target_delay_minutes"]
    )
    eta_predictions = eta_pipeline.predict(test_features)
    delay_predictions = delay_pipeline.predict(test_features)

    baseline_delay = float(final_train["target_delay_minutes"].mean())
    baseline_eta_predictions = test["scheduled_travel_time_minutes"].to_numpy() + baseline_delay
    baseline_delay_predictions = np.full(len(test), baseline_delay)

    metrics = {
        "validation": {
            "eta_ml": regression_metrics(validation["target_eta_minutes"], eta_validation_predictions),
            "delay_ml": regression_metrics(validation["target_delay_minutes"], delay_validation_predictions),
        },
        "test": {
            "eta_baseline": regression_metrics(test["target_eta_minutes"], baseline_eta_predictions),
            "eta_ml": regression_metrics(test["target_eta_minutes"], eta_predictions),
            "delay_baseline": regression_metrics(test["target_delay_minutes"], baseline_delay_predictions),
            "delay_ml": regression_metrics(test["target_delay_minutes"], delay_predictions),
        },
    }

    split_metadata = {
        "strategy": "chronological_trip_group_split",
        "group_column": "trip_group",
        "train_rows": len(train),
        "validation_rows": len(validation),
        "test_rows": len(test),
        "train_date_max": train["event_date"].max().date().isoformat(),
        "validation_date_range": [
            validation["event_date"].min().date().isoformat(),
            validation["event_date"].max().date().isoformat(),
        ],
        "test_date_min": test["event_date"].min().date().isoformat(),
    }
    metadata = {
        "version": "eta-v2",
        "trained_at": datetime.now(timezone.utc).isoformat(),
        "features": FEATURE_COLUMNS,
        "numeric_features": NUMERIC_FEATURES,
        "categorical_features": CATEGORICAL_FEATURES,
        "targets": ["target_eta_minutes", "target_delay_minutes"],
        "split": split_metadata,
        "baseline": {"delay_mean_minutes": baseline_delay},
        "uncertainty": {
            "method": "validation_absolute_error_quantile",
            "calibration_level": CALIBRATION_LEVEL,
            "eta_interval_minutes": eta_uncertainty,
            "eta_calibration_coverage": eta_coverage,
            "delay_interval_minutes": delay_uncertainty,
            "delay_calibration_coverage": delay_coverage,
        },
        "metrics": metrics,
    }

    bundle = {
        "eta_pipeline": eta_pipeline,
        "delay_pipeline": delay_pipeline,
        "metadata": metadata,
    }
    os.makedirs(os.path.dirname(model_path), exist_ok=True)
    joblib.dump(bundle, model_path)
    return bundle, metrics


if __name__ == "__main__":
    _, evaluation = train_and_evaluate()
    print(json.dumps(evaluation, indent=2, sort_keys=True))
