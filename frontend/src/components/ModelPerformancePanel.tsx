
/**
 * AirScope | nik
 * Model Performance & Limitations.
 *
 * Displays verified Berlin test-set results.
 * Compares ML forecasting with persistence.
 * Includes station-level model evaluation.
 */

import { useTranslation } from "react-i18next";

import {
  Alert,
  Box,
  Card,
  CardContent,
  Divider,
  Stack,
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

import StationEvaluationChart from "./StationEvaluationChart";

// Previously verified chronological Berlin test results.
const results = [
  {
    horizon: 6,
    samples: 9404,
    baselineMAE: 0.9696,
    modelMAE: 0.9292,
    baselineRMSE: 2.3693,
    modelRMSE: 2.6415,
  },
  {
    horizon: 12,
    samples: 9176,
    baselineMAE: 1.8102,
    modelMAE: 1.6712,
    baselineRMSE: 4.3221,
    modelRMSE: 3.9935,
  },
  {
    horizon: 24,
    samples: 8736,
    baselineMAE: 3.1725,
    modelMAE: 2.9142,
    baselineRMSE: 7.2063,
    modelRMSE: 5.9941,
  },
];

function calculateImprovement(
  baseline: number,
  model: number
) {
  return ((baseline - model) / baseline) * 100;
}

export default function ModelPerformancePanel() {
  const { i18n } = useTranslation();
  const german = i18n.language.startsWith("de");

  const labels = german
    ? {
        title: "Modellleistung und Grenzen",
        subtitle:
          "Wissenschaftliche Bewertung der Berliner PM2,5-Prognosen",
        maeTitle: "Vergleich des mittleren absoluten Fehlers (MAE)",
        model: "ML-Modell",
        baseline: "Persistenz-Baseline",
        horizon: "Horizont",
        samples: "Testbeispiele",
        improvement: "MAE-Verbesserung",
        results: "Detaillierte Testergebnisse",
        limitation: "Wichtige Einschränkungen",
        methodology:
          "Die Bewertung basiert auf einem chronologischen Testsatz. Die Persistenz-Baseline verwendet den aktuellen PM2,5-Messwert als Zukunftsprognose.",
        limitation1:
          "Beim 6-Stunden-Horizont verbessert das ML-Modell den MAE, hat aber einen höheren RMSE als die Persistenz-Baseline.",
        limitation2:
          "Ein lokales PM2,5-Ereignis an der Frankfurter Allee führte zu erheblichen Prognosefehlern.",
        limitation3:
          "Für London liegen noch keine unabhängig validierten ML-Prognoseergebnisse vor.",
        limitation4:
          "Die Ergebnisse beruhen auf gespeicherten historischen Messwerten und garantieren keine zukünftige Prognosegenauigkeit.",
      }
    : {
        title: "Model Performance & Limitations",
        subtitle:
          "Scientific evaluation of Berlin PM2.5 forecasting models",
        maeTitle: "Mean Absolute Error (MAE) Comparison",
        model: "ML model",
        baseline: "Persistence baseline",
        horizon: "Horizon",
        samples: "Test samples",
        improvement: "MAE improvement",
        results: "Detailed Test Results",
        limitation: "Important Limitations",
        methodology:
          "Evaluation uses a chronological test set. The persistence baseline predicts that the current PM2.5 observation will remain unchanged at the target time.",
        limitation1:
          "At the 6-hour horizon, ML improves MAE but produces worse RMSE than persistence.",
        limitation2:
          "A localized PM2.5 event at Frankfurter Allee produced substantial forecasting errors.",
        limitation3:
          "London does not yet have independently validated ML forecast results.",
        limitation4:
          "Results are based on stored historical observations and do not guarantee future forecasting accuracy.",
      };

  // Prepare the verified MAE values for Recharts.
  const chartData = results.map((result) => ({
    horizon: `${result.horizon}h`,
    baseline: result.baselineMAE,
    model: result.modelMAE,
  }));

  return (
    <Box sx={{ py: 3 }}>
      <Stack spacing={4}>
        {/* Overall evaluation heading */}
        <Box>
          <Typography
            variant="h4"
            component="h3"
            sx={{ fontWeight: 700 }}
            gutterBottom
          >
            {labels.title}
          </Typography>

          <Typography color="text.secondary">
            {labels.subtitle}
          </Typography>
        </Box>

        {/* Explain the evaluation methodology. */}
        <Alert severity="info">
          {labels.methodology}
        </Alert>

        {/* Overall model vs baseline MAE */}
        <Card variant="outlined">
          <CardContent>
            <Stack spacing={2}>
              <Typography
                variant="h6"
                sx={{ fontWeight: 700 }}
              >
                {labels.maeTitle}
              </Typography>

              <Box sx={{ width: "100%", height: 320 }}>
                <ResponsiveContainer
                  width="100%"
                  height="100%"
                >
                  <BarChart data={chartData}>
                    <CartesianGrid strokeDasharray="3 3" />

                    <XAxis dataKey="horizon" />

                    <YAxis domain={[0, "auto"]} />

                    <Tooltip />

                    <Legend />

                    <Bar
                      dataKey="baseline"
                      name={labels.baseline}
                      fill="#427AA1"
                    />

                    <Bar
                      dataKey="model"
                      name={labels.model}
                      fill="#F07F23"
                    />
                  </BarChart>
                </ResponsiveContainer>
              </Box>

              <Typography
                variant="body2"
                color="text.secondary"
              >
                MAE: µg/m³
              </Typography>
            </Stack>
          </CardContent>
        </Card>

        {/* Exact chronological test results */}
        <Card variant="outlined">
          <CardContent>
            <Typography
              variant="h6"
              sx={{ fontWeight: 700, mb: 2 }}
            >
              {labels.results}
            </Typography>

            <Box sx={{ overflowX: "auto" }}>
              <Box
                component="table"
                sx={{
                  width: "100%",
                  borderCollapse: "collapse",
                  minWidth: 680,
                  "& th, & td": {
                    textAlign: "right",
                    p: 1.5,
                    borderBottom: "1px solid",
                    borderColor: "divider",
                    fontSize: 13,
                  },
                  "& th:first-of-type, & td:first-of-type": {
                    textAlign: "left",
                  },
                }}
              >
                <thead>
                  <tr>
                    <th>{labels.horizon}</th>
                    <th>{labels.samples}</th>
                    <th>{labels.baseline} MAE</th>
                    <th>{labels.model} MAE</th>
                    <th>{labels.improvement}</th>
                    <th>{labels.baseline} RMSE</th>
                    <th>{labels.model} RMSE</th>
                  </tr>
                </thead>

                <tbody>
                  {results.map((result) => (
                    <tr key={result.horizon}>
                      <td>{result.horizon}h</td>
                      <td>{result.samples}</td>
                      <td>{result.baselineMAE.toFixed(4)}</td>
                      <td>{result.modelMAE.toFixed(4)}</td>
                      <td>
                        {calculateImprovement(
                          result.baselineMAE,
                          result.modelMAE
                        ).toFixed(2)}
                        %
                      </td>
                      <td>{result.baselineRMSE.toFixed(4)}</td>
                      <td>{result.modelRMSE.toFixed(4)}</td>
                    </tr>
                  ))}
                </tbody>
              </Box>
            </Box>

            <Typography
              variant="caption"
              color="text.secondary"
              sx={{ display: "block", mt: 2 }}
            >
              MAE and RMSE are measured in µg/m³.
            </Typography>
          </CardContent>
        </Card>

        {/* Real station-level metrics from FastAPI */}
        <StationEvaluationChart />

        {/* Limitations: results are not uniformly superior. */}
        <Card variant="outlined">
          <CardContent>
            <Typography
              variant="h6"
              sx={{ fontWeight: 700, mb: 2 }}
            >
              {labels.limitation}
            </Typography>

            <Stack spacing={2} divider={<Divider />}>
              <Typography variant="body2">
                {labels.limitation1}
              </Typography>

              <Typography variant="body2">
                {labels.limitation2}
              </Typography>

              <Typography variant="body2">
                {labels.limitation3}
              </Typography>

              <Typography variant="body2">
                {labels.limitation4}
              </Typography>
            </Stack>
          </CardContent>
        </Card>
      </Stack>
    </Box>
  );
}
