"use client";

import { motion } from "motion/react";
import { Bell } from "lucide-react";
import { useAlerts } from "./use-alerts";
import { useEffect, useState } from "react";

import { useAlertDrawer } from "./alert-context";

export function AlertBell() {
  const { merchantId, setOpen } = useAlertDrawer();
  const { unreadCount } = useAlerts(merchantId);
  const [pulse, setPulse] = useState(false);
  const [prev, setPrev] = useState(unreadCount);

  useEffect(() => {
    if (unreadCount > prev) {
      setPulse(true);
      setTimeout(() => setPulse(false), 420);
    }
    setPrev(unreadCount);
  }, [unreadCount, prev]);

  return (
    <button 
      onClick={() => setOpen(true)}
      className="relative p-2 rounded-full hover:bg-bg-2 transition-colors focus-visible outline-none"
      aria-label="Alerts"
    >
      <Bell className="w-5 h-5 text-fg-2" />
      {unreadCount > 0 && (
        <motion.div
          animate={pulse ? { scale: [1, 1.15, 1] } : { scale: 1 }}
          transition={{ ease: [0.34, 1.56, 0.64, 1], duration: 0.42 }}
          className="absolute top-1.5 right-1.5 w-4 h-4 bg-[var(--color-feki)] rounded-full flex items-center justify-center text-[10px] type-data font-bold text-white border-2 border-bg"
        >
          {unreadCount}
        </motion.div>
      )}
    </button>
  );
}
