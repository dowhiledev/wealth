"use client";
import { useEffect, useState } from "react";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { formatAmount } from "@/lib/utils";

type Tx = { id: number; ts: string; account_id: number; asset_symbol: string; side: string; qty: string | number; total_quote?: string | number; quote_ccy?: string };

export function WealthLatest({ accountId }: { accountId?: number }) {
  const [rows, setRows] = useState<Tx[]>([]);
  useEffect(() => {
    const base = process.env.NEXT_PUBLIC_API_BASE || "http://127.0.0.1:8001";
    const q = new URLSearchParams({ limit: String(10) });
    if (accountId) q.set("account_id", String(accountId));
    fetch(`${base}/transactions?${q.toString()}`).then(r => r.json()).then(setRows).catch(() => {});
  }, [accountId]);
  return (
    <Card className="mx-4 lg:mx-6">
      <CardHeader>
        <CardTitle>Latest Transactions</CardTitle>
      </CardHeader>
      <CardContent>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>ID</TableHead>
              <TableHead>Time</TableHead>
              <TableHead>Acct</TableHead>
              <TableHead>Asset</TableHead>
              <TableHead>Side</TableHead>
              <TableHead>Qty</TableHead>
              <TableHead>Total</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {rows.map(t => (
              <TableRow key={t.id}>
                <TableCell>{t.id}</TableCell>
                <TableCell>{new Date(t.ts).toLocaleString()}</TableCell>
                <TableCell>{t.account_id}</TableCell>
                <TableCell>{t.asset_symbol}</TableCell>
                <TableCell>{t.side}</TableCell>
                <TableCell>{formatAmount(t.qty)}</TableCell>
                <TableCell>{t.total_quote != null ? formatAmount(t.total_quote) : ""} {t.quote_ccy ?? ""}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </CardContent>
    </Card>
  );
}
