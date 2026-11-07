"use client";

import type { CSSProperties } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ArrowLeft } from "lucide-react";
import { toast } from "sonner";
import { EvidenceBars } from "@/components/checker/evidence-bars";
import { HashGrid } from "@/components/checker/hash-grid";
import { useAlertDrawer } from "@/components/merchant/alert-context";
import { CompareSlider } from "@/components/merchant/compare-slider";
import { FileSection } from "@/components/merchant/file-section";
import { HandleDiff } from "@/components/merchant/handle-diff";
import { ScoreRadar } from "@/components/merchant/score-radar";
import { StrikeConsole, type StrikeKind } from "@/components/merchant/strike-console";
import { ApiError, api, qk } from "@/lib/api";
import { STATUS_LABEL, STATUS_STEPS, isOpen } from "@/lib/case";
import { formatDateTime, maskPhone, shortId, timeAgo } from "@/lib/format";
import { maskNumbersInText } from "@/lib/result";
import { merchantStatus, type ThreatStatus } from "@/lib/schemas";
import { VERDICTS } from "@/lib/verdict";
import { cn } from "@/lib/utils";

/**
 * A case file. Top to bottom it answers what a merchant asks in order: what is this and how bad
 * (the verdict), how do I know (evidence), what do I do (strike pack), what has happened (record).
 */
export default function ThreatDetailPage() {
  const id = useParams<{ id: string }>().id;
  const { merchantId, merchantSlug } = useAlertDrawer();
  const queryClient = useQueryClient();

  const { data: threat, isLoading, error } = useQuery({ queryKey: qk.threat(id), queryFn: () => api.getThreat(id), retry: false });
  const { data: merchant } = useQuery({ queryKey: qk.merchant(merchantSlug), queryFn: () => api.getMerchant(merchantSlug) });

  const update = useMutation({
    mutationFn: (status: ThreatStatus) => api.updateThreat(id, status),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: qk.threat(id) });
      void queryClient.invalidateQueries({ queryKey: ["threats", merchantId] });
      void queryClient.invalidateQueries({ queryKey: qk.stats(merchantId) });
    },
    onError: (err) => toast.error(err instanceof ApiError ? err.message : "Could not update the case."),
  });

  const back = (
    <Link href="/dashboard" className="type-caption group inline-flex h-11 w-fit items-center gap-2 text-fg-2 hover:text-fg">
      <ArrowLeft className="size-4 transition-transform duration-(--dur-ui) group-hover:-translate-x-0.5" aria-hidden="true" />
      All cases
    </Link>
  );

  if (isLoading) {
    return (
      <div className="grid gap-6">
        {back}
        <div className="skeleton-ink h-56" />
        <div className="skeleton-ink h-80" />
      </div>
    );
  }

  if (error || !threat) {
    return (
      <div className="grid gap-6">
        {back}
        <p className="font-display text-[clamp(2.5rem,7vw,5rem)] leading-none font-extrabold uppercase">Case not found.</p>
        <p className="measure text-fg-2">{error instanceof ApiError && error.status === 403 ? "This case belongs to another account." : "It may have been removed, or the link is wrong."}</p>
      </div>
    );
  }

  const meta = VERDICTS[threat.verdict];
  const officials = merchant?.official_handles.map((h) => h.handle) ?? [];
  const locked = merchant ? merchantStatus(merchant) === "claimed" : false;
  const caseId = shortId(threat.id ?? threat.scan_id);
  const open = isOpen(threat.status);
  const stepIndex = STATUS_STEPS.indexOf(threat.status as (typeof STATUS_STEPS)[number]);
  const phones = threat.extracted_phones;
  const tills = threat.extracted_tills;

  function onSent(kind: StrikeKind) {
    if (!threat) return;
    if (kind === "advisory" && threat.status === "detected") update.mutate("advisory_sent");
    if (kind === "platform" && (threat.status === "detected" || threat.status === "advisory_sent")) update.mutate("takedown_filed");
  }

  return (
    <div className="grid gap-[clamp(3rem,6vw,5.5rem)]">
      {back}

      {/* the verdict */}
      <header className="grid gap-8">
        <p className="type-caption text-fg-3">
          Case {caseId} · {threat.target.platform ?? "unknown platform"}
          {threat.first_seen_at ? ` · first seen ${timeAgo(threat.first_seen_at)}` : ""}
        </p>

        <div className="flex flex-wrap items-end justify-between gap-x-10 gap-y-4">
          <h1 className="type-display-xl" style={{ color: meta.stampColor }}>
            <span className="reveal-line"><span>{meta.stamp}</span></span>
          </h1>
          <div className="reveal-fade pb-2 text-right" style={{ "--i": 3 } as CSSProperties}>
            <p className="type-data text-[clamp(2.5rem,6vw,4.5rem)] leading-none">{Math.round(threat.score)}<span className="text-fg-3">/100</span></p>
            <p className="type-caption mt-2 text-fg-3">Confidence {Math.round(threat.confidence * 100)}%</p>
          </div>
        </div>

        <div className="reveal-fade grid gap-2" style={{ "--i": 4 } as CSSProperties}>
          <p className="type-caption text-fg-3">The imitating account</p>
          <HandleDiff target={threat.target.handle ?? ""} officials={officials} className="text-[clamp(1.5rem,4.2vw,3.25rem)] leading-tight" />
          {threat.target.url ? (
            <a href={threat.target.url} target="_blank" rel="noopener noreferrer" className="type-data w-fit text-[0.8125rem] break-all text-fg-3 underline underline-offset-4 hover:text-fg">
              {threat.target.url}
            </a>
          ) : null}
        </div>

        {/* where the case stands */}
        <div className="grid gap-5 border-y border-line py-5">
          <ol className="grid grid-cols-4 gap-2" aria-label="Case progress">
            {STATUS_STEPS.map((step, i) => {
              const reached = stepIndex >= i;
              return (
                <li key={step} className="grid gap-2" aria-current={threat.status === step ? "step" : undefined}>
                  <span className={cn("h-[3px] transition-colors duration-(--dur-ui)", reached ? "bg-fg" : "bg-line-strong")} />
                  <span className={cn("type-caption leading-tight", reached ? "text-fg" : "text-fg-3")}>{STATUS_LABEL[step]}</span>
                </li>
              );
            })}
          </ol>
          <div className="flex flex-wrap items-center gap-x-6 gap-y-2">
            {threat.status === "false_positive" ? (
              <p className="type-caption text-fg-2">Marked as a false alarm</p>
            ) : null}
            {open ? (
              <>
                <button type="button" disabled={update.isPending} onClick={() => update.mutate("resolved")} className="type-caption h-11 cursor-pointer border border-line-strong px-4 hover:bg-bg-2 disabled:opacity-50 active:scale-[0.97]">
                  Mark resolved
                </button>
                <button type="button" disabled={update.isPending} onClick={() => update.mutate("false_positive")} className="min-h-11 cursor-pointer text-[0.9375rem] text-fg-3 underline decoration-line-strong underline-offset-4 hover:text-fg disabled:opacity-50">
                  This is not an imitation
                </button>
              </>
            ) : (
              <button type="button" disabled={update.isPending} onClick={() => update.mutate("detected")} className="type-caption h-11 cursor-pointer border border-line-strong px-4 hover:bg-bg-2 disabled:opacity-50 active:scale-[0.97]">
                Reopen case
              </button>
            )}
          </div>
        </div>
      </header>

      {/* 01 evidence */}
      <FileSection n={1} title="Evidence" id="evidence" aside={`${threat.dimensions.filter((d) => d.available).length} of ${threat.dimensions.length} signals`}>
        <div className="grid gap-[clamp(2rem,4vw,4rem)] lg:grid-cols-12">
          <div className="grid content-start gap-3 lg:col-span-7">
            <h3 className="type-caption text-fg-3">The logos, side by side</h3>
            <div className="corner-marks desk-panel p-4 sm:p-6">
              <CompareSlider official={merchant?.logo_url ?? ""} suspect={threat.target.avatar_url ?? ""} />
            </div>
          </div>

          <div className="grid content-start gap-3 lg:col-span-5">
            <h3 className="type-caption text-fg-3">
              Fingerprint{threat.hashes?.hamming_distance != null ? ` · ${threat.hashes.hamming_distance} bits differ` : ""}
            </h3>
            <div className="desk-panel p-4 sm:p-6">
              {threat.hashes?.target_phash && threat.hashes.reference_phash ? (
                <HashGrid hex={threat.hashes.target_phash} compareHex={threat.hashes.reference_phash} label="Hash" />
              ) : (
                <p className="text-[0.9375rem] text-fg-3">No logo could be fingerprinted for this account.</p>
              )}
            </div>
          </div>
        </div>

        <div className="grid gap-[clamp(2rem,4vw,4rem)] lg:grid-cols-12">
          <div className="grid content-start gap-3 lg:col-span-7">
            <h3 className="type-caption text-fg-3">Five signals</h3>
            <div className="desk-panel grid items-center gap-8 p-5 sm:p-6 md:grid-cols-[12rem_minmax(0,1fr)]">
              <div className="mx-auto w-full max-w-48">
                <ScoreRadar dimensions={threat.dimensions} />
              </div>
              <EvidenceBars dimensions={threat.dimensions} color={meta.stampColor} dense />
            </div>
          </div>

          <div className="grid content-start gap-6 lg:col-span-5">
            {threat.reasons.length ? (
              <div className="grid gap-3">
                <h3 className="type-caption text-fg-3">Why Halisi flagged it</h3>
                <ul className="grid gap-4">
                  {threat.reasons.map((r, i) => (
                    <li key={`${r.code}-${i}`} className="flex gap-3.5">
                      <span aria-hidden="true" className={cn("mt-[0.6rem] size-2 shrink-0 rounded-full", r.severity === "high" ? "bg-feki" : "bg-onyo")} />
                      <span className="text-[1.0625rem] leading-snug text-fg-2">{maskNumbersInText(r.text)}</span>
                    </li>
                  ))}
                </ul>
              </div>
            ) : null}

            {phones.length || tills.length ? (
              <div className="grid gap-3 border-t border-line pt-5">
                <h3 className="type-caption text-fg-3">Where the money is asked for</h3>
                <ul className="flex flex-wrap gap-2">
                  {phones.map((p) => (
                    <li key={p} className="type-data border border-line px-3 py-1.5 text-[0.9375rem]">{maskPhone(p)}</li>
                  ))}
                  {tills.map((t) => (
                    <li key={t} className="type-data border border-line px-3 py-1.5 text-[0.9375rem]">Till {t}</li>
                  ))}
                </ul>
                <p className="text-[0.8125rem] text-fg-3">Shown masked here. The drafts in section 2 carry what the reports need.</p>
              </div>
            ) : null}
          </div>
        </div>
      </FileSection>

      {/* 02 strike */}
      <FileSection n={2} title="Prepare strike" id="strike">
        <StrikeConsole
          threatId={threat.id ?? id}
          platform={threat.target.platform ?? "the platform"}
          locked={locked}
          hasPaymentEvidence={phones.length + tills.length > 0}
          onSent={onSent}
        />
      </FileSection>

      {/* 03 record */}
      <FileSection n={3} title="Record" id="record" aside="Africa/Nairobi time">
        {threat.status_history.length ? (
          <ol className="grid">
            {[...threat.status_history].reverse().map((h, i) => (
              <li key={`${h.status}-${h.at}-${i}`} className="grid grid-cols-[auto_1fr_auto] items-baseline gap-4 border-b border-line py-3.5">
                <span aria-hidden="true" className={cn("size-2 rounded-full", i === 0 ? "bg-fg" : "bg-line-strong")} />
                <span className="text-[1.0625rem]">{STATUS_LABEL[h.status]}</span>
                <time dateTime={h.at} className="type-data text-[0.8125rem] text-fg-3">{formatDateTime(h.at)}</time>
              </li>
            ))}
          </ol>
        ) : (
          <p className="text-fg-3">No status changes yet.</p>
        )}
      </FileSection>
    </div>
  );
}
