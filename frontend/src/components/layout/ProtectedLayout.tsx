// File: frontend/src/components/layout/ProtectedLayout.tsx
import { Link, Navigate, Outlet, useLocation } from "react-router-dom";
import { useTranslation } from "react-i18next";

import { useAuthStore } from "@/stores/auth";

import { Header } from "./Header";

export default function ProtectedLayout({ adminOnly = false }: { adminOnly?: boolean }) {
  const location = useLocation();
  const { t } = useTranslation("common");
  const { isAuthenticated, isAdmin } = useAuthStore();

  if (!isAuthenticated()) {
    return <Navigate to="/login" replace state={{ from: location }} />;
  }
  if (adminOnly && !isAdmin()) {
    return <Navigate to="/dashboard" replace />;
  }

  return (
    <div className="flex min-h-full flex-col">
      <Header />
      <main className="flex-1 bg-slate-50">
        <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
          <Outlet />
        </div>
      </main>
      <footer className="border-t border-slate-200 bg-white py-4 text-center text-xs text-slate-500">
        <p>
          {t("footer.tagline")}
          {" · "}
          <Link to="/legal" className="hover:underline">
            {t("footer.legalLink")}
          </Link>
        </p>
      </footer>
    </div>
  );
}
