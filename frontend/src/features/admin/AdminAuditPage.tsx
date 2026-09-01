// File: frontend/src/features/admin/AdminAuditPage.tsx
import { useQuery } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";

import { adminApi } from "@/api/endpoints";
import { Card, Spinner } from "@/components/ui";
import type { AuditLogEntry } from "@/types/domain";

export default function AdminAuditPage() {
  const { t } = useTranslation("admin");

  const audit = useQuery<AuditLogEntry[]>({
    queryKey: ["admin", "audit", "full"],
    queryFn: () => adminApi.audit(500),
  });

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-slate-900">{t("audit.title")}</h1>

      <Card>
        {audit.isLoading ? (
          <Spinner />
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-slate-200 text-sm">
              <thead>
                <tr className="text-left text-xs uppercase tracking-wide text-slate-500">
                  <th className="px-2 py-2">{t("audit.columns.action")}</th>
                  <th className="px-2 py-2">{t("audit.columns.actor")}</th>
                  <th className="px-2 py-2">{t("audit.columns.entity")}</th>
                  <th className="px-2 py-2">{t("audit.columns.when")}</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {audit.data?.map((a) => (
                  <tr key={a.id}>
                    <td className="px-2 py-3 font-medium text-slate-800">
                      {a.action.replace(/_/g, " ")}
                    </td>
                    <td className="px-2 py-3 text-slate-600">
                      {a.actor_email ?? t("recentActivity.system")}
                    </td>
                    <td className="px-2 py-3 text-slate-500">
                      {a.entity_type ? `${a.entity_type} #${a.entity_id ?? "?"}` : "—"}
                    </td>
                    <td className="px-2 py-3 text-slate-500">
                      {new Date(a.created_at).toISOString().slice(0, 16).replace("T", " ")}
                    </td>
                  </tr>
                ))}
                {audit.data?.length === 0 && (
                  <tr>
                    <td colSpan={4} className="px-2 py-6 text-center text-slate-500">
                      {t("audit.empty")}
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        )}
      </Card>
    </div>
  );
}
