// File: frontend/src/components/layout/Header.tsx
import { Link, NavLink } from "react-router-dom";
import { LogOut, Shield } from "lucide-react";
import { useTranslation } from "react-i18next";

import { Button } from "@/components/ui/Button";
import { useLogout } from "@/features/auth/useAuth";
import { useAuthStore } from "@/stores/auth";

import { LanguageSwitcher } from "./LanguageSwitcher";

export function Header() {
  const { t } = useTranslation(["navigation", "common"]);
  const { user, isAuthenticated, isAdmin } = useAuthStore();
  const logout = useLogout();
  const authed = isAuthenticated();

  return (
    <header className="border-b border-slate-200 bg-white">
      <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-4 sm:px-6 lg:px-8">
        <Link to="/" className="flex items-center gap-2 font-semibold text-slate-900">
          <span className="grid h-9 w-9 place-items-center rounded-lg bg-brand-600 text-white">
            <Shield size={18} />
          </span>
          <span className="text-lg">
            InsureCompare<span className="text-brand-600">.at</span>
            {isAdmin() ? (
              <span className="ml-2 text-sm font-normal text-slate-500">
                - {t("navigation:adminBadge")}
              </span>
            ) : null}
          </span>
        </Link>

        <nav className="hidden gap-6 text-sm font-medium text-slate-600 md:flex">
          {authed && !isAdmin() && (
            <>
              <NavLink to="/dashboard" className={({ isActive }) =>
                isActive ? "text-brand-700" : "hover:text-slate-900"}>
                {t("navigation:dashboard")}
              </NavLink>
              <NavLink to="/upload" className={({ isActive }) =>
                isActive ? "text-brand-700" : "hover:text-slate-900"}>
                {t("navigation:uploadPolicy")}
              </NavLink>
              <NavLink to="/recommendations" className={({ isActive }) =>
                isActive ? "text-brand-700" : "hover:text-slate-900"}>
                {t("navigation:recommendations")}
              </NavLink>
              <NavLink to="/compare" className={({ isActive }) =>
                isActive ? "text-brand-700" : "hover:text-slate-900"}>
                {t("navigation:compare")}
              </NavLink>
            </>
          )}
          {authed && isAdmin() && (
            <NavLink to="/admin" className="hover:text-slate-900">
              {t("navigation:adminDashboard")}
            </NavLink>
          )}
          {!authed && (
            <>
              <Link to="/#types" className="hover:text-slate-900">
                {t("navigation:insuranceTypes")}
              </Link>
              <Link to="/#how-it-works" className="hover:text-slate-900">
                {t("navigation:howItWorks")}
              </Link>
              <Link to="/#why" className="hover:text-slate-900">
                {t("navigation:whyInsureCompare")}
              </Link>
              <Link to="/#about" className="hover:text-slate-900">
                {t("navigation:about")}
              </Link>
            </>
          )}
        </nav>

        <div className="flex items-center gap-4">
          <LanguageSwitcher />
          {authed ? (
            <>
              <span className="hidden text-sm text-slate-600 md:inline">
                {t("navigation:welcome", { name: user?.full_name ?? user?.email ?? "" })}
              </span>
              <Button variant="ghost" size="sm" onClick={logout}>
                <LogOut size={16} className="mr-1.5" />
                {t("common:actions.signOut")}
              </Button>
            </>
          ) : (
            <>
              <Link to="/login" className="text-sm font-medium text-slate-600 hover:text-slate-900">
                {t("navigation:login")}
              </Link>
              <Link to="/register">
                <Button size="sm">{t("navigation:register")}</Button>
              </Link>
            </>
          )}
        </div>
      </div>
    </header>
  );
}
