
"""
AirScope | nik
Discover official DEFRA PM2.5 observation offerings.

DEFRA identifies PM2.5 using EEA pollutant code 6001.
"""

import json
from pathlib import Path
from xml.etree import ElementTree as ET


ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = ROOT / "data" / "raw"

PM25_URI = (
    "http://dd.eionet.europa.eu/"
    "vocabulary/aq/pollutant/6001"
)


def local_name(tag):
    """Remove an XML namespace."""
    return tag.split("}")[-1]


def child_text(element, name):
    """Find the text of a matching child element."""
    for child in element.iter():
        if local_name(child.tag) == name:
            return (child.text or "").strip()

    return ""


def discover_pm25_offerings():
    """Extract offerings measuring PM2.5."""

    xml_path = RAW_DIR / "defra_capabilities.xml"

    if not xml_path.exists():
        raise FileNotFoundError(
            "DEFRA capabilities XML is missing."
        )

    tree = ET.parse(xml_path)
    root = tree.getroot()

    offerings = []

    for element in root.iter():
        if local_name(element.tag) != "ObservationOffering":
            continue

        pollutant = child_text(
            element,
            "observableProperty",
        )

        if pollutant != PM25_URI:
            continue

        offerings.append({
            "offering_id": child_text(
                element,
                "identifier",
            ),
            "name": child_text(element, "name"),
            "procedure": child_text(
                element,
                "procedure",
            ),
            "pollutant": "PM2.5",
            "pollutant_uri": pollutant,
        })

    output_path = RAW_DIR / "defra_pm25_offerings.json"

    output_path.write_text(
        json.dumps(
            offerings,
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    return offerings


if __name__ == "__main__":
    results = discover_pm25_offerings()

    print(f"PM2.5 offerings found: {len(results)}")

    for offering in results[:5]:
        print(offering["offering_id"])
