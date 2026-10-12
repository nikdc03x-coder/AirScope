
"""
AirScope | nik
Build a station-reference registry from DEFRA SOS metadata.

The registry preserves official references without guessing
station names or coordinates.
"""

import json
from pathlib import Path
from xml.etree import ElementTree as ET

import pandas as pd


# AirScope | nik
# Define project paths and the official PM2.5 pollutant identifier.
ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = ROOT / "data" / "raw"
PROCESSED_DIR = ROOT / "data" / "processed"

XML_PATH = RAW_DIR / "defra_capabilities.xml"
OUTPUT_PATH = PROCESSED_DIR / "defra_pm25_registry.csv"

PM25_URI = (
    "http://dd.eionet.europa.eu/"
    "vocabulary/aq/pollutant/6001"
)


def local_name(tag):
    """Remove the namespace from an XML tag."""
    return tag.split("}")[-1]


def extract_values(element, name):
    """Read text and reference attributes from matching elements."""
    values = []

    for child in element.iter():
        if local_name(child.tag) != name:
            continue

        if child.text and child.text.strip():
            values.append(child.text.strip())

        for key, value in child.attrib.items():
            if local_name(key) in ("href", "title") and value:
                values.append(value)

    return list(dict.fromkeys(values))


def main():
    """Build a registry containing official DEFRA PM2.5 offerings."""

    if not XML_PATH.exists():
        raise FileNotFoundError(
            "DEFRA metadata is missing. Run run_ingestion.py first."
        )

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    tree = ET.parse(XML_PATH)
    root = tree.getroot()

    records = []

    # Examine each official observation offering.
    for element in root.iter():
        if local_name(element.tag) != "ObservationOffering":
            continue

        properties = extract_values(
            element,
            "observableProperty",
        )

        # Only accept the exact official PM2.5 pollutant URI.
        if PM25_URI not in properties:
            continue

        identifiers = extract_values(element, "identifier")
        procedures = extract_values(element, "procedure")

        # Preserve geographic references if they are available.
        features = extract_values(element, "relatedFeature")
        features += extract_values(element, "featureOfInterest")

        records.append({
            "offering_id": identifiers[0] if identifiers else "",
            "procedure_id": procedures[0] if procedures else "",
            "feature_references": json.dumps(
                list(dict.fromkeys(features))
            ),
            "pollutant": "PM2.5",
            "unit": "µg/m³",
            "source": "DEFRA UK-AIR SOS",
        })

    # Convert the extracted records into a structured dataset.
    df = pd.DataFrame(records)

    if df.empty:
        raise RuntimeError("No DEFRA PM2.5 offerings found.")

    # Each observation offering should appear only once.
    df = df.drop_duplicates(subset=["offering_id"])

    df.to_csv(
        OUTPUT_PATH,
        index=False,
        encoding="utf-8",
    )

    print("AirScope | DEFRA PM2.5 station registry")
    print(f"Offerings: {len(df)}")

    referenced = df[
        df["feature_references"] != "[]"
    ]

    print(
        "Offerings with feature references: "
        f"{len(referenced)}"
    )

    print("\nFirst five records:")
    print(df.head().to_string(index=False))

    print(f"\nSaved: {OUTPUT_PATH.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
