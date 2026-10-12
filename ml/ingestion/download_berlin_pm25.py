
"""
AirScope | nik
Download official Berlin hourly PM2.5 observations.

- Use the 12 verified Berlin monitoring stations.
- Download data in monthly batches.
- Cache original UBA JSON responses.
- Preserve source timestamps and missing values.
- Convert documented CET JSON timestamps to UTC.
- Export one station-hour Parquet dataset.

No synthetic measurements or interpolation.
"""

import calendar
import json
import time
from datetime import date, timedelta
from pathlib import Path

import httpx
import pandas as pd

format="%Y-%m-%d %H:%M:%S"
ROOT = Path(__file__).resolve().parents[2]

STATIONS_FILE = (
    ROOT / "data" / "processed" / "berlin_pm25_stations.csv"
)

CACHE_DIR = ROOT / "data" / "raw" / "uba_monthly"

OUTPUT_FILE = (
    ROOT / "data" / "processed" / "berlin_pm25_hourly.parquet"
)

API_URL = (
    "https://luftdaten.umweltbundesamt.de"
    "/api/air-data/v3/measures/json"
)

PM25_COMPONENT = 9

START_DATE = date(2025, 1, 1)
END_DATE = date(2026, 10, 11)

# UBA JSON measurement timestamps use CET (UTC+01:00).
# CET is a fixed offset; do not apply Europe/Berlin DST.
CET_OFFSET = "+01:00"


def monthly_windows(start, end):
    """Yield non-overlapping calendar-month date windows."""

    current = start

    while current <= end:
        last_day = calendar.monthrange(
            current.year,
            current.month,
        )[1]

        month_end = min(
            date(current.year, current.month, last_day),
            end,
        )

        yield current, month_end

        current = month_end + timedelta(days=1)


def load_stations():
    """Load the stations verified to have PM2.5 readings."""

    if not STATIONS_FILE.exists():
        raise FileNotFoundError(
            f"Missing verified stations: {STATIONS_FILE}"
        )

    stations = pd.read_csv(
        STATIONS_FILE,
        dtype={"station_id": str, "station_code": str},
    )

    if stations.empty:
        raise ValueError("No verified Berlin stations found.")

    return stations


def download_month(client, station, start, end):
    """Download one station-month, reusing cached JSON."""

    code = station["station_code"]

    filename = (
        f"{code}_{start:%Y%m%d}_{end:%Y%m%d}.json"
    )

    path = CACHE_DIR / filename

    if path.exists():
        return json.loads(
            path.read_text(encoding="utf-8")
        )

    params = {
        "date_from": start.isoformat(),
        "date_to": end.isoformat(),
        "time_from": 1,
        "time_to": 24,
        "station": code,
        "component": PM25_COMPONENT,
        "lang": "en",
    }

    response = client.get(
        API_URL,
        params=params,
    )

    response.raise_for_status()

    payload = response.json()

    if not isinstance(payload.get("data"), dict):
        raise ValueError(
            f"Unexpected UBA response for {code}: "
            f"{start} to {end}"
        )

    CACHE_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    path.write_text(
        json.dumps(payload, ensure_ascii=False),
        encoding="utf-8",
    )

    time.sleep(0.15)

    return payload


def get_record_layout(payload):
    """
    Read the actual nested UBA v3 measurement schema.

    UBA structure:
    indices -> data -> station id -> date start -> fields
    """

    indices = payload.get("indices", {})

    try:
        fields = indices["data"]["station id"]["date start"]
    except (KeyError, TypeError):
        raise ValueError(
            f"Unexpected UBA measurement schema: {indices}"
        )

    if not isinstance(fields, list):
        raise ValueError(
            f"UBA measurement fields must be a list: {fields}"
        )

    normalized = [
        str(field).strip().lower()
        for field in fields
    ]

    required_fields = [
        "component id",
        "value",
        "date end",
    ]

    missing = [
        field
        for field in required_fields
        if field not in normalized
    ]

    if missing:
        raise ValueError(
            f"Missing required UBA fields: {missing}"
        )

    component_index = normalized.index("component id")
    value_index = normalized.index("value")
    end_index = normalized.index("date end")

    return component_index, value_index, end_index
def parse_month(payload, station, cache_name):
    """Extract genuine PM2.5 records from one UBA response."""

    data = payload.get("data", {})

    # UBA has used compact index formats. Stop rather than
    # silently interpret an unfamiliar schema incorrectly.
    try:
        component_idx, value_idx, end_idx = (
            get_record_layout(payload)
        )
    except ValueError:
        # Some v3 responses supply indices as nested arrays.
        # Show the schema so it can be corrected safely.
        print("\nUnexpected measurement schema:")
        print(json.dumps(
            payload.get("indices"),
            indent=2,
            ensure_ascii=False,
        ))
        raise

    records = []

    for station_key, observations in data.items():

        if str(station_key) != str(station["station_id"]):
            raise ValueError(
                "UBA station ID mismatch: "
                f"expected {station['station_id']}, "
                f"received {station_key}"
            )

        if not isinstance(observations, dict):
            raise ValueError(
                "Unexpected station observation structure."
            )

        for source_start, measurement in observations.items():

            if not isinstance(measurement, list):
                raise ValueError(
                    "Unexpected measurement record type."
                )

            if int(measurement[component_idx]) != PM25_COMPONENT:
                raise ValueError(
                    "Non-PM2.5 measurement returned."
                )

            source_end = measurement[end_idx]
            raw_value = measurement[value_idx]

            records.append({
                "timestamp_start_source": source_start,
                "timestamp_end_source": source_end,
                "pm25_ugm3": raw_value,
                "source_file": cache_name,
            })

    return records

def parse_uba_timestamp(values):
    """
    Parse UBA hourly timestamps.

    UBA sometimes represents midnight as 24:00:00.
    Convert it to 00:00:00 on the following day.
    Preserve the original strings elsewhere in the dataset.
    """

    def fix_midnight(value):
        value = str(value).strip()

        if " 24:00:00" in value:
            date_part = value.split(" ")[0]

            next_day = (
                pd.Timestamp(date_part)
                + pd.Timedelta(days=1)
            )

            return next_day.strftime("%Y-%m-%d 00:00:00")

        if " 24:00" in value:
            date_part = value.split(" ")[0]

            next_day = (
                pd.Timestamp(date_part)
                + pd.Timedelta(days=1)
            )

            return next_day.strftime("%Y-%m-%d 00:00:00")

        return value

    corrected = values.map(fix_midnight)

    return pd.to_datetime(
        corrected,
        format="mixed",
        errors="raise",
    )
def normalize_records(records, station):
    """Convert source records into the AirScope schema."""

    if not records:
        return pd.DataFrame()

    df = pd.DataFrame(records)

    # UBA JSON uses fixed CET timestamps.
    # Attach UTC+01:00, then convert to UTC.
    source_end = parse_uba_timestamp(
    df["timestamp_end_source"]
)

    df["timestamp_utc"] = (
        source_end
        .dt.tz_localize(CET_OFFSET)
        .dt.tz_convert("UTC")
    )

    # Preserve nulls. Never fill or interpolate them.
    df["pm25_ugm3"] = pd.to_numeric(
        df["pm25_ugm3"],
        errors="coerce",
    )

    df["city"] = "Berlin"
    df["station_id"] = str(station["station_code"])
    df["station_name"] = station["station_name"]

    df["latitude"] = float(station["latitude"])
    df["longitude"] = float(station["longitude"])

    df["source"] = "Umweltbundesamt (UBA)"
    df["time_convention"] = "CET_hour_ending"
    df["is_missing"] = df["pm25_ugm3"].isna()

    return df


def main():
    print("AirScope | Berlin PM2.5 historical ingestion")

    stations = load_stations()
    windows = list(monthly_windows(START_DATE, END_DATE))

    print(f"Verified stations: {len(stations)}")
    print(f"Monthly windows: {len(windows)}")

    all_frames = []

    with httpx.Client(
        timeout=90,
        follow_redirects=True,
    ) as client:

        for _, station in stations.iterrows():

            print(f"\nStation: {station['station_name']}")

            station_frames = []

            for start, end in windows:

                cache_name = (
                    f"{station['station_code']}_"
                    f"{start:%Y%m%d}_{end:%Y%m%d}.json"
                )

                payload = download_month(
                    client,
                    station,
                    start,
                    end,
                )

                records = parse_month(
                    payload,
                    station,
                    cache_name,
                )

                frame = normalize_records(
                    records,
                    station,
                )

                if not frame.empty:
                    station_frames.append(frame)

                print(
                    f"  {start:%Y-%m}: {len(frame)} records"
                )

            if station_frames:
                combined = pd.concat(
                    station_frames,
                    ignore_index=True,
                )

                all_frames.append(combined)

    if not all_frames:
        raise RuntimeError(
            "No Berlin PM2.5 measurements downloaded."
        )

    result = pd.concat(
        all_frames,
        ignore_index=True,
    )

    result = result.sort_values(
        ["station_id", "timestamp_utc"]
    ).reset_index(drop=True)

    duplicates = result.duplicated(
        subset=["station_id", "timestamp_utc"]
    )

    if duplicates.any():
        raise ValueError(
            f"Duplicate station-hour records: "
            f"{duplicates.sum()}"
        )

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    result.to_parquet(
        OUTPUT_FILE,
        index=False,
    )

    print("\nAirScope | Berlin ingestion complete")
    print(f"Rows: {len(result)}")
    print(f"Stations: {result['station_id'].nunique()}")
    print(f"Missing readings: {result['is_missing'].sum()}")
    print(
        "UTC range: "
        f"{result['timestamp_utc'].min()} to "
        f"{result['timestamp_utc'].max()}"
    )
    print(f"Saved: {OUTPUT_FILE.relative_to(ROOT)}")


if __name__ == "__main__":
    main()



