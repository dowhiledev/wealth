"use client";
import { useEffect, useState } from "react";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { PieChart, Pie, Cell, Legend, Tooltip, ResponsiveContainer } from "recharts";

type Position = { asset: string; value?: number; qty: number };

const PALETTE = ["var(--chart-1)", "var(--chart-2)", "var(--chart-3)", "var(--chart-4)", "var(--chart-5)"];

export function WealthAllocation() {
  const [data, setData] = useState<Position[]>([]);

  useEffect(() => {
    const base = process.env.NEXT_PUBLIC_API_BASE || "http://127.0.0.1:8001";
    fetch(`${base}/portfolio/summary`).then(r => r.json()).then((s) => {
      const ds = (s.positions as any[]).map(p => ({ asset: p.asset, value: Number(p.value ?? 0), qty: Number(p.qty) }))
        .filter(p => p.value > 0);
      setData(ds);
    }).catch(() => {});
  }, []);

  return (
    <Card className="mx-4 lg:mx-6">
      <CardHeader>
        <CardTitle>Allocation</CardTitle>
      </CardHeader>
      <CardContent className="h-[320px]">
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Pie data={data} dataKey="value" nameKey="asset" outerRadius={120} innerRadius={60} stroke="var(--border)">
              {data.map((_, idx) => (
                <Cell key={idx} fill={PALETTE[idx % PALETTE.length]} />
              ))}
            </Pie>
            <Tooltip />
            <Legend />
          </PieChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
}

