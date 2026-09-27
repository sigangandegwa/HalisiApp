"use client";

import { useEffect, useRef, useState } from "react";
import { LogoImage } from "@/components/brand/logo-image";
import { Stamp } from "@/components/brand/stamp";
import { useMediaQuery } from "@/lib/hooks";
import { useI18n } from "@/lib/i18n/provider";
import type { MessageKey } from "@/lib/i18n";
import { cn } from "@/lib/utils";

const REAL = "nairobisneakervault";

/** Letter-by-letter mutation frames: nairobisneakervault -> nairobi_sneakervault_official_ke. */
const HANDLE_FRAMES: string[] = (() => {
  const frames = [REAL, "nairobi_sneakervault"];
  const suffix = "_official_ke";
  for (let i = 1; i <= suffix.length; i++) frames.push(`nairobi_sneakervault${suffix.slice(0, i)}`);
  return frames;
})();

const BEATS: { dim: MessageKey; weight: number; title: MessageKey; body: MessageKey }[] = [
  { dim: "dim.visual", weight: 30, title: "story.1.title", body: "story.1.body" },
  { dim: "dim.identity", weight: 25, title: "story.2.title", body: "story.2.body" },
  { dim: "dim.language", weight: 10, title: "story.3.title", body: "story.3.body" },
  { dim: "dim.payment", weight: 25, title: "story.4.title", body: "story.4.body" },
  { dim: "dim.account", weight: 10, title: "story.5.title", body: "story.5.body" },
];

const clamp01 = (v: number) => Math.min(1, Math.max(0, v));

/**
 * A generic, trademark-neutral social profile card that is cloned as `p` goes 0 -> 5
 * (one unit per beat: logo, handle, bio, payment, account).
 */
function ProfileCard({ p, logo, annotate = true }: { p: number; logo: string | null; annotate?: boolean }) {
  const { t } = useI18n();
  const beat = (i: number) => clamp01(p - i); // 0..1 progress within beat i
  const handle = HANDLE_FRAMES[Math.round(beat(1) * (HANDLE_FRAMES.length - 1))];
  const bioText = t("story.bio");
  const bioChars = Math.round(beat(2) * bioText.length);
  const payFake = beat(3) > 0.35;
  const joined = beat(4) > 0.3;
  const stamp = p >= 4.92;

  const note = (i: number, cls: string) =>
    annotate ? (
      <span
        aria-hidden="true"
        className={cn("pointer-events-none absolute hidden items-center gap-2 whitespace-nowrap lg:flex", cls)}
        style={{ opacity: beat(i) > 0.05 ? 1 : 0, transition: "opacity 320ms var(--ease-quart)" }}
      >
        <span className="h-px w-14 origin-left bg-feki" style={{ transform: `scaleX(${clamp01(beat(i) * 2.2)})` }} />
        <span className="rounded-pill border border-feki bg-bg px-2.5 py-1 font-mono text-[0.6875rem] tracking-[0.06em] text-fake uppercase">
          {t(BEATS[i].dim)} · {BEATS[i].weight}%
        </span>
      </span>
    ) : null;

  return (
    <div className="relative w-full max-w-[25rem]">
      <div className="relative rounded-doc border border-line-strong bg-bg p-6 shadow-[0_1px_0_var(--line)]">
        <div className="relative flex items-center gap-5">
          {note(0, "top-0 left-full ml-12")}
          {note(1, "bottom-0 left-full ml-12")}
          <div className="relative size-20 shrink-0">
            <div className="absolute inset-0 rounded-full border border-dashed border-line-strong" />
            <div
              className="absolute inset-0"
              style={{
                opacity: beat(0),
                transform: `translate3d(${(1 - beat(0)) * -60}px, 0, 0) scale(${0.9 + beat(0) * 0.1})`,
              }}
            >
              <LogoImage src={logo} alt="" size={80} className="size-20" />
            </div>
          </div>
          <div className="min-w-0">
            <p className="type-data truncate text-[0.9375rem]">
              @{handle}
              {beat(1) > 0 && beat(1) < 1 ? <span className="ml-0.5 inline-block h-4 w-px animate-pulse bg-fg align-middle" /> : null}
            </p>
            <p className="mt-1 text-small font-semibold">{t("story.cardName")}</p>
            <p className="mt-2 flex gap-4 font-mono text-[0.75rem] text-fg-2">
              <span>{joined ? "9" : "1,204"} {t("story.posts")}</span>
              <span>{joined ? "212" : "18.6k"} {t("story.followers")}</span>
            </p>
          </div>
        </div>

        <div className="relative mt-5 min-h-12 border-t border-line pt-4 text-[0.9375rem]">
          {beat(2) > 0 ? (
            <p>
              <span>{bioText.slice(0, bioChars)}</span>
              {beat(2) < 1 ? <span className="ml-0.5 inline-block h-4 w-px animate-pulse bg-fg align-middle" /> : null}
            </p>
          ) : (
            <p className="text-fg-2">{t("story.bioReal")}</p>
          )}
          {note(2, "top-4 left-full ml-12")}
        </div>

        <div className="relative mt-4 flex flex-wrap items-center gap-x-3 gap-y-1 font-mono text-[0.875rem]">
          <span className={cn("transition-[color,opacity] duration-(--dur-ui) ease-quart", payFake && "text-fg-3 line-through decoration-feki")}>
            {t("story.payReal")}
          </span>
          <span
            className="text-fake transition-[opacity,transform] duration-(--dur-ui) ease-out"
            style={{ opacity: payFake ? 1 : 0, transform: `translate3d(0, ${payFake ? 0 : 6}px, 0)` }}
          >
            {t("story.payFake")}
          </span>
          {note(3, "top-1/2 left-full ml-12 -translate-y-1/2")}
        </div>

        <div className="relative mt-5 h-8">
          <span
            className="inline-flex h-8 items-center rounded-pill bg-bg-2 px-3 font-mono text-[0.75rem] text-fg-2 transition-[opacity,transform] duration-(--dur-ui) ease-stamp"
            style={{ opacity: joined ? 1 : 0, transform: `scale(${joined ? 1 : 0.85})` }}
          >
            {t("story.joined")}
          </span>
          {note(4, "top-1/2 left-full ml-12 -translate-y-1/2")}
        </div>
      </div>
      <div
        className="pointer-events-none absolute -right-6 -bottom-8 transition-[opacity,transform] duration-[420ms] ease-stamp"
        style={{ opacity: stamp ? 1 : 0, transform: `scale(${stamp ? 1 : 1.15}) rotate(${stamp ? -4 : -9}deg)` }}
        aria-hidden="true"
      >
        <Stamp word="FEKI." color="var(--color-feki)" size="md" misregister rotate={0} />
      </div>
    </div>
  );
}

/**
 * "Anatomy of a clone" (FRONTEND.md section 6.1.3). Desktop with a fine pointer: pinned GSAP
 * ScrollTrigger story, GSAP loaded with import() only when the section is within one viewport.
 * Phones and reduced motion: five stacked cards with IntersectionObserver reveals.
 */
export function CloneAnatomy({ logoUrl }: { logoUrl: string | null }) {
  const { t } = useI18n();
  const sectionRef = useRef<HTMLElement>(null);
  const stageRef = useRef<HTMLDivElement>(null);
  const desktop = useMediaQuery("(min-width: 64rem) and (pointer: fine)");
  const reduced = useMediaQuery("(prefers-reduced-motion: reduce)");
  const mode: "pin" | "stack" = desktop && !reduced ? "pin" : "stack";
  const [p, setP] = useState(0);

  useEffect(() => {
    if (mode !== "pin" || !sectionRef.current || !stageRef.current) return;
    let kill: (() => void) | undefined;
    let cancelled = false;
    const section = sectionRef.current;
    const stage = stageRef.current;
    const io = new IntersectionObserver(
      async ([entry]) => {
        if (!entry?.isIntersecting) return;
        io.disconnect();
        const [{ gsap }, { ScrollTrigger }] = await Promise.all([import("gsap"), import("gsap/ScrollTrigger")]);
        if (cancelled) return;
        gsap.registerPlugin(ScrollTrigger);
        const lenis = (window as unknown as { __lenis?: { on: (e: string, cb: () => void) => void } }).__lenis;
        lenis?.on("scroll", ScrollTrigger.update);
        let last = -1;
        const st = ScrollTrigger.create({
          trigger: section,
          start: "top top",
          end: "+=420%",
          pin: stage,
          scrub: true,
          onUpdate: (self) => {
            const q = Math.round(self.progress * 5 * 120) / 120;
            if (q !== last) {
              last = q;
              setP(q);
            }
          },
        });
        kill = () => st.kill();
      },
      { rootMargin: "100% 0px" },
    );
    io.observe(section);
    return () => {
      cancelled = true;
      io.disconnect();
      kill?.();
    };
  }, [mode]);

  const active = Math.min(4, Math.floor(p));

  return (
    <section ref={sectionRef} aria-labelledby="story-title" className="relative border-t border-line">
      {mode === "pin" ? (
        <div ref={stageRef} className="page-grid h-dvh items-center">
          <div className="col-span-5">
            <p className="type-caption text-fg-3">{t("story.eyebrow")}</p>
            <h2 id="story-title" className="type-display-m mt-4 max-w-[14ch]">{t("story.title")}</h2>
            <ol className="relative mt-10 h-56">
              {BEATS.map((b, i) => (
                <li
                  key={b.title}
                  className="absolute inset-0 transition-[opacity,transform] duration-(--dur-reveal) ease-out"
                  style={{ opacity: i === active ? 1 : 0, transform: `translate3d(0, ${i === active ? 0 : i < active ? -16 : 16}px, 0)` }}
                  aria-hidden={i !== active}
                >
                  <p className="font-mono text-[0.75rem] tracking-[0.06em] text-fake uppercase">
                    0{i + 1} · {t(b.dim)} · {b.weight}%
                  </p>
                  <h3 className="mt-3 font-display text-[2rem] leading-tight font-medium tracking-[-0.02em]">{t(b.title)}</h3>
                  <p className="measure mt-3 text-fg-2">{t(b.body)}</p>
                </li>
              ))}
            </ol>
            <div className="mt-6 flex gap-1.5" aria-hidden="true">
              {BEATS.map((b, i) => (
                <span key={b.dim} className="h-0.5 w-10 overflow-hidden bg-line-strong">
                  <span className="block h-full origin-left bg-fg" style={{ transform: `scaleX(${clamp01(p - i)})` }} />
                </span>
              ))}
            </div>
          </div>
          <div className="col-span-6 col-start-7 flex justify-start">
            <ProfileCard p={p} logo={logoUrl} />
          </div>
        </div>
      ) : (
        <div className="page-wrap section-y">
          <p className="type-caption text-fg-3">{t("story.eyebrow")}</p>
          <h2 id="story-title" className="type-display-m mt-4 max-w-[16ch]">{t("story.title")}</h2>
          <ol className="mt-12 grid gap-14 md:grid-cols-2 md:gap-x-10">
            {BEATS.map((b, i) => (
              <StackBeat key={b.title} index={i}>
                <p className="font-mono text-[0.75rem] tracking-[0.06em] text-fake uppercase">
                  0{i + 1} · {t(b.dim)} · {b.weight}%
                </p>
                <h3 className="mt-2 font-display text-[1.75rem] leading-tight font-medium tracking-[-0.02em]">{t(b.title)}</h3>
                <p className="mt-2 text-fg-2">{t(b.body)}</p>
                <div className="mt-6">
                  <ProfileCard p={i + 1} logo={logoUrl} annotate={false} />
                </div>
              </StackBeat>
            ))}
          </ol>
        </div>
      )}
    </section>
  );
}

function StackBeat({ children, index }: { children: React.ReactNode; index: number }) {
  const ref = useRef<HTMLLIElement>(null);
  const [seen, setSeen] = useState(false);
  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    const io = new IntersectionObserver(([e]) => e?.isIntersecting && (setSeen(true), io.disconnect()), { rootMargin: "0px 0px -15% 0px" });
    io.observe(el);
    return () => io.disconnect();
  }, []);
  return (
    <li
      ref={ref}
      className="transition-[opacity,transform] duration-(--dur-reveal) ease-out"
      style={{ opacity: seen ? 1 : 0, transform: `translate3d(0, ${seen ? 0 : 24}px, 0)`, transitionDelay: `${(index % 2) * 70}ms` }}
    >
      {children}
    </li>
  );
}
