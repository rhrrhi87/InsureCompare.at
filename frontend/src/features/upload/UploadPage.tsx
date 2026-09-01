// File: frontend/src/features/upload/UploadPage.tsx
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { CheckCircle2, FileText, Upload as UploadIcon, XCircle } from "lucide-react";
import { useCallback } from "react";
import { useDropzone } from "react-dropzone";
import { useTranslation } from "react-i18next";

import { extractErrorMessage } from "@/api/client";
import { uploadApi } from "@/api/endpoints";
import { Alert, Badge, Card, CardSubtitle, CardTitle, Spinner } from "@/components/ui";
import { AdvisorPanel } from "@/features/advisor/AdvisorPanel";
import { cn } from "@/lib/cn";
import { formatBytes, formatEur, formatPercent } from "@/lib/format";
import { translateConcept } from "@/lib/i18nInsurance";
import type { UploadOut, UploadStatus } from "@/types/domain";

export default function UploadPage() {
  const { t } = useTranslation("documents");
  const qc = useQueryClient();

  const list = useQuery<UploadOut[]>({
    queryKey: ["uploads"],
    queryFn: uploadApi.list,
  });

  const upload = useMutation({
    mutationFn: (file: File) => uploadApi.upload(file),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["uploads"] }),
  });

  const onDrop = useCallback(
    (files: File[]) => {
      if (files[0]) upload.mutate(files[0]);
    },
    [upload],
  );

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    multiple: false,
    accept: {
      "application/pdf": [".pdf"],
      "image/jpeg": [".jpg", ".jpeg"],
      "image/png": [".png"],
    },
    maxSize: 10 * 1024 * 1024,
    disabled: upload.isPending,
  });

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-slate-900">{t("title")}</h1>
        <p className="text-slate-600">{t("subtitle")}</p>
      </div>

      <Card>
        <div
          {...getRootProps()}
          className={cn(
            "flex cursor-pointer flex-col items-center justify-center rounded-xl border-2 border-dashed border-slate-300 bg-slate-50 px-6 py-12 text-center transition",
            isDragActive && "border-brand-500 bg-brand-50",
            upload.isPending && "pointer-events-none opacity-70",
          )}
        >
          <input {...getInputProps()} aria-label={t("title")} />
          <UploadIcon size={36} className="text-slate-400" />
          <p className="mt-3 font-medium text-slate-800">
            {isDragActive ? t("dropzone.active") : t("dropzone.idle")}
          </p>
          <p className="mt-1 text-xs text-slate-500">{t("dropzone.hint")}</p>
        </div>
        {upload.isPending && (
          <div className="mt-4 flex items-center gap-2 text-sm text-slate-600">
            <Spinner /> {t("processing")}
          </div>
        )}
        {upload.isError && (
          <div className="mt-4">
            <Alert variant="error">{extractErrorMessage(upload.error)}</Alert>
          </div>
        )}
      </Card>

      <Card>
        <CardTitle>{t("recentUploads")}</CardTitle>
        <CardSubtitle>{t("recentUploadsHint")}</CardSubtitle>
        <div className="mt-4 divide-y divide-slate-200">
          {(list.data ?? []).length === 0 && !list.isLoading ? (
            <p className="py-8 text-center text-sm text-slate-500">{t("empty")}</p>
          ) : null}
          {list.data?.map((u) => (
            <UploadRow key={u.id} item={u} />
          ))}
        </div>
      </Card>
    </div>
  );
}

function UploadRow({ item }: { item: UploadOut }) {
  return (
    <div className="flex items-start gap-4 py-4">
      <FileText className="mt-1 text-slate-400" size={22} />
      <div className="flex-1">
        <div className="flex items-center gap-2">
          <p className="font-semibold text-slate-900">{item.filename}</p>
          <StatusBadge status={item.status} />
        </div>
        <p className="text-xs text-slate-500">
          {item.content_type} · {formatBytes(item.size_bytes)}
        </p>
        {item.extracted ? (
          <ExtractedSummary extracted={item.extracted} ocrConfidence={item.ocr_confidence} />
        ) : null}
        {item.error_message ? (
          <p className="mt-2 text-xs text-amber-700">{item.error_message}</p>
        ) : null}
        {item.status === "ready" && <AdvisorPanel uploadId={item.id} />}
      </div>
    </div>
  );
}

function StatusBadge({ status }: { status: UploadStatus }) {
  const { t } = useTranslation("documents");
  switch (status) {
    case "ready":
      return (
        <Badge tone="low">
          <CheckCircle2 size={12} className="mr-1" /> {t("status.ready")}
        </Badge>
      );
    case "failed":
      return (
        <Badge tone="high">
          <XCircle size={12} className="mr-1" /> {t("status.failed")}
        </Badge>
      );
    case "processing":
      return <Badge tone="info">{t("status.processing")}</Badge>;
    default:
      return <Badge tone="neutral">{t("status.queued")}</Badge>;
  }
}

function ExtractedSummary({
  extracted,
  ocrConfidence,
}: {
  extracted: NonNullable<UploadOut["extracted"]>;
  ocrConfidence: number | null;
}) {
  const { t } = useTranslation("documents");
  const dash = "—";
  return (
    <div className="mt-2 grid gap-2 text-xs text-slate-600 sm:grid-cols-3">
      <Field label={t("fields.monthlyPremium")} value={formatEur(extracted.monthly_premium_eur)} />
      <Field label={t("fields.annualPremium")} value={formatEur(extracted.annual_premium_eur)} />
      <Field label={t("fields.deductible")} value={formatEur(extracted.deductible_eur)} />
      <Field label={t("fields.coverageLimit")} value={formatEur(extracted.coverage_limit_eur)} />
      <Field
        label={t("fields.detectedCoverages")}
        value={
          extracted.coverages.length
            ? extracted.coverages.map((c) => translateConcept(t, c)).join(", ")
            : dash
        }
      />
      <Field
        label={t("fields.detectedExclusions")}
        value={
          extracted.exclusions.length
            ? extracted.exclusions.map((c) => translateConcept(t, c)).join(", ")
            : dash
        }
      />
      <Field label={t("fields.clausesExtracted")} value={String(extracted.clauses.length)} />
      <Field
        label={t("fields.ocrConfidence")}
        value={ocrConfidence != null ? formatPercent(ocrConfidence / 100) : dash}
      />
      {extracted.clauses.length > 0 && (
        <div className="col-span-full mt-2 space-y-2">
          {extracted.clauses.slice(0, 5).map((c, idx) => (
            <div key={idx} className="rounded-lg border border-slate-200 p-2">
              <div className="flex flex-wrap items-center gap-2">
                <Badge tone="info">{t(`insurance:clauseType.${c.clause_type}`)}</Badge>
                {c.page_number != null && (
                  <span className="text-[11px] text-slate-500">p. {c.page_number}</span>
                )}
                {c.confidence < 0.75 && (
                  <span className="text-[11px] text-amber-700">{t("lowConfidenceWarning")}</span>
                )}
              </div>
              <p lang="de" className="mt-1 italic text-slate-600">"{c.text}"</p>
            </div>
          ))}
          {extracted.clauses.length > 5 && (
            <p className="text-[11px] text-slate-500">
              {t("moreClauses", { count: extracted.clauses.length - 5 })}
            </p>
          )}
        </div>
      )}
    </div>
  );
}

function Field({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <p className="text-[11px] uppercase tracking-wide text-slate-500">{label}</p>
      <p className="font-medium text-slate-700">{value}</p>
    </div>
  );
}
