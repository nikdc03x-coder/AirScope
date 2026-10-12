
"""
AirScope | nik
Build leakage-safe PM2.5 forecasting examples.

For each station and forecast origin:
- Use current and past observations only.
- Match future targets by exact UTC timestamp.
- Respect source quality eligibility.
- Never fill missing values or invent hours.
- Keep origins and targets in the same data partition.
"""

from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
PROCESSED = ROOT / "data" / "processed"

INPUT_FILE = PROCESSED / "airscope_pm25_unified.parquet"
OUTPUT_FILE = PROCESSED / "airscope_forecast_features.parquet"

LAGS = [1, 3, 6, 12, 24]
HORIZONS = [6, 12, 24]


def build_station_features(station):
    """Build exact-time features for one monitoring station."""

    station = station.sort_values("timestamp_utc").copy()

    if station["timestamp_utc"].duplicated().any():
        raise ValueError("Duplicate timestamps within a station.")

    # The index contains only real source observation times.
    station = station.set_index("timestamp_utc")

    # Exclude readings not eligible for primary ML analysis.
    valid_values = station["pm25_ugm3"].where(
        station["is_training_eligible"].fillna(False)
    )

    origins = pd.DatetimeIndex(station.index)

    base = pd.DataFrame({
        "city": station["city"].to_numpy(),
        "station_id": station["station_id"].to_numpy(),
        "station_name": station["station_name"].to_numpy(),
        "forecast_origin_utc": origins,
        "origin_partition": station["partition"].to_numpy(),
        "pm25_current": valid_values.to_numpy(),
    })

    # Reindex by exact elapsed hours, not row positions.
    # A missing source hour therefore stays missing.
    for lag in LAGS:
        earlier_times = origins - pd.Timedelta(hours=lag)

        base[f"pm25_lag_{lag}h"] = (
            valid_values.reindex(earlier_times).to_numpy()
        )

    examples = []

    for horizon in HORIZONS:
        future_times = origins + pd.Timedelta(hours=horizon)

        frame = base.copy()

        frame["horizon_hours"] = horizon
        frame["target_timestamp_utc"] = future_times

        frame["target_pm25"] = (
            valid_values.reindex(future_times).to_numpy()
        )

        frame["target_partition"] = (
            station["partition"]
            .reindex(future_times)
            .to_numpy()
        )

        required = [
            "pm25_current",
            *[f"pm25_lag_{lag}h" for lag in LAGS],
            "target_pm25",
        ]

        # Drop incomplete ML examples only.
        # The original unified dataset stays unchanged.
        frame = frame.dropna(subset=required)

        # Keep the training, validation, and test evaluation
        # boundaries separate.
        frame = frame[
            frame["origin_partition"]
            == frame["target_partition"]
        ].copy()

        frame["partition"] = frame["target_partition"]

        examples.append(frame)

    return pd.concat(examples, ignore_index=True)


def main():
    print("AirScope | Build forecasting features")

    df = pd.read_parquet(INPUT_FILE)

    required = [
        "city",
        "station_id",
        "station_name",
        "timestamp_utc",
        "pm25_ugm3",
        "is_training_eligible",
        "partition",
    ]

    missing = [
        col for col in required if col not in df.columns
    ]

    if missing:
        raise ValueError(f"Missing columns: {missing}")

    if not isinstance(
        df["timestamp_utc"].dtype,
        pd.DatetimeTZDtype,
    ):
        raise ValueError("UTC timestamps must be timezone-aware.")

    if str(df["timestamp_utc"].dt.tz) != "UTC":
        raise ValueError("Expected UTC timestamps.")

    frames = []

    for (city, station_id), station in df.groupby(
        ["city", "station_id"], sort=True
    ):
        result = build_station_features(station)
        frames.append(result)

        print(
            f"{city} | {station_id}: "
            f"{len(result):,} prediction examples"
        )

    features = pd.concat(frames, ignore_index=True)

    if features.empty:
        raise RuntimeError("No valid forecasting examples.")

    features = features.sort_values([
        "city",
        "station_id",
        "forecast_origin_utc",
        "horizon_hours",
    ]).reset_index(drop=True)

    # Defensive checks against future-data leakage.
    delta = (
        features["target_timestamp_utc"]
        - features["forecast_origin_utc"]
    )

    assert (
        delta.dt.total_seconds() / 3600
        == features["horizon_hours"]
    ).all()

    assert (
        features["origin_partition"]
        == features["target_partition"]
    ).all()

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    features.to_parquet(OUTPUT_FILE, index=False)

    print("\nForecast examples by city, horizon and partition:")

    print(
        features.groupby(
            ["city", "horizon_hours", "partition"]
        ).size().to_string()
    )

    print(f"\nTotal examples: {len(features):,}")
    print(f"Saved: {OUTPUT_FILE.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
