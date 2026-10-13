
"""
AirScope | nik
Read-only verification of data and ML pipeline artifacts.

Checks:
- Berlin and London processed datasets
- Unified forecast feature dataset
- Three trusted Berlin ML model artifacts
- Station evaluation report

Does not ingest data, train models, or overwrite files.
"""

from pathlib import Path

import joblib
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]

DATASETS = {
    "Berlin hourly observations":
        "data/processed/berlin_pm25_hourly.parquet",

    "London hourly observations":
        "data/processed/london_pm25_final.parquet",

    "Forecast features":
        "data/processed/airscope_forecast_features.parquet",

    "Station evaluation":
        "data/processed/berlin_station_evaluation.csv",
}

MODELS = {
    6: "models/berlin_pm25_hgb_6h.joblib",
    12: "models/berlin_pm25_hgb_12h.joblib",
    24: "models/berlin_pm25_hgb_24h.joblib",
}


def section(title):
    print("\n" + "=" * 60)
    print(title)
    print("=" * 60)


def verify_dataset(label, relative_path):
    """Check that a dataset exists and can be read."""

    path = ROOT / relative_path

    if not path.is_file():
        raise FileNotFoundError(
            f"{label}: Missing {relative_path}"
        )

    if path.suffix == ".parquet":
        dataframe = pd.read_parquet(path)
    else:
        dataframe = pd.read_csv(path)

    if dataframe.empty:
        raise ValueError(
            f"{label}: Dataset is empty"
        )

    print(f"PASS: {label}")
    print(f"  File: {relative_path}")
    print(f"  Rows: {len(dataframe):,}")
    print(f"  Columns: {len(dataframe.columns)}")

    return dataframe


def verify_models():
    """Inspect trusted locally generated ML artifacts."""

    section("2. Berlin Forecast Models")

    for horizon, relative_path in MODELS.items():
        path = ROOT / relative_path

        if not path.is_file():
            raise FileNotFoundError(
                f"Missing {relative_path}"
            )

        # Joblib can execute code when loading.
        # Only load the project's trusted local artifacts.
        artifact = joblib.load(path)

        if not isinstance(artifact, dict):
            raise TypeError(
                f"{horizon}h artifact must be a dictionary"
            )

        required = {
            "model",
            "feature_columns",
            "horizon_hours",
        }

        missing = required - set(artifact)

        if missing:
            raise ValueError(
                f"{horizon}h model missing fields: {missing}"
            )

        if artifact["horizon_hours"] != horizon:
            raise ValueError(
                f"{horizon}h model has incorrect horizon"
            )

        print(f"PASS: {horizon}h model")
        print(
            f"  Features: "
            f"{len(artifact['feature_columns'])}"
        )


def verify_evaluation(dataframe):
    """Verify saved station evaluation coverage."""

    section("3. Station Evaluation")

    required = {
        "station_id",
        "horizon_hours",
        "samples",
        "baseline_mae",
        "model_mae",
    }

    missing = required - set(dataframe.columns)

    if missing:
        raise ValueError(
            f"Station evaluation missing columns: {missing}"
        )

    assert len(dataframe) == 36
    assert dataframe["station_id"].nunique() == 12
    assert set(
        dataframe["horizon_hours"].unique()
    ) == {6, 12, 24}

    print("PASS: 36 station-horizon evaluations")
    print("PASS: 12 Berlin monitoring stations")
    print("PASS: 6h, 12h, 24h evaluation coverage")


def main():
    print("=" * 60)
    print("AirScope | Pipeline Artifact Verification")
    print("=" * 60)

    section("1. Processed Datasets")

    evaluation = None

    for label, relative_path in DATASETS.items():
        dataframe = verify_dataset(
            label,
            relative_path,
        )

        if label == "Station evaluation":
            evaluation = dataframe

    verify_models()

    if evaluation is None:
        raise RuntimeError(
            "Station evaluation dataset was not loaded"
        )

    verify_evaluation(evaluation)

    section("4. Verification Summary")

    print("All existing pipeline artifacts passed.")
    print(
        "This verifies saved files, not full regeneration "
        "from official raw sources."
    )


if __name__ == "__main__":
    main()
