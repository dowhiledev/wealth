"use client";
import { useEffect, useMemo, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Bar, BarChart, CartesianGrid, Legend, XAxis, YAxis } from "recharts";
import { ChartContainer, ChartTooltip, ChartTooltipContent } from "@/components/ui/chart";
import { api, type Tx } from "@/lib/api";
import { formatAmount } from "@/lib/utils";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";

type Row = { date: string; buy: number; sell: number };

export function WealthVolume({ accountIds }: { accountIds?: number[] }) {
  const [rows, setRows] = useState<Row[]>([]);
  const [asset, setAsset] = useState<string>("all");
  const [assetOptions, setAssetOptions] = useState<string[]>([]);
  const [days, setDays] = useState<number>(60);

  useEffect(() => {
    const load = async () => {
      let txs: Tx[] = [];
      if (!accountIds || accountIds.length === 0) {
        txs = await api.tx.list({ limit: 5000 });
      } else if (accountIds.length === 1) {
        txs = await api.tx.list({ account_id: accountIds[0], limit: 5000 });
      } else {
        const lists = await Promise.all(accountIds.map((id) => api.tx.list({ account_id: id, limit: 5000 })));
        txs = lists.flat();
      }
      // assets list
      const assets = Array.from(new Set(txs.map(t => String(t.asset_symbol).toUpperCase()))).sort();
      setAssetOptions(["all", ...assets]);
      const lastNDays = days;
      const cutoff = new Date();
      cutoff.setDate(cutoff.getDate() - lastNDays);
      const daily: Record<string, { buy: number; sell: number }> = {};
      for (const t of txs) {
        const d = new Date(t.ts);
        if (d < cutoff) continue;
        const sym = String(t.asset_symbol).toUpperCase();
        if (asset !== "all" && sym !== asset.toUpperCase()) continue;
        const key = d.toISOString().slice(0, 10);
        const total = Number(t.total_quote ?? 0) || (t.price_quote != null ? Number(t.price_quote) * Number(t.qty) : 0);
        const bucket = daily[key] ?? { buy: 0, sell: 0 };
        if (t.side === "buy") bucket.buy += Math.abs(total);
        else if (t.side === "sell") bucket.sell += Math.abs(total);
        daily[key] = bucket;
      }
      const ds: Row[] = Object.entries(daily)
        .map(([date, v]) => ({ date, buy: v.buy, sell: v.sell }))
        .sort((a, b) => new Date(a.date).getTime() - new Date(b.date).getTime());
      setRows(ds);
    };
    load().catch(() => {});
  }, [accountIds, asset, days]);

  const data = useMemo(() => rows, [rows]);

  return (
    <Card>
      <CardHeader>
        <CardTitle>Trade Volume (Buy vs Sell)</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="flex items-center justify-end gap-2 pb-2">
          <Select value={String(days)} onValueChange={(v: string) => setDays(Number(v))}>
            <SelectTrigger className="w-28" size="sm"><SelectValue placeholder="60 days" /></SelectTrigger>
            <SelectContent>
              <SelectItem value="30">30 days</SelectItem>
              <SelectItem value="60">60 days</SelectItem>
              <SelectItem value="90">90 days</SelectItem>
            </SelectContent>
          </Select>
          <Select value={asset} onValueChange={(v: string) => setAsset(v)}>
            <SelectTrigger className="w-40" size="sm"><SelectValue placeholder="All assets" /></SelectTrigger>
            <SelectContent>
              {assetOptions.map(a => (
                <SelectItem key={a} value={a}>{a === 'all' ? 'All assets' : a}</SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
        <ChartContainer config={{}} className="aspect-auto h-[280px] w-full">
          <BarChart data={data}>
            <CartesianGrid vertical={false} />
            <XAxis dataKey="date" minTickGap={32} tickFormatter={(v) => new Date(v as string).toLocaleDateString(undefined, { month: "short", day: "numeric" })} />
            <YAxis tickFormatter={(v) => formatAmount(v as number)} />
            <ChartTooltip cursor={false} content={<ChartTooltipContent />} />
            <Legend />
            <Bar dataKey="buy" stackId="v" fill="var(--chart-4)" radius={[0, 0, 0, 0]} />
            <Bar dataKey="sell" stackId="v" fill="var(--chart-3)" radius={[0, 0, 0, 0]} />
          </BarChart>
        </ChartContainer>
      </CardContent>
    </Card>
  );
}
