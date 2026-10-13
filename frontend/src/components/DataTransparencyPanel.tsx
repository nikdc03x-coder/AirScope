
/**
 * AirScope | nik
 * Data transparency and scientific disclosure panel.
 *
 * Explains official data sources, historical timestamps,
 * forecast limitations and evaluation coverage.
 */

import { useTranslation } from "react-i18next";

import {
  Accordion,
  AccordionDetails,
  AccordionSummary,
  Alert,
  Box,
  Chip,
  Stack,
  Typography,
} from "@mui/material";

import ExpandMoreIcon from "@mui/icons-material/ExpandMore";

export default function DataTransparencyPanel() {
  const { i18n } = useTranslation();
  const german = i18n.language.startsWith("de");

  const labels = german
    ? {
        title: "Datenquellen und Transparenz",
        subtitle:
          "Wie AirScope Messwerte und Prognosen verwendet",
        berlinTitle: "Berlin — Umweltbundesamt",
        berlinText:
          "Die historischen PM2,5-Messwerte stammen vom deutschen Umweltbundesamt (UBA). AirScope verwendet gespeicherte stündliche Beobachtungen von zwölf Berliner Messstationen.",
        londonTitle: "London — DEFRA UK-AIR",
        londonText:
          "Die Londoner PM2,5-Messwerte stammen aus dem offiziellen DEFRA UK-AIR-Datenarchiv. Die verfügbaren Qualitätskennzeichnungen werden beibehalten.",
        forecastTitle: "ML-Prognosen",
        forecastText:
          "Die experimentellen Prognosen für Berlin verwenden trainierte Modelle und gespeicherte Messwerte. Sie stellen keine Echtzeitprognosen oder offiziellen Warnungen dar.",
        evaluationTitle: "Modellbewertung",
        evaluationText:
          "Die Berliner Prognosemodelle wurden anhand eines chronologischen Testsatzes und einer Persistenz-Baseline bewertet. Für London liegen noch keine entsprechend validierten Prognoseergebnisse vor.",
        status: "Historische Daten — nicht live",
        warning:
          "AirScope ist ein Forschungsprototyp und kein offizieller Luftqualitätswarndienst.",
      }
    : {
        title: "Data Sources & Transparency",
        subtitle:
          "How AirScope uses observations and predictions",
        berlinTitle: "Berlin — Umweltbundesamt",
        berlinText:
          "Historical PM2.5 measurements come from Germany's Umweltbundesamt (UBA). AirScope uses stored hourly observations from twelve Berlin monitoring stations.",
        londonTitle: "London — DEFRA UK-AIR",
        londonText:
          "London PM2.5 observations come from the official DEFRA UK-AIR archive. Available source quality labels are preserved.",
        forecastTitle: "ML Forecasts",
        forecastText:
          "Experimental Berlin forecasts use trained models and stored observations. They are not real-time forecasts or official alerts.",
        evaluationTitle: "Model Evaluation",
        evaluationText:
          "Berlin forecasting models were evaluated using a chronological test set and a persistence baseline. Equivalent validated forecasting results are not yet available for London.",
        status: "Historical data — not live",
        warning:
          "AirScope is a research prototype, not an official air-quality warning service.",
      };

  const sections = [
    {
      title: labels.berlinTitle,
      description: labels.berlinText,
    },
    {
      title: labels.londonTitle,
      description: labels.londonText,
    },
    {
      title: labels.forecastTitle,
      description: labels.forecastText,
    },
    {
      title: labels.evaluationTitle,
      description: labels.evaluationText,
    },
  ];

  return (
    <Box sx={{ py: 3 }}>
      <Stack spacing={2}>
        <Box>
          <Typography
            variant="h4"
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

        <Chip
          label={labels.status}
          variant="outlined"
          sx={{ alignSelf: "flex-start" }}
        />

        {/* Source and scientific methodology explanations */}
        {sections.map((section) => (
          <Accordion
            key={section.title}
            variant="outlined"
            disableGutters
          >
            <AccordionSummary
              expandIcon={<ExpandMoreIcon />}
            >
              <Typography sx={{ fontWeight: 600 }}>
                {section.title}
              </Typography>
            </AccordionSummary>

            <AccordionDetails>
              <Typography color="text.secondary">
                {section.description}
              </Typography>
            </AccordionDetails>
          </Accordion>
        ))}

        <Alert severity="info">
          {labels.warning}
        </Alert>
      </Stack>
    </Box>
  );
}
