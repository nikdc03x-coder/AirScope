
"""
AirScope | nik
Build a unified London and Berlin PM2.5 dataset.

- Preserve genuine source observations.
- Keep station identities and quality information.
- Use timezone-aware UTC timestamps.
- Preserve missing measurements without interpolation.
- Create chronological ML partitions.
"""

import json
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "data" / "processed"

LONDON_FILE = DATA_DIR / "london_pm25_final.parquet"
BERLIN_FILE = DATA_DIR / "berlin_pm25_hourly.parquet"

OUTPUT_FILE = DATA_DIR / "airscope_pm25_unified.parquet"
SUMMARY_FILE = DATA_DIR / "airscope_dataset_summary.json"

# Fixed chronological boundaries across both cities.
VALIDATION_START = pd.Timestamp(
    "2026-07-01", tz="UTC"
)
TEST_START = pd.Timestamp(
    "2026-09-01", tz="UTC"
)


def find_column(frame, candidates, dataset):
    """Select an explicitly supported source column."""

    for name in candidates:
        if name in frame.columns:
            return name

    raise ValueError(
        f"{dataset}: PM2.5 column not recognized.\n"
        f"Available columns: {list(frame.columns)}"
    )


def normalize_utc(values, dataset):
    """Require genuine timezone-aware timestamps."""

    if not isinstance(values.dtype, pd.DatetimeTZDtype):
        raise ValueError(
            f"{dataset}: timestamps must be timezone-aware."
        )

    return values.dt.tz_convert("UTC")


def prepare_london():
    """Standardize verified DEFRA London observations."""

    df = pd.read_parquet(LONDON_FILE)

    value_col = find_column(
        df,
        [
            "pm25_ugm3",
            "pm25",
            "pm25_value",
            "pm25_concentration",
        ],
        "London",
    )

    required = [
        "timestamp_utc",
        "quality_status",
        "is_training_eligible",
    ]

    for column in required:
        if column not in df.columns:
            raise ValueError(
                f"London missing required column: {column}"
            )

    result = pd.DataFrame({
        "city": "London",
        "country": "UK",
        "station_id": "CLL2",
        "station_name": "London Bloomsbury",
        "timestamp_utc": normalize_utc(
            df["timestamp_utc"], "London"
        ),
        "pm25_ugm3": pd.to_numeric(
            df[value_col], errors="coerce"
        ),
        "quality_status": df["quality_status"],
        "source": "DEFRA UK-AIR",
        "source_time_convention": "GMT_hour_ending",
        "latitude": pd.NA,
        "longitude": pd.NA,
    })

    # Only ratified London readings enter the primary
    # training dataset.
    result["is_training_eligible"] = (
        df["is_training_eligible"].fillna(False).astype(bool)
        & result["pm25_ugm3"].notna()
    )

    return result


def prepare_berlin():
    """Standardize official UBA station observations."""

    df = pd.read_parquet(BERLIN_FILE)

    required = [
        "timestamp_utc",
        "station_id",
        "station_name",
        "pm25_ugm3",
        "latitude",
        "longitude",
    ]

    for column in required:
        if column not in df.columns:
            raise ValueError(
                f"Berlin missing required column: {column}"
            )

    result = pd.DataFrame({
        "city": "Berlin",
        "country": "Germany",
        "station_id": df["station_id"].astype(str),
        "station_name": df["station_name"],
        "timestamp_utc": normalize_utc(
            df["timestamp_utc"], "Berlin"
        ),
        "pm25_ugm3": pd.to_numeric(
            df["pm25_ugm3"], errors="coerce"
        ),
        # The UBA records do not carry the DEFRA
        # ratified/provisional distinction.
        "quality_status": "not_provided",
        "source": "Umweltbundesamt (UBA)",
        "source_time_convention": "CET_hour_ending",
        "latitude": df["latitude"],
        "longitude": df["longitude"],
    })

    # Eligibility here means an available numeric reading.
    # It does not imply official ratification.
    result["is_training_eligible"] = (
        result["pm25_ugm3"].notna()
    )

    return result


def assign_partition(timestamps):
    """Partition chronologically without random shuffling."""

    partition = pd.Series(
        "train",
        index=timestamps.index,
        dtype="string",
    )

    partition.loc[
        timestamps >= VALIDATION_START
    ] = "validation"

    partition.loc[
        timestamps >= TEST_START
    ] = "test"

    return partition


def main():
    print("AirScope | Build unified ML dataset")

    london = prepare_london()
    berlin = prepare_berlin()

    unified = pd.concat(
        [london, berlin],
        ignore_index=True,
    )

    unified = unified.sort_values(
        ["city", "station_id", "timestamp_utc"]
    ).reset_index(drop=True)

    duplicate_keys = [
        "city",
        "station_id",
        "timestamp_utc",
    ]

    duplicate_count = int(
        unified.duplicated(duplicate_keys).sum()
    )

    if duplicate_count:
        raise ValueError(
            f"Duplicate station-hour records: "
            f"{duplicate_count}"
        )

    unified["partition"] = assign_partition(
        unified["timestamp_utc"]
    )

    # Retain unavailable observations and non-ratified
    # London readings for auditing and dashboard use.
    # Model preparation will apply eligibility rules.
    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    unified.to_parquet(
        OUTPUT_FILE,
        index=False,
    )

    summary = {
        "project": "AirScope",
        "pollutant": "PM2.5",
        "unit": "ug/m3",
        "total_rows": int(len(unified)),
        "cities": {},
        "partitions": {},
        "duplicate_station_hours": duplicate_count,
        "validation_start_utc": str(VALIDATION_START),
        "test_start_utc": str(TEST_START),
        "missing_values_preserved": True,
        "interpolation_applied": False,
    }

    for city, frame in unified.groupby("city"):
        summary["cities"][city] = {
            "rows": int(len(frame)),
            "stations": int(frame["station_id"].nunique()),
            "missing_values": int(
                frame["pm25_ugm3"].isna().sum()
            ),
            "training_eligible": int(
                frame["is_training_eligible"].sum()
            ),
            "first_utc": str(
                frame["timestamp_utc"].min()
            ),
            "last_utc": str(
                frame["timestamp_utc"].max()
            ),
        }

    for partition, frame in unified.groupby("partition"):
        summary["partitions"][partition] = {
            "rows": int(len(frame)),
            "eligible_rows": int(
                frame["is_training_eligible"].sum()
            ),
        }

    SUMMARY_FILE.write_text(
        json.dumps(summary, indent=2),
        encoding="utf-8",
    )

    print("\nCity summary")
    print(
        unified.groupby("city").agg(
            records=("pm25_ugm3", "size"),
            stations=("station_id", "nunique"),
            eligible=("is_training_eligible", "sum"),
        ).to_string()
    )

    print("\nChronological partitions")
    print(
        unified.groupby(
            ["city", "partition"]
        ).size().to_string()
    )

    print("\nQuality checks")
    print(f"Duplicate station-hours: {duplicate_count}")
    print(
        "Missing measurements preserved:",
        int(unified["pm25_ugm3"].isna().sum())
    )

    print(f"\nSaved: {OUTPUT_FILE.relative_to(ROOT)}")
    print(f"Saved: {SUMMARY_FILE.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
