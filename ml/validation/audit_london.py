
"""
AirScope | nik
Audit official London PM2.5 data before ML training.

Checks:
- Original DEFRA CSV metadata
- Quality-status distribution
- Missing and duplicate timestamps
- Hourly time continuity
- Ratified measurement availability
"""

import json
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "data" / "raw"
PROCESSED = ROOT / "data" / "processed"

INPUT = PROCESSED / "london_pm25_hourly.parquet"
REPORT = PROCESSED / "london_quality_report.json"

YEARS = (2025, 2026)

STATUS_MEANINGS = {
    "R": "Ratified",
    "P": "Provisional",
    "A": "As supplied",
    "V": "Validated",
    "S": "Suspect",
}


def inspect_source_headers():
    """Read the original metadata supplied by DEFRA."""

    metadata = {}

    for year in YEARS:
        path = RAW / f"CLL2_{year}.csv"

        if not path.exists():
            raise FileNotFoundError(path)

        with path.open(
            "r",
            encoding="utf-8-sig",
            errors="replace",
        ) as file:
            lines = [
                next(file).strip()
                for _ in range(4)
            ]

        print(f"\nDEFRA metadata — {year}")

        for line in lines:
            print(" ", line)

        metadata[str(year)] = lines

    return metadata


def main():
    print("AirScope | London PM2.5 quality audit")

    metadata = inspect_source_headers()

    if not INPUT.exists():
        raise FileNotFoundError(
            f"Run normalization first: {INPUT}"
        )

    df = pd.read_parquet(INPUT)

    df = df.sort_values(
        "timestamp_source"
    ).reset_index(drop=True)

    # Count measurement status codes without changing them.
    status_counts = (
        df["measurement_status"]
        .fillna("MISSING_STATUS")
        .value_counts()
        .to_dict()
    )

    print("\nMeasurement status distribution:")

    for code, count in status_counts.items():
        meaning = STATUS_MEANINGS.get(
            code,
            "Unknown or missing status",
        )

        print(f"  {code}: {count} ({meaning})")

    # Audit timestamp consistency.
    timestamps = df["timestamp_source"]

    duplicate_count = int(
        timestamps.duplicated().sum()
    )

    expected_hours = pd.date_range(
        start=timestamps.min(),
        end=timestamps.max(),
        freq="h",
    )

    missing_hours = expected_hours.difference(
        pd.DatetimeIndex(timestamps)
    )

    extra_hours = pd.DatetimeIndex(
        timestamps
    ).difference(expected_hours)

    # Ratified data is our strict training-data candidate.
    ratified = (
        df["measurement_status"].eq("R")
        & df["pm25_ugm3"].notna()
    )

    missing_values = int(
        df["pm25_ugm3"].isna().sum()
    )

    report = {
        "station_id": "CLL2",
        "station_name": "London Bloomsbury",
        "source": "DEFRA UK-AIR",
        "total_rows": int(len(df)),
        "available_measurements": int(
            df["pm25_ugm3"].notna().sum()
        ),
        "missing_measurements": missing_values,
        "ratified_available_measurements": int(
            ratified.sum()
        ),
        "status_counts": {
            str(code): int(count)
            for code, count in status_counts.items()
        },
        "first_timestamp": str(timestamps.min()),
        "last_timestamp": str(timestamps.max()),
        "duplicate_timestamps": duplicate_count,
        "missing_hour_slots": int(len(missing_hours)),
        "unexpected_hour_slots": int(len(extra_hours)),
        "source_metadata": metadata,
        "timestamp_note": (
            "DEFRA CSV documentation describes GMT "
            "hour-ending timestamps. Confirm the metadata "
            "in both downloaded source files."
        ),
    }

    print("\nQuality summary")
    print(f"Total rows: {report['total_rows']}")
    print(f"Missing readings: {missing_values}")
    print(
        "Ratified readings available: "
        f"{report['ratified_available_measurements']}"
    )
    print(f"Duplicate hours: {duplicate_count}")
    print(f"Missing hour slots: {len(missing_hours)}")
    print(f"Unexpected hour slots: {len(extra_hours)}")

    REPORT.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    REPORT.write_text(
        json.dumps(
            report,
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    print(f"\nReport saved: {REPORT.relative_to(ROOT)}")

    if duplicate_count or len(missing_hours) or len(extra_hours):
        raise ValueError(
            "Timestamp continuity audit failed. "
            "Review the report before training."
        )


if __name__ == "__main__":
    main()
