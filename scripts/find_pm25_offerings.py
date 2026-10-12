
"""
AirScope | nik
Find PM2.5 observation offerings in DEFRA's SOS metadata.

We inspect complete offering elements before discarding them,
so child information is not lost during XML parsing.
"""

import json
from pathlib import Path
from xml.etree import ElementTree as ET


ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "raw"

XML_PATH = RAW_DIR / "defra_capabilities.xml"
OUTPUT_PATH = RAW_DIR / "defra_pm25_offerings.json"


def local_name(tag):
    """Return an XML element name without its namespace."""
    return tag.split("}")[-1]


def find_values(element, target_name):
    """Collect nonempty text from matching XML elements."""
    values = []

    for child in element.iter():
        if local_name(child.tag) == target_name:
            value = (child.text or "").strip()

            if value:
                values.append(value)

    return list(dict.fromkeys(values))


def main():
    if not XML_PATH.exists():
        raise FileNotFoundError(
            "Missing DEFRA metadata. Run run_ingestion.py first."
        )

    print("AirScope | Finding official DEFRA PM2.5 offerings")

    tree = ET.parse(XML_PATH)
    root = tree.getroot()

    matches = []
    total_offerings = 0

    for element in root.iter():
        if local_name(element.tag) != "ObservationOffering":
            continue

        total_offerings += 1

        identifiers = find_values(element, "identifier")
        names = find_values(element, "name")
        properties = find_values(element, "observableProperty")
        procedures = find_values(element, "procedure")

        # Search both readable labels and pollutant URIs.
        searchable = " ".join(
            identifiers + names + properties
        ).lower()

        is_pm25 = any(
            term in searchable
            for term in (
                "pm2.5",
                "pm2_5",
                "pm25",
                "particulate matter 2.5",
            )
        )

        if not is_pm25:
            continue

        matches.append({
            "identifiers": identifiers,
            "names": names,
            "observable_properties": properties,
            "procedures": procedures,
        })

    # Save discovered identifiers for our future collector.
    OUTPUT_PATH.write_text(
        json.dumps(matches, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    print(f"\nTotal offerings: {total_offerings}")
    print(f"PM2.5 offerings: {len(matches)}")

    print("\n=== FIRST FIVE PM2.5 OFFERINGS ===")

    for index, offering in enumerate(matches[:5], start=1):
        print(f"\nOffering {index}")

        for key, values in offering.items():
            print(f"{key}: {values[:3]}")

    print(f"\nSaved: {OUTPUT_PATH.relative_to(ROOT)}")

    if not matches:
        print(
            "\nNo PM2.5 offerings matched the known labels. "
            "We may need to inspect DEFRA's pollutant URI conventions."
        )


if __name__ == "__main__":
    main()
