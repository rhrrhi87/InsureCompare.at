// File: frontend/src/components/layout/PublicLayout.tsx
import { Link, Outlet } from "react-router-dom";
import { useTranslation } from "react-i18next";

import { Header } from "./Header";

export default function PublicLayout() {
  const { t } = useTranslation("common");

  return (
    <div className="flex min-h-full flex-col">
      <Header />
      <main className="flex-1">
        <Outlet />
      </main>
      <footer className="border-t border-slate-200 bg-white py-6 text-center text-xs text-slate-500">
        <p className="font-medium text-slate-600">{t("footer.tagline")}</p>
        <p className="mt-1">
          {t("footer.copyright", { year: new Date().getFullYear() })}
          {" · "}
          <Link to="/legal" className="hover:underline">
            {t("footer.legalLink")}
          </Link>
        </p>
      </footer>
    </div>
  );
}
