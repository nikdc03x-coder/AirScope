
"""
AirScope | nik
Check whether Berlin's missing hours are absent from
the original UBA API responses or lost during parsing.

Read cached JSON only. Do not modify observations.
"""

import json
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[2]

CACHE_DIR = ROOT / "data/raw/uba_monthly"

DATA_FILE = ROOT / "data/processed/berlin_pm25_hourly.parquet"

STATION = "DEBE010"

PERIODS = [
    ("2026-08-15", "2026-08-23"),
    ("2026-09-11", "2026-09-13"),
    ("2026-09-19", "2026-09-19"),
]


def parse_source_timestamp(value):
    """Handle UBA's 24:00 midnight notation."""

    text = str(value).strip()

    if text.endswith("24:00:00"):
        day = pd.Timestamp(text[:10])
        return day + pd.Timedelta(days=1)

    return pd.Timestamp(text)


def inspect_cache():
    """Count source timestamps in the relevant monthly files."""

    for month in ["202608", "202609"]:
        files = sorted(CACHE_DIR.glob(f"{STATION}_{month}*.json"))

        print(f"\nCached files for {month}: {len(files)}")

        for path in files:
            payload = json.loads(
                path.read_text(encoding="utf-8")
            )

            data = payload.get("data", {})

            source_times = []

            for observations in data.values():
                if not isinstance(observations, dict):
                    continue

                for timestamp in observations:
                    source_times.append(
                        parse_source_timestamp(timestamp)
                    )

            print(
                f"{path.name}: "
                f"{len(source_times)} source timestamps"
            )

            if source_times:
                print(
                    "  Source range:",
                    min(source_times),
                    "to",
                    max(source_times),
                )


def inspect_missing_periods():
    """Compare expected hours with saved station observations."""

    df = pd.read_parquet(DATA_FILE)

    station = df[df["station_id"] == STATION]

    for start, end in PERIODS:
        start_utc = pd.Timestamp(start, tz="UTC")
        end_utc = (
            pd.Timestamp(end, tz="UTC")
            + pd.Timedelta(hours=23)
        )

        expected = pd.date_range(
            start_utc,
            end_utc,
            freq="h",
        )

        actual = pd.DatetimeIndex(
            station["timestamp_utc"]
        )

        missing = expected.difference(actual)

        print(f"\nPeriod: {start} to {end}")
        print(f"Expected hours: {len(expected)}")
        print(f"Missing hours: {len(missing)}")

        if len(missing):
            print("First missing:", missing[0])
            print("Last missing:", missing[-1])


def main():
    print("AirScope | Berlin raw-gap verification")

    inspect_cache()
    inspect_missing_periods()


if __name__ == "__main__":
    main()
