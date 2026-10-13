
"""
AirScope | nik
Inspect ML feature and model artifact structures.

Read-only inspection before station-level evaluation.
Does not retrain models or modify any data.
"""

from pathlib import Path

import joblib
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]

FEATURES_PATH = (
    ROOT / "data" / "processed"
    / "airscope_forecast_features.parquet"
)

MODELS_DIR = ROOT / "models"


def inspect_features():
    """Display feature schema and test partition information."""

    print("\n" + "=" * 60)
    print("AIRScope | FORECAST FEATURES")
    print("=" * 60)

    if not FEATURES_PATH.exists():
        print("Feature file not found:", FEATURES_PATH)
        return

    df = pd.read_parquet(FEATURES_PATH)

    print("\nShape:", df.shape)

    print("\nColumns and types:")
    for column, dtype in df.dtypes.items():
        print(f"  {column}: {dtype}")

    print("\nFirst two rows:")
    print(df.head(2).to_string(index=False))

    for column in ["split", "partition", "dataset_split"]:
        if column in df.columns:
            print(f"\n{column} distribution:")
            print(
                df[column]
                .value_counts(dropna=False)
                .to_string()
            )

    if "station_id" in df.columns:
        print("\nStation counts:")
        print(df["station_id"].value_counts().to_string())

    if "city" in df.columns:
        print("\nCity counts:")
        print(df["city"].value_counts().to_string())


def inspect_models():
    """Inspect locally trained model artifact structures."""

    print("\n" + "=" * 60)
    print("AIRScope | SAVED MODELS")
    print("=" * 60)

    for horizon in (6, 12, 24):
        path = (
            MODELS_DIR
            / f"berlin_pm25_hgb_{horizon}h.joblib"
        )

        print(f"\n--- {horizon}h model ---")

        if not path.exists():
            print("Not found:", path)
            continue

        # Only load locally created, trusted joblib files.
        bundle = joblib.load(path)

        print("Artifact type:", type(bundle).__name__)

        if isinstance(bundle, dict):
            print("Artifact keys:", list(bundle.keys()))

            for key, value in bundle.items():
                if key in {
                    "feature_columns",
                    "features",
                    "input_columns",
                }:
                    print(f"\n{key}:")
                    print(value)
                elif key in {
                    "model",
                    "estimator",
                    "regressor",
                }:
                    print(
                        f"{key} type:",
                        type(value).__name__,
                    )
                else:
                    print(
                        f"{key} type:",
                        type(value).__name__,
                    )
        else:
            print(
                "Model feature names:",
                getattr(
                    bundle,
                    "feature_names_in_",
                    "Not available",
                ),
            )


def main():
    inspect_features()
    inspect_models()

    print("\nInspection complete. No files modified.")


if __name__ == "__main__":
    main()
