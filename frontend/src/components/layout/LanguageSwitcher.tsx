
import { Button, ButtonGroup } from "@mui/material";
import { useTranslation } from "react-i18next";

// AirScope | nik
// This component switches the website language.
// The selected language is saved so it stays the same
// after the user refreshes the page.

function LanguageSwitcher() {
  const { i18n } = useTranslation();

  const currentLanguage =
    i18n.resolvedLanguage === "de" ? "de" : "en";

  const changeLanguage = (language: "en" | "de") => {
    // Update the visible translations.
    void i18n.changeLanguage(language);

    // Remember the language for future visits.
    localStorage.setItem("airscope-language", language);
  };

  return (
    <ButtonGroup size="small" aria-label="Website language">
      <Button
        color="inherit"
        variant={currentLanguage === "en" ? "contained" : "outlined"}
        onClick={() => changeLanguage("en")}
        aria-pressed={currentLanguage === "en"}
      >
        EN
      </Button>

      <Button
        color="inherit"
        variant={currentLanguage === "de" ? "contained" : "outlined"}
        onClick={() => changeLanguage("de")}
        aria-pressed={currentLanguage === "de"}
      >
        DE
      </Button>
    </ButtonGroup>
  );
}

export default LanguageSwitcher;
