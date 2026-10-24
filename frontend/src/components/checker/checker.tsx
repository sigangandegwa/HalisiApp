"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { AnimatePresence, motion, useReducedMotion } from "motion/react";
import { useRouter } from "next/navigation";
import { useCallback, useEffect, useRef, useState } from "react";
import { ApiError, api, qk } from "@/lib/api";
import { looksLikePayment, parseTarget } from "@/lib/format";
import { useI18n } from "@/lib/i18n/provider";
import type { MessageKey } from "@/lib/i18n";
import { bezier } from "@/lib/motion";
import type { CheckRequest, CheckResult } from "@/lib/schemas";
import { cn } from "@/lib/utils";
import { VERDICTS } from "@/lib/verdict";
import { CheckerInput } from "./checker-input";
import { ExampleChips, type Example } from "./example-chips";
import { ManualFallback } from "./manual-fallback";
import { ResultCase } from "./result-case";
import { ScanConsole } from "./scan-console";
import { VerdictTakeover } from "./verdict-takeover";

/** idle -> pending (console) -> takeover (the verdict floods the screen) -> reveal (evidence) -> done */
type Stage = "idle" | "pending" | "takeover" | "reveal" | "done";

/** Time-paced activity lines (honest: they describe what Halisi does, they don't measure progress). */
const STEPS: { at: number; key: MessageKey }[] = [
  { at: 0, key: "scan.opening" },
  { at: 1100, key: "scan.bio" },
  { at: 2100, key: "scan.logo" },
  { at: 3300, key: "scan.payment" },
  { at: 4800, key: "scan.verdict" },
];
const STEP_KEYS = STEPS.map((s) => s.key);
const SLOW_AFTER_MS = 8000;

export function scrollToElement(el: HTMLElement | null, reduced: boolean) {
  if (!el) return;
  const lenis = (window as unknown as { __lenis?: { scrollTo: (t: HTMLElement, o?: object) => void } }).__lenis;
  if (lenis && !reduced) lenis.scrollTo(el, { offset: -88, duration: 1.1 });
  else el.scrollIntoView({ behavior: reduced ? "auto" : "smooth", block: "start" });
}

function toRequest(value: string): CheckRequest {
  return /^(https?:\/\/|www\.)|\.(com|me)\//i.test(value) ? { url: value } : { handle: value.replace(/^@/, "") };
}

/**
 * The checker (FRONTEND.md sections 6.1, 7, 8). Renders two grid children: the input block and
 * the result stage, so the landing can place them on different columns.
 */
export function Checker({ inputClassName, resultClassName }: { inputClassName?: string; resultClassName?: string }) {
  const { t } = useI18n();
  const router = useRouter();
  const queryClient = useQueryClient();
  const reduced = useReducedMotion() ?? false;
  const inputRef = useRef<HTMLInputElement>(null);
  const resultRef = useRef<HTMLDivElement>(null);
  const [value, setValue] = useState("");
  const [stage, setStage] = useState<Stage>("idle");
  const [result, setResult] = useState<CheckResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [manual, setManual] = useState<{ request: CheckRequest; message: string | null } | null>(null);
  const [step, setStep] = useState(0);
  const [slow, setSlow] = useState(false);
  const [runId, setRunId] = useState(0);
  const [announce, setAnnounce] = useState("");

  const mutation = useMutation({ mutationFn: (req: CheckRequest) => api.check(req) });

  // Honest, time-paced console lines while the API works.
  useEffect(() => {
    if (stage !== "pending") return;
    const timers = STEPS.map((s, i) => window.setTimeout(() => setStep(i), s.at));
    timers.push(window.setTimeout(() => setSlow(true), SLOW_AFTER_MS));
    return () => timers.forEach(clearTimeout);
  }, [stage, runId]);

  const fail = useCallback(
    (err: unknown, request: CheckRequest) => {
      setStage("idle");
      if (!(err instanceof ApiError)) return setError(t("checker.error.generic"));
      if (err.status === 502 && err.code === "TARGET_UNREACHABLE") {
        setManual({ request, message: err.fixture ? `${t("manual.body")} ${t("checker.error.offline")}` : null });
        return;
      }
      if (err.code === "ENGINE_OFFLINE") return setError(t("checker.error.offline"));
      if (err.code === "PAYMENT_INPUT") {
        const raw = request.url ?? request.handle ?? "";
        setError(t("checker.error.payment"));
        router.push(`/pay?value=${encodeURIComponent(raw)}`);
        return;
      }
      if (err.status === 422) return setError(err.code === "UNSUPPORTED_PLATFORM" ? t("checker.error.invalid") : err.message);
      if (err.status === 429) return setError(t("checker.error.rate"));
      if (err.status === 0) return setError(t("checker.error.network"));
      setError(t("checker.error.generic"));
    },
    [t, router],
  );

  const run = useCallback(
    async (request: CheckRequest) => {
      setError(null);
      setManual(null);
      setResult(null);
      setStep(0);
      setSlow(false);
      setAnnounce("");
      setStage("pending");
      setRunId((n) => n + 1);
      try {
        const fetched = await mutation.mutateAsync(request);
        // Manual checks don't return an avatar URL: show the picture the user uploaded (display only).
        const upload = request.manual?.avatar_base64;
        const res =
          upload && !fetched.target.avatar_url
            ? { ...fetched, target: { ...fetched.target, avatar_url: upload.startsWith("data:") ? upload : `data:image/png;base64,${upload}` } }
            : fetched;
        queryClient.setQueryData(qk.scan(res.scan_id), fetched);
        setResult(res);
        const meta = VERDICTS[res.verdict];
        // The verdict is announced immediately; the animation never delays information.
        const lineKey = res.verdict === "suspicious" && !res.matched_merchant ? "line.suspicious.nobody" : meta.line;
        setAnnounce(`${t(meta.word)} ${t(meta.sub)}. ${t(lineKey, { business: res.matched_merchant?.business_name ?? "" })}`);
        window.history.replaceState(null, "", `/check/${res.scan_id}`);
        if (reduced) {
          // No takeover under reduced motion: the evidence is simply there.
          setStage("reveal");
          requestAnimationFrame(() => scrollToElement(resultRef.current, reduced));
        } else {
          setStage("takeover");
        }
      } catch (err) {
        fail(err, request);
      }
    },
    [mutation, queryClient, fail, reduced, t],
  );

  const submit = useCallback(
    (raw?: string) => {
      const v = (raw ?? value).trim();
      if (raw !== undefined) setValue(raw);
      if (!v) return setError(t("checker.error.empty"));
      if (looksLikePayment(v)) {
        setError(t("checker.error.payment"));
        router.push(`/pay?value=${encodeURIComponent(v)}`);
        return;
      }
      if (!parseTarget(v)) return setError(t("checker.error.invalid"));
      void run(toRequest(v));
    },
    [value, t, router, run],
  );

  const pickExample = useCallback(
    async (ex: Example) => {
      setValue(`@${ex.handle}`);
      if (!ex.manual) return submit(`@${ex.handle}`);
      try {
        const blob = await fetch(ex.manual.avatar).then((r) => r.blob());
        const base64 = await new Promise<string>((resolve, reject) => {
          const reader = new FileReader();
          reader.onload = () => resolve(String(reader.result).split(",")[1] ?? "");
          reader.onerror = () => reject(reader.error);
          reader.readAsDataURL(blob);
        });
        void run({ handle: ex.handle, manual: { display_name: ex.manual.display_name, bio: ex.manual.bio, avatar_base64: base64 } });
      } catch {
        setError(t("checker.error.network"));
      }
    },
    [submit, run, t],
  );

  const reset = useCallback(() => {
    setResult(null);
    setManual(null);
    setError(null);
    setStage("idle");
    setValue("");
    window.history.replaceState(null, "", "/");
    requestAnimationFrame(() => {
      scrollToElement(inputRef.current?.closest("form") ?? null, reduced);
      inputRef.current?.focus({ preventScroll: true });
    });
  }, [reduced]);

  const collapsed = stage === "pending" || stage === "takeover" || stage === "reveal";
  const busy = stage === "pending";
  const consoleTarget = value.trim() || "…";

  return (
    <>
      <div className={cn("grid gap-3", inputClassName)}>
        <CheckerInput
          ref={inputRef}
          value={value}
          onChange={(v) => {
            setValue(v);
            if (error) setError(null);
          }}
          onSubmit={() => submit()}
          onPasteText={(text) => {
            // Paste auto-detection: a supported link submits straight away.
            if (parseTarget(text) && !looksLikePayment(text)) submit(text);
            else setValue(text);
          }}
          collapsed={collapsed}
          error={error}
        />
        {busy ? <ScanConsole target={consoleTarget} steps={STEP_KEYS} active={step} /> : null}
        {busy && slow ? (
          <p className="-mt-3 text-small text-fg-2">
            {t("scan.slow")}{" "}
            <button
              type="button"
              className="cursor-pointer font-medium text-fg underline underline-offset-4"
              onClick={() => {
                const req = parseTarget(value) ? toRequest(value.trim()) : { handle: value.trim() };
                mutation.reset();
                setStage("idle");
                setManual({ request: req, message: null });
              }}
            >
              {t("scan.slowAction")}
            </button>
          </p>
        ) : null}
        <ExampleChips onPick={pickExample} disabled={busy} />
      </div>

      <div aria-live="assertive" aria-atomic="true" className="sr-only">
        {announce}
      </div>
      <div ref={resultRef} className={cn("scroll-mt-24", resultClassName)}>
        <AnimatePresence mode="wait" initial={false}>
          {manual ? (
            <motion.div key="manual" exit={{ opacity: 0, y: -8 }} transition={{ duration: 0.2, ease: bezier("quart") }}>
              <ManualFallback
                pending={mutation.isPending}
                message={manual.message}
                onCancel={() => setManual(null)}
                onSubmit={(m) => void run({ ...manual.request, manual: m })}
              />
            </motion.div>
          ) : result && (stage === "reveal" || stage === "done") ? (
            <motion.div key={`${result.scan_id}-${runId}`} exit={{ opacity: 0, y: -8 }} transition={{ duration: 0.2, ease: bezier("quart") }}>
              <ResultCase result={result} onAgain={reset} />
            </motion.div>
          ) : null}
        </AnimatePresence>
      </div>

      {result && stage === "takeover" ? (
        <VerdictTakeover
          result={result}
          onDone={() => {
            setStage("reveal");
            requestAnimationFrame(() => scrollToElement(resultRef.current, reduced));
          }}
        />
      ) : null}
    </>
  );
}
