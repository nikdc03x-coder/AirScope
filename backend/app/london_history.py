
"""
AirScope | nik
Historical London PM2.5 observations API.

Reads verified DEFRA UK-AIR observations, preserves
ratified/provisional quality labels and missing hours.
Never interpolates or fabricates measurements.
"""

from functools import lru_cache
from pathlib import Path

import pandas as pd
from fastapi import APIRouter, HTTPException, Query


ROOT = Path(__file__).resolve().parents[2]
DATA_FILE = ROOT / "data/processed/london_pm25_final.parquet"

router = APIRouter(
    prefix="/api/v1",
    tags=["London historical observations"],
)

STATION_ID = "CLL2"
STATION_NAME = "London Bloomsbury"


@lru_cache(maxsize=1)
def load_london():
    """Load London's verified source observations."""

    if not DATA_FILE.exists():
        raise RuntimeError(
            "London dataset not found. Run the London "
            "ingestion pipeline first."
        )

    df = pd.read_parquet(DATA_FILE)

    # Accept only known AirScope PM2.5 column names.
    value_column = next(
        (
            name
            for name in [
                "pm25_ugm3",
                "pm25",
                "pm25_value",
                "pm25_concentration",
            ]
            if name in df.columns
        ),
        None,
    )

    if value_column is None:
        raise RuntimeError(
            "London PM2.5 column not recognized: "
            f"{list(df.columns)}"
        )

    if "timestamp_utc" not in df.columns:
        raise RuntimeError(
            "London data has no timestamp_utc column."
        )

    if "quality_status" not in df.columns:
        raise RuntimeError(
            "London data has no quality_status column."
        )

    if not isinstance(
        df["timestamp_utc"].dtype,
        pd.DatetimeTZDtype,
    ):
        raise RuntimeError(
            "London timestamps must be timezone-aware."
        )

    normalized = pd.DataFrame({
        "timestamp_utc": (
            df["timestamp_utc"].dt.tz_convert("UTC")
        ),
        "pm25_ugm3": pd.to_numeric(
            df[value_column],
            errors="coerce",
        ),
        "quality_status": (
            df["quality_status"]
            .fillna("missing_or_unknown")
            .astype(str)
        ),
    })

    if normalized["timestamp_utc"].duplicated().any():
        raise RuntimeError(
            "Duplicate London hourly timestamps detected."
        )

    return normalized.sort_values(
        "timestamp_utc"
    ).reset_index(drop=True)


@router.get("/observations/london/{station_id}")
def london_observations(
    station_id: str,
    days: int = Query(default=7, ge=1, le=90),
):
    """Return the latest stored London hourly observations."""

    if station_id != STATION_ID:
        raise HTTPException(
            status_code=404,
            detail=f"Unknown London station: {station_id}",
        )

    df = load_london()

    if df.empty:
        raise HTTPException(
            status_code=503,
            detail="No London observations available.",
        )

    end = df["timestamp_utc"].max()
    start = end - pd.Timedelta(hours=days * 24 - 1)

    selected = df.loc[
        (df["timestamp_utc"] >= start)
        & (df["timestamp_utc"] <= end)
    ].copy()

    # Reindex creates explicit gaps without inventing values.
    hourly_index = pd.date_range(
        start=start,
        end=end,
        freq="h",
        tz="UTC",
    )

    hourly = selected.set_index(
        "timestamp_utc"
    ).reindex(hourly_index)

    observations = []

    for timestamp, record in hourly.iterrows():
        value = record["pm25_ugm3"]
        quality = record["quality_status"]

        observations.append({
            "timestamp_utc": timestamp.isoformat(),
            "pm25_ugm3": (
                float(value) if pd.notna(value) else None
            ),
            "quality_status": (
                str(quality)
                if pd.notna(quality)
                else "missing_hour"
            ),
        })

    values = hourly["pm25_ugm3"]
    quality_counts = (
        hourly["quality_status"]
        .fillna("missing_hour")
        .value_counts()
        .to_dict()
    )

    return {
        "city": "London",
        "station_id": STATION_ID,
        "station_name": STATION_NAME,
        "source": "DEFRA UK-AIR",
        "unit": "ug/m3",
        "is_live": False,
        "window_days": days,
        "window_start_utc": start.isoformat(),
        "window_end_utc": end.isoformat(),
        "total_hour_slots": len(hourly),
        "available_measurements": int(values.notna().sum()),
        "missing_measurements": int(values.isna().sum()),
        "mean_pm25_ugm3": (
            round(float(values.mean()), 3)
            if values.notna().any()
            else None
        ),
        "quality_counts": {
            str(key): int(value)
            for key, value in quality_counts.items()
        },
        "observations": observations,
    }
