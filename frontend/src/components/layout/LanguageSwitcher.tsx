// File: frontend/src/components/layout/LanguageSwitcher.tsx
import { useTranslation } from "react-i18next";

import { SUPPORTED_LANGUAGES, type SupportedLanguage } from "@/i18n/config";
import { cn } from "@/lib/cn";

/**
 * EN | DE switcher. Changing language only swaps UI copy (react-i18next
 * resource bundle) — it never touches policy data, scores or
 * recommendations, which are language-independent domain state.
 */
export function LanguageSwitcher() {
  const { i18n, t } = useTranslation();
  const current = (i18n.resolvedLanguage ?? i18n.language ?? "en").slice(
    0,
    2,
  ) as SupportedLanguage;

  return (
    <div
      className="flex items-center gap-1 text-sm font-medium"
      aria-label={t("language.switchTo")}
      role="group"
    >
      {SUPPORTED_LANGUAGES.map((lng, idx) => (
        <span key={lng} className="flex items-center gap-1">
          <button
            type="button"
            onClick={() => void i18n.changeLanguage(lng)}
            aria-pressed={current === lng}
            className={cn(
              "rounded px-1 py-0.5 uppercase transition",
              current === lng
                ? "font-semibold text-brand-700"
                : "text-slate-500 hover:text-slate-600",
            )}
          >
            {lng}
          </button>
          {idx < SUPPORTED_LANGUAGES.length - 1 && (
            <span className="text-slate-300" aria-hidden="true">
              |
            </span>
          )}
        </span>
      ))}
    </div>
  );
}
