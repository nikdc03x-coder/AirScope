
import type { ReactNode } from "react";
import { Box } from "@mui/material";

import Header from "./Header";
import Footer from "./Footer";

// AirScope | nik
// MainLayout gives every page the same header and footer.
// The children property represents the page content
// displayed between them.

type MainLayoutProps = {
  children: ReactNode;
};

function MainLayout({ children }: MainLayoutProps) {
  return (
    <Box
      sx={{
        display: "flex",
        flexDirection: "column",
        minHeight: "100vh",
      }}
    >
      {/* Shared navigation bar. */}
      <Header />

      {/* The current page fills the available space. */}
      <Box component="main" sx={{ flexGrow: 1 }}>
        {children}
      </Box>

      {/* Shared footer stays below the page content. */}
      <Footer />
    </Box>
  );
}

export default MainLayout;
