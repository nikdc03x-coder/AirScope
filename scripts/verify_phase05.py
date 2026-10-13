
"""
AirScope | nik
Phase 5 verification.

Checks:
- Saved model artifacts
- Station-level evaluation report
- Reproduced test metrics
- Evaluation API responses

No retraining or dataset modifications.
"""

import json
from pathlib import Path

import joblib
import pandas as pd
from fastapi.testclient import TestClient

from backend.app.main import app


ROOT = Path(__file__).resolve().parents[1]
REPORT_DIR = ROOT / "data" / "processed"
MODEL_DIR = ROOT / "models"

EXPECTED = {
    6: (9404, 0.9696, 0.9292),
    12: (9176, 1.8102, 1.6712),
    24: (8736, 3.1725, 2.9142),
}


def verify_models():
    """Confirm all trained Berlin models exist."""

    print("\n[1] Saved ML models")

    for horizon in (6, 12, 24):
        path = (
            MODEL_DIR
            / f"berlin_pm25_hgb_{horizon}h.joblib"
        )

        assert path.exists(), f"Missing model: {path}"

        # Load only locally trained, trusted model artifacts.
        bundle = joblib.load(path)

        assert bundle["horizon_hours"] == horizon
        assert len(bundle["feature_columns"]) == 24

        print(f"  PASS: {horizon}h model")


def verify_station_report():
    """Check station-level evaluation completeness."""

    print("\n[2] Station evaluation report")

    csv_path = (
        REPORT_DIR / "berlin_station_evaluation.csv"
    )

    summary_path = (
        REPORT_DIR
        / "berlin_station_evaluation_summary.json"
    )

    assert csv_path.exists(), "Station CSV report missing"
    assert summary_path.exists(), "Station JSON summary missing"

    df = pd.read_csv(csv_path)

    assert len(df) == 36
    assert df["station_id"].nunique() == 12
    assert set(df["horizon_hours"]) == {6, 12, 24}

    assert not df.duplicated(
        ["station_id", "horizon_hours"]
    ).any()

    with summary_path.open(encoding="utf-8") as file:
        summary = json.load(file)

    for result in summary["overall"]:
        horizon = result["horizon_hours"]

        expected_samples, expected_baseline, expected_model = (
            EXPECTED[horizon]
        )

        assert result["samples"] == expected_samples

        assert abs(
            result["baseline_mae"] - expected_baseline
        ) < 0.005

        assert abs(
            result["model_mae"] - expected_model
        ) < 0.005

    print("  PASS: 36 station-horizon evaluations")
    print("  PASS: Reproduced overall test metrics")


def verify_api():
    """Test FastAPI endpoints without starting a server."""

    print("\n[3] FastAPI evaluation endpoints")

    client = TestClient(app)

    for horizon in (6, 12, 24):
        response = client.get(
            "/api/v1/evaluation/berlin/stations",
            params={"horizon": horizon},
        )

        assert response.status_code == 200, (
            f"{horizon}h API returned {response.status_code}: "
            f"{response.text}"
        )

        data = response.json()

        assert data["horizon_hours"] == horizon
        assert data["station_count"] == 12
        assert len(data["stations"]) == 12
        assert data["is_live"] is False

        print(f"  PASS: {horizon}h station evaluation API")

    invalid = client.get(
        "/api/v1/evaluation/berlin/stations",
        params={"horizon": 5},
    )

    assert invalid.status_code == 422
    print("  PASS: Invalid horizon rejected")


def main():
    print("=" * 60)
    print("AirScope | Phase 5 Verification")
    print("=" * 60)

    verify_models()
    verify_station_report()
    verify_api()

    print("\nAll Phase 5 backend checks passed.")


if __name__ == "__main__":
    main()
