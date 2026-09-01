// File: frontend/src/features/admin/AdminDashboardPage.tsx
import { useQuery } from "@tanstack/react-query";
import {
  Bot,
  ClipboardList,
  Cpu,
  Database,
  UploadCloud,
  Users,
} from "lucide-react";
import { useTranslation } from "react-i18next";

import { adminApi, policyApi } from "@/api/endpoints";
import { Alert, Badge, Card, Spinner, StatCard } from "@/components/ui";
import { ProviderLogo } from "@/components/ui/ProviderLogo";
import { cn } from "@/lib/cn";
import { productLineLabel as translateProductLine } from "@/lib/i18nInsurance";
import type {
  AdminStats,
  AuditLogEntry,
  Policy,
  ProductLine,
  Provider,
  User,
} from "@/types/domain";

export default function AdminDashboardPage() {
  const { t, i18n } = useTranslation(["admin", "insurance", "common"]);
  const stats = useQuery<AdminStats>({ queryKey: ["admin", "stats"], queryFn: adminApi.stats });
  const users = useQuery<User[]>({ queryKey: ["admin", "users"], queryFn: adminApi.users });
  const audit = useQuery<AuditLogEntry[]>({
    queryKey: ["admin", "audit"],
    queryFn: () => adminApi.audit(20),
  });
  const providers = useQuery<Provider[]>({
    queryKey: ["providers"],
    queryFn: policyApi.listProviders,
  });
  const policies = useQuery<Policy[]>({ queryKey: ["policies"], queryFn: () => policyApi.list() });

  if (stats.isLoading) {
    return <Spinner className="h-8 w-8" />;
  }
  if (stats.isError || !stats.data) {
    return <Alert variant="error">{t("errors:generic")}</Alert>;
  }

  const policiesByLine = (policies.data ?? []).reduce<Record<string, number>>((acc, p) => {
    acc[p.product_line] = (acc[p.product_line] ?? 0) + 1;
    return acc;
  }, {});
  const totalPolicies = policies.data?.length ?? 0;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-slate-900">{t("admin:title")}</h1>
        <p className="text-slate-600">{t("admin:subtitle")}</p>
      </div>

      {/* KPI cards */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard label={t("admin:kpi.totalUsers")} value={stats.data.total_users} icon={<Users size={22} />} hint={t("admin:kpi.activeHint")} />
        <StatCard label={t("admin:kpi.totalPolicies")} value={stats.data.total_policies} icon={<Database size={22} />} hint={t("admin:kpi.catalogueHint")} />
        <StatCard label={t("admin:kpi.totalUploads")} value={stats.data.total_uploads} icon={<UploadCloud size={22} />} hint={t("admin:kpi.documentsHint")} />
        <StatCard label={t("admin:kpi.totalRecommendations")} value={stats.data.total_recommendations} icon={<Bot size={22} />} hint={t("admin:kpi.aiHint")} />
      </div>

      {/* User mgmt + recent activity */}
      <div className="grid gap-6 lg:grid-cols-2">
        <Card>
          <h2 className="text-lg font-semibold">{t("admin:userManagement.title")}</h2>
          {users.isLoading && <Spinner className="mt-4" />}
          {users.data?.length === 0 && (
            <p className="mt-4 text-sm text-slate-500">{t("admin:userManagement.empty")}</p>
          )}
          <div className="mt-4 space-y-3">
            {users.data?.slice(0, 6).map((u) => (
              <div key={u.id} className="flex items-center justify-between rounded-lg border border-slate-200 px-4 py-3">
                <div>
                  <p className="font-semibold text-slate-900">{u.full_name ?? "—"}</p>
                  <p className="text-xs text-slate-500">{u.email}</p>
                  <p className="text-[11px] text-slate-500">
                    {t("admin:userManagement.joined", {
                      date: new Date(u.created_at).toISOString().slice(0, 10),
                    })}
                  </p>
                </div>
                <Badge tone={u.role === "admin" ? "high" : "info"}>
                  {u.role.toUpperCase()}
                </Badge>
              </div>
            ))}
          </div>
        </Card>

        <Card>
          <h2 className="text-lg font-semibold">{t("admin:recentActivity.title")}</h2>
          {audit.isLoading && <Spinner className="mt-4" />}
          {audit.data?.length === 0 && (
            <p className="mt-4 text-sm text-slate-500">{t("admin:recentActivity.empty")}</p>
          )}
          <div className="mt-4 space-y-3">
            {audit.data?.slice(0, 8).map((a) => (
              <div key={a.id} className="flex items-start gap-3 border-l-2 border-brand-500 pl-3">
                <ClipboardList size={16} className="mt-1 text-brand-600" />
                <div>
                  <p className="text-sm font-semibold text-slate-800 capitalize">
                    {a.action.replace(/_/g, " ")}
                  </p>
                  <p className="text-xs text-slate-500">
                    {a.actor_email ?? t("admin:recentActivity.system")} ·{" "}
                    {new Date(a.created_at).toISOString().slice(0, 16).replace("T", " ")}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </Card>
      </div>

      {/* Insurers */}
      <Card>
        <h2 className="text-lg font-semibold">
          {t("admin:insurers.title", { count: providers.data?.length ?? 0 })}
        </h2>
        <div className="mt-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-5">
          {providers.data?.map((prov) => {
            const count = (policies.data ?? []).filter((p) => p.provider_id === prov.id).length;
            return (
              <div key={prov.id} className="rounded-lg border border-slate-200 p-4 text-center">
                <ProviderLogo provider={prov} size={28} className="mx-auto" />
                <p className="mt-2 font-semibold text-slate-900">{prov.name}</p>
                <p className="text-xs text-slate-500">{prov.country.toUpperCase()}</p>
                <p className="mt-1 text-xs font-medium text-brand-700">
                  {t("admin:insurers.policiesCount", { count })}
                </p>
              </div>
            );
          })}
        </div>
      </Card>

      {/* Policy distribution */}
      <Card>
        <h2 className="text-lg font-semibold">{t("admin:policyDistribution.title")}</h2>
        <div className="mt-4 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {(["car", "household", "travel", "legal"] as ProductLine[]).map((line) => {
            const count = policiesByLine[line] ?? 0;
            const percent = totalPolicies > 0 ? Math.round((count / totalPolicies) * 100) : 0;
            return (
              <div key={line} className="rounded-lg border border-slate-200 p-4">
                <p className="text-xs uppercase tracking-wide text-slate-500">
                  {translateProductLine(t, i18n.language, line)}
                </p>
                <p className="mt-1 text-2xl font-bold text-slate-900">{count}</p>
                <div className="mt-2 h-1.5 w-full rounded-full bg-slate-200">
                  <div
                    className={cn("h-1.5 rounded-full bg-brand-600")}
                    style={{ width: `${percent}%` }}
                  />
                </div>
                <p className="mt-1 text-xs text-slate-500">
                  {t("admin:policyDistribution.ofTotal", { percent })}
                </p>
              </div>
            );
          })}
        </div>
      </Card>

      {/* System info footer */}
      <Card className="bg-slate-100">
        <div className="flex flex-wrap items-center justify-between gap-3 text-xs text-slate-600">
          <span className="inline-flex items-center gap-1">
            <Cpu size={14} /> {t("admin:systemInfo.title")}
          </span>
          <span><strong>{t("admin:systemInfo.version")}:</strong> 1.0.0</span>
          <span><strong>{t("admin:systemInfo.environment")}:</strong> {import.meta.env.MODE}</span>
          <span>
            <strong>{t("admin:systemInfo.lastUpdated")}:</strong>{" "}
            {new Date().toISOString().slice(0, 10)}
          </span>
        </div>
      </Card>
    </div>
  );
}
