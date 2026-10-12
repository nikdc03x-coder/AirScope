
"""
AirScope | nik
Extract real station-feature locations from DEFRA SOS metadata.

Coordinates and identifiers come directly from the official XML.
No station names or geographic positions are invented.
"""

from pathlib import Path
from xml.etree import ElementTree as ET

import pandas as pd


ROOT = Path(__file__).resolve().parents[2]

INPUT_PATH = ROOT / "data/raw/defra_station_features.xml"
OUTPUT_PATH = ROOT / "data/processed/defra_station_locations.csv"

NS = {
    "sos": "http://www.opengis.net/sos/2.0",
    "sams": "http://www.opengis.net/samplingSpatial/2.0",
    "sf": "http://www.opengis.net/sampling/2.0",
    "gml": "http://www.opengis.net/gml/3.2",
    "xlink": "http://www.w3.org/1999/xlink",
}


def get_text(element, path):
    """Read optional XML text safely."""
    node = element.find(path, NS)

    if node is not None and node.text:
        return node.text.strip()

    return ""


def extract_location(feature):
    """Extract coordinates and their declared reference system."""

    position = feature.find(".//gml:pos", NS)

    if position is None or not position.text:
        return None, None, ""

    values = position.text.strip().split()

    if len(values) < 2:
        return None, None, ""

    try:
        first = float(values[0])
        second = float(values[1])
    except ValueError:
        return None, None, ""

    srs_name = position.get("srsName", "")

    # A coordinate reference system may be declared on a parent.
    if not srs_name:
        for node in feature.iter():
            if node.tag.endswith("Point"):
                srs_name = node.get("srsName", "")
                if srs_name:
                    break

    return first, second, srs_name


def main():
    """Parse the downloaded DEFRA station-feature XML."""

    if not INPUT_PATH.exists():
        raise FileNotFoundError(
            "Missing DEFRA features XML. Run defra_client.py first."
        )

    tree = ET.parse(INPUT_PATH)
    root = tree.getroot()

    records = []

    features = root.findall(
        ".//sams:SF_SpatialSamplingFeature",
        NS,
    )

    for feature in features:
        identifier = get_text(feature, "gml:identifier")
        name = get_text(feature, "gml:name")
        description = get_text(feature, "gml:description")

        first, second, srs_name = extract_location(feature)

        records.append({
            "feature_id": identifier,
            "station_name": name,
            "description": description,
            "coordinate_1": first,
            "coordinate_2": second,
            "srs_name": srs_name,
            "source": "DEFRA UK-AIR SOS",
        })

    df = pd.DataFrame(records)

    if df.empty:
        raise RuntimeError("No spatial sampling features found.")

    df = df.drop_duplicates(subset=["feature_id"])

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUTPUT_PATH, index=False, encoding="utf-8")

    print("AirScope | DEFRA station locations")
    print(f"Total features: {len(df)}")

    valid = df[
        df["coordinate_1"].notna()
        & df["coordinate_2"].notna()
    ]

    print(f"Features with coordinates: {len(valid)}")

    print("\nCoordinate reference systems:")
    print(df["srs_name"].value_counts(dropna=False).head(10))

    london = df[
        df["station_name"].str.contains(
            "London",
            case=False,
            na=False,
        )
        | df["description"].str.contains(
            "London",
            case=False,
            na=False,
        )
    ]

    print(f"\nFeatures mentioning London: {len(london)}")
    print(london.head(10).to_string(index=False))

    print(f"\nSaved: {OUTPUT_PATH.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
