// File: frontend/src/features/compare/ComparePage.tsx
import { useMutation, useQuery } from "@tanstack/react-query";
import { Bot, ChevronLeft } from "lucide-react";
import { useMemo, useState } from "react";
import { useTranslation } from "react-i18next";
import { Link, useNavigate } from "react-router-dom";

import { extractErrorMessage } from "@/api/client";
import { compareApi, policyApi } from "@/api/endpoints";
import { Alert, Badge, Card, Spinner } from "@/components/ui";
import { Button } from "@/components/ui/Button";
import { ProviderLogo } from "@/components/ui/ProviderLogo";
import { cn } from "@/lib/cn";
import { formatEur, formatEurCompact } from "@/lib/format";
import { productLineLabel as translateProductLine } from "@/lib/i18nInsurance";
import type {
  CompareResponse,
  Policy,
  ProductLine,
  RiskLevel,
} from "@/types/domain";

const riskTone: Record<RiskLevel, "low" | "medium" | "high"> = {
  low: "low",
  medium: "medium",
  high: "high",
};

export default function ComparePage() {
  const { t, i18n } = useTranslation(["comparison", "insurance", "common"]);
  const navigate = useNavigate();
  const [productLine, setProductLine] = useState<ProductLine>("car");
  const [selected, setSelected] = useState<number[]>([]);
  const [response, setResponse] = useState<CompareResponse | null>(null);

  const policies = useQuery<Policy[]>({
    queryKey: ["policies", productLine],
    queryFn: () => policyApi.list({ product_line: productLine }),
  });

  const compare = useMutation({
    mutationFn: (ids: number[]) => compareApi.compare(ids),
    onSuccess: setResponse,
  });

  const canCompare = selected.length >= 2 && selected.length <= 3;

  const toggle = (id: number) => {
    setResponse(null);
    setSelected((prev) => {
      if (prev.includes(id)) return prev.filter((x) => x !== id);
      if (prev.length >= 3) return prev;
      return [...prev, id];
    });
  };

  const visiblePolicies = useMemo(
    () => (response ? response.policies : policies.data ?? []),
    [response, policies.data],
  );

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-slate-900">{t("comparison:title")}</h1>
          <p className="text-slate-600">{t("comparison:subtitle")}</p>
        </div>
        <Link to="/dashboard" className="inline-flex items-center text-sm text-slate-600 hover:underline">
          <ChevronLeft size={16} /> {t("common:actions.backToDashboard")}
        </Link>
      </div>

      <Card>
        <div className="flex flex-wrap items-center gap-4">
          <div>
            <label htmlFor="compare-product-line" className="mr-2 text-sm text-slate-600">
              {t("comparison:productLineLabel")}
            </label>
            <select
              id="compare-product-line"
              className="input-field inline-block w-auto"
              value={productLine}
              onChange={(e) => {
                setProductLine(e.target.value as ProductLine);
                setSelected([]);
                setResponse(null);
              }}
            >
              {(["car", "household", "travel", "legal"] as ProductLine[]).map((line) => (
                <option key={line} value={line}>
                  {translateProductLine(t, i18n.language, line)}
                </option>
              ))}
            </select>
          </div>
          <span className="text-sm text-slate-500">
            {t("comparison:selectedCount", { count: selected.length })}
          </span>
          <div className="ml-auto flex gap-2">
            <Button variant="secondary" disabled={selected.length === 0} onClick={() => {
              setSelected([]);
              setResponse(null);
            }}>
              {t("common:actions.reset")}
            </Button>
            <Button
              disabled={!canCompare}
              loading={compare.isPending}
              onClick={() => compare.mutate(selected)}
            >
              {selected.length > 0
                ? t("comparison:compareButtonWithCount", { count: selected.length })
                : t("comparison:compareButton")}
            </Button>
          </div>
        </div>

        {compare.isError && (
          <div className="mt-4">
            <Alert variant="error">{extractErrorMessage(compare.error)}</Alert>
          </div>
        )}
      </Card>

      {policies.isLoading ? (
        <Spinner />
      ) : (
        <Card>
          <div className="mb-2 flex flex-wrap items-center gap-2">
            <h2 className="text-lg font-semibold">
              {response
                ? t("comparison:comparingCount", {
                    count: response.policies.length,
                    line: translateProductLine(t, i18n.language, productLine),
                  })
                : t("comparison:availablePolicies")}
            </h2>
            {visiblePolicies.some((p) => p.is_demo_data) && (
              <Badge tone="neutral">{t("common:demoData.label")}</Badge>
            )}
          </div>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-slate-200 text-sm">
              <thead>
                <tr className="text-left text-xs uppercase tracking-wide text-slate-500">
                  {!response && <th className="px-2 py-2">{t("comparison:table.pick")}</th>}
                  <th className="px-2 py-2">{t("comparison:table.insurer")}</th>
                  <th className="px-2 py-2">{t("comparison:table.policyName")}</th>
                  <th className="px-2 py-2">{t("comparison:table.monthlyPremium")}</th>
                  <th className="px-2 py-2">{t("comparison:table.deductible")}</th>
                  <th className="px-2 py-2">{t("comparison:table.coverageLimit")}</th>
                  <th className="px-2 py-2">{t("comparison:table.riskLevel")}</th>
                  <th className="px-2 py-2">{t("comparison:table.coverageItems")}</th>
                  <th className="px-2 py-2">{t("comparison:table.actions")}</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {visiblePolicies.map((p) => {
                  const checked = selected.includes(p.id);
                  return (
                    <tr key={p.id} className={cn(checked && !response && "bg-brand-50")}>
                      {!response && (
                        <td className="px-2 py-3">
                          <input
                            type="checkbox"
                            aria-label={t("comparison:table.pick") + `: ${p.name}`}
                            className="h-4 w-4 rounded border-slate-300 text-brand-600"
                            checked={checked}
                            onChange={() => toggle(p.id)}
                          />
                        </td>
                      )}
                      <td className="px-2 py-3 font-medium text-slate-700">
                        <div className="flex items-center gap-2">
                          {p.provider && <ProviderLogo provider={p.provider} size={20} />}
                          {p.provider?.name ?? t("common:status.notAvailable")}
                        </div>
                      </td>
                      <td className="px-2 py-3 text-slate-700">{p.name}</td>
                      <td className="px-2 py-3 font-semibold text-green-700">
                        {formatEur(p.monthly_premium_eur)}
                      </td>
                      <td className="px-2 py-3 text-slate-700">{formatEur(p.deductible_eur)}</td>
                      <td className="px-2 py-3 text-slate-700">{formatEurCompact(p.coverage_limit_eur)}</td>
                      <td className="px-2 py-3">
                        <Badge tone={riskTone[p.risk_level]}>{t(`insurance:riskLevel.${p.risk_level}`)}</Badge>
                      </td>
                      <td className="px-2 py-3 text-slate-700">
                        {t("comparison:table.itemsCount", { count: p.coverage_items.length })}
                      </td>
                      <td className="px-2 py-3">
                        <Link
                          to={`/policies/${p.id}`}
                          className="text-xs font-semibold text-brand-700 hover:underline"
                        >
                          {t("common:actions.viewDetails")} →
                        </Link>
                      </td>
                    </tr>
                  );
                })}
                {visiblePolicies.length === 0 && (
                  <tr>
                    <td className="px-2 py-6 text-center text-slate-500" colSpan={9}>
                      {t("comparison:noPolicies")}
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </Card>
      )}

      {response && (
        <>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <SummaryStat label={t("comparison:summary.cheapest")} value={formatEur(response.summary.cheapest_monthly_eur)} accent="text-green-700" />
            <SummaryStat label={t("comparison:summary.average")} value={formatEur(response.summary.average_monthly_eur)} accent="text-brand-700" />
            <SummaryStat
              label={t("comparison:summary.withinBudget")}
              value={`${response.summary.within_budget_count}/${response.policies.length}`}
              accent="text-slate-800"
            />
            <SummaryStat
              label={t("comparison:summary.lowRisk")}
              value={String(response.summary.low_risk_count)}
              accent="text-slate-800"
            />
          </div>

          <div className="flex justify-center">
            <Button onClick={() => navigate("/recommendations")}>
              <Bot size={16} className="mr-2" />
              {t("comparison:getRecommendations")}
            </Button>
          </div>
        </>
      )}
    </div>
  );
}

function SummaryStat({
  label,
  value,
  accent,
}: {
  label: string;
  value: string;
  accent: string;
}) {
  return (
    <Card className="p-5">
      <p className="text-xs uppercase tracking-wide text-slate-500">{label}</p>
      <p className={cn("mt-2 text-2xl font-bold", accent)}>{value}</p>
    </Card>
  );
}
