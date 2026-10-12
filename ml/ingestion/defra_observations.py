
"""
AirScope | nik
Retrieve real PM2.5 observations from DEFRA UK-AIR SOS.

The first request tests a known London observation offering.
"""

from pathlib import Path
from xml.etree import ElementTree as ET

import httpx
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]

STATIONS_PATH = ROOT / "data/processed/london_pm25_stations.csv"
RAW_DIR = ROOT / "data/raw"

SOS_URL = "https://uk-air.defra.gov.uk/sos-ukair/service"

PM25_URI = (
    "http://dd.eionet.europa.eu/"
    "vocabulary/aq/pollutant/6001"
)


def fetch_observations(offering_id):
    """Request observations for a real DEFRA PM2.5 offering."""

    params = {
        "service": "SOS",
        "version": "2.0.0",
        "request": "GetObservation",
        "offering": offering_id,
        "observedProperty": PM25_URI,
    }

    print("AirScope | Requesting DEFRA PM2.5 observations")
    print(f"Offering: {offering_id}")

    with httpx.Client(
        timeout=120.0,
        follow_redirects=True,
    ) as client:
        response = client.get(SOS_URL, params=params)
        response.raise_for_status()

    RAW_DIR.mkdir(parents=True, exist_ok=True)

    output_path = RAW_DIR / "defra_london_test_observations.xml"
    output_path.write_bytes(response.content)

    print(f"HTTP status: {response.status_code}")
    print(f"Response size: {len(response.content):,} bytes")

    root = ET.fromstring(response.content)

    print(f"XML root: {root.tag}")

    if "ExceptionReport" in root.tag:
        print("\nDEFRA service exception:")
        print(" ".join(root.itertext())[:1500])
        return

    print("\nResponse preview:")
    print(response.text[:1800])

    print(f"\nSaved: {output_path.relative_to(ROOT)}")


def main():
    stations = pd.read_csv(STATIONS_PATH)

    # Start with one verified geographic candidate.
    station = stations.iloc[0]

    print(f"Station candidate: {station['station_name']}")

    fetch_observations(station["offering_id"])


if __name__ == "__main__":
    main()
