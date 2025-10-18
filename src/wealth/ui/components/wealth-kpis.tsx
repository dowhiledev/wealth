"use client";
import { useEffect, useMemo, useState } from "react";
import { Card, CardHeader, CardTitle, CardDescription, CardAction } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { formatAmount } from "@/lib/utils";

type Totals = { value: string | number; cost_open: string | number; unrealized: string | number; realized: string | number };

export function WealthKPIs({ accountId }: { accountId?: number }) {
  const [totals, setTotals] = useState<Totals | null>(null);
  const [counts, setCounts] = useState<{ accounts: number; transactions: number } | null>(null);

  useEffect(() => {
    const base = process.env.NEXT_PUBLIC_API_BASE || "http://127.0.0.1:8001";
    const q = accountId ? `?account_id=${accountId}` : "";
    Promise.all([
      fetch(`${base}/portfolio/summary${q}`).then(r => r.json()),
      fetch(`${base}/stats`).then(r => r.json()),
    ]).then(([summary, stats]) => {
      setTotals(summary.totals);
      setCounts(stats);
    }).catch(() => {});
  }, [accountId]);

  const valueStr = useMemo(() => (totals ? formatAmount(totals.value) : "-"), [totals]);
  const unrealStr = useMemo(() => (totals ? formatAmount(totals.unrealized) : "-"), [totals]);
  const realizedStr = useMemo(() => (totals ? formatAmount(totals.realized) : "-"), [totals]);
  const costStr = useMemo(() => (totals ? formatAmount(totals.cost_open) : "-"), [totals]);

  return (
    <div className="*:data-[slot=card]:from-primary/5 *:data-[slot=card]:to-card dark:*:data-[slot=card]:bg-card grid grid-cols-1 gap-4 px-4 *:data-[slot=card]:bg-gradient-to-t *:data-[slot=card]:shadow-xs lg:px-6 @xl/main:grid-cols-2 @5xl/main:grid-cols-4">
      <Card className="@container/card">
        <CardHeader>
          <CardDescription>Portfolio Value</CardDescription>
          <CardTitle className="text-2xl font-semibold tabular-nums @[250px]/card:text-3xl">
            ${valueStr}
          </CardTitle>
          <CardAction>
            <Badge variant="outline">Unrealized ${unrealStr}</Badge>
          </CardAction>
        </CardHeader>
      </Card>
      <Card className="@container/card">
        <CardHeader>
          <CardDescription>Realized PnL</CardDescription>
          <CardTitle className="text-2xl font-semibold tabular-nums @[250px]/card:text-3xl">
            ${realizedStr}
          </CardTitle>
          <CardAction>
            <Badge variant="outline">Cost ${costStr}</Badge>
          </CardAction>
        </CardHeader>
      </Card>
      <Card className="@container/card">
        <CardHeader>
          <CardDescription>Accounts</CardDescription>
          <CardTitle className="text-2xl font-semibold tabular-nums @[250px]/card:text-3xl">
            {counts?.accounts ?? "-"}
          </CardTitle>
        </CardHeader>
      </Card>
      <Card className="@container/card">
        <CardHeader>
          <CardDescription>Transactions</CardDescription>
          <CardTitle className="text-2xl font-semibold tabular-nums @[250px]/card:text-3xl">
            {counts?.transactions ?? "-"}
          </CardTitle>
        </CardHeader>
      </Card>
    </div>
  );
}
