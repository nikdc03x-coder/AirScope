
/**
 * AirScope | nik
 * Main city dashboard for Berlin and London.
 *
 * Berlin: historical PM2.5 and experimental ML forecasts.
 * London: official PM2.5 observations and quality information.
 * Comparison: historical PM2.5 trends from both cities.
 */

import { useState } from "react";
import { useTranslation } from "react-i18next";

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

// AirScope dashboard components.
import BerlinForecastPanel from "../components/BerlinForecastPanel";
import StationHistoryChart from "../components/StationHistoryChart";
import CityComparisonChart from "../components/CityComparisonChart";

// Only the supported AirScope cities can be selected.
type City = "berlin" | "london";

function CitiesPage() {
  const { t, i18n } = useTranslation();

  const german = i18n.language.startsWith("de");

  // Berlin is the default because validated forecast models
  // are currently available only for Berlin.
  const [selectedCity, setSelectedCity] = useState<City>("berlin");

  // English and German dashboard labels.
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
          "Für London sind derzeit keine validierten KI-Prognosen verfügbar. Die historischen Messwerte können bereits untersucht werden.",

        comparisonHeading: "Städtevergleich",

        comparisonDescription:
          "Vergleichen Sie historische PM2,5-Messwerte aus Berlin und London.",
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
          "Validated AI forecasts are not yet available for London. You can still explore its historical observations.",

        comparisonHeading: "City Comparison",

        comparisonDescription:
          "Compare historical PM2.5 measurements from Berlin and London.",
      };

  return (
    <Container maxWidth="lg">
      <Box sx={{ py: { xs: 5, md: 8 } }}>
        {/* =========================================
            PAGE HEADING
            Existing translation keys are preserved.
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
            // Prevent the selection from becoming empty.
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
            Official historical measurements and
            experimental 6h, 12h, 24h ML forecasts.
           ========================================= */}

        {selectedCity === "berlin" && (
          <Box>
            {/* Berlin city information */}
            <Card
              variant="outlined"
              sx={{ mb: 3 }}
            >
              <CardContent>
                <Typography
                  variant="h5"
                  sx={{ fontWeight: 700 }}
                  gutterBottom
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

            {/* Berlin monitoring station selection,
                ML forecasts and historical chart. */}
            <BerlinForecastPanel />
          </Box>
        )}

        {/* =========================================
            LONDON DASHBOARD
            Verified DEFRA historical observations.
            London ML forecasts are not available yet.
           ========================================= */}

        {selectedCity === "london" && (
          <Box>
            {/* London city information */}
            <Card
              variant="outlined"
              sx={{ mb: 3 }}
            >
              <CardContent>
                <Typography
                  variant="h5"
                  sx={{ fontWeight: 700 }}
                  gutterBottom
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

            {/* Explain that London forecasts have
                not yet been independently validated. */}
            <Alert
              severity="info"
              sx={{ mb: 3 }}
            >
              {labels.londonForecast}
            </Alert>

            {/* London Bloomsbury historical observations.
                Includes quality-status information. */}
            <StationHistoryChart
              city="london"
              stationId="CLL2"
            />
          </Box>
        )}

        {/* =========================================
            BERLIN VS LONDON COMPARISON
            Visible regardless of selected city.

            Uses official historical observations
            from both cities, aligned by UTC date.
           ========================================= */}

        <Box sx={{ mt: { xs: 5, md: 7 } }}>
          <Typography
            variant="h4"
            component="h2"
            gutterBottom
            sx={{
              fontWeight: 700,
            }}
          >
            {labels.comparisonHeading}
          </Typography>

          <Typography
            color="text.secondary"
            sx={{ mb: 3 }}
          >
            {labels.comparisonDescription}
          </Typography>

          {/* Shared Berlin–London historical comparison.
              Includes its own 7D/30D range selector. */}
          <CityComparisonChart />
        </Box>
      </Box>
    </Container>
  );
}

export default CitiesPage;
