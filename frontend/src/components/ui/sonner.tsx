"use client";

import { Toaster as Sonner, type ToasterProps } from "sonner";

/**
 * Toasts restyled as small documents with a severity rail (FRONTEND.md section 6.10).
 * One visible at a time; the rest queue. aria-live polite is sonner's default.
 */
export function Toaster(props: ToasterProps) {
  return (
    <Sonner
      position="bottom-right"
      visibleToasts={1}
      gap={10}
      offset={20}
      mobileOffset={12}
      toastOptions={{
        unstyled: true,
        duration: 8000,
        classNames: {
          toast: [
            "group/toast relative flex w-[min(92vw,24rem)] items-start gap-3 overflow-hidden rounded-doc border border-line",
            "bg-bg-2 py-4 pr-4 pl-6 text-fg shadow-[0_1px_0_color-mix(in_oklab,var(--color-paper)_6%,transparent)_inset]",
            "before:absolute before:inset-y-0 before:left-0 before:w-[3px] before:bg-fg-3",
            "data-[type=error]:before:bg-feki data-[type=warning]:before:bg-caution data-[type=success]:before:bg-real",
          ].join(" "),
          title: "text-[0.9375rem] font-semibold leading-snug",
          description: "mt-1 text-small text-fg-2",
          actionButton:
            "ml-auto h-9 shrink-0 cursor-pointer rounded-pill bg-fg px-4 text-[0.8125rem] font-medium text-bg transition-colors duration-(--dur-ui) ease-quart hover:opacity-90",
          cancelButton: "h-9 shrink-0 cursor-pointer rounded-pill px-3 text-[0.8125rem] text-fg-2 hover:text-fg",
          closeButton: "text-fg-3",
          icon: "mt-0.5 text-fg-2",
        },
      }}
      {...props}
    />
  );
}
