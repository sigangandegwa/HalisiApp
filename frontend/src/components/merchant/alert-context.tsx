"use client";

import { createContext, useContext, useState, ReactNode } from "react";

interface AlertContextType {
  isOpen: boolean;
  setOpen: (v: boolean) => void;
  merchantId: string;
}

const AlertContext = createContext<AlertContextType | null>(null);

export function AlertProvider({ children, merchantId }: { children: ReactNode; merchantId: string }) {
  const [isOpen, setOpen] = useState(false);
  return (
    <AlertContext.Provider value={{ isOpen, setOpen, merchantId }}>
      {children}
    </AlertContext.Provider>
  );
}

export function useAlertDrawer() {
  const ctx = useContext(AlertContext);
  if (!ctx) throw new Error("useAlertDrawer must be used within AlertProvider");
  return ctx;
}
