
import {
  AppBar,
  Box,
  Button,
  Container,
  Toolbar,
  Typography,
} from "@mui/material";

import AirIcon from "@mui/icons-material/Air";

import { NavLink } from "react-router";
import { useTranslation } from "react-i18next";

import LanguageSwitcher from "./LanguageSwitcher";

// AirScope | nik
// This header is shared across all pages.
// React Router handles navigation without refreshing the website.

function Header() {
  const { t } = useTranslation();

  return (
    <AppBar position="static" elevation={0}>
      <Container maxWidth="lg">
        <Toolbar
          disableGutters
          sx={{
            minHeight: 72,
            gap: 2,
            flexWrap: "wrap",
            py: 1,
          }}
        >
          {/* Project logo and name. */}
          <Box
            sx={{
              display: "flex",
              alignItems: "center",
              gap: 1,
              flexGrow: 1,
            }}
          >
            <AirIcon />

            <Typography
              variant="h6"
              component="span"
              sx={{ fontWeight: 700 }}
            >
              {t("brand")}
            </Typography>
          </Box>

          {/* Main navigation links. */}
          <Box
            component="nav"
            aria-label="Main navigation"
            sx={{
              display: "flex",
              alignItems: "center",
              gap: 1,
            }}
          >
            <Button
              component={NavLink}
              to="/"
              end
              color="inherit"
              sx={{
                "&.active": {
                  bgcolor: "rgba(255,255,255,0.18)",
                },
              }}
            >
              {t("navigation.home")}
            </Button>

            <Button
              component={NavLink}
              to="/cities"
              color="inherit"
              sx={{
                "&.active": {
                  bgcolor: "rgba(255,255,255,0.18)",
                },
              }}
            >
              {t("navigation.cities")}
            </Button>
          </Box>

          {/* Existing English/German language switcher. */}
          <LanguageSwitcher />
        </Toolbar>
      </Container>
    </AppBar>
  );
}

export default Header;
