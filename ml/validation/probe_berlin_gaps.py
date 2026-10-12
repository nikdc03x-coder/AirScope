
"""
AirScope | nik
Check whether UBA can recover missing Berlin PM2.5 hours.

Query the three known missing periods directly.
Save the original API responses without changing
the existing Berlin Parquet dataset.
"""

import json
from datetime import date
from pathlib import Path

import httpx


ROOT = Path(__file__).resolve().parents[2]

OUTPUT_DIR = ROOT / "data/raw/uba_gap_recovery"

STATION_CODE = "DEBE010"
STATION_ID = "121"
PM25_COMPONENT = 9

API_URL = (
    "https://luftdaten.umweltbundesamt.de"
    "/api/air-data/v3/measures/json"
)

PERIODS = [
    ("2026-08-15", "2026-08-23"),
    ("2026-09-11", "2026-09-13"),
    ("2026-09-19", "2026-09-19"),
]


def fetch_period(client, start, end):
    """Request genuine PM2.5 observations for one gap."""

    params = {
        "date_from": start,
        "date_to": end,
        "time_from": 1,
        "time_to": 24,
        "station": STATION_CODE,
        "component": PM25_COMPONENT,
        "lang": "en",
    }

    response = client.get(API_URL, params=params)
    response.raise_for_status()

    payload = response.json()

    if not isinstance(payload.get("data"), dict):
        raise ValueError(
            f"Unexpected API response for {start} to {end}"
        )

    filename = (
        f"{STATION_CODE}_{start.replace('-', '')}"
        f"_{end.replace('-', '')}.json"
    )

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    path = OUTPUT_DIR / filename

    path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    observations = payload["data"].get(STATION_ID, {})

    if not isinstance(observations, dict):
        raise ValueError(
            f"Unexpected station data for {STATION_CODE}"
        )

    return path, observations


def main():
    print("AirScope | Berlin targeted gap recovery")

    total_records = 0

    with httpx.Client(
        timeout=90,
        follow_redirects=True,
    ) as client:

        for start, end in PERIODS:

            print(f"\nChecking: {start} to {end}")

            path, observations = fetch_period(
                client,
                start,
                end,
            )

            count = len(observations)
            total_records += count

            print(f"Returned observations: {count}")

            if observations:
                timestamps = sorted(observations)

                print(f"First source hour: {timestamps[0]}")
                print(f"Last source hour: {timestamps[-1]}")

            print(f"Saved: {path.relative_to(ROOT)}")

    print("\nRecovery probe complete")
    print(f"Total returned observations: {total_records}")

    if total_records == 0:
        print(
            "UBA returned no observations for these "
            "periods in this targeted probe."
        )
    else:
        print(
            "UBA returned observations. Compare them "
            "against the existing dataset before merging."
        )


if __name__ == "__main__":
    main()
