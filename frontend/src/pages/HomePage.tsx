// File: frontend/src/pages/HomePage.tsx
import { Bot, BarChart3, Check, Globe2, Minus } from "lucide-react";
import { Link } from "react-router-dom";
import { useTranslation } from "react-i18next";

import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui";
import { productLinePair } from "@/lib/i18nInsurance";
import type { ProductLine } from "@/types/domain";

const PRODUCT_LINES: ProductLine[] = ["car", "household", "travel", "legal"];
const PRODUCT_LINE_EMOJI: Record<ProductLine, string> = {
  car: "🚗",
  household: "🏠",
  travel: "✈️",
  legal: "⚖️",
};

const HOW_IT_WORKS_STEPS = ["upload", "analysis", "compare", "understand"] as const;
const MATRIX_ROWS = [
  "premium",
  "coverage",
  "exclusions",
  "documents",
  "preferences",
  "explainable",
  "clauseEvidence",
  "traceability",
] as const;

export default function HomePage() {
  const { t } = useTranslation(["home", "insurance", "navigation"]);

  return (
    <div className="bg-gradient-to-b from-brand-50 to-white">
      {/* Hero */}
      <section className="mx-auto max-w-5xl px-4 pt-16 pb-10 text-center sm:px-6 lg:px-8">
        <h1 className="text-4xl font-extrabold tracking-tight text-slate-900 sm:text-5xl">
          {t("home:hero.titleLine1")}
          <br />
          {t("home:hero.titleLine2")}
        </h1>
        <p className="mx-auto mt-4 max-w-2xl text-lg text-slate-600">
          {t("home:hero.subtitle")}
        </p>
        <div className="mt-8 flex flex-col justify-center gap-3 sm:flex-row">
          <Link to="/register">
            <Button size="lg" className="w-full sm:w-auto">
              {t("home:hero.ctaPrimary")}
            </Button>
          </Link>
          <a href="#how-it-works">
            <Button size="lg" variant="secondary" className="w-full sm:w-auto">
              {t("home:hero.ctaSecondary")}
            </Button>
          </a>
        </div>
      </section>

      {/* Feature cards */}
      <section className="mx-auto mt-4 grid max-w-6xl gap-6 px-4 pb-12 sm:px-6 sm:grid-cols-3 lg:px-8">
        <Card>
          <div className="mb-3 grid h-10 w-10 place-items-center rounded-lg bg-brand-50 text-brand-600">
            <Bot size={20} />
          </div>
          <h3 className="text-lg font-semibold text-slate-900">{t("home:features.ai.title")}</h3>
          <p className="mt-1 text-sm text-slate-600">{t("home:features.ai.body")}</p>
        </Card>
        <Card>
          <div className="mb-3 grid h-10 w-10 place-items-center rounded-lg bg-brand-50 text-brand-600">
            <BarChart3 size={20} />
          </div>
          <h3 className="text-lg font-semibold text-slate-900">
            {t("home:features.comparison.title")}
          </h3>
          <p className="mt-1 text-sm text-slate-600">{t("home:features.comparison.body")}</p>
        </Card>
        <Card>
          <div className="mb-3 grid h-10 w-10 place-items-center rounded-lg bg-brand-50 text-brand-600">
            <Globe2 size={20} />
          </div>
          <h3 className="text-lg font-semibold text-slate-900">
            {t("home:features.austria.title")}
          </h3>
          <p className="mt-1 text-sm text-slate-600">{t("home:features.austria.body")}</p>
        </Card>
      </section>

      {/* Insurance types */}
      <section id="types" className="mx-auto max-w-6xl scroll-mt-20 px-4 pb-20 sm:px-6 lg:px-8">
        <h2 className="mb-6 text-center text-2xl font-bold text-slate-900">
          {t("home:insuranceTypesTitle")}
        </h2>
        <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
          {PRODUCT_LINES.map((line) => {
            const pair = productLinePair(t, line);
            return (
              <Card key={line} className="text-center">
                <div className="text-4xl">{PRODUCT_LINE_EMOJI[line]}</div>
                <p className="mt-2 font-semibold text-slate-900">{pair.en}</p>
                <p className="text-xs text-slate-500">{pair.at}</p>
              </Card>
            );
          })}
        </div>
      </section>

      {/* How it works */}
      <section
        id="how-it-works"
        className="scroll-mt-20 border-t border-slate-200 bg-white py-16"
      >
        <div className="mx-auto max-w-6xl px-4 sm:px-6 lg:px-8">
          <h2 className="mb-10 text-center text-2xl font-bold text-slate-900">
            {t("home:howItWorks.title")}
          </h2>
          <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
            {HOW_IT_WORKS_STEPS.map((step, idx) => (
              <div key={step} className="relative rounded-xl border border-slate-200 p-5">
                <span className="grid h-8 w-8 place-items-center rounded-full bg-brand-600 text-sm font-bold text-white">
                  {idx + 1}
                </span>
                <h3 className="mt-3 font-semibold text-slate-900">
                  {t(`home:howItWorks.steps.${step}.title`)}
                </h3>
                <p className="mt-1 text-sm text-slate-600">
                  {t(`home:howItWorks.steps.${step}.body`)}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Why InsureCompare / Beyond price comparison */}
      <section id="why" className="scroll-mt-20 bg-slate-50 py-16">
        <div className="mx-auto max-w-5xl px-4 sm:px-6 lg:px-8">
          <h2 className="text-center text-2xl font-bold text-slate-900">
            {t("home:whyInsureCompare.title")}
          </h2>
          <p className="mx-auto mt-3 max-w-2xl text-center text-slate-600">
            {t("home:whyInsureCompare.subtitle")}
          </p>

          <div className="mt-8 overflow-x-auto rounded-xl border border-slate-200 bg-white">
            <table className="min-w-full divide-y divide-slate-200 text-sm">
              <thead>
                <tr className="bg-slate-50 text-left text-xs uppercase tracking-wide text-slate-500">
                  <th className="px-4 py-3">{t("home:whyInsureCompare.matrix.dimension")}</th>
                  <th className="px-4 py-3">{t("home:whyInsureCompare.matrix.conventional")}</th>
                  <th className="px-4 py-3 text-brand-700">
                    {t("home:whyInsureCompare.matrix.insurecompare")}
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {MATRIX_ROWS.map((row) => (
                  <tr key={row}>
                    <td className="px-4 py-3 font-medium text-slate-800">
                      {t(`home:whyInsureCompare.matrix.rows.${row}`)}
                    </td>
                    <td className="px-4 py-3 text-slate-500">
                      {t(`home:whyInsureCompare.matrix.conventionalValues.${row}`)}
                    </td>
                    <td className="px-4 py-3">
                      <span className="inline-flex items-center gap-1.5 font-medium text-green-700">
                        <Check size={16} /> {t("common:status.yes")}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <p className="mt-3 flex items-start gap-1.5 text-xs text-slate-500">
            <Minus size={12} className="mt-0.5 shrink-0" />
            {t("home:whyInsureCompare.footnote")}
          </p>
        </div>
      </section>

      {/* About */}
      <section id="about" className="scroll-mt-20 mx-auto max-w-4xl px-4 py-16 sm:px-6 lg:px-8">
        <h2 className="text-center text-2xl font-bold text-slate-900">
          {t("navigation:about")}
        </h2>
        <p className="mx-auto mt-4 max-w-2xl text-center text-sm text-slate-600">
          {t("home:about.body")}
        </p>
      </section>
    </div>
  );
}
