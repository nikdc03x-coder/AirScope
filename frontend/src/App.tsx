
import MainLayout from "./components/layout/MainLayout";
import HomePage from "./pages/HomePage";

// AirScope | nik
// App connects the shared website layout to the homepage.
// Later, a router will decide which page to display.

function App() {
  return (
    <MainLayout>
      <HomePage />
    </MainLayout>
  );
}

export default App;
