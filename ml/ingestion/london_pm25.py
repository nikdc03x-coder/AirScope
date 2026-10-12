
"""
AirScope | nik
Identify London PM2.5 monitoring features using DEFRA metadata.

Only features with a matching official PM2.5 offering and
a verified geographic location are included.
"""

from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[2]

REGISTRY_PATH = ROOT / "data/processed/defra_pm25_registry.csv"
LOCATIONS_PATH = ROOT / "data/processed/defra_station_locations.csv"

OUTPUT_PATH = ROOT / "data/processed/london_pm25_stations.csv"

OFFERING_PREFIX = (
    "http://environment.data.gov.uk/"
    "air-quality/so/GB_Offering_"
)

FEATURE_PREFIX = (
    "http://environment.data.gov.uk/"
    "air-quality/so/GB_SamplingFeature_"
)


def main():
    """Connect PM2.5 offerings to geographic sampling features."""

    offerings = pd.read_csv(REGISTRY_PATH)
    locations = pd.read_csv(LOCATIONS_PATH)

    # Extract official numeric suffixes for candidate matching.
    offerings["reference_number"] = (
        offerings["offering_id"]
        .str.removeprefix(OFFERING_PREFIX)
    )

    locations["reference_number"] = (
        locations["feature_id"]
        .str.removeprefix(FEATURE_PREFIX)
    )

    # Join the records using matching reference numbers.
    matched = offerings.merge(
        locations,
        on="reference_number",
        how="inner",
        validate="one_to_one",
    )

    # Keep stations whose official names identify London.
    london = matched[
        matched["station_name"].str.contains(
            "London",
            case=False,
            na=False,
        )
    ].copy()

    # Confirm that the coordinates are in the London region.
    london = london[
        london["coordinate_1"].between(51.25, 51.75)
        & london["coordinate_2"].between(-0.55, 0.35)
    ].copy()

    # Retain only the fields needed for downstream ingestion.
    london = london[[
        "offering_id",
        "procedure_id",
        "feature_id",
        "station_name",
        "coordinate_1",
        "coordinate_2",
        "pollutant",
        "unit",
        "source_x",
    ]].rename(columns={
        "coordinate_1": "latitude",
        "coordinate_2": "longitude",
        "source_x": "source",
    })

    london = london.sort_values("station_name")

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    london.to_csv(
        OUTPUT_PATH,
        index=False,
        encoding="utf-8",
    )

    print("AirScope | London PM2.5 stations")
    print(f"Total matched offerings: {len(matched)}")
    print(f"London PM2.5 features: {len(london)}")

    print("\nStations:")
    print(
        london[[
            "station_name",
            "latitude",
            "longitude",
        ]].to_string(index=False)
    )

    print(f"\nSaved: {OUTPUT_PATH.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
