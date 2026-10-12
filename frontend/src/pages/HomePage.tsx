
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
import { Link as RouterLink } from "react-router";

// AirScope | nik
// HomePage contains the content shown on our landing page.
// Keeping it separate makes future navigation easier.

function HomePage() {
  const { t } = useTranslation();

  return (
    <Container maxWidth="lg">
      <Box sx={{ py: { xs: 6, md: 10 } }}>
        {/* Main heading introducing AirScope. */}
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

        {/* Explain the purpose of our platform. */}
        <Typography
          variant="h6"
          color="text.secondary"
          sx={{ maxWidth: 650, mb: 4 }}
        >
          {t("hero.description")}
        </Typography>

        {/* AirScope | nik
            Navigate to the Cities page using React Router.
            The page changes without a full browser reload.
        */}
        <Button
          component={RouterLink}
          to="/cities"
          variant="contained"
          size="large"
          endIcon={<ArrowForwardIcon />}
        >
          {t("hero.explore")}
        </Button>

        {/* Preview of our upcoming forecasting feature. */}
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
  );
}

export default HomePage;
