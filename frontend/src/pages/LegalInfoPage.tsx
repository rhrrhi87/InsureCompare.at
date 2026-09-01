// File: frontend/src/pages/LegalInfoPage.tsx
import { useTranslation } from "react-i18next";
import { Link } from "react-router-dom";

export default function LegalInfoPage() {
  const { t } = useTranslation("common");

  return (
    <div className="mx-auto max-w-2xl px-4 py-16 sm:px-6 lg:px-8">
      <h1 className="text-2xl font-bold text-slate-900">{t("legal.title")}</h1>
      <p className="mt-4 text-sm text-slate-700">{t("legal.intro")}</p>
      <p className="mt-4 text-sm text-slate-600">{t("legal.notice")}</p>
      <Link to="/" className="mt-8 inline-block text-sm text-brand-600 hover:underline">
        ← {t("actions.backToHome")}
      </Link>
    </div>
  );
}
