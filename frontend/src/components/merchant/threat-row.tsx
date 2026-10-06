"use client";

import Link from "next/link";
import { timeAgo } from "@/lib/format";
import type { ThreatSummary } from "@/lib/schemas";
import { motion } from "motion/react";
import { HandleDiff } from "./handle-diff";

interface ThreatRowProps {
  threat: ThreatSummary;
  merchantHandles: string[];
}

export function ThreatRow({ threat, merchantHandles }: ThreatRowProps) {
  const isHighRisk = threat.composite_score >= 70;
  
  return (
    <motion.div
      initial={{ opacity: 0, y: -20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.8, ease: [0.16, 1, 0.3, 1] }}
    >
      <Link 
        href={`/dashboard/threat/${threat.id}`}
        className="desk-panel group flex items-center p-4 gap-4 transition-colors hover:bg-bg-3 relative overflow-hidden"
      >
        <div className={`absolute left-0 top-0 bottom-0 w-1 ${isHighRisk ? 'bg-[var(--color-feki)]' : 'bg-[var(--color-caution)]'}`} />
        
        <div className="w-12 h-12 rounded-full overflow-hidden bg-bg-2 border border-line flex-shrink-0">
           {threat.avatar_url ? (
             <img src={threat.avatar_url} alt="" className="w-full h-full object-cover" />
           ) : (
             <div className="w-full h-full bg-line-strong" />
           )}
        </div>

        <div className="flex-1 min-w-0">
          <HandleDiff 
            target={threat.target_handle} 
            officials={merchantHandles}
          />
          <p className="type-caption text-fg-2 mt-1 truncate">{threat.top_reason?.text}</p>
        </div>

        <div className="text-right whitespace-nowrap">
          <div className={`type-data text-lg ${isHighRisk ? 'text-[var(--color-feki)]' : 'text-[var(--color-caution)]'}`}>
            {threat.composite_score}%
          </div>
          <p className="text-xs text-fg-3 mt-1">{timeAgo(threat.first_seen_at)}</p>
        </div>
        
        <div className="ml-4 pl-4 border-l border-line flex flex-col justify-center min-w-[100px]">
          <span className="type-caption text-fg-2">{threat.status.replace("_", " ")}</span>
        </div>
      </Link>
    </motion.div>
  );
}
