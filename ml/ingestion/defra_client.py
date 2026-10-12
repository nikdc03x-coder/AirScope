
"""
AirScope | nik
DEFRA SOS station metadata client.

Request station features using the standard SOS
GetFeatureOfInterest operation without unsupported filters.
"""

from pathlib import Path
from xml.etree import ElementTree as ET

import httpx


ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = ROOT / "data" / "raw"

SOS_URL = "https://uk-air.defra.gov.uk/sos-ukair/service"


def request_station_features():
    """Request available station features from DEFRA."""

    params = {
        "service": "SOS",
        "version": "2.0.0",
        "request": "GetFeatureOfInterest",
    }

    print("AirScope | Requesting DEFRA station features")

    with httpx.Client(
        timeout=90.0,
        follow_redirects=True,
    ) as client:
        response = client.get(SOS_URL, params=params)
        response.raise_for_status()

    RAW_DIR.mkdir(parents=True, exist_ok=True)

    output_path = RAW_DIR / "defra_station_features.xml"
    output_path.write_bytes(response.content)

    print(f"HTTP status: {response.status_code}")
    print(f"Response size: {len(response.content):,} bytes")
    print(f"Saved: {output_path.relative_to(ROOT)}")

    root = ET.fromstring(response.content)

    print(f"XML root: {root.tag}")

    if "ExceptionReport" in root.tag:
        print("\nDEFRA service exception:")
        print(" ".join(root.itertext())[:1000])
        return

    # Count geographic features returned by the service.
    features = [
        element
        for element in root.iter()
        if element.tag.split("}")[-1]
        in ("featureMember", "featureMembers", "SF_SpatialSamplingFeature")
    ]

    print(f"Feature-related XML elements: {len(features)}")

    print("\nResponse preview:")
    print(response.text[:1200])


if __name__ == "__main__":
    request_station_features()
