import Image from "next/image";
import { cn } from "@/lib/utils";

/**
 * Merchant logos and suspect avatars. `unoptimized` because avatars come from arbitrary CDNs
 * (signed IG URLs expire) and fixtures are already sized; explicit width/height prevent CLS.
 */
export function LogoImage({
  src,
  alt,
  size = 96,
  className,
  priority = false,
  rounded = "full",
}: {
  src: string | null | undefined;
  alt: string;
  size?: number;
  className?: string;
  priority?: boolean;
  rounded?: "full" | "doc";
}) {
  const radius = rounded === "full" ? "rounded-full" : "rounded-doc";
  // A `size-*` class controls the rendered size responsively; otherwise use the intrinsic size.
  const sized = /(^|\s)(\w+:)?size-/.test(className ?? "");
  if (!src) {
    const initials = alt
      .replace(/^@/, "")
      .split(/[\s._-]+/)
      .filter(Boolean)
      .slice(0, 2)
      .map((w) => w[0]?.toUpperCase())
      .join("");
    return (
      <span
        role="img"
        aria-label={alt}
        className={cn("grid shrink-0 place-items-center bg-bg-3 font-mono text-fg-2", radius, className)}
        style={sized ? { fontSize: size * 0.28 } : { width: size, height: size, fontSize: size * 0.32 }}
      >
        {initials || "?"}
      </span>
    );
  }
  return (
    <Image
      src={src}
      alt={alt}
      width={size}
      height={size}
      unoptimized
      priority={priority}
      className={cn("shrink-0 bg-bg-2 object-cover", radius, className)}
      style={sized ? undefined : { width: size, height: size }}
    />
  );
}
