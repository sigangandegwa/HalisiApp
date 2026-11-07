"use client";

import Link from "next/link";
import { motion, useReducedMotion } from "motion/react";
import { timeAgo, shortId } from "@/lib/format";
import { STATUS_LABEL } from "@/lib/case";
import { bezier } from "@/lib/motion";
import type { ThreatSummary } from "@/lib/schemas";
import { VERDICTS } from "@/lib/verdict";
import { HandleDiff } from "./handle-diff";

/**
 * One case in the ledger. The verdict word is the loudest thing on the row because it is the
 * decision; the handle diff is second because it is the proof. Nothing else competes.
 */
export function ThreatRow({ threat, merchantHandles, index = 0 }: { threat: ThreatSummary; merchantHandles: string[]; index?: number }) {
  const reduced = useReducedMotion() ?? false;
  const meta = VERDICTS[threat.verdict];

  return (
    <motion.li
      initial={reduced ? false : { opacity: 0, y: 14 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.7, delay: Math.min(index, 8) * 0.06, ease: bezier("out") }}
    >
      <Link
        href={`/dashboard/threat/${threat.id}`}
        className="group relative grid grid-cols-[auto_minmax(0,1fr)_auto] items-center gap-x-4 gap-y-2 border-b border-line py-5 pl-5 transition-colors duration-(--dur-ui) hover:bg-bg-2 sm:gap-x-6 sm:pl-6"
      >
        <span aria-hidden="true" className="absolute inset-y-0 left-0 w-[3px] origin-top scale-y-60 transition-transform duration-(--dur-ui) ease-out group-hover:scale-y-100" style={{ background: meta.stampColor }} />

        <div className="size-12 shrink-0 overflow-hidden rounded-full border border-line bg-bg-3 sm:size-14">
          {threat.avatar_url ? (
            // eslint-disable-next-line @next/next/no-img-element -- seeded/remote avatars, sizes unknown
            <img src={threat.avatar_url} alt="" className="size-full object-cover" />
          ) : null}
        </div>

        <div className="min-w-0">
          <p className="type-caption text-fg-3">
            Case {shortId(threat.id)} · {threat.platform}
          </p>
          <HandleDiff target={threat.target_handle} officials={merchantHandles} className="mt-1 text-[1.0625rem] sm:text-[1.25rem]" />
          {threat.top_reason ? <p className="mt-1.5 line-clamp-1 text-[0.9375rem] text-fg-2">{threat.top_reason.text}</p> : null}
        </div>

        <div className="text-right">
          <p className="font-display text-[clamp(1.75rem,3.4vw,2.5rem)] leading-[0.85] font-black uppercase" style={{ color: meta.stampColor }}>
            {meta.stamp}
          </p>
          <p className="type-data mt-1.5 text-[0.8125rem] text-fg-2">{Math.round(threat.composite_score)}/100</p>
        </div>

        <p className="col-span-3 col-start-1 flex items-center justify-between gap-3 pl-0 text-[0.8125rem] text-fg-3 sm:col-span-1 sm:col-start-3 sm:justify-end">
          <span className="type-caption">{STATUS_LABEL[threat.status]}</span>
          <span aria-hidden="true">·</span>
          <time dateTime={threat.first_seen_at}>{timeAgo(threat.first_seen_at)}</time>
        </p>
      </Link>
    </motion.li>
  );
}
