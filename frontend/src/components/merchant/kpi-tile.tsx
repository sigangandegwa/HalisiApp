import { ReactNode } from "react";

interface KpiTileProps {
  label: string;
  value: ReactNode;
  subtitle?: string;
  highlight?: boolean;
}

export function KpiTile({ label, value, subtitle, highlight }: KpiTileProps) {
  return (
    <div className="desk-panel p-6 flex flex-col justify-between">
      <h3 className="type-caption text-fg-2 mb-4">{label}</h3>
      <div className={`type-data text-display-l ${highlight ? "text-[var(--color-feki)]" : "text-fg"}`}>
        {value}
      </div>
      {subtitle && (
        <p className="text-sm text-fg-3 mt-2">{subtitle}</p>
      )}
    </div>
  );
}
