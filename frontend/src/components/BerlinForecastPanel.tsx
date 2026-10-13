
/**
 * AirScope | nik
 * Berlin PM2.5 forecasting dashboard.
 *
 * Loads stations and experimental forecasts from FastAPI.
 * Reuses StationHistoryChart for historical observations.
 * All data comes from official stored measurements.
 */

import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";

import {
  Alert,
  Box,
  Card,
  CardContent,
  Chip,
  CircularProgress,
  FormControl,
  InputLabel,
  MenuItem,
  Select,
  Stack,
  Typography,
} from "@mui/material";

import StationHistoryChart from "./StationHistoryChart";

// Berlin station information from the backend.
type Station = {
  station_id: string;
  station_name: string;
  latitude: number;
  longitude: number;
  latest_observation_utc: string;
};

// One forecast from a trained ML model.
type Prediction = {
  horizon_hours: number;
  target_timestamp_utc: string;
  predicted_pm25_ugm3: number;
};

// Complete FastAPI forecast response.
type Forecast = {
  city: string;
  station_id: string;
  station_name: string;
  model: string;
  forecast_origin_utc: string;
  latest_stored_observation_utc: string;
  current_pm25_ugm3: number;
  unit: string;
  forecast_type: string;
  is_live: boolean;
  predictions: Prediction[];
  disclaimer: string;
};

const API_BASE = "http://127.0.0.1:8000/api/v1";

// Display all stored timestamps in UTC.
function formatDate(value: string, german: boolean) {
  const formatted = new Intl.DateTimeFormat(
    german ? "de-DE" : "en-GB",
    {
      dateStyle: "medium",
      timeStyle: "short",
      timeZone: "UTC",
    }
  ).format(new Date(value));

  return `${formatted} UTC`;
}

export default function BerlinForecastPanel() {
  const { i18n } = useTranslation();
  const german = i18n.language.startsWith("de");

  // Keep the panel bilingual without changing existing i18n files.
  const labels = german
    ? {
        title: "Berlin – PM2,5-Prognosen",
        subtitle:
          "Experimentelle Vorhersagen auf Basis offizieller Messdaten",
        station: "Messstation auswählen",
        reading: "PM2,5 zum Prognosezeitpunkt",
        origin: "Prognosezeitpunkt",
        latest: "Letzte gespeicherte Messung",
        forecast: "Vorhersage für",
        hours: "Stunden",
        loadingStations: "Messstationen werden geladen...",
        loadingForecasts: "Prognosen werden geladen...",
        stationError: "Messstationen konnten nicht geladen werden.",
        forecastError: "Prognosen konnten nicht geladen werden.",
        historical: "Historische Daten · Nicht live",
        disclaimer:
          "Die Prognosen sind experimentell und verwenden gespeicherte Messdaten. Sie sind keine Live-Luftqualitätswarnungen.",
        unit: "µg/m³",
      }
    : {
        title: "Berlin PM2.5 Forecasts",
        subtitle:
          "Experimental predictions based on official observations",
        station: "Select monitoring station",
        reading: "PM2.5 at forecast origin",
        origin: "Forecast origin",
        latest: "Latest stored observation",
        forecast: "Forecast for",
        hours: "hours",
        loadingStations: "Loading monitoring stations...",
        loadingForecasts: "Loading forecasts...",
        stationError: "Unable to load monitoring stations.",
        forecastError: "Unable to load forecasts.",
        historical: "Historical data · Not live",
        disclaimer:
          "These experimental forecasts use stored observations. They are not live air-quality warnings.",
        unit: "µg/m³",
      };

  // State shared by the station selector, forecasts and history chart.
  const [stations, setStations] = useState<Station[]>([]);
  const [stationId, setStationId] = useState("DEBE010");
  const [forecast, setForecast] = useState<Forecast | null>(null);

  const [stationsLoading, setStationsLoading] = useState(true);
  const [forecastLoading, setForecastLoading] = useState(false);

  const [stationsError, setStationsError] = useState("");
  const [forecastError, setForecastError] = useState("");

  // Fetch official Berlin station metadata once.
  useEffect(() => {
    const controller = new AbortController();

    async function loadStations() {
      try {
        const response = await fetch(`${API_BASE}/stations`, {
          signal: controller.signal,
        });

        if (!response.ok) {
          throw new Error(`HTTP ${response.status}`);
        }

        const data: { stations: Station[] } =
          await response.json();

        if (!Array.isArray(data.stations)) {
          throw new Error("Invalid station response");
        }

        setStations(data.stations);

        // Prefer Berlin Wedding if it exists in the registry.
        if (data.stations.length > 0) {
          const preferred = data.stations.find(
            (station) => station.station_id === "DEBE010"
          );

          setStationId(
            preferred?.station_id ?? data.stations[0].station_id
          );
        }
      } catch (error) {
        if (controller.signal.aborted) return;

        setStationsError(
          error instanceof Error ? error.message : "Unknown error"
        );
      } finally {
        if (!controller.signal.aborted) {
          setStationsLoading(false);
        }
      }
    }

    void loadStations();

    return () => controller.abort();
  }, []);

  // Fetch new forecasts when the monitoring station changes.
  useEffect(() => {
    // Do not request forecasts until station metadata is loaded.
    if (stationsLoading || stations.length === 0) return;

    const controller = new AbortController();

    async function loadForecast() {
      setForecastLoading(true);
      setForecast(null);
      setForecastError("");

      try {
        const url =
          `${API_BASE}/forecasts/berlin/` +
          encodeURIComponent(stationId);

        const response = await fetch(url, {
          signal: controller.signal,
        });

        if (!response.ok) {
          throw new Error(`HTTP ${response.status}`);
        }

        const data: Forecast = await response.json();

        // Reject unexpected responses rather than showing wrong data.
        if (
          data.station_id !== stationId ||
          !Array.isArray(data.predictions) ||
          data.is_live !== false
        ) {
          throw new Error("Invalid forecast response");
        }

        setForecast(data);
      } catch (error) {
        if (controller.signal.aborted) return;

        setForecastError(
          error instanceof Error ? error.message : "Unknown error"
        );
      } finally {
        if (!controller.signal.aborted) {
          setForecastLoading(false);
        }
      }
    }

    void loadForecast();

    return () => controller.abort();
  }, [stationId, stationsLoading, stations.length]);

  return (
    <Box sx={{ py: 3 }}>
      <Stack spacing={3}>
        {/* Forecast section heading */}
        <Box>
          <Typography
            variant="h4"
            component="h2"
            gutterBottom
            sx={{ fontWeight: 700 }}
          >
            {labels.title}
          </Typography>

          <Typography color="text.secondary">
            {labels.subtitle}
          </Typography>
        </Box>

        {/* Make it clear the predictions are not live. */}
        <Alert severity="info">
          {labels.disclaimer}
        </Alert>

        {/* Report station-loading problems. */}
        {stationsError && (
          <Alert severity="error">
            {labels.stationError} ({stationsError})
          </Alert>
        )}

        {/* Berlin station selection */}
        <FormControl fullWidth sx={{ maxWidth: 480 }}>
          <InputLabel id="berlin-station-label">
            {labels.station}
          </InputLabel>

          <Select
            labelId="berlin-station-label"
            value={stationId}
            label={labels.station}
            disabled={stationsLoading || stations.length === 0}
            onChange={(event) => {
              setStationId(event.target.value);
            }}
          >
            {stations.map((station) => (
              <MenuItem
                key={station.station_id}
                value={station.station_id}
              >
                {station.station_name}
              </MenuItem>
            ))}
          </Select>
        </FormControl>

        {/* Station and forecast loading indicators */}
        {(stationsLoading || forecastLoading) && (
          <Stack
            direction="row"
            spacing={2}
            sx={{ alignItems: "center" }}
          >
            <CircularProgress size={24} />

            <Typography color="text.secondary">
              {stationsLoading
                ? labels.loadingStations
                : labels.loadingForecasts}
            </Typography>
          </Stack>
        )}

        {/* Report forecasting API errors separately. */}
        {forecastError && (
          <Alert severity="error">
            {labels.forecastError} ({forecastError})
          </Alert>
        )}

        {forecast && (
          <>
            {/* Latest usable reading for model inference */}
            <Card variant="outlined">
              <CardContent>
                <Stack spacing={2}>
                  <Stack
                    direction="row"
                    spacing={2}
                    sx={{
                      alignItems: "center",
                      flexWrap: "wrap",
                    }}
                  >
                    <Typography
                      variant="h6"
                      sx={{ fontWeight: 700 }}
                    >
                      {forecast.station_name}
                    </Typography>

                    <Chip
                      label={labels.historical}
                      size="small"
                      variant="outlined"
                    />
                  </Stack>

                  <Typography
                    variant="h4"
                    color="primary"
                    sx={{ fontWeight: 700 }}
                  >
                    {forecast.current_pm25_ugm3.toFixed(1)}
                    {" "}
                    {labels.unit}
                  </Typography>

                  <Typography color="text.secondary">
                    {labels.reading}
                  </Typography>

                  <Typography variant="body2">
                    <strong>{labels.origin}:</strong>{" "}
                    {formatDate(
                      forecast.forecast_origin_utc,
                      german
                    )}
                  </Typography>

                  <Typography variant="body2">
                    <strong>{labels.latest}:</strong>{" "}
                    {formatDate(
                      forecast.latest_stored_observation_utc,
                      german
                    )}
                  </Typography>
                </Stack>
              </CardContent>
            </Card>

            {/* Model predictions for 6, 12 and 24 hours ahead */}
            <Box
              sx={{
                display: "grid",
                gridTemplateColumns: {
                  xs: "1fr",
                  sm: "repeat(3, minmax(0, 1fr))",
                },
                gap: 2,
              }}
            >
              {[...forecast.predictions]
                .sort(
                  (a, b) =>
                    a.horizon_hours - b.horizon_hours
                )
                .map((prediction) => (
                  <Card
                    key={prediction.horizon_hours}
                    variant="outlined"
                  >
                    <CardContent>
                      <Typography color="text.secondary">
                        {labels.forecast}{" "}
                        {prediction.horizon_hours}{" "}
                        {labels.hours}
                      </Typography>

                      <Typography
                        variant="h4"
                        sx={{
                          fontWeight: 700,
                          my: 2,
                        }}
                      >
                        {prediction.predicted_pm25_ugm3.toFixed(1)}
                      </Typography>

                      <Typography color="text.secondary">
                        {labels.unit}
                      </Typography>

                      <Typography
                        variant="body2"
                        color="text.secondary"
                        sx={{ mt: 2 }}
                      >
                        {formatDate(
                          prediction.target_timestamp_utc,
                          german
                        )}
                      </Typography>
                    </CardContent>
                  </Card>
                ))}
            </Box>
          </>
        )}

        {/* Reuse the station selector for historical observations. */}
        {stations.length > 0 && (
          <StationHistoryChart
            city="berlin"
            stationId={stationId}
          />
        )}
      </Stack>
    </Box>
  );
}
