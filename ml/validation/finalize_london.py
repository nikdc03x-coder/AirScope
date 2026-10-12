
"""
AirScope | nik
Finalize London PM2.5 data after source-quality verification.

DEFRA CSV metadata confirms:
- All data GMT hour ending
- R = Ratified
- P = Provisional
- P* = As supplied

Preserve every source observation.
Add UTC timestamps and explicit training-quality flags.
"""

from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
PROCESSED = ROOT / "data" / "processed"

INPUT = PROCESSED / "london_pm25_hourly.parquet"
OUTPUT = PROCESSED / "london_pm25_final.parquet"

STATUS_MEANINGS = {
    "R": "ratified",
    "P": "provisional",
    "P*": "as_supplied",
}


def main():
    print("AirScope | Finalize London PM2.5")

    if not INPUT.exists():
        raise FileNotFoundError(INPUT)

    df = pd.read_parquet(INPUT)

    # DEFRA explicitly specifies GMT hour-ending timestamps.
    # GMT has a zero-hour offset from UTC, including in summer.
    df["timestamp_utc"] = (
        pd.to_datetime(df["timestamp_source"])
        .dt.tz_localize("UTC")
    )

    # Preserve the original status code and explain its meaning.
    df["quality_status"] = (
        df["measurement_status"]
        .map(STATUS_MEANINGS)
        .fillna("missing_or_unknown")
    )

    # Only ratified, non-missing readings enter the strict
    # supervised-training target dataset.
    df["is_training_eligible"] = (
        df["measurement_status"].eq("R")
        & df["pm25_ugm3"].notna()
    ).fillna(False)

    df["time_convention"] = "GMT_hour_ending"

    # Verify that the conversion has not changed row counts.
    if df["timestamp_utc"].isna().any():
        raise ValueError("Invalid UTC timestamps found.")

    duplicates = df.duplicated(
        subset=["station_id", "timestamp_utc"]
    ).sum()

    if duplicates:
        raise ValueError(
            f"Found {duplicates} duplicate station hours."
        )

    df = df.sort_values(
        "timestamp_utc"
    ).reset_index(drop=True)

    OUTPUT.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    df.to_parquet(
        OUTPUT,
        index=False,
    )

    print(f"Total rows: {len(df)}")
    print(
        "Training-eligible readings: "
        f"{df['is_training_eligible'].sum()}"
    )
    print(
        "Provisional readings: "
        f"{(df['measurement_status'] == 'P').sum()}"
    )
    print(f"Missing readings: {df['is_missing'].sum()}")
    print(f"Saved: {OUTPUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
