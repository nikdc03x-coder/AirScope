
import { createTheme } from "@mui/material/styles";

// AirScope | nik
// This file controls the overall look of our website.
// By keeping colors and styles here, we avoid repeating
// the same design code in every component.

const theme = createTheme({
  palette: {
    mode: "light",

    // Main brand color used for buttons and navigation.
    primary: {
      main: "#176B91",
      light: "#4A9AB8",
      dark: "#104C69",
    },

    // Secondary color for smaller design accents.
    secondary: {
      main: "#269B83",
    },

    // Soft background colors for a clean appearance.
    background: {
      default: "#F5F8FB",
      paper: "#FFFFFF",
    },

    text: {
      primary: "#172B3A",
      secondary: "#607584",
    },
  },

  // Rounded corners give cards and buttons a modern look.
  shape: {
    borderRadius: 12,
  },

  typography: {
    fontFamily: "Inter, Arial, sans-serif",

    h2: {
      fontWeight: 700,
    },

    h6: {
      fontWeight: 600,
    },

    button: {
      textTransform: "none",
      fontWeight: 600,
    },
  },

  // Customize existing MUI components in one place.
  components: {
    MuiButton: {
      styleOverrides: {
        root: {
          borderRadius: 10,
          paddingLeft: 20,
          paddingRight: 20,
        },
      },
    },

    MuiCard: {
      styleOverrides: {
        root: {
          borderRadius: 16,
        },
      },
    },
  },
});

export default theme;
