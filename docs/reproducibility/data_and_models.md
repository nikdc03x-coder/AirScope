# AirScope — Data and Model Reproducibility

## Purpose

AirScope uses official historical PM2.5 observations
and locally trained machine-learning models.

Some generated artifacts are intentionally excluded
from Git version control.

Consequently, cloning the repository does not
necessarily provide a fully populated data directory
or ready-to-use forecasting models.

## Official sources

### Berlin

Provider: Umweltbundesamt (UBA), Germany.

Data: Hourly PM2.5 observations from twelve
Berlin monitoring stations.

Official source:
https://www.umweltbundesamt.de/en/data/air/air-data

### London

Provider: DEFRA UK-AIR, United Kingdom.

Data: Hourly PM2.5 observations from
London Bloomsbury, station CLL2.

Official source:
https://uk-air.defra.gov.uk/

## Locally generated datasets

| File                                                    | Purpose                                |
| ------------------------------------------------------- | -------------------------------------- |
| `data/processed/berlin_pm25_hourly.parquet`             | Berlin hourly observations             |
| `data/processed/london_pm25_final.parquet`              | London hourly observations             |
| `data/processed/airscope_forecast_features.parquet`     | Model training and evaluation examples |
| `data/processed/berlin_station_evaluation.csv`          | Station-level evaluation metrics       |
| `data/processed/berlin_station_evaluation_summary.json` | Evaluation summary                     |

These files may be unavailable in a fresh clone.

## Trained model artifacts

The forecasting application expects:

- `models/berlin_pm25_hgb_6h.joblib`
- `models/berlin_pm25_hgb_12h.joblib`
- `models/berlin_pm25_hgb_24h.joblib`

The files contain trusted locally trained
scikit-learn models and model metadata.

Only load model artifacts from trusted sources.
Joblib files should not be loaded from arbitrary
third-party downloads.

## Evaluation

AirScope evaluates Berlin forecasting models using:

- Chronological training, validation and test partitions
- A persistence forecasting baseline
- Mean Absolute Error (MAE)
- Root Mean Squared Error (RMSE)
- Station-level performance analysis

Existing verification commands:

    python -m scripts.verify_phase05
    python -m scripts.verify_end_to_end

These commands require relevant datasets and models
to be available locally.

## Fresh-clone limitation

A fresh Git clone may require the original official
observations to be retrieved and the preprocessing,
feature engineering and model training pipelines
to be executed.

The exact regeneration commands must be verified
against the repository's current scripts before
they are published as reproducible instructions.

Until that verification is complete, the project
should not claim that its entire data and model
pipeline can be reproduced with a single command.

## Future reproducibility improvements

- Document verified ingestion commands
- Document feature engineering commands
- Document model training commands
- Record original source date ranges
- Check generated data schemas
- Verify that regenerated models can be evaluated
- Consider checksums for distributed artifacts

---

AirScope | nik
