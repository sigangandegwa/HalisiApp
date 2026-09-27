"use client";

import { motion } from "motion/react";
import { useMemo } from "react";
import type { Dimension } from "@/lib/schemas";

interface RadarProps {
  dimensions: Dimension[];
}

const AXES = [
  { key: "visual", label: "Visual" },
  { key: "identity", label: "Identity" },
  { key: "payment", label: "Payment" },
  { key: "language", label: "Language" },
  { key: "account", label: "Account" }
] as const;

export function ScoreRadar({ dimensions }: RadarProps) {
  const size = 200;
  const center = size / 2;
  const radius = size / 2 - 20;

  const getPoint = (value: number | null, angle: number) => {
    // If value is null, treat as 0 for drawing but it will be dashed
    const v = value === null ? 0 : value;
    const r = (v / 100) * radius;
    const a = angle - Math.PI / 2;
    return {
      x: center + r * Math.cos(a),
      y: center + r * Math.sin(a),
      isNull: value === null
    };
  };

  const points = useMemo(() => {
    return AXES.map((axis, i) => {
      const angle = (Math.PI * 2 * i) / AXES.length;
      const dim = dimensions.find(d => d.key === axis.key);
      const val = dim?.available ? dim.score : null;
      return getPoint(val, angle);
    });
  }, [dimensions]);

  const pathData = points.map((p, i) => `${i === 0 ? "M" : "L"} ${p.x},${p.y}`).join(" ") + " Z";

  return (
    <div className="relative w-full aspect-square flex items-center justify-center">
      <svg width="100%" height="100%" viewBox={`0 0 ${size} ${size}`} className="overflow-visible" role="img" aria-label="Score radar">
        {/* Background webs */}
        {[0.2, 0.4, 0.6, 0.8, 1].map((scale, i) => (
          <polygon
            key={i}
            points={AXES.map((_, j) => {
              const angle = (Math.PI * 2 * j) / AXES.length - Math.PI / 2;
              const r = radius * scale;
              return `${center + r * Math.cos(angle)},${center + r * Math.sin(angle)}`;
            }).join(" ")}
            fill="none"
            stroke="var(--color-night-rule)"
            strokeWidth="1"
          />
        ))}

        {/* Axes lines */}
        {AXES.map((_, i) => {
          const angle = (Math.PI * 2 * i) / AXES.length - Math.PI / 2;
          return (
            <line
              key={i}
              x1={center}
              y1={center}
              x2={center + radius * Math.cos(angle)}
              y2={center + radius * Math.sin(angle)}
              stroke="var(--color-night-rule)"
              strokeWidth="1"
            />
          );
        })}

        {/* Labels */}
        {AXES.map((axis, i) => {
          const angle = (Math.PI * 2 * i) / AXES.length - Math.PI / 2;
          const labelRadius = radius + 15;
          const x = center + labelRadius * Math.cos(angle);
          const y = center + labelRadius * Math.sin(angle);
          const dim = dimensions.find(d => d.key === axis.key);
          const val = dim?.available ? dim.score : null;
          return (
            <text
              key={i}
              x={x}
              y={y}
              fill="var(--color-fg-2)"
              fontSize="8"
              fontFamily="var(--font-sans)"
              textAnchor="middle"
              alignmentBaseline="middle"
              className="type-caption uppercase"
            >
              {axis.label} {val !== null ? `(${Math.round(val)})` : '(No Data)'}
            </text>
          );
        })}

        {/* The polygon */}
        <motion.path
          initial={{ scale: 0, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          transition={{ duration: 0.8, ease: [0.16, 1, 0.3, 1] }}
          style={{ originX: "50%", originY: "50%" }}
          d={pathData}
          fill="color-mix(in oklab, var(--color-feki) 18%, transparent)"
          stroke="var(--color-feki)"
          strokeWidth="1.5"
          strokeLinejoin="round"
        />
      </svg>
    </div>
  );
}
