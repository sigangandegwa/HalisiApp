import type { Metadata } from "next";
import type { ReactNode } from "react";
import { Guilloche } from "@/components/brand/guilloche";
import { Microprint, MicroprintRing } from "@/components/brand/microprint";
import { Seal } from "@/components/brand/seal";
import { Misregister, Stamp } from "@/components/brand/stamp";
import { VerdictGlyph, Wordmark } from "@/components/brand/wordmark";
import { SiteNav } from "@/components/site/site-nav";
import {
  ButtonDemo,
  CheckerStates,
  EvidenceDemo,
  FieldDemo,
  MotionDemo,
  OverlayDemo,
  StampDemo,
  Swatch,
  TabsDemo,
} from "@/components/styleguide/demos";
import { fixtures } from "@/lib/fixtures";
import { dur, stagger } from "@/lib/motion";

export const metadata: Metadata = { title: "Styleguide", robots: { index: false } };

const RAW = [
  { name: "--color-paper", value: "#F2EEE3", note: "Public background (never #fff)" },
  { name: "--color-paper-2", value: "#E8E2D2", note: "Cards and wells on paper" },
  { name: "--color-ink", value: "#12130F", note: "Text, primary buttons (never #000)" },
  { name: "--color-halisi", value: "#1D5C43", note: "Verified only: banknote green" },
  { name: "--color-halisi-glow", value: "#43C58A", note: "Verified accent on Night Desk" },
  { name: "--color-feki", value: "#E4412A", note: "Fake only: large type, fills" },
  { name: "--color-feki-ink", value: "#B3301C", note: "Fake small text on paper (5.2:1)" },
  { name: "--color-caution", value: "#D99A1E", note: "Suspicious fills" },
  { name: "--color-caution-ink", value: "#8A5A00", note: "Suspicious text on paper" },
  { name: "--color-night", value: "#0D0F0C", note: "Night Desk background" },
  { name: "--color-night-2", value: "#161913", note: "Night Desk panels" },
];

const TYPE: { cls: string; label: string; sample: string; spec: string }[] = [
  { cls: "type-display-xl", label: "Display XL", sample: "FEKI.", spec: "Fraunces 600 · clamp(4.5rem, 14vw, 13rem) · -0.045em / 0.88" },
  { cls: "type-display-l", label: "Display L", sample: "Get Halisi Verified.", spec: "Fraunces 500 · clamp(2.75rem, 7vw, 6.5rem) · -0.035em / 0.95" },
  { cls: "type-display-m", label: "Display M", sample: "How protection works", spec: "Fraunces 500 · clamp(2rem, 4.2vw, 3.75rem)" },
  { cls: "type-display-l type-accent", label: "Display italic accent", sample: "halisi", spec: "Fraunces italic · SOFT 100" },
  { cls: "type-heading", label: "Heading", sample: "We couldn’t open that page.", spec: "Geist 600 · clamp(1.25rem, 2vw, 1.75rem) · -0.01em / 1.2" },
  { cls: "text-lede", label: "Lede", sample: "Paste an Instagram, Facebook or TikTok link.", spec: "Geist 400 · clamp(1.125rem, 1.4vw, 1.3125rem)" },
  { cls: "text-body", label: "Body", sample: "Halisi checks it against verified Kenyan businesses in seconds. Measure 45–75ch.", spec: "Geist 400 · 1.0625rem / 1.6" },
  { cls: "type-caption", label: "Caption", sample: "Forensic report", spec: "Geist 500 uppercase · 0.75rem · 0.08em" },
  { cls: "type-data text-[1.5rem]", label: "Data", sample: "Till 543 210 · 0798 *** 111", spec: "Geist Mono 500 · tabular-nums" },
];

const SPACE = [0.25, 0.5, 0.75, 1, 1.5, 2, 3, 4, 6, 8, 12, 16];

function Section({ id, title, children, note }: { id: string; title: string; children: ReactNode; note?: string }) {
  return (
    <section id={id} aria-labelledby={`${id}-t`} className="border-t border-line py-14">
      <div className="mb-8 flex flex-wrap items-baseline justify-between gap-3">
        <h2 id={`${id}-t`} className="type-display-m">{title}</h2>
        {note ? <p className="max-w-[48ch] text-small text-fg-3">{note}</p> : null}
      </div>
      {children}
    </section>
  );
}

/** Every token and state (TSK-020 Definition of Done: Collins signs off here). */
export default function StyleguidePage() {
  const sources = fixtures().sources;
  const merchant = fixtures().merchants[0];
  return (
    <div className="paper-grain min-h-dvh">
      <SiteNav />
      <main id="content" className="page-wrap pb-24">
        <header className="py-14">
          <p className="type-caption text-fg-3">TSK-020 · Design system</p>
          <h1 className="type-display-l mt-4">
            Halisi <span className="type-accent">styleguide</span>
          </h1>
          <p className="mt-5 max-w-[60ch] text-lede text-fg-2">
            Colour is evidence: green only when verified, vermilion only when fake, amber for caution. Everything else is ink on paper.
          </p>
          <p className="mt-4 font-mono text-[0.75rem] text-fg-3">
            Fixture sources: {Object.entries(sources).map(([k, v]) => `${k}=${v}`).join(" · ")}
          </p>
          <nav aria-label="Sections" className="mt-6 flex flex-wrap gap-x-5 gap-y-2 text-small">
            {["colour", "type", "space", "motion", "ornaments", "stamps", "components", "evidence", "night"].map((s) => (
              <a key={s} href={`#${s}`} className="underline decoration-line-strong underline-offset-4 hover:decoration-fg">{s}</a>
            ))}
          </nav>
        </header>

        <Section id="colour" title="Colour" note="Raw tokens, then the semantic tokens components actually use. Body text ≥ 4.5:1, display ≥ 3:1.">
          <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-6">
            {RAW.map((c) => <Swatch key={c.name} {...c} />)}
          </div>
          <div className="mt-10 grid gap-6 md:grid-cols-2">
            <div className="rounded-doc border border-line p-6">
              <p className="type-caption text-fg-3">Paper (semantic)</p>
              <ul className="mt-4 grid gap-2 font-mono text-[0.8125rem]">
                <li className="text-fg">fg · #12130F · 17.1:1</li>
                <li className="text-fg-2">fg-2 · ink 64% · 6.1:1</li>
                <li className="text-fg-3">fg-3 · ink 56% · 4.6:1</li>
                <li className="text-real">real · halisi · 7.5:1</li>
                <li className="text-fake">fake · feki-ink · 5.2:1</li>
                <li className="text-warn">warn · caution-ink · 5.0:1</li>
              </ul>
            </div>
            <div className="theme-night desk-panel p-6">
              <p className="type-caption text-fg-3">Night Desk (semantic)</p>
              <ul className="mt-4 grid gap-2 font-mono text-[0.8125rem]">
                <li className="text-fg">fg · paper · 16.4:1</li>
                <li className="text-fg-2">fg-2 · paper 70% · 8.2:1</li>
                <li className="text-fg-3">fg-3 · paper 56% · 4.6:1</li>
                <li className="text-real">real · halisi-glow · 8.9:1</li>
                <li className="text-fake">fake · feki · 4.9:1</li>
                <li className="text-warn">warn · caution · 8.0:1</li>
              </ul>
            </div>
          </div>
        </Section>

        <Section id="type" title="Type" note="Fraunces display over Geist body at ~12:1. text-wrap: balance on headings, pretty on paragraphs.">
          <div className="grid gap-10">
            {TYPE.map((row) => (
              <div key={row.label} className="grid gap-3 border-b border-line pb-8 md:grid-cols-[14rem_minmax(0,1fr)]">
                <div>
                  <p className="font-mono text-[0.75rem]">{row.label}</p>
                  <p className="mt-1 font-mono text-[0.6875rem] text-fg-3">{row.spec}</p>
                </div>
                <p className={`${row.cls} min-w-0 break-words`}>{row.sample}</p>
              </div>
            ))}
          </div>
        </Section>

        <Section id="space" title="Space, radius, grid" note="Space scale in rem. Radius: 2 px documents, 999 px pills, nothing in between. 12 columns, max 1440 px.">
          <div className="grid gap-2">
            {SPACE.map((s) => (
              <div key={s} className="flex items-center gap-4">
                <span className="w-16 font-mono text-[0.75rem] text-fg-3">{s}rem</span>
                <span className="h-3 bg-fg" style={{ width: `${s}rem` }} />
              </div>
            ))}
          </div>
          <div className="mt-10 flex flex-wrap gap-6">
            <div className="grid size-32 place-items-center rounded-doc border border-line-strong bg-bg-2 font-mono text-[0.75rem]">radius-doc 2px</div>
            <div className="grid h-14 w-48 place-items-center rounded-pill border border-line-strong bg-bg-2 font-mono text-[0.75rem]">radius-pill</div>
          </div>
          <div className="page-grid mt-10 !px-0" aria-hidden="true">
            {Array.from({ length: 12 }, (_, i) => (
              <div key={i} className="h-16 bg-[color-mix(in_oklab,var(--color-feki)_14%,transparent)] font-mono text-[0.625rem] text-fg-3">{i + 1}</div>
            ))}
          </div>
        </Section>

        <Section id="motion" title="Motion" note={`Durations: micro ${dur.micro * 1000} · ui ${dur.ui * 1000} · reveal ${dur.reveal * 1000} · story ${dur.story * 1000} ms. Stagger: words ${stagger.words * 1000} · lines ${stagger.lines * 1000} · cards ${stagger.cards * 1000} ms. Only transform, opacity, clip-path and (stamp only) filter animate.`}>
          <MotionDemo />
        </Section>

        <Section id="ornaments" title="Brand ornaments" note="All decorative ornaments are aria-hidden. The guilloche draws in once and never loops.">
          <div className="grid gap-8 md:grid-cols-3">
            <figure className="m-0 rounded-doc border border-line p-6">
              <Guilloche seed={7} layers={5} draw opacity={0.5} className="mx-auto w-full max-w-72 text-fg" />
              <figcaption className="mt-4 font-mono text-[0.75rem] text-fg-3">Guilloche · hypotrochoid rosette, seeded</figcaption>
            </figure>
            <figure className="m-0 grid place-items-center rounded-doc border border-line p-6">
              {merchant ? <Seal logoUrl={merchant.logo_url} name={merchant.business_name} size={220} /> : null}
              <figcaption className="mt-4 font-mono text-[0.75rem] text-fg-3">Seal · guilloche ring + microprint + logo</figcaption>
            </figure>
            <figure className="m-0 grid place-items-center rounded-doc border border-line p-6">
              <MicroprintRing id="sg-ring" size={220} radius={96} className="size-56 text-fg" />
              <figcaption className="mt-4 font-mono text-[0.75rem] text-fg-3">Microprint ring · 6 px Geist Mono</figcaption>
            </figure>
          </div>
          <div className="mt-8 grid gap-6">
            <Microprint />
            <p className="type-display-l">
              <Misregister offset={3}>ha1isi</Misregister> → halisi
            </p>
            <div className="flex flex-wrap items-center gap-6">
              <Wordmark className="text-[1.25rem]" />
              <span className="inline-flex items-center gap-2 text-real"><VerdictGlyph glyph="seal" /> official</span>
              <span className="inline-flex items-center gap-2 text-fake"><VerdictGlyph glyph="broken" /> fake</span>
              <span className="inline-flex items-center gap-2 text-warn"><VerdictGlyph glyph="triangle" /> caution</span>
              <span className="inline-flex items-center gap-2 text-fg"><VerdictGlyph glyph="circle" /> unknown</span>
            </div>
          </div>
        </Section>

        <Section id="stamps" title="Verdict stamps" note="Double-rule rectangle, −2.5°, feTurbulence + feDisplacementMap ink bleed. FEKI is misregistered.">
          <div className="mb-10">
            <Stamp word="FEKI." sub="Impersonator detected" color="var(--color-feki)" misregister />
          </div>
          <StampDemo />
        </Section>

        <Section id="components" title="Components and states" note="Restyled shadcn/base-ui primitives: button, input, tabs, sheet, toast, tooltip.">
          <div className="grid gap-14">
            <ButtonDemo />
            <FieldDemo />
            <TabsDemo />
            <OverlayDemo />
            <CheckerStates />
          </div>
        </Section>

        <Section id="evidence" title="Forensic evidence" note="Real bit grids from 16-hex pHashes; differing bits flash twice. Bars scale from 0; unavailable signals are dashed.">
          <EvidenceDemo />
        </Section>

        <section id="night" aria-labelledby="night-t" className="theme-night -mx-[var(--gutter)] mt-6 rounded-doc px-[var(--gutter)] py-14">
          <h2 id="night-t" className="type-display-m">Night Desk</h2>
          <p className="mt-3 max-w-[56ch] text-fg-2">The merchant world. Paper-based text tones, 1 px rules and an inner highlight instead of shadows.</p>
          <div className="mt-10 grid gap-10">
            <ButtonDemo />
            <StampDemo />
            <div className="desk-panel p-6">
              <EvidenceDemo />
            </div>
            <FieldDemo />
          </div>
        </section>
      </main>
    </div>
  );
}
