
import i18n from "i18next";
import { initReactI18next } from "react-i18next";

import en from "./locales/en.json";
import de from "./locales/de.json";

// AirScope | nik
// This file manages the languages supported by AirScope.
// We use English by default and remember the user's choice.

const savedLanguage = localStorage.getItem("airscope-language");

const initialLanguage =
  savedLanguage === "de" ? "de" : "en";

void i18n.use(initReactI18next).init({
  resources: {
    en: { translation: en },
    de: { translation: de },
  },

  lng: initialLanguage,
  fallbackLng: "en",

  interpolation: {
    escapeValue: false,
  },
});

export default i18n;
