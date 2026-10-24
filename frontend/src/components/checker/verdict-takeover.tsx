"use client";

import { useGSAP } from "@gsap/react";
import gsap from "gsap";
import { ArrowDown } from "lucide-react";
import { useCallback, useEffect, useRef } from "react";
import { createPortal } from "react-dom";
import { VerdictGlyph } from "@/components/brand/wordmark";
import { formatMs, shortId } from "@/lib/format";
import { useI18n } from "@/lib/i18n/provider";
import type { CheckResult } from "@/lib/schemas";
import { VERDICTS } from "@/lib/verdict";

gsap.registerPlugin(useGSAP);

/** How long the word holds on screen before the takeover folds away by itself. */
const HOLD_SECONDS = 1.35;
/**
 * The Verdict Takeover: the moment people remember.
 *
 * The result arrives, the viewport floods with the verdict colour from the bottom edge, and the
 * stamp word (HALISI / FEKI / ONYO / HAIJULIKANI) slams in at a size computed so it fills the screen.
 * Then it folds away upward into the evidence document. FEKI hits harder than the rest.
 *
 * It never delays information: the verdict is announced to screen readers the moment the result
 * lands (see Checker), the takeover is skippable (tap, Esc, or the button), and it is not rendered
 * at all under prefers-reduced-motion.
 */
export function VerdictTakeover({ result, onDone }: { result: CheckResult; onDone: () => void }) {
  const { t } = useI18n();
  const meta = VERDICTS[result.verdict];
  const root = useRef<HTMLDivElement>(null);
  const timeline = useRef<gsap.core.Timeline | null>(null);
  const closing = useRef(false);
  const doneRef = useRef(onDone);
  useEffect(() => {
    doneRef.current = onDone;
  });
  const business = result.matched_merchant?.business_name ?? "";
  const word = meta.stamp;
  const fake = result.verdict === "impersonation";
  const lineKey = result.verdict === "suspicious" && !result.matched_merchant ? "line.suspicious.nobody" : meta.line;

  // Freeze the page behind the takeover (Lenis too), and hand control back on the way out.
  useEffect(() => {
    const lenis = (window as unknown as { __lenis?: { stop: () => void; start: () => void } }).__lenis;
    const prev = document.documentElement.style.overflow;
    document.documentElement.style.overflow = "hidden";
    lenis?.stop();
    return () => {
      document.documentElement.style.overflow = prev;
      lenis?.start();
    };
  }, []);

  const close = useCallback((fast = false) => {
    if (closing.current || !root.current) return;
    closing.current = true;
    timeline.current?.kill();
    gsap.to(root.current, {
      clipPath: "inset(0% 0% 100% 0%)",
      duration: fast ? 0.45 : 0.75,
      ease: "expo.inOut",
      onComplete: () => doneRef.current(),
    });
  }, []);

  useGSAP(
    () => {
      const el = root.current;
      if (!el) return;
      const letters = el.querySelectorAll("[data-letter]");
      const lines = el.querySelectorAll("[data-line]");
      const mark = el.querySelector("[data-glyph]");
      gsap.set(el, { clipPath: "circle(0% at 50% 100%)" });
      gsap.set(letters, { yPercent: 118, rotate: (i: number) => (i % 2 ? 5 : -5) });
      gsap.set(lines, { y: 28, opacity: 0 });
      gsap.set(mark, { scale: 0.4, opacity: 0 });

      const tl = gsap.timeline({ defaults: { ease: "expo.out" } });
      timeline.current = tl;
      tl.to(el, { clipPath: "circle(150% at 50% 100%)", duration: 0.75, ease: "expo.inOut" })
        .to(letters, { yPercent: 0, rotate: 0, duration: 0.8, stagger: 0.055 }, "-=0.3")
        .to(mark, { scale: 1, opacity: 1, duration: 0.5, ease: "back.out(2.2)" }, "-=0.55")
        .fromTo(
          el.querySelector("[data-stage]"),
          { scale: fake ? 1.045 : 1.02 },
          { scale: 1, duration: 0.7, ease: "expo.out" },
          "-=0.35",
        )
        .to(lines, { y: 0, opacity: 1, duration: 0.7, stagger: 0.09 }, "-=0.55");

      if (fake) {
        // FEKI lands like a slammed door: a short, damped shake of the whole sheet.
        tl.fromTo(
          el,
          { x: 0, y: 0 },
          { x: 9, y: -6, duration: 0.05, repeat: 9, yoyo: true, ease: "power2.inOut", clearProps: "x,y" },
          0.95,
        );
      }

      tl.to({}, { duration: HOLD_SECONDS }).call(() => close());
      return () => tl.kill();
    },
    { scope: root },
  );

  // Esc skips. Focus moves to the button so keyboard users are never stranded behind the sheet.
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") close(true);
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [close]);
  useEffect(() => {
    root.current?.querySelector<HTMLButtonElement>("button")?.focus({ preventScroll: true });
  }, []);

  // Only ever rendered after a check completes in the browser, so `document` always exists here.
  return createPortal(
    <div
      ref={root}
      role="dialog"
      aria-modal="true"
      aria-label={`${word}. ${t(meta.sub)}`}
      onClick={() => close(true)}
      style={{ background: meta.stampColor, color: meta.onColor, clipPath: "circle(0% at 50% 100%)" }}
      className="fixed inset-0 z-[80] flex cursor-pointer flex-col overflow-hidden"
    >
      {/* film grain + vignette keep the flood from reading as a flat web colour */}
      <div aria-hidden="true" className="paper-grain pointer-events-none absolute inset-0 opacity-60 mix-blend-multiply" />
      <div
        aria-hidden="true"
        className="pointer-events-none absolute inset-0 bg-[radial-gradient(ellipse_at_50%_55%,transparent_40%,rgb(0_0_0/0.28)_100%)]"
      />

      <header className="relative flex items-center justify-between gap-4 px-[var(--gutter)] pt-5 font-mono text-[0.75rem] tracking-[0.1em] uppercase sm:pt-7">
        <p data-line>
          {t("console.case")} {shortId(result.scan_id)}
          {result.target.platform ? ` · ${result.target.platform}` : ""}
        </p>
        <p data-line className="truncate">
          {result.target.handle ? `@${result.target.handle}` : ""}
          {result.elapsed_ms ? ` · ${formatMs(result.elapsed_ms)}` : ""}
        </p>
      </header>

      <div data-stage className="relative flex min-h-0 flex-1 flex-col items-center justify-center px-[var(--gutter)]">
        <div className="flex items-center gap-3 font-mono text-[0.8125rem] tracking-[0.12em] uppercase sm:text-[0.9375rem]">
          <span data-glyph>
            <VerdictGlyph glyph={meta.glyph} className="size-6 sm:size-7" />
          </span>
          <span data-line>{t(meta.sub)}</span>
        </div>

        <h2
          aria-hidden="true"
          className="font-display leading-[0.8] font-black tracking-[-0.012em] uppercase select-none"
          style={{ fontSize: `min(calc(205vw / ${word.length}), 56vh)` }}
        >
          <span className="flex">
            {word.split("").map((ch, i) => (
              <span key={`${ch}-${i}`} className="block overflow-hidden pt-[0.04em] pb-[0.1em]">
                <span data-letter className="block">
                  {ch}
                </span>
              </span>
            ))}
          </span>
        </h2>

        <p data-line className="mt-2 max-w-[34ch] text-center text-[clamp(1.05rem,2.1vw,1.625rem)] leading-snug font-medium text-balance">
          {t(lineKey, { business })}
        </p>
      </div>

      <footer className="relative flex items-center justify-between px-[var(--gutter)] pb-6 sm:pb-8">
        <p data-line className="font-mono text-[0.6875rem] tracking-[0.1em] uppercase opacity-70">
          {t("takeover.hint")}
        </p>
        <button
          type="button"
          data-line
          onClick={(e) => {
            e.stopPropagation();
            close(true);
          }}
          className="inline-flex h-12 cursor-pointer items-center gap-3 rounded-pill border border-current px-6 text-[0.9375rem] font-medium transition-[background-color,color,transform] duration-(--dur-ui) ease-quart hover:border-night hover:bg-night hover:text-paper active:scale-[0.97]"
        >
          {t("takeover.evidence")}
          <ArrowDown className="size-4" strokeWidth={2} aria-hidden="true" />
        </button>
      </footer>
    </div>,
    document.body,
  );
}
