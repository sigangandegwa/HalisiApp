"use client";

import { useState } from "react";
import { toast } from "sonner";
import { Bell, Copy } from "lucide-react";
import { EvidenceBars } from "@/components/checker/evidence-bars";
import { HashGrid } from "@/components/checker/hash-grid";
import { CheckerInput } from "@/components/checker/checker-input";
import { VerdictStamp } from "@/components/checker/verdict-stamp";
import { Button } from "@/components/ui/button";
import { Field, Input, Textarea } from "@/components/ui/input";
import { Sheet, SheetContent, SheetDescription, SheetHeader, SheetTitle, SheetTrigger } from "@/components/ui/sheet";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";
import { ease } from "@/lib/motion";
import type { Dimension } from "@/lib/schemas";
import { cn } from "@/lib/utils";

const SAMPLE_DIMS: Dimension[] = [
  { key: "visual", label: "Logo match", score: 100, weight: 0.3, available: true, evidence: "pHash distance 2/64 · dHash distance 0/64" },
  { key: "identity", label: "Name & handle", score: 100, weight: 0.25, available: true, evidence: "'nairobi_sneakervault_official_ke' is 'nairobisneakervault' + affix 'official' 'ke'" },
  { key: "payment", label: "Payment details", score: 100, weight: 0.25, available: true, evidence: "Asks for payment to number 0798 *** 111 (not registered to this business)" },
  { key: "language", label: "Scam language", score: 0, weight: 0.1, available: false, evidence: "No data" },
  { key: "account", label: "Account signals", score: 60, weight: 0.1, available: true, evidence: "11 posts · 410 followers" },
];

export function ButtonDemo() {
  return (
    <div className="grid gap-6">
      {(["primary", "secondary", "ghost", "quiet", "real", "fake", "link"] as const).map((v) => (
        <div key={v} className="flex flex-wrap items-center gap-3">
          <span className="w-24 font-mono text-[0.75rem] text-fg-3">{v}</span>
          <Button variant={v} size="sm">Small</Button>
          <Button variant={v}>Medium</Button>
          <Button variant={v} size="lg">Large</Button>
          <Button variant={v} disabled>Disabled</Button>
          {v !== "link" ? (
            <Button variant={v} size="icon" aria-label="Copy">
              <Copy strokeWidth={1.5} />
            </Button>
          ) : null}
        </div>
      ))}
      <p className="text-small text-fg-3">Tab through to see the focus ring: 2 px, offset 3 px, ink on paper, paper on night.</p>
    </div>
  );
}

export function FieldDemo() {
  return (
    <div className="grid gap-6 md:grid-cols-2">
      <Field label="Default" hint="Hint text sits under the control." htmlFor="sg-a">
        <Input id="sg-a" placeholder="Placeholder is never the label" />
      </Field>
      <Field label="Mono data" htmlFor="sg-b">
        <Input id="sg-b" mono defaultValue="0712 345 678" />
      </Field>
      <Field label="Error" error="That doesn’t look like a Kenyan number." htmlFor="sg-c">
        <Input id="sg-c" aria-invalid defaultValue="12" />
      </Field>
      <Field label="Disabled" htmlFor="sg-d">
        <Input id="sg-d" disabled defaultValue="Read only" />
      </Field>
      <Field label="Textarea" htmlFor="sg-e" className="md:col-span-2">
        <Textarea id="sg-e" defaultValue="Documents have sharp corners." />
      </Field>
    </div>
  );
}

export function CheckerStates() {
  const [v, setV] = useState("");
  return (
    <div className="grid gap-8">
      <div>
        <p className="mb-2 font-mono text-[0.75rem] text-fg-3">idle / focused (click in)</p>
        <CheckerInput value={v} onChange={setV} onSubmit={() => {}} collapsed={false} />
      </div>
      <div>
        <p className="mb-2 font-mono text-[0.75rem] text-fg-3">error</p>
        <CheckerInput value="facebook.co/x" onChange={() => {}} onSubmit={() => {}} collapsed={false} error="That doesn’t look like an Instagram, Facebook, TikTok or X link." />
      </div>
      <div>
        <p className="mb-2 font-mono text-[0.75rem] text-fg-3">collapsed into the scan bar (pending)</p>
        <CheckerInput value="@nairobi_sneakervault_official_ke" onChange={() => {}} onSubmit={() => {}} collapsed pendingLabel="Comparing logo…" />
      </div>
    </div>
  );
}

export function TabsDemo() {
  return (
    <div className="grid gap-10">
      <Tabs defaultValue="customers">
        <TabsList>
          <TabsTrigger value="customers">Customers</TabsTrigger>
          <TabsTrigger value="platform">Instagram / Facebook</TabsTrigger>
          <TabsTrigger value="safaricom">Safaricom</TabsTrigger>
          <TabsTrigger value="kecirt">KE-CIRT/CC</TabsTrigger>
        </TabsList>
        <TabsContent value="customers" className="text-fg-2">Line tabs: the 2 px rule slides between tabs (ease.out, 320 ms).</TabsContent>
        <TabsContent value="platform" className="text-fg-2">Platform takedown text.</TabsContent>
        <TabsContent value="safaricom" className="text-fg-2">Safaricom report.</TabsContent>
        <TabsContent value="kecirt" className="text-fg-2">KE-CIRT/CC report.</TabsContent>
      </Tabs>
      <Tabs defaultValue="en">
        <TabsList variant="pill">
          <TabsTrigger value="en">English</TabsTrigger>
          <TabsTrigger value="sw">Kiswahili</TabsTrigger>
        </TabsList>
      </Tabs>
    </div>
  );
}

export function OverlayDemo() {
  return (
    <div className="flex flex-wrap items-center gap-3">
      <Button variant="secondary" onClick={() => toast("Impersonator detected: @nairobi_sneakervault_official_ke", { description: "Uses a logo 100% similar to Nairobi Sneaker Vault’s.", action: { label: "Open", onClick: () => {} } })}>
        <Bell strokeWidth={1.5} /> Alert toast
      </Button>
      <Button variant="secondary" onClick={() => toast.error("Fake page reported", { description: "Error rail = vermilion." })}>Error toast</Button>
      <Button variant="secondary" onClick={() => toast.success("Takedown resolved", { description: "Success rail = verified green." })}>Success toast</Button>
      <Button variant="secondary" onClick={() => toast.warning("Score rose to 91", { description: "Warning rail = amber." })}>Warning toast</Button>
      <Sheet>
        <SheetTrigger render={<Button variant="secondary" />}>Open sheet</SheetTrigger>
        <SheetContent>
          <SheetHeader>
            <SheetTitle>Alerts</SheetTitle>
            <SheetDescription>Slides in from the right (480 ms, ease.out).</SheetDescription>
          </SheetHeader>
          <p className="p-6 text-fg-2">No alerts. Halisi is watching.</p>
        </SheetContent>
      </Sheet>
      <Tooltip>
        <TooltipTrigger render={<Button variant="ghost" />}>Tooltip</TooltipTrigger>
        <TooltipContent>pHash distance 2/64</TooltipContent>
      </Tooltip>
    </div>
  );
}

export function EvidenceDemo() {
  const [run, setRun] = useState(0);
  return (
    <div className="grid gap-8" key={run}>
      <div className="flex flex-wrap items-center gap-8">
        <HashGrid hex="ab44dc9b7a8e3a20" compareHex="ab44dc9b7a8e3a22" label="Registered logo" instant={run === 0} />
        <HashGrid hex="ab44dc9b7a8e3a22" compareHex="ab44dc9b7a8e3a20" label="This page" instant={run === 0} delay={40} />
        <Button variant="secondary" size="sm" onClick={() => setRun((n) => n + 1)}>Replay</Button>
      </div>
      <div className="max-w-xl">
        <EvidenceBars dimensions={SAMPLE_DIMS} color="var(--color-feki)" instant={run === 0} />
      </div>
    </div>
  );
}

export function StampDemo() {
  return (
    <div className="grid gap-10">
      <div className="flex flex-wrap items-end gap-10">
        <VerdictStamp verdict="official" size="md" />
        <VerdictStamp verdict="impersonation" size="md" />
        <VerdictStamp verdict="suspicious" size="md" />
        <VerdictStamp verdict="no_match" size="md" />
      </div>
      <div className="flex flex-wrap items-end gap-6">
        <VerdictStamp verdict="official" size="sm" />
        <VerdictStamp verdict="impersonation" size="sm" />
        <VerdictStamp verdict="suspicious" size="sm" />
        <VerdictStamp verdict="no_match" size="sm" />
      </div>
    </div>
  );
}

const CURVES = Object.entries(ease) as [keyof typeof ease, readonly [number, number, number, number]][];

export function MotionDemo() {
  const [on, setOn] = useState(false);
  return (
    <div className="grid gap-6">
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {CURVES.map(([name, c]) => (
          <figure key={name} className="m-0 rounded-doc border border-line p-4">
            <svg viewBox="-0.1 -0.6 1.2 2.2" className="h-28 w-full" aria-hidden="true">
              <path d="M0 1 L1 1 M0 0 L1 0" stroke="var(--line)" strokeWidth="0.01" />
              <path d={`M0 1 C${c[0]} ${1 - c[1]} ${c[2]} ${1 - c[3]} 1 0`} fill="none" stroke="var(--fg)" strokeWidth="0.025" />
            </svg>
            <figcaption className="mt-2 font-mono text-[0.75rem]">
              ease.{name}
              <span className="block text-fg-3">cubic-bezier({c.join(", ")})</span>
            </figcaption>
            <div className="mt-3 h-2 rounded-pill bg-bg-2">
              <div
                className="size-2 rounded-full bg-fg"
                style={{ transform: `translateX(${on ? "calc(100% * 20)" : "0"})`, transition: `transform 800ms cubic-bezier(${c.join(",")})` }}
              />
            </div>
          </figure>
        ))}
      </div>
      <div>
        <Button variant="secondary" size="sm" onClick={() => setOn((v) => !v)}>
          Play curves
        </Button>
      </div>
    </div>
  );
}

export function Swatch({ name, value, note, className, dark }: { name: string; value: string; note?: string; className?: string; dark?: boolean }) {
  return (
    <figure className="m-0 overflow-hidden rounded-doc border border-line">
      <div className={cn("h-20", className)} style={{ background: value }} />
      <figcaption className={cn("p-3", dark && "theme-night")}>
        <p className="font-mono text-[0.75rem] font-medium">{name}</p>
        <p className="font-mono text-[0.6875rem] text-fg-3">{value}</p>
        {note ? <p className="mt-1 text-[0.75rem] text-fg-2">{note}</p> : null}
      </figcaption>
    </figure>
  );
}
