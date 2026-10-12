
"""
AirScope | nik
Audit official Berlin PM2.5 observations.

Check station coverage, duplicate hours, missing values,
timestamp consistency, and suspicious measurements.

This script reports problems without changing source data.
"""

from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[2]

DATA_FILE = (
    ROOT / "data" / "processed" / "berlin_pm25_hourly.parquet"
)

STATIONS_FILE = (
    ROOT / "data" / "processed" / "berlin_pm25_stations.csv"
)

REPORT_FILE = (
    ROOT / "data" / "processed" / "berlin_quality_report.csv"
)

EXPECTED_START = pd.Timestamp(
    "2025-01-01 00:00:00",
    tz="UTC",
)

EXPECTED_END = pd.Timestamp(
    "2026-10-11 23:00:00",
    tz="UTC",
)


def audit_station(station_data, station_name):
    """Check one station's hourly PM2.5 observations."""

    df = station_data.sort_values("timestamp_utc").copy()

    timestamps = df["timestamp_utc"]

    duplicates = int(timestamps.duplicated().sum())

    # Find missing hourly slots within the station's
    # observed time range.
    hourly_index = pd.date_range(
        start=timestamps.min(),
        end=timestamps.max(),
        freq="h",
        tz="UTC",
    )

    missing_hours = len(
        hourly_index.difference(
            pd.DatetimeIndex(timestamps)
        )
    )

    # Check missing PM2.5 values separately from missing
    # timestamps. They represent different quality issues.
    missing_values = int(df["pm25_ugm3"].isna().sum())

    negative_values = int(
        (df["pm25_ugm3"] < 0).sum()
    )

    high_values = int(
        (df["pm25_ugm3"] > 500).sum()
    )

    # These are diagnostic flags, not automatic exclusions.
    return {
        "station_id": df["station_id"].iloc[0],
        "station_name": station_name,
        "total_records": len(df),
        "first_timestamp": timestamps.min(),
        "last_timestamp": timestamps.max(),
        "duplicate_hours": duplicates,
        "missing_hour_slots": missing_hours,
        "missing_pm25_values": missing_values,
        "negative_values": negative_values,
        "values_above_500": high_values,
        "mean_pm25": round(
            df["pm25_ugm3"].mean(), 2
        ),
        "max_pm25": df["pm25_ugm3"].max(),
    }


def main():
    print("AirScope | Berlin PM2.5 quality audit")

    if not DATA_FILE.exists():
        raise FileNotFoundError(
            "Berlin Parquet file not found. "
            "Run the downloader first."
        )

    df = pd.read_parquet(DATA_FILE)

    required_columns = [
        "station_id",
        "station_name",
        "timestamp_utc",
        "pm25_ugm3",
    ]

    missing_columns = [
        col for col in required_columns
        if col not in df.columns
    ]

    if missing_columns:
        raise ValueError(
            f"Missing required columns: {missing_columns}"
        )

    if df.empty:
        raise ValueError("Berlin dataset is empty.")

    if not isinstance(
        df["timestamp_utc"].dtype,
        pd.DatetimeTZDtype,
    ):
        raise ValueError(
            "Berlin timestamps must be timezone-aware."
        )

    if str(df["timestamp_utc"].dt.tz) != "UTC":
        raise ValueError(
            "Berlin timestamps must use UTC."
        )

    report_rows = []

    for station_name, station_data in df.groupby(
        "station_name"
    ):
        report_rows.append(
            audit_station(station_data, station_name)
        )

    report = pd.DataFrame(report_rows)

    REPORT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    report.to_csv(
        REPORT_FILE,
        index=False,
    )

    print("\nDataset summary")
    print(f"Total rows: {len(df):,}")
    print(f"Stations: {df['station_id'].nunique()}")
    print(
        "Date range: "
        f"{df['timestamp_utc'].min()} to "
        f"{df['timestamp_utc'].max()}"
    )

    print("\nQuality summary")
    print(
        "Duplicate station-hours:",
        report["duplicate_hours"].sum(),
    )
    print(
        "Missing hour slots:",
        report["missing_hour_slots"].sum(),
    )
    print(
        "Missing PM2.5 values:",
        report["missing_pm25_values"].sum(),
    )
    print(
        "Negative values:",
        report["negative_values"].sum(),
    )
    print(
        "Values above 500:",
        report["values_above_500"].sum(),
    )

    print("\nStation report:")
    print(
        report[
            [
                "station_name",
                "total_records",
                "missing_hour_slots",
                "missing_pm25_values",
            ]
        ].to_string(index=False)
    )

    # Verify the historical coverage before training.
    actual_start = df["timestamp_utc"].min()
    actual_end = df["timestamp_utc"].max()

    if (
        actual_start > EXPECTED_START
        or actual_end < EXPECTED_END
    ):
        print(
            "\nWARNING: Historical coverage is incomplete."
        )
        print(
            "The file may still contain the short test "
            "rather than the full 22-month download."
        )
    else:
        print(
            "\nHistorical date boundaries are covered."
        )

    if STATIONS_FILE.exists():
        expected_stations = pd.read_csv(
            STATIONS_FILE
        )["station_code"].nunique()

        if df["station_id"].nunique() != expected_stations:
            print(
                "\nWARNING: Station count does not match "
                "the verified station registry."
            )

    print(f"\nSaved: {REPORT_FILE.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
