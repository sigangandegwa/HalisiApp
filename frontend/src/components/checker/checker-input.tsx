"use client";

import { forwardRef } from "react";
import { ArrowRight } from "lucide-react";
import { useI18n } from "@/lib/i18n/provider";
import { cn } from "@/lib/utils";

/**
 * The one field. A link, a @handle, a till or a phone number all go in the same box; the checker
 * works out which it is. One input, one round button, nothing else competing for the thumb.
 * `collapsed` dims it while the engine works or the verdict plays.
 */
export const CheckerInput = forwardRef<
  HTMLInputElement,
  {
    value: string;
    onChange: (v: string) => void;
    onSubmit: () => void;
    onPasteText?: (text: string) => void;
    collapsed: boolean;
    error?: string | null;
  }
>(function CheckerInput({ value, onChange, onSubmit, onPasteText, collapsed, error }, ref) {
  const { t } = useI18n();
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
      <div
        className={cn(
          "group/field relative transition-opacity duration-(--dur-ui) ease-quart",
          collapsed && "pointer-events-none opacity-40",
        )}
      >
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
          disabled={collapsed}
          aria-invalid={Boolean(error)}
          aria-describedby={error ? "checker-error" : undefined}
          className={cn(
            "h-16 w-full min-w-0 rounded-pill border bg-transparent pr-20 pl-6 text-[1.0625rem] text-fg",
            "transition-[border-color,background-color] duration-(--dur-ui) ease-quart outline-none",
            "placeholder:text-fg-3 hover:border-fg-3 focus:border-fg focus:bg-bg-2",
            error ? "border-fake" : "border-line-strong",
          )}
        />
        <button
          type="submit"
          disabled={collapsed}
          aria-label={t("checker.submit")}
          className="absolute top-1.5 right-1.5 grid size-[3.25rem] cursor-pointer place-items-center rounded-full bg-fg text-bg transition-transform duration-(--dur-ui) ease-out hover:scale-[1.04] active:scale-95"
        >
          <ArrowRight className="size-5" strokeWidth={2} aria-hidden="true" />
        </button>
      </div>
      {error ? (
        <p id="checker-error" role="alert" className="mt-3 pl-6 text-small text-fake">
          {error}
        </p>
      ) : null}
    </form>
  );
});
