
import {
  AppBar,
  Box,
  Button,
  Card,
  CardContent,
  Container,
  Toolbar,
  Typography,
} from "@mui/material";

import AirIcon from "@mui/icons-material/Air";
import ArrowForwardIcon from "@mui/icons-material/ArrowForward";

import { useTranslation } from "react-i18next";

import LanguageSwitcher from "./components/layout/LanguageSwitcher";

// AirScope | nik
// All visible text comes from our translation files.
// This allows the same page to work in English and German.

function App() {
  const { t } = useTranslation();

  return (
    <>
      {/* Shared navigation bar. */}
      <AppBar position="static" elevation={0}>
        <Toolbar>
          <AirIcon sx={{ mr: 1 }} />

          <Typography variant="h6" sx={{ flexGrow: 1 }}>
            {t("brand")}
          </Typography>

          <LanguageSwitcher />
        </Toolbar>
      </AppBar>

      {/* Homepage introduction. */}
      <Container maxWidth="lg">
        <Box sx={{ py: { xs: 6, md: 10 } }}>
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

          <Typography
            variant="h6"
            color="text.secondary"
            sx={{ maxWidth: 650, mb: 4 }}
          >
            {t("hero.description")}
          </Typography>

          {/* City exploration will be implemented later. */}
          <Button
            variant="contained"
            size="large"
            endIcon={<ArrowForwardIcon />}
            disabled
          >
            {t("hero.explore")}
          </Button>

          {/* Preview of our upcoming forecast feature. */}
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
    </>
  );
}

export default App;
