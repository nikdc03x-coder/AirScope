
import { BrowserRouter, Route, Routes } from "react-router";

import MainLayout from "./components/layout/MainLayout";
import HomePage from "./pages/HomePage";
import CitiesPage from "./pages/CitiesPage";
import NotFoundPage from "./pages/NotFoundPage";
// AirScope | nik
// React Router decides which page to display based on the URL.
// MainLayout keeps the same header and footer around every page.

function App() {
  return (
    <BrowserRouter>
      <MainLayout>
        <Routes>
  {/* Homepage */}
  <Route path="/" element={<HomePage />} />

  {/* Supported cities */}
  <Route path="/cities" element={<CitiesPage />} />

  {/* Show this page for every unknown URL. */}
  <Route path="*" element={<NotFoundPage />} />
</Routes>
      </MainLayout>
    </BrowserRouter>
  );
}

export default App;
