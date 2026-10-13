
/**
 * AirScope | nik
 * Interactive Berlin historical PM2.5 chart.
 *
 * Loads genuine hourly observations from FastAPI.
 * Supports 7-, 30-, and 90-day history.
 * Missing readings are displayed as gaps, not zeros.
 */

import { useEffect, useState } from "react";

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

import { useTranslation } from "react-i18next";

type HistoryPoint = {
  timestamp_utc: string;
  pm25_ugm3: number | null;
};

type HistoryResponse = {
  station_id: string;
  station_name: string;
  window_days: number;
  mean_pm25_ugm3: number | null;
  missing_measurements: number;
  available_measurements: number;
  observations: HistoryPoint[];
};

type Props = {
  stationId: string;
};

const API_BASE = "http://127.0.0.1:8000/api/v1";

export default function BerlinHistoryChart({ stationId }: Props) {
  const { i18n } = useTranslation();
  const german = i18n.language.startsWith("de");

  const [days, setDays] = useState<7 | 30 | 90>(7);
  const [history, setHistory] = useState<HistoryResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const labels = german
    ? {
        title: "Historischer PM2,5-Verlauf",
        description: "Stündliche Messwerte der ausgewählten Station",
        average: "Durchschnitt",
        missing: "Fehlende Messwerte",
        loading: "Messdaten werden geladen...",
        error: "Historische Messwerte konnten nicht geladen werden.",
        historical: "Gespeicherte Messdaten · Nicht live",
      }
    : {
        title: "Historical PM2.5 Trends",
        description: "Hourly observations from the selected station",
        average: "Average",
        missing: "Missing readings",
        loading: "Loading observations...",
        error: "Could not load historical observations.",
        historical: "Stored observations · Not live",
      };

  // Fetch the selected period whenever station or days changes.
  useEffect(() => {
    const controller = new AbortController();

    async function loadHistory() {
      setLoading(true);
      setError("");
      setHistory(null);

      try {
        const response = await fetch(
          `${API_BASE}/observations/berlin/${encodeURIComponent(stationId)}?days=${days}`,
          { signal: controller.signal }
        );

        if (!response.ok) {
          throw new Error(`API returned ${response.status}`);
        }

        const result: HistoryResponse = await response.json();

        if (
          result.station_id !== stationId ||
          !Array.isArray(result.observations)
        ) {
          throw new Error("Invalid observation response");
        }

        setHistory(result);
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
  }, [stationId, days]);

  // Recharts expects numeric timestamps for a chronological axis.
  const chartData =
    history?.observations.map((item) => ({
      timestamp: new Date(item.timestamp_utc).getTime(),
      pm25: item.pm25_ugm3,
    })) ?? [];

  function formatTime(timestamp: number) {
    return new Intl.DateTimeFormat(
      german ? "de-DE" : "en-GB",
      {
        month: "short",
        day: "numeric",
        timeZone: "UTC",
      }
    ).format(new Date(timestamp));
  }

  function formatTooltipTime(timestamp: number) {
    return new Intl.DateTimeFormat(
      german ? "de-DE" : "en-GB",
      {
        dateStyle: "medium",
        timeStyle: "short",
        timeZone: "UTC",
      }
    ).format(new Date(timestamp)) + " UTC";
  }

  return (
    <Card variant="outlined">
      <CardContent>
        <Stack spacing={3}>
          <Box>
            <Typography
              variant="h5"
              sx={{ fontWeight: 700 }}
            >
              {labels.title}
            </Typography>

            <Typography color="text.secondary">
              {labels.description}
            </Typography>
          </Box>

          <ToggleButtonGroup
            exclusive
            value={days}
            onChange={(_event, value: 7 | 30 | 90 | null) => {
              if (value !== null) setDays(value);
            }}
            size="small"
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
              {labels.error} ({error})
            </Alert>
          )}

          {history && (
            <>
              <Stack direction="row" spacing={3} sx={{ flexWrap: "wrap" }}>
                <Box>
                  <Typography variant="body2" color="text.secondary">
                    {labels.average}
                  </Typography>
                  <Typography variant="h6" sx={{ fontWeight: 700 }}>
                    {history.mean_pm25_ugm3?.toFixed(1) ?? "—"} µg/m³
                  </Typography>
                </Box>

                <Box>
                  <Typography variant="body2" color="text.secondary">
                    {labels.missing}
                  </Typography>
                  <Typography variant="h6" sx={{ fontWeight: 700 }}>
                    {history.missing_measurements}
                  </Typography>
                </Box>
              </Stack>

              <Box sx={{ width: "100%", height: 300 }}>
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={chartData}>
                    <CartesianGrid strokeDasharray="3 3" />

                    <XAxis
                      dataKey="timestamp"
                      type="number"
                      scale="time"
                      domain={["dataMin", "dataMax"]}
                      tickFormatter={formatTime}
                    />

                    <YAxis
                      width={45}
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
