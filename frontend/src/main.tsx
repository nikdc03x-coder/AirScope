
import React from "react";
import ReactDOM from "react-dom/client";

import App from "./App";

// AirScope | nik
// This file starts our React application.
// It connects the App component to the HTML page.

ReactDOM.createRoot(
  document.getElementById("root")!
).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
