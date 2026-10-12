
import { BrowserRouter, Route, Routes } from "react-router";

import MainLayout from "./components/layout/MainLayout";
import HomePage from "./pages/HomePage";
import CitiesPage from "./pages/CitiesPage";
// AirScope | nik
// React Router decides which page to display based on the URL.
// MainLayout keeps the same header and footer around every page.

function App() {
  return (
    <BrowserRouter>
      <MainLayout>
        <Routes>
  <Route path="/" element={<HomePage />} />
  <Route path="/cities" element={<CitiesPage />} />
</Routes>
      </MainLayout>
    </BrowserRouter>
  );
}

export default App;
