// File: frontend/src/features/policy/PolicyDetailPage.tsx
import { useQuery } from "@tanstack/react-query";
import { Check, ChevronLeft, FileSearch, Shield, Star, X } from "lucide-react";
import { useTranslation } from "react-i18next";
import { Link, useNavigate, useParams } from "react-router-dom";

import { policyApi } from "@/api/endpoints";
import { Alert, Badge, Card, Spinner } from "@/components/ui";
import { Button } from "@/components/ui/Button";
import { ProviderLogo } from "@/components/ui/ProviderLogo";
import { formatEur, formatPercent } from "@/lib/format";
import { productLineLabel as translateProductLine, translateConcept } from "@/lib/i18nInsurance";
import type { Policy, RiskLevel, SourceClause } from "@/types/domain";

const riskTone: Record<RiskLevel, "low" | "medium" | "high"> = {
  low: "low",
  medium: "medium",
  high: "high",
};

export default function PolicyDetailPage() {
  const { t, i18n } = useTranslation(["dashboard", "insurance", "common"]);
  const navigate = useNavigate();
  const { id } = useParams<{ id: string }>();
  const numericId = Number(id);

  const policy = useQuery<Policy>({
    queryKey: ["policy", numericId],
    queryFn: () => policyApi.get(numericId),
    enabled: Number.isFinite(numericId),
  });

  const clauses = useQuery<SourceClause[]>({
    queryKey: ["policy-clauses", numericId],
    queryFn: () => policyApi.clauses(numericId),
    enabled: Number.isFinite(numericId),
  });

  if (policy.isLoading) {
    return <Spinner className="h-8 w-8" />;
  }
  if (policy.isError || !policy.data) {
    return (
      <Alert variant="error">
        {t("dashboard:policyDetail.notFound")}{" "}
        <Link to="/recommendations" className="underline">
          {t("dashboard:policyDetail.backToRecommendations")}
        </Link>
      </Alert>
    );
  }

  const p = policy.data;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <Link to="/recommendations" className="inline-flex items-center text-sm text-slate-600 hover:underline">
          <ChevronLeft size={16} /> {t("common:actions.back")}
        </Link>
      </div>

      {/* Header card */}
      <Card>
        <div className="flex items-start justify-between gap-4">
          <div>
            <div className="flex items-center gap-3">
              <span className="grid h-10 w-10 place-items-center rounded-lg bg-brand-100 text-brand-700">
                <Shield size={20} />
              </span>
              <div>
                <h1 className="text-2xl font-bold text-slate-900">{p.name}</h1>
                <p className="flex items-center gap-1.5 text-sm text-slate-500">
                  {p.provider && <ProviderLogo provider={p.provider} size={16} />}
                  {p.provider?.name ?? t("common:status.notAvailable")}
                </p>
              </div>
            </div>
            <div className="mt-3 flex flex-wrap gap-2">
              <Badge tone="info">{translateProductLine(t, i18n.language, p.product_line)}</Badge>
              <Badge tone={riskTone[p.risk_level]}>{t(`insurance:riskLevel.${p.risk_level}`)}</Badge>
              {p.is_demo_data && (
                <Badge tone="neutral">{t("dashboard:policyDetail.demoDataBadge")}</Badge>
              )}
            </div>
          </div>
          <div className="text-right">
            <p className="text-3xl font-extrabold text-brand-700">
              {formatEur(p.monthly_premium_eur)}
            </p>
            <p className="text-xs text-slate-500">{t("dashboard:policyDetail.perMonth")}</p>
            <p className="mt-1 text-xs text-slate-500">
              {t("dashboard:policyDetail.annually", { amount: formatEur(p.annual_premium_eur) })}
            </p>
          </div>
        </div>
      </Card>

      {/* KPI grid */}
      <div className="grid gap-4 sm:grid-cols-3">
        <Stat
          label={t("insurance:terms.deductible")}
          value={formatEur(p.deductible_eur)}
          hint={t("dashboard:policyDetail.deductibleHint")}
        />
        <Stat
          label={t("insurance:terms.coverageLimit")}
          value={formatEur(p.coverage_limit_eur)}
          hint={t("dashboard:policyDetail.coverageLimitHint")}
        />
        <Stat
          label={t("comparison:table.coverageItems")}
          value={String(p.coverage_items.length)}
          hint={t("dashboard:policyDetail.coverageItemsHint")}
        />
      </div>

      {/* Coverage details */}
      <Card>
        <h2 className="text-lg font-semibold">{t("dashboard:policyDetail.coverageDetails")}</h2>
        <div className="mt-4 grid gap-2 sm:grid-cols-2">
          {p.coverage_items.map((item) => (
            <div
              key={item}
              className="flex items-center gap-2 rounded-lg bg-green-50 px-3 py-2 text-sm text-green-800"
            >
              <Check size={16} className="text-green-600" />
              {translateConcept(t, item)}
            </div>
          ))}
          {p.coverage_items.length === 0 && (
            <p className="text-sm text-slate-500">{t("dashboard:policyDetail.noCoverageItems")}</p>
          )}
        </div>
      </Card>

      {/* Additional features */}
      {p.additional_features.length > 0 && (
        <Card>
          <h2 className="text-lg font-semibold">{t("dashboard:policyDetail.additionalFeatures")}</h2>
          <div className="mt-4 space-y-2">
            {p.additional_features.map((f) => (
              <div
                key={f}
                className="flex items-center gap-2 rounded-lg bg-brand-50 px-3 py-2 text-sm text-slate-700"
              >
                <Star size={16} className="text-amber-500" />
                {translateConcept(t, f)}
              </div>
            ))}
          </div>
        </Card>
      )}

      {/* Exclusions */}
      <Card>
        <h2 className="text-lg font-semibold">{t("dashboard:policyDetail.exclusionsTitle")}</h2>
        <p className="mt-1 text-sm text-slate-500">{t("dashboard:policyDetail.exclusionsHint")}</p>
        <div className="mt-4 space-y-2">
          {p.exclusions.length === 0 ? (
            <p className="text-sm text-slate-500">{t("dashboard:policyDetail.noExclusions")}</p>
          ) : (
            p.exclusions.map((e) => (
              <div
                key={e}
                className="flex items-center gap-2 rounded-lg bg-red-50 px-3 py-2 text-sm text-red-800"
              >
                <X size={16} className="text-red-600" />
                {translateConcept(t, e)}
              </div>
            ))
          )}
        </div>
      </Card>

      {/* Summary */}
      <Card>
        <h2 className="text-lg font-semibold">{t("dashboard:policyDetail.summary")}</h2>
        <div className="mt-4 grid gap-4 sm:grid-cols-2">
          <div>
            <h3 className="mb-2 text-sm font-semibold text-slate-700">
              {t("dashboard:policyDetail.basicInfo")}
            </h3>
            <SummaryRow
              label={t("dashboard:policyDetail.policyType")}
              value={translateProductLine(t, i18n.language, p.product_line)}
            />
            <SummaryRow
              label={t("insurance:terms.riskLevel")}
              value={t(`insurance:riskLevel.${p.risk_level}`)}
            />
            <SummaryRow
              label={t("dashboard:policyDetail.insurer")}
              value={p.provider?.name ?? t("common:status.notAvailable")}
            />
          </div>
          <div>
            <h3 className="mb-2 text-sm font-semibold text-slate-700">
              {t("dashboard:policyDetail.financialDetails")}
            </h3>
            <SummaryRow label={t("insurance:terms.monthlyPremium")} value={formatEur(p.monthly_premium_eur)} />
            <SummaryRow label={t("insurance:terms.annualPremium")} value={formatEur(p.annual_premium_eur)} />
            <SummaryRow label={t("insurance:terms.deductible")} value={formatEur(p.deductible_eur)} />
            <SummaryRow label={t("insurance:terms.coverageLimit")} value={formatEur(p.coverage_limit_eur)} />
          </div>
        </div>
      </Card>

      {/* Source evidence */}
      <Card>
        <div className="flex items-center gap-2">
          <FileSearch size={18} className="text-brand-600" />
          <h2 className="text-lg font-semibold">{t("dashboard:policyDetail.sourceEvidence")}</h2>
        </div>
        <p className="mt-1 text-sm text-slate-500">{t("dashboard:policyDetail.sourceEvidenceHint")}</p>
        <div className="mt-4 space-y-3">
          {clauses.isLoading && <Spinner />}
          {!clauses.isLoading && (clauses.data ?? []).length === 0 && (
            <Alert variant="info">{t("dashboard:policyDetail.noEvidenceDemo")}</Alert>
          )}
          {clauses.data?.map((c) => (
            <div key={c.id} className="rounded-lg border border-slate-200 p-3">
              <div className="flex flex-wrap items-center gap-2">
                <Badge tone="info">{t(`insurance:clauseType.${c.clause_type}`)}</Badge>
                {c.page_number != null && (
                  <span className="text-xs text-slate-500">
                    {t("dashboard:policyDetail.evidencePage", { page: c.page_number })}
                  </span>
                )}
                <span className="text-xs text-slate-500">
                  {t("dashboard:policyDetail.evidenceConfidence", {
                    value: formatPercent(c.confidence),
                  })}
                </span>
              </div>
              {/* Original clause text, verbatim (German) — never translated. */}
              <p lang={c.document_language} className="mt-2 text-sm italic text-slate-700">
                "{c.text}"
              </p>
            </div>
          ))}
        </div>
      </Card>

      <div className="flex flex-col gap-3 sm:flex-row">
        <Button variant="dark" onClick={() => navigate("/compare")} className="flex-1">
          {t("dashboard:policyDetail.compareWithOthers")}
        </Button>
        <Button onClick={() => navigate("/recommendations")} className="flex-1">
          {t("dashboard:policyDetail.viewRecommendations")}
        </Button>
      </div>
    </div>
  );
}

function Stat({ label, value, hint }: { label: string; value: string; hint?: string }) {
  return (
    <Card>
      <p className="text-xs uppercase tracking-wide text-slate-500">{label}</p>
      <p className="mt-2 text-2xl font-bold text-slate-900">{value}</p>
      {hint && <p className="mt-1 text-xs text-slate-500">{hint}</p>}
    </Card>
  );
}

function SummaryRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex justify-between border-b border-slate-100 py-1.5 text-sm">
      <span className="text-slate-500">{label}:</span>
      <span className="font-semibold text-slate-800">{value}</span>
    </div>
  );
}
