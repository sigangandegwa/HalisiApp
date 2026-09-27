"use client";

import { createContext, useContext, useState, ReactNode } from "react";

interface AlertContextType {
  isOpen: boolean;
  setOpen: (v: boolean) => void;
  merchantId: string;
  /** The logged-in merchant's slug, for the one public endpoint that's keyed by slug (GET /merchants/{slug}). */
  merchantSlug: string;
}

const AlertContext = createContext<AlertContextType | null>(null);

export function AlertProvider({
  children,
  merchantId,
  merchantSlug,
}: {
  children: ReactNode;
  merchantId: string;
  merchantSlug: string;
}) {
  const [isOpen, setOpen] = useState(false);
  return (
    <AlertContext.Provider value={{ isOpen, setOpen, merchantId, merchantSlug }}>
      {children}
    </AlertContext.Provider>
  );
}

export function useAlertDrawer() {
  const ctx = useContext(AlertContext);
  if (!ctx) throw new Error("useAlertDrawer must be used within AlertProvider");
  return ctx;
}
