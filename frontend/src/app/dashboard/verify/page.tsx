"use client";

import { useState } from "react";
import Link from "next/link";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { motion, useReducedMotion } from "motion/react";
import { ArrowUpRight, Check, Copy } from "lucide-react";
import { toast } from "sonner";
import { useAlertDrawer } from "@/components/merchant/alert-context";
import { FileSection } from "@/components/merchant/file-section";
import { TrustChip } from "@/components/merchant/trust-chip";
import { ApiError, api, qk } from "@/lib/api";
import { formatDate } from "@/lib/format";
import { bezier } from "@/lib/motion";
import { merchantStatus, type OfficialHandle } from "@/lib/schemas";

function profileUrl(h: OfficialHandle): string | null {
  if (h.url) return h.url;
  const handle = encodeURIComponent(h.handle);
  switch (h.platform) {
    case "instagram": return `https://www.instagram.com/${handle}/`;
    case "tiktok": return `https://www.tiktok.com/@${handle}`;
    case "facebook": return `https://www.facebook.com/${handle}`;
    case "x": return `https://x.com/${handle}`;
    default: return null;
  }
}

/**
 * Ownership proof (PRODUCT_V2 section 5). The merchant puts a one-time code in a bio they control,
 * Halisi reads the bio, and only then does the brand become something Halisi will defend. This is
 * the whole answer to "what stops a scammer claiming my brand first": they cannot edit your bio.
 */
export default function VerifyPage() {
  const { merchantId, merchantSlug } = useAlertDrawer();
  const queryClient = useQueryClient();
  const reduced = useReducedMotion() ?? false;
  const [copied, setCopied] = useState(false);
  const [notFoundMsg, setNotFoundMsg] = useState<string | null>(null);

  const { data: merchant } = useQuery({ queryKey: qk.merchant(merchantSlug), queryFn: () => api.getMerchant(merchantSlug) });
  const { data: state, isLoading, error } = useQuery({
    queryKey: qk.verification(merchantId),
    queryFn: () => api.getVerification(merchantId),
    retry: false,
  });

  const check = useMutation({
    mutationFn: () => api.checkVerification(merchantId),
    onMutate: () => setNotFoundMsg(null),
    onSuccess: (res) => {
      queryClient.setQueryData(qk.verification(merchantId), res);
      void queryClient.invalidateQueries({ queryKey: qk.merchant(merchantSlug) });
      toast.success("Ownership verified.");
    },
    onError: (err) => {
      if (err instanceof ApiError && err.code === "VERIFICATION_CODE_NOT_FOUND") {
        setNotFoundMsg(err.message);
        return;
      }
      toast.error(err instanceof ApiError ? err.message : "The check did not finish. Try again.");
    },
  });

  async function copyCode(code: string) {
    try {
      await navigator.clipboard.writeText(code);
      setCopied(true);
      window.setTimeout(() => setCopied(false), 1800);
    } catch {
      toast.error("Copy was blocked. Select the code and copy it by hand.");
    }
  }

  const status = state?.status ?? (merchant ? merchantStatus(merchant) : null);
  const proven = status === "verified" || status === "curated";
  const rise = (delay: number) => ({
    initial: reduced ? false : { opacity: 0, y: 16 },
    animate: { opacity: 1, y: 0 },
    transition: { duration: 0.7, delay, ease: bezier("out") },
  });

  return (
    <div className="grid gap-[clamp(3rem,6vw,5rem)]">
      <header className="grid gap-6">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <Link href="/dashboard" className="type-caption text-fg-3 hover:text-fg">← All cases</Link>
          {status ? <TrustChip status={status} /> : null}
        </div>

        {proven ? (
          <>
            <h1 className="type-display-xl text-halisi">
              <span className="reveal-line"><span>HALISI</span></span>
            </h1>
            <p className="measure text-lede text-fg-2">
              {status === "curated"
                ? "Halisi added this brand from public sources. Customers who check your handles or Till see HALISI."
                : `You proved you own this brand${state?.verified_at ? ` on ${formatDate(state.verified_at)}` : ""}${state?.found_on ? `, from ${state.found_on}` : ""}. Customers who check your handles or Till now see HALISI, and clones of you read FEKI.`}
            </p>
            <div className="flex flex-wrap gap-3">
              <Link href="/dashboard" className="inline-flex h-12 items-center border border-fg bg-fg px-6 text-[0.9375rem] font-semibold text-bg active:scale-[0.98]">
                Go to cases
              </Link>
              <Link href={`/v/${merchantSlug}`} target="_blank" rel="noopener noreferrer" className="inline-flex h-12 items-center gap-2 border border-line-strong px-6 text-[0.9375rem] font-medium hover:bg-bg-2 active:scale-[0.98]">
                View your certificate <ArrowUpRight className="size-4" aria-hidden="true" />
              </Link>
            </div>
          </>
        ) : (
          <>
            <h1 className="type-display-l">
              <span className="reveal-line"><span>Prove it&rsquo;s yours.</span></span>
            </h1>
            <p className="measure text-lede text-fg-2">
              Until you do, Halisi stores your brand but does not defend it: no clone alerts, no certificate, no strike packs. Anyone can type a business name. Only the owner can edit the bio.
            </p>
          </>
        )}
      </header>

      {!proven ? (
        <>
          <FileSection n={1} title="Your code" id="code">
            {isLoading ? (
              <div className="skeleton-ink h-32" />
            ) : state?.verification_code ? (
              <motion.div {...rise(0)} className="corner-marks desk-panel grid gap-6 p-6 sm:p-10">
                <p className="type-caption text-fg-3">One-time code</p>
                <p className="type-data text-[clamp(2rem,9vw,5.5rem)] leading-none break-all" aria-label={`Your code is ${state.verification_code}`}>
                  {state.verification_code}
                </p>
                <div>
                  <button
                    type="button"
                    onClick={() => void copyCode(state.verification_code ?? "")}
                    className="type-caption inline-flex h-12 cursor-pointer items-center gap-2 border border-line-strong px-5 transition-colors duration-(--dur-micro) hover:bg-bg-2 active:scale-[0.97]"
                  >
                    {copied ? <Check className="size-4" aria-hidden="true" /> : <Copy className="size-4" aria-hidden="true" />}
                    {copied ? "Copied" : "Copy code"}
                  </button>
                </div>
              </motion.div>
            ) : (
              <p className="text-fg-2">
                {error instanceof ApiError ? error.message : "No code is waiting for this account. Contact Halisi if you expected one."}
              </p>
            )}
          </FileSection>

          <FileSection n={2} title="Put it in your bio" id="bio">
            <ol className="grid gap-5 text-[1.0625rem] text-fg-2">
              <li className="flex gap-4"><span className="type-caption pt-1.5 text-fg-3">i</span><span>Open the profile of <strong className="font-medium text-fg">one</strong> of your official accounts and edit the bio.</span></li>
              <li className="flex gap-4"><span className="type-caption pt-1.5 text-fg-3">ii</span><span>Paste the code anywhere in the bio and save.</span></li>
              <li className="flex gap-4"><span className="type-caption pt-1.5 text-fg-3">iii</span><span>Come back and press <strong className="font-medium text-fg">Check my bio</strong>. Once it passes you can delete the code.</span></li>
            </ol>
            {state?.handles_to_check.length ? (
              <ul className="grid gap-2 sm:grid-cols-2">
                {state.handles_to_check.map((h) => {
                  const href = profileUrl(h);
                  const inner = (
                    <>
                      <span className="type-data">@{h.handle}</span>
                      <span className="type-caption text-fg-3">{h.platform}</span>
                    </>
                  );
                  return (
                    <li key={`${h.platform}-${h.handle}`}>
                      {href ? (
                        <a href={href} target="_blank" rel="noopener noreferrer" className="flex min-h-12 items-center justify-between gap-3 border border-line px-4 hover:bg-bg-2">
                          {inner}
                        </a>
                      ) : (
                        <div className="flex min-h-12 items-center justify-between gap-3 border border-line px-4">{inner}</div>
                      )}
                    </li>
                  );
                })}
              </ul>
            ) : null}
          </FileSection>

          <FileSection n={3} title="Check" id="check">
            <div className="grid gap-4">
              <button
                type="button"
                disabled={check.isPending || !state?.verification_code}
                onClick={() => check.mutate()}
                className="inline-flex h-14 w-full cursor-pointer items-center justify-center gap-3 border border-fg bg-fg px-6 text-[1.0625rem] font-semibold text-bg transition-transform duration-(--dur-micro) active:scale-[0.99] disabled:cursor-not-allowed disabled:opacity-50 sm:w-fit sm:min-w-72"
              >
                {check.isPending ? (
                  <>
                    Reading your bio<span className="caret" aria-hidden="true" />
                  </>
                ) : (
                  "Check my bio"
                )}
              </button>
              <div aria-live="polite">
                {notFoundMsg ? (
                  <p className="measure border border-dashed border-line-strong p-4 text-[0.9375rem] text-fg-2">
                    {notFoundMsg} Platforms can take a few minutes to show a new bio to us. Wait a moment and try again.
                  </p>
                ) : null}
              </div>
              <p className="measure text-[0.8125rem] text-fg-3">
                Halisi reads the public bio of the handles you registered. If a platform blocks us, we say so; we never mark you verified on a guess.
              </p>
            </div>
          </FileSection>
        </>
      ) : null}
    </div>
  );
}
