
"""
AirScope | nik
Download official hourly air-quality data for London Bloomsbury.

Preserve the original CSV before normalizing observations.
"""

from pathlib import Path
from urllib.parse import urljoin, urlparse

import httpx
import pandas as pd
from html.parser import HTMLParser


ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = ROOT / "data" / "raw"

SITE_CODE = "CLL2"
SITE_NAME = "London Bloomsbury"

ARCHIVE_URL = (
    "https://uk-air.defra.gov.uk/data/"
    f"flat_files?site_id={SITE_CODE}"
)

YEARS = (2025, 2026)


class CSVLinkParser(HTMLParser):
    """Collect official CSV download links."""

    def __init__(self):
        super().__init__()
        self.links = []

    def handle_starttag(self, tag, attrs):
        if tag != "a":
            return

        href = dict(attrs).get("href", "")

        if ".csv" in href.lower():
            self.links.append(href)


def main():
    RAW_DIR.mkdir(parents=True, exist_ok=True)

    print(f"AirScope | {SITE_NAME}")
    print("Downloading official hourly CSV files")

    with httpx.Client(
        timeout=120.0,
        follow_redirects=True,
    ) as client:

        page = client.get(ARCHIVE_URL)
        page.raise_for_status()

        parser = CSVLinkParser()
        parser.feed(page.text)

        for year in YEARS:
            expected_name = f"{SITE_CODE}_{year}.csv"

            matches = [
                urljoin(ARCHIVE_URL, link)
                for link in parser.links
                if Path(
                    urlparse(link).path
                ).name == expected_name
            ]

            if not matches:
                print(f"No official CSV link for {year}")
                continue

            csv_url = matches[0]

            response = client.get(csv_url)
            response.raise_for_status()

            output = RAW_DIR / expected_name
            output.write_bytes(response.content)

            print(f"\nYear: {year}")
            print(f"Source: {csv_url}")
            print(f"Saved: {output.relative_to(ROOT)}")
            print(f"Size: {len(response.content):,} bytes")

            # Inspect the original columns before normalization.
            try:
                df = pd.read_csv(
                    output,
                    encoding="utf-8-sig",
                    nrows=5,
                )
            except (UnicodeError, pd.errors.ParserError) as exc:
                print(f"CSV inspection failed: {exc}")
                continue

            print("Columns:")
            print(df.columns.tolist())

            print("\nFirst three rows:")
            print(df.head(3).to_string(index=False))


if __name__ == "__main__":
    main()
