// File: frontend/src/components/layout/AdminLayout.tsx
import { NavLink, Outlet } from "react-router-dom";
import { useTranslation } from "react-i18next";

export default function AdminLayout() {
  const { t } = useTranslation("admin");

  const tabs: { to: string; label: string; end?: boolean }[] = [
    { to: "/admin", label: t("nav.dashboard"), end: true },
    { to: "/admin/providers", label: t("nav.providers") },
    { to: "/admin/policies", label: t("nav.policies") },
    { to: "/admin/documents", label: t("nav.documents") },
    { to: "/admin/audit", label: t("nav.audit") },
  ];

  return (
    <div className="space-y-6">
      <nav className="flex gap-1 overflow-x-auto border-b border-slate-200">
        {tabs.map((tab) => (
          <NavLink
            key={tab.to}
            to={tab.to}
            end={tab.end}
            className={({ isActive }) =>
              [
                "whitespace-nowrap border-b-2 px-4 py-2.5 text-sm font-medium transition",
                isActive
                  ? "border-brand-600 text-brand-700"
                  : "border-transparent text-slate-500 hover:text-slate-800",
              ].join(" ")
            }
          >
            {tab.label}
          </NavLink>
        ))}
      </nav>
      <Outlet />
    </div>
  );
}
