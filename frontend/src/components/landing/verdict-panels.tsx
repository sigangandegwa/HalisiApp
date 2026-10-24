import type { T } from "@/lib/i18n";
import type { Verdict } from "@/lib/schemas";
import { VERDICTS } from "@/lib/verdict";

const ORDER: { verdict: Exclude<Verdict, "error">; body: "verdicts.official" | "verdicts.impersonation" | "verdicts.suspicious" | "verdicts.no_match" }[] = [
  { verdict: "official", body: "verdicts.official" },
  { verdict: "impersonation", body: "verdicts.impersonation" },
  { verdict: "suspicious", body: "verdicts.suspicious" },
  { verdict: "no_match", body: "verdicts.no_match" },
];

/**
 * The four possible answers, one full screen each. Every panel is sticky, so as you scroll the next
 * colour slides over the last like a deck of cards. Each panel holds exactly three things: a counter,
 * the word at the size that fills the screen, and one sentence. Pure CSS: no JavaScript, no layout shift.
 */
export function VerdictPanels({ t }: { t: T }) {
  return (
    <section aria-labelledby="verdicts-title">
      <h2 id="verdicts-title" className="sr-only">
        {t("verdicts.title1")} {t("verdicts.title2")}
      </h2>
      {ORDER.map((p, i) => {
        const meta = VERDICTS[p.verdict];
        return (
          <article
            key={p.verdict}
            style={{ background: meta.stampColor, color: meta.onColor, zIndex: i + 1 }}
            className="sticky top-0 flex min-h-svh flex-col justify-between px-(--gutter) pt-24 pb-10 md:pb-14"
          >
            <p className="font-mono text-[0.8125rem] tracking-[0.12em] uppercase">
              0{i + 1} / 04 · {t(meta.sub)}
            </p>
            <div>
              <p
                aria-hidden="true"
                className="font-display leading-[0.8] font-black tracking-[-0.012em] uppercase"
                style={{ fontSize: `min(calc(200vw / ${meta.stamp.length}), 40vh)` }}
              >
                {meta.stamp}
              </p>
              <p className="mt-6 max-w-[30ch] text-[clamp(1.25rem,5vw,2.125rem)] leading-snug font-medium text-balance">{t(p.body)}</p>
            </div>
          </article>
        );
      })}
    </section>
  );
}
