// File: frontend/src/features/auth/LoginPage.tsx
import { zodResolver } from "@hookform/resolvers/zod";
import { Shield, User as UserIcon, ShieldCheck } from "lucide-react";
import { useMemo } from "react";
import { useForm } from "react-hook-form";
import { useTranslation } from "react-i18next";
import { Link, useLocation } from "react-router-dom";
import { z } from "zod";

import { extractErrorMessage } from "@/api/client";
import { Button } from "@/components/ui/Button";
import { Alert, Card, Input, Label } from "@/components/ui";

import { useLogin } from "./useAuth";

type FormValues = { email: string; password: string };

const DEMO_USER = { email: "user@test.at", password: "user123" };
const DEMO_ADMIN = { email: "admin@insurance.at", password: "admin123" };

export default function LoginPage() {
  const { t } = useTranslation("auth");
  const location = useLocation() as { state?: { registered?: boolean } };
  const login = useLogin();

  const schema = useMemo(
    () =>
      z.object({
        email: z.string().email(t("validation.emailInvalid")),
        password: z.string().min(1, t("validation.passwordRequired")),
      }),
    [t],
  );

  const {
    register,
    handleSubmit,
    setValue,
    formState: { errors, isSubmitting },
  } = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: { email: "", password: "" },
  });

  const onSubmit = handleSubmit((values) => login.mutate(values));

  const fillDemoUser = () => {
    setValue("email", DEMO_USER.email);
    setValue("password", DEMO_USER.password);
  };
  const fillDemoAdmin = () => {
    setValue("email", DEMO_ADMIN.email);
    setValue("password", DEMO_ADMIN.password);
  };

  return (
    <div className="flex min-h-[80vh] items-center justify-center bg-slate-50 px-4">
      <Card className="w-full max-w-md">
        <div className="mb-6 flex flex-col items-center text-center">
          <span className="grid h-12 w-12 place-items-center rounded-xl bg-brand-600 text-white">
            <Shield size={22} />
          </span>
          <p className="mt-3 text-2xl font-bold text-slate-900">
            InsureCompare<span className="text-brand-600">.at</span>
          </p>
          <h1 className="mt-1 text-lg font-semibold text-slate-800">{t("login.welcomeBack")}</h1>
          <p className="text-sm text-slate-500">{t("login.signInToAccount")}</p>
        </div>

        {location.state?.registered && (
          <div className="mb-4">
            <Alert variant="success">{t("login.accountCreated")}</Alert>
          </div>
        )}

        {login.isError && (
          <div className="mb-4">
            <Alert variant="error">{extractErrorMessage(login.error)}</Alert>
          </div>
        )}

        <form onSubmit={onSubmit} className="space-y-4">
          <div>
            <Label htmlFor="email">{t("login.emailLabel")}</Label>
            <Input
              id="email"
              type="email"
              placeholder={t("login.emailPlaceholder")}
              autoComplete="email"
              {...register("email")}
            />
            {errors.email && (
              <p className="mt-1 text-xs text-red-600">{errors.email.message}</p>
            )}
          </div>

          <div>
            <Label htmlFor="password">{t("login.passwordLabel")}</Label>
            <Input
              id="password"
              type="password"
              placeholder={t("login.passwordPlaceholder")}
              autoComplete="current-password"
              {...register("password")}
            />
            {errors.password && (
              <p className="mt-1 text-xs text-red-600">{errors.password.message}</p>
            )}
          </div>

          <Button type="submit" className="w-full" loading={isSubmitting || login.isPending}>
            {t("login.submit")}
          </Button>
        </form>

        <div className="mt-6 border-t border-slate-200 pt-4">
          <p className="mb-2 text-center text-xs uppercase tracking-wide text-slate-500">
            {t("login.demoAccounts")}
          </p>
          <div className="flex flex-col gap-2">
            <button
              type="button"
              onClick={fillDemoUser}
              className="flex items-center gap-2 rounded-lg bg-slate-100 px-3 py-2 text-sm text-slate-700 hover:bg-slate-200"
            >
              <UserIcon size={16} />
              {t("login.loginAsUser", { email: DEMO_USER.email })}
            </button>
            <button
              type="button"
              onClick={fillDemoAdmin}
              className="flex items-center gap-2 rounded-lg bg-slate-100 px-3 py-2 text-sm text-slate-700 hover:bg-slate-200"
            >
              <ShieldCheck size={16} />
              {t("login.loginAsAdmin", { email: DEMO_ADMIN.email })}
            </button>
          </div>
        </div>

        <p className="mt-6 text-center text-sm text-slate-600">
          {t("login.noAccount")}{" "}
          <Link to="/register" className="font-medium text-brand-600 hover:underline">
            {t("login.registerHere")}
          </Link>
        </p>
        <p className="mt-2 text-center text-xs text-slate-500">
          <Link to="/">{t("login.backToHome")}</Link>
        </p>
      </Card>
    </div>
  );
}
