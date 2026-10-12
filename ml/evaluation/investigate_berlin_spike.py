
"""
AirScope | nik
Investigate the September 2026 Berlin PM2.5 episode.

Compare measured PM2.5 values across monitoring stations.
Check source values, neighboring stations, and persistence.
No observations are modified or removed.
"""

from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "data" / "processed"

OBSERVATIONS_FILE = DATA_DIR / "berlin_pm25_hourly.parquet"
PREDICTIONS_FILE = DATA_DIR / "berlin_ml_predictions.parquet"

STATION_REPORT = DATA_DIR / "berlin_spike_station_summary.csv"
HOURLY_REPORT = DATA_DIR / "berlin_spike_hourly_comparison.csv"
PREDICTION_REPORT = DATA_DIR / "berlin_spike_prediction_errors.csv"

START = pd.Timestamp("2026-09-25", tz="UTC")
END = pd.Timestamp("2026-09-29", tz="UTC")

FOCUS_STATION = "DEBE065"


def load_observations():
    """Select real observations from the investigated period."""

    df = pd.read_parquet(OBSERVATIONS_FILE)

    required = [
        "station_id",
        "station_name",
        "timestamp_utc",
        "pm25_ugm3",
    ]

    missing = [col for col in required if col not in df.columns]

    if missing:
        raise ValueError(f"Missing observation columns: {missing}")

    episode = df.loc[
        (df["timestamp_utc"] >= START)
        & (df["timestamp_utc"] < END)
    ].copy()

    if episode.empty:
        raise ValueError("No measurements in the selected period.")

    return episode


def summarize_stations(episode):
    """Compare episode concentrations across all stations."""

    report = (
        episode.groupby(["station_id", "station_name"])
        .agg(
            available_hours=("pm25_ugm3", "count"),
            missing_values=("pm25_ugm3", lambda x: x.isna().sum()),
            mean_pm25=("pm25_ugm3", "mean"),
            max_pm25=("pm25_ugm3", "max"),
            hours_above_25=("pm25_ugm3", lambda x: (x > 25).sum()),
            hours_above_50=("pm25_ugm3", lambda x: (x > 50).sum()),
        )
        .reset_index()
        .sort_values("max_pm25", ascending=False)
    )

    report.to_csv(STATION_REPORT, index=False)

    return report


def compare_hourly(episode):
    """Compare the focus station with other Berlin stations."""

    pivot = episode.pivot(
        index="timestamp_utc",
        columns="station_id",
        values="pm25_ugm3",
    )

    if FOCUS_STATION not in pivot.columns:
        raise ValueError("Frankfurter Allee is missing.")

    other_stations = pivot.drop(columns=[FOCUS_STATION])

    comparison = pd.DataFrame({
        "timestamp_utc": pivot.index,
        "frankfurter_allee": pivot[FOCUS_STATION],
        "other_stations_median": other_stations.median(axis=1),
        "other_stations_max": other_stations.max(axis=1),
        "other_stations_reporting": other_stations.count(axis=1),
    }).reset_index(drop=True)

    comparison["focus_minus_others_median"] = (
        comparison["frankfurter_allee"]
        - comparison["other_stations_median"]
    )

    comparison.to_csv(HOURLY_REPORT, index=False)

    return comparison


def inspect_predictions():
    """Examine saved model errors without retraining."""

    predictions = pd.read_parquet(PREDICTIONS_FILE)

    selection = predictions.loc[
        (predictions["station_id"] == FOCUS_STATION)
        & (predictions["partition"] == "test")
        & (predictions["target_timestamp_utc"] >= START)
        & (predictions["target_timestamp_utc"] < END)
    ].copy()

    selection["ml_absolute_error"] = (
        selection["ml_prediction"] - selection["actual"]
    ).abs()

    selection["baseline_absolute_error"] = (
        selection["persistence_prediction"] - selection["actual"]
    ).abs()

    selection = selection.sort_values(
        "ml_absolute_error", ascending=False
    )

    selection.to_csv(PREDICTION_REPORT, index=False)

    return selection


def main():
    print("AirScope | Berlin high-PM2.5 investigation")

    episode = load_observations()

    stations = summarize_stations(episode)
    hourly = compare_hourly(episode)
    predictions = inspect_predictions()

    print("\nStation-level episode summary:")
    print(
        stations[
            [
                "station_id",
                "available_hours",
                "max_pm25",
                "hours_above_25",
                "hours_above_50",
            ]
        ].round(2).to_string(index=False)
    )

    print("\nLargest Frankfurter Allee observations:")
    largest = hourly.sort_values(
        "frankfurter_allee", ascending=False
    ).head(10)

    print(
        largest[
            [
                "timestamp_utc",
                "frankfurter_allee",
                "other_stations_median",
                "other_stations_max",
                "other_stations_reporting",
            ]
        ].to_string(index=False)
    )

    print("\nLargest saved ML errors at Frankfurter Allee:")
    print(
        predictions[
            [
                "horizon_hours",
                "target_timestamp_utc",
                "actual",
                "ml_prediction",
                "persistence_prediction",
                "ml_absolute_error",
            ]
        ].head(10).to_string(index=False)
    )

    print("\nReports saved:")
    print(STATION_REPORT.relative_to(ROOT))
    print(HOURLY_REPORT.relative_to(ROOT))
    print(PREDICTION_REPORT.relative_to(ROOT))

    print(
        "\nNote: A high or isolated reading is not "
        "automatically invalid."
    )


if __name__ == "__main__":
    main()
