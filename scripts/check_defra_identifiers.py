
"""
AirScope | nik
Inspect DEFRA observation offering identifiers.

Prints real identifiers, names, and observable properties
from the saved official SOS capabilities response.
"""

from pathlib import Path
from xml.etree import ElementTree as ET


ROOT = Path(__file__).resolve().parents[1]
XML_PATH = ROOT / "data" / "raw" / "defra_capabilities.xml"


def local_name(tag):
    return tag.split("}")[-1]


def main():
    print("AirScope | DEFRA offering identifiers")

    tree = ET.parse(XML_PATH)
    root = tree.getroot()

    count = 0
    properties = set()

    for element in root.iter():
        if local_name(element.tag) == "observableProperty":
            value = element.attrib.get("href", "")

            # Some XML namespaces store href with a prefix.
            if not value:
                for key, item in element.attrib.items():
                    if local_name(key) == "href":
                        value = item
                        break

            if value:
                properties.add(value)

        if local_name(element.tag) != "ObservationOffering":
            continue

        count += 1

        if count <= 3:
            print(f"\n=== OFFERING {count} ===")

            for child in element.iter():
                name = local_name(child.tag)

                if name in (
                    "identifier",
                    "name",
                    "observableProperty",
                    "procedure",
                ):
                    text = (child.text or "").strip()
                    attributes = dict(child.attrib)

                    print(
                        f"{name}: "
                        f"text={text!r}, "
                        f"attributes={attributes}"
                    )

    print(f"\nTotal offerings: {count}")

    print("\n=== UNIQUE OBSERVABLE PROPERTIES ===")

    for property_uri in sorted(properties)[:40]:
        print(property_uri)

    print(f"\nUnique property URIs: {len(properties)}")


if __name__ == "__main__":
    main()
