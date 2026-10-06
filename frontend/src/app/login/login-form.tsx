"use client";

import { useRouter, useSearchParams } from "next/navigation";
import { useId, useState } from "react";
import { ArrowRight } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Field, Input } from "@/components/ui/input";
import { dictionaries, translator, type Locale, type MessageKey } from "@/lib/i18n";

/** Body shape returned by POST /api/session (src/app/api/session/route.ts). */
interface SessionError {
  error?: { code: string; message: string };
}

const CODE_KEY: Record<string, MessageKey> = {
  INVALID_PASSCODE: "login.error.invalid",
  RATE_LIMITED: "login.error.rate",
  NOT_CONFIGURED: "login.error.notConfigured",
};

export function LoginForm({ locale }: { locale: Locale }) {
  const t = translator(dictionaries[locale]);
  const id = useId();
  const router = useRouter();
  const params = useSearchParams();
  const next = params.get("next");
  const safeNext = next && next.startsWith("/") && !next.startsWith("//") ? next : "/dashboard";

  const [passcode, setPasscode] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [pending, setPending] = useState(false);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    const value = passcode.trim();
    if (!value) return setError(t("login.error.empty"));
    setError(null);
    setPending(true);
    try {
      const res = await fetch("/api/session", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ passcode: value }),
      });
      if (!res.ok) {
        const body: SessionError = await res.json().catch(() => ({}));
        const key = body.error ? CODE_KEY[body.error.code] : undefined;
        setError(key ? t(key) : (body.error?.message ?? t("login.error.generic")));
        return;
      }
      router.push(safeNext);
      router.refresh();
    } catch {
      setError(t("login.error.generic"));
    } finally {
      setPending(false);
    }
  }

  return (
    <form onSubmit={submit} noValidate className="mt-8 grid gap-5">
      <Field label={t("login.label")} htmlFor={id} error={error}>
        <Input
          id={id}
          name="passcode"
          type="password"
          autoComplete="current-password"
          autoFocus
          mono
          placeholder={t("login.placeholder")}
          value={passcode}
          onChange={(e) => {
            setPasscode(e.target.value);
            if (error) setError(null);
          }}
          aria-invalid={error ? true : undefined}
          aria-describedby={error ? `${id}-error` : undefined}
        />
      </Field>
      <Button type="submit" size="lg" disabled={pending} className="w-full">
        {pending ? t("login.submitting") : t("login.submit")}
        {pending ? null : <ArrowRight className="size-5" strokeWidth={1.5} aria-hidden="true" />}
      </Button>
      <Button type="button" variant="link" onClick={() => router.push("/")} className="justify-self-start">
        {t("login.back")}
      </Button>
    </form>
  );
}
