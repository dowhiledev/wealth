"use client";
import * as React from "react";
import { useEffect, useMemo, useState } from "react";
import { Area, AreaChart, CartesianGrid, XAxis, YAxis } from "recharts";

import { Card, CardAction, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { ChartConfig, ChartContainer, ChartTooltip, ChartTooltipContent } from "@/components/ui/chart";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { ToggleGroup, ToggleGroupItem } from "@/components/ui/toggle-group";
import { api, type Tx } from "@/lib/api";
import { formatAmount } from "@/lib/utils";

type SeriesPoint = { date: string; pnl: number };

const chartConfig = {
  pnl: {
    label: "Realized PnL",
    color: "var(--primary)",
  },
} satisfies ChartConfig;

export function WealthPnL({ accountIds }: { accountIds?: number[] }) {
  const [timeRange, setTimeRange] = useState<"90d" | "30d" | "7d">("90d");
  const [series, setSeries] = useState<SeriesPoint[]>([]);
  const [asset, setAsset] = useState<string>("all");
  const [assetOptions, setAssetOptions] = useState<string[]>([]);

  useEffect(() => {
    const load = async () => {
      // Load up to 5000 latest txs to compute FIFO realized PnL
      let txs: Tx[] = [];
      if (!accountIds || accountIds.length === 0) {
        txs = await api.tx.list({ limit: 5000 });
      } else if (accountIds.length === 1) {
        txs = await api.tx.list({ account_id: accountIds[0], limit: 5000 });
      } else {
        const lists = await Promise.all(accountIds.map((id) => api.tx.list({ account_id: id, limit: 5000 })));
        txs = lists.flat();
      }
      // set asset options
      const assets = Array.from(new Set(txs.map(t => String(t.asset_symbol).toUpperCase()))).sort();
      setAssetOptions(["all", ...assets]);
      txs.sort((a, b) => new Date(a.ts).getTime() - new Date(b.ts).getTime());
      // FIFO per asset: lots as [qty_remaining, cost_per_unit]
      const lots: Record<string, Array<[number, number]>> = {};
      const daily: Record<string, number> = {};
      for (const t of txs) {
        const sym = (t.asset_symbol || "").toUpperCase();
        if (asset !== "all" && sym !== asset.toUpperCase()) continue;
        const qty = Number(t.qty || 0);
        const price = t.price_quote != null ? Number(t.price_quote) : undefined;
        const total = t.total_quote != null ? Number(t.total_quote) : undefined;
        const dateKey = new Date(t.ts).toISOString().slice(0, 10);
        if (t.side === "buy") {
          const totalCost = total ?? (price != null ? price * qty : 0);
          const cpu = qty !== 0 ? totalCost / qty : 0;
          if (!lots[sym]) lots[sym] = [];
          lots[sym].push([qty, cpu]);
        } else if (t.side === "sell") {
          let remaining = qty;
          let costAccum = 0;
          const proceeds = total ?? (price != null ? price * qty : 0);
          const symLots = lots[sym] || (lots[sym] = []);
          while (remaining > 0 && symLots.length > 0) {
            const [lqty, cpu] = symLots[0];
            const take = Math.min(lqty, remaining);
            costAccum += take * cpu;
            const leftover = lqty - take;
            remaining -= take;
            if (leftover <= 0) symLots.shift();
            else symLots[0] = [leftover, cpu];
          }
          const realized = proceeds - costAccum;
          daily[dateKey] = (daily[dateKey] ?? 0) + realized;
        }
      }
      const dates = Object.keys(daily).sort();
      let accum = 0;
      const s: SeriesPoint[] = dates.map((d) => {
        accum += daily[d];
        return { date: d, pnl: Number(accum.toFixed(8)) };
      });
      setSeries(s);
    };
    load().catch(() => {});
  }, [accountIds, asset]);

  const filtered = useMemo(() => {
    if (series.length === 0) return series;
    const end = new Date(series[series.length - 1]?.date ?? new Date());
    const days = timeRange === "90d" ? 90 : timeRange === "30d" ? 30 : 7;
    const start = new Date(end);
    start.setDate(start.getDate() - days);
    return series.filter((p) => new Date(p.date) >= start);
  }, [series, timeRange]);

  return (
    <Card className="@container/card">
        <CardHeader>
          <CardTitle>Realized P&L</CardTitle>
          <CardDescription>
          <span className="hidden @[540px]/card:block">Cumulative, last {timeRange.replace("d", " days")}</span>
          <span className="@[540px]/card:hidden">Cumulative</span>
        </CardDescription>
        <CardAction>
          <ToggleGroup
            type="single"
            value={timeRange}
            onValueChange={(v) => {
              if (v === "90d" || v === "30d" || v === "7d" || v === "") {
                if (v) setTimeRange(v);
              }
            }}
            variant="outline"
            className="hidden *:data-[slot=toggle-group-item]:!px-4 @[767px]/card:flex"
          >
            <ToggleGroupItem value="90d">Last 3 months</ToggleGroupItem>
            <ToggleGroupItem value="30d">Last 30 days</ToggleGroupItem>
            <ToggleGroupItem value="7d">Last 7 days</ToggleGroupItem>
          </ToggleGroup>
          <Select value={timeRange} onValueChange={(v: "90d" | "30d" | "7d") => setTimeRange(v)}>
            <SelectTrigger className="flex w-40 **:data-[slot=select-value]:block **:data-[slot=select-value]:truncate @[767px]/card:hidden" size="sm" aria-label="Select a value">
              <SelectValue placeholder="Last 3 months" />
            </SelectTrigger>
            <SelectContent className="rounded-xl">
              <SelectItem value="90d" className="rounded-lg">Last 3 months</SelectItem>
              <SelectItem value="30d" className="rounded-lg">Last 30 days</SelectItem>
              <SelectItem value="7d" className="rounded-lg">Last 7 days</SelectItem>
            </SelectContent>
          </Select>
          <Select value={asset} onValueChange={(v: string) => setAsset(v)}>
            <SelectTrigger className="w-40" size="sm" aria-label="Select asset">
              <SelectValue placeholder="All assets" />
            </SelectTrigger>
            <SelectContent className="rounded-xl">
              {assetOptions.map(a => (
                <SelectItem key={a} value={a}>{a === 'all' ? 'All assets' : a}</SelectItem>
              ))}
            </SelectContent>
          </Select>
        </CardAction>
      </CardHeader>
      <CardContent className="px-2 pt-4 sm:px-6 sm:pt-6">
        <ChartContainer config={chartConfig} className="aspect-auto h-[250px] w-full">
          <AreaChart data={filtered}>
            <defs>
              <linearGradient id="fillPnL" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="var(--color-pnl)" stopOpacity={0.8} />
                <stop offset="95%" stopColor="var(--color-pnl)" stopOpacity={0.1} />
              </linearGradient>
            </defs>
            <CartesianGrid vertical={false} />
            <XAxis
              dataKey="date"
              tickLine={false}
              axisLine={false}
              tickMargin={8}
              minTickGap={32}
              tickFormatter={(value) => {
                const date = new Date(value as string);
                return date.toLocaleDateString(undefined, { month: "short", day: "numeric" });
              }}
            />
            <YAxis
              tickLine={false}
              axisLine={false}
              tickMargin={8}
              tickFormatter={(v) => formatAmount(v as number)}
            />
            <ChartTooltip
              cursor={false}
              content={
                <ChartTooltipContent
                  labelFormatter={(value) => new Date(value as string).toLocaleDateString(undefined, { month: "short", day: "numeric" })}
                  formatter={(value) => (
                    <div className="flex w-full items-center justify-between gap-2">
                      <span className="text-muted-foreground">Realized PnL</span>
                      <span className="text-foreground font-mono font-medium tabular-nums">{formatAmount(value as number)}</span>
                    </div>
                  )}
                  indicator="dot"
                  hideLabel
                />
              }
            />
            <Area dataKey="pnl" type="natural" fill="url(#fillPnL)" stroke="var(--color-pnl)" />
          </AreaChart>
        </ChartContainer>
      </CardContent>
    </Card>
  );
}
