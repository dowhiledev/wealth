"use client";
import React, { createContext, useContext, useEffect, useState } from "react";
import { api, type Account } from "@/lib/api";

type DashboardState = {
  accounts: Account[];
  selected: number[];
  setSelected: (v: number[]) => void;
  reloadKey: number;
  triggerReload: () => void;
};

const Ctx = createContext<DashboardState | null>(null);

export function DashboardProvider({ children }: { children: React.ReactNode }) {
  const [accounts, setAccounts] = useState<Account[]>([]);
  const [selected, setSelected] = useState<number[]>([]);
  const [reloadKey, setReloadKey] = useState(0);

  useEffect(() => {
    api.accounts.list().then(setAccounts).catch(() => {});
  }, []);

  const value: DashboardState = {
    accounts,
    selected,
    setSelected,
    reloadKey,
    triggerReload: () => setReloadKey((k) => k + 1),
  };

  return <Ctx.Provider value={value}>{children}</Ctx.Provider>;
}

export function useDashboard() {
  const ctx = useContext(Ctx);
  if (!ctx) throw new Error("useDashboard must be used within DashboardProvider");
  return ctx;
}

