"use client";

import { useRouter, useSearchParams } from "next/navigation";
import { useId, useState } from "react";
import { AlertCircle, ArrowRight, AtSign, Eye, EyeOff, Loader2, Lock, Sparkles } from "lucide-react";
import { dictionaries, translator, type Locale, type MessageKey } from "@/lib/i18n";

/** Body shape returned by POST /api/session (src/app/api/session/route.ts). */
interface SessionError {
  error?: { code: string; message: string };
}

const CODE_KEY: Record<string, MessageKey> = {
  INVALID_PASSCODE: "login.error.invalid",
  MERCHANT_NOT_FOUND: "login.error.notFound",
  RATE_LIMITED: "login.error.rate",
  NOT_CONFIGURED: "login.error.notConfigured",
};

export function LoginForm({ locale }: { locale: Locale }) {
  const t = translator(dictionaries[locale]);
  const identifierId = useId();
  const passcodeId = useId();
  const router = useRouter();
  const params = useSearchParams();
  const next = params.get("next");
  const safeNext = next && next.startsWith("/") && !next.startsWith("//") ? next : "/dashboard";

  const [identifier, setIdentifier] = useState("");
  const [passcode, setPasscode] = useState("");
  const [showPasscode, setShowPasscode] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [pending, setPending] = useState(false);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    const cleanPasscode = passcode.trim();
    if (!cleanPasscode) {
      setError(t("login.error.empty"));
      return;
    }

    setError(null);
    setPending(true);

    try {
      const res = await fetch("/api/session", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({
          identifier: identifier.trim() || undefined,
          passcode: cleanPasscode,
        }),
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

  function fillDemo(slug: string) {
    setIdentifier(slug);
    setPasscode("halisi-demo");
    setError(null);
  }

  return (
    <form onSubmit={submit} noValidate className="mt-8 space-y-5">
      {/* Error Banner with smooth entry */}
      {error && (
        <div
          role="alert"
          className="flex items-start gap-3 rounded-xl border border-fake/30 bg-fake/10 p-3.5 text-xs text-fake transition-all duration-150 ease-out animate-in fade-in slide-in-from-top-1"
        >
          <AlertCircle className="size-4 shrink-0 mt-0.5" strokeWidth={2} />
          <div className="flex-1 font-medium leading-relaxed">{error}</div>
        </div>
      )}

      {/* Input 1: Business Identifier */}
      <div className="space-y-1.5">
        <label htmlFor={identifierId} className="block text-xs font-mono uppercase tracking-[0.14em] text-fg-3 font-medium">
          {t("login.identifierLabel")}
        </label>
        <div className="relative flex items-center">
          <div className="pointer-events-none absolute left-3.5 flex items-center justify-center text-fg-3">
            <AtSign className="size-4" strokeWidth={1.5} />
          </div>
          <input
            id={identifierId}
            name="identifier"
            type="text"
            autoCapitalize="none"
            autoCorrect="off"
            spellCheck={false}
            autoComplete="username"
            placeholder={t("login.identifierPlaceholder")}
            value={identifier}
            onChange={(e) => {
              setIdentifier(e.target.value);
              if (error) setError(null);
            }}
            className="h-12 w-full rounded-xl border border-line-strong bg-bg-3/30 pl-10 pr-4 text-sm text-fg placeholder:text-fg-3/50 transition-all duration-150 ease-out hover:border-fg/40 focus:border-fg focus:bg-bg/90 focus:outline-none focus:ring-2 focus:ring-fg/20"
          />
        </div>
        <p className="text-[11px] text-fg-3 leading-normal">
          Slug, business name, or @handle (defaults to Nairobi Sneaker Vault)
        </p>
      </div>

      {/* Input 2: Dashboard Passcode */}
      <div className="space-y-1.5">
        <div className="flex items-center justify-between">
          <label htmlFor={passcodeId} className="block text-xs font-mono uppercase tracking-[0.14em] text-fg-3 font-medium">
            {t("login.passcodeLabel")}
          </label>
        </div>
        <div className="relative flex items-center">
          <div className="pointer-events-none absolute left-3.5 flex items-center justify-center text-fg-3">
            <Lock className="size-4" strokeWidth={1.5} />
          </div>
          <input
            id={passcodeId}
            name="passcode"
            type={showPasscode ? "text" : "password"}
            autoComplete="current-password"
            placeholder={t("login.placeholder")}
            value={passcode}
            onChange={(e) => {
              setPasscode(e.target.value);
              if (error) setError(null);
            }}
            className="h-12 w-full rounded-xl border border-line-strong bg-bg-3/30 pl-10 pr-11 font-mono text-sm tracking-wider text-fg placeholder:font-sans placeholder:tracking-normal placeholder:text-fg-3/50 transition-all duration-150 ease-out hover:border-fg/40 focus:border-fg focus:bg-bg/90 focus:outline-none focus:ring-2 focus:ring-fg/20"
          />
          <button
            type="button"
            onClick={() => setShowPasscode(!showPasscode)}
            className="absolute right-3.5 p-1 text-fg-3 hover:text-fg transition-transform duration-100 ease-out active:scale-90"
            aria-label={showPasscode ? "Hide password" : "Show password"}
          >
            {showPasscode ? <EyeOff className="size-4" /> : <Eye className="size-4" />}
          </button>
        </div>
      </div>

      {/* Fast Demo Shortcuts for Judges */}
      <div className="rounded-xl border border-line/40 bg-bg-3/20 p-2.5">
        <div className="flex items-center justify-between gap-2">
          <span className="flex items-center gap-1.5 text-[11px] font-mono uppercase tracking-wider text-fg-3">
            <Sparkles className="size-3 text-real" /> Quick fill:
          </span>
          <div className="flex items-center gap-1.5 flex-wrap">
            <button
              type="button"
              onClick={() => fillDemo("nairobi-sneaker-vault")}
              className="rounded-lg border border-line px-2 py-0.5 text-[11px] font-mono text-fg-2 hover:border-fg/40 hover:text-fg hover:bg-bg-3/50 transition-all duration-100 ease-out active:scale-95"
            >
              sneaker-vault
            </button>
            <button
              type="button"
              onClick={() => fillDemo("pwani-threads")}
              className="rounded-lg border border-line px-2 py-0.5 text-[11px] font-mono text-fg-2 hover:border-fg/40 hover:text-fg hover:bg-bg-3/50 transition-all duration-100 ease-out active:scale-95"
            >
              pwani-threads
            </button>
          </div>
        </div>
      </div>

      {/* Apple Design instant-feedback submit button */}
      <button
        type="submit"
        disabled={pending}
        className="group relative flex h-12 w-full items-center justify-center gap-2 rounded-xl bg-fg text-bg font-medium text-sm shadow-md transition-all duration-100 ease-out active:scale-[0.98] hover:bg-[color-mix(in_oklab,var(--fg)_88%,var(--bg))] disabled:pointer-events-none disabled:opacity-45 cursor-pointer"
      >
        {pending ? (
          <>
            <Loader2 className="size-4 animate-spin" />
            <span>{t("login.submitting")}...</span>
          </>
        ) : (
          <>
            <span>{t("login.submit")}</span>
            <ArrowRight className="size-4 transition-transform duration-150 ease-out group-hover:translate-x-0.5" />
          </>
        )}
      </button>

      {/* Back to public checker */}
      <div className="text-center pt-1">
        <button
          type="button"
          onClick={() => router.push("/")}
          className="text-xs text-fg-3 hover:text-fg transition-colors duration-100 ease-out underline decoration-line underline-offset-4 active:scale-95"
        >
          {t("login.back")}
        </button>
      </div>
    </form>
  );
}
