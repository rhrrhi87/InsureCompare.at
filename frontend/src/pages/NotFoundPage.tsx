// File: frontend/src/pages/NotFoundPage.tsx
import { Link } from "react-router-dom";
import { useTranslation } from "react-i18next";

import { Button } from "@/components/ui/Button";

export default function NotFoundPage() {
  const { t } = useTranslation(["errors", "common"]);
  return (
    <div className="mx-auto flex min-h-[60vh] max-w-md flex-col items-center justify-center text-center">
      <p className="text-7xl font-extrabold text-brand-600">{t("errors:notFound.code")}</p>
      <h1 className="mt-2 text-2xl font-bold text-slate-900">{t("errors:notFound.title")}</h1>
      <p className="mt-1 text-slate-500">{t("errors:notFound.body")}</p>
      <Link to="/" className="mt-6">
        <Button>{t("common:actions.backToHome")}</Button>
      </Link>
    </div>
  );
}
