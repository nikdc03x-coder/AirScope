
"""
AirScope | nik
Discover official German air-quality monitoring stations.

Fetch UBA station metadata, inspect its structure,
and identify candidate Berlin monitoring stations.

No measurements are fabricated or modified.
"""

import json
from pathlib import Path

import httpx


ROOT = Path(__file__).resolve().parents[2]

RAW_DIR = ROOT / "data" / "raw"
PROCESSED_DIR = ROOT / "data" / "processed"

BASE_URL = "https://www.umweltbundesamt.de/api/air_data/v3"

RAW_FILE = RAW_DIR / "uba_stations_2025_2026.json"
REPORT_FILE = PROCESSED_DIR / "uba_station_discovery.json"


def fetch_station_metadata():
    """Request official UBA station metadata."""

    url = f"{BASE_URL}/stations/json"

    params = {
        "use": "measure",
        "date_from": "2025-01-01",
        "date_to": "2026-10-12",
        "time_from": 1,
        "time_to": 24,
        "lang": "en",
    }

    with httpx.Client(
        timeout=90,
        follow_redirects=True,
    ) as client:
        response = client.get(url, params=params)
        response.raise_for_status()

    payload = response.json()

    if not isinstance(payload, dict):
        raise ValueError(
            "Unexpected UBA station response format."
        )

    RAW_DIR.mkdir(parents=True, exist_ok=True)

    RAW_FILE.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    print(f"HTTP status: {response.status_code}")
    print(f"Source: {response.url}")
    print(f"Saved: {RAW_FILE.relative_to(ROOT)}")

    return payload


def inspect_stations(payload):
    """Inspect station metadata without assuming field positions."""

    print("\nTop-level response keys:")
    print(list(payload.keys()))

    stations = payload.get("data")

    if not isinstance(stations, dict):
        raise ValueError(
            "Expected UBA station data to be a dictionary."
        )

    print(f"\nTotal station entries: {len(stations)}")

    # The API can return compact array-based records.
    # Preserve its index metadata so fields can be mapped
    # correctly in the next ingestion step.
    indices = payload.get("indices", {})

    print("\nIndex definitions:")
    print(json.dumps(indices, indent=2, ensure_ascii=False))

    print("\nFirst three station records:")

    for station_id, record in list(stations.items())[:3]:
        print(f"\nStation key: {station_id}")
        print(json.dumps(record, ensure_ascii=False)[:1200])

    # Search only textual station metadata for Berlin.
    # This is discovery, not yet a validated PM2.5 registry.
    berlin_candidates = []

    for station_id, record in stations.items():
        record_text = json.dumps(
            record,
            ensure_ascii=False,
        ).lower()

        if "berlin" in record_text:
            berlin_candidates.append({
                "station_key": station_id,
                "record": record,
            })

    report = {
        "source": "UBA Air Data API v3",
        "total_stations": len(stations),
        "indices": indices,
        "berlin_text_matches": berlin_candidates,
    }

    PROCESSED_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    REPORT_FILE.write_text(
        json.dumps(report, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    print(
        "\nBerlin text-match candidates: "
        f"{len(berlin_candidates)}"
    )

    print("\nFirst five Berlin candidates:")

    for candidate in berlin_candidates[:5]:
        print(json.dumps(candidate, ensure_ascii=False)[:700])

    print(f"\nSaved: {REPORT_FILE.relative_to(ROOT)}")


def main():
    print("AirScope | UBA Berlin station discovery")

    payload = fetch_station_metadata()
    inspect_stations(payload)


if __name__ == "__main__":
    main()
