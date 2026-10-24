"use client";

import { AnimatePresence, motion, useReducedMotion } from "motion/react";
import { ChevronDown } from "lucide-react";
import { useState } from "react";
import { VerdictGlyph } from "@/components/brand/wordmark";
import { formatMs, shortId } from "@/lib/format";
import { useI18n } from "@/lib/i18n/provider";
import { bezier } from "@/lib/motion";
import { maskNumbersInText } from "@/lib/result";
import type { CheckResult } from "@/lib/schemas";
import { VERDICTS } from "@/lib/verdict";
import { cn } from "@/lib/utils";
import { EvidencePanel } from "./evidence-panel";
import { SafeActionCard } from "./safe-action-card";
import { ShareActions } from "./share-actions";

const REASONS_SHOWN = 3;

/**
 * The answer, as one calm column. Order is the order a worried shopper needs it:
 * the word, the sentence, what to do instead, why, the proof (closed), and how to warn others.
 */
export function ResultCase({
  result,
  instant = false,
  onAgain,
  onReplay,
  className,
}: {
  result: CheckResult;
  instant?: boolean;
  onAgain?: () => void;
  onReplay?: () => void;
  className?: string;
}) {
  const { t, locale } = useI18n();
  const reduced = useReducedMotion() ?? false;
  const still = instant || reduced;
  const meta = VERDICTS[result.verdict];
  const business = result.matched_merchant?.business_name ?? "";
  const word = meta.stamp;
  const lineKey = result.verdict === "suspicious" && !result.matched_merchant ? "line.suspicious.nobody" : meta.line;
  const [showAll, setShowAll] = useState(false);
  const [proof, setProof] = useState(false);
  const reasons = showAll ? result.reasons : result.reasons.slice(0, REASONS_SHOWN);
  const hidden = result.reasons.length - REASONS_SHOWN;
  const ease = bezier("out");
  const rise = (delay: number) => ({
    initial: still ? false : { opacity: 0, y: 18 },
    animate: { opacity: 1, y: 0 },
    transition: { duration: 0.7, delay, ease },
  });

  return (
    <article aria-labelledby={`verdict-${result.scan_id}`} className={cn("mx-auto grid w-full max-w-[40rem] gap-8", className)}>
      <motion.p {...rise(0)} className="font-mono text-[0.75rem] tracking-[0.1em] text-fg-3 uppercase">
        {t("console.case")} {shortId(result.scan_id)}
        {result.target.platform ? ` · ${result.target.platform}` : ""}
        {result.elapsed_ms ? ` · ${formatMs(result.elapsed_ms)}` : ""}
      </motion.p>

      <motion.div {...rise(0.05)} className="grid gap-5" style={{ color: meta.stampColor }}>
        <h2
          id={`verdict-${result.scan_id}`}
          className="font-display leading-[0.8] font-black tracking-[-0.012em] uppercase"
          style={{ fontSize: `calc(min(100vw - 2rem, 40rem) * 2.15 / ${word.length})` }}
        >
          {word}
        </h2>
        <p className="flex items-center gap-2.5 font-mono text-[0.8125rem] tracking-[0.1em] uppercase">
          <VerdictGlyph glyph={meta.glyph} className="size-5" />
          {t(meta.sub)}
        </p>
      </motion.div>

      <motion.p {...rise(0.12)} className="text-[clamp(1.375rem,5.6vw,1.875rem)] leading-[1.25] font-medium text-balance">
        {t(lineKey, { business })}
        {result.verdict === "no_match" ? <span className="mt-3 block text-[1rem] font-normal text-fg-2">{t("line.no_match.note")}</span> : null}
      </motion.p>

      <motion.div {...rise(0.18)}>
        <SafeActionCard result={result} />
      </motion.div>

      {reasons.length ? (
        <motion.section {...rise(0.24)} aria-label={t("reasons.title")} className="grid gap-4 border-t border-line pt-6">
          <h3 className="type-caption text-fg-3">{t("reasons.title")}</h3>
          <ul className="grid gap-4">
            {reasons.map((r, i) => (
              <li key={`${r.code}-${i}`} className="flex gap-3.5">
                <span aria-hidden="true" className={cn("mt-[0.6rem] size-2 shrink-0 rounded-full", r.severity === "high" ? "bg-feki" : "bg-onyo")} />
                <span className="text-[1.0625rem] leading-snug text-fg-2" lang={locale}>
                  {maskNumbersInText(locale === "sw" ? r.text_sw : r.text)}
                </span>
              </li>
            ))}
          </ul>
          {hidden > 0 ? (
            <button
              type="button"
              onClick={() => setShowAll((v) => !v)}
              className="inline-flex h-11 w-fit cursor-pointer items-center font-mono text-[0.8125rem] tracking-[0.08em] text-fg-3 uppercase underline decoration-line-strong underline-offset-[0.35em] hover:text-fg"
            >
              {showAll ? t("reasons.less") : `+ ${t("reasons.more", { n: hidden })}`}
            </button>
          ) : null}
        </motion.section>
      ) : null}

      {result.dimensions.length || result.hashes ? (
        <motion.section {...rise(0.3)} className="border-t border-line">
          <button
            type="button"
            aria-expanded={proof}
            aria-controls={`proof-${result.scan_id}`}
            onClick={() => setProof((v) => !v)}
            className="flex h-16 w-full cursor-pointer items-center justify-between text-left text-[1.0625rem] font-medium"
          >
            {proof ? t("result.hideEvidence") : t("result.showEvidence")}
            <ChevronDown className={cn("size-5 transition-transform duration-(--dur-ui) ease-out", proof && "rotate-180")} strokeWidth={1.75} aria-hidden="true" />
          </button>
          <AnimatePresence initial={false}>
            {proof ? (
              <motion.div
                id={`proof-${result.scan_id}`}
                initial={{ height: 0, opacity: 0 }}
                animate={{ height: "auto", opacity: 1 }}
                exit={{ height: 0, opacity: 0 }}
                transition={{ duration: 0.5, ease }}
                className="overflow-hidden"
              >
                <EvidencePanel result={result} instant={reduced} />
              </motion.div>
            ) : null}
          </AnimatePresence>
        </motion.section>
      ) : null}

      <motion.div {...rise(0.36)} className="border-t border-line pt-6">
        <ShareActions result={result} onAgain={onAgain} onReplay={onReplay} />
      </motion.div>
    </article>
  );
}
