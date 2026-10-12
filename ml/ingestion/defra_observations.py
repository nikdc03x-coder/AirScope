
"""
AirScope | nik
Test time-filtered DEFRA PM2.5 observation requests.

Try London station candidates and save the first response
containing real observation records.
"""

from datetime import datetime, timedelta, timezone
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


def local_name(tag):
    """Remove an XML namespace."""
    return tag.split("}")[-1]


def fetch_observations(client, station, start_time, end_time):
    """Request PM2.5 observations within a specific UTC period."""

    params = {
        "service": "SOS",
        "version": "2.0.0",
        "request": "GetObservation",
        "offering": station["offering_id"],
        "observedProperty": PM25_URI,
        "temporalFilter": (
            "om:phenomenonTime,"
            f"{start_time}/{end_time}"
        ),
    }

    response = client.get(SOS_URL, params=params)
    response.raise_for_status()

    root = ET.fromstring(response.content)

    if "ExceptionReport" in root.tag:
        message = " ".join(root.itertext()).strip()
        return response, root, 0, message

    # Count observation elements, not arbitrary XML elements.
    count = sum(
        1
        for element in root.iter()
        if local_name(element.tag) in (
            "OM_Observation",
            "OM_Measurement",
        )
    )

    return response, root, count, ""


def main():
    """Test London PM2.5 candidates with a bounded date range."""

    stations = pd.read_csv(STATIONS_PATH)

    end = datetime.now(timezone.utc)
    start = end - timedelta(days=7)

    start_time = start.strftime("%Y-%m-%dT%H:%M:%SZ")
    end_time = end.strftime("%Y-%m-%dT%H:%M:%SZ")

    RAW_DIR.mkdir(parents=True, exist_ok=True)

    print("AirScope | DEFRA London PM2.5 observation test")
    print(f"Period: {start_time} to {end_time}")
    print(f"Candidates: {len(stations)}")

    with httpx.Client(
        timeout=120.0,
        follow_redirects=True,
    ) as client:

        for _, station in stations.iterrows():
            name = station["station_name"]

            print(f"\nTesting: {name}")

            try:
                response, root, count, error = fetch_observations(
                    client,
                    station,
                    start_time,
                    end_time,
                )
            except (httpx.HTTPError, ET.ParseError) as exc:
                print(f"Request failed: {exc}")
                continue

            print(f"HTTP status: {response.status_code}")
            print(f"XML root: {local_name(root.tag)}")
            print(f"Observation records: {count}")
            print(f"Response size: {len(response.content):,} bytes")

            if error:
                print(f"Service exception: {error[:500]}")
                break

            if count > 0:
                output_path = (
                    RAW_DIR / "defra_london_test_observations.xml"
                )

                output_path.write_bytes(response.content)

                print("\nReal observations found.")
                print(f"Saved: {output_path.relative_to(ROOT)}")
                print("\nResponse preview:")
                print(response.text[:1500])
                break

        else:
            print(
                "\nNo observations returned for these "
                "candidates in the selected period."
            )


if __name__ == "__main__":
    main()
