
import React from "react";
import ReactDOM from "react-dom/client";

import { CssBaseline, ThemeProvider } from "@mui/material";

import App from "./App";
import theme from "./app/theme";
// Initialize translations before the homepage renders.
import "./i18n";

// AirScope | nik
// ThemeProvider applies our shared colors and styles
// to every Material UI component in the application.
//
// CssBaseline removes inconsistent browser default styles.

ReactDOM.createRoot(
  document.getElementById("root")!
).render(
  <React.StrictMode>
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <App />
    </ThemeProvider>
  </React.StrictMode>
);
