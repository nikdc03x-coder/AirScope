
"""
AirScope | nik
Normalize official DEFRA hourly PM2.5 measurements.

- Read London Bloomsbury CSV files for 2025 and 2026.
- Handle HTML-formatted pollutant names.
- Parse hour-ending times, including 24:00.
- Preserve missing values, quality status, and units.
- Reject invalid timestamps and duplicate station hours.
- Save normalized observations as Parquet.

Important:
The source timestamp timezone has not yet been verified.
We preserve source clock times rather than falsely labeling them UTC.
"""

import csv
import re
from pathlib import Path

import pandas as pd


# --------------------------------------------------
# Configuration
# --------------------------------------------------

ROOT = Path(__file__).resolve().parents[2]

RAW_DIR = ROOT / "data" / "raw"
OUTPUT_DIR = ROOT / "data" / "processed"

OUTPUT_FILE = OUTPUT_DIR / "london_pm25_hourly.parquet"

SITE_CODE = "CLL2"
SITE_NAME = "London Bloomsbury"

LATITUDE = 51.522290
LONGITUDE = -0.125889

YEARS = (2025, 2026)


# --------------------------------------------------
# Detect the real CSV header
# --------------------------------------------------

def find_header(lines):
    """Find the row containing the Date and time headers."""

    for index, line in enumerate(lines[:100]):
        columns = next(csv.reader([line]))

        names = [
            str(column).strip().lower()
            for column in columns
        ]

        if (
            "date" in names
            and "time" in names
            and len(columns) >= 3
        ):
            return index

    raise ValueError(
        "Could not find the DEFRA CSV header."
    )


# --------------------------------------------------
# Identify PM2.5 and timestamp columns
# --------------------------------------------------

def find_pm25_column(columns):
    """Recognize PM2.5 even when the header contains HTML."""

    for column in columns:

        # Remove tags like <sub> and </sub>.
        clean_name = re.sub(
            r"<[^>]+>",
            "",
            str(column),
        )

        # PM<sub>2.5</sub> becomes pm25.
        normalized = re.sub(
            r"[^a-z0-9]",
            "",
            clean_name.lower(),
        )

        if "pm25" in normalized:
            return column

    raise ValueError(
        f"PM2.5 column not found: {list(columns)}"
    )


def find_time_columns(columns):
    """Find the exact Date and time columns."""

    lookup = {
        str(column).strip().lower(): column
        for column in columns
    }

    if "date" not in lookup or "time" not in lookup:
        raise ValueError(
            "DEFRA CSV must contain Date and time columns."
        )

    return lookup["date"], lookup["time"]


# --------------------------------------------------
# Parse source timestamps
# --------------------------------------------------

def parse_defra_timestamps(date_values, time_values):
    """
    Parse DEFRA hourly source clock times.

    Example:
        01-01-2025 01:00 -> 2025-01-01 01:00
        01-01-2025 24:00 -> 2025-01-02 00:00

    These are timezone-naive source clock times.
    They are not labeled UTC until verified.
    """

    dates = pd.to_datetime(
        date_values.astype("string").str.strip(),
        format="%d-%m-%Y",
        errors="coerce",
    )

    times = time_values.astype("string").str.strip()

    parts = times.str.extract(
        r"^(\d{1,2}):(\d{2})$"
    )

    hours = pd.to_numeric(
        parts[0],
        errors="coerce",
    )

    minutes = pd.to_numeric(
        parts[1],
        errors="coerce",
    )

    invalid = (
        dates.isna()
        | hours.isna()
        | minutes.isna()
        | ~hours.between(0, 24)
        | ~minutes.between(0, 59)
        | ((hours == 24) & (minutes != 0))
    )

    if invalid.any():
        examples = pd.DataFrame({
            "date": date_values,
            "time": time_values,
        }).loc[invalid].head(5)

        raise ValueError(
            "Invalid DEFRA date/time values:\n"
            f"{examples.to_string(index=False)}"
        )

    # 24:00 automatically becomes 00:00 on the next day.
    timestamps = (
        dates
        + pd.to_timedelta(hours, unit="h")
        + pd.to_timedelta(minutes, unit="m")
    )

    return timestamps


# --------------------------------------------------
# Load and normalize one year
# --------------------------------------------------

def load_year(year):
    """Load one DEFRA annual CSV and extract PM2.5."""

    path = RAW_DIR / f"{SITE_CODE}_{year}.csv"

    if not path.exists():
        raise FileNotFoundError(
            f"Missing source CSV: {path}"
        )

    # The first few lines contain source metadata.
    lines = path.read_text(
        encoding="utf-8-sig",
        errors="replace",
    ).splitlines()

    header_index = find_header(lines)

    df = pd.read_csv(
        path,
        skiprows=header_index,
        encoding="utf-8-sig",
        low_memory=False,
    )

    df.columns = [
        str(column).strip()
        for column in df.columns
    ]

    pm25_column = find_pm25_column(df.columns)

    date_column, time_column = find_time_columns(
        df.columns
    )

    timestamps = parse_defra_timestamps(
        df[date_column],
        df[time_column],
    )

    # Each pollutant has its own status and unit columns.
    pm25_index = df.columns.get_loc(pm25_column)

    if pm25_index + 2 >= len(df.columns):
        raise ValueError(
            f"{year}: PM2.5 status/unit columns missing."
        )

    status_column = df.columns[pm25_index + 1]
    unit_column = df.columns[pm25_index + 2]

    if not str(status_column).lower().startswith("status"):
        raise ValueError(
            f"Unexpected status column: {status_column}"
        )

    if not str(unit_column).lower().startswith("unit"):
        raise ValueError(
            f"Unexpected unit column: {unit_column}"
        )

    # Convert numeric observations; preserve missing values.
    raw_values = df[pm25_column].astype("string").str.strip()

    pm25_values = pd.to_numeric(
        raw_values,
        errors="coerce",
    )

    # Do not silently treat unexpected text as missing data.
    missing_tokens = {"", "nan", "na", "n/a", "null", "none", "-"}
    unexpected_text = (
        pm25_values.isna()
        & raw_values.notna()
        & ~raw_values.str.lower().isin(missing_tokens)
    ).fillna(False)

    if unexpected_text.any():
        examples = raw_values[unexpected_text].unique()[:5]

        raise ValueError(
            f"{year}: unexpected PM2.5 values: {list(examples)}"
        )

    statuses = df[status_column].astype("string").str.strip()
    units = df[unit_column].astype("string").str.strip()

    # Check the unit for every non-missing measurement.
    measured_units = (
        units[pm25_values.notna()]
        .dropna()
        .unique()
        .tolist()
    )

    invalid_units = [
        unit
        for unit in measured_units
        if "ugm-3" not in unit.lower().replace(" ", "")
    ]

    if invalid_units:
        raise ValueError(
            f"{year}: unexpected PM2.5 units: {invalid_units}"
        )

    # Preserve the original date and time for auditing.
    result = pd.DataFrame({
        "timestamp_source": timestamps,
        "source_date": df[date_column].astype("string"),
        "source_time": df[time_column].astype("string"),
        "city": "London",
        "station_id": SITE_CODE,
        "station_name": SITE_NAME,
        "latitude": LATITUDE,
        "longitude": LONGITUDE,
        "pm25_ugm3": pm25_values,
        "measurement_status": statuses,
        "measurement_unit": units,
        "source": "DEFRA UK-AIR",
        "source_file": path.name,
    })

    result["is_missing"] = result["pm25_ugm3"].isna()

    print(f"\nYear: {year}")
    print(f"CSV header line: {header_index + 1}")
    print(f"PM2.5 column: {pm25_column}")
    print(f"Status column: {status_column}")
    print(f"Unit column: {unit_column}")
    print(f"Rows: {len(result)}")
    print(f"Missing readings: {result['is_missing'].sum()}")
    print(f"Measurement units: {measured_units}")

    return result


# --------------------------------------------------
# Combine and export
# --------------------------------------------------

def main():
    """Build the London PM2.5 observation dataset."""

    print("AirScope | DEFRA PM2.5 normalization")

    frames = [
        load_year(year)
        for year in YEARS
    ]

    result = pd.concat(
        frames,
        ignore_index=True,
    )

    result = result.sort_values(
        "timestamp_source"
    ).reset_index(drop=True)

    duplicates = result.duplicated(
        subset=["station_id", "timestamp_source"]
    )

    if duplicates.any():
        examples = result.loc[
            duplicates,
            ["station_id", "timestamp_source", "source_file"]
        ].head(5)

        raise ValueError(
            "Duplicate station timestamps detected:\n"
            f"{examples.to_string(index=False)}"
        )

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    result.to_parquet(
        OUTPUT_FILE,
        index=False,
    )

    print("\nAirScope | Normalization complete")
    print(f"Total rows: {len(result)}")
    print(f"Missing readings: {result['is_missing'].sum()}")
    print(
        "Date range: "
        f"{result['timestamp_source'].min()} to "
        f"{result['timestamp_source'].max()}"
    )
    print(f"Saved: {OUTPUT_FILE.relative_to(ROOT)}")
    print("Timezone: source clock time (UTC not yet verified)")


if __name__ == "__main__":
    main()
