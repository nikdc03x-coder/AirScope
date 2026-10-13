
/**
 * AirScope | nik
 * Main city dashboard for Berlin and London.
 *
 * Berlin: historical PM2.5 and experimental ML forecasts.
 * London: official PM2.5 observations and quality information.
 * Comparison: historical PM2.5 trends from both cities.
 * Evaluation: model performance and scientific limitations.
 * Transparency: official sources and data reliability.
 */

import { useState } from "react";
import { useTranslation } from "react-i18next";
import DataFreshnessPanel from "../components/DataFreshnessPanel";
import {
  Alert,
  Box,
  Card,
  CardContent,
  Container,
  ToggleButton,
  ToggleButtonGroup,
  Typography,
} from "@mui/material";

// AirScope | nik
// Reuse existing components instead of duplicating their logic.
import BerlinForecastPanel from "../components/BerlinForecastPanel";
import StationHistoryChart from "../components/StationHistoryChart";
import CityComparisonChart from "../components/CityComparisonChart";
import ModelPerformancePanel from "../components/ModelPerformancePanel";
import DataTransparencyPanel from "../components/DataTransparencyPanel";

// Only Berlin and London are currently supported.
type City = "berlin" | "london";

function CitiesPage() {
  const { t, i18n } = useTranslation();

  const german = i18n.language.startsWith("de");

  // Berlin is selected initially because it has evaluated ML models.
  const [selectedCity, setSelectedCity] = useState<City>("berlin");

  // English and German labels for this page.
  const labels = german
    ? {
        selectCity: "Stadt auswählen",

        berlinDescription:
          "Offizielle PM2,5-Messwerte und experimentelle KI-Prognosen",

        londonTitle: "London – PM2,5-Messwerte",

        londonDescription:
          "Historische Luftqualitätsdaten von London Bloomsbury",

        londonSource: "Datenquelle: DEFRA UK-AIR",

        londonForecast:
          "Für London sind derzeit keine unabhängig validierten KI-Prognosen verfügbar. Die historischen Messwerte können bereits untersucht werden.",

        comparisonHeading: "Städtevergleich",

        comparisonDescription:
          "Vergleichen Sie historische PM2,5-Messwerte von Berlin Wedding und London Bloomsbury.",

        evaluationHeading: "Wissenschaftliche Modellbewertung",

        evaluationDescription:
          "Untersuchen Sie die Genauigkeit der Berliner ML-Prognosen, die Persistenz-Baseline und die Grenzen der Modelle.",
      }
    : {
        selectCity: "Select a city",

        berlinDescription:
          "Official PM2.5 observations and experimental AI forecasts",

        londonTitle: "London PM2.5 Observations",

        londonDescription:
          "Historical air-quality measurements from London Bloomsbury",

        londonSource: "Data source: DEFRA UK-AIR",

        londonForecast:
          "Independently validated AI forecasts are not yet available for London. You can still explore its historical observations.",

        comparisonHeading: "City Comparison",

        comparisonDescription:
          "Compare historical PM2.5 measurements from Berlin Wedding and London Bloomsbury.",

        evaluationHeading: "Scientific Model Evaluation",

        evaluationDescription:
          "Explore Berlin ML forecast accuracy, the persistence baseline, and important model limitations.",
      };

  return (
    <Container maxWidth="lg">
      <Box sx={{ py: { xs: 5, md: 8 } }}>
        {/* =========================================
            PAGE HEADING
            Preserve existing translation keys.
           ========================================= */}

        <Typography
          variant="h3"
          component="h1"
          gutterBottom
        >
          {t("cities.title")}
        </Typography>

        <Typography
          color="text.secondary"
          sx={{ mb: 4 }}
        >
          {t("cities.description")}
        </Typography>

        {/* =========================================
            CITY SELECTION
            Switch between Berlin and London.
           ========================================= */}

        <Typography
          variant="subtitle1"
          sx={{
            fontWeight: 600,
            mb: 2,
          }}
        >
          {labels.selectCity}
        </Typography>

        <ToggleButtonGroup
          exclusive
          value={selectedCity}
          onChange={(_event, city: City | null) => {
            // Prevent the user from deselecting both cities.
            if (city !== null) {
              setSelectedCity(city);
            }
          }}
          aria-label={labels.selectCity}
          sx={{
            mb: 4,
            flexWrap: "wrap",
          }}
        >
          <ToggleButton value="berlin">
            {t("cities.berlin")}
          </ToggleButton>

          <ToggleButton value="london">
            {t("cities.london")}
          </ToggleButton>
        </ToggleButtonGroup>

        {/* =========================================
            BERLIN DASHBOARD
            Historical observations + 6h/12h/24h
            experimental machine-learning forecasts.
           ========================================= */}

        {selectedCity === "berlin" && (
          <Box>
            <Card
              variant="outlined"
              sx={{ mb: 3 }}
            >
              <CardContent>
                <Typography
                  variant="h5"
                  gutterBottom
                  sx={{ fontWeight: 700 }}
                >
                  {t("cities.berlin")}
                </Typography>

                <Typography color="text.secondary">
                  {t("cities.berlinCountry")}
                </Typography>

                <Typography
                  variant="body2"
                  color="text.secondary"
                  sx={{ mt: 2 }}
                >
                  {labels.berlinDescription}
                </Typography>
              </CardContent>
            </Card>

            {/* Berlin station selector, historical chart
                and experimental ML forecasts. */}
            <BerlinForecastPanel />
          </Box>
        )}

        {/* =========================================
            LONDON DASHBOARD
            Official historical observations.
            No validated London ML forecasts yet.
           ========================================= */}

        {selectedCity === "london" && (
          <Box>
            <Card
              variant="outlined"
              sx={{ mb: 3 }}
            >
              <CardContent>
                <Typography
                  variant="h5"
                  gutterBottom
                  sx={{ fontWeight: 700 }}
                >
                  {labels.londonTitle}
                </Typography>

                <Typography color="text.secondary">
                  {t("cities.londonCountry")}
                </Typography>

                <Typography
                  variant="body2"
                  color="text.secondary"
                  sx={{ mt: 2 }}
                >
                  {labels.londonDescription}
                </Typography>

                <Typography
                  variant="body2"
                  color="text.secondary"
                  sx={{ mt: 1 }}
                >
                  {labels.londonSource}
                </Typography>
              </CardContent>
            </Card>

            {/* Explain the limitation of London ML coverage. */}
            <Alert
              severity="info"
              sx={{ mb: 3 }}
            >
              {labels.londonForecast}
            </Alert>
{/* London Bloomsbury data freshness */}
<Box sx={{ mb: 3 }}>
  <DataFreshnessPanel
    city="london"
    stationId="CLL2"
  />
</Box>
            {/* London Bloomsbury historical measurements
                with preserved source-quality information. */}
            <StationHistoryChart
              city="london"
              stationId="CLL2"
            />
          </Box>
        )}

        {/* =========================================
            BERLIN VS LONDON COMPARISON
            Visible for both city selections.
           ========================================= */}

        <Box sx={{ mt: { xs: 5, md: 7 } }}>
          <Typography
            variant="h4"
            component="h2"
            gutterBottom
            sx={{ fontWeight: 700 }}
          >
            {labels.comparisonHeading}
          </Typography>

          <Typography
            color="text.secondary"
            sx={{ mb: 3 }}
          >
            {labels.comparisonDescription}
          </Typography>

          {/* Historical daily PM2.5 comparison
              from two official monitoring stations. */}
          <CityComparisonChart />
        </Box>

        {/* =========================================
            PHASE 5 — MODEL PERFORMANCE
            Berlin test metrics, persistence baseline,
            station evaluation and limitations.
           ========================================= */}

        <Box sx={{ mt: { xs: 5, md: 7 } }}>
          <Typography
            variant="h4"
            component="h2"
            gutterBottom
            sx={{ fontWeight: 700 }}
          >
            {labels.evaluationHeading}
          </Typography>

          <Typography
            color="text.secondary"
            sx={{ mb: 2 }}
          >
            {labels.evaluationDescription}
          </Typography>

          {/* ModelPerformancePanel includes overall metrics.
              It also includes StationEvaluationChart if
              that component was added in Phase 5. */}
          <ModelPerformancePanel />
        </Box>

        {/* =========================================
            PHASE 6 — DATA TRANSPARENCY
            Official sources, historical data notices,
            model limitations and research disclosures.
           ========================================= */}

        <Box sx={{ mt: { xs: 5, md: 7 } }}>
          <DataTransparencyPanel />
        </Box>
      </Box>
    </Container>
  );
}

export default CitiesPage;
