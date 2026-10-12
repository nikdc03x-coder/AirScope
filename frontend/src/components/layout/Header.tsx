
import {
  AppBar,
  Box,
  Container,
  Toolbar,
  Typography,
} from "@mui/material";

import AirIcon from "@mui/icons-material/Air";
import { useTranslation } from "react-i18next";

import LanguageSwitcher from "./LanguageSwitcher";

// AirScope | nik
// This header appears at the top of our website.
// Keeping it separate allows us to reuse it on every page.

function Header() {
  const { t } = useTranslation();

  return (
    <AppBar position="static" elevation={0}>
      <Container maxWidth="lg">
        <Toolbar disableGutters sx={{ minHeight: 72 }}>
          {/* Brand icon and project name. */}
          <Box
            sx={{
              display: "flex",
              alignItems: "center",
              gap: 1,
              flexGrow: 1,
            }}
          >
            <AirIcon fontSize="medium" />

            <Typography
              variant="h6"
              component="span"
              sx={{ fontWeight: 700 }}
            >
              {t("brand")}
            </Typography>
          </Box>

          {/* Reuse our existing language switcher. */}
          <LanguageSwitcher />
        </Toolbar>
      </Container>
    </AppBar>
  );
}

export default Header;
