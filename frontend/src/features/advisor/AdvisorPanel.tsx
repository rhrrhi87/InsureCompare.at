// File: frontend/src/features/advisor/AdvisorPanel.tsx
//
// The AI Policy Advisor: an evidence-grounded, RAG-based explanation panel
// embedded directly in the Upload page for a single processed document.
// Not a general chat interface (Part 15) — every answer surfaces Key
// points / Attention points / Source Evidence, and every piece of source
// evidence is rendered from the real database clause, never from
// LLM-generated text (Part 9 / Part 10).
import { useMutation, useQuery } from "@tanstack/react-query";
import { ChevronDown, ChevronUp, FileSearch } from "lucide-react";
import { useState } from "react";
import { useTranslation } from "react-i18next";

import { extractErrorMessage } from "@/api/client";
import { advisorApi } from "@/api/endpoints";
import { Alert, Badge, Spinner } from "@/components/ui";
import { Button } from "@/components/ui/Button";
import { cn } from "@/lib/cn";
import { formatPercent } from "@/lib/format";
import type { AdvisorAnswer, AdvisorEvidenceRef, AdvisorSummary } from "@/types/domain";

type Language = "de" | "en";

function useAdvisorLanguage(): Language {
  const { i18n } = useTranslation();
  return i18n.language.startsWith("de") ? "de" : "en";
}

export function AdvisorPanel({ uploadId }: { uploadId: number }) {
  const { t } = useTranslation("advisor");
  const language = useAdvisorLanguage();
  const [expanded, setExpanded] = useState(false);
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState<AdvisorAnswer | null>(null);

  // Fetched only once the panel is actually opened — never on every render,
  // and never repeated just because the user refreshes the page, since the
  // backend caches the summary per document (Part 22).
  const summaryQuery = useQuery({
    queryKey: ["advisor-summary", uploadId, language],
    queryFn: () => advisorApi.summary(uploadId, language),
    enabled: expanded,
    staleTime: Infinity,
  });

  const askMutation = useMutation({
    mutationFn: (q: string) => advisorApi.ask(uploadId, q, language),
    onSuccess: setAnswer,
  });

  const submitQuestion = (q: string) => {
    if (!q.trim() || askMutation.isPending) return;
    setAnswer(null);
    askMutation.mutate(q.trim());
  };

  const examples = t("ask.examples", { returnObjects: true }) as string[];

  return (
    <div className="mt-3 border-t border-slate-200 pt-3">
      <button
        type="button"
        onClick={() => setExpanded((v) => !v)}
        aria-expanded={expanded}
        className="flex items-center gap-2 text-sm font-semibold text-brand-700 hover:text-brand-800"
      >
        <FileSearch size={16} aria-hidden="true" />
        {t("title")}
        {expanded ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
      </button>

      {expanded && (
        <div className="mt-3 space-y-5">
          {summaryQuery.isLoading && (
            <div className="flex items-center gap-2 text-sm text-slate-500">
              <Spinner /> {t("loading")}
            </div>
          )}

          {summaryQuery.isError && (
            <Alert variant="error">{extractErrorMessage(summaryQuery.error)}</Alert>
          )}

          {summaryQuery.data && !summaryQuery.data.available && (
            <Alert variant="error">{t("unavailable")}</Alert>
          )}

          {summaryQuery.data?.summary && (
            <AdvisorOverview summary={summaryQuery.data.summary} evidence={summaryQuery.data.evidence} />
          )}

          {summaryQuery.data && !summaryQuery.data.summary && summaryQuery.data.available && (
            <p className="text-sm text-slate-500">{t("noEvidenceYet")}</p>
          )}

          <div>
            <h4 className="text-sm font-semibold text-slate-800">{t("ask.heading")}</h4>
            <form
              onSubmit={(e) => {
                e.preventDefault();
                submitQuestion(question);
              }}
              className="mt-2 flex gap-2"
            >
              <input
                className="input-field flex-1"
                placeholder={t("ask.placeholder")}
                value={question}
                onChange={(e) => setQuestion(e.target.value)}
                maxLength={500}
              />
              <Button type="submit" size="sm" loading={askMutation.isPending}>
                {t("ask.submit")}
              </Button>
            </form>
            <div className="mt-2 flex flex-wrap gap-1.5">
              {examples.slice(0, 4).map((example) => (
                <button
                  key={example}
                  type="button"
                  className="rounded-full border border-slate-200 px-2.5 py-1 text-[11px] text-slate-600 transition hover:bg-slate-50"
                  onClick={() => {
                    setQuestion(example);
                    submitQuestion(example);
                  }}
                >
                  {example}
                </button>
              ))}
            </div>

            {askMutation.isError && (
              <div className="mt-3">
                <Alert variant="error">{extractErrorMessage(askMutation.error)}</Alert>
              </div>
            )}

            {answer && <AdvisorAnswerCard answer={answer} />}
          </div>

          <p className="text-[11px] text-slate-500">{t("note")}</p>
        </div>
      )}
    </div>
  );
}

function AdvisorOverview({
  summary,
  evidence,
}: {
  summary: AdvisorSummary;
  evidence: AdvisorEvidenceRef[];
}) {
  const { t } = useTranslation("advisor");

  const fields: { label: string; value: string | null }[] = [
    { label: t("overview.insurer"), value: summary.insurer },
    { label: t("overview.insuranceType"), value: summary.insurance_type },
    { label: t("overview.productName"), value: summary.product_name },
    { label: t("overview.deductible"), value: summary.deductible },
    { label: t("overview.coverageLimits"), value: summary.coverage_limits },
    { label: t("overview.territorialScope"), value: summary.territorial_scope },
  ].filter((f) => f.value);

  return (
    <div className="space-y-4">
      <div>
        <h4 className="text-sm font-semibold text-slate-800">{t("overview.heading")}</h4>
        {fields.length > 0 && (
          <div className="mt-2 grid gap-2 text-xs sm:grid-cols-2">
            {fields.map((f) => (
              <div key={f.label}>
                <p className="uppercase tracking-wide text-slate-500">{f.label}</p>
                <p className="font-medium text-slate-700">{f.value}</p>
              </div>
            ))}
          </div>
        )}
        <BulletField label={t("overview.mainCoverages")} items={summary.main_coverages} />
        <BulletField label={t("overview.importantExclusions")} items={summary.important_exclusions} />
        <BulletField label={t("overview.majorConditions")} items={summary.major_conditions} />
      </div>

      {summary.strengths.length > 0 && (
        <div>
          <h4 className="text-sm font-semibold text-slate-800">{t("strengths.heading")}</h4>
          <ul className="mt-1 list-inside list-disc space-y-1 text-sm text-slate-600">
            {summary.strengths.map((s, i) => (
              <li key={i}>{s}</li>
            ))}
          </ul>
        </div>
      )}

      {summary.attention_points.length > 0 && (
        <div>
          <h4 className="text-sm font-semibold text-slate-800">{t("attentionPoints.heading")}</h4>
          <ul className="mt-1 list-inside list-disc space-y-1 text-sm text-amber-700">
            {summary.attention_points.map((s, i) => (
              <li key={i}>{s}</li>
            ))}
          </ul>
        </div>
      )}

      {evidence.length > 0 && <EvidenceList evidence={evidence} />}
    </div>
  );
}

function BulletField({ label, items }: { label: string; items: string[] }) {
  if (items.length === 0) return null;
  return (
    <div className="mt-2">
      <p className="text-[11px] uppercase tracking-wide text-slate-500">{label}</p>
      <ul className="mt-1 list-inside list-disc text-sm text-slate-700">
        {items.map((item, i) => (
          <li key={i}>{item}</li>
        ))}
      </ul>
    </div>
  );
}

function AdvisorAnswerCard({ answer }: { answer: AdvisorAnswer }) {
  const { t } = useTranslation("advisor");

  if (!answer.available) {
    return (
      <div className="mt-3">
        <Alert variant="error">{answer.answer}</Alert>
      </div>
    );
  }

  return (
    <div className="mt-3 rounded-lg border border-slate-200 bg-slate-50 p-4">
      <p className={cn("text-sm", answer.supported ? "text-slate-800" : "text-slate-600 italic")}>
        {answer.answer}
      </p>

      {answer.key_points.length > 0 && (
        <div className="mt-3">
          <p className="text-[11px] font-semibold uppercase tracking-wide text-slate-500">
            {t("answer.keyPoints")}
          </p>
          <ul className="mt-1 list-inside list-disc text-sm text-slate-700">
            {answer.key_points.map((p, i) => (
              <li key={i}>{p}</li>
            ))}
          </ul>
        </div>
      )}

      {answer.attention_points.length > 0 && (
        <div className="mt-3">
          <p className="text-[11px] font-semibold uppercase tracking-wide text-amber-700">
            {t("answer.attentionPoints")}
          </p>
          <ul className="mt-1 list-inside list-disc text-sm text-amber-700">
            {answer.attention_points.map((p, i) => (
              <li key={i}>{p}</li>
            ))}
          </ul>
        </div>
      )}

      {answer.evidence.length > 0 && <EvidenceList evidence={answer.evidence} document={answer.document} />}
    </div>
  );
}

function EvidenceList({
  evidence,
  document,
}: {
  evidence: AdvisorEvidenceRef[];
  document?: AdvisorAnswer["document"];
}) {
  const { t } = useTranslation(["advisor", "insurance"]);
  return (
    <div className="mt-3">
      <p className="text-[11px] font-semibold uppercase tracking-wide text-slate-500">
        {t("advisor:answer.sourceEvidence")}
      </p>
      {document && (document.detected_insurer || document.document_title) && (
        <p className="mt-1 text-xs font-medium text-slate-600">
          {[document.detected_insurer, document.document_title].filter(Boolean).join(" · ")}
        </p>
      )}
      <div className="mt-2 space-y-2">
        {evidence.map((e) => (
          <div key={e.clause_id} className="rounded-lg border border-slate-200 bg-white p-2">
            <div className="flex flex-wrap items-center gap-2">
              <Badge tone="info">{t(`insurance:clauseType.${e.clause_type}`)}</Badge>
              <Badge tone="neutral">
                {t(
                  `advisor:evidence.provenance.${e.provenance}`,
                  e.provenance,
                )}
              </Badge>
              {e.page_number != null && (
                <span className="text-[11px] text-slate-500">
                  {t("advisor:evidence.page", { page: e.page_number })}
                </span>
              )}
              <span className="text-[11px] text-slate-500">
                {t("advisor:evidence.confidence", { value: formatPercent(e.confidence) })}
              </span>
            </div>
            <p lang="de" className="mt-1 text-sm italic text-slate-700">
              "{e.text}"
            </p>
          </div>
        ))}
      </div>
    </div>
  );
}
