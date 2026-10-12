
import {
  Box,
  Button,
  Container,
  Typography,
} from "@mui/material";

import HomeIcon from "@mui/icons-material/Home";
import { Link as RouterLink } from "react-router";
import { useTranslation } from "react-i18next";

// AirScope | nik
// This page appears when someone visits an unknown URL.
// It provides a clear message and a way back to the homepage.

function NotFoundPage() {
  const { t } = useTranslation();

  return (
    <Container maxWidth="md">
      <Box
        sx={{
          py: { xs: 8, md: 12 },
          textAlign: "center",
        }}
      >
        {/* Standard HTTP-style error number. */}
        <Typography
          variant="h1"
          component="h1"
          sx={{
            fontWeight: 800,
            color: "primary.main",
          }}
        >
          404
        </Typography>

        {/* Explain the problem in the selected language. */}
        <Typography variant="h4" sx={{ mt: 2, mb: 2 }}>
          {t("notFound.title")}
        </Typography>

        <Typography
          color="text.secondary"
          sx={{ mb: 4 }}
        >
          {t("notFound.description")}
        </Typography>

        {/* Return to the homepage without reloading. */}
        <Button
          component={RouterLink}
          to="/"
          variant="contained"
          startIcon={<HomeIcon />}
        >
          {t("notFound.backHome")}
        </Button>
      </Box>
    </Container>
  );
}

export default NotFoundPage;
