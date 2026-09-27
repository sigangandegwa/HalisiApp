import { Button as ButtonPrimitive } from "@base-ui/react/button";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";

/**
 * Halisi button (restyled shadcn/base-ui). Pills only; ink on paper, paper on night.
 * Motion: 160 ms press, 320 ms colour, custom easing. Focus uses the global designed ring.
 */
export const buttonVariants = cva(
  [
    "group/button relative inline-flex shrink-0 cursor-pointer items-center justify-center gap-2 rounded-pill",
    "font-sans font-medium whitespace-nowrap select-none",
    "transition-[background-color,color,border-color,transform,opacity] duration-(--dur-ui) ease-quart",
    "active:scale-[0.98] active:duration-(--dur-micro)",
    "disabled:pointer-events-none disabled:opacity-45 aria-disabled:pointer-events-none aria-disabled:opacity-45",
    "[&_svg]:pointer-events-none [&_svg]:shrink-0",
  ],
  {
    variants: {
      variant: {
        primary: "bg-fg text-bg hover:bg-[color-mix(in_oklab,var(--fg)_84%,var(--bg))]",
        secondary: "border border-line-strong bg-transparent text-fg hover:border-fg hover:bg-bg-2",
        ghost: "bg-transparent text-fg hover:bg-bg-2",
        quiet: "bg-bg-2 text-fg hover:bg-bg-3",
        fake: "bg-feki text-paper hover:bg-feki-ink",
        real: "bg-halisi text-paper hover:bg-[color-mix(in_oklab,var(--color-halisi)_86%,var(--color-ink))] night:bg-halisi-glow night:text-night",
        link: "h-auto rounded-none p-0 text-fg underline decoration-line-strong decoration-1 underline-offset-[0.25em] hover:decoration-fg",
      },
      size: {
        sm: "h-9 px-4 text-[0.875rem] pointer-coarse:h-11 [&_svg:not([class*='size-'])]:size-4",
        md: "h-11 px-5 text-[0.9375rem] [&_svg:not([class*='size-'])]:size-[1.05rem]",
        lg: "h-14 px-7 text-body [&_svg:not([class*='size-'])]:size-5",
        icon: "size-11 [&_svg:not([class*='size-'])]:size-[1.15rem]",
        "icon-sm": "size-9 pointer-coarse:size-11 [&_svg:not([class*='size-'])]:size-4",
      },
    },
    compoundVariants: [{ variant: "link", className: "h-auto px-0" }],
    defaultVariants: { variant: "primary", size: "md" },
  },
);

export type ButtonVariants = VariantProps<typeof buttonVariants>;

export function Button({ className, variant, size, ...props }: ButtonPrimitive.Props & ButtonVariants) {
  return <ButtonPrimitive data-slot="button" className={cn(buttonVariants({ variant, size }), className)} {...props} />;
}
