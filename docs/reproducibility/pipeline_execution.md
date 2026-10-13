# AirScope — Pipeline Execution Guide

> Generated inventory. Commands are candidates,
> not yet verified regeneration instructions.

## Intended pipeline

1. Ingest official Berlin UBA observations.
2. Ingest official London DEFRA observations.
3. Validate and normalize timestamps.
4. Create chronological forecasting features.
5. Train Berlin 6h, 12h and 24h models.
6. Evaluate models against persistence.
7. Generate station-level evaluation reports.
8. Serve stored results through FastAPI.

## Discovered Python entry points

| Script | Candidate command |
|---|---|
| `ml/baselines/persistence.py` | `python -m ml.baselines.persistence` |
| `ml/evaluation/analyze_berlin.py` | `python -m ml.evaluation.analyze_berlin` |
| `ml/evaluation/evaluate_stations.py` | `python -m ml.evaluation.evaluate_stations` |
| `ml/evaluation/inspect_artifacts.py` | `python -m ml.evaluation.inspect_artifacts` |
| `ml/evaluation/investigate_berlin_spike.py` | `python -m ml.evaluation.investigate_berlin_spike` |
| `ml/features/build_forecast_features.py` | `python -m ml.features.build_forecast_features` |
| `ml/ingestion/defra.py` | `python -m ml.ingestion.defra` |
| `ml/ingestion/defra_client.py` | `python -m ml.ingestion.defra_client` |
| `ml/ingestion/defra_csv.py` | `python -m ml.ingestion.defra_csv` |
| `ml/ingestion/defra_observations.py` | `python -m ml.ingestion.defra_observations` |
| `ml/ingestion/download_berlin_pm25.py` | `python -m ml.ingestion.download_berlin_pm25` |
| `ml/ingestion/london_pm25.py` | `python -m ml.ingestion.london_pm25` |
| `ml/ingestion/london_stations.py` | `python -m ml.ingestion.london_stations` |
| `ml/ingestion/normalize_defra.py` | `python -m ml.ingestion.normalize_defra` |
| `ml/ingestion/station_locations.py` | `python -m ml.ingestion.station_locations` |
| `ml/ingestion/station_registry.py` | `python -m ml.ingestion.station_registry` |
| `ml/ingestion/uba_stations.py` | `python -m ml.ingestion.uba_stations` |
| `ml/ingestion/verify_berlin_pm25.py` | `python -m ml.ingestion.verify_berlin_pm25` |
| `ml/preprocessing/build_unified_dataset.py` | `python -m ml.preprocessing.build_unified_dataset` |
| `ml/training/train_berlin.py` | `python -m ml.training.train_berlin` |
| `ml/validation/audit_berlin.py` | `python -m ml.validation.audit_berlin` |
| `ml/validation/audit_london.py` | `python -m ml.validation.audit_london` |
| `ml/validation/audit_spatial_anomalies.py` | `python -m ml.validation.audit_spatial_anomalies` |
| `ml/validation/check_berlin_raw_gaps.py` | `python -m ml.validation.check_berlin_raw_gaps` |
| `ml/validation/finalize_berlin.py` | `python -m ml.validation.finalize_berlin` |
| `ml/validation/finalize_london.py` | `python -m ml.validation.finalize_london` |
| `ml/validation/inspect_berlin_gaps.py` | `python -m ml.validation.inspect_berlin_gaps` |
| `ml/validation/probe_berlin_gaps.py` | `python -m ml.validation.probe_berlin_gaps` |
| `scripts/audit_reproducibility.py` | `python -m scripts.audit_reproducibility` |
| `scripts/check_defra_identifiers.py` | `python -m scripts.check_defra_identifiers` |
| `scripts/find_pm25_offerings.py` | `python -m scripts.find_pm25_offerings` |
| `scripts/generate_pipeline_guide.py` | `python -m scripts.generate_pipeline_guide` |
| `scripts/generate_requirements.py` | `python -m scripts.generate_requirements` |
| `scripts/inspect_defra_xml.py` | `python -m scripts.inspect_defra_xml` |
| `scripts/inspect_dependencies.py` | `python -m scripts.inspect_dependencies` |
| `scripts/inspect_pipeline.py` | `python -m scripts.inspect_pipeline` |
| `scripts/inspect_sources.py` | `python -m scripts.inspect_sources` |
| `scripts/run_ingestion.py` | `python -m scripts.run_ingestion` |
| `scripts/test_api.py` | `python -m scripts.test_api` |
| `scripts/verify_end_to_end.py` | `python -m scripts.verify_end_to_end` |
| `scripts/verify_phase05.py` | `python -m scripts.verify_phase05` |

## Referenced data and model files

### `ml/baselines/persistence.py`

- `airscope_forecast_features.parquet`
- `persistence_metrics.csv`
- `persistence_predictions.parquet`

### `ml/evaluation/analyze_berlin.py`

- `berlin_ml_predictions.parquet`
- `berlin_pollution_metrics.csv`
- `berlin_station_metrics.csv`
- `berlin_worst_errors.csv`

### `ml/evaluation/evaluate_stations.py`

- `airscope_forecast_features.parquet`
- `berlin_station_evaluation.csv`
- `berlin_station_evaluation_summary.json`
- `h.joblib`

### `ml/evaluation/inspect_artifacts.py`

- `airscope_forecast_features.parquet`
- `h.joblib`

### `ml/evaluation/investigate_berlin_spike.py`

- `berlin_ml_predictions.parquet`
- `berlin_pm25_hourly.parquet`
- `berlin_spike_hourly_comparison.csv`
- `berlin_spike_prediction_errors.csv`
- `berlin_spike_station_summary.csv`

### `ml/features/build_forecast_features.py`

- `airscope_forecast_features.parquet`
- `airscope_pm25_unified.parquet`

### `ml/ingestion/defra.py`

- `defra_pm25_offerings.json`

### `ml/ingestion/defra_csv.py`

- `.csv`

### `ml/ingestion/defra_observations.py`

- `data/processed/london_pm25_stations.csv`

### `ml/ingestion/download_berlin_pm25.py`

- `.json`
- `berlin_pm25_hourly.parquet`
- `berlin_pm25_stations.csv`

### `ml/ingestion/london_pm25.py`

- `data/processed/defra_pm25_registry.csv`
- `data/processed/defra_station_locations.csv`
- `data/processed/london_pm25_stations.csv`

### `ml/ingestion/london_stations.py`

- `defra_london_candidates.json`

### `ml/ingestion/normalize_defra.py`

- `.csv`
- `london_pm25_hourly.parquet`

### `ml/ingestion/station_locations.py`

- `data/processed/defra_station_locations.csv`

### `ml/ingestion/station_registry.py`

- `defra_pm25_registry.csv`

### `ml/ingestion/uba_stations.py`

- `uba_station_discovery.json`
- `uba_stations_2025_2026.json`

### `ml/ingestion/verify_berlin_pm25.py`

- `berlin_pm25_probe.json`
- `berlin_pm25_stations.csv`
- `uba_stations_2025_2026.json`

### `ml/preprocessing/build_unified_dataset.py`

- `airscope_dataset_summary.json`
- `airscope_pm25_unified.parquet`
- `berlin_pm25_hourly.parquet`
- `london_pm25_final.parquet`

### `ml/training/train_berlin.py`

- `airscope_forecast_features.parquet`
- `berlin_ml_metrics.csv`
- `berlin_ml_predictions.parquet`
- `h.joblib`

### `ml/validation/audit_berlin.py`

- `berlin_pm25_hourly.parquet`
- `berlin_pm25_stations.csv`
- `berlin_quality_report.csv`

### `ml/validation/audit_london.py`

- `.csv`
- `london_pm25_hourly.parquet`
- `london_quality_report.json`

### `ml/validation/audit_spatial_anomalies.py`

- `_20260901_20260930.json`
- `berlin_pm25_hourly.parquet`
- `berlin_spatial_anomalies.csv`
- `berlin_spike_source_check.csv`

### `ml/validation/check_berlin_raw_gaps.py`

- `*.json`
- `data/processed/berlin_pm25_hourly.parquet`

### `ml/validation/finalize_berlin.py`

- `_*.json`
- `data/processed/berlin_final_quality.csv`
- `data/processed/berlin_final_summary.json`
- `data/processed/berlin_pm25_hourly.parquet`
- `data/processed/berlin_pm25_stations.csv`

### `ml/validation/finalize_london.py`

- `london_pm25_final.parquet`
- `london_pm25_hourly.parquet`

### `ml/validation/inspect_berlin_gaps.py`

- `data/processed/berlin_missing_gaps.csv`
- `data/processed/berlin_pm25_hourly.parquet`

### `ml/validation/probe_berlin_gaps.py`

- `.json`

### `scripts/audit_reproducibility.py`

- `data/processed/airscope_forecast_features.parquet`
- `data/processed/berlin_pm25_hourly.parquet`
- `data/processed/berlin_station_evaluation.csv`
- `data/processed/london_pm25_final.parquet`
- `frontend/package-lock.json`
- `frontend/package.json`
- `models/berlin_pm25_hgb_12h.joblib`
- `models/berlin_pm25_hgb_24h.joblib`
- `models/berlin_pm25_hgb_6h.joblib`

### `scripts/find_pm25_offerings.py`

- `defra_pm25_offerings.json`

### `scripts/generate_pipeline_guide.py`

- `.csv`
- `.joblib`
- `.json`
- `.parquet`

### `scripts/inspect_pipeline.py`

- `.csv`
- `.joblib`
- `.json`
- `.parquet`

### `scripts/inspect_sources.py`

- `uba_components.json`

### `scripts/run_ingestion.py`

- `source_check.json`
- `uba_components.json`

### `scripts/verify_phase05.py`

- `berlin_station_evaluation.csv`
- `berlin_station_evaluation_summary.json`
- `h.joblib`

## Verification commands

These commands validate existing local artifacts:

```bash
python -m scripts.verify_phase05
python -m scripts.verify_end_to_end
```

## Safety and reproducibility notes

- Do not execute ingestion or training scripts
  before reviewing their input and output paths.
- Some scripts may overwrite existing artifacts.
- Official source data may change over time.
- Model results may differ if source snapshots
  or dependency versions change.
- A main block does not guarantee a module
  can be executed successfully.

## Manual verification still required

For each pipeline stage, confirm:

- Exact command-line arguments
- Required input files
- Expected output files
- Whether existing files are overwritten
- Expected data schema
- Network requirements
- Model evaluation consistency

---

AirScope | nik
