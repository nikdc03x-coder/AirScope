
"""
AirScope | nik
Verify which official UBA Berlin stations measure PM2.5.

Uses the existing UBA station registry and tests
real hourly measurements from the UBA v3 API.
"""

import json
import time
from pathlib import Path

import httpx
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]

STATIONS_FILE = (
    ROOT / "data" / "raw" / "uba_stations_2025_2026.json"
)

OUTPUT_FILE = (
    ROOT / "data" / "processed" / "berlin_pm25_stations.csv"
)

REPORT_FILE = (
    ROOT / "data" / "processed" / "berlin_pm25_probe.json"
)

API_URL = (
    "https://luftdaten.umweltbundesamt.de"
    "/api/air-data/v3/measures/json"
)

PM25_COMPONENT = 9

# Test two periods to reduce the chance that a temporary
# station outage causes us to miss a PM2.5 station.
TEST_PERIODS = [
    ("2025-06-01", "2025-06-03"),
    ("2026-09-01", "2026-09-03"),
]


def load_berlin_stations():
    """Read official station metadata saved previously."""

    if not STATIONS_FILE.exists():
        raise FileNotFoundError(
            f"Run uba_stations.py first: {STATIONS_FILE}"
        )

    payload = json.loads(
        STATIONS_FILE.read_text(encoding="utf-8")
    )

    indices = payload["indices"]
    records = payload["data"]

    stations = []

    for station_key, values in records.items():
        station = dict(zip(indices, values))

        # Use the official station city/network fields.
        if (
            station.get("station city") != "Berlin"
            or station.get("network code") != "BE"
        ):
            continue

        stations.append({
            "station_id": str(station_key),
            "station_code": station["station code"],
            "station_name": station["station name"],
            "latitude": float(station["station latitude"]),
            "longitude": float(station["station longitude"]),
            "station_type": station.get("station type name"),
            "station_setting": station.get(
                "station setting name"
            ),
        })

    return stations


def count_measurements(payload):
    """
    Count actual measurement records.

    UBA measure responses group observations by station
    and then by measurement start time.
    """

    data = payload.get("data", {})

    if not isinstance(data, dict):
        raise ValueError(
            "Unexpected UBA measurement response structure."
        )

    count = 0

    for station_data in data.values():
        if isinstance(station_data, dict):
            for observation in station_data.values():
                if isinstance(observation, list):
                    count += 1

    return count


def probe_station(client, station):
    """Test a station against two historical date windows."""

    tests = []

    for start_date, end_date in TEST_PERIODS:

        params = {
            "date_from": start_date,
            "date_to": end_date,
            "time_from": 1,
            "time_to": 24,
            "station": station["station_code"],
            "component": PM25_COMPONENT,
            "lang": "en",
        }

        response = client.get(
            API_URL,
            params=params,
        )

        response.raise_for_status()

        payload = response.json()

        measurement_count = count_measurements(payload)

        tests.append({
            "date_from": start_date,
            "date_to": end_date,
            "measurement_records": measurement_count,
            "response_indices": payload.get("indices"),
        })

        # One successful period confirms PM2.5 availability.
        if measurement_count > 0:
            break

        time.sleep(0.2)

    return tests


def main():
    print("AirScope | Berlin PM2.5 station verification")

    stations = load_berlin_stations()

    print(f"Berlin candidates: {len(stations)}")

    verified = []
    probe_results = []

    with httpx.Client(
        timeout=60,
        follow_redirects=True,
    ) as client:

        for index, station in enumerate(stations, start=1):

            print(
                f"\n[{index}/{len(stations)}] "
                f"{station['station_name']}"
            )

            try:
                tests = probe_station(client, station)

                found = any(
                    test["measurement_records"] > 0
                    for test in tests
                )

                probe_results.append({
                    "station_code": station["station_code"],
                    "station_name": station["station_name"],
                    "pm25_verified": found,
                    "tests": tests,
                })

                if found:
                    verified.append(station)
                    print("PM2.5 observations found")
                else:
                    print("No observations in tested periods")

            except (httpx.HTTPError, ValueError) as error:
                probe_results.append({
                    "station_code": station["station_code"],
                    "station_name": station["station_name"],
                    "pm25_verified": False,
                    "error": str(error),
                })

                print(f"Probe failed: {error}")

            time.sleep(0.2)

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    columns = [
        "station_id",
        "station_code",
        "station_name",
        "latitude",
        "longitude",
        "station_type",
        "station_setting",
    ]

    pd.DataFrame(
        verified,
        columns=columns,
    ).to_csv(
        OUTPUT_FILE,
        index=False,
    )

    REPORT_FILE.write_text(
        json.dumps(
            probe_results,
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    print("\nAirScope | Verification complete")
    print(f"Berlin candidates: {len(stations)}")
    print(f"PM2.5-verified stations: {len(verified)}")
    print(f"Saved: {OUTPUT_FILE.relative_to(ROOT)}")
    print(f"Report: {REPORT_FILE.relative_to(ROOT)}")

    if not verified:
        raise RuntimeError(
            "No Berlin PM2.5 stations were verified. "
            "Inspect the probe report before continuing."
        )


if __name__ == "__main__":
    main()
