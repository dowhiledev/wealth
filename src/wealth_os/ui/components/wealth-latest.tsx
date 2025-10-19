"use client";
import { useEffect, useState } from "react";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { TransactionsTable } from "@/components/transactions-table";
import type { Tx } from "@/lib/api";

export function WealthLatest({ accountIds }: { accountIds?: number[] }) {
  const [rows, setRows] = useState<Tx[]>([]);
  useEffect(() => {
    const base = process.env.NEXT_PUBLIC_API_BASE || "http://127.0.0.1:8001";
    const load = async () => {
      if (!accountIds || accountIds.length === 0) {
        const q = new URLSearchParams({ limit: String(10) });
        const res: Tx[] = await fetch(`${base}/transactions?${q.toString()}`).then(r => r.json());
        setRows(res);
        return;
      }
      const lists = await Promise.all(
        accountIds.map((id) => fetch(`${base}/transactions?${new URLSearchParams({ account_id: String(id), limit: String(10) }).toString()}`).then(r => r.json() as Promise<Tx[]>))
      );
      const merged: Tx[] = (lists as Tx[][]).flat();
      merged.sort((a, b) => new Date(b.ts).getTime() - new Date(a.ts).getTime());
      setRows(merged.slice(0, 10));
    };
    load().catch(() => {});
  }, [accountIds]);
  const reload = () => {
    // trigger refetch
    const base = process.env.NEXT_PUBLIC_API_BASE || "http://127.0.0.1:8001";
    const run = async () => {
      if (!accountIds || accountIds.length === 0) {
        const q = new URLSearchParams({ limit: String(10) });
        const res: Tx[] = await fetch(`${base}/transactions?${q.toString()}`).then(r => r.json());
        setRows(res);
        return;
      }
      const lists = await Promise.all(
        accountIds.map((id) => fetch(`${base}/transactions?${new URLSearchParams({ account_id: String(id), limit: String(10) }).toString()}`).then(r => r.json() as Promise<Tx[]>))
      );
      const merged: Tx[] = (lists as Tx[][]).flat();
      merged.sort((a, b) => new Date(b.ts).getTime() - new Date(a.ts).getTime());
      setRows(merged.slice(0, 10));
    };
    run().catch(() => {});
  };
  return (
    <Card>
      <CardHeader>
        <CardTitle>Recent Activity</CardTitle>
      </CardHeader>
      <CardContent>
        <TransactionsTable rows={rows} onChanged={reload} />
      </CardContent>
    </Card>
  );
}
