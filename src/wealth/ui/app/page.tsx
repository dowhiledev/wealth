"use client";
import { useEffect, useState } from "react";
import { WealthKPIs } from "@/components/wealth-kpis";
import { WealthAllocation } from "@/components/wealth-allocation";
import { WealthLatest } from "@/components/wealth-latest";
import { WealthPnL } from "@/components/wealth-pnl";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { api, type Account } from "@/lib/api";

export default function Home() {
  const [accounts, setAccounts] = useState<Account[]>([]);
  const [accountId, setAccountId] = useState<number | undefined>(undefined);

  useEffect(() => {
    api.accounts.list().then(setAccounts).catch(() => {});
  }, []);

  return (
    <div className="flex flex-1 flex-col gap-4 py-4 md:gap-6 md:py-6">
      <div className="flex items-center justify-between px-4 lg:px-6">
        <h1 className="text-xl font-semibold">Wealth Dashboard</h1>
        <div className="min-w-56">
          <Select value={accountId ? String(accountId) : "all"} onValueChange={(v) => setAccountId(v === "all" ? undefined : Number(v))}>
            <SelectTrigger aria-label="Account Filter">
              <SelectValue placeholder="All Accounts" />
            </SelectTrigger>
            <SelectContent className="rounded-xl">
              <SelectItem value="all">All Accounts</SelectItem>
              {accounts.map((a) => (
                <SelectItem key={a.id} value={String(a.id)}>{a.name}</SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      </div>

      <WealthKPIs accountId={accountId} />

      <div className="grid grid-cols-1 gap-4 px-4 lg:grid-cols-2 lg:px-6">
        <WealthAllocation accountId={accountId} />
        <WealthPnL accountId={accountId} />
      </div>

      <WealthLatest accountId={accountId} />
    </div>
  );
}
