// File: frontend/src/features/admin/AdminDocumentsPage.tsx
import { useQuery } from "@tanstack/react-query";
import { AlertTriangle } from "lucide-react";
import { useTranslation } from "react-i18next";

import { adminApi } from "@/api/endpoints";
import { Badge, Card, Spinner } from "@/components/ui";
import { formatBytes, formatPercent } from "@/lib/format";
import type { UploadOut } from "@/types/domain";

export default function AdminDocumentsPage() {
  const { t } = useTranslation(["admin", "documents"]);

  const uploads = useQuery<UploadOut[]>({
    queryKey: ["admin", "uploads"],
    queryFn: () => adminApi.uploads(200),
  });

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-slate-900">{t("admin:documents.title")}</h1>

      <Card>
        {uploads.isLoading ? (
          <Spinner />
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-slate-200 text-sm">
              <thead>
                <tr className="text-left text-xs uppercase tracking-wide text-slate-500">
                  <th className="px-2 py-2">{t("admin:documents.columns.user")}</th>
                  <th className="px-2 py-2">{t("admin:documents.columns.filename")}</th>
                  <th className="px-2 py-2">{t("admin:documents.columns.status")}</th>
                  <th className="px-2 py-2">{t("admin:documents.columns.confidence")}</th>
                  <th className="px-2 py-2">{t("admin:documents.columns.uploaded")}</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {uploads.data?.map((u) => (
                  <tr key={u.id}>
                    <td className="px-2 py-3 text-slate-600">#{u.user_id}</td>
                    <td className="px-2 py-3">
                      <p className="font-medium text-slate-800">{u.filename}</p>
                      <p className="text-xs text-slate-500">{formatBytes(u.size_bytes)}</p>
                    </td>
                    <td className="px-2 py-3">
                      <Badge
                        tone={
                          u.status === "ready" ? "low" : u.status === "failed" ? "high" : "info"
                        }
                      >
                        {t(`documents:status.${u.status}`)}
                      </Badge>
                    </td>
                    <td className="px-2 py-3">
                      {u.ocr_confidence != null ? (
                        <span
                          className={
                            u.ocr_confidence < 70
                              ? "inline-flex items-center gap-1 text-amber-600"
                              : "text-slate-700"
                          }
                        >
                          {u.ocr_confidence < 70 && <AlertTriangle size={14} />}
                          {formatPercent(u.ocr_confidence / 100)}
                        </span>
                      ) : (
                        "—"
                      )}
                    </td>
                    <td className="px-2 py-3 text-slate-500">
                      {new Date(u.created_at).toISOString().slice(0, 16).replace("T", " ")}
                    </td>
                  </tr>
                ))}
                {uploads.data?.length === 0 && (
                  <tr>
                    <td colSpan={5} className="px-2 py-6 text-center text-slate-500">
                      —
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
