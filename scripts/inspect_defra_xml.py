
"""
AirScope | nik
Inspect the real structure of DEFRA's SOS capabilities XML.

This script reads the existing downloaded file.
It does not make another network request.
"""

from collections import Counter
from pathlib import Path
from xml.etree import ElementTree as ET


ROOT = Path(__file__).resolve().parents[1]
XML_PATH = ROOT / "data" / "raw" / "defra_capabilities.xml"


def local_name(tag):
    """Remove the XML namespace from an element name."""
    return tag.split("}")[-1]


def main():
    if not XML_PATH.exists():
        raise FileNotFoundError(
            "DEFRA metadata not found. Run run_ingestion.py first."
        )

    print("AirScope | DEFRA XML structure inspection")

    tag_counts = Counter()
    pm25_matches = []
    offering_samples = []

    # Stream the XML to avoid holding the entire file in memory.
    for _, element in ET.iterparse(XML_PATH, events=("end",)):
        name = local_name(element.tag)
        tag_counts[name] += 1

        # Inspect attributes and text for pollutant references.
        content = " ".join(
            [element.text or ""]
            + list(element.attrib.values())
        ).strip()

        normalized = content.lower()

        if any(
            term in normalized
            for term in ("pm2.5", "pm2_5", "pm25", "particulate")
        ):
            if len(pm25_matches) < 15:
                pm25_matches.append((name, content[:250]))

        # Identify how the service represents its offerings.
        if "offering" in name.lower():
            if len(offering_samples) < 10:
                offering_samples.append(
                    (name, content[:200])
                )

        element.clear()

    print("\n=== MOST COMMON XML ELEMENTS ===")
    for name, count in tag_counts.most_common(20):
        print(f"{name}: {count}")

    print("\n=== ELEMENTS CONTAINING 'OFFERING' ===")
    for name, content in offering_samples:
        print(f"{name}: {content}")

    print("\n=== PM2.5 / PARTICULATE REFERENCES ===")
    for name, content in pm25_matches:
        print(f"{name}: {content}")

    print(f"\nPM2.5 reference samples found: {len(pm25_matches)}")

    if not pm25_matches:
        print(
            "No direct PM2.5 text matches found. "
            "The service may use pollutant identifiers or URIs."
        )


if __name__ == "__main__":
    main()
