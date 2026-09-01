// File: frontend/src/i18n/config.ts
//
// i18next setup. English is the default/fallback language; German is a
// complete localisation loaded from the same namespace files. The selected
// language is a pure presentation preference — it must never influence
// policy data, scores, or recommendations (see docs/LOCALISATION.md).
import i18n from "i18next";
import LanguageDetector from "i18next-browser-languagedetector";
import { initReactI18next } from "react-i18next";

import enAdmin from "@/locales/en/admin.json";
import enAdvisor from "@/locales/en/advisor.json";
import enAuth from "@/locales/en/auth.json";
import enComparison from "@/locales/en/comparison.json";
import enCommon from "@/locales/en/common.json";
import enDashboard from "@/locales/en/dashboard.json";
import enDocuments from "@/locales/en/documents.json";
import enErrors from "@/locales/en/errors.json";
import enHome from "@/locales/en/home.json";
import enInsurance from "@/locales/en/insurance.json";
import enNavigation from "@/locales/en/navigation.json";
import enRecommendation from "@/locales/en/recommendation.json";

import deAdmin from "@/locales/de/admin.json";
import deAdvisor from "@/locales/de/advisor.json";
import deAuth from "@/locales/de/auth.json";
import deComparison from "@/locales/de/comparison.json";
import deCommon from "@/locales/de/common.json";
import deDashboard from "@/locales/de/dashboard.json";
import deDocuments from "@/locales/de/documents.json";
import deErrors from "@/locales/de/errors.json";
import deHome from "@/locales/de/home.json";
import deInsurance from "@/locales/de/insurance.json";
import deNavigation from "@/locales/de/navigation.json";
import deRecommendation from "@/locales/de/recommendation.json";

export const SUPPORTED_LANGUAGES = ["en", "de"] as const;
export type SupportedLanguage = (typeof SUPPORTED_LANGUAGES)[number];

export const LANGUAGE_STORAGE_KEY = "insurecompare.lang";
export const defaultNS = "common" as const;

export const resources = {
  en: {
    common: enCommon,
    navigation: enNavigation,
    insurance: enInsurance,
    comparison: enComparison,
    recommendation: enRecommendation,
    documents: enDocuments,
    auth: enAuth,
    admin: enAdmin,
    errors: enErrors,
    home: enHome,
    dashboard: enDashboard,
    advisor: enAdvisor,
  },
  de: {
    common: deCommon,
    navigation: deNavigation,
    insurance: deInsurance,
    comparison: deComparison,
    recommendation: deRecommendation,
    documents: deDocuments,
    auth: deAuth,
    admin: deAdmin,
    errors: deErrors,
    home: deHome,
    dashboard: deDashboard,
    advisor: deAdvisor,
  },
} as const;

void i18n
  .use(LanguageDetector)
  .use(initReactI18next)
  .init({
    resources,
    fallbackLng: "en",
    supportedLngs: SUPPORTED_LANGUAGES as unknown as string[],
    defaultNS,
    ns: Object.keys(resources.en),
    interpolation: { escapeValue: false },
    detection: {
      order: ["localStorage", "navigator"],
      lookupLocalStorage: LANGUAGE_STORAGE_KEY,
      caches: ["localStorage"],
    },
  });

// Keep <html lang> in sync for accessibility/SEO — screen readers and
// browser translation prompts key off this attribute, not just visible text.
const syncHtmlLang = (lng: string) => {
  document.documentElement.lang = lng.slice(0, 2);
};
i18n.on("languageChanged", syncHtmlLang);
if (i18n.resolvedLanguage) syncHtmlLang(i18n.resolvedLanguage);

export default i18n;
