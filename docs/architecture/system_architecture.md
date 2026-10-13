# AirScope — System Architecture

**Project:** AirScope  
**Focus:** PM2.5 monitoring, historical analysis and ML forecasting  
**Cities:** Berlin, Germany and London, United Kingdom  
**Project type:** Research-oriented full-stack application  
**Status:** Experimental prototype

---

## 1. Project overview

AirScope is a web application that uses official environmental
observations to explore historical PM2.5 concentrations and
demonstrate machine-learning-based forecasting.

The application combines:

- Official environmental datasets
- Data validation and preprocessing
- Time-series feature engineering
- Machine-learning forecasting
- Reproducible model evaluation
- A Python FastAPI backend
- A React and TypeScript frontend

The application is not a live operational air-quality warning service.

## 2. System architecture

```text
            OFFICIAL ENVIRONMENTAL SOURCES
                        |
          +-------------+-------------+
          |                           |
     UBA air-data                 DEFRA UK-AIR
     Berlin, Germany              London, UK
          |                           |
          +-------------+-------------+
                        |
                DATA INGESTION
                        |
                 DATA VALIDATION
                        |
                PARQUET STORAGE
                        |
          +-------------+-------------+
          |                           |
    HISTORICAL DATA             ML PIPELINE
          |                           |
          |                    Feature engineering
          |                           |
          |                    Train / validation / test
          |                           |
          |                    Persistence baseline
          |                           |
          |                    Gradient boosting models
          |                           |
          |                    Evaluation reports
          |                           |
          +-------------+-------------+
                        |
                   FASTAPI API
                        |
               HTTP / JSON responses
                        |
                 REACT FRONTEND
                        |
       +----------------+----------------+
       |                |                |
   City dashboard   Trend charts    Model evaluation
       |                |                |
   Station choice   Data quality     Accuracy + limitations
```

## 3. Data ingestion

### Berlin

Source: German Umweltbundesamt (UBA).

AirScope uses official hourly PM2.5 observations from
12 monitoring stations.

The Berlin ingestion pipeline:

1. Requests official air-quality observations.
2. Retrieves monitoring station metadata.
3. Normalizes source timestamps to UTC.
4. Preserves missing measurements.
5. Validates station-hour records.
6. Stores processed observations as Parquet.

Processed dataset:

    data/processed/berlin_pm25_hourly.parquet

Some official API intervals contain missing observation
hours. These gaps are not replaced with artificial values.

### London

Source: DEFRA UK-AIR.

AirScope uses hourly PM2.5 observations from the
London Bloomsbury monitoring station, CLL2.

The London ingestion pipeline:

1. Reads official source observations.
2. Normalizes hour-ending timestamps.
3. Preserves ratified and provisional quality flags.
4. Checks missing observations.
5. Exports normalized Parquet data.

Processed dataset:

    data/processed/london_pm25_final.parquet

Historical visualization may display provisional
observations with quality information.

The stricter ML development pipeline restricts eligible
London observations to ratified measurements.

## 4. Unified data preparation

A unified dataset combines Berlin and London observations
using consistent column names and UTC timestamps.

Saved dataset:

    data/processed/airscope_pm25_unified.parquet

Recorded dataset characteristics:

- 198,900 station-hour records
- 13 stations
- No duplicate station-hour combinations

Missing observations are not silently interpolated.

## 5. Feature engineering

Forecast examples use past PM2.5 concentrations,
station identity and cyclical time information.

### PM2.5 inputs

- Current concentration
- 1-hour lag
- 3-hour lag
- 6-hour lag
- 12-hour lag
- 24-hour lag

### Time inputs

- Hour sine and cosine
- Weekday sine and cosine
- Year-cycle sine and cosine

### Spatial identifiers

- One-hot encoded Berlin station IDs

### Prediction targets

Three independent forecast horizons:

- 6 hours ahead
- 12 hours ahead
- 24 hours ahead

Saved feature dataset:

    data/processed/airscope_forecast_features.parquet

Training examples use exact lag and target timestamps.

The pipeline avoids constructing target examples across
chronological partition boundaries.

## 6. Training and evaluation

### Chronological partitions

| Partition  | Time                  |
| ---------- | --------------------- |
| Training   | Before July 2026      |
| Validation | July–August 2026      |
| Test       | September 2026 onward |

### Baseline

Persistence forecasting predicts that the present
PM2.5 concentration remains unchanged at the future
target timestamp.

### ML model

The forecasting approach uses scikit-learn's
HistGradientBoostingRegressor.

There is one trained Berlin model per horizon.

Saved artifacts:

    models/berlin_pm25_hgb_6h.joblib
    models/berlin_pm25_hgb_12h.joblib
    models/berlin_pm25_hgb_24h.joblib

Model artifacts also contain the expected feature columns.

Only trusted locally generated model files should be loaded.

## 7. Verified Berlin test results

| Horizon | Samples | Persistence MAE | ML MAE | Persistence RMSE | ML RMSE |
| ------- | ------: | --------------: | -----: | ---------------: | ------: |
| 6h      |   9,404 |          0.9696 | 0.9292 |           2.3693 |  2.6415 |
| 12h     |   9,176 |          1.8102 | 1.6712 |           4.3221 |  3.9935 |
| 24h     |   8,736 |          3.1725 | 2.9142 |           7.2063 |  5.9941 |

All errors are measured in µg/m³.

The ML models improved overall test MAE at all three
horizons.

However, the 6-hour model performed worse than
persistence on RMSE.

The project reports both improvements and limitations.

## 8. Station-level evaluation

AirScope also calculates separate forecasting metrics
for all 12 Berlin monitoring stations.

Each station is evaluated independently at:

- 6 hours
- 12 hours
- 24 hours

That produces 36 station-horizon evaluations.

Recorded reports:

    data/processed/berlin_station_evaluation.csv
    data/processed/berlin_station_evaluation_summary.json

Evaluation metrics include:

- Test sample count
- ML MAE
- Persistence MAE
- ML RMSE
- Persistence RMSE
- MAE improvement percentage
- Prediction bias

The Frankfurter Allee station demonstrates how
localized pollution episodes can influence forecasting
errors.

## 9. Backend architecture

Framework: FastAPI.

The backend reads stored Parquet observations,
loads trusted model artifacts, creates predictions
and exposes JSON APIs.

### Main endpoints

| Endpoint                                     | Purpose                  |
| -------------------------------------------- | ------------------------ |
| GET /api/v1/health                           | Service health           |
| GET /api/v1/stations                         | Berlin station metadata  |
| GET /api/v1/forecasts/berlin/{station_id}    | Berlin ML forecasts      |
| GET /api/v1/observations/berlin/{station_id} | Berlin history           |
| GET /api/v1/observations/london/{station_id} | London history           |
| GET /api/v1/evaluation/berlin/stations       | Station-level evaluation |

The historical observation endpoints support a
`days` query parameter with a supported range of
1–90 days.

The station evaluation endpoint supports horizons
of 6, 12 and 24 hours.

The frontend communicates with the backend using
HTTP requests and JSON responses.

## 10. Frontend architecture

Technology stack:

- React
- TypeScript
- Vite
- Material UI
- React Router
- i18next
- Recharts

The frontend includes:

### Berlin dashboard

- Monitoring station selection
- Experimental ML predictions
- Historical hourly PM2.5 visualization
- Data freshness information

### London dashboard

- Historical PM2.5 visualization
- Observation quality information
- Data freshness information
- Transparent statement of forecasting limitations

### City comparison

- Berlin Wedding and London Bloomsbury
- Historical daily PM2.5 comparison
- Selectable time ranges

### Evaluation dashboard

- Overall ML and persistence comparison
- Recorded test metrics
- Station-level accuracy visualization
- Model limitations

### Transparency

- Official data sources
- Historical/not-live indicators
- Scientific evaluation disclosures

## 11. Data freshness

Historical datasets are not automatically updated
when the dashboard is opened.

Freshness indicators report timestamps from the
latest stored available observations.

This is not the same as verifying that a measurement
is currently being collected in real time.

The application distinguishes historical observations
from experimental model predictions.

## 12. Known limitations

1. The prediction service currently uses stored observations.
2. Berlin forecasting models are experimental.
3. London does not have independently validated ML forecasts.
4. Extreme localized pollution events can cause large errors.
5. Model performance may vary by station.
6. The current model inputs do not include future weather forecasts.
7. The historical city comparison represents individual stations,
   not complete citywide pollution exposure.
8. London provisional observations require appropriate quality
   interpretation before scientific comparisons.
9. Additional future-period evaluations are needed to demonstrate
   stronger model generalization.

## 13. Local development

### Backend

Run from the project root:

    source .venv/Scripts/activate
    python -m uvicorn backend.app.main:app --reload

Local backend:

    http://127.0.0.1:8000

Interactive API documentation:

    http://127.0.0.1:8000/docs

### Frontend

Run from the frontend directory:

    cd frontend
    npm install
    npm run dev

Local frontend:

    http://localhost:5173

### Frontend checks

    npm run lint
    npm run build

### Model evaluation

Run from the project root:

    python ml/evaluation/evaluate_stations.py

### Phase 5 verification

    python -m scripts.verify_phase05

## 14. Repository development workflow

AirScope development uses phase-specific Git branches.

Completed phases are committed incrementally.

Branches are not merged into main after every phase.
Integration into main is reserved for the final
reviewed project version.

## 15. Conclusion

AirScope demonstrates an end-to-end workflow for
official environmental data ingestion, reproducible
ML forecasting, quantitative evaluation and
interactive web visualization.

Its central strength is not merely displaying
predictions, but making the supporting data,
benchmarks, limitations and evaluation methods
visible to users.

---

AirScope | nik
