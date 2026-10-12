
"""
AirScope | nik
Audit unusual Berlin PM2.5 readings.

- Inspect original UBA component and scope metadata.
- Compare stations at matching UTC timestamps.
- Flag unusually isolated elevated measurements.
- Never remove, replace, or interpolate observations.

These flags are diagnostic, not proof of invalid data.
"""

import json
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]

DATA_DIR = ROOT / "data" / "processed"
RAW_DIR = ROOT / "data" / "raw" / "uba_monthly"

INPUT_FILE = DATA_DIR / "berlin_pm25_hourly.parquet"

ANOMALY_FILE = DATA_DIR / "berlin_spatial_anomalies.csv"
SOURCE_FILE = DATA_DIR / "berlin_spike_source_check.csv"

FOCUS_STATION = "DEBE065"

# Diagnostic criteria, not regulatory thresholds.
MIN_OTHER_STATIONS = 5
MIN_CONCENTRATION = 25
MIN_DIFFERENCE = 20
MIN_RATIO = 5


def check_source_records():
    """Inspect the original cached September UBA response."""

    path = (
        RAW_DIR
        / f"{FOCUS_STATION}_20260901_20260930.json"
    )

    if not path.exists():
        raise FileNotFoundError(
            f"Original UBA cache not found: {path}"
        )

    payload = json.loads(
        path.read_text(encoding="utf-8")
    )

    fields = payload["indices"]["data"]["station id"]["date start"]

    component_idx = fields.index("component id")
    scope_idx = fields.index("scope id")
    value_idx = fields.index("value")
    end_idx = fields.index("date end")
    index_idx = fields.index("index")

    records = []

    for station_id, observations in payload["data"].items():
        for start, values in observations.items():

            records.append({
                "source_station_id": station_id,
                "source_start": start,
                "source_end": values[end_idx],
                "component_id": values[component_idx],
                "scope_id": values[scope_idx],
                "pm25_source_value": values[value_idx],
                "source_index": values[index_idx],
            })

    frame = pd.DataFrame(records)

    if frame.empty:
        raise ValueError("No cached source records found.")

    if not (frame["component_id"] == 9).all():
        raise ValueError(
            "Unexpected pollutant component in PM2.5 cache."
        )

    frame.to_csv(SOURCE_FILE, index=False)

    print("\nOriginal UBA source inspection")
    print(f"Source records: {len(frame)}")
    print(
        "Scope ID counts:",
        dict(Counter(frame["scope_id"])),
    )
    print(
        "Source index counts:",
        dict(Counter(frame["source_index"].astype(str))),
    )

    print("\nHighest cached source readings:")
    print(
        frame.sort_values(
            "pm25_source_value",
            ascending=False,
        )[
            [
                "source_start",
                "source_end",
                "scope_id",
                "pm25_source_value",
                "source_index",
            ]
        ].head(10).to_string(index=False)
    )


def audit_spatial_values():
    """Compare each station with other stations at the same hour."""

    df = pd.read_parquet(INPUT_FILE)

    required = {
        "station_id",
        "station_name",
        "timestamp_utc",
        "pm25_ugm3",
    }

    missing = required - set(df.columns)

    if missing:
        raise ValueError(f"Missing columns: {sorted(missing)}")

    if df.duplicated(
        ["station_id", "timestamp_utc"]
    ).any():
        raise ValueError("Duplicate station-hour records.")

    pivot = df.pivot(
        index="timestamp_utc",
        columns="station_id",
        values="pm25_ugm3",
    ).sort_index()

    results = []

    for station_id in pivot.columns:
        current = pivot[station_id]

        others = pivot.drop(columns=station_id)

        peer_median = others.median(axis=1)
        peer_max = others.max(axis=1)
        peer_count = others.count(axis=1)

        difference = current - peer_median

        # NaN when the peer median is zero: ratios are
        # undefined and must not be treated as infinity.
        ratio = current / peer_median.replace(0, np.nan)

        flagged = (
            current.notna()
            & (peer_count >= MIN_OTHER_STATIONS)
            & (current > MIN_CONCENTRATION)
            & (difference > MIN_DIFFERENCE)
            & (ratio >= MIN_RATIO)
        )

        if not flagged.any():
            continue

        station_name = (
            df.loc[
                df["station_id"] == station_id,
                "station_name",
            ].iloc[0]
        )

        flagged_times = current.index[flagged]

        station_flags = pd.DataFrame({
            "station_id": station_id,
            "station_name": station_name,
            "timestamp_utc": flagged_times,
            "pm25_ugm3": current.loc[
                flagged_times
            ].to_numpy(),
            "other_stations_median": peer_median.loc[
                flagged_times
            ].to_numpy(),
            "other_stations_max": peer_max.loc[
                flagged_times
            ].to_numpy(),
            "other_stations_reporting": peer_count.loc[
                flagged_times
            ].to_numpy(),
            "difference_from_peer_median": difference.loc[
                flagged_times
            ].to_numpy(),
            "ratio_to_peer_median": ratio.loc[
                flagged_times
            ].to_numpy(),
        })

        results.append(station_flags)

    columns = [
        "station_id",
        "station_name",
        "timestamp_utc",
        "pm25_ugm3",
        "other_stations_median",
        "other_stations_max",
        "other_stations_reporting",
        "difference_from_peer_median",
        "ratio_to_peer_median",
    ]

    if results:
        anomalies = pd.concat(
            results,
            ignore_index=True,
        )

        anomalies = anomalies.sort_values(
            "difference_from_peer_median",
            ascending=False,
        )
    else:
        anomalies = pd.DataFrame(columns=columns)

    anomalies.to_csv(ANOMALY_FILE, index=False)

    print("\nSpatial anomaly summary")
    print(f"Total flagged station-hours: {len(anomalies)}")

    if not anomalies.empty:
        print("\nFlags per station:")
        print(
            anomalies.groupby("station_id")
            .size()
            .sort_values(ascending=False)
            .to_string()
        )

        print("\nLargest spatial differences:")
        print(
            anomalies[
                [
                    "station_id",
                    "timestamp_utc",
                    "pm25_ugm3",
                    "other_stations_median",
                    "ratio_to_peer_median",
                ]
            ].head(10).to_string(index=False)
        )

    print(f"\nSaved: {ANOMALY_FILE.relative_to(ROOT)}")


def main():
    print("AirScope | Berlin spatial anomaly audit")

    DATA_DIR.mkdir(parents=True, exist_ok=True)

    check_source_records()
    audit_spatial_values()

    print(f"Saved: {SOURCE_FILE.relative_to(ROOT)}")

    print(
        "\nAll source measurements remain unchanged."
    )


if __name__ == "__main__":
    main()
