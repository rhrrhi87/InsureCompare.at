// File: frontend/src/features/admin/AdminProvidersPage.tsx
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Plus, ShieldCheck, ShieldOff } from "lucide-react";
import { useState } from "react";
import { useTranslation } from "react-i18next";

import { extractErrorMessage } from "@/api/client";
import { policyApi, providerApi } from "@/api/endpoints";
import { Alert, Badge, Card, Input, Label, Spinner } from "@/components/ui";
import { Button } from "@/components/ui/Button";
import { ProviderLogo } from "@/components/ui/ProviderLogo";
import type { Provider } from "@/types/domain";

type ProviderFormValues = {
  name: string;
  country: string;
  rating_score: number;
};

const EMPTY_FORM: ProviderFormValues = { name: "", country: "AT", rating_score: 8.0 };

export default function AdminProvidersPage() {
  const { t } = useTranslation("admin");
  const qc = useQueryClient();
  const [creating, setCreating] = useState(false);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [form, setForm] = useState<ProviderFormValues>(EMPTY_FORM);

  const providers = useQuery<Provider[]>({
    queryKey: ["providers"],
    queryFn: policyApi.listProviders,
  });

  const create = useMutation({
    mutationFn: () => providerApi.create(form),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["providers"] });
      setCreating(false);
      setForm(EMPTY_FORM);
    },
  });

  const update = useMutation({
    mutationFn: (id: number) => providerApi.update(id, form),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["providers"] });
      setEditingId(null);
    },
  });

  const toggleActive = useMutation({
    mutationFn: (p: Provider) =>
      p.is_active ? providerApi.deactivate(p.id) : providerApi.reactivate(p.id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["providers"] }),
  });

  const startEdit = (p: Provider) => {
    setEditingId(p.id);
    setCreating(false);
    setForm({ name: p.name, country: p.country, rating_score: p.rating_score });
  };

  const mutationError = create.error ?? update.error ?? toggleActive.error;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-slate-900">{t("providers.title")}</h1>
        <Button
          size="sm"
          onClick={() => {
            setCreating((v) => !v);
            setEditingId(null);
            setForm(EMPTY_FORM);
          }}
        >
          <Plus size={16} className="mr-1.5" />
          {t("providers.create")}
        </Button>
      </div>

      {mutationError ? <Alert variant="error">{extractErrorMessage(mutationError)}</Alert> : null}

      {creating && (
        <ProviderForm
          form={form}
          setForm={setForm}
          onSubmit={() => create.mutate()}
          onCancel={() => setCreating(false)}
          loading={create.isPending}
          submitLabel={t("common:actions.save")}
        />
      )}

      <Card>
        {providers.isLoading ? (
          <Spinner />
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-slate-200 text-sm">
              <thead>
                <tr className="text-left text-xs uppercase tracking-wide text-slate-500">
                  <th className="px-2 py-2">{t("providers.columns.name")}</th>
                  <th className="px-2 py-2">{t("providers.columns.country")}</th>
                  <th className="px-2 py-2">{t("providers.columns.rating")}</th>
                  <th className="px-2 py-2">{t("policies.columns.status")}</th>
                  <th className="px-2 py-2">{t("providers.columns.actions")}</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {providers.data?.map((p) =>
                  editingId === p.id ? (
                    <tr key={p.id}>
                      <td colSpan={5} className="px-2 py-3">
                        <ProviderForm
                          form={form}
                          setForm={setForm}
                          onSubmit={() => update.mutate(p.id)}
                          onCancel={() => setEditingId(null)}
                          loading={update.isPending}
                          submitLabel={t("common:actions.save")}
                          inline
                        />
                      </td>
                    </tr>
                  ) : (
                    <tr key={p.id}>
                      <td className="px-2 py-3 font-medium text-slate-800">
                        <div className="flex items-center gap-2">
                          <ProviderLogo provider={p} size={20} />
                          {p.name}
                        </div>
                      </td>
                      <td className="px-2 py-3">{p.country}</td>
                      <td className="px-2 py-3">{p.rating_score.toFixed(1)}</td>
                      <td className="px-2 py-3">
                        <Badge tone={p.is_active ? "low" : "neutral"}>
                          {p.is_active ? t("policies.statusActive") : t("policies.statusRetired")}
                        </Badge>
                      </td>
                      <td className="px-2 py-3">
                        <div className="flex gap-2">
                          <Button size="sm" variant="secondary" onClick={() => startEdit(p)}>
                            {t("providers.edit")}
                          </Button>
                          <Button
                            size="sm"
                            variant={p.is_active ? "danger" : "secondary"}
                            onClick={() => toggleActive.mutate(p)}
                            loading={toggleActive.isPending}
                          >
                            {p.is_active ? (
                              <ShieldOff size={14} className="mr-1" />
                            ) : (
                              <ShieldCheck size={14} className="mr-1" />
                            )}
                            {p.is_active ? t("policies.retire") : t("policies.reactivate")}
                          </Button>
                        </div>
                      </td>
                    </tr>
                  ),
                )}
              </tbody>
            </table>
          </div>
        )}
      </Card>
    </div>
  );
}

function ProviderForm({
  form,
  setForm,
  onSubmit,
  onCancel,
  loading,
  submitLabel,
  inline,
}: {
  form: ProviderFormValues;
  setForm: (f: ProviderFormValues) => void;
  onSubmit: () => void;
  onCancel: () => void;
  loading: boolean;
  submitLabel: string;
  inline?: boolean;
}) {
  const { t } = useTranslation("common");
  return (
    <Card className={inline ? "bg-slate-50" : undefined}>
      <div className="grid gap-4 sm:grid-cols-3">
        <div>
          <Label htmlFor="provider-name">{t("terms.provider", { ns: "insurance" })}</Label>
          <Input
            id="provider-name"
            value={form.name}
            onChange={(e) => setForm({ ...form, name: e.target.value })}
          />
        </div>
        <div>
          <Label htmlFor="provider-country">Country</Label>
          <Input
            id="provider-country"
            maxLength={2}
            value={form.country}
            onChange={(e) => setForm({ ...form, country: e.target.value.toUpperCase() })}
          />
        </div>
        <div>
          <Label htmlFor="provider-rating">Rating (0-10)</Label>
          <Input
            id="provider-rating"
            type="number"
            min={0}
            max={10}
            step={0.1}
            value={form.rating_score}
            onChange={(e) => setForm({ ...form, rating_score: Number(e.target.value) })}
          />
        </div>
      </div>
      <div className="mt-4 flex gap-2">
        <Button size="sm" onClick={onSubmit} loading={loading} disabled={!form.name}>
          {submitLabel}
        </Button>
        <Button size="sm" variant="secondary" onClick={onCancel}>
          {t("actions.cancel")}
        </Button>
      </div>
    </Card>
  );
}
