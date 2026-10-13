
/**
 * AirScope | nik
 * Station-level model evaluation visualization.
 *
 * Displays genuine chronological test metrics from FastAPI.
 * Compares ML model MAE against persistence baseline.
 * Supports mobile scrolling and English/German labels.
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
  Stack,
  ToggleButton,
  ToggleButtonGroup,
  Typography,
} from "@mui/material";

import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

// Supported forecasting horizons.
type Horizon = 6 | 12 | 24;

// Station-level metrics returned by FastAPI.
type StationResult = {
  station_id: string;
  station_name: string;
  horizon_hours: number;
  samples: number;
  baseline_mae: number;
  model_mae: number;
  baseline_rmse: number;
  model_rmse: number;
  mae_improvement_pct: number | null;
  model_bias: number;
};

// Complete evaluation API response.
type EvaluationResponse = {
  city: string;
  evaluation_partition: string;
  horizon_hours: number;
  station_count: number;
  unit: string;
  is_live: boolean;
  stations: StationResult[];
};

const API_BASE = "http://127.0.0.1:8000/api/v1";

export default function StationEvaluationChart() {
  const { i18n } = useTranslation();
  const german = i18n.language.startsWith("de");

  const [horizon, setHorizon] = useState<Horizon>(24);
  const [results, setResults] = useState<StationResult[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  // Localized labels for the evaluation dashboard.
  const labels = german
    ? {
        title: "Modellgenauigkeit nach Messstation",
        subtitle:
          "MAE-Vergleich zwischen ML-Modell und Persistenz",
        model: "ML-Modell",
        baseline: "Persistenz",
        loading: "Testergebnisse werden geladen...",
        error: "Testergebnisse konnten nicht geladen werden.",
        worse: "ML schlechter als Persistenz",
        better: "ML besser als Persistenz",
        equal: "Gleiche Genauigkeit",
        samples: "Testbeispiele",
        improvement: "MAE-Verbesserung",
        horizon: "Prognosehorizont",
        scrollHint:
          "Auf kleinen Bildschirmen horizontal scrollen, um alle Werte zu sehen.",
        note:
          "Die Fehlerwerte stammen aus dem chronologischen Testsatz. Niedrigere MAE-Werte sind besser. Negative Verbesserungswerte bedeuten, dass Persistenz besser abschneidet.",
      }
    : {
        title: "Model Accuracy by Station",
        subtitle:
          "MAE comparison between ML and persistence",
        model: "ML model",
        baseline: "Persistence",
        loading: "Loading test results...",
        error: "Unable to load evaluation results.",
        worse: "ML worse than persistence",
        better: "ML better than persistence",
        equal: "Equal accuracy",
        samples: "Test samples",
        improvement: "MAE improvement",
        horizon: "Forecast horizon",
        scrollHint:
          "On small screens, scroll horizontally to view the full chart.",
        note:
          "These errors come from the chronological test set. Lower MAE is better. Negative improvement means persistence performed better.",
      };

  // Fetch evaluation data whenever the horizon changes.
  useEffect(() => {
    const controller = new AbortController();

    async function loadResults() {
      setLoading(true);
      setError("");
      setResults([]);

      try {
        const response = await fetch(
          `${API_BASE}/evaluation/berlin/stations?horizon=${horizon}`,
          {
            signal: controller.signal,
          }
        );

        if (!response.ok) {
          throw new Error(`HTTP ${response.status}`);
        }

        const data: EvaluationResponse = await response.json();

        // Reject incomplete or unexpected API responses.
        if (
          data.horizon_hours !== horizon ||
          data.station_count !== 12 ||
          data.is_live !== false ||
          !Array.isArray(data.stations) ||
          data.stations.length !== 12
        ) {
          throw new Error("Unexpected evaluation response");
        }

        setResults(data.stations);
      } catch (err) {
        if (controller.signal.aborted) return;

        setError(
          err instanceof Error
            ? err.message
            : "Unknown error"
        );
      } finally {
        if (!controller.signal.aborted) {
          setLoading(false);
        }
      }
    }

    void loadResults();

    return () => controller.abort();
  }, [horizon]);

  // Sort stations by ML error so difficult stations appear first.
  const chartData = [...results]
    .sort((a, b) => b.model_mae - a.model_mae)
    .map((item) => ({
      station: item.station_name.replace(/^Berlin\s+/, ""),
      model: Number(item.model_mae.toFixed(3)),
      baseline: Number(item.baseline_mae.toFixed(3)),
    }));

  return (
    <Card variant="outlined" sx={{ minWidth: 0 }}>
      <CardContent>
        <Stack spacing={3}>
          {/* =========================================
              HEADING
             ========================================= */}
          <Box>
            <Typography
              variant="h5"
              component="h3"
              gutterBottom
              sx={{ fontWeight: 700 }}
            >
              {labels.title}
            </Typography>

            <Typography color="text.secondary">
              {labels.subtitle}
            </Typography>
          </Box>

          {/* =========================================
              FORECAST HORIZON SELECTOR
             ========================================= */}
          <ToggleButtonGroup
            exclusive
            value={horizon}
            size="small"
            aria-label={labels.horizon}
            onChange={(_event, value: Horizon | null) => {
              if (value !== null) {
                setHorizon(value);
              }
            }}
            sx={{
              alignSelf: "flex-start",
              maxWidth: "100%",
            }}
          >
            <ToggleButton value={6}>
              6h
            </ToggleButton>

            <ToggleButton value={12}>
              12h
            </ToggleButton>

            <ToggleButton value={24}>
              24h
            </ToggleButton>
          </ToggleButtonGroup>

          {/* =========================================
              LOADING AND ERROR STATES
             ========================================= */}
          {loading && (
            <Stack
              direction="row"
              spacing={2}
              sx={{
                alignItems: "center",
                flexWrap: "wrap",
              }}
            >
              <CircularProgress size={24} />

              <Typography>
                {labels.loading}
              </Typography>
            </Stack>
          )}

          {error && (
            <Alert severity="error">
              {labels.error} ({error})
            </Alert>
          )}

          {/* =========================================
              STATION EVALUATION RESULTS
             ========================================= */}
          {!loading && !error && results.length > 0 && (
            <>
              {/* Explain mobile horizontal scrolling. */}
              <Typography
                variant="caption"
                color="text.secondary"
                sx={{
                  display: {
                    xs: "block",
                    md: "none",
                  },
                }}
              >
                {labels.scrollHint}
              </Typography>

              {/* =====================================
                  MOBILE RESPONSIVE CHART

                  Outer Box:
                  Scroll horizontally on smaller screens.

                  Inner Box:
                  Preserve enough width for 12 station labels.
                 ===================================== */}
              <Box
                role="region"
                aria-label={labels.title}
                tabIndex={0}
                sx={{
                  width: "100%",
                  maxWidth: "100%",
                  overflowX: "auto",
                  overflowY: "hidden",
                  WebkitOverflowScrolling: "touch",
                  pb: 1,
                }}
              >
                <Box
                  sx={{
                    width: "100%",
                    minWidth: 680,
                    height: 580,
                  }}
                >
                  <ResponsiveContainer
                    width="100%"
                    height="100%"
                  >
                    <BarChart
                      data={chartData}
                      layout="vertical"
                      margin={{
                        top: 10,
                        right: 25,
                        bottom: 10,
                        left: 15,
                      }}
                    >
                      <CartesianGrid
                        strokeDasharray="3 3"
                      />

                      <XAxis
                        type="number"
                        domain={[0, "auto"]}
                        tickFormatter={(value: number) =>
                          value.toFixed(1)
                        }
                      />

                      <YAxis
                        type="category"
                        dataKey="station"
                        width={175}
                        tick={{
                          fontSize: 11,
                        }}
                      />

                      <Tooltip
                        formatter={(value, name) => [
                          `${Number(value).toFixed(3)} µg/m³`,
                          String(name),
                        ]}
                      />

                      <Legend />

                      <Bar
                        name={labels.baseline}
                        dataKey="baseline"
                        fill="#427AA1"
                      />

                      <Bar
                        name={labels.model}
                        dataKey="model"
                        fill="#F07F23"
                      />
                    </BarChart>
                  </ResponsiveContainer>
                </Box>
              </Box>

              {/* =====================================
                  STATION-LEVEL SUMMARY

                  Each station wraps on smaller screens.
                  Negative improvement is highlighted.
                 ===================================== */}
              <Stack spacing={1}>
                {[...results]
                  .sort((a, b) =>
                    a.station_name.localeCompare(
                      b.station_name
                    )
                  )
                  .map((item) => {
                    const improvement =
                      item.mae_improvement_pct;

                    const isEqual =
                      improvement === null ||
                      Math.abs(improvement) < 0.005;

                    const isWorse =
                      improvement !== null &&
                      improvement < -0.005;

                    const status = isEqual
                      ? labels.equal
                      : isWorse
                        ? labels.worse
                        : labels.better;

                    return (
                      <Box
                        key={item.station_id}
                        sx={{
                          display: "flex",
                          flexDirection: {
                            xs: "column",
                            sm: "row",
                          },
                          justifyContent:
                            "space-between",
                          alignItems: {
                            xs: "flex-start",
                            sm: "center",
                          },
                          gap: 1.5,
                          py: 1.5,
                          borderBottom: "1px solid",
                          borderColor: "divider",
                        }}
                      >
                        {/* Station name and test samples */}
                        <Box sx={{ minWidth: 0 }}>
                          <Typography
                            variant="body2"
                            sx={{
                              fontWeight: 600,
                              overflowWrap: "anywhere",
                            }}
                          >
                            {item.station_name}
                          </Typography>

                          <Typography
                            variant="caption"
                            color="text.secondary"
                          >
                            {labels.samples}:{" "}
                            {item.samples.toLocaleString(
                              german ? "de-DE" : "en-GB"
                            )}
                          </Typography>
                        </Box>

                        {/* Improvement percentage and status */}
                        <Stack
                          direction="row"
                          spacing={1}
                          sx={{
                            alignItems: "center",
                            flexWrap: "wrap",
                            rowGap: 1,
                            maxWidth: "100%",
                          }}
                        >
                          <Typography variant="body2">
                            {labels.improvement}:{" "}
                            {improvement === null
                              ? "—"
                              : `${
                                  improvement > 0 ? "+" : ""
                                }${improvement.toFixed(2)}%`}
                          </Typography>

                          <Chip
                            size="small"
                            variant="outlined"
                            label={status}
                            color={
                              isWorse
                                ? "warning"
                                : "default"
                            }
                            sx={{
                              maxWidth: "100%",
                              height: "auto",
                              "& .MuiChip-label": {
                                whiteSpace: "normal",
                                py: 0.5,
                              },
                            }}
                          />
                        </Stack>
                      </Box>
                    );
                  })}
              </Stack>

              {/* Explain the scientific interpretation. */}
              <Alert severity="info">
                {labels.note}
              </Alert>
            </>
          )}
        </Stack>
      </CardContent>
    </Card>
  );
}
