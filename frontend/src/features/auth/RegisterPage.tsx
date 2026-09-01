// File: frontend/src/features/auth/RegisterPage.tsx
import { zodResolver } from "@hookform/resolvers/zod";
import { Shield } from "lucide-react";
import { useMemo } from "react";
import { useForm } from "react-hook-form";
import { useTranslation } from "react-i18next";
import { Link } from "react-router-dom";
import { z } from "zod";

import { extractErrorMessage } from "@/api/client";
import { Button } from "@/components/ui/Button";
import { Alert, Card, Input, Label } from "@/components/ui";

import { useRegister } from "./useAuth";

type FormValues = {
  full_name: string;
  email: string;
  password: string;
  confirm: string;
};

export default function RegisterPage() {
  const { t } = useTranslation("auth");
  const register_ = useRegister();

  const schema = useMemo(
    () =>
      z
        .object({
          full_name: z.string().min(2, t("validation.nameRequired")).max(120),
          email: z.string().email(t("validation.emailInvalid")),
          password: z.string().min(6, t("validation.passwordMinLength")),
          confirm: z.string().min(6, t("validation.confirmRequired")),
        })
        .refine((data) => data.password === data.confirm, {
          path: ["confirm"],
          message: t("validation.passwordsMustMatch"),
        }),
    [t],
  );

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<FormValues>({ resolver: zodResolver(schema) });

  const onSubmit = handleSubmit(({ confirm: _c, ...rest }) =>
    register_.mutate(rest),
  );

  return (
    <div className="flex min-h-[80vh] items-center justify-center px-4">
      <Card className="w-full max-w-md">
        <div className="mb-6 flex flex-col items-center text-center">
          <span className="grid h-12 w-12 place-items-center rounded-xl bg-brand-600 text-white">
            <Shield size={22} />
          </span>
          <h1 className="mt-3 text-xl font-semibold">{t("register.title")}</h1>
          <p className="text-sm text-slate-500">{t("register.subtitle")}</p>
        </div>

        {register_.isError && (
          <div className="mb-4">
            <Alert variant="error">{extractErrorMessage(register_.error)}</Alert>
          </div>
        )}

        <form onSubmit={onSubmit} className="space-y-4">
          <div>
            <Label htmlFor="full_name">{t("register.fullNameLabel")}</Label>
            <Input
              id="full_name"
              placeholder={t("register.fullNamePlaceholder")}
              {...register("full_name")}
            />
            {errors.full_name && (
              <p className="mt-1 text-xs text-red-600">{errors.full_name.message}</p>
            )}
          </div>
          <div>
            <Label htmlFor="email">{t("register.emailLabel")}</Label>
            <Input
              id="email"
              type="email"
              placeholder={t("register.emailPlaceholder")}
              {...register("email")}
            />
            {errors.email && (
              <p className="mt-1 text-xs text-red-600">{errors.email.message}</p>
            )}
          </div>
          <div>
            <Label htmlFor="password">{t("register.passwordLabel")}</Label>
            <Input
              id="password"
              type="password"
              placeholder={t("register.passwordPlaceholder")}
              {...register("password")}
            />
            {errors.password && (
              <p className="mt-1 text-xs text-red-600">{errors.password.message}</p>
            )}
          </div>
          <div>
            <Label htmlFor="confirm">{t("register.confirmLabel")}</Label>
            <Input
              id="confirm"
              type="password"
              placeholder={t("register.confirmPlaceholder")}
              {...register("confirm")}
            />
            {errors.confirm && (
              <p className="mt-1 text-xs text-red-600">{errors.confirm.message}</p>
            )}
          </div>

          <Button type="submit" className="w-full" loading={isSubmitting || register_.isPending}>
            {t("register.submit")}
          </Button>
        </form>

        <p className="mt-6 text-center text-sm text-slate-600">
          {t("register.haveAccount")}{" "}
          <Link to="/login" className="font-medium text-brand-600 hover:underline">
            {t("register.signInHere")}
          </Link>
        </p>
      </Card>
    </div>
  );
}
