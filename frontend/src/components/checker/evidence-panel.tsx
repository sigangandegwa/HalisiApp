"use client";

import { motion } from "motion/react";
import { LogoImage } from "@/components/brand/logo-image";
import { isHash } from "@/lib/hash";
import { useI18n } from "@/lib/i18n/provider";
import { bezier } from "@/lib/motion";
import type { CheckResult } from "@/lib/schemas";
import { VERDICTS, toneColor } from "@/lib/verdict";
import { CountUp } from "./count-up";
import { EvidenceBars } from "./evidence-bars";
import { HashGrid } from "./hash-grid";

/**
 * The proof, for people who want it: the registered logo next to this page's picture, the 64-bit
 * fingerprint of each, and the five signal bars. It only mounts when the reader opens it, so none
 * of this competes with the answer.
 */
export function EvidencePanel({ result, instant = false }: { result: CheckResult; instant?: boolean }) {
  const { t } = useI18n();
  const color = toneColor[VERDICTS[result.verdict].tone];
  const m = result.matched_merchant;
  const official = result.verdict === "official";
  const h = result.hashes;
  const hasGrids = Boolean(h && isHash(h.target_phash) && isHash(h.reference_phash));
  const target = result.target;
  const showRef = Boolean(m?.logo_url) && !official;
  const ease = bezier("out");

  return (
    <div className="grid gap-10 pt-2 pb-2">
      <div className="grid grid-cols-2 gap-4">
        {showRef ? (
          <motion.figure
            initial={instant ? false : { opacity: 0, y: 14 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, ease }}
            className="grid justify-items-start gap-3"
          >
            <LogoImage src={m?.logo_url} alt={`${m?.business_name} registered logo`} size={160} className="size-28 sm:size-36" />
            <figcaption>
              <span className="type-caption block text-fg-3">{t("hash.registered")}</span>
              <span className="mt-1 block text-small font-medium">{m?.business_name}</span>
            </figcaption>
          </motion.figure>
        ) : null}
        <motion.figure
          initial={instant ? false : { opacity: 0, y: 14 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: showRef ? 0.1 : 0, ease }}
          className={showRef ? "grid justify-items-start gap-3" : "col-span-2 grid justify-items-start gap-3"}
        >
          <LogoImage src={target.avatar_url ?? m?.logo_url} alt={`@${target.handle ?? ""}`} size={160} className="size-28 sm:size-36" />
          <figcaption className="min-w-0">
            <span className="type-caption block text-fg-3">{official ? t("hash.registered") : t("hash.thisPage")}</span>
            <span className="mt-1 block truncate font-mono text-small">@{target.handle}</span>
          </figcaption>
        </motion.figure>
      </div>

      {hasGrids && h ? (
        <section aria-label={t("hash.title")}>
          <h3 className="type-caption mb-4 text-fg-3">{t("hash.title")}</h3>
          <div className="flex items-center justify-between gap-3">
            <HashGrid hex={h.reference_phash!} compareHex={h.target_phash} color={color} delay={150} instant={instant} label={t("hash.registered")} size={96} />
            <div className="grid justify-items-center text-center">
              <p className="type-data text-[clamp(2.5rem,12vw,4rem)] leading-none">
                <CountUp from={64} to={h.hamming_distance ?? 0} delay={150} duration={700} instant={instant} />
                <span className="sr-only">{h.hamming_distance ?? 0}</span>
              </p>
              <p className="mt-2 font-mono text-[0.6875rem] tracking-[0.06em] text-fg-3 uppercase">
                {t("hash.of")} {t("hash.differ")}
              </p>
            </div>
            <HashGrid hex={h.target_phash!} compareHex={h.reference_phash} color={color} delay={190} instant={instant} label={t("hash.thisPage")} size={96} />
          </div>
        </section>
      ) : (
        <p className="max-w-[46ch] text-small text-fg-3">{official ? t("hash.official") : t("hash.none")}</p>
      )}

      {result.dimensions.length ? (
        <section aria-label={t("evidence.title")}>
          <h3 className="type-caption mb-5 text-fg-3">{t("evidence.title")}</h3>
          <EvidenceBars dimensions={result.dimensions} color={color} delay={250} instant={instant} />
        </section>
      ) : null}
    </div>
  );
}
