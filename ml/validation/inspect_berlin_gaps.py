
"""
AirScope | nik
Investigate missing Berlin hourly observation slots.

Identify consecutive gaps and check whether missing
timestamps are shared across monitoring stations.
"""

from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[2]

DATA_FILE = ROOT / "data/processed/berlin_pm25_hourly.parquet"
OUTPUT_FILE = ROOT / "data/processed/berlin_missing_gaps.csv"


def main():
    print("AirScope | Berlin missing-hour investigation")

    df = pd.read_parquet(DATA_FILE)

    expected = pd.date_range(
        start="2025-01-01 00:00:00+00:00",
        end="2026-10-11 23:00:00+00:00",
        freq="h",
    )

    station_gaps = {}

    for station_id, station_data in df.groupby("station_id"):
        actual = pd.DatetimeIndex(station_data["timestamp_utc"])
        missing = expected.difference(actual)

        station_gaps[station_id] = set(missing)

        print(f"{station_id}: {len(missing)} missing hours")

    shared = set.intersection(*station_gaps.values())

    print(f"\nMissing in every station: {len(shared)}")

    reference_station = next(iter(station_gaps))
    identical = all(
        gaps == station_gaps[reference_station]
        for gaps in station_gaps.values()
    )

    print(f"All station gaps identical: {identical}")

    if not shared:
        print("No shared missing timestamps found.")
        return

    missing_df = pd.DataFrame({
        "timestamp_utc": sorted(shared)
    })

    # Start a new gap when consecutive missing timestamps
    # are separated by more than one hour.
    missing_df["gap_group"] = (
        missing_df["timestamp_utc"]
        .diff()
        .gt(pd.Timedelta(hours=1))
        .cumsum()
    )

    gaps = (
        missing_df.groupby("gap_group")
        .agg(
            gap_start=("timestamp_utc", "min"),
            gap_end=("timestamp_utc", "max"),
            missing_hours=("timestamp_utc", "size"),
        )
        .reset_index(drop=True)
    )

    gaps = gaps.sort_values(
        "missing_hours",
        ascending=False,
    )

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    gaps.to_csv(OUTPUT_FILE, index=False)

    print("\nLargest shared gaps:")
    print(gaps.head(20).to_string(index=False))

    print(f"\nTotal gap periods: {len(gaps)}")
    print(f"Saved: {OUTPUT_FILE.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
