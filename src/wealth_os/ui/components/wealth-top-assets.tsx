"use client";
import { useEffect, useMemo, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Bar, BarChart, CartesianGrid, XAxis, YAxis } from "recharts";
import { ChartContainer, ChartTooltip, ChartTooltipContent } from "@/components/ui/chart";
import { formatAmount } from "@/lib/utils";

type Position = { asset: string; value: number };

export function WealthTopAssets({ accountIds }: { accountIds?: number[] }) {
  const [data, setData] = useState<Position[]>([]);

  useEffect(() => {
    const base = process.env.NEXT_PUBLIC_API_BASE || "http://127.0.0.1:8001";
    const load = async () => {
      const pull = async (id?: number) => {
        const q = id ? `?account_id=${id}` : "";
        const s: { positions: Array<{ asset: string; value?: number | string }> } = await fetch(`${base}/portfolio/summary${q}`).then(r => r.json());
        return s.positions.map(p => ({ asset: p.asset, value: Number(p.value ?? 0) }));
      };
      let positions: Position[] = [];
      if (!accountIds || accountIds.length === 0) {
        positions = await pull();
      } else if (accountIds.length === 1) {
        positions = await pull(accountIds[0]);
      } else {
        const lists = await Promise.all(accountIds.map((id) => pull(id)));
        const byAsset = new Map<string, number>();
        for (const list of lists) {
          for (const p of list) byAsset.set(p.asset, (byAsset.get(p.asset) ?? 0) + p.value);
        }
        positions = Array.from(byAsset.entries()).map(([asset, value]) => ({ asset, value }));
      }
      positions.sort((a, b) => b.value - a.value);
      setData(positions.slice(0, 5));
    };
    load().catch(() => {});
  }, [accountIds]);

  const chartData = useMemo(() => data.map(d => ({ name: d.asset, value: d.value })), [data]);

  return (
    <Card>
      <CardHeader>
        <CardTitle>Top Holdings by Value</CardTitle>
      </CardHeader>
      <CardContent>
        <ChartContainer config={{}} className="aspect-auto h-[280px] w-full">
          <BarChart data={chartData} layout="vertical">
            <CartesianGrid horizontal vertical={false} />
            <XAxis type="number" tickFormatter={(v) => formatAmount(v as number)} />
            <YAxis type="category" dataKey="name" width={60} />
            <ChartTooltip cursor={false} content={<ChartTooltipContent />} />
            <Bar dataKey="value" fill="var(--chart-2)" radius={[0, 0, 0, 0]} />
          </BarChart>
        </ChartContainer>
      </CardContent>
    </Card>
  );
}
