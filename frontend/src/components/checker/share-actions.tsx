"use client";

import Link from "next/link";
import { useState } from "react";
import { Check, Flag, Link2, RotateCcw, Search } from "lucide-react";
import { buttonVariants } from "@/components/ui/button";
import { useI18n } from "@/lib/i18n/provider";
import { officialHandle, resultUrl, whatsappUrl } from "@/lib/result";
import type { CheckResult } from "@/lib/schemas";
import { cn } from "@/lib/utils";

export async function copyText(text: string): Promise<boolean> {
  try {
    await navigator.clipboard.writeText(text);
    return true;
  } catch {
    const ta = document.createElement("textarea");
    ta.value = text;
    ta.setAttribute("readonly", "");
    ta.style.position = "fixed";
    ta.style.opacity = "0";
    document.body.appendChild(ta);
    ta.select();
    const ok = document.execCommand("copy");
    ta.remove();
    return ok;
  }
}

function WhatsAppGlyph({ className }: { className?: string }) {
  return (
    <svg viewBox="0 0 24 24" className={className} aria-hidden="true" focusable="false" fill="currentColor">
      <path d="M12 2.2A9.8 9.8 0 0 0 3.6 17l-1.3 4.8 4.9-1.3A9.8 9.8 0 1 0 12 2.2zm0 17.8a8 8 0 0 1-4.1-1.1l-.3-.2-2.9.8.8-2.8-.2-.3A8 8 0 1 1 12 20zm4.4-6c-.2-.1-1.4-.7-1.7-.8-.2-.1-.4-.1-.5.1l-.8.9c-.1.2-.3.2-.5.1a6.5 6.5 0 0 1-3.2-2.8c-.2-.4.2-.4.7-1.2.1-.1 0-.3 0-.4l-.8-1.8c-.2-.5-.4-.4-.5-.4h-.5a.9.9 0 0 0-.7.3 2.8 2.8 0 0 0-.9 2.1 4.9 4.9 0 0 0 1 2.6 11.2 11.2 0 0 0 4.3 3.8c1.6.7 2.2.7 3 .6.5-.1 1.4-.6 1.6-1.1.2-.6.2-1 .1-1.1l-.5-.3z" />
    </svg>
  );
}

/** Share / copy / report / check another (FRONTEND.md section 6.2). */
export function ShareActions({
  result,
  onAgain,
  onReplay,
  className,
}: {
  result: CheckResult;
  onAgain?: () => void;
  onReplay?: () => void;
  className?: string;
}) {
  const { t } = useI18n();
  const [copied, setCopied] = useState(false);
  const m = result.matched_merchant;
  const handle = officialHandle(m, result.target.platform);
  const url = resultUrl(result.scan_id);
  const vars = {
    handle: result.target.handle ?? "",
    business: m?.business_name ?? "",
    official: handle ? `@${handle.handle}` : "",
  };
  const messageKey =
    result.verdict === "impersonation"
      ? "share.message.impersonation"
      : result.verdict === "suspicious"
        ? "share.message.suspicious"
        : result.verdict === "official"
          ? "share.message.official"
          : "share.message.no_match";
  const message = `${t(messageKey, vars)} ${url}`;
  const report = new URLSearchParams();
  if (result.target.url) report.set("url", result.target.url);
  else if (result.target.handle) report.set("handle", result.target.handle);

  const quiet =
    "inline-flex h-12 cursor-pointer items-center gap-2 font-medium text-fg-2 transition-colors duration-(--dur-ui) ease-quart hover:text-fg [&_svg]:size-[1.05rem]";

  // One big button for the thing worth doing (warn a friend), then quiet text actions.
  return (
    <div className={cn("grid gap-2", className)}>
      <a
        href={whatsappUrl(message)}
        target="_blank"
        rel="noopener noreferrer"
        className={cn(buttonVariants({ variant: "primary", size: "lg" }), "w-full")}
      >
        <WhatsAppGlyph className="size-[1.2rem]" />
        {t("share.whatsapp")}
      </a>
      <div className="flex flex-wrap items-center gap-x-6">
        <button
          type="button"
          className={quiet}
          onClick={async () => {
            if (await copyText(url)) {
              setCopied(true);
              window.setTimeout(() => setCopied(false), 1800);
            }
          }}
          aria-live="polite"
        >
          {copied ? <Check strokeWidth={1.75} /> : <Link2 strokeWidth={1.5} />}
          {copied ? t("share.copied") : t("share.copy")}
        </button>
        {result.verdict !== "official" ? (
          <Link href={`/report?${report.toString()}`} className={quiet}>
            <Flag strokeWidth={1.5} />
            {t("share.report")}
          </Link>
        ) : null}
        {onReplay ? (
          <button type="button" className={quiet} onClick={onReplay}>
            <RotateCcw strokeWidth={1.5} />
            {t("share.replay")}
          </button>
        ) : null}
        {onAgain ? (
          <button type="button" className={quiet} onClick={onAgain}>
            <Search strokeWidth={1.5} />
            {t("share.again")}
          </button>
        ) : null}
      </div>
    </div>
  );
}
