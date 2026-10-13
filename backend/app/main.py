
"""
AirScope | nik
FastAPI backend for Berlin PM2.5 forecasting.

- Read genuine stored UBA observations.
- Load the three trained Berlin forecasting models.
- Construct features using observed history only.
- Return the source timestamp with each prediction.

Forecasts are experimental and not live air-quality alerts.
"""

from functools import lru_cache
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from backend.app.history import router as history_router
from backend.app.london_history import router as london_history_router
ROOT = Path(__file__).resolve().parents[2]

DATA_FILE = (
    ROOT / "data" / "processed" / "berlin_pm25_hourly.parquet"
)

MODEL_DIR = ROOT / "models"

HORIZONS = [6, 12, 24]
LAGS = [1, 3, 6, 12, 24]


app = FastAPI(
    title="AirScope API",
    description="Historical PM2.5 observations and experimental forecasts.",
    version="0.1.0",
)
# AirScope | nik
# Allow the local React development server to call FastAPI.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=False,
    allow_methods=["GET"],
    allow_headers=["*"],
)

# Register historical PM2.5 observations without changing
# the existing station or forecasting endpoints.
app.include_router(history_router)
# AirScope | nik
# Make official London observations available to React.
app.include_router(london_history_router)
@lru_cache(maxsize=1)
def load_observations():
    """Load stored Berlin observations once."""

    if not DATA_FILE.exists():
        raise RuntimeError(
            f"Berlin dataset not found: {DATA_FILE}"
        )

    df = pd.read_parquet(DATA_FILE)

    required = {
        "station_id",
        "station_name",
        "timestamp_utc",
        "pm25_ugm3",
        "latitude",
        "longitude",
    }

    missing = required - set(df.columns)

    if missing:
        raise RuntimeError(
            f"Missing Berlin columns: {sorted(missing)}"
        )

    if str(df["timestamp_utc"].dt.tz) != "UTC":
        raise RuntimeError(
            "Berlin observation timestamps must use UTC."
        )

    if df.duplicated(
        ["station_id", "timestamp_utc"]
    ).any():
        raise RuntimeError(
            "Duplicate station-hour observations."
        )

    return df.sort_values(
        ["station_id", "timestamp_utc"]
    ).reset_index(drop=True)


@lru_cache(maxsize=3)
def load_model(horizon):
    """Load only locally trained, trusted model files."""

    if horizon not in HORIZONS:
        raise ValueError("Unsupported forecast horizon.")

    path = MODEL_DIR / (
        f"berlin_pm25_hgb_{horizon}h.joblib"
    )

    if not path.exists():
        raise RuntimeError(
            f"Trained model not found: {path}"
        )

    artifact = joblib.load(path)

    if artifact.get("horizon_hours") != horizon:
        raise RuntimeError(
            "Saved model horizon does not match its filename."
        )

    return artifact


def find_valid_origin(station):
    """
    Find the latest observed hour with all required lags.

    Do not interpolate across missing hours.
    """

    station = station.set_index(
        "timestamp_utc"
    ).sort_index()

    values = pd.to_numeric(
        station["pm25_ugm3"],
        errors="coerce",
    )

    for origin in reversed(station.index):

        required_times = [
            origin,
            *[
                origin - pd.Timedelta(hours=lag)
                for lag in LAGS
            ],
        ]

        historical = values.reindex(required_times)

        if historical.notna().all():
            return origin, historical

    raise HTTPException(
        status_code=422,
        detail="No complete 24-hour input history exists.",
    )


def build_features(station_id, origin, historical):
    """Recreate the feature engineering used during training."""

    features = {
        "pm25_current": float(historical.iloc[0]),
    }

    for position, lag in enumerate(LAGS, start=1):
        features[f"pm25_lag_{lag}h"] = float(
            historical.iloc[position]
        )

    hour = origin.hour
    weekday = origin.dayofweek
    day_of_year = origin.dayofyear

    features.update({
        "hour_sin": float(np.sin(2 * np.pi * hour / 24)),
        "hour_cos": float(np.cos(2 * np.pi * hour / 24)),
        "weekday_sin": float(
            np.sin(2 * np.pi * weekday / 7)
        ),
        "weekday_cos": float(
            np.cos(2 * np.pi * weekday / 7)
        ),
        "year_sin": float(
            np.sin(2 * np.pi * day_of_year / 365.25)
        ),
        "year_cos": float(
            np.cos(2 * np.pi * day_of_year / 365.25)
        ),
    })

    # Match the one-hot station features saved at training.
    features[f"station_{station_id}"] = 1

    return features


@app.get("/api/v1/health")
def health():
    """Simple API health check."""

    return {
        "service": "AirScope",
        "status": "ok",
        "version": "0.1.0",
    }


@app.get("/api/v1/stations")
def list_stations():
    """List Berlin stations available in stored observations."""

    df = load_observations()

    stations = (
        df.sort_values("timestamp_utc")
        .groupby("station_id", as_index=False)
        .last()
    )

    return {
        "city": "Berlin",
        "station_count": len(stations),
        "stations": [
            {
                "station_id": row["station_id"],
                "station_name": row["station_name"],
                "latitude": float(row["latitude"]),
                "longitude": float(row["longitude"]),
                "latest_observation_utc": (
                    row["timestamp_utc"].isoformat()
                ),
            }
            for _, row in stations.iterrows()
        ],
    }


@app.get("/api/v1/forecasts/berlin/{station_id}")
def forecast_berlin(station_id: str):
    """Generate forecasts from stored historical observations."""

    df = load_observations()

    station = df.loc[
        df["station_id"] == station_id
    ].copy()

    if station.empty:
        raise HTTPException(
            status_code=404,
            detail=f"Unknown Berlin station: {station_id}",
        )

    origin, historical = find_valid_origin(station)

    input_features = build_features(
        station_id,
        origin,
        historical,
    )

    predictions = []

    for horizon in HORIZONS:
        artifact = load_model(horizon)

        feature_columns = artifact["feature_columns"]

        # All training features must be known at inference.
        # Unset one-hot station columns correctly remain 0.
        feature_row = {
            name: input_features.get(name, 0)
            for name in feature_columns
        }

        missing_features = [
            name
            for name in feature_columns
            if name not in input_features
            and not name.startswith("station_")
        ]

        if missing_features:
            raise RuntimeError(
                f"Missing inference features: {missing_features}"
            )

        X = pd.DataFrame(
            [feature_row],
            columns=feature_columns,
        )

        prediction = float(
            artifact["model"].predict(X)[0]
        )

        target_time = (
            origin + pd.Timedelta(hours=horizon)
        )

        predictions.append({
            "horizon_hours": horizon,
            "target_timestamp_utc": target_time.isoformat(),
            "predicted_pm25_ugm3": round(prediction, 3),
        })

    return {
        "city": "Berlin",
        "station_id": station_id,
        "station_name": station["station_name"].iloc[0],
        "model": "hist_gradient_boosting",
        "data_source": "Umweltbundesamt (UBA)",
        "forecast_origin_utc": origin.isoformat(),
        "latest_stored_observation_utc": (
            station["timestamp_utc"].max().isoformat()
        ),
        "current_pm25_ugm3": float(historical.iloc[0]),
        "unit": "ug/m3",
        "forecast_type": "historical_data_snapshot",
        "is_live": False,
        "predictions": predictions,
        "disclaimer": (
            "Experimental forecast using stored observations. "
            "Not a live air-quality warning service."
        ),
    }
