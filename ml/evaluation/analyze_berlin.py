
"""
AirScope | nik
Analyze Berlin PM2.5 model errors.

Compare gradient boosting with persistence:
- Separately for every monitoring station
- Across forecast horizons
- During higher-PM2.5 observations
- On the largest individual prediction errors

Evaluation uses saved predictions, not training data.
"""

from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "data" / "processed"

INPUT_FILE = DATA_DIR / "berlin_ml_predictions.parquet"

STATION_REPORT = DATA_DIR / "berlin_station_metrics.csv"
POLLUTION_REPORT = DATA_DIR / "berlin_pollution_metrics.csv"
WORST_ERRORS = DATA_DIR / "berlin_worst_errors.csv"

# Diagnostic categories, not official health thresholds.
POLLUTION_BINS = [-np.inf, 10, 25, np.inf]
POLLUTION_LABELS = ["below_10", "10_to_25", "above_25"]


def calculate_metrics(group):
    """Evaluate both predictors using identical rows."""

    actual = group["actual"].to_numpy(dtype=float)
    ml = group["ml_prediction"].to_numpy(dtype=float)
    baseline = group["persistence_prediction"].to_numpy(dtype=float)

    ml_error = ml - actual
    baseline_error = baseline - actual

    ml_mae = np.mean(np.abs(ml_error))
    baseline_mae = np.mean(np.abs(baseline_error))

    ml_rmse = np.sqrt(np.mean(ml_error ** 2))
    baseline_rmse = np.sqrt(np.mean(baseline_error ** 2))

    improvement = (
        100 * (baseline_mae - ml_mae) / baseline_mae
        if baseline_mae > 0
        else np.nan
    )

    return pd.Series({
        "samples": len(group),
        "ml_mae": round(ml_mae, 4),
        "baseline_mae": round(baseline_mae, 4),
        "mae_improvement_pct": round(improvement, 2),
        "ml_rmse": round(ml_rmse, 4),
        "baseline_rmse": round(baseline_rmse, 4),
        "ml_bias": round(np.mean(ml_error), 4),
        "baseline_bias": round(np.mean(baseline_error), 4),
    })


def grouped_metrics(df, columns):
    """Produce metrics for the requested comparison groups."""

    return (
        df.groupby(columns, observed=True)
        .apply(calculate_metrics, include_groups=False)
        .reset_index()
    )


def main():
    print("AirScope | Berlin model error analysis")

    df = pd.read_parquet(INPUT_FILE)

    required = [
        "station_id",
        "horizon_hours",
        "partition",
        "forecast_origin_utc",
        "target_timestamp_utc",
        "actual",
        "ml_prediction",
        "persistence_prediction",
    ]

    missing = [
        name for name in required
        if name not in df.columns
    ]

    if missing:
        raise ValueError(f"Missing columns: {missing}")

    # Inspect the held-out test period only.
    test = df.loc[df["partition"] == "test"].copy()

    if test.empty:
        raise ValueError("No held-out test predictions found.")

    if test[[
        "actual", "ml_prediction", "persistence_prediction"
    ]].isna().any().any():
        raise ValueError("Test predictions contain null values.")

    test["ml_absolute_error"] = (
        test["ml_prediction"] - test["actual"]
    ).abs()

    test["baseline_absolute_error"] = (
        test["persistence_prediction"] - test["actual"]
    ).abs()

    # Station-level comparison.
    stations = grouped_metrics(
        test,
        ["station_id", "horizon_hours"],
    )

    stations.to_csv(STATION_REPORT, index=False)

    # These bins help reveal performance on elevated PM2.5.
    # They are not claimed as regulatory categories.
    test["pollution_category"] = pd.cut(
        test["actual"],
        bins=POLLUTION_BINS,
        labels=POLLUTION_LABELS,
        include_lowest=True,
    )

    pollution = grouped_metrics(
        test.dropna(subset=["pollution_category"]),
        ["horizon_hours", "pollution_category"],
    )

    pollution.to_csv(POLLUTION_REPORT, index=False)

    # Find the largest individual ML errors.
    worst = test.sort_values(
        "ml_absolute_error",
        ascending=False,
    ).head(30)

    worst_columns = [
        "station_id",
        "horizon_hours",
        "forecast_origin_utc",
        "target_timestamp_utc",
        "actual",
        "ml_prediction",
        "persistence_prediction",
        "ml_absolute_error",
        "baseline_absolute_error",
    ]

    worst[worst_columns].to_csv(
        WORST_ERRORS,
        index=False,
    )

    print("\nTest performance by pollution level:")
    print(
        pollution[
            [
                "horizon_hours",
                "pollution_category",
                "samples",
                "ml_mae",
                "baseline_mae",
                "mae_improvement_pct",
            ]
        ].to_string(index=False)
    )

    print("\nStations where ML is worse on MAE:")
    worse = stations[
        stations["mae_improvement_pct"] < 0
    ]

    if worse.empty:
        print("None")
    else:
        print(
            worse[
                [
                    "station_id",
                    "horizon_hours",
                    "samples",
                    "ml_mae",
                    "baseline_mae",
                    "mae_improvement_pct",
                ]
            ].to_string(index=False)
        )

    print("\nLargest ML prediction errors:")
    print(
        worst[worst_columns]
        .head(10)
        .round(3)
        .to_string(index=False)
    )

    print("\nSaved:")
    print(STATION_REPORT.relative_to(ROOT))
    print(POLLUTION_REPORT.relative_to(ROOT))
    print(WORST_ERRORS.relative_to(ROOT))


if __name__ == "__main__":
    main()
