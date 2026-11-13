"use client";

import { useRouter, useSearchParams } from "next/navigation";
import { useId, useState } from "react";
import { AnimatePresence, motion, useAnimationControls, useReducedMotion } from "motion/react";
import { ArrowRight } from "lucide-react";
import { VerdictGlyph } from "@/components/brand/wordmark";
import { dictionaries, translator, type Locale, type MessageKey } from "@/lib/i18n";
import { bezier } from "@/lib/motion";

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

/** Fictional seeded merchants, offered as one-tap fills when the deployment shows the demo passcode. */
const DEMO_BUSINESSES = [
  { slug: "nairobi-sneaker-vault", name: "Nairobi Sneaker Vault" },
  { slug: "pwani-threads", name: "Pwani Threads" },
] as const;

const FIELD =
  "peer h-14 w-full border-0 border-b border-line-strong bg-transparent px-0 text-[1.25rem] leading-none text-fg caret-fg focus-visible:outline-none";

/** The rule under a field thickens from the left when the field has focus: the designed focus state. */
function FocusRule() {
  return (
    <span
      aria-hidden="true"
      className="pointer-events-none absolute inset-x-0 bottom-0 h-0.5 origin-left scale-x-0 bg-fg transition-transform duration-(--dur-ui) ease-out peer-focus:scale-x-100"
    />
  );
}

/**
 * The sign-in slip: two ruled lines and one bar. A refusal reads like a verdict (broken seal, FEKI red)
 * and nudges the slip; a pass raises a bone sheet over the room while the dashboard loads behind it.
 * `demoPasscode` is null unless the server was told to show it (SHOW_DEMO_PASSCODE).
 */
export function LoginForm({ locale, demoPasscode }: { locale: Locale; demoPasscode: string | null }) {
  const t = translator(dictionaries[locale]);
  const identifierId = useId();
  const passcodeId = useId();
  const errorId = useId();
  const router = useRouter();
  const params = useSearchParams();
  const reduced = useReducedMotion() ?? false;
  const nudge = useAnimationControls();
  const next = params.get("next");
  const safeNext = next && next.startsWith("/") && !next.startsWith("//") ? next : "/dashboard";

  const [identifier, setIdentifier] = useState("");
  const [passcode, setPasscode] = useState("");
  const [showPasscode, setShowPasscode] = useState(false);
  const [error, setError] = useState<{ message: string; refused: boolean } | null>(null);
  const [pending, setPending] = useState(false);
  const [opened, setOpened] = useState(false);

  function fail(message: string, refused: boolean) {
    setError({ message, refused });
    if (!reduced) {
      void nudge.start({ x: [0, -7, 6, -3, 0], transition: { duration: 0.42, ease: bezier("quart") } });
    }
  }

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    const cleanPasscode = passcode.trim();
    if (!cleanPasscode) {
      fail(t("login.error.empty"), false);
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
        fail(key ? t(key) : (body.error?.message ?? t("login.error.generic")), true);
        setPending(false);
        return;
      }

      // The sheet rises while the dashboard loads; navigation is not delayed for the animation.
      setOpened(true);
      router.push(safeNext);
      router.refresh();
    } catch {
      fail(t("login.error.generic"), false);
      setPending(false);
    }
  }

  function fillDemo(slug: string) {
    if (!demoPasscode) return;
    setIdentifier(slug);
    setPasscode(demoPasscode);
    setError(null);
  }

  return (
    <>
      <motion.form onSubmit={submit} noValidate animate={nudge} className="grid gap-8">
        <div className="group grid gap-1">
          <label htmlFor={identifierId} className="type-caption flex items-baseline gap-3 text-fg-3 transition-colors duration-(--dur-ui) group-focus-within:text-fg">
            <span className="tabular-nums">01</span>
            {t("login.identifierLabel")}
          </label>
          <div className="relative">
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
              className={FIELD}
            />
            <FocusRule />
          </div>
        </div>

        <div className="group grid gap-1">
          <label htmlFor={passcodeId} className="type-caption flex items-baseline gap-3 text-fg-3 transition-colors duration-(--dur-ui) group-focus-within:text-fg">
            <span className="tabular-nums">02</span>
            {t("login.passcodeLabel")}
          </label>
          <div className="relative">
            <input
              id={passcodeId}
              name="passcode"
              type={showPasscode ? "text" : "password"}
              autoComplete="current-password"
              placeholder={t("login.placeholder")}
              value={passcode}
              aria-invalid={error ? true : undefined}
              aria-describedby={error ? errorId : undefined}
              onChange={(e) => {
                setPasscode(e.target.value);
                if (error) setError(null);
              }}
              className={`${FIELD} pr-20 ${showPasscode && passcode ? "font-mono tracking-[0.04em]" : ""}`}
            />
            <FocusRule />
            <button
              type="button"
              aria-pressed={showPasscode}
              onClick={() => setShowPasscode((v) => !v)}
              className="type-caption absolute top-1/2 right-0 inline-flex h-11 -translate-y-1/2 cursor-pointer items-center pl-4 text-fg-3 transition-colors duration-(--dur-micro) hover:text-fg"
            >
              {showPasscode ? t("login.hide") : t("login.show")}
            </button>
          </div>
        </div>

        <div aria-live="assertive" className="-my-2 empty:hidden">
          {error ? (
            <div id={errorId} role="alert" className="flex items-start gap-3 border-l-2 border-fake py-1 pl-4 [animation:halisi-fade-up_480ms_var(--ease-out)_both]">
              {error.refused ? <VerdictGlyph glyph="broken" className="mt-0.5 text-fake" /> : null}
              <p className="grid gap-1">
                {error.refused ? <span className="type-caption text-fake">{t("login.refused")}</span> : null}
                <span className="text-[0.9375rem] leading-snug text-fg-2">{error.message}</span>
              </p>
            </div>
          ) : null}
        </div>

        <button
          type="submit"
          disabled={pending}
          className="group/go relative inline-flex h-14 w-full cursor-pointer items-center justify-between gap-3 overflow-hidden border border-fg bg-fg px-6 text-[1.0625rem] font-semibold text-bg transition-transform duration-(--dur-micro) active:scale-[0.99] disabled:cursor-progress"
        >
          {pending ? (
            <span>
              {t("login.submitting")}
              <span className="caret" aria-hidden="true" />
            </span>
          ) : (
            <>
              <span>{t("login.submit")}</span>
              <ArrowRight className="size-5 transition-transform duration-(--dur-ui) ease-out group-hover/go:translate-x-1.5" strokeWidth={1.75} aria-hidden="true" />
            </>
          )}
        </button>

        {demoPasscode ? (
          <div className="grid gap-3 border border-dashed border-line-strong p-4">
            <p className="type-caption text-fg-3">{t("login.demo")}</p>
            <div className="flex flex-wrap gap-2">
              {DEMO_BUSINESSES.map((b) => (
                <button
                  key={b.slug}
                  type="button"
                  onClick={() => fillDemo(b.slug)}
                  className="inline-flex min-h-11 cursor-pointer items-center border border-line-strong px-4 text-[0.875rem] transition-colors duration-(--dur-micro) hover:bg-bg-2 active:scale-[0.98]"
                >
                  {b.name}
                </button>
              ))}
            </div>
            <p className="text-[0.8125rem] text-fg-3">{t("login.demoHint", { passcode: demoPasscode })}</p>
          </div>
        ) : null}
      </motion.form>

      <AnimatePresence>
        {opened ? (
          <motion.div
            role="status"
            className="theme-paper fixed inset-0 z-50 flex items-end bg-bg p-(--gutter) pb-[max(var(--gutter),env(safe-area-inset-bottom))] text-fg"
            initial={reduced ? false : { y: "100%" }}
            animate={{ y: 0 }}
            transition={{ duration: 0.7, ease: bezier("inOut") }}
          >
            <p className="font-display text-[clamp(3.75rem,17vw,13rem)] leading-[0.82] font-black tracking-[-0.012em] uppercase">
              {t("login.opening")}
            </p>
          </motion.div>
        ) : null}
      </AnimatePresence>
    </>
  );
}
