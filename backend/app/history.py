
"""
AirScope | nik
Historical PM2.5 observations API.

Returns genuine UBA measurements for Berlin stations.
Missing values remain null; no interpolation is applied.
"""

from functools import lru_cache
from pathlib import Path

import pandas as pd
from fastapi import APIRouter, HTTPException, Query


ROOT = Path(__file__).resolve().parents[2]

DATA_FILE = (
    ROOT / "data" / "processed" / "berlin_pm25_hourly.parquet"
)

router = APIRouter(prefix="/api/v1", tags=["Historical observations"])


@lru_cache(maxsize=1)
def load_history():
    """Read verified Berlin observations from local Parquet."""

    if not DATA_FILE.exists():
        raise RuntimeError("Berlin observations are unavailable.")

    df = pd.read_parquet(DATA_FILE)

    required = {
        "station_id",
        "station_name",
        "timestamp_utc",
        "pm25_ugm3",
    }

    missing = required - set(df.columns)

    if missing:
        raise RuntimeError(
            f"Missing observation fields: {sorted(missing)}"
        )

    if not isinstance(df["timestamp_utc"].dtype, pd.DatetimeTZDtype):
        raise RuntimeError("Observation timestamps must have a timezone.")

    df["timestamp_utc"] = df["timestamp_utc"].dt.tz_convert("UTC")

    if df.duplicated(["station_id", "timestamp_utc"]).any():
        raise RuntimeError("Duplicate station-hour observations detected.")

    return df.sort_values(["station_id", "timestamp_utc"])


@router.get("/observations/berlin/{station_id}")
def berlin_observations(
    station_id: str,
    days: int = Query(default=7, ge=1, le=90),
):
    """
    Return the latest 1–90 days of stored hourly measurements.

    The window ends at the station's latest stored observation,
    not the current clock time.
    """

    df = load_history()

    station = df.loc[df["station_id"] == station_id].copy()

    if station.empty:
        raise HTTPException(
            status_code=404,
            detail=f"Unknown Berlin station: {station_id}",
        )

    latest = station["timestamp_utc"].max()

    # Include exactly the requested number of hourly slots
    # ending at the latest stored observation.
    start = latest - pd.Timedelta(hours=days * 24 - 1)

    selected = station.loc[
        (station["timestamp_utc"] >= start)
        & (station["timestamp_utc"] <= latest),
        ["timestamp_utc", "pm25_ugm3"],
    ].copy()

    # Reindex missing source hours explicitly as null.
    # These are gaps, not measured zero concentrations.
    hourly_index = pd.date_range(
        start=start,
        end=latest,
        freq="h",
        tz="UTC",
    )

    values = selected.set_index("timestamp_utc")["pm25_ugm3"]
    values = values.reindex(hourly_index)

    observations = [
        {
            "timestamp_utc": timestamp.isoformat(),
            "pm25_ugm3": (
                float(value) if pd.notna(value) else None
            ),
        }
        for timestamp, value in values.items()
    ]

    valid_values = values.dropna()

    return {
        "city": "Berlin",
        "station_id": station_id,
        "station_name": station["station_name"].iloc[0],
        "source": "Umweltbundesamt (UBA)",
        "unit": "ug/m3",
        "is_live": False,
        "window_days": days,
        "window_start_utc": start.isoformat(),
        "window_end_utc": latest.isoformat(),
        "total_hour_slots": len(observations),
        "available_measurements": int(values.notna().sum()),
        "missing_measurements": int(values.isna().sum()),
        "mean_pm25_ugm3": (
            round(float(valid_values.mean()), 3)
            if not valid_values.empty
            else None
        ),
        "observations": observations,
    }
