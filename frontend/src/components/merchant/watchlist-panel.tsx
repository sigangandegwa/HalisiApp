"use client";

import Link from "next/link";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { ApiError, api, qk } from "@/lib/api";
import { VERDICTS } from "@/lib/verdict";

const SHOWN_PER_HANDLE = 5;

/**
 * Typosquat watchlist (PRODUCT_V2 section 6). It lists the look-alikes Halisi would recognise and lets
 * the merchant probe the ones that resolve publicly. The copy states the limit plainly: this is not a
 * crawl of Instagram, and an unreachable account is not a clean one.
 */
export function WatchlistPanel({ merchantId }: { merchantId: string }) {
  const queryClient = useQueryClient();

  const list = useQuery({ queryKey: qk.watchlist(merchantId), queryFn: () => api.getWatchlist(merchantId), retry: false });

  const scan = useMutation({
    mutationFn: () => api.scanWatchlist(merchantId),
    onSuccess: (res) => {
      void queryClient.invalidateQueries({ queryKey: ["threats", merchantId] });
      void queryClient.invalidateQueries({ queryKey: qk.stats(merchantId) });
      toast.success(
        res.findings.length
          ? `${res.findings.length} look-alike${res.findings.length === 1 ? "" : "s"} found.`
          : `Probed ${res.probed}. Nothing imitating you was reachable.`,
      );
    },
    onError: (err) => toast.error(err instanceof ApiError ? err.message : "The scan did not finish. Try again."),
  });

  const total = list.data?.handles.reduce((n, h) => n + h.variants.length, 0) ?? 0;
  const locked = list.error instanceof ApiError && (list.error.status === 403 || list.error.status === 409);

  return (
    <div className="grid gap-5">
      <p className="text-[0.9375rem] leading-relaxed text-fg-2">
        Halisi generates the spellings a cloner would pick, then checks the ones that exist. It does not crawl social
        platforms, and an account it cannot reach is not a clean one.
      </p>

      {list.isLoading ? (
        <div className="skeleton-ink h-24" />
      ) : locked ? (
        <p className="border border-line-strong p-4 text-[0.9375rem] text-fg-2">
          The watchlist switches on once your brand is verified.{" "}
          <Link href="/dashboard/verify" className="text-fg underline underline-offset-4">Verify now</Link>
        </p>
      ) : list.data ? (
        <>
          <p className="type-data text-[0.8125rem] text-fg-3">{total} look-alike spellings across {list.data.handles.length} official handle{list.data.handles.length === 1 ? "" : "s"}</p>
          <ul className="grid gap-4">
            {list.data.handles.map((h) => (
              <li key={`${h.platform}-${h.handle}`} className="grid gap-2">
                <p className="type-caption text-fg-3">{h.platform} · @{h.handle}</p>
                <ul className="flex flex-wrap gap-1.5">
                  {h.variants.slice(0, SHOWN_PER_HANDLE).map((v) => (
                    <li key={v} className="type-data border border-line px-2 py-1 text-[0.8125rem] text-fg-2">@{v}</li>
                  ))}
                  {h.variants.length > SHOWN_PER_HANDLE ? (
                    <li className="type-data px-1 py-1 text-[0.8125rem] text-fg-3">+{h.variants.length - SHOWN_PER_HANDLE}</li>
                  ) : null}
                </ul>
              </li>
            ))}
          </ul>
        </>
      ) : (
        <p className="text-[0.9375rem] text-fg-3">
          {list.error instanceof ApiError ? list.error.message : "The watchlist could not be loaded."}
        </p>
      )}

      <button
        type="button"
        disabled={scan.isPending || locked || !list.data}
        onClick={() => scan.mutate()}
        className="inline-flex h-12 w-full cursor-pointer items-center justify-center border border-fg bg-fg px-5 text-[0.9375rem] font-semibold text-bg transition-[transform,opacity] duration-(--dur-micro) active:scale-[0.98] disabled:cursor-not-allowed disabled:opacity-40"
      >
        {scan.isPending ? "Probing look-alikes" : "Scan look-alikes now"}
        {scan.isPending ? <span className="caret" aria-hidden="true" /> : null}
      </button>

      {scan.data ? (
        <div className="grid gap-3 border-t border-line pt-4" aria-live="polite">
          <p className="type-data text-[0.8125rem] text-fg-2">
            {scan.data.variants_generated} generated · {scan.data.probed} probed · {scan.data.resolved} reachable · {scan.data.unreachable} unreachable
          </p>
          {scan.data.budget_exhausted ? <p className="text-[0.8125rem] text-warn">Scan budget reached. Some spellings were not probed.</p> : null}
          {scan.data.findings.length ? (
            <ul className="grid gap-2">
              {scan.data.findings.map((f) => {
                const meta = VERDICTS[f.verdict];
                const body = (
                  <>
                    <span className="type-data text-fg">@{f.handle}</span>
                    <span className="font-display text-lg font-extrabold uppercase" style={{ color: meta.stampColor }}>{meta.stamp}</span>
                  </>
                );
                return (
                  <li key={f.scan_id}>
                    {f.threat_id ? (
                      <Link href={`/dashboard/threat/${f.threat_id}`} className="flex items-center justify-between gap-3 border border-line px-3 py-2 hover:bg-bg-2">{body}</Link>
                    ) : (
                      <div className="flex items-center justify-between gap-3 border border-line px-3 py-2">{body}</div>
                    )}
                  </li>
                );
              })}
            </ul>
          ) : null}
        </div>
      ) : null}
    </div>
  );
}
