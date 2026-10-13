
"""
AirScope | nik
Read-only station-level evaluation API.

Serves genuine saved test-set metrics for the
12 Berlin monitoring stations and three horizons.
"""

from functools import lru_cache
from pathlib import Path

import pandas as pd
from fastapi import APIRouter, HTTPException, Query


ROOT = Path(__file__).resolve().parents[2]
REPORT_PATH = (
    ROOT / "data" / "processed"
    / "berlin_station_evaluation.csv"
)

router = APIRouter(
    prefix="/api/v1",
    tags=["Model evaluation"],
)

REQUIRED_COLUMNS = {
    "station_id",
    "station_name",
    "horizon_hours",
    "samples",
    "baseline_mae",
    "model_mae",
    "baseline_rmse",
    "model_rmse",
    "mae_improvement_pct",
    "model_bias",
}


@lru_cache(maxsize=1)
def load_evaluation():
    """Load the locally generated evaluation report."""

    if not REPORT_PATH.exists():
        raise FileNotFoundError(
            "Station evaluation report not found. "
            "Run ml/evaluation/evaluate_stations.py."
        )

    df = pd.read_csv(REPORT_PATH)

    missing = REQUIRED_COLUMNS - set(df.columns)

    if missing:
        raise ValueError(
            f"Missing evaluation fields: {sorted(missing)}"
        )

    if df.duplicated(
        ["station_id", "horizon_hours"]
    ).any():
        raise ValueError(
            "Duplicate station-horizon evaluation records."
        )

    if len(df) != 36:
        raise ValueError(
            f"Expected 36 records, found {len(df)}."
        )

    if df["station_id"].nunique() != 12:
        raise ValueError(
            "Expected exactly 12 Berlin stations."
        )

    if set(df["horizon_hours"]) != {6, 12, 24}:
        raise ValueError(
            "Expected 6h, 12h and 24h horizons."
        )

    return df.sort_values(
        ["horizon_hours", "station_name"]
    ).reset_index(drop=True)


@router.get("/evaluation/berlin/stations")
def station_evaluation(
    horizon: int = Query(default=24),
):
    """Return station metrics for one forecast horizon."""

    if horizon not in (6, 12, 24):
        raise HTTPException(
            status_code=422,
            detail="Horizon must be 6, 12, or 24 hours.",
        )

    try:
        df = load_evaluation()
    except (FileNotFoundError, ValueError) as error:
        raise HTTPException(
            status_code=503,
            detail=str(error),
        ) from error

    selected = df.loc[
        df["horizon_hours"] == horizon
    ].copy()

    records = []

    for row in selected.itertuples(index=False):
        records.append({
            "station_id": row.station_id,
            "station_name": row.station_name,
            "horizon_hours": int(row.horizon_hours),
            "samples": int(row.samples),
            "baseline_mae": float(row.baseline_mae),
            "model_mae": float(row.model_mae),
            "baseline_rmse": float(row.baseline_rmse),
            "model_rmse": float(row.model_rmse),
            "mae_improvement_pct": (
                float(row.mae_improvement_pct)
                if pd.notna(row.mae_improvement_pct)
                else None
            ),
            "model_bias": float(row.model_bias),
        })

    return {
        "city": "Berlin",
        "evaluation_partition": "test",
        "horizon_hours": horizon,
        "station_count": len(records),
        "unit": "µg/m³",
        "is_live": False,
        "stations": records,
    }
