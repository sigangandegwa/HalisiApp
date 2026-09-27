"use client";

import { motion } from "motion/react";
import { forwardRef } from "react";
import { ArrowRight, ClipboardPaste, Link2 } from "lucide-react";
import { useClientValue } from "@/lib/hooks";
import { useI18n } from "@/lib/i18n/provider";
import { bezier } from "@/lib/motion";
import { cn } from "@/lib/utils";

/**
 * The checker pill (FRONTEND.md section 7): 64 px, paper-2 fill, ink hairline.
 * States: idle, focused (2 px ink ring, paper-2 -> paper), collapsed (becomes the 2 px scan bar
 * while pending and while the verdict plays), error (inline, feki-ink, never a toast).
 */
export const CheckerInput = forwardRef<
  HTMLInputElement,
  {
    value: string;
    onChange: (v: string) => void;
    onSubmit: () => void;
    onPasteText?: (text: string) => void;
    collapsed: boolean;
    pendingLabel?: string | null;
    error?: string | null;
  }
>(function CheckerInput({ value, onChange, onSubmit, onPasteText, collapsed, pendingLabel, error }, ref) {
  const { t } = useI18n();
  const canPaste = useClientValue(() => Boolean(navigator.clipboard?.readText), false);

  const ease = bezier("quart");
  return (
    <form
      role="search"
      aria-label={t("checker.label")}
      noValidate
      onSubmit={(e) => {
        e.preventDefault();
        onSubmit();
      }}
    >
      <label htmlFor="checker-input" className="sr-only">
        {t("checker.label")}
      </label>
      <div className="relative h-16">
        <motion.div
          className={cn(
            "group/pill absolute inset-0 flex items-center gap-2 rounded-pill border bg-bg-2 pr-2 pl-5",
            "transition-[background-color,border-color,box-shadow] duration-(--dur-ui) ease-quart",
            "focus-within:border-fg focus-within:bg-bg focus-within:shadow-[0_0_0_1px_var(--fg)]",
            error ? "border-fake" : "border-line-strong hover:border-[color-mix(in_oklab,var(--fg)_50%,transparent)]",
          )}
          initial={false}
          animate={collapsed ? { opacity: 0, scaleY: 0.5 } : { opacity: 1, scaleY: 1 }}
          transition={{ duration: 0.32, ease }}
          style={{ pointerEvents: collapsed ? "none" : "auto" }}
          aria-hidden={collapsed}
        >
          <Link2 className="size-5 shrink-0 text-fg-3" strokeWidth={1.5} aria-hidden="true" />
          <input
            ref={ref}
            id="checker-input"
            name="q"
            type="text"
            inputMode="url"
            autoComplete="off"
            autoCapitalize="off"
            autoCorrect="off"
            spellCheck={false}
            enterKeyHint="go"
            placeholder={t("checker.placeholder")}
            value={value}
            onChange={(e) => onChange(e.target.value)}
            onPaste={(e) => {
              const text = e.clipboardData.getData("text");
              if (text && onPasteText) {
                e.preventDefault();
                onPasteText(text.trim());
              }
            }}
            aria-invalid={Boolean(error)}
            aria-describedby={error ? "checker-error" : undefined}
            disabled={collapsed}
            className="h-full min-w-0 flex-1 bg-transparent text-[1.0625rem] text-fg outline-none placeholder:text-fg-3 focus-visible:outline-none"
          />
          {!value && canPaste ? (
            <button
              type="button"
              onClick={async () => {
                try {
                  const text = await navigator.clipboard.readText();
                  if (text) onPasteText?.(text.trim());
                } catch {
                  /* permission denied: the user can still paste manually */
                }
              }}
              className="hidden h-11 shrink-0 cursor-pointer items-center gap-2 rounded-pill px-3 text-[0.875rem] font-medium text-fg-2 transition-colors duration-(--dur-ui) ease-quart hover:bg-bg-3 hover:text-fg sm:inline-flex"
            >
              <ClipboardPaste className="size-4" strokeWidth={1.5} aria-hidden="true" />
              {t("checker.paste")}
            </button>
          ) : null}
          <button
            type="submit"
            className="inline-flex h-12 shrink-0 cursor-pointer items-center gap-2 rounded-pill bg-fg px-5 text-[0.9375rem] font-medium text-bg transition-[background-color,transform] duration-(--dur-ui) ease-quart hover:bg-[color-mix(in_oklab,var(--fg)_84%,var(--bg))] active:scale-[0.97] sm:px-6"
          >
            {t("checker.submit")}
            <ArrowRight className="size-4 transition-transform duration-(--dur-ui) ease-out group-focus-within/pill:translate-x-0.5" strokeWidth={1.75} aria-hidden="true" />
          </button>
        </motion.div>

        {/* the scan bar the pill collapses into */}
        <motion.div
          aria-hidden="true"
          className="pointer-events-none absolute inset-x-0 top-1/2 h-0.5 -translate-y-1/2 origin-left overflow-hidden bg-fg"
          initial={false}
          animate={collapsed ? { scaleX: 1, opacity: 1 } : { scaleX: 0, opacity: 0 }}
          transition={{ duration: collapsed ? 0.32 : 0.2, ease }}
        >
          <span className="absolute inset-y-0 left-0 w-1/3 bg-[linear-gradient(90deg,transparent,var(--bg),transparent)] opacity-80" style={{ animation: "halisi-sweep 1.1s var(--ease-in-out) infinite" }} />
        </motion.div>
      </div>

      <div className="mt-3 min-h-6">
        {error ? (
          <p id="checker-error" role="alert" className="text-small text-fake">
            {error}
          </p>
        ) : collapsed && pendingLabel ? (
          <p role="status" className="font-mono text-[0.75rem] tracking-[0.04em] text-fg-2 uppercase">
            {pendingLabel}
          </p>
        ) : null}
      </div>
    </form>
  );
});
