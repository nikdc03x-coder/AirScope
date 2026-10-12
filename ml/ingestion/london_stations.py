
"""
AirScope | nik
Inspect DEFRA PM2.5 offerings for London station metadata.

Uses the official SOS capabilities XML already downloaded.
Does not invent station names or coordinates.
"""

import json
from pathlib import Path
from xml.etree import ElementTree as ET


ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = ROOT / "data" / "raw"

INPUT_PATH = RAW_DIR / "defra_capabilities.xml"
OUTPUT_PATH = RAW_DIR / "defra_london_candidates.json"

PM25_URI = (
    "http://dd.eionet.europa.eu/"
    "vocabulary/aq/pollutant/6001"
)


def local_name(tag):
    """Remove an XML namespace from a tag."""
    return tag.split("}")[-1]


def get_text(element, name):
    """Return text from the first matching child."""
    for child in element.iter():
        if local_name(child.tag) == name:
            return (child.text or "").strip()

    return ""


def main():
    if not INPUT_PATH.exists():
        raise FileNotFoundError(
            "DEFRA capabilities XML is missing."
        )

    print("AirScope | Finding London PM2.5 stations")

    tree = ET.parse(INPUT_PATH)
    root = tree.getroot()

    candidates = []
    total_pm25 = 0

    for element in root.iter():
        if local_name(element.tag) != "ObservationOffering":
            continue

        pollutant = get_text(
            element,
            "observableProperty",
        )

        if pollutant != PM25_URI:
            continue

        total_pm25 += 1

        # Preserve the complete metadata for inspection.
        metadata = " ".join(
            text.strip()
            for text in element.itertext()
            if text and text.strip()
        )

        # Search for London references in the metadata.
        if "london" not in metadata.lower():
            continue

        candidates.append({
            "offering_id": get_text(element, "identifier"),
            "name": get_text(element, "name"),
            "procedure": get_text(element, "procedure"),
            "metadata_preview": metadata[:500],
        })

    OUTPUT_PATH.write_text(
        json.dumps(candidates, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    print(f"Total PM2.5 offerings: {total_pm25}")
    print(f"London candidates: {len(candidates)}")

    for station in candidates[:10]:
        print("\nOffering:", station["offering_id"])
        print("Name:", station["name"])
        print("Metadata:", station["metadata_preview"][:200])

    print(f"\nSaved: {OUTPUT_PATH.relative_to(ROOT)}")

    if not candidates:
        print(
            "\nNo London references found in offering metadata. "
            "We will need station coordinates or a station registry "
            "to identify London locations."
        )


if __name__ == "__main__":
    main()
