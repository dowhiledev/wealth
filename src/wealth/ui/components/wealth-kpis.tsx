"use client";
import { useEffect, useMemo, useState } from "react";
import { Card, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { formatAmount } from "@/lib/utils";

type Totals = { value: string | number; cost_open: string | number; unrealized: string | number; realized: string | number };

export function WealthKPIs({ accountIds, showAccountsKPI = true }: { accountIds?: number[]; showAccountsKPI?: boolean }) {
  const [totals, setTotals] = useState<Totals | null>(null);
  const [counts, setCounts] = useState<{ accounts: number; transactions: number } | null>(null);

  useEffect(() => {
    const base = process.env.NEXT_PUBLIC_API_BASE || "http://127.0.0.1:8001";
    const load = async () => {
      if (!accountIds || accountIds.length === 0) {
        const [summary, stats] = await Promise.all([
          fetch(`${base}/portfolio/summary`).then(r => r.json()),
          fetch(`${base}/stats`).then(r => r.json()),
        ]);
        setTotals(summary.totals);
        setCounts(stats);
        return;
      }
      if (accountIds.length === 1) {
        const [summary, stats] = await Promise.all([
          fetch(`${base}/portfolio/summary?account_id=${accountIds[0]}`).then(r => r.json()),
          fetch(`${base}/stats?account_id=${accountIds[0]}`).then(r => r.json()),
        ]);
        setTotals(summary.totals);
        setCounts(stats);
        return;
      }
      const summaries = await Promise.all(
        accountIds.map((id) => fetch(`${base}/portfolio/summary?account_id=${id}`).then(r => r.json()))
      );
      const agg = summaries.reduce(
        (acc, s) => {
          acc.value += Number(s.totals?.value ?? 0);
          acc.cost_open += Number(s.totals?.cost_open ?? 0);
          acc.unrealized += Number(s.totals?.unrealized ?? 0);
          acc.realized += Number(s.totals?.realized ?? 0);
          return acc;
        },
        { value: 0, cost_open: 0, unrealized: 0, realized: 0 }
      );
      setTotals(agg as Totals);
      const stats = await fetch(`${base}/stats`).then(r => r.json()).catch(() => null);
      if (stats) setCounts(stats);
    };
    load().catch(() => {});
  }, [accountIds]);

  const valueStr = useMemo(() => (totals ? formatAmount(totals.value) : "-"), [totals]);
  const unrealStr = useMemo(() => (totals ? formatAmount(totals.unrealized) : "-"), [totals]);
  const realizedStr = useMemo(() => (totals ? formatAmount(totals.realized) : "-"), [totals]);
  const costStr = useMemo(() => (totals ? formatAmount(totals.cost_open) : "-"), [totals]);

  return (
    <div className="*:data-[slot=card]:from-primary/5 *:data-[slot=card]:to-card dark:*:data-[slot=card]:bg-card grid grid-cols-1 gap-4 *:data-[slot=card]:bg-gradient-to-t *:data-[slot=card]:shadow-xs md:grid-cols-2 xl:grid-cols-4">
      <Card className="min-w-0 @container/card">
        <CardHeader>
          <CardDescription>Portfolio Value</CardDescription>
          <CardTitle className="text-2xl font-semibold tabular-nums break-words leading-tight @[250px]/card:text-3xl">
            ${valueStr}
          </CardTitle>
          <div className="mt-1">
            <Badge variant="outline" className="whitespace-normal break-words text-xs px-2 py-0.5">Unrealized ${unrealStr}</Badge>
          </div>
        </CardHeader>
      </Card>
      <Card className="min-w-0 @container/card">
        <CardHeader>
          <CardDescription>Realized PnL</CardDescription>
          <CardTitle className="text-2xl font-semibold tabular-nums break-words leading-tight @[250px]/card:text-3xl">
            ${realizedStr}
          </CardTitle>
          <div className="mt-1">
            <Badge variant="outline" className="whitespace-normal break-words text-xs px-2 py-0.5">Cost ${costStr}</Badge>
          </div>
        </CardHeader>
      </Card>
      {showAccountsKPI && (
        <Card className="min-w-0 @container/card">
          <CardHeader>
            <CardDescription>Accounts</CardDescription>
            <CardTitle className="text-2xl font-semibold tabular-nums leading-tight @[250px]/card:text-3xl">
              {counts?.accounts ?? "-"}
            </CardTitle>
          </CardHeader>
        </Card>
      )}
      <Card className="min-w-0 @container/card">
        <CardHeader>
          <CardDescription>Transactions</CardDescription>
          <CardTitle className="text-2xl font-semibold tabular-nums leading-tight @[250px]/card:text-3xl">
            {counts?.transactions ?? "-"}
          </CardTitle>
        </CardHeader>
      </Card>
    </div>
  );
}
