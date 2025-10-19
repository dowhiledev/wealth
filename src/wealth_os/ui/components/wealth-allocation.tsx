"use client";
import { useEffect, useState } from "react";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { PieChart, Pie, Cell, Legend, Tooltip, ResponsiveContainer } from "recharts";
import { formatAmount } from "@/lib/utils";

type Position = { asset: string; value?: number; qty: number };

const PALETTE = ["var(--chart-1)", "var(--chart-2)", "var(--chart-3)", "var(--chart-4)", "var(--chart-5)"];

export function WealthAllocation({ accountIds }: { accountIds?: number[] }) {
  const [data, setData] = useState<Position[]>([]);

  useEffect(() => {
    const base = process.env.NEXT_PUBLIC_API_BASE || "http://127.0.0.1:8001";
    const load = async () => {
      if (!accountIds || accountIds.length === 0) {
        const s: { positions: Array<{ asset: string; value?: number | string; qty: number | string }> } = await fetch(`${base}/portfolio/summary`).then(r => r.json());
        const ds = s.positions
          .map(p => ({ asset: p.asset, value: Number(p.value ?? 0), qty: Number(p.qty) }))
          .filter(p => (p.value ?? 0) > 0);
        setData(ds);
        return;
      }
      if (accountIds.length === 1) {
        const s: { positions: Array<{ asset: string; value?: number | string; qty: number | string }> } = await fetch(`${base}/portfolio/summary?account_id=${accountIds[0]}`).then(r => r.json());
        const ds = s.positions
          .map(p => ({ asset: p.asset, value: Number(p.value ?? 0), qty: Number(p.qty) }))
          .filter(p => (p.value ?? 0) > 0);
        setData(ds);
        return;
      }
      const summaries = await Promise.all(
        accountIds.map((id) => fetch(`${base}/portfolio/summary?account_id=${id}`).then(r => r.json() as Promise<{ positions: Array<{ asset: string; value?: number | string; qty: number | string }> }>))
      );
      const byAsset = new Map<string, { asset: string; value: number; qty: number }>();
      for (const s of summaries) {
        for (const p of s.positions) {
          const a = String(p.asset);
          const v = Number(p.value ?? 0);
          const q = Number(p.qty ?? 0);
          const cur = byAsset.get(a) || { asset: a, value: 0, qty: 0 };
          cur.value += v;
          cur.qty += q;
          byAsset.set(a, cur);
        }
      }
      const ds = Array.from(byAsset.values()).filter(p => (p.value ?? 0) > 0);
      setData(ds);
    };
    load().catch(() => {});
  }, [accountIds]);

  return (
    <Card>
      <CardHeader>
        <CardTitle>Portfolio Allocation</CardTitle>
      </CardHeader>
      <CardContent className="h-[320px]">
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Pie data={data} dataKey="value" nameKey="asset" outerRadius={120} innerRadius={60} stroke="var(--border)">
              {data.map((_, idx) => (
                <Cell key={idx} fill={PALETTE[idx % PALETTE.length]} />
              ))}
            </Pie>
            <Tooltip formatter={(v) => formatAmount(v as number)} />
            <Legend />
          </PieChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
}
