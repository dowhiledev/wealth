"use client";
import * as React from "react";
import { useEffect, useMemo, useState } from "react";
import { Area, AreaChart, CartesianGrid, XAxis, YAxis } from "recharts";

import { Card, CardAction, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { ChartConfig, ChartContainer, ChartTooltip, ChartTooltipContent } from "@/components/ui/chart";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { ToggleGroup, ToggleGroupItem } from "@/components/ui/toggle-group";
import { formatAmount } from "@/lib/utils";

type SeriesPoint = { date: string; value: number };

const chartConfig = {
  value: {
    label: "Value",
    color: "var(--primary)",
  },
} satisfies ChartConfig;

export function WealthPnL({ accountIds }: { accountIds?: number[] }) {
  const [timeRange, setTimeRange] = useState<"90d" | "30d" | "7d">("90d");
  const [series, setSeries] = useState<SeriesPoint[]>([]);

  useEffect(() => {
    const base = process.env.NEXT_PUBLIC_API_BASE || "http://127.0.0.1:8001";
    const load = async () => {
      const q = new URLSearchParams();
      const now = new Date();
      const days = 90; // fetch last 90 days, we trim by UI range
      const since = new Date(now);
      since.setDate(since.getDate() - days);
      q.set("since", since.toISOString());
      q.set("until", now.toISOString());
      if (accountIds && accountIds.length === 1) q.set("account_id", String(accountIds[0]));
      const res = await fetch(`${base}/portfolio/value_series?${q.toString()}`);
      const rows = (await res.json()) as Array<{ date: string; value: number }>;
      const s: SeriesPoint[] = rows.map((r) => ({ date: r.date, value: Number(r.value) }));
      setSeries(s);
    };
    load().catch(() => {});
  }, [accountIds]);

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
          <CardTitle>Portfolio Value Over Time</CardTitle>
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
        </CardAction>
      </CardHeader>
      <CardContent className="px-2 pt-4 sm:px-6 sm:pt-6">
        <ChartContainer config={chartConfig} className="aspect-auto h-[250px] w-full">
          <AreaChart data={filtered}>
            <defs>
              <linearGradient id="fillValue" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="var(--color-value)" stopOpacity={0.8} />
                <stop offset="95%" stopColor="var(--color-value)" stopOpacity={0.1} />
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
                      <span className="text-muted-foreground">Value</span>
                      <span className="text-foreground font-mono font-medium tabular-nums">{formatAmount(value as number)}</span>
                    </div>
                  )}
                  indicator="dot"
                  hideLabel
                />
              }
            />
            <Area dataKey="value" type="natural" fill="url(#fillValue)" stroke="var(--color-value)" />
          </AreaChart>
        </ChartContainer>
      </CardContent>
    </Card>
  );
}
