# AirScope

### Explainable PM2.5 Forecasting and Air-Quality Intelligence

AirScope is a research-oriented full-stack application for exploring historical air-quality observations, evaluating machine-learning forecasts, and comparing monitoring stations across European cities.

The project combines official environmental data from Berlin and London with a reproducible forecasting pipeline, a FastAPI backend, and an interactive React dashboard.

**Project status:** Experimental research prototype  
**Cities:** Berlin, Germany · London, United Kingdom  
**Pollutant:** PM2.5  
**Languages:** English and German

> AirScope is not an official air-quality monitoring or warning service. Its displayed observations and forecasts are based on stored data and should not be interpreted as live measurements.

---

## 1. Project Overview

AirScope aims to make air-quality forecasting more transparent by connecting historical environmental measurements with machine-learning predictions and quantitative performance evaluation.

Instead of simply presenting a predicted PM2.5 value, the project also provides:

- The historical data underlying the application
- Source attribution and observation quality information
- Comparisons with a simple persistence baseline
- Forecast errors at multiple prediction horizons
- Station-level model performance
- Clearly documented limitations

### Research questions

1. Can gradient-boosting models outperform persistence forecasting for short-term PM2.5 prediction?
2. How does predictive accuracy change at 6-, 12-, and 24-hour horizons?
3. Does forecasting performance vary between monitoring stations?
4. How do localized pollution episodes influence evaluation metrics?
5. How can scientific uncertainty and data freshness be communicated clearly through a web application?

---

## 2. Core Features

### Berlin Air-Quality Dashboard

- Historical hourly PM2.5 observations
- Twelve official Berlin monitoring stations
- Selectable monitoring station
- Experimental 6h, 12h, and 24h ML forecasts
- Historical observation charts
- Source and data freshness information

### London Air-Quality Dashboard

- Historical PM2.5 observations from London Bloomsbury
- Official DEFRA UK-AIR data
- Observation quality information
- Data freshness indicators
- Explicit disclosure that validated London ML forecasts are not yet available

### Berlin–London Comparison

- Historical PM2.5 comparison
- Berlin Wedding versus London Bloomsbury
- Daily aggregation of station measurements
- Selectable observation windows

The comparison represents two monitoring locations, not complete citywide air-quality exposure.

### Scientific Evaluation Dashboard

- Persistence baseline versus ML forecasting
- Mean Absolute Error (MAE)
- Root Mean Squared Error (RMSE)
- Forecasting performance by horizon
- Station-level MAE comparison
- Model limitations and research disclosures

---

## 3. Technology Stack

| Layer                | Technologies            |
| -------------------- | ----------------------- |
| Frontend             | React, TypeScript, Vite |
| UI                   | Material UI             |
| Visualization        | Recharts                |
| Internationalization | react-i18next           |
| Backend              | Python, FastAPI         |
| Data analysis        | pandas, NumPy           |
| Machine learning     | scikit-learn            |
| Data storage         | Parquet                 |
| Model artifacts      | joblib                  |
| Version control      | Git and GitHub          |

---

## 4. System Architecture

    Official Data Sources
              |
       +------+------+
       |             |
     UBA          DEFRA
    Berlin        London
       |             |
       +------+------+
              |
       Data Ingestion
              |
       Data Validation
              |
        Parquet Files
              |
       +------+------+
       |             |
    Historical     Feature
      Data       Engineering
       |             |
       |         ML Training
       |             |
       |         Evaluation
       |             |
       +------+------+
              |
         FastAPI
              |
         HTTP / JSON
              |
       React Frontend
              |
    Interactive Dashboard

Additional architecture details are documented in:

`docs/architecture/system_architecture.md`

---

## 5. Official Data Sources

### Berlin, Germany

**Provider:** Umweltbundesamt (UBA)

Official website:

https://www.umweltbundesamt.de/en

Air-quality data portal:

https://www.umweltbundesamt.de/en/data/air/air-data

The Berlin dataset includes hourly PM2.5 observations from twelve monitoring stations.

Missing observations are preserved instead of being silently replaced.

### London, United Kingdom

**Provider:** UK Department for Environment, Food & Rural Affairs (DEFRA)

Official UK-AIR website:

https://uk-air.defra.gov.uk/

The London dataset uses the Bloomsbury monitoring station (CLL2).

Source quality classifications are retained so that ratified and provisional observations can be distinguished.

### Important data note

AirScope works with locally stored datasets.

Opening the dashboard does not automatically request current official monitoring data.

---

## 6. Dataset Preparation

The project processes original environmental observations into standardized datasets.

### Berlin

`data/processed/berlin_pm25_hourly.parquet`

- Twelve monitoring stations
- Hourly PM2.5 observations
- UTC timestamps
- Missing observations retained

### London

`data/processed/london_pm25_final.parquet`

- London Bloomsbury station
- Hourly PM2.5 observations
- UTC timestamps
- Source quality classifications retained

### Forecast feature dataset

`data/processed/airscope_forecast_features.parquet`

The forecasting dataset contains lagged PM2.5 inputs, timestamps, station identifiers, target values, and chronological partition metadata.

---

## 7. Machine-Learning Approach

### Model

AirScope uses scikit-learn's:

`HistGradientBoostingRegressor`

Three separate Berlin models are trained for:

- 6-hour-ahead forecasts
- 12-hour-ahead forecasts
- 24-hour-ahead forecasts

### Feature engineering

The model uses:

**Pollution history**

- Current PM2.5
- PM2.5 lagged by 1 hour
- PM2.5 lagged by 3 hours
- PM2.5 lagged by 6 hours
- PM2.5 lagged by 12 hours
- PM2.5 lagged by 24 hours

**Time features**

- Hour-of-day sine and cosine
- Day-of-week sine and cosine
- Annual-cycle sine and cosine

**Station information**

- One-hot encoded Berlin monitoring station identifiers

### Persistence baseline

The baseline assumes that the current PM2.5 concentration remains unchanged at the forecast target time.

This provides a simple but meaningful comparison for the ML models.

### Temporal evaluation

The data is divided chronologically into training, validation, and test partitions.

This prevents the evaluation from treating future measurements as if they were already known during training.

---

## 8. Verified Berlin Model Results

The following results were recorded on the chronological Berlin test partition.

### Mean Absolute Error

| Horizon | Test samples | Persistence MAE | ML MAE | Relative MAE improvement |
| ------- | -----------: | --------------: | -----: | -----------------------: |
| 6h      |        9,404 |          0.9696 | 0.9292 |                    4.17% |
| 12h     |        9,176 |          1.8102 | 1.6712 |                    7.68% |
| 24h     |        8,736 |          3.1725 | 2.9142 |                    8.13% |

### Root Mean Squared Error

| Horizon | Persistence RMSE | ML RMSE |
| ------- | ---------------: | ------: |
| 6h      |           2.3693 |  2.6415 |
| 12h     |           4.3221 |  3.9935 |
| 24h     |           7.2063 |  5.9941 |

**Units:** µg/m³

### Interpretation

The ML models improved overall test MAE at all three horizons.

However, the 6-hour model produced a higher RMSE than the persistence baseline, suggesting that some relatively large forecasting errors remain an important limitation.

These results should not be interpreted as a guarantee of future performance.

---

## 9. Station-Level Evaluation

AirScope includes independent station-level error summaries for all twelve Berlin monitoring stations.

Each station is evaluated at three forecasting horizons, producing 36 station-horizon result groups.

Metrics include:

- Test sample count
- Model MAE
- Baseline MAE
- Model RMSE
- Baseline RMSE
- Relative MAE improvement
- Prediction bias

An unusual localized PM2.5 episode at Frankfurter Allee illustrates the difficulty of forecasting extreme pollution events.

The cause of the episode has not been established by the project.

---

## 10. ## Application Screenshots

The following screenshots show AirScope running locally with
stored official PM2.5 observations and experimental Berlin forecasts.

### Berlin Dashboard

![Berlin dashboard](docs/screenshots/01-berlin-dashboard.png)

### Berlin Historical Observations

![Berlin PM2.5 history](docs/screenshots/02-berlin-history.png)

### London Dashboard

![London Bloomsbury observations](docs/screenshots/03-london-dashboard.png)

### Berlin–London Comparison

![Historical station comparison](docs/screenshots/04-city-comparison.png)

### Scientific Model Evaluation

![Berlin model evaluation](docs/screenshots/05-model-evaluation.png)

### Mobile Dashboard

## ![Responsive mobile interface](docs/screenshots/06-mobile-dashboard.png)

## 11. Local Installation

### Prerequisites

- Python
- Node.js and npm
- Git

Use compatible versions defined by the project's dependency files.

### Clone the repository

Replace the placeholder URL with the actual public repository URL:

    git clone <YOUR_REPOSITORY_URL>
    cd airscope

### Create a Python virtual environment

Windows Git Bash:

    python -m venv .venv
    source .venv/Scripts/activate

### Install Python dependencies

If the repository contains `requirements.txt`:

    pip install -r requirements.txt

Otherwise, follow the project's documented Python environment configuration.

### Start the backend

From the project root:

    python -m uvicorn backend.app.main:app --reload

Backend:

http://127.0.0.1:8000

Interactive API documentation:

http://127.0.0.1:8000/docs

### Start the frontend

Open another terminal:

    cd frontend
    npm install
    npm run dev

Frontend:

http://localhost:5173

### Required local artifacts

Some endpoints depend on processed Parquet datasets and trained model artifacts.

Ensure these files are present or generated through the project's data and ML pipeline before running the complete application.

The README does not assume that large data files or trained models are automatically included in every clone.

---

## 12. Validation

### Frontend

From `frontend/`:

    npm run lint
    npm run build

### Scientific evaluation

From the repository root:

    python -m scripts.verify_phase05

### Backend end-to-end validation

From the repository root:

    python -m scripts.verify_end_to_end

These checks require the appropriate Python dependencies, processed datasets, and trusted model artifacts.

---

## 13. API Overview

| Endpoint                                   | Description                    |
| ------------------------------------------ | ------------------------------ |
| `/api/v1/health`                           | Backend health                 |
| `/api/v1/stations`                         | Berlin monitoring stations     |
| `/api/v1/forecasts/berlin/{station_id}`    | Berlin ML forecasts            |
| `/api/v1/observations/berlin/{station_id}` | Berlin historical observations |
| `/api/v1/observations/london/{station_id}` | London historical observations |
| `/api/v1/evaluation/berlin/stations`       | Station-level evaluation       |

The documented API is served locally by FastAPI.

---

## 14. Scientific Limitations

AirScope has several important limitations:

1. Forecasts use stored historical observations rather than live monitoring feeds.
2. Evaluated ML forecasting is currently available only for Berlin.
3. London observations may include provisional measurements that require careful interpretation.
4. Forecasting performance varies between monitoring stations.
5. Extreme local pollution episodes can produce substantial errors.
6. The current forecasting models do not incorporate future meteorological forecasts.
7. Comparing individual stations does not establish citywide exposure differences.
8. Additional independent temporal evaluations are required before operational deployment.

AirScope is intended for research, education, and demonstration rather than public-health decision-making.

---

## 15. Future Improvements

Potential directions include:

- Rolling-origin forecasting evaluation
- Weather-based explanatory variables
- Prediction uncertainty estimates
- Additional European monitoring stations
- Cross-city transfer-learning experiments
- Automated data ingestion
- Reproducible model retraining pipelines
- Stronger forecasting baselines
- Model explainability analysis
- Deployment and continuous integration

These are research opportunities, not implemented features.

---

## 16. Development Process

The project was developed incrementally using phase-specific Git branches and meaningful commits.

Major development stages include:

1. Frontend foundation
2. Environmental data ingestion
3. ML feature engineering and model training
4. API integration
5. Scientific evaluation
6. Usability and transparency
7. Final validation and portfolio preparation

The Git history provides a record of this development process.

---

## 17. Author

**AirScope | nik**

Research-oriented AI/ML and software engineering portfolio project.

---

## 18. Acknowledgements

Environmental observations originate from official data providers:

- Umweltbundesamt (Germany)
- DEFRA UK-AIR (United Kingdom)

The project is an independent research prototype and is not affiliated with or endorsed by either provider.

Application
