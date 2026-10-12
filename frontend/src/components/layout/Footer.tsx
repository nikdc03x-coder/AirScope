
import { Box, Container, Typography } from "@mui/material";
import { useTranslation } from "react-i18next";

// AirScope | nik
// This footer is shared across the website.
// It uses Material UI for styling and supports both languages.

function Footer() {
  const { t } = useTranslation();

  return (
    <Box
      component="footer"
      sx={{
        mt: "auto",
        py: 3,
        borderTop: 1,
        borderColor: "divider",
        bgcolor: "background.paper",
      }}
    >
      <Container maxWidth="lg">
        <Box
          sx={{
            display: "flex",
            flexDirection: { xs: "column", sm: "row" },
            justifyContent: "space-between",
            alignItems: { xs: "center", sm: "flex-start" },
            gap: 1,
          }}
        >
          {/* Project name and tagline. */}
          <Typography variant="body2" color="text.secondary">
            {t("footer.brand")}
          </Typography>

          {/* A reminder that forecasts are estimates. */}
          <Typography
            variant="body2"
            color="text.secondary"
            sx={{ textAlign: { xs: "center", sm: "right" } }}
          >
            {t("footer.disclaimer")}
          </Typography>
        </Box>
      </Container>
    </Box>
  );
}

export default Footer;
