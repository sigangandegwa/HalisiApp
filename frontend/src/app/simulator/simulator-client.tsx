"use client";

import { useMutation } from "@tanstack/react-query";
import { AnimatePresence, motion } from "motion/react";
import { useState } from "react";
import { RotateCcw, Sparkles } from "lucide-react";
import { LogoImage } from "@/components/brand/logo-image";
import { ScanSequence } from "@/components/checker/scan-sequence";
import { Button } from "@/components/ui/button";
import { ApiError, api } from "@/lib/api";
import { dictionaries, translator, type Locale, type MessageKey } from "@/lib/i18n";
import { bezier } from "@/lib/motion";
import type { CheckResult, Tweaks } from "@/lib/schemas";
import { cn } from "@/lib/utils";

export interface SimulatorMerchant {
  id: string;
  slug: string;
  business_name: string;
  logo_url: string | null;
}

const HANDLE_STYLES: Tweaks["handle_style"][] = ["suffix", "homoglyph", "underscore"];
const LOGO_TWEAKS: Tweaks["logo"][] = ["exact", "recolor", "crop", "jpeg"];
const PAYMENT_TWEAKS: Tweaks["payment"][] = ["phone", "pochi", "none"];

const DEFAULT_TWEAKS: Tweaks = { handle_style: "suffix", logo: "exact", payment: "phone", bio_tokens: true };

/**
 * Toggle group of pill buttons for one tweak dimension. Each option is a real engine input
 * (BACKEND.md 5.10), not a decorative label: changing it changes what gets scored.
 */
function Group<T extends string | boolean>({
  label,
  options,
  value,
  onChange,
  labelKey,
  t,
  disabled,
}: {
  label: string;
  options: T[];
  value: T;
  onChange: (v: T) => void;
  labelKey: (v: T) => MessageKey;
  t: ReturnType<typeof translator>;
  disabled?: boolean;
}) {
  return (
    <fieldset className="grid gap-2.5">
      <legend className="type-caption text-fg-3">{label}</legend>
      <div className="flex flex-wrap gap-2" role="radiogroup">
        {options.map((opt) => (
          <button
            key={String(opt)}
            type="button"
            role="radio"
            aria-checked={value === opt}
            disabled={disabled}
            onClick={() => onChange(opt)}
            className={cn(
              "h-10 cursor-pointer rounded-pill border px-4 text-[0.8125rem] font-medium transition-colors duration-(--dur-ui) ease-quart disabled:pointer-events-none disabled:opacity-50",
              value === opt ? "border-fg bg-fg text-bg" : "border-line-strong text-fg-2 hover:border-fg hover:text-fg",
            )}
          >
            {t(labelKey(opt))}
          </button>
        ))}
      </div>
    </fieldset>
  );
}

export function SimulatorClient({ merchants, locale }: { merchants: SimulatorMerchant[]; locale: Locale }) {
  const t = translator(dictionaries[locale]);
  const [merchantId, setMerchantId] = useState(merchants[0]?.id ?? "");
  const [tweaks, setTweaks] = useState<Tweaks>(DEFAULT_TWEAKS);
  const [result, setResult] = useState<CheckResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  const mutation = useMutation({
    mutationFn: () => api.simulateClone({ merchant_id: merchantId, tweaks }),
    onSuccess: (res) => {
      setError(null);
      setResult(res);
    },
    onError: (err) => setError(err instanceof ApiError ? err.message : t("sim.error")),
  });

  const patch = <K extends keyof Tweaks>(key: K, value: Tweaks[K]) => setTweaks((prev) => ({ ...prev, [key]: value }));
  const merchant = merchants.find((m) => m.id === merchantId);

  return (
    <div className="grid gap-10 lg:grid-cols-[22rem_1fr] lg:items-start lg:gap-14">
      <div className="grid gap-8">
        <fieldset className="grid gap-2.5">
          <legend className="type-caption text-fg-3">{t("sim.merchant")}</legend>
          <div className="grid gap-2">
            {merchants.map((m) => (
              <button
                key={m.id}
                type="button"
                role="radio"
                aria-checked={m.id === merchantId}
                disabled={mutation.isPending}
                onClick={() => setMerchantId(m.id)}
                className={cn(
                  "flex cursor-pointer items-center gap-3 rounded-doc border px-4 py-3 text-left transition-colors duration-(--dur-ui) ease-quart disabled:pointer-events-none disabled:opacity-50",
                  m.id === merchantId ? "border-fg bg-bg-2" : "border-line-strong hover:border-fg",
                )}
              >
                <LogoImage src={m.logo_url} alt="" size={36} className="size-9 shrink-0" />
                <span className="text-[0.9375rem] font-medium">{m.business_name}</span>
              </button>
            ))}
          </div>
        </fieldset>

        <Group label={t("sim.handle")} options={HANDLE_STYLES} value={tweaks.handle_style} onChange={(v) => patch("handle_style", v)} labelKey={(v) => `sim.handle.${v}` as MessageKey} t={t} disabled={mutation.isPending} />
        <Group label={t("sim.logo")} options={LOGO_TWEAKS} value={tweaks.logo} onChange={(v) => patch("logo", v)} labelKey={(v) => `sim.logo.${v}` as MessageKey} t={t} disabled={mutation.isPending} />
        <Group label={t("sim.payment")} options={PAYMENT_TWEAKS} value={tweaks.payment} onChange={(v) => patch("payment", v)} labelKey={(v) => `sim.payment.${v}` as MessageKey} t={t} disabled={mutation.isPending} />
        <Group
          label={t("sim.bio")}
          options={[true, false]}
          value={tweaks.bio_tokens}
          onChange={(v) => patch("bio_tokens", v)}
          labelKey={(v) => (v ? "sim.bio.on" : "sim.bio.off")}
          t={t}
          disabled={mutation.isPending}
        />

        <Button size="lg" disabled={!merchantId || mutation.isPending} onClick={() => mutation.mutate()} className="mt-2 w-full">
          {mutation.isPending ? t("sim.launching") : t("sim.launch")}
          <Sparkles className="size-5" strokeWidth={1.5} aria-hidden="true" />
        </Button>
        {error ? <p className="text-small text-fake">{error}</p> : null}
        {merchant ? (
          <p className="font-mono text-[0.6875rem] text-fg-3 uppercase">
            {result?.target.fetched_via === "simulator" ? t("sim.live") : result ? t("sim.offline") : null}
          </p>
        ) : null}
      </div>

      <div className="min-h-112">
        <AnimatePresence mode="wait">
          {result ? (
            <motion.div
              key={result.scan_id}
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.32, ease: bezier("out") }}
              className="theme-paper rounded-doc bg-paper p-6 text-ink sm:p-10"
            >
              <ScanSequence result={result} onAgain={() => setResult(null)} />
              <Button variant="secondary" className="mt-8" onClick={() => setResult(null)}>
                <RotateCcw className="size-4" strokeWidth={1.5} aria-hidden="true" />
                {t("sim.again")}
              </Button>
            </motion.div>
          ) : (
            <div className="grid h-full min-h-112 place-items-center rounded-doc border border-dashed border-line-strong text-fg-3">
              <p className="type-caption">{t("sim.launch")}</p>
            </div>
          )}
        </AnimatePresence>
      </div>
    </div>
  );
}
