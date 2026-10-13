
"""
AirScope | nik
Station-level Berlin PM2.5 evaluation.

Evaluates saved models without retraining.
Uses the existing chronological test partition.
Compares ML predictions against persistence.

Important:
The reconstructed inference features must match training.
The script checks overall metrics before exporting results.
"""

import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]

FEATURES_FILE = (
    ROOT / "data" / "processed"
    / "airscope_forecast_features.parquet"
)

MODELS_DIR = ROOT / "models"
OUTPUT_DIR = ROOT / "data" / "processed"

HORIZONS = (6, 12, 24)

# Previously recorded independent Berlin test metrics.
# These serve as reproducibility checks, not new results.
EXPECTED = {
    6: {
        "samples": 9404,
        "baseline_mae": 0.9696,
        "model_mae": 0.9292,
    },
    12: {
        "samples": 9176,
        "baseline_mae": 1.8102,
        "model_mae": 1.6712,
    },
    24: {
        "samples": 8736,
        "baseline_mae": 3.1725,
        "model_mae": 2.9142,
    },
}


def mae(actual, predicted):
    """Mean absolute error."""
    return float(np.mean(np.abs(actual - predicted)))


def rmse(actual, predicted):
    """Root mean squared error."""
    return float(
        np.sqrt(np.mean((actual - predicted) ** 2))
    )


def build_model_inputs(df, feature_columns):
    """
    Reconstruct model inputs from the saved feature dataset.

    Check cyclical feature definitions against train_berlin.py.
    The overall-metric verification below must pass before
    station-level results are accepted.
    """

    x = df[
        [
            "pm25_current",
            "pm25_lag_1h",
            "pm25_lag_3h",
            "pm25_lag_6h",
            "pm25_lag_12h",
            "pm25_lag_24h",
        ]
    ].copy()

    timestamps = pd.to_datetime(
        df["forecast_origin_utc"],
        utc=True,
    )

    hour = timestamps.dt.hour.to_numpy()
    weekday = timestamps.dt.dayofweek.to_numpy()
    day_of_year = timestamps.dt.dayofyear.to_numpy()

    # Cyclical time features.
    x["hour_sin"] = np.sin(2 * np.pi * hour / 24)
    x["hour_cos"] = np.cos(2 * np.pi * hour / 24)

    x["weekday_sin"] = np.sin(
        2 * np.pi * weekday / 7
    )
    x["weekday_cos"] = np.cos(
        2 * np.pi * weekday / 7
    )

    # Verify this convention matches the training code.
    x["year_sin"] = np.sin(
        2 * np.pi * day_of_year / 365.25
    )
    x["year_cos"] = np.cos(
        2 * np.pi * day_of_year / 365.25
    )

    # One-hot station features in the saved model order.
    for column in feature_columns:
        if column.startswith("station_"):
            station_id = column.removeprefix("station_")

            x[column] = (
                df["station_id"] == station_id
            ).astype(int).to_numpy()

    missing = [
        column
        for column in feature_columns
        if column not in x.columns
    ]

    if missing:
        raise ValueError(
            f"Missing model features: {missing}"
        )

    return x.loc[:, feature_columns]


def evaluate_one_horizon(df, horizon):
    """Evaluate each Berlin station at one forecast horizon."""

    artifact_path = (
        MODELS_DIR
        / f"berlin_pm25_hgb_{horizon}h.joblib"
    )

    if not artifact_path.exists():
        raise FileNotFoundError(artifact_path)

    # Trusted locally trained model artifact.
    bundle = joblib.load(artifact_path)

    model = bundle["model"]
    feature_columns = bundle["feature_columns"]

    if int(bundle["horizon_hours"]) != horizon:
        raise ValueError(
            f"Incorrect model horizon in {artifact_path}"
        )

    selected = df.loc[
        (df["city"] == "Berlin")
        & (df["partition"] == "test")
        & (df["horizon_hours"] == horizon)
    ].copy()

    selected = selected.sort_values(
        ["station_id", "forecast_origin_utc"]
    ).reset_index(drop=True)

    if selected.empty:
        raise ValueError(
            f"No Berlin test examples for {horizon}h"
        )

    # Ensure feature, baseline and target inputs are valid.
    required = [
        "pm25_current",
        "pm25_lag_1h",
        "pm25_lag_3h",
        "pm25_lag_6h",
        "pm25_lag_12h",
        "pm25_lag_24h",
        "target_pm25",
    ]

    if selected[required].isna().any().any():
        raise ValueError(
            f"Missing test values for {horizon}h"
        )

    x_test = build_model_inputs(
        selected,
        feature_columns,
    )

    actual = selected["target_pm25"].to_numpy(
        dtype=float
    )

    baseline = selected["pm25_current"].to_numpy(
        dtype=float
    )

    predictions = np.asarray(
        model.predict(x_test),
        dtype=float,
    )

    if not np.isfinite(predictions).all():
        raise ValueError("Model produced invalid predictions")

    overall = {
        "horizon_hours": horizon,
        "samples": len(selected),
        "baseline_mae": mae(actual, baseline),
        "model_mae": mae(actual, predictions),
        "baseline_rmse": rmse(actual, baseline),
        "model_rmse": rmse(actual, predictions),
    }

    # Overall statistics must reproduce the earlier evaluation.
    expected = EXPECTED[horizon]

    print(f"\n--- {horizon}h overall test verification ---")
    print("Samples:", overall["samples"])
    print("Baseline MAE:", round(overall["baseline_mae"], 4))
    print("Model MAE:", round(overall["model_mae"], 4))
    print("Baseline RMSE:", round(overall["baseline_rmse"], 4))
    print("Model RMSE:", round(overall["model_rmse"], 4))

    if overall["samples"] != expected["samples"]:
        raise ValueError(
            f"{horizon}h test sample count does not match "
            "the previous evaluation."
        )

    if (
        abs(
            overall["baseline_mae"]
            - expected["baseline_mae"]
        )
        > 0.005
    ):
        raise ValueError(
            f"{horizon}h persistence results do not match "
            "the previous evaluation."
        )

    if (
        abs(
            overall["model_mae"]
            - expected["model_mae"]
        )
        > 0.005
    ):
        raise ValueError(
            f"{horizon}h ML results do not match the previous "
            "evaluation. Verify cyclical feature engineering "
            "against ml/training/train_berlin.py."
        )

    # Calculate station-specific metrics using aligned arrays.
    selected["actual"] = actual
    selected["baseline_prediction"] = baseline
    selected["ml_prediction"] = predictions

    rows = []

    for station_id, group in selected.groupby("station_id"):
        y = group["actual"].to_numpy()
        base = group["baseline_prediction"].to_numpy()
        pred = group["ml_prediction"].to_numpy()

        baseline_mae = mae(y, base)
        model_mae = mae(y, pred)

        improvement = (
            100 * (baseline_mae - model_mae) / baseline_mae
            if baseline_mae > 0
            else None
        )

        rows.append({
            "station_id": station_id,
            "station_name": group["station_name"].iloc[0],
            "horizon_hours": horizon,
            "samples": len(group),
            "baseline_mae": baseline_mae,
            "model_mae": model_mae,
            "baseline_rmse": rmse(y, base),
            "model_rmse": rmse(y, pred),
            "mae_improvement_pct": improvement,
            "model_bias": float(np.mean(pred - y)),
        })

    return rows, overall


def main():
    """Run independent Berlin station-level evaluation."""

    print("=" * 62)
    print("AirScope | Station-Level Model Evaluation")
    print("=" * 62)

    if not FEATURES_FILE.exists():
        raise FileNotFoundError(FEATURES_FILE)

    df = pd.read_parquet(FEATURES_FILE)

    expected_columns = {
        "city",
        "station_id",
        "station_name",
        "forecast_origin_utc",
        "partition",
        "horizon_hours",
        "target_pm25",
        "pm25_current",
    }

    missing = expected_columns - set(df.columns)

    if missing:
        raise ValueError(
            f"Missing dataset columns: {sorted(missing)}"
        )

    all_rows = []
    overall_results = []

    for horizon in HORIZONS:
        rows, overall = evaluate_one_horizon(
            df,
            horizon,
        )

        all_rows.extend(rows)
        overall_results.append(overall)

    results = pd.DataFrame(all_rows)

    # Expected: 12 stations x 3 forecast horizons.
    if len(results) != 36:
        raise ValueError(
            f"Expected 36 station-horizon rows, got {len(results)}"
        )

    results = results.sort_values(
        ["horizon_hours", "model_mae", "station_id"]
    ).reset_index(drop=True)

    print("\nStation-level results:")
    print(
        results[
            [
                "station_id",
                "horizon_hours",
                "samples",
                "baseline_mae",
                "model_mae",
                "mae_improvement_pct",
            ]
        ].round(4).to_string(index=False)
    )

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    csv_path = (
        OUTPUT_DIR / "berlin_station_evaluation.csv"
    )

    summary_path = (
        OUTPUT_DIR / "berlin_station_evaluation_summary.json"
    )

    results.to_csv(csv_path, index=False)

    summary = {
        "city": "Berlin",
        "partition": "test",
        "source": "Saved chronological forecast features",
        "horizons": list(HORIZONS),
        "station_count": int(
            results["station_id"].nunique()
        ),
        "station_horizon_rows": len(results),
        "overall": overall_results,
        "note": (
            "Station metrics reproduce the recorded overall "
            "test MAE before export. Results are not live."
        ),
    }

    summary_path.write_text(
        json.dumps(summary, indent=2),
        encoding="utf-8",
    )

    print("\nVerification passed for all three horizons.")
    print("Saved:", csv_path)
    print("Saved:", summary_path)


if __name__ == "__main__":
    main()
