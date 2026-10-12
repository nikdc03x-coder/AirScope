
import {
  Box,
  Button,
  Card,
  CardContent,
  Container,
  Typography,
} from "@mui/material";

import ArrowForwardIcon from "@mui/icons-material/ArrowForward";
import { useTranslation } from "react-i18next";

import MainLayout from "./components/layout/MainLayout";

// AirScope | nik
// This is the main component of our website.
// MainLayout automatically adds the header and footer.
// All visible text comes from our translation files.

function App() {
  const { t } = useTranslation();

  return (
    <MainLayout>
      {/* Main homepage content. */}
      <Container maxWidth="lg">
        <Box sx={{ py: { xs: 6, md: 10 } }}>
          {/* Main heading of the AirScope homepage. */}
          <Typography
            variant="h2"
            component="h1"
            sx={{
              fontWeight: 700,
              fontSize: { xs: "2.5rem", md: "3.75rem" },
            }}
            gutterBottom
          >
            {t("hero.titleLine1")}
            <br />
            {t("hero.titleLine2")}
          </Typography>

          {/* Short introduction explaining AirScope. */}
          <Typography
            variant="h6"
            color="text.secondary"
            sx={{ maxWidth: 650, mb: 4 }}
          >
            {t("hero.description")}
          </Typography>

          {/* City exploration will be enabled when
              the city pages are implemented. */}
          <Button
            variant="contained"
            size="large"
            endIcon={<ArrowForwardIcon />}
            disabled
          >
            {t("hero.explore")}
          </Button>

          {/* Preview of our upcoming air quality forecasts. */}
          <Card
            variant="outlined"
            sx={{ mt: 6, maxWidth: 500 }}
          >
            <CardContent>
              <Typography variant="h6" gutterBottom>
                {t("forecast.title")}
              </Typography>

              <Typography color="text.secondary">
                {t("forecast.description")}
              </Typography>
            </CardContent>
          </Card>
        </Box>
      </Container>
    </MainLayout>
  );
}

export default App;
