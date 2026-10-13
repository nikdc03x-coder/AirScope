
/**
 * AirScope | nik
 * Berlin vs London historical PM2.5 comparison.
 *
 * Uses official observations from the existing FastAPI endpoints.
 * Aligns observations by UTC date and calculates daily means.
 * Missing measurements are never replaced with zero.
 */

import { useEffect, useMemo, useState } from "react";
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
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

type Days = 7 | 30;

type Observation = {
  timestamp_utc: string;
  pm25_ugm3: number | null;
};

type HistoryResponse = {
  station_id: string;
  station_name: string;
  window_end_utc: string;
  observations: Observation[];
};

type DailyRecord = {
  date: string;
  berlin: number | null;
  london: number | null;
  berlinCount: number;
  londonCount: number;
};

const API_BASE = "http://127.0.0.1:8000/api/v1";

// Calculate daily means from genuine non-null observations.
function calculateDailyMeans(observations: Observation[]) {
  const days = new Map<
    string,
    { total: number; count: number }
  >();

  for (const item of observations) {
    const date = item.timestamp_utc.slice(0, 10);

    if (item.pm25_ugm3 === null) {
      continue;
    }

    if (!Number.isFinite(item.pm25_ugm3)) {
      continue;
    }

    const entry = days.get(date) ?? {
      total: 0,
      count: 0,
    };

    entry.total += item.pm25_ugm3;
    entry.count += 1;

    days.set(date, entry);
  }

  return days;
}

export default function CityComparisonChart() {
  const { i18n } = useTranslation();
  const german = i18n.language.startsWith("de");

  const [days, setDays] = useState<Days>(7);
  const [berlin, setBerlin] = useState<HistoryResponse | null>(
    null
  );
  const [london, setLondon] = useState<HistoryResponse | null>(
    null
  );
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const labels = german
    ? {
        title: "Berlin–London-Vergleich",
        subtitle:
          "Tägliche PM2,5-Mittelwerte aus offiziellen Messstationen",
        berlin: "Berlin Wedding",
        london: "London Bloomsbury",
        loading: "Vergleichsdaten werden geladen...",
        error: "Vergleichsdaten konnten nicht geladen werden.",
        info:
          "Verglichen werden zwei einzelne Messstationen, nicht die gesamten Städte. Die Werte sind historische Messungen und keine Live-Daten.",
        period:
          "Die Tagesmittel werden nur aus verfügbaren stündlichen Messwerten berechnet. Fehlende Messungen werden nicht ergänzt.",
        noData:
          "Keine gemeinsamen Beobachtungstage verfügbar.",
        days: "Tage",
        readings: "Messwerte",
      }
    : {
        title: "Berlin vs London",
        subtitle:
          "Daily mean PM2.5 from official monitoring stations",
        berlin: "Berlin Wedding",
        london: "London Bloomsbury",
        loading: "Loading comparison data...",
        error: "Unable to load comparison data.",
        info:
          "This compares two individual monitoring stations, not entire cities. These are historical observations, not live readings.",
        period:
          "Daily means use available hourly measurements only. Missing readings are not filled in.",
        noData:
          "No overlapping observation dates are available.",
        days: "days",
        readings: "readings",
      };

  // Load both stations for the same requested time window.
  useEffect(() => {
    const controller = new AbortController();

    async function loadComparison() {
      setLoading(true);
      setError("");
      setBerlin(null);
      setLondon(null);

      try {
        const urls = [
          `${API_BASE}/observations/berlin/DEBE010?days=${days}`,
          `${API_BASE}/observations/london/CLL2?days=${days}`,
        ];

        const responses = await Promise.all(
          urls.map((url) =>
            fetch(url, { signal: controller.signal })
          )
        );

        if (responses.some((response) => !response.ok)) {
          throw new Error(
            `API returned ${responses.map((r) => r.status).join(", ")}`
          );
        }

        const [berlinData, londonData] =
          (await Promise.all(
            responses.map((response) => response.json())
          )) as HistoryResponse[];

        if (
          berlinData.station_id !== "DEBE010" ||
          londonData.station_id !== "CLL2" ||
          !Array.isArray(berlinData.observations) ||
          !Array.isArray(londonData.observations)
        ) {
          throw new Error("Unexpected comparison response");
        }

        setBerlin(berlinData);
        setLondon(londonData);
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

    void loadComparison();

    return () => controller.abort();
  }, [days]);

  // Align daily values by UTC date, not array position.
  const chartData = useMemo<DailyRecord[]>(() => {
    if (!berlin || !london) return [];

    const berlinDaily = calculateDailyMeans(
      berlin.observations
    );
    const londonDaily = calculateDailyMeans(
      london.observations
    );

    // Only plot dates covered by both requested windows.
    const berlinDates = new Set(
      berlin.observations.map((item) =>
        item.timestamp_utc.slice(0, 10)
      )
    );
    const londonDates = new Set(
      london.observations.map((item) =>
        item.timestamp_utc.slice(0, 10)
      )
    );

    const sharedDates = [...berlinDates]
      .filter((date) => londonDates.has(date))
      .sort();

    return sharedDates.map((date) => {
      const b = berlinDaily.get(date);
      const l = londonDaily.get(date);

      return {
        date,
        berlin: b ? Number((b.total / b.count).toFixed(2)) : null,
        london: l ? Number((l.total / l.count).toFixed(2)) : null,
        berlinCount: b?.count ?? 0,
        londonCount: l?.count ?? 0,
      };
    });
  }, [berlin, london]);

  function formatDate(date: string) {
    return new Intl.DateTimeFormat(
      german ? "de-DE" : "en-GB",
      {
        day: "numeric",
        month: "short",
        timeZone: "UTC",
      }
    ).format(new Date(`${date}T00:00:00Z`));
  }

  return (
    <Card variant="outlined">
      <CardContent>
        <Stack spacing={3}>
          {/* Comparison heading */}
          <Box>
            <Typography
              variant="h5"
              component="h2"
              sx={{ fontWeight: 700 }}
              gutterBottom
            >
              {labels.title}
            </Typography>

            <Typography color="text.secondary">
              {labels.subtitle}
            </Typography>
          </Box>

          <Alert severity="info">
            {labels.info}
          </Alert>

          {/* Compare matching historical time windows. */}
          <ToggleButtonGroup
            exclusive
            value={days}
            size="small"
            onChange={(_event, value: Days | null) => {
              if (value !== null) {
                setDays(value);
              }
            }}
            aria-label="Comparison time range"
          >
            <ToggleButton value={7}>7D</ToggleButton>
            <ToggleButton value={30}>30D</ToggleButton>
          </ToggleButtonGroup>

          {/* Loading and errors */}
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

          {/* Daily PM2.5 comparison */}
          {!loading && !error && berlin && london && (
            <>
              {chartData.length === 0 ? (
                <Alert severity="warning">
                  {labels.noData}
                </Alert>
              ) : (
                <Box sx={{ width: "100%", height: 350 }}>
                  <ResponsiveContainer
                    width="100%"
                    height="100%"
                  >
                    <LineChart
                      data={chartData}
                      margin={{
                        top: 10,
                        right: 15,
                        bottom: 10,
                        left: 10,
                      }}
                    >
                      <CartesianGrid
                        strokeDasharray="3 3"
                      />

                      <XAxis
                        dataKey="date"
                        tickFormatter={formatDate}
                        minTickGap={20}
                      />

                      <YAxis
                        domain={[0, "auto"]}
                        width={48}
                        label={{
                          value: "µg/m³",
                          angle: -90,
                          position: "insideLeft",
                        }}
                      />

                      <Tooltip
                        labelFormatter={(value) =>
                          String(value)
                        }
                      />

                      <Legend />

                      <Line
                        name={labels.berlin}
                        dataKey="berlin"
                        type="monotone"
                        stroke="#427AA1"
                        strokeWidth={2}
                        dot={days === 7}
                        connectNulls={false}
                        isAnimationActive={false}
                      />

                      <Line
                        name={labels.london}
                        dataKey="london"
                        type="monotone"
                        stroke="#F07F23"
                        strokeWidth={2}
                        dot={days === 7}
                        connectNulls={false}
                        isAnimationActive={false}
                      />
                    </LineChart>
                  </ResponsiveContainer>
                </Box>
              )}

              <Typography
                variant="body2"
                color="text.secondary"
              >
                {labels.period}
              </Typography>

              <Typography
                variant="caption"
                color="text.secondary"
              >
                {labels.berlin}: UBA · {labels.london}: DEFRA UK-AIR
              </Typography>
            </>
          )}
        </Stack>
      </CardContent>
    </Card>
  );
}
