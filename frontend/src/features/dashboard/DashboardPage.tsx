// File: frontend/src/features/dashboard/DashboardPage.tsx
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Bot, ChevronDown, Database, Target, Upload as UploadIcon } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { useForm } from "react-hook-form";
import { useTranslation } from "react-i18next";
import { Link, useNavigate } from "react-router-dom";

import { extractErrorMessage } from "@/api/client";
import { profileApi } from "@/api/endpoints";
import { Alert, Card, CardSubtitle, CardTitle, Label, Select } from "@/components/ui";
import { Button } from "@/components/ui/Button";
import { cn } from "@/lib/cn";
import { formatEur } from "@/lib/format";
import { productLinePair, translateConcept } from "@/lib/i18nInsurance";
import type {
  CoverageLevel,
  DeductiblePreference,
  ProductLine,
  RiskProfile,
  RiskTolerance,
} from "@/types/domain";

type FormValues = {
  insurance_type: ProductLine;
  monthly_budget_eur: number;
  risk_tolerance: RiskTolerance;
  coverage_level: CoverageLevel;
  deductible_preference: DeductiblePreference;
};

const DEFAULT_VALUES: FormValues = {
  insurance_type: "car",
  monthly_budget_eur: 100,
  risk_tolerance: "medium",
  coverage_level: "standard",
  deductible_preference: "medium",
};

// Must mirror DEFAULT_WEIGHTS in backend/app/recommender/scorer.py.
const DEFAULT_WEIGHTS_PCT: Record<string, number> = {
  price: 25,
  coverage: 30,
  exclusion: 20,
  deductible: 10,
  fit: 15,
};
const WEIGHT_FACTORS = ["price", "coverage", "exclusion", "deductible", "fit"] as const;

// Candidate required-coverage options per product line, drawn from the NLP
// pipeline's controlled coverage vocabulary (see app/nlp/extractor.py).
const REQUIRED_COVERAGE_OPTIONS: Record<ProductLine, string[]> = {
  car: ["Liability coverage", "Comprehensive coverage", "Collision coverage", "Glass breakage", "Theft protection"],
  household: ["Fire damage", "Storm damage", "Water damage", "Theft protection", "Bicycle theft", "Home electronics"],
  travel: ["Travel medical", "Trip cancellation", "Travel luggage", "Liability coverage"],
  legal: ["Legal protection", "Contract disputes", "Tenancy disputes", "Employment disputes"],
};

export default function DashboardPage() {
  const { t } = useTranslation(["dashboard", "insurance", "common", "recommendation"]);
  const navigate = useNavigate();
  const qc = useQueryClient();

  const profile = useQuery<RiskProfile | null>({
    queryKey: ["profile"],
    queryFn: async () => {
      try {
        return await profileApi.get();
      } catch {
        return null;
      }
    },
  });

  const { register, handleSubmit, watch, setValue, reset } = useForm<FormValues>({
    defaultValues: DEFAULT_VALUES,
  });
  const selected = watch();

  const [requiredCoverages, setRequiredCoverages] = useState<string[]>([]);
  const [weightsPct, setWeightsPct] = useState<Record<string, number>>(DEFAULT_WEIGHTS_PCT);
  const [advancedOpen, setAdvancedOpen] = useState(false);

  useEffect(() => {
    if (profile.data) {
      reset({
        insurance_type: profile.data.insurance_type,
        monthly_budget_eur: profile.data.monthly_budget_eur,
        risk_tolerance: profile.data.risk_tolerance,
        coverage_level: profile.data.coverage_level,
        deductible_preference: profile.data.deductible_preference,
      });
      setRequiredCoverages(profile.data.required_coverages ?? []);
      const hasCustomWeights = Object.keys(profile.data.weights ?? {}).length > 0;
      if (hasCustomWeights) {
        setWeightsPct(
          Object.fromEntries(
            WEIGHT_FACTORS.map((f) => [f, Math.round((profile.data!.weights[f] ?? 0) * 100)]),
          ),
        );
        setAdvancedOpen(true);
      }
    }
  }, [profile.data, reset]);

  const weightsTotal = useMemo(
    () => WEIGHT_FACTORS.reduce((sum, f) => sum + (weightsPct[f] ?? 0), 0),
    [weightsPct],
  );
  const weightsValid = weightsTotal === 100;
  const weightsAreCustom = advancedOpen;

  const toggleRequiredCoverage = (concept: string) => {
    setRequiredCoverages((prev) =>
      prev.includes(concept) ? prev.filter((c) => c !== concept) : [...prev, concept],
    );
  };

  const save = useMutation({
    mutationFn: async (values: FormValues) => {
      const weights = weightsAreCustom
        ? Object.fromEntries(WEIGHT_FACTORS.map((f) => [f, (weightsPct[f] ?? 0) / 100]))
        : {};
      return profileApi.upsert({
        ...values,
        household_size: profile.data?.household_size ?? 1,
        property_value_eur: profile.data?.property_value_eur ?? null,
        required_coverages: requiredCoverages,
        weights,
      });
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["profile"] });
    },
  });

  const canSave = !weightsAreCustom || weightsValid;

  const onSavePreferences = handleSubmit((values) => {
    if (canSave) save.mutate(values);
  });

  const onGetRecommendations = handleSubmit(async (values) => {
    if (!canSave) return;
    await save.mutateAsync(values);
    navigate("/recommendations");
  });

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-slate-900">{t("dashboard:title")}</h1>
        <p className="text-slate-600">{t("dashboard:subtitle")}</p>
      </div>

      {/* Action cards */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <Link to="/upload">
          <ActionCard
            icon={<UploadIcon className="text-rose-500" size={20} />}
            title={t("dashboard:actionCards.upload.title")}
            subtitle={t("dashboard:actionCards.upload.subtitle")}
          />
        </Link>
        <Link to="/compare">
          <ActionCard
            icon={<Database className="text-amber-500" size={20} />}
            title={t("dashboard:actionCards.compare.title")}
            subtitle={t("dashboard:actionCards.compare.subtitle")}
          />
        </Link>
        <Link to="/recommendations">
          <ActionCard
            icon={<Bot className="text-brand-600" size={20} />}
            title={t("dashboard:actionCards.recommend.title")}
            subtitle={t("dashboard:actionCards.recommend.subtitle")}
          />
        </Link>
        <Link to="/recommendations">
          <ActionCard
            icon={<Target className="text-violet-600" size={20} />}
            title={t("dashboard:actionCards.demo.title")}
            subtitle={t("dashboard:actionCards.demo.subtitle")}
          />
        </Link>
      </div>

      {/* Preferences */}
      <Card>
        <CardTitle>{t("dashboard:preferences.title")}</CardTitle>
        <CardSubtitle>{t("dashboard:preferences.subtitle")}</CardSubtitle>

        {save.isError && (
          <div className="mt-4">
            <Alert variant="error">{extractErrorMessage(save.error)}</Alert>
          </div>
        )}

        <form onSubmit={onSavePreferences} className="mt-6 space-y-6">
          <div>
            <Label htmlFor="insurance_type">{t("dashboard:preferences.insuranceType")}</Label>
            <Select id="insurance_type" {...register("insurance_type")}>
              {(["car", "household", "travel", "legal"] as const).map((line) => {
                const pair = productLinePair(t, line);
                return (
                  <option key={line} value={line}>
                    {pair.en} ({pair.at})
                  </option>
                );
              })}
            </Select>
          </div>

          <div>
            <Label htmlFor="monthly_budget_eur">
              {t("dashboard:preferences.monthlyBudget", {
                amount: formatEur(Number(selected.monthly_budget_eur)),
              })}
            </Label>
            <input
              id="monthly_budget_eur"
              type="range"
              min={20}
              max={200}
              step={5}
              className="w-full accent-brand-600"
              {...register("monthly_budget_eur", { valueAsNumber: true })}
            />
            <div className="mt-1 flex justify-between text-xs text-slate-500">
              <span>€20</span>
              <span>€200</span>
            </div>
          </div>

          <SegmentedField
            label={t("dashboard:preferences.riskTolerance")}
            value={selected.risk_tolerance}
            onChange={(v) => setValue("risk_tolerance", v as RiskTolerance)}
            options={[
              { value: "low", label: t("insurance:riskTolerance.low") },
              { value: "medium", label: t("insurance:riskTolerance.medium") },
              { value: "high", label: t("insurance:riskTolerance.high") },
            ]}
          />
          <SegmentedField
            label={t("dashboard:preferences.coverageLevel")}
            value={selected.coverage_level}
            onChange={(v) => setValue("coverage_level", v as CoverageLevel)}
            options={[
              { value: "basic", label: t("insurance:coverageLevel.basic") },
              { value: "standard", label: t("insurance:coverageLevel.standard") },
              { value: "comprehensive", label: t("insurance:coverageLevel.comprehensive") },
            ]}
          />
          <SegmentedField
            label={t("dashboard:preferences.deductiblePreference")}
            value={selected.deductible_preference}
            onChange={(v) => setValue("deductible_preference", v as DeductiblePreference)}
            options={[
              { value: "low", label: t("insurance:deductiblePreference.low"), hint: "€150-300" },
              { value: "medium", label: t("insurance:deductiblePreference.medium"), hint: "€400-600" },
              { value: "high", label: t("insurance:deductiblePreference.high"), hint: "€700-1000" },
            ]}
          />

          <div>
            <Label>{t("dashboard:preferences.requiredCoverages.label")}</Label>
            <p className="mb-2 text-xs text-slate-500">
              {t("dashboard:preferences.requiredCoverages.hint")}
            </p>
            <div className="flex flex-wrap gap-2">
              {(REQUIRED_COVERAGE_OPTIONS[selected.insurance_type] ?? []).map((concept) => {
                const active = requiredCoverages.includes(concept);
                return (
                  <button
                    key={concept}
                    type="button"
                    onClick={() => toggleRequiredCoverage(concept)}
                    className={cn(
                      "rounded-full border px-3 py-1.5 text-xs transition",
                      active
                        ? "border-brand-500 bg-brand-50 text-brand-700"
                        : "border-slate-300 bg-white text-slate-600 hover:bg-slate-50",
                    )}
                  >
                    {translateConcept(t, concept)}
                  </button>
                );
              })}
            </div>
          </div>

          <div className="border-t border-slate-200 pt-4">
            <button
              type="button"
              onClick={() => setAdvancedOpen((v) => !v)}
              className="flex items-center gap-1.5 text-sm font-medium text-slate-700"
            >
              <ChevronDown
                size={16}
                className={cn("transition-transform", advancedOpen && "rotate-180")}
              />
              {t("dashboard:preferences.advanced.toggle")}
            </button>
            {advancedOpen && (
              <div className="mt-4 space-y-4">
                <p className="text-xs text-slate-500">{t("dashboard:preferences.advanced.hint")}</p>
                {WEIGHT_FACTORS.map((factor) => (
                  <div key={factor}>
                    <div className="flex items-center justify-between text-sm">
                      <span>{t(`recommendation:feature.${factor}`)}</span>
                      <span className="font-semibold">{weightsPct[factor] ?? 0}%</span>
                    </div>
                    <input
                      type="range"
                      min={0}
                      max={100}
                      step={5}
                      value={weightsPct[factor] ?? 0}
                      onChange={(e) =>
                        setWeightsPct((prev) => ({ ...prev, [factor]: Number(e.target.value) }))
                      }
                      className="w-full accent-brand-600"
                    />
                  </div>
                ))}
                <div className="flex items-center justify-between">
                  <span
                    className={cn(
                      "text-sm font-semibold",
                      weightsValid ? "text-green-700" : "text-red-700",
                    )}
                  >
                    {t("dashboard:preferences.advanced.total", { total: weightsTotal })}
                  </span>
                  <button
                    type="button"
                    className="text-xs text-slate-500 underline"
                    onClick={() => setWeightsPct(DEFAULT_WEIGHTS_PCT)}
                  >
                    {t("dashboard:preferences.advanced.resetDefaults")}
                  </button>
                </div>
                {!weightsValid && (
                  <Alert variant="warning">{t("dashboard:preferences.advanced.totalError")}</Alert>
                )}
              </div>
            )}
          </div>

          <div className="flex flex-col gap-3 sm:flex-row">
            <Button
              type="submit"
              variant="dark"
              className="flex-1"
              loading={save.isPending}
              disabled={!canSave}
            >
              {t("dashboard:preferences.save")}
            </Button>
            <Button
              type="button"
              className="flex-1"
              onClick={onGetRecommendations}
              loading={save.isPending}
              disabled={!canSave}
            >
              {t("dashboard:preferences.getRecommendations")}
            </Button>
          </div>
        </form>
      </Card>
    </div>
  );
}

function ActionCard({
  icon, title, subtitle,
}: { icon: React.ReactNode; title: string; subtitle: string }) {
  return (
    <Card className="cursor-pointer transition hover:shadow-elevated">
      <div className="flex items-start gap-3">
        <div className="grid h-10 w-10 place-items-center rounded-lg bg-slate-100">{icon}</div>
        <div>
          <p className="font-semibold text-slate-900">{title}</p>
          <p className="text-xs text-slate-500">{subtitle}</p>
        </div>
      </div>
    </Card>
  );
}

function SegmentedField({
  label,
  value,
  onChange,
  options,
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
  options: { value: string; label: string; hint?: string }[];
}) {
  return (
    <div>
      <Label>{label}</Label>
      <div className="grid grid-cols-3 gap-2">
        {options.map((opt) => {
          const active = opt.value === value;
          return (
            <button
              key={opt.value}
              type="button"
              onClick={() => onChange(opt.value)}
              className={cn(
                "rounded-lg border px-4 py-3 text-sm transition",
                active
                  ? "border-brand-500 bg-brand-50 text-brand-700"
                  : "border-slate-300 bg-white text-slate-700 hover:bg-slate-50",
              )}
            >
              <div className="font-medium">{opt.label}</div>
              {opt.hint && (
                <div className={cn("text-xs", active ? "text-brand-700" : "text-slate-500")}>
                  {opt.hint}
                </div>
              )}
            </button>
          );
        })}
      </div>
    </div>
  );
}
