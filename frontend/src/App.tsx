
import {
  AppBar,
  Box,
  Button,
  Card,
  CardContent,
  Container,
  CssBaseline,
  Toolbar,
  Typography,
} from "@mui/material";

import AirIcon from "@mui/icons-material/Air";
import ArrowForwardIcon from "@mui/icons-material/ArrowForward";

// AirScope | nik
// This is our first homepage.
// We use Material UI components instead of writing
// custom HTML and CSS for every section.

function App() {
  return (
    <>
      {/* Gives the website a consistent starting style. */}
      <CssBaseline />

      {/* Top navigation bar with our project name. */}
      <AppBar position="static" elevation={0}>
        <Toolbar>
          <AirIcon sx={{ mr: 1 }} />

          <Typography variant="h6" sx={{ flexGrow: 1 }}>
            AirScope
          </Typography>

          {/* Language switching will be added later. */}
          <Button color="inherit" disabled>
            EN / DE
          </Button>
        </Toolbar>
      </AppBar>

      {/* Main content stays centered on large screens. */}
      <Container maxWidth="lg">
        <Box sx={{ py: { xs: 6, md: 10 } }}>
         
{/* AirScope | nik
    This is the main heading of our homepage.
    We use sx to style the text using Material UI.
*/}
<Typography
  variant="h2"
  component="h1"
  sx={{ fontWeight: 700 }}
  gutterBottom
>
  Understand the air.
  <br />
  See what comes next.
</Typography>


          <Typography
            variant="h6"
            color="text.secondary"
            sx={{ maxWidth: 650, mb: 4 }}
          >
            Explore air quality in Germany and the United
            Kingdom. Understand recent measurements and
            discover how pollution may change.
          </Typography>

          {/* Our future city explorer will open from here. */}
          <Button
            variant="contained"
            size="large"
            endIcon={<ArrowForwardIcon />}
            disabled
          >
            Explore Cities
          </Button>

          {/* A preview card describing the first feature. */}
          <Card
            variant="outlined"
            sx={{ mt: 6, maxWidth: 500, borderRadius: 3 }}
          >
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Air Quality Forecasts
              </Typography>

              <Typography color="text.secondary">
                Soon, you will be able to explore recent
                pollution readings and see forecasts for
                Berlin and London.
              </Typography>
            </CardContent>
          </Card>
        </Box>
      </Container>
    </>
  );
}

export default App;
