
import {
  Box,
  Card,
  CardContent,
  Container,
  Grid,
  Typography,
} from "@mui/material";

import { useTranslation } from "react-i18next";

// AirScope | nik
// This page introduces the cities supported by AirScope.
// Actual pollution measurements will come from our data pipeline later.

const cities = [
  { id: "berlin", country: "Germany" },
  { id: "london", country: "United Kingdom" },
];

function CitiesPage() {
  const { t } = useTranslation();

  return (
    <Container maxWidth="lg">
      <Box sx={{ py: { xs: 5, md: 8 } }}>
        <Typography variant="h3" component="h1" gutterBottom>
          {t("cities.title")}
        </Typography>

        <Typography color="text.secondary" sx={{ mb: 4 }}>
          {t("cities.description")}
        </Typography>

        <Grid container spacing={3}>
          {cities.map((city) => (
            <Grid key={city.id} size={{ xs: 12, md: 6 }}>
              <Card variant="outlined" sx={{ height: "100%" }}>
                <CardContent>
                  <Typography variant="h5" gutterBottom>
                    {t(`cities.${city.id}`)}
                  </Typography>

                  <Typography color="text.secondary">
                    {t(`cities.${city.id}Country`)}
                  </Typography>

                  <Typography
                    variant="body2"
                    color="text.secondary"
                    sx={{ mt: 2 }}
                  >
                    {t("cities.comingSoon")}
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
          ))}
        </Grid>
      </Box>
    </Container>
  );
}

export default CitiesPage;
