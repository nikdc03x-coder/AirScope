
"""
AirScope | nik
Evaluate a PM2.5 persistence forecasting baseline.

Prediction:
Future PM2.5 = PM2.5 at forecast origin.

Evaluate separately by city, horizon, and time partition.
"""

from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
PROCESSED = ROOT / "data" / "processed"

FEATURES_FILE = (
    PROCESSED / "airscope_forecast_features.parquet"
)

PREDICTIONS_FILE = (
    PROCESSED / "persistence_predictions.parquet"
)

METRICS_FILE = (
    PROCESSED / "persistence_metrics.csv"
)


def evaluate_group(group):
    """Calculate common forecasting error metrics."""

    actual = group["target_pm25"].to_numpy(dtype=float)
    predicted = group["prediction"].to_numpy(dtype=float)

    error = predicted - actual

    return pd.Series({
        "samples": len(group),
        "mae": round(np.mean(np.abs(error)), 4),
        "rmse": round(np.sqrt(np.mean(error ** 2)), 4),
        "bias": round(np.mean(error), 4),
    })


def main():
    print("AirScope | Persistence baseline")

    df = pd.read_parquet(FEATURES_FILE)

    if df.empty:
        raise ValueError("No forecasting features available.")

    # Persistence uses only the observation at time t.
    df["prediction"] = df["pm25_current"]

    df["absolute_error"] = (
        df["prediction"] - df["target_pm25"]
    ).abs()

    df["squared_error"] = (
        df["prediction"] - df["target_pm25"]
    ) ** 2

    metrics = (
        df.groupby(
            ["city", "horizon_hours", "partition"]
        )
        .apply(
            evaluate_group,
            include_groups=False,
        )
        .reset_index()
    )

    PROCESSED.mkdir(parents=True, exist_ok=True)

    df.to_parquet(PREDICTIONS_FILE, index=False)
    metrics.to_csv(METRICS_FILE, index=False)

    print("\nBaseline metrics (µg/m³)")
    print(metrics.to_string(index=False))

    print("\nNotes:")
    print("- MAE: average absolute forecasting error.")
    print("- RMSE: emphasizes larger prediction errors.")
    print("- Bias: positive means overprediction.")
    print("- Missing partition rows mean no eligible examples.")

    print(
        f"\nSaved: {PREDICTIONS_FILE.relative_to(ROOT)}"
    )
    print(f"Saved: {METRICS_FILE.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
