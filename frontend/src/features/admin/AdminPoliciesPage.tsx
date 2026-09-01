// File: frontend/src/features/admin/AdminPoliciesPage.tsx
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Plus, RotateCcw, ShieldOff } from "lucide-react";
import { useMemo, useState } from "react";
import { useTranslation } from "react-i18next";

import { extractErrorMessage } from "@/api/client";
import { policyApi } from "@/api/endpoints";
import { Alert, Badge, Card, Input, Label, Select, Spinner } from "@/components/ui";
import { Button } from "@/components/ui/Button";
import { formatEur } from "@/lib/format";
import { productLineLabel as translateProductLine } from "@/lib/i18nInsurance";
import type { Policy, ProductLine, Provider, RiskLevel } from "@/types/domain";

type PolicyFormValues = {
  provider_id: number | "";
  name: string;
  product_line: ProductLine;
  monthly_premium_eur: number;
  annual_premium_eur: number;
  deductible_eur: number;
  coverage_limit_eur: number;
  risk_level: RiskLevel;
  coverage_items: string;
  additional_features: string;
  exclusions: string;
  description: string;
  is_demo_data: boolean;
  document_title: string;
  document_type: string;
  source_url: string;
  source_organisation: string;
};

const EMPTY_FORM: PolicyFormValues = {
  provider_id: "",
  name: "",
  product_line: "car",
  monthly_premium_eur: 0,
  annual_premium_eur: 0,
  deductible_eur: 0,
  coverage_limit_eur: 0,
  risk_level: "medium",
  coverage_items: "",
  additional_features: "",
  exclusions: "",
  description: "",
  is_demo_data: true,
  document_title: "",
  document_type: "",
  source_url: "",
  source_organisation: "",
};

function toPayload(form: PolicyFormValues) {
  const csv = (s: string) =>
    s.split(",").map((x) => x.trim()).filter(Boolean);
  return {
    provider_id: Number(form.provider_id),
    name: form.name,
    product_line: form.product_line,
    monthly_premium_eur: form.monthly_premium_eur,
    annual_premium_eur: form.annual_premium_eur,
    deductible_eur: form.deductible_eur,
    coverage_limit_eur: form.coverage_limit_eur,
    risk_level: form.risk_level,
    coverage_items: csv(form.coverage_items),
    additional_features: csv(form.additional_features),
    exclusions: csv(form.exclusions),
    description: form.description || null,
    is_demo_data: form.is_demo_data,
    document_title: form.document_title || null,
    document_type: form.document_type || null,
    source_url: form.source_url || null,
    source_organisation: form.source_organisation || null,
  };
}

function fromPolicy(p: Policy): PolicyFormValues {
  return {
    provider_id: p.provider_id,
    name: p.name,
    product_line: p.product_line,
    monthly_premium_eur: p.monthly_premium_eur,
    annual_premium_eur: p.annual_premium_eur,
    deductible_eur: p.deductible_eur,
    coverage_limit_eur: p.coverage_limit_eur,
    risk_level: p.risk_level,
    coverage_items: p.coverage_items.join(", "),
    additional_features: p.additional_features.join(", "),
    exclusions: p.exclusions.join(", "),
    description: p.description ?? "",
    is_demo_data: p.is_demo_data,
    document_title: p.document_title ?? "",
    document_type: p.document_type ?? "",
    source_url: p.source_url ?? "",
    source_organisation: p.source_organisation ?? "",
  };
}

export default function AdminPoliciesPage() {
  const { t, i18n } = useTranslation(["admin", "insurance", "common"]);
  const qc = useQueryClient();
  const providers = useQuery<Provider[]>({
    queryKey: ["providers"],
    queryFn: policyApi.listProviders,
  });

  const [statusFilter, setStatusFilter] = useState<"all" | "active" | "retired">("all");
  const [lineFilter, setLineFilter] = useState<ProductLine | "all">("all");
  const [search, setSearch] = useState("");
  const [creating, setCreating] = useState(false);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [form, setForm] = useState<PolicyFormValues>(EMPTY_FORM);

  const policies = useQuery<Policy[]>({
    queryKey: ["admin", "policies", "all"],
    queryFn: () => policyApi.list({ active_only: false }),
  });

  const filtered = useMemo(() => {
    return (policies.data ?? []).filter((p) => {
      if (statusFilter === "active" && !p.is_active) return false;
      if (statusFilter === "retired" && p.is_active) return false;
      if (lineFilter !== "all" && p.product_line !== lineFilter) return false;
      if (search && !p.name.toLowerCase().includes(search.toLowerCase())) return false;
      return true;
    });
  }, [policies.data, statusFilter, lineFilter, search]);

  const invalidate = () => qc.invalidateQueries({ queryKey: ["admin", "policies", "all"] });

  const create = useMutation({
    mutationFn: () => policyApi.create(toPayload(form)),
    onSuccess: () => {
      invalidate();
      setCreating(false);
      setForm(EMPTY_FORM);
    },
  });

  const update = useMutation({
    mutationFn: (id: number) => policyApi.update(id, toPayload(form)),
    onSuccess: () => {
      invalidate();
      setEditingId(null);
    },
  });

  const retire = useMutation({
    mutationFn: (id: number) => policyApi.retire(id),
    onSuccess: invalidate,
  });

  const reactivate = useMutation({
    mutationFn: (id: number) => policyApi.reactivate(id),
    onSuccess: invalidate,
  });

  const mutationError = create.error ?? update.error ?? retire.error ?? reactivate.error;

  const startEdit = (p: Policy) => {
    setEditingId(p.id);
    setCreating(false);
    setForm(fromPolicy(p));
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h1 className="text-2xl font-bold text-slate-900">{t("admin:policies.title")}</h1>
        <Button
          size="sm"
          onClick={() => {
            setCreating((v) => !v);
            setEditingId(null);
            setForm(EMPTY_FORM);
          }}
        >
          <Plus size={16} className="mr-1.5" />
          {t("admin:policies.create")}
        </Button>
      </div>

      {mutationError ? <Alert variant="error">{extractErrorMessage(mutationError)}</Alert> : null}

      <Card>
        <div className="flex flex-wrap items-center gap-4">
          <Input
            placeholder={t("admin:policies.search")}
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-56"
          />
          <div>
            <label htmlFor="admin-policy-status-filter" className="mr-2 text-sm text-slate-600">
              {t("admin:policies.filterStatus")}:
            </label>
            <Select
              id="admin-policy-status-filter"
              className="inline-block w-auto"
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value as typeof statusFilter)}
            >
              <option value="all">—</option>
              <option value="active">{t("admin:policies.statusActive")}</option>
              <option value="retired">{t("admin:policies.statusRetired")}</option>
            </Select>
          </div>
          <div>
            <label htmlFor="admin-policy-line-filter" className="mr-2 text-sm text-slate-600">
              {t("admin:policies.filterLine")}:
            </label>
            <Select
              id="admin-policy-line-filter"
              className="inline-block w-auto"
              value={lineFilter}
              onChange={(e) => setLineFilter(e.target.value as typeof lineFilter)}
            >
              <option value="all">—</option>
              {(["car", "household", "travel", "legal"] as ProductLine[]).map((line) => (
                <option key={line} value={line}>
                  {translateProductLine(t, i18n.language, line)}
                </option>
              ))}
            </Select>
          </div>
        </div>
      </Card>

      {(creating || editingId !== null) && (
        <PolicyForm
          form={form}
          setForm={setForm}
          providers={providers.data ?? []}
          onSubmit={() => (editingId !== null ? update.mutate(editingId) : create.mutate())}
          onCancel={() => {
            setCreating(false);
            setEditingId(null);
          }}
          loading={create.isPending || update.isPending}
        />
      )}

      <Card>
        {policies.isLoading ? (
          <Spinner />
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-slate-200 text-sm">
              <thead>
                <tr className="text-left text-xs uppercase tracking-wide text-slate-500">
                  <th className="px-2 py-2">{t("admin:policies.columns.name")}</th>
                  <th className="px-2 py-2">{t("admin:policies.columns.provider")}</th>
                  <th className="px-2 py-2">{t("admin:policies.columns.line")}</th>
                  <th className="px-2 py-2">{t("admin:policies.columns.premium")}</th>
                  <th className="px-2 py-2">{t("admin:policies.columns.status")}</th>
                  <th className="px-2 py-2">{t("admin:policies.columns.actions")}</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {filtered.map((p) => (
                  <tr key={p.id}>
                    <td className="px-2 py-3 font-medium text-slate-800">
                      {p.name}
                      {p.is_demo_data && (
                        <span className="ml-2 text-[10px] uppercase text-slate-500">
                          {t("common:demoData.label")}
                        </span>
                      )}
                    </td>
                    <td className="px-2 py-3">{p.provider?.name ?? p.provider_id}</td>
                    <td className="px-2 py-3">{translateProductLine(t, i18n.language, p.product_line)}</td>
                    <td className="px-2 py-3">{formatEur(p.monthly_premium_eur)}</td>
                    <td className="px-2 py-3">
                      <Badge tone={p.is_active ? "low" : "neutral"}>
                        {p.is_active ? t("admin:policies.statusActive") : t("admin:policies.statusRetired")}
                      </Badge>
                    </td>
                    <td className="px-2 py-3">
                      <div className="flex gap-2">
                        <Button size="sm" variant="secondary" onClick={() => startEdit(p)}>
                          {t("admin:policies.edit")}
                        </Button>
                        {p.is_active ? (
                          <Button
                            size="sm"
                            variant="danger"
                            onClick={() => retire.mutate(p.id)}
                            loading={retire.isPending}
                          >
                            <ShieldOff size={14} className="mr-1" />
                            {t("admin:policies.retire")}
                          </Button>
                        ) : (
                          <Button
                            size="sm"
                            variant="secondary"
                            onClick={() => reactivate.mutate(p.id)}
                            loading={reactivate.isPending}
                          >
                            <RotateCcw size={14} className="mr-1" />
                            {t("admin:policies.reactivate")}
                          </Button>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
                {filtered.length === 0 && (
                  <tr>
                    <td colSpan={6} className="px-2 py-6 text-center text-slate-500">
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

function PolicyForm({
  form,
  setForm,
  providers,
  onSubmit,
  onCancel,
  loading,
}: {
  form: PolicyFormValues;
  setForm: (f: PolicyFormValues) => void;
  providers: Provider[];
  onSubmit: () => void;
  onCancel: () => void;
  loading: boolean;
}) {
  const { t } = useTranslation(["admin", "insurance", "common"]);
  const set = <K extends keyof PolicyFormValues>(key: K, value: PolicyFormValues[K]) =>
    setForm({ ...form, [key]: value });

  return (
    <Card className="space-y-4">
      <div className="grid gap-4 sm:grid-cols-3">
        <div>
          <Label>{t("insurance:terms.provider")}</Label>
          <Select value={form.provider_id} onChange={(e) => set("provider_id", Number(e.target.value))}>
            <option value="">—</option>
            {providers.map((p) => (
              <option key={p.id} value={p.id}>
                {p.name}
              </option>
            ))}
          </Select>
        </div>
        <div>
          <Label>Name</Label>
          <Input value={form.name} onChange={(e) => set("name", e.target.value)} />
        </div>
        <div>
          <Label>{t("insurance:productLines.car.en")} / ...</Label>
          <Select
            value={form.product_line}
            onChange={(e) => set("product_line", e.target.value as ProductLine)}
          >
            <option value="car">{t("insurance:productLines.car.en")}</option>
            <option value="household">{t("insurance:productLines.household.en")}</option>
            <option value="travel">{t("insurance:productLines.travel.en")}</option>
            <option value="legal">{t("insurance:productLines.legal.en")}</option>
          </Select>
        </div>
      </div>

      <div className="grid gap-4 sm:grid-cols-4">
        <div>
          <Label>{t("insurance:terms.monthlyPremium")} (€)</Label>
          <Input
            type="number"
            value={form.monthly_premium_eur}
            onChange={(e) => set("monthly_premium_eur", Number(e.target.value))}
          />
        </div>
        <div>
          <Label>{t("insurance:terms.annualPremium")} (€)</Label>
          <Input
            type="number"
            value={form.annual_premium_eur}
            onChange={(e) => set("annual_premium_eur", Number(e.target.value))}
          />
        </div>
        <div>
          <Label>{t("insurance:terms.deductible")} (€)</Label>
          <Input
            type="number"
            value={form.deductible_eur}
            onChange={(e) => set("deductible_eur", Number(e.target.value))}
          />
        </div>
        <div>
          <Label>{t("insurance:terms.coverageLimit")} (€)</Label>
          <Input
            type="number"
            value={form.coverage_limit_eur}
            onChange={(e) => set("coverage_limit_eur", Number(e.target.value))}
          />
        </div>
      </div>

      <div>
        <Label>{t("insurance:riskLevel.low")} / {t("insurance:riskLevel.medium")} / {t("insurance:riskLevel.high")}</Label>
        <Select value={form.risk_level} onChange={(e) => set("risk_level", e.target.value as RiskLevel)}>
          <option value="low">{t("insurance:riskLevel.low")}</option>
          <option value="medium">{t("insurance:riskLevel.medium")}</option>
          <option value="high">{t("insurance:riskLevel.high")}</option>
        </Select>
      </div>

      <div className="grid gap-4 sm:grid-cols-3">
        <div>
          <Label>{t("insurance:terms.coverage")} (comma-separated)</Label>
          <Input value={form.coverage_items} onChange={(e) => set("coverage_items", e.target.value)} />
        </div>
        <div>
          <Label>{t("insurance:terms.additionalFeatures")} (comma-separated)</Label>
          <Input
            value={form.additional_features}
            onChange={(e) => set("additional_features", e.target.value)}
          />
        </div>
        <div>
          <Label>{t("insurance:terms.exclusions")} (comma-separated)</Label>
          <Input value={form.exclusions} onChange={(e) => set("exclusions", e.target.value)} />
        </div>
      </div>

      <div className="rounded-lg border border-slate-200 p-4">
        <label className="flex items-center gap-2 text-sm font-medium text-slate-700">
          <input
            type="checkbox"
            checked={form.is_demo_data}
            onChange={(e) => set("is_demo_data", e.target.checked)}
          />
          {t("common:demoData.label")} (uncheck once a real public source document is cited below)
        </label>
        {!form.is_demo_data && (
          <div className="mt-3 grid gap-4 sm:grid-cols-2">
            <div>
              <Label>Document title</Label>
              <Input
                value={form.document_title}
                onChange={(e) => set("document_title", e.target.value)}
                placeholder="e.g. IPID – Kfz-Haftpflichtversicherung"
              />
            </div>
            <div>
              <Label>Document type</Label>
              <Input
                value={form.document_type}
                onChange={(e) => set("document_type", e.target.value)}
                placeholder="IPID / AVB"
              />
            </div>
            <div>
              <Label>Source URL</Label>
              <Input value={form.source_url} onChange={(e) => set("source_url", e.target.value)} />
            </div>
            <div>
              <Label>Source organisation</Label>
              <Input
                value={form.source_organisation}
                onChange={(e) => set("source_organisation", e.target.value)}
              />
            </div>
          </div>
        )}
      </div>

      <div className="flex gap-2">
        <Button
          size="sm"
          onClick={onSubmit}
          loading={loading}
          disabled={!form.name || !form.provider_id}
        >
          {t("common:actions.save")}
        </Button>
        <Button size="sm" variant="secondary" onClick={onCancel}>
          {t("common:actions.cancel")}
        </Button>
      </div>
    </Card>
  );
}
