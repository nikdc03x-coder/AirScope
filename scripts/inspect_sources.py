
"""
AirScope | nik
Inspect official air-quality source metadata.

Uses locally saved API responses.
Does not download or invent measurements.
"""

import json
from pathlib import Path
from xml.etree import ElementTree as ET


ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"


def inspect_uba():
    """Identify the official UBA PM2.5 component."""

    path = RAW / "uba_components.json"
    data = json.loads(path.read_text(encoding="utf-8"))

    print("\n=== GERMANY: UBA COMPONENTS ===")

    for key, value in data.items():
        if key in ("count", "indices"):
            continue

        print(f"Component {key}: {value}")


def inspect_defra():
    """Find PM2.5 offerings in the saved DEFRA metadata."""

    path = RAW / "defra_capabilities.xml"

    print("\n=== UNITED KINGDOM: DEFRA PM2.5 ===")

    matches = 0
    london_matches = 0

    # Streaming XML parsing avoids loading the full 12 MB into memory.
    for _, element in ET.iterparse(path, events=("end",)):
        if element.tag.split("}")[-1] != "ObservationOffering":
            continue

        details = " ".join(
            text.strip()
            for text in element.itertext()
            if text and text.strip()
        )

        normalized = details.lower()

        is_pm25 = any(
            term in normalized
            for term in ("pm2.5", "pm2_5", "pm25")
        )

        if is_pm25:
            matches += 1

            if "london" in normalized:
                london_matches += 1

            if matches <= 5 or (
                "london" in normalized and london_matches <= 5
            ):
                print("\nOffering:")
                print(details[:700])

        element.clear()

    print(f"\nPM2.5 offerings found: {matches}")
    print(f"Offerings mentioning London: {london_matches}")


def main():
    inspect_uba()
    inspect_defra()


if __name__ == "__main__":
    main()
