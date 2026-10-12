
"""
AirScope | nik
Sprint 1: Verify official air-quality data sources.

This script:
1. Contacts Germany's UBA air-quality API.
2. Contacts the UK's DEFRA SOS service.
3. Saves the original responses.
4. Reports whether each source is accessible.

No measurements are invented or modified.
"""

from pathlib import Path
import json

import httpx


# Resolve the project folder independently of where Python runs.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = PROJECT_ROOT / "data" / "raw"
RAW_DIR.mkdir(parents=True, exist_ok=True)


SOURCES = {
    "uba_components": {
        "url": "https://www.umweltbundesamt.de/api/air_data/v2/components/json",
        "filename": "uba_components.json",
    },
    "defra_capabilities": {
        "url": "https://uk-air.defra.gov.uk/sos-ukair/service",
        "params": {
            "service": "SOS",
            "request": "GetCapabilities",
        },
        "filename": "defra_capabilities.xml",
    },
}


def download_source(client, name, config):
    """Download one official source and preserve its response."""

    print(f"\nChecking {name}...")

    response = client.get(
        config["url"],
        params=config.get("params"),
    )

    response.raise_for_status()

    # Save the response without changing the original data.
    output_path = RAW_DIR / config["filename"]
    output_path.write_bytes(response.content)

    print(f"Status: {response.status_code}")
    print(f"Saved: {output_path.relative_to(PROJECT_ROOT)}")
    print(f"Size: {len(response.content):,} bytes")

    # Check the expected response format.
    if name == "uba_components":
        data = response.json()
        print(f"JSON response type: {type(data).__name__}")

        if isinstance(data, dict):
            print(f"Top-level keys: {list(data.keys())[:10]}")

    elif name == "defra_capabilities":
        from xml.etree import ElementTree

        root = ElementTree.fromstring(response.content)
        print(f"XML root: {root.tag}")


def main():
    """Check each source independently."""

    print("AirScope | Official data source verification")

    results = {}

    with httpx.Client(
        timeout=45.0,
        follow_redirects=True,
        headers={"User-Agent": "AirScope-Research/0.1"},
    ) as client:

        for name, config in SOURCES.items():
            try:
                download_source(client, name, config)
                results[name] = "success"

            except (httpx.HTTPError, ValueError) as error:
                results[name] = "failed"
                print(f"Source error: {error}")

            except Exception as error:
                results[name] = "failed"
                print(f"Unexpected error: {error}")

    # Save a compact report of this verification run.
    report_path = RAW_DIR / "source_check.json"
    report_path.write_text(
        json.dumps(results, indent=2),
        encoding="utf-8",
    )

    print("\nVerification summary:")
    for name, status in results.items():
        print(f"  {name}: {status}")

    if any(status == "failed" for status in results.values()):
        raise SystemExit(
            "Some sources failed. Review the errors above."
        )


if __name__ == "__main__":
    main()
