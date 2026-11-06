"use client";

import { useState, type ReactNode } from "react";
import Link from "next/link";
import { useMutation } from "@tanstack/react-query";
import { motion, useReducedMotion } from "motion/react";
import { Check, Copy, Download, ExternalLink } from "lucide-react";
import { toast } from "sonner";
import { ApiError, api } from "@/lib/api";
import { bezier } from "@/lib/motion";
import type { Playbooks } from "@/lib/schemas";
import { cn } from "@/lib/utils";

type Lang = "en" | "sw";
export type StrikeKind = "platform" | "safaricom" | "advisory" | "kecirt";

const storageKey = (threatId: string) => `halisi.strike.${threatId}`;

function readSubmitted(threatId: string): StrikeKind[] {
  try {
    const raw = window.localStorage.getItem(storageKey(threatId));
    const parsed: unknown = raw ? JSON.parse(raw) : [];
    return Array.isArray(parsed) ? (parsed.filter((k) => ["platform", "safaricom", "advisory", "kecirt"].includes(k)) as StrikeKind[]) : [];
  } catch {
    return []; // storage can be blocked; the console must still work
  }
}

interface Card {
  kind: StrikeKind;
  n: string;
  title: string;
  who: string;
  idle: string;
  body: string | null;
  open: { label: string; href: string } | null;
  note?: string;
}

function buildCards(pack: Playbooks | null, platform: string): Card[] {
  const mailto = (to: string, subject: string, body: string) => `mailto:${to}?subject=${encodeURIComponent(subject)}&body=${encodeURIComponent(body)}`;
  return [
    {
      kind: "platform",
      n: "A",
      title: "Report the account",
      who: `To ${pack?.platform_takedown.platform ?? platform}`,
      idle: "Text for the platform's impersonation form, citing the real scores and the first-seen date.",
      body: pack?.platform_takedown.body ?? null,
      open: pack ? { label: "Open the report form", href: pack.platform_takedown.report_url } : null,
    },
    {
      kind: "safaricom",
      n: "B",
      title: "Ask Safaricom to review the number",
      who: pack ? `To ${pack.safaricom_report.to}` : "To Safaricom fraud desk",
      idle: "Asks Safaricom to review the number or till that is collecting money. A review request; Safaricom decides what happens.",
      body: pack?.safaricom_report.body ?? null,
      open: pack ? { label: "Open an email draft", href: mailto(pack.safaricom_report.to, pack.safaricom_report.subject, pack.safaricom_report.body) } : null,
      note: pack && pack.contacts_verified === false ? "Confirm this address on Safaricom's site before you send." : undefined,
    },
    {
      kind: "advisory",
      n: "C",
      title: "Warn your customers",
      who: "WhatsApp status or broadcast",
      idle: "A short notice that names your real handle and Till, and tells people not to pay the fake one.",
      body: pack ? `${pack.consumer_warning.title}\n\n${pack.consumer_warning.body}` : null,
      open: pack ? { label: "Share on WhatsApp", href: pack.consumer_warning.whatsapp_share_url } : null,
    },
  ];
}

/**
 * "Prepare strike", never "freeze" (PRODUCT_V2 section 7). Halisi drafts; the merchant sends. A card
 * is only marked sent when the merchant ticks it themselves, and that tick is the only thing that moves
 * the case along.
 */
export function StrikeConsole({
  threatId,
  platform,
  locked,
  hasPaymentEvidence,
  onSent,
}: {
  threatId: string;
  platform: string;
  /** Merchant is not verified/curated: strikes are not available. */
  locked: boolean;
  hasPaymentEvidence: boolean;
  onSent: (kind: StrikeKind) => void;
}) {
  const reduced = useReducedMotion() ?? false;
  const [lang, setLang] = useState<Lang>("en");
  const [packs, setPacks] = useState<Partial<Record<Lang, Playbooks>>>({});
  const [sent, setSent] = useState<StrikeKind[]>(() => (typeof window === "undefined" ? [] : readSubmitted(threatId)));
  const [copied, setCopied] = useState<StrikeKind | null>(null);

  const prepare = useMutation({
    mutationFn: (l: Lang) => api.generatePlaybooks(threatId, l),
    onSuccess: (pack, l) => setPacks((p) => ({ ...p, [l]: pack })),
    onError: (err) => toast.error(err instanceof ApiError ? err.message : "Could not prepare the pack. Try again."),
  });

  const pack = packs[lang] ?? null;
  const cards = buildCards(pack, platform);

  async function copy(kind: StrikeKind, text: string) {
    try {
      await navigator.clipboard.writeText(text);
      setCopied(kind);
      window.setTimeout(() => setCopied((c) => (c === kind ? null : c)), 1800);
    } catch {
      toast.error("Copy was blocked by the browser. Select the text and copy it by hand.");
    }
  }

  function toggleSent(kind: StrikeKind) {
    const next = sent.includes(kind) ? sent.filter((k) => k !== kind) : [...sent, kind];
    setSent(next);
    try {
      window.localStorage.setItem(storageKey(threatId), JSON.stringify(next));
    } catch {
      /* ignore: the case status below still records it */
    }
    if (!sent.includes(kind)) onSent(kind);
  }

  if (locked) {
    return (
      <div className="grid gap-4 border border-dashed border-line-strong p-6 sm:p-8">
        <p className="font-display text-[clamp(1.5rem,3vw,2.25rem)] leading-none font-extrabold uppercase">Strikes are locked.</p>
        <p className="measure text-fg-2">Reports carry weight only when they come from the real owner. Verify your brand and this pack unlocks.</p>
        <Link href="/dashboard/verify" className="inline-flex h-12 w-fit items-center border border-fg bg-fg px-6 text-[0.9375rem] font-semibold text-bg active:scale-[0.98]">
          Verify ownership
        </Link>
      </div>
    );
  }

  return (
    <div className="grid gap-6">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <p className="measure text-[0.9375rem] text-fg-2">
          Three drafts, written from this case&rsquo;s facts. Halisi sends nothing. You read each one, send it, and tick it off.
        </p>
        <div role="group" aria-label="Language of the drafts" className="flex border border-line">
          {(["en", "sw"] as const).map((l) => (
            <button
              key={l}
              type="button"
              aria-pressed={lang === l}
              onClick={() => setLang(l)}
              className={cn(
                "type-caption h-10 min-w-14 cursor-pointer px-4 transition-colors duration-(--dur-micro)",
                lang === l ? "bg-fg text-bg" : "text-fg-2 hover:text-fg",
              )}
            >
              {l === "en" ? "English" : "Kiswahili"}
            </button>
          ))}
        </div>
      </div>

      {!pack ? (
        <button
          type="button"
          disabled={prepare.isPending}
          onClick={() => prepare.mutate(lang)}
          className="inline-flex h-14 w-full cursor-pointer items-center justify-center gap-3 border border-fg bg-fg px-6 text-[1.0625rem] font-semibold text-bg transition-transform duration-(--dur-micro) active:scale-[0.99] disabled:cursor-wait disabled:opacity-60 sm:w-fit sm:min-w-72"
        >
          {prepare.isPending ? (
            <>
              Writing the drafts<span className="caret" aria-hidden="true" />
            </>
          ) : (
            "Prepare strike pack"
          )}
        </button>
      ) : null}

      <ol className="grid gap-px border border-line bg-line lg:grid-cols-3">
        {cards.map((c, i) => {
          const done = sent.includes(c.kind);
          return (
            <motion.li
              key={`${c.kind}-${lang}-${pack ? "ready" : "idle"}`}
              initial={reduced || !pack ? false : { opacity: 0, y: 16 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.7, delay: i * 0.1, ease: bezier("out") }}
              className="grid content-start gap-4 bg-bg p-5 sm:p-6"
            >
              <div className="flex items-baseline justify-between gap-3">
                <span className="font-display text-5xl leading-none font-black text-fg-3">{c.n}</span>
                <span className={cn("type-caption", done ? "text-fg" : "text-fg-3")}>{done ? "Sent" : c.body ? "Ready" : "Not prepared"}</span>
              </div>
              <div className="grid gap-1">
                <h3 className="type-heading">{c.title}</h3>
                <p className="type-caption text-fg-3 normal-case">{c.who}</p>
              </div>

              {c.body ? (
                <>
                  <pre lang={lang} className="max-h-72 overflow-auto border border-line bg-bg-2 p-4 font-sans text-[0.9375rem] leading-relaxed whitespace-pre-wrap text-fg-2">
                    {c.body}
                  </pre>
                  {c.note ? <p className="text-[0.8125rem] text-warn">{c.note}</p> : null}
                  <div className="flex flex-wrap gap-2">
                    <ActionButton onClick={() => void copy(c.kind, c.body ?? "")} icon={copied === c.kind ? <Check className="size-4" /> : <Copy className="size-4" />}>
                      {copied === c.kind ? "Copied" : "Copy"}
                    </ActionButton>
                    {c.open ? (
                      <a
                        href={c.open.href}
                        target={c.open.href.startsWith("mailto:") ? undefined : "_blank"}
                        rel="noopener noreferrer"
                        className="type-caption inline-flex h-11 items-center gap-2 border border-line-strong px-4 transition-colors duration-(--dur-micro) hover:bg-bg-2 active:scale-[0.97]"
                      >
                        <ExternalLink className="size-4" aria-hidden="true" /> {c.open.label}
                      </a>
                    ) : null}
                  </div>
                  <label className="flex min-h-11 cursor-pointer items-center gap-3 border-t border-line pt-4 text-[0.9375rem]">
                    <input type="checkbox" checked={done} onChange={() => toggleSent(c.kind)} className="size-5 shrink-0 cursor-pointer accent-(--color-paper)" />
                    I sent this
                  </label>
                </>
              ) : (
                <>
                  <p className="text-[0.9375rem] text-fg-3">{c.idle}</p>
                  {c.kind === "safaricom" && !hasPaymentEvidence ? (
                    <p className="text-[0.8125rem] text-warn">No payment number was found on this page, so this report will be thin.</p>
                  ) : null}
                </>
              )}
            </motion.li>
          );
        })}
      </ol>

      {pack ? (
        <div className="grid gap-4 border-t border-line pt-5 text-[0.8125rem] text-fg-3 sm:grid-cols-[1fr_auto] sm:items-center">
          <p>
            {pack.generator === "llm" ? `Drafted by ${pack.model ?? "a language model"} via NVIDIA NIM` : "Drafted from a Halisi template"}. Read it before you send it.
            Every number and handle in it comes from this case.
          </p>
          <button
            type="button"
            disabled={prepare.isPending}
            onClick={() => prepare.mutate(lang)}
            className="type-caption h-10 cursor-pointer border border-line px-4 text-fg-2 hover:text-fg disabled:opacity-50"
          >
            {prepare.isPending ? "Rewriting" : "Rewrite drafts"}
          </button>
        </div>
      ) : null}

      <div className="grid gap-3 border border-line p-5 sm:grid-cols-[1fr_auto] sm:items-center sm:p-6">
        <div className="grid gap-1">
          <h3 className="type-heading">Evidence dossier</h3>
          <p className="text-[0.9375rem] text-fg-2">
            A PDF of this case with a SHA-256 over the evidence bundle, so anyone can check it was not edited afterwards. Attach it to A and B.
          </p>
        </div>
        <a
          href={`/api/halisi/threats/${encodeURIComponent(threatId)}/dossier?format=pdf`}
          target="_blank"
          rel="noopener noreferrer"
          className="type-caption inline-flex h-11 items-center gap-2 border border-line-strong px-4 transition-colors duration-(--dur-micro) hover:bg-bg-2 active:scale-[0.97]"
        >
          <Download className="size-4" aria-hidden="true" /> Download PDF
        </a>
      </div>

      {pack ? (
        <details className="group border border-line">
          <summary className="flex min-h-12 cursor-pointer list-none items-center justify-between px-5 text-[0.9375rem] text-fg-2 hover:text-fg">
            Also report to KE-CIRT/CC
            <span className="type-caption text-fg-3">{sent.includes("kecirt") ? "Sent" : "Optional"}</span>
          </summary>
          <div className="grid gap-4 border-t border-line p-5">
            <p className="type-caption text-fg-3 normal-case">To {pack.kecirt_report.to}</p>
            <pre lang={lang} className="max-h-64 overflow-auto border border-line bg-bg-2 p-4 font-sans text-[0.9375rem] leading-relaxed whitespace-pre-wrap text-fg-2">{pack.kecirt_report.body}</pre>
            <div className="flex flex-wrap items-center gap-3">
              <ActionButton onClick={() => void copy("kecirt", pack.kecirt_report.body)} icon={copied === "kecirt" ? <Check className="size-4" /> : <Copy className="size-4" />}>
                {copied === "kecirt" ? "Copied" : "Copy"}
              </ActionButton>
              <label className="flex min-h-11 cursor-pointer items-center gap-3 text-[0.9375rem]">
                <input type="checkbox" checked={sent.includes("kecirt")} onChange={() => toggleSent("kecirt")} className="size-5 cursor-pointer accent-(--color-paper)" />
                I sent this
              </label>
            </div>
          </div>
        </details>
      ) : null}
    </div>
  );
}

function ActionButton({ onClick, icon, children }: { onClick: () => void; icon: ReactNode; children: ReactNode }) {
  return (
    <button
      type="button"
      onClick={onClick}
      className="type-caption inline-flex h-11 cursor-pointer items-center gap-2 border border-line-strong px-4 transition-colors duration-(--dur-micro) hover:bg-bg-2 active:scale-[0.97]"
    >
      <span aria-hidden="true">{icon}</span>
      {children}
    </button>
  );
}
