
import { BrowserRouter, Route, Routes } from "react-router";

import MainLayout from "./components/layout/MainLayout";
import HomePage from "./pages/HomePage";

// AirScope | nik
// React Router decides which page to display based on the URL.
// MainLayout keeps the same header and footer around every page.

function App() {
  return (
    <BrowserRouter>
      <MainLayout>
        <Routes>
          {/* Show our homepage at the main website address. */}
          <Route path="/" element={<HomePage />} />
        </Routes>
      </MainLayout>
    </BrowserRouter>
  );
}

export default App;
