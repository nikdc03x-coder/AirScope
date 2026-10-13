# AirScope | Model Evaluation Report

**Project:** AirScope — Urban PM2.5 Intelligence and Forecasting  
**Evaluation:** Berlin hourly PM2.5 forecasting  
**Model:** Histogram-based Gradient Boosting Regressor  
**Forecast horizons:** 6, 12 and 24 hours  
**Data sources:** Umweltbundesamt (UBA), DEFRA UK-AIR  
**Status:** Experimental research prototype

---

## 1. Research objective

AirScope investigates whether machine-learning models can
predict future PM2.5 concentrations more accurately than
a simple persistence baseline.

The project uses genuine air-quality observations from
monitoring stations in Berlin and London.

The current independent forecasting evaluation covers
Berlin only. London observations are available for
historical analysis, but validated London forecasting
results are not yet available.

## 2. Data sources

### Berlin, Germany

- Official source: Umweltbundesamt (UBA)
- Pollutant: PM2.5
- Observation frequency: Hourly
- Monitoring stations: 12
- Data interval: January 2025 to October 2026
- Values are derived from official station observations.
- Source gaps and missing concentrations are retained.

### London, United Kingdom

- Official source: DEFRA UK-AIR
- Monitoring station: London Bloomsbury (CLL2)
- Pollutant: PM2.5
- Observation frequency: Hourly
- Source quality labels are preserved.
- Ratified observations are eligible for the strict
  model-development dataset.

London was not included in independent forecasting
evaluation because the strict eligibility rules left
no suitable validation or test examples.

## 3. Data preparation

Berlin and London datasets were standardized using
UTC timestamps.

The unified dataset contains:

- 198,900 station-hour records
- 13 monitoring stations
- No duplicate station-hour combinations

Forecast features were constructed using exact
timestamps rather than row positions.

Historical PM2.5 features:

- Current PM2.5
- 1-hour lag
- 3-hour lag
- 6-hour lag
- 12-hour lag
- 24-hour lag

Additional features:

- Cyclical time-related variables
- Monitoring station identifiers

Targets correspond to PM2.5 observations exactly
6, 12 or 24 hours after the forecast origin.

No missing hourly observations were fabricated.
Training examples requiring unavailable lag or
target measurements were excluded.

## 4. Chronological data splitting

The dataset was split chronologically to simulate
forecasting on observations collected after training.

| Partition  | Time interval         |
| ---------- | --------------------- |
| Training   | Before 1 July 2026    |
| Validation | July–August 2026      |
| Test       | September 2026 onward |

Forecast feature construction respected partition
boundaries.

The test set was reserved for final independent
evaluation rather than repeated model tuning.

This approach avoids random mixing of earlier and
later observations.

## 5. Forecasting approaches

### 5.1 Persistence baseline

The persistence baseline assumes the current PM2.5
concentration remains unchanged at the forecast
target time.

Persistence prediction:

    PM2.5(t + h) = PM2.5(t)

where h is the forecast horizon.

This is a simple but meaningful benchmark for
short-term air-quality forecasting.

### 5.2 Machine-learning model

AirScope uses scikit-learn's
HistGradientBoostingRegressor.

Separate models are trained for:

- 6-hour forecasting
- 12-hour forecasting
- 24-hour forecasting

Model artifacts are stored locally and served
through the project's FastAPI backend.

## 6. Evaluation metrics

### Mean Absolute Error (MAE)

MAE measures the average absolute difference between
predicted and observed PM2.5 concentrations.

Lower MAE indicates better typical prediction accuracy.

### Root Mean Squared Error (RMSE)

RMSE gives greater weight to large prediction errors.

Lower RMSE indicates fewer or smaller severe errors.

Both metrics are expressed in µg/m³.

## 7. Independent Berlin test results

| Horizon | Samples | Baseline MAE | ML MAE | Baseline RMSE | ML RMSE |
| ------- | ------: | -----------: | -----: | ------------: | ------: |
| 6 h     |   9,404 |       0.9696 | 0.9292 |        2.3693 |  2.6415 |
| 12 h    |   9,176 |       1.8102 | 1.6712 |        4.3221 |  3.9935 |
| 24 h    |   8,736 |       3.1725 | 2.9142 |        7.2063 |  5.9941 |

### MAE improvement over persistence

| Forecast horizon | Improvement |
| ---------------- | ----------: |
| 6 hours          |       4.16% |
| 12 hours         |       7.67% |
| 24 hours         |       8.14% |

The machine-learning models improved test-set MAE
at all three forecasting horizons.

For the 12-hour and 24-hour horizons, the ML models
also reduced RMSE.

However, the 6-hour ML model had a higher RMSE
than the persistence baseline.

Therefore, the ML models should not be described
as uniformly better across all evaluation metrics.

## 8. Validation observations

Recorded validation MAE results:

| Horizon | Persistence MAE | ML MAE |
| ------- | --------------: | -----: |
| 6 h     |          0.6236 | 0.6287 |
| 12 h    |          1.1411 | 1.0708 |
| 24 h    |          1.9718 | 1.8182 |

The 6-hour ML model did not outperform persistence
on validation MAE.

The 12-hour and 24-hour models improved validation MAE.

These results show that improvements depend on
the forecast horizon and evaluation period.

## 9. Extreme-event error analysis

A notable localized PM2.5 episode was identified
at Berlin Frankfurter Allee (DEBE065) during
26–27 September 2026.

Recorded observations included:

- Peak station PM2.5: approximately 127 µg/m³
- Approximate peer-station median: 11 µg/m³
- 32 spatially flagged hours from the anomaly audit

The event was concentrated at one monitoring station.

The 6-hour ML model struggled with some high-pollution
observations, contributing to its worse RMSE compared
with persistence.

These observations were preserved rather than
removed from the test data.

The evidence establishes an unusual localized
measurement pattern, but it does not independently
establish the physical cause of the episode.

## 10. Limitations

### 10.1 Geographic coverage

Berlin forecasting is evaluated across 12 stations,
but the results do not necessarily generalize to
other cities.

### 10.2 London forecasting

London does not yet have independently evaluated
forecasting models under the current strict
quality and chronological-split requirements.

### 10.3 Extreme pollution events

Large localized pollution episodes can produce
substantial prediction errors.

Model performance under extreme conditions remains
an important research limitation.

### 10.4 Predictor coverage

The current forecasting models rely on PM2.5 history,
time features and station identity.

They do not yet incorporate external meteorological
forecasts, traffic activity or other explanatory data.

### 10.5 Historical-data snapshots

The currently deployed API produces experimental
predictions from stored observations.

It is not a live operational forecasting service.

### 10.6 Generalization

The project has one primary chronological test period.
Independent tests across additional future periods
would be needed to establish stronger evidence
of generalization.

## 11. Future improvements

Potential next research steps include:

1. Rolling-origin evaluation over multiple periods.
2. Quantifying error separately during high-PM2.5 events.
3. Comparing additional model architectures.
4. Integrating verified meteorological predictors.
5. Measuring station-specific forecast performance.
6. Developing an independently evaluated London model.
7. Adding uncertainty estimates for forecasts.

Each improvement would require separate validation
before being presented as a demonstrated result.

## 12. Conclusion

AirScope demonstrates an end-to-end forecasting
workflow using official environmental observations,
chronological data preparation, baseline comparisons,
machine-learning models and a web application.

The Berlin models improve typical forecasting accuracy
over persistence on the independent test set,
particularly at 12- and 24-hour horizons.

However, the 6-hour model exhibits worse RMSE,
and localized high-pollution events remain difficult
to predict.

The project therefore reports both improvements
and limitations rather than claiming consistently
superior model performance.

---

**AirScope | nik**

Research-oriented environmental data and
machine-learning engineering project.
