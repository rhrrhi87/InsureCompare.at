// File: frontend/src/features/recommendations/RecommendationsPage.tsx
import { useQuery } from "@tanstack/react-query";
import { GitCompareArrows, Trophy } from "lucide-react";
import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { Link, useNavigate } from "react-router-dom";

import { extractErrorMessage } from "@/api/client";
import { profileApi } from "@/api/endpoints";
import { Alert, Badge, Card, Spinner } from "@/components/ui";
import { Button } from "@/components/ui/Button";
import { ProviderLogo } from "@/components/ui/ProviderLogo";
import { cn } from "@/lib/cn";
import { formatEur } from "@/lib/format";
import { productLineLabel as translateProductLine } from "@/lib/i18nInsurance";
import type {
  CounterfactualExplanation,
  RecommendationResponse,
  ScoredPolicy,
} from "@/types/domain";

import { useRecommend } from "./useRecommendations";

const FEATURE_ORDER = ["price", "coverage", "exclusion", "deductible", "fit"] as const;

export default function RecommendationsPage() {
  const { t, i18n } = useTranslation(["recommendation", "insurance", "common"]);
  const navigate = useNavigate();
  const recommend = useRecommend();
  const [response, setResponse] = useState<RecommendationResponse | null>(null);

  const profile = useQuery({
    queryKey: ["profile"],
    queryFn: profileApi.get,
    retry: false,
  });

  // Auto-trigger when the page loads (and a profile exists)
  useEffect(() => {
    if (!profile.data || response || recommend.isPending) return;
    recommend.mutate(undefined, {
      onSuccess: setResponse,
    });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [profile.data]);

  if (profile.isLoading) {
    return (
      <div className="flex items-center justify-center py-20">
        <Spinner />
      </div>
    );
  }

  if (profile.isError) {
    return (
      <Alert variant="warning">
        {t("recommendation:completeProfilePrompt")}{" "}
        <Link to="/dashboard" className="underline">
          {t("recommendation:goToDashboard")}
        </Link>
        .
      </Alert>
    );
  }

  if (recommend.isPending && !response) {
    return (
      <div className="flex flex-col items-center gap-3 py-20 text-slate-600">
        <Spinner className="h-8 w-8" />
        <p>{t("recommendation:calculating")}</p>
      </div>
    );
  }

  if (recommend.isError) {
    return (
      <div className="space-y-3">
        <Alert variant="error">{extractErrorMessage(recommend.error)}</Alert>
        <Button onClick={() => navigate("/dashboard")} variant="secondary">
          {t("common:actions.backToDashboard")}
        </Button>
      </div>
    );
  }

  if (!response) {
    return null;
  }

  const monthlyBudget = profile.data?.monthly_budget_eur ?? 100;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-slate-900">{t("recommendation:resultsTitle")}</h1>
          <p className="text-slate-600">
            {t("recommendation:resultsSubtitle", {
              line: translateProductLine(t, i18n.language, response.product_line),
              budget: formatEur(monthlyBudget),
            })}
          </p>
        </div>
        <Link to="/dashboard" className="text-sm text-slate-600 hover:underline">
          ← {t("common:actions.backToDashboard")}
        </Link>
      </div>

      <BestMatchCard scored={response.top_pick} t={t} />

      <Card>
        <div className="mb-4 flex flex-wrap items-center gap-2">
          <h2 className="text-xl font-bold text-slate-900">{t("recommendation:allRanked")}</h2>
          {response.ranked_policies.some((sp) => sp.policy.is_demo_data) && (
            <Badge tone="neutral">{t("common:demoData.label")}</Badge>
          )}
        </div>
        <div className="space-y-4">
          {response.ranked_policies.map((sp, idx) => (
            <RankedPolicyCard key={sp.policy.id} scored={sp} rank={idx + 1} t={t} />
          ))}
        </div>
      </Card>

      {response.counterfactual && (
        <SensitivityCard explanation={response.counterfactual} t={t} />
      )}

      <ScoringMethodologyCard weights={response.weights} t={t} />
    </div>
  );
}

type Translator = ReturnType<typeof useTranslation>["t"];

// ---------- Deterministic sensitivity / counterfactual explanation ----------
function SensitivityCard({
  explanation,
  t,
}: {
  explanation: CounterfactualExplanation;
  t: Translator;
}) {
  const featureLabel = t(
    `recommendation:feature.${explanation.changed_feature}`,
  );
  return (
    <Card className="border-violet-200 bg-violet-50">
      <div className="flex items-center gap-2">
        <GitCompareArrows size={19} className="text-violet-700" />
        <h2 className="text-lg font-bold text-violet-950">
          {t("recommendation:sensitivity.title")}
        </h2>
      </div>
      <p className="mt-2 text-sm text-violet-900">
        {t("recommendation:sensitivity.change", {
          feature: featureLabel,
          current: Math.round(explanation.current_weight * 100),
          suggested: Math.round(explanation.suggested_weight * 100),
          alternative: explanation.alternative_policy_name,
          currentPolicy: explanation.current_policy_name,
        })}
      </p>
      <p className="mt-2 text-sm text-slate-700">
        {t("recommendation:sensitivity.projected", {
          alternative: explanation.alternative_policy_name,
          alternativeScore: explanation.alternative_policy_score.toFixed(1),
          currentPolicy: explanation.current_policy_name,
          currentScore: explanation.current_policy_score.toFixed(1),
        })}
      </p>
      <p className="mt-2 text-xs text-slate-600">
        {t("recommendation:sensitivity.method")}
      </p>
    </Card>
  );
}

// ---------- Best match (hero card) ----------
function BestMatchCard({ scored, t }: { scored: ScoredPolicy; t: Translator }) {
  return (
    <Card className="bg-gradient-to-br from-brand-600 to-brand-800 p-8 text-white">
      <div className="flex items-start justify-between">
        <div>
          <div className="flex flex-wrap items-center gap-2">
            <Trophy size={20} className="text-amber-300" />
            <h2 className="text-xl font-bold">{t("recommendation:bestMatch.title")}</h2>
            {scored.policy.is_demo_data && <Badge tone="neutral">{t("common:demoData.label")}</Badge>}
          </div>
          <p className="mt-1 text-sm text-brand-100">{t("recommendation:bestMatch.subtitle")}</p>
        </div>
        <div className="text-right">
          <p className="text-4xl font-extrabold leading-none">{Math.round(scored.score)}</p>
          <p className="text-xs text-brand-100">{t("recommendation:bestMatch.outOf100")}</p>
        </div>
      </div>

      <div className="mt-5 flex flex-wrap items-baseline justify-between gap-3">
        <div>
          <p className="text-2xl font-bold">{scored.policy.name}</p>
          <p className="flex items-center gap-1.5 text-sm text-brand-100">
            {scored.policy.provider && <ProviderLogo provider={scored.policy.provider} size={18} />}
            {scored.policy.provider?.name ?? t("common:status.notAvailable")}
          </p>
        </div>
        <div className="text-right">
          <p className="text-3xl font-bold">{formatEur(scored.policy.monthly_premium_eur)}</p>
          <p className="text-sm text-brand-100">{t("recommendation:bestMatch.perMonth")}</p>
        </div>
      </div>

      <div className="mt-5 grid grid-cols-2 gap-3 sm:grid-cols-5">
        {FEATURE_ORDER.filter((f) => f in scored.breakdown).map((feature) => (
          <div key={feature} className="rounded-lg bg-brand-700/40 px-3 py-2 text-center">
            <p className="text-[11px] uppercase tracking-wide text-brand-200">
              {t(`recommendation:feature.${feature}`)}
            </p>
            <p className="text-2xl font-bold">{Math.round(scored.breakdown[feature])}</p>
          </div>
        ))}
      </div>

      <p className="mt-5 rounded-lg bg-brand-700/30 px-4 py-3 text-sm">{scored.narrative}</p>

      <Link to={`/policies/${scored.policy.id}`}>
        <button className="mt-5 w-full rounded-lg bg-white py-2.5 text-sm font-semibold text-brand-700 transition hover:bg-brand-50">
          {t("common:actions.viewFullDetails")} →
        </button>
      </Link>
    </Card>
  );
}

// ---------- Ranked policy card ----------
function RankedPolicyCard({
  scored,
  rank,
  t,
}: {
  scored: ScoredPolicy;
  rank: number;
  t: Translator;
}) {
  const ringClass = rank === 1 ? "ring-2 ring-brand-500" : "";

  const riskTone =
    scored.policy.risk_level === "low"
      ? "low"
      : scored.policy.risk_level === "medium"
      ? "medium"
      : "high";

  return (
    <Card className={cn("p-5", ringClass)}>
      <div className="flex items-start gap-4">
        <RankBadge rank={rank} />
        <div className="flex-1 min-w-0">
          <div className="flex flex-wrap items-center gap-2">
            <h3 className="text-lg font-semibold text-slate-900">{scored.policy.name}</h3>
            <Badge tone={riskTone as "low" | "medium" | "high"}>
              {t(`insurance:riskLevel.${scored.policy.risk_level}`)}
            </Badge>
          </div>
          <p className="flex items-center gap-1.5 text-sm text-slate-500">
            {scored.policy.provider && <ProviderLogo provider={scored.policy.provider} size={16} />}
            {scored.policy.provider?.name}
          </p>

          <div className="mt-3 grid grid-cols-2 gap-2 text-sm sm:grid-cols-5">
            {FEATURE_ORDER.filter((f) => f in scored.breakdown).map((feature) => {
              const contribution = scored.contributions.find((c) => c.feature === feature);
              const value = scored.breakdown[feature];
              return (
                <div key={feature}>
                  <p className="text-[11px] uppercase tracking-wide text-slate-500">
                    {t(`recommendation:feature.${feature}`)}{" "}
                    {contribution &&
                      t("recommendation:featureWeight", {
                        weight: Math.round(contribution.weight * 100),
                      })}
                  </p>
                  <p
                    className={cn(
                      "text-xl font-bold",
                      value >= 85 ? "text-green-700" : value >= 60 ? "text-brand-700" : "text-amber-700",
                    )}
                  >
                    {Math.round(value)}
                  </p>
                </div>
              );
            })}
          </div>

          <p className="mt-3 text-xs text-slate-600">{scored.narrative}</p>
        </div>

        <div className="hidden text-right sm:block">
          <p className={cn("text-3xl font-bold", rank === 1 ? "text-brand-700" : "text-slate-700")}>
            {Math.round(scored.score)}
          </p>
          <p className="text-xs uppercase tracking-wide text-slate-500">
            {t("recommendation:totalScore")}
          </p>
          <p className="mt-2 text-xl font-bold text-slate-900">
            {formatEur(scored.policy.monthly_premium_eur)}
          </p>
          <p className="text-xs text-slate-500">{t("recommendation:bestMatch.perMonth")}</p>
          <Link to={`/policies/${scored.policy.id}`}>
            <Button size="sm" className="mt-2">
              {t("common:actions.viewDetails")}
            </Button>
          </Link>
        </div>
      </div>
    </Card>
  );
}

function RankBadge({ rank }: { rank: number }) {
  const colour =
    rank === 1
      ? "bg-amber-400 text-amber-900"
      : rank === 2
      ? "bg-slate-300 text-slate-800"
      : rank === 3
      ? "bg-amber-700 text-amber-50"
      : "bg-slate-200 text-slate-600";
  return (
    <div
      className={cn(
        "grid h-9 w-9 shrink-0 place-items-center rounded-full text-sm font-bold",
        colour,
      )}
    >
      #{rank}
    </div>
  );
}

// ---------- Methodology card ----------
function ScoringMethodologyCard({
  weights,
  t,
}: {
  weights: Record<string, number>;
  t: Translator;
}) {
  return (
    <Card className="border-brand-200 bg-brand-50">
      <h2 className="text-lg font-bold text-brand-900">
        📊 {t("recommendation:methodology.title")}
      </h2>
      <p className="mt-1 text-sm text-brand-800">{t("recommendation:methodology.intro")}</p>
      <ul className="mt-4 space-y-2 text-sm text-slate-700">
        {FEATURE_ORDER.map((feature) => {
          const w = weights[feature] ?? 0;
          return (
            <li key={feature} className="flex items-start gap-2">
              <span className="mt-1 inline-block h-1.5 w-1.5 rounded-full bg-brand-700" />
              <span>
                <span className="font-semibold">
                  {t(`recommendation:methodology.${feature}.label`)} ({Math.round(w * 100)}%):
                </span>{" "}
                {t(`recommendation:methodology.${feature}.hint`)}
              </span>
            </li>
          );
        })}
      </ul>
    </Card>
  );
}
