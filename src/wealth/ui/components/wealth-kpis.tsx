"use client";
import { useEffect, useState } from "react";
import { Card, CardHeader, CardTitle, CardDescription, CardFooter, CardAction } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

type Totals = { value: string | number; cost_open: string | number; unrealized: string | number; realized: string | number };

export function WealthKPIs() {
  const [totals, setTotals] = useState<Totals | null>(null);
  const [counts, setCounts] = useState<{ accounts: number; transactions: number } | null>(null);

  useEffect(() => {
    const base = process.env.NEXT_PUBLIC_API_BASE || "http://127.0.0.1:8001";
    Promise.all([
      fetch(`${base}/portfolio/summary`).then(r => r.json()),
      fetch(`${base}/stats`).then(r => r.json()),
    ]).then(([summary, stats]) => {
      setTotals(summary.totals);
      setCounts(stats);
    }).catch(() => {});
  }, []);

  const V = (x?: any) => (x != null ? new Intl.NumberFormat(undefined, { maximumFractionDigits: 2 }).format(Number(x)) : "-");

  return (
    <div className="*:data-[slot=card]:from-primary/5 *:data-[slot=card]:to-card dark:*:data-[slot=card]:bg-card grid grid-cols-1 gap-4 px-4 *:data-[slot=card]:bg-gradient-to-t *:data-[slot=card]:shadow-xs lg:px-6 @xl/main:grid-cols-2 @5xl/main:grid-cols-4">
      <Card className="@container/card">
        <CardHeader>
          <CardDescription>Portfolio Value</CardDescription>
          <CardTitle className="text-2xl font-semibold tabular-nums @[250px]/card:text-3xl">
            ${V(totals?.value)}
          </CardTitle>
          <CardAction>
            <Badge variant="outline">Unrealized ${V(totals?.unrealized)}</Badge>
          </CardAction>
        </CardHeader>
      </Card>
      <Card className="@container/card">
        <CardHeader>
          <CardDescription>Realized PnL</CardDescription>
          <CardTitle className="text-2xl font-semibold tabular-nums @[250px]/card:text-3xl">
            ${V(totals?.realized)}
          </CardTitle>
          <CardAction>
            <Badge variant="outline">Cost ${V(totals?.cost_open)}</Badge>
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

