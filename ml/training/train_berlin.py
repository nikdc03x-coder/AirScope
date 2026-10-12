
"""
AirScope | nik
Train the first Berlin PM2.5 forecasting models.

- One model per forecast horizon: 6, 12, 24 hours.
- Train only on chronological training data.
- Evaluate against persistence on identical rows.
- Save trained models and reproducible metrics.
- Never use future PM2.5 readings as features.
"""

import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

from sklearn.ensemble import HistGradientBoostingRegressor


ROOT = Path(__file__).resolve().parents[2]
PROCESSED = ROOT / "data" / "processed"
MODEL_DIR = ROOT / "models"

INPUT_FILE = (
    PROCESSED / "airscope_forecast_features.parquet"
)

METRICS_FILE = (
    PROCESSED / "berlin_ml_metrics.csv"
)

PREDICTIONS_FILE = (
    PROCESSED / "berlin_ml_predictions.parquet"
)

HORIZONS = [6, 12, 24]

BASE_FEATURES = [
    "pm25_current",
    "pm25_lag_1h",
    "pm25_lag_3h",
    "pm25_lag_6h",
    "pm25_lag_12h",
    "pm25_lag_24h",
]

TIME_FEATURES = [
    "hour_sin",
    "hour_cos",
    "weekday_sin",
    "weekday_cos",
    "year_sin",
    "year_cos",
]


def add_time_features(df):
    """Add calendar features known at forecast time."""

    df = df.copy()
    times = df["forecast_origin_utc"].dt

    hour = times.hour
    weekday = times.dayofweek
    day_of_year = times.dayofyear

    df["hour_sin"] = np.sin(2 * np.pi * hour / 24)
    df["hour_cos"] = np.cos(2 * np.pi * hour / 24)

    df["weekday_sin"] = np.sin(
        2 * np.pi * weekday / 7
    )
    df["weekday_cos"] = np.cos(
        2 * np.pi * weekday / 7
    )

    df["year_sin"] = np.sin(
        2 * np.pi * day_of_year / 365.25
    )
    df["year_cos"] = np.cos(
        2 * np.pi * day_of_year / 365.25
    )

    return df


def evaluate(actual, predicted):
    """Calculate MAE, RMSE and signed bias."""

    actual = np.asarray(actual, dtype=float)
    predicted = np.asarray(predicted, dtype=float)

    error = predicted - actual

    return {
        "mae": float(np.mean(np.abs(error))),
        "rmse": float(
            np.sqrt(np.mean(error ** 2))
        ),
        "bias": float(np.mean(error)),
    }


def load_features():
    """Load Berlin examples without changing the source."""

    df = pd.read_parquet(INPUT_FILE)

    df = df[df["city"] == "Berlin"].copy()

    if df.empty:
        raise ValueError("No Berlin forecast examples found.")

    required = (
        BASE_FEATURES
        + [
            "station_id",
            "forecast_origin_utc",
            "target_timestamp_utc",
            "target_pm25",
            "partition",
            "horizon_hours",
        ]
    )

    missing = [
        col for col in required
        if col not in df.columns
    ]

    if missing:
        raise ValueError(
            f"Missing forecast columns: {missing}"
        )

    if not (
        df["target_timestamp_utc"]
        > df["forecast_origin_utc"]
    ).all():
        raise ValueError(
            "Forecast targets must occur after origins."
        )

    df = add_time_features(df)

    # Station IDs are metadata known at prediction time.
    # One-hot encoding gives the model station context.
    station_columns = pd.get_dummies(
        df["station_id"].astype(str),
        prefix="station",
        dtype=int,
    )

    df = pd.concat(
        [df, station_columns],
        axis=1,
    )

    feature_columns = (
        BASE_FEATURES
        + TIME_FEATURES
        + station_columns.columns.tolist()
    )

    if df[feature_columns].isna().any().any():
        raise ValueError(
            "ML features contain missing values."
        )

    return df, feature_columns


def train_horizon(df, horizon, feature_columns):
    """Train and evaluate one forecast horizon."""

    subset = df[
        df["horizon_hours"] == horizon
    ].copy()

    train = subset[
        subset["partition"] == "train"
    ].copy()

    validation = subset[
        subset["partition"] == "validation"
    ].copy()

    test = subset[
        subset["partition"] == "test"
    ].copy()

    for name, partition in [
        ("train", train),
        ("validation", validation),
        ("test", test),
    ]:
        if partition.empty:
            raise ValueError(
                f"No {name} data for {horizon}h."
            )

    # Do not randomly mix future and past examples.
    model = HistGradientBoostingRegressor(
        max_iter=100,
        learning_rate=0.06,
        max_leaf_nodes=21,
        min_samples_leaf=50,
        l2_regularization=1.0,
        early_stopping=False,
        random_state=42,
    )

    model.fit(
        train[feature_columns],
        train["target_pm25"],
    )

    results = []
    prediction_frames = []

    for partition_name, partition in [
        ("train", train),
        ("validation", validation),
        ("test", test),
    ]:
        actual = partition["target_pm25"].to_numpy()

        ml_prediction = model.predict(
            partition[feature_columns]
        )

        # Persistence comparison uses identical examples.
        baseline_prediction = (
            partition["pm25_current"].to_numpy()
        )

        ml_metrics = evaluate(actual, ml_prediction)
        baseline_metrics = evaluate(
            actual,
            baseline_prediction,
        )

        improvement = (
            100
            * (
                baseline_metrics["mae"]
                - ml_metrics["mae"]
            )
            / baseline_metrics["mae"]
        )

        for model_name, metrics in [
            ("persistence", baseline_metrics),
            ("hist_gradient_boosting", ml_metrics),
        ]:
            results.append({
                "city": "Berlin",
                "horizon_hours": horizon,
                "partition": partition_name,
                "model": model_name,
                "samples": len(partition),
                **metrics,
            })

        prediction_frames.append(
            pd.DataFrame({
                "city": "Berlin",
                "station_id": partition["station_id"].to_numpy(),
                "forecast_origin_utc": (
                    partition["forecast_origin_utc"].to_numpy()
                ),
                "target_timestamp_utc": (
                    partition["target_timestamp_utc"].to_numpy()
                ),
                "horizon_hours": horizon,
                "partition": partition_name,
                "actual": actual,
                "ml_prediction": ml_prediction,
                "persistence_prediction": baseline_prediction,
            })
        )

        if partition_name in ["validation", "test"]:
            print(
                f"  {partition_name}: "
                f"ML MAE={ml_metrics['mae']:.4f}, "
                f"baseline MAE={baseline_metrics['mae']:.4f}, "
                f"improvement={improvement:.2f}%"
            )

    MODEL_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    model_path = (
        MODEL_DIR / f"berlin_pm25_hgb_{horizon}h.joblib"
    )

    # Save the exact feature order alongside the model.
    joblib.dump(
        {
            "model": model,
            "feature_columns": feature_columns,
            "horizon_hours": horizon,
            "city": "Berlin",
            "pollutant": "PM2.5",
            "unit": "ug/m3",
        },
        model_path,
    )

    print(f"  Saved: {model_path.relative_to(ROOT)}")

    return results, prediction_frames


def main():
    print("AirScope | Train Berlin PM2.5 models")

    df, feature_columns = load_features()

    print(f"Berlin examples: {len(df):,}")
    print(f"Features per model: {len(feature_columns)}")

    all_metrics = []
    all_predictions = []

    for horizon in HORIZONS:
        print(f"\nForecast horizon: {horizon} hours")

        metrics, predictions = train_horizon(
            df,
            horizon,
            feature_columns,
        )

        all_metrics.extend(metrics)
        all_predictions.extend(predictions)

    metrics_df = pd.DataFrame(all_metrics)
    predictions_df = pd.concat(
        all_predictions,
        ignore_index=True,
    )

    PROCESSED.mkdir(
        parents=True,
        exist_ok=True,
    )

    metrics_df.to_csv(
        METRICS_FILE,
        index=False,
    )

    predictions_df.to_parquet(
        PREDICTIONS_FILE,
        index=False,
    )

    print("\nHeld-out test performance:")
    test_metrics = metrics_df[
        metrics_df["partition"] == "test"
    ]

    print(
        test_metrics[
            [
                "horizon_hours",
                "model",
                "samples",
                "mae",
                "rmse",
                "bias",
            ]
        ].round(4).to_string(index=False)
    )

    print(
        f"\nSaved: {METRICS_FILE.relative_to(ROOT)}"
    )
    print(
        f"Saved: {PREDICTIONS_FILE.relative_to(ROOT)}"
    )


if __name__ == "__main__":
    main()
