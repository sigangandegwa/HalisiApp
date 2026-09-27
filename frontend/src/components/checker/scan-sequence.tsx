"use client";

import { motion, useReducedMotion } from "motion/react";
import { useCallback, useEffect, useRef, useState, type ReactNode } from "react";
import { LogoImage } from "@/components/brand/logo-image";
import { VerdictGlyph } from "@/components/brand/wordmark";
import { formatMs, shortId } from "@/lib/format";
import { isHash } from "@/lib/hash";
import { useI18n } from "@/lib/i18n/provider";
import { bezier } from "@/lib/motion";
import { availableSignals, maskNumbersInText } from "@/lib/result";
import type { CheckResult } from "@/lib/schemas";
import { VERDICTS, toneColor, toneText } from "@/lib/verdict";
import { cn } from "@/lib/utils";
import { CountUp } from "./count-up";
import { EvidenceBars } from "./evidence-bars";
import { HashGrid } from "./hash-grid";
import { SafeActionCard } from "./safe-action-card";
import { ShareActions } from "./share-actions";
import { VerdictStamp } from "./verdict-stamp";

/** Beat times in ms (FRONTEND.md section 8). */
export const BEAT = { logos: 150, scan: 700, grids: 900, bars: 1300, stamp: 1900, rise: 2200, end: 2800 } as const;
const s = (ms: number) => ms / 1000;

/**
 * The Forensic Verdict. Real forensic data *is* the animation: the grids are the API's pHashes,
 * the bars are the sub-scores. ~2.4 s, skippable (click / Esc), announced to screen readers
 * immediately, and reduced to a 160 ms fade under prefers-reduced-motion.
 */
export function ScanSequence({
  result,
  instant: instantProp = false,
  onDone,
  onAgain,
  onReplay,
  className,
}: {
  result: CheckResult;
  instant?: boolean;
  onDone?: () => void;
  onAgain?: () => void;
  onReplay?: () => void;
  className?: string;
}) {
  const reduced = useReducedMotion() ?? false;
  const [skipped, setSkipped] = useState(false);
  const instant = instantProp || reduced || skipped;
  const docRef = useRef<HTMLElement>(null);
  const { t, locale } = useI18n();
  const meta = VERDICTS[result.verdict];
  const color = toneColor[meta.tone];
  const m = result.matched_merchant;
  const business = m?.business_name ?? "";

  const finish = useCallback(() => {
    setSkipped(true);
    onDone?.();
  }, [onDone]);

  // Timeline end + the 1-frame "impact" as the stamp lands.
  useEffect(() => {
    if (instant) {
      onDone?.();
      return;
    }
    const timers: number[] = [];
    timers.push(
      window.setTimeout(() => {
        const el = docRef.current;
        if (!el) return;
        el.style.transform = "translate3d(0, 4px, 0)";
        requestAnimationFrame(() => requestAnimationFrame(() => (el.style.transform = "")));
      }, BEAT.stamp + 150),
    );
    timers.push(window.setTimeout(() => onDone?.(), BEAT.end));
    const onKey = (e: KeyboardEvent) => e.key === "Escape" && finish();
    window.addEventListener("keydown", onKey);
    return () => {
      timers.forEach(clearTimeout);
      window.removeEventListener("keydown", onKey);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [instant]);

  const hashes = result.hashes;
  const hasGrids = Boolean(hashes && isHash(hashes.target_phash) && isHash(hashes.reference_phash));
  const signals = availableSignals(result);
  const reasons = result.reasons;

  return (
    <motion.article
      ref={docRef}
      aria-labelledby={`verdict-${result.scan_id}`}
      initial={reduced && !instantProp ? { opacity: 0 } : false}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.16, ease: bezier("quart") }}
      onClick={instant ? undefined : finish}
      className={cn(
        "relative scroll-mt-24 rounded-doc border border-line bg-bg px-5 pt-5 pb-7 sm:px-8 sm:pt-6 sm:pb-10 lg:px-12 lg:pb-12",
        className,
      )}
    >
      {/* document header */}
      <header className="mb-7 flex flex-wrap items-center gap-x-4 gap-y-2 border-b border-line pb-4 sm:mb-10">
        <p className="type-caption text-fg-2">{t("scan.report")}</p>
        <p className="font-mono text-[0.6875rem] tracking-[0.06em] text-fg-3 uppercase">
          {t("scan.scan")} {shortId(result.scan_id)}
          {result.target.platform ? ` · ${result.target.platform}` : ""}
          {result.elapsed_ms ? ` · ${formatMs(result.elapsed_ms)}` : ""}
        </p>
        {!instant ? (
          <button
            type="button"
            onClick={(e) => {
              e.stopPropagation();
              finish();
            }}
            className="ml-auto inline-flex h-9 cursor-pointer items-center gap-2 rounded-pill px-3 font-mono text-[0.6875rem] tracking-[0.06em] text-fg-2 uppercase hover:bg-bg-2 hover:text-fg"
          >
            {t("scan.skip")} <kbd className="rounded-[2px] border border-line-strong px-1 font-mono text-[0.625rem]">Esc</kbd>
          </button>
        ) : null}
      </header>

      <div className="result-grid">
        <div data-area="compare">
          <Comparison result={result} instant={instant} color={color} />
        </div>

        <div data-area="hash">
          {hasGrids && hashes ? (
            <HashRow result={result} instant={instant} color={color} />
          ) : (
            <Rise instant={instant} delay={BEAT.grids}>
              <p className="max-w-[46ch] text-small text-fg-2">{result.verdict === "official" ? t("hash.official") : t("hash.none")}</p>
            </Rise>
          )}
        </div>

        <div data-area="verdict" className="relative lg:pt-2">
          <motion.div
            className="origin-[40%_60%] will-change-transform"
            initial={instant ? false : { opacity: 0, scale: 1.12, rotate: -6 }}
            animate={{ opacity: 1, scale: 1, rotate: -2.5 }}
            transition={{
              delay: s(BEAT.stamp),
              duration: 0.42,
              ease: bezier("stamp"),
              opacity: { delay: s(BEAT.stamp), duration: 0.1, ease: bezier("quart") },
            }}
          >
            <VerdictStamp verdict={result.verdict} rotate={0} />
          </motion.div>

          <Rise instant={instant} delay={BEAT.stamp + 160} className="mt-8">
            <h2 id={`verdict-${result.scan_id}`} className="flex items-start gap-3 text-[clamp(1.375rem,2.4vw,1.875rem)] leading-tight font-semibold tracking-[-0.015em]">
              <VerdictGlyph glyph={meta.glyph} className={cn("mt-1 size-6", toneText[meta.tone])} />
              <span>{t(meta.line, { business })}</span>
            </h2>
            {result.verdict === "no_match" ? <p className="mt-2 pl-9 text-fg-2">{t("line.no_match.note")}</p> : null}
            {result.verdict !== "official" ? (
              <p className="mt-3 pl-9 font-mono text-[0.75rem] tracking-[0.04em] text-fg-3 uppercase">
                {t("line.score", { score: Math.round(result.score) })} · {t("line.confidence", { n: signals })}
              </p>
            ) : null}
          </Rise>

          <Rise instant={instant} delay={BEAT.rise} className="mt-8 grid gap-5">
            <SafeActionCard result={result} />
            <ShareActions result={result} onAgain={onAgain} onReplay={onReplay} />
          </Rise>
        </div>

        {result.dimensions.length ? (
          <section data-area="bars" aria-labelledby={`bars-${result.scan_id}`}>
            <h3 id={`bars-${result.scan_id}`} className="type-caption mb-5 text-fg-2">
              {t("evidence.title")}
            </h3>
            <EvidenceBars dimensions={result.dimensions} color={color} delay={BEAT.bars} instant={instant} />
          </section>
        ) : null}

        {reasons.length ? (
          <Rise instant={instant} delay={BEAT.rise + 120} data-area="reasons">
            <h3 className="type-caption mb-4 text-fg-2">{t("reasons.title")}</h3>
            <ul className="grid gap-3">
              {reasons.map((r) => (
                <li key={r.code} className="flex gap-3 border-t border-line pt-3">
                  <span
                    aria-hidden="true"
                    className={cn("mt-2 size-2 shrink-0 rounded-full", r.severity === "high" ? "bg-feki" : "bg-caution")}
                  />
                  <span className="text-fg-2" lang={locale}>
                    {maskNumbersInText(locale === "sw" ? r.text_sw : r.text)}
                  </span>
                </li>
              ))}
            </ul>
          </Rise>
        ) : (
          <div data-area="reasons" />
        )}
      </div>
    </motion.article>
  );
}

function Rise({
  children,
  delay,
  instant,
  className,
  ...rest
}: {
  children: ReactNode;
  delay: number;
  instant: boolean;
  className?: string;
  "data-area"?: string;
}) {
  return (
    <motion.div
      className={className}
      initial={instant ? false : { opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: s(delay), duration: 0.6, ease: bezier("out") }}
      {...rest}
    >
      {children}
    </motion.div>
  );
}

/** Reference logo and suspect avatar slide together, overlap at 50 %, a scan line sweeps, they settle. */
function Comparison({ result, instant, color }: { result: CheckResult; instant: boolean; color: string }) {
  const { t } = useI18n();
  const m = result.matched_merchant;
  const official = result.verdict === "official";
  const hasRef = Boolean(m?.logo_url) && !official;
  const target = result.target;
  const size = 160;
  const move = { duration: 1.35, delay: s(BEAT.logos), times: [0, 0.55, 1], ease: [bezier("out"), bezier("inOut")] };

  if (!hasRef) {
    return (
      <div className="flex items-center gap-5">
        <motion.div
          initial={instant ? false : { opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: s(BEAT.logos), duration: 0.8, ease: bezier("out") }}
          className={cn("rounded-full p-1.5", official ? "ring-2 ring-real" : "ring-1 ring-line-strong")}
        >
          <LogoImage src={target.avatar_url ?? m?.logo_url} alt={`@${target.handle ?? ""}`} size={size} className="size-24 lg:size-36" priority />
        </motion.div>
        <div className="min-w-0">
          <p className="type-caption text-fg-3">{official ? t("hash.registered") : t("hash.thisPage")}</p>
          <p className="mt-1 truncate type-data text-[1.0625rem]">@{target.handle}</p>
          {target.display_name ? <p className="mt-0.5 truncate text-small text-fg-2">{target.display_name}</p> : null}
        </div>
      </div>
    );
  }

  return (
    <div>
      <div className="relative flex items-start justify-center gap-3 sm:gap-5">
        <motion.figure
          className="relative z-0 m-0 flex min-w-0 flex-col items-center"
          initial={instant ? false : { x: "-90%", opacity: 0 }}
          animate={{ x: instant ? "0%" : ["-90%", "34%", "0%"], opacity: instant ? 1 : [0, 1, 1] }}
          transition={instant ? { duration: 0 } : move}
        >
          <LogoImage src={m?.logo_url} alt={`${m?.business_name} registered logo`} size={size} className="size-24 lg:size-36" priority />
          <figcaption className="mt-3 max-w-40 text-center">
            <span className="type-caption block text-fg-3">{t("hash.registered")}</span>
            <span className="mt-1 block truncate text-small font-medium">{m?.business_name}</span>
          </figcaption>
        </motion.figure>

        <motion.figure
          className="relative z-10 m-0 flex min-w-0 flex-col items-center"
          initial={instant ? false : { x: "90%", opacity: 0 }}
          animate={{ x: instant ? "0%" : ["90%", "-34%", "0%"], opacity: instant ? 1 : [0, 0.5, 1] }}
          transition={instant ? { duration: 0 } : move}
        >
          <LogoImage src={target.avatar_url} alt={`@${target.handle} profile picture`} size={size} className="size-24 lg:size-36" priority />
          <figcaption className="mt-3 max-w-44 text-center">
            <span className="type-caption block text-fg-3">{t("hash.thisPage")}</span>
            <span className="mt-1 block truncate type-data text-small">@{target.handle}</span>
          </figcaption>
        </motion.figure>

        {!instant ? (
          <div aria-hidden="true" className="pointer-events-none absolute inset-x-[18%] top-0 h-24 overflow-hidden lg:h-36">
            <div
              className="absolute inset-x-0 top-0 h-full"
              style={{ animation: `halisi-scanline 600ms var(--ease-in-out) ${BEAT.scan}ms both` }}
            >
              <div className="h-0.5 w-full" style={{ background: color, boxShadow: `0 0 18px 2px ${color}` }} />
            </div>
          </div>
        ) : null}
      </div>
    </div>
  );
}

/** Both 8x8 grids flanking the Hamming readout, which counts 64 -> distance. */
function HashRow({ result, instant, color }: { result: CheckResult; instant: boolean; color: string }) {
  const { t } = useI18n();
  const h = result.hashes!;
  const distance = h.hamming_distance ?? 0;
  const refLabel = result.matched_merchant ? t("hash.registered") : t("hash.closest");
  return (
    <section aria-label={t("hash.title")}>
      <h3 className="type-caption mb-4 text-fg-2">{t("hash.title")}</h3>
      <div className="flex items-center justify-between gap-3 sm:justify-start sm:gap-8">
        <div>
          <HashGrid hex={h.reference_phash!} compareHex={h.target_phash} color={color} delay={BEAT.grids} instant={instant} label={refLabel} size={96} className="sm:hidden" />
          <HashGrid hex={h.reference_phash!} compareHex={h.target_phash} color={color} delay={BEAT.grids} instant={instant} label={refLabel} size={124} className="hidden sm:block" />
        </div>
        <div className="grid justify-items-center text-center">
          <p className="type-data text-[clamp(2.5rem,6vw,4rem)] leading-none tracking-[-0.03em]" style={{ color: distance <= 10 ? color : undefined }}>
            <CountUp from={64} to={distance} delay={BEAT.grids} duration={700} instant={instant} />
            <span className="sr-only">{distance}</span>
          </p>
          <p className="mt-2 font-mono text-[0.6875rem] tracking-[0.04em] text-fg-3 uppercase">
            {t("hash.of")}
            <br />
            {t("hash.differ")}
          </p>
        </div>
        <div>
          <HashGrid hex={h.target_phash!} compareHex={h.reference_phash} color={color} delay={BEAT.grids + 40} instant={instant} label={t("hash.thisPage")} size={96} className="sm:hidden" />
          <HashGrid hex={h.target_phash!} compareHex={h.reference_phash} color={color} delay={BEAT.grids + 40} instant={instant} label={t("hash.thisPage")} size={124} className="hidden sm:block" />
        </div>
      </div>
    </section>
  );
}
