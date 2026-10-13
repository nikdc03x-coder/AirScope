
/**
 * AirScope | nik
 * Shared historical PM2.5 chart for Berlin and London.
 *
 * Fetches genuine hourly observations from FastAPI.
 * Missing measurements remain gaps in the chart.
 * Supports English and German labels.
 */

import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";

import {
  Alert,
  Box,
  Card,
  CardContent,
  CircularProgress,
  Stack,
  ToggleButton,
  ToggleButtonGroup,
  Typography,
} from "@mui/material";

import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

type City = "berlin" | "london";
type Days = 7 | 30 | 90;

type Observation = {
  timestamp_utc: string;
  pm25_ugm3: number | null;
  quality_status?: string;
};

type HistoryResponse = {
  city: string;
  station_id: string;
  station_name: string;
  window_days: number;
  mean_pm25_ugm3: number | null;
  available_measurements: number;
  missing_measurements: number;
  quality_counts?: Record<string, number>;
  observations: Observation[];
};

type Props = {
  city: City;
  stationId: string;
};

const API_BASE = "http://127.0.0.1:8000/api/v1";

export default function StationHistoryChart({
  city,
  stationId,
}: Props) {
  const { i18n } = useTranslation();
  const german = i18n.language.startsWith("de");

  const [days, setDays] = useState<Days>(7);
  const [history, setHistory] = useState<HistoryResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const labels = german
    ? {
        title: "Historischer PM2,5-Verlauf",
        subtitle: "Offizielle stündliche Messwerte",
        average: "Durchschnitt",
        available: "Verfügbare Messwerte",
        missing: "Fehlende Messwerte",
        quality: "Datenqualität",
        loading: "Messdaten werden geladen...",
        unavailable: "Messdaten konnten nicht geladen werden",
        historical: "Gespeicherte Messungen · Nicht live",
      }
    : {
        title: "Historical PM2.5 Trends",
        subtitle: "Official hourly observations",
        average: "Average",
        available: "Available readings",
        missing: "Missing readings",
        quality: "Data quality",
        loading: "Loading observations...",
        unavailable: "Unable to load observations",
        historical: "Stored observations · Not live",
      };

  // Reload when the city, station, or selected period changes.
  useEffect(() => {
    const controller = new AbortController();

    async function loadHistory() {
      setLoading(true);
      setError("");
      setHistory(null);

      try {
        const url =
          `${API_BASE}/observations/${city}/` +
          `${encodeURIComponent(stationId)}?days=${days}`;

        const response = await fetch(url, {
          signal: controller.signal,
        });

        if (!response.ok) {
          throw new Error(`API returned ${response.status}`);
        }

        const data: HistoryResponse = await response.json();

        if (
          data.station_id !== stationId ||
          !Array.isArray(data.observations)
        ) {
          throw new Error("Invalid history response");
        }

        setHistory(data);
      } catch (err) {
        if (controller.signal.aborted) return;

        setError(
          err instanceof Error ? err.message : "Unknown error"
        );
      } finally {
        if (!controller.signal.aborted) {
          setLoading(false);
        }
      }
    }

    void loadHistory();

    return () => controller.abort();
  }, [city, stationId, days]);

  // Convert ISO dates to numeric timestamps for Recharts.
  const chartData =
    history?.observations.map((item) => ({
      timestamp: new Date(item.timestamp_utc).getTime(),
      pm25: item.pm25_ugm3,
    })) ?? [];

  function formatAxisTime(value: number) {
    return new Intl.DateTimeFormat(
      german ? "de-DE" : "en-GB",
      {
        month: "short",
        day: "numeric",
        timeZone: "UTC",
      }
    ).format(new Date(value));
  }

  function formatTooltipTime(value: number) {
    const result = new Intl.DateTimeFormat(
      german ? "de-DE" : "en-GB",
      {
        dateStyle: "medium",
        timeStyle: "short",
        timeZone: "UTC",
      }
    ).format(new Date(value));

    return `${result} UTC`;
  }

  return (
    <Card variant="outlined">
      <CardContent>
        <Stack spacing={3}>
          {/* Heading and source information */}
          <Box>
            <Typography
              variant="h5"
              sx={{ fontWeight: 700 }}
            >
              {labels.title}
            </Typography>

            <Typography color="text.secondary">
              {labels.subtitle}
            </Typography>

            <Typography
              variant="body2"
              color="text.secondary"
              sx={{ mt: 1 }}
            >
              {history?.station_name ?? stationId}
            </Typography>
          </Box>

          {/* Range selector */}
          <ToggleButtonGroup
            exclusive
            size="small"
            value={days}
            onChange={(_event, value: Days | null) => {
              if (value !== null) setDays(value);
            }}
            aria-label="Historical time range"
          >
            <ToggleButton value={7}>7D</ToggleButton>
            <ToggleButton value={30}>30D</ToggleButton>
            <ToggleButton value={90}>90D</ToggleButton>
          </ToggleButtonGroup>

          {loading && (
            <Stack
              direction="row"
              spacing={2}
              sx={{ alignItems: "center" }}
            >
              <CircularProgress size={22} />
              <Typography>{labels.loading}</Typography>
            </Stack>
          )}

          {error && (
            <Alert severity="error">
              {labels.unavailable}: {error}
            </Alert>
          )}

          {history && (
            <>
              {/* Data coverage statistics */}
              <Box
                sx={{
                  display: "grid",
                  gridTemplateColumns: {
                    xs: "repeat(2, 1fr)",
                    md: "repeat(3, 1fr)",
                  },
                  gap: 2,
                }}
              >
                <Box>
                  <Typography
                    variant="body2"
                    color="text.secondary"
                  >
                    {labels.average}
                  </Typography>

                  <Typography
                    variant="h6"
                    sx={{ fontWeight: 700 }}
                  >
                    {history.mean_pm25_ugm3?.toFixed(1) ?? "—"}
                    {" µg/m³"}
                  </Typography>
                </Box>

                <Box>
                  <Typography
                    variant="body2"
                    color="text.secondary"
                  >
                    {labels.available}
                  </Typography>

                  <Typography
                    variant="h6"
                    sx={{ fontWeight: 700 }}
                  >
                    {history.available_measurements}
                  </Typography>
                </Box>

                <Box>
                  <Typography
                    variant="body2"
                    color="text.secondary"
                  >
                    {labels.missing}
                  </Typography>

                  <Typography
                    variant="h6"
                    sx={{ fontWeight: 700 }}
                  >
                    {history.missing_measurements}
                  </Typography>
                </Box>
              </Box>

              {/* Actual observations, preserving missing gaps */}
              <Box sx={{ width: "100%", height: 320 }}>
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={chartData}>
                    <CartesianGrid strokeDasharray="3 3" />

                    <XAxis
                      dataKey="timestamp"
                      type="number"
                      scale="time"
                      domain={["dataMin", "dataMax"]}
                      tickFormatter={formatAxisTime}
                    />

                    <YAxis
                      width={54}
                      domain={[0, "auto"]}
                      label={{
                        value: "µg/m³",
                        angle: -90,
                        position: "insideLeft",
                      }}
                    />

                    <Tooltip
                      labelFormatter={(value) =>
                        formatTooltipTime(Number(value))
                      }
                    />

                    <Line
                      type="monotone"
                      dataKey="pm25"
                      stroke="#427AA1"
                      strokeWidth={2}
                      dot={false}
                      connectNulls={false}
                      isAnimationActive={false}
                    />
                  </LineChart>
                </ResponsiveContainer>
              </Box>

              {/* London has official ratified/provisional labels. */}
              {city === "london" && history.quality_counts && (
                <Box>
                  <Typography
                    variant="subtitle2"
                    sx={{ mb: 1 }}
                  >
                    {labels.quality}
                  </Typography>

                  <Stack
                    direction="row"
                    spacing={2}
                    sx={{ flexWrap: "wrap" }}
                  >
                    {Object.entries(history.quality_counts).map(
                      ([status, count]) => (
                        <Typography
                          key={status}
                          variant="body2"
                          color="text.secondary"
                        >
                          {status}: {count}
                        </Typography>
                      )
                    )}
                  </Stack>
                </Box>
              )}

              <Typography
                variant="body2"
                color="text.secondary"
              >
                {labels.historical}
              </Typography>
            </>
          )}
        </Stack>
      </CardContent>
    </Card>
  );
}
