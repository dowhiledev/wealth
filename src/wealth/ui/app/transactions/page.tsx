"use client";

import { useEffect, useState } from "react";
import { api, type Tx, type TxIn, type Account } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { toast } from "sonner";

export default function TransactionsPage() {
  const [accounts, setAccounts] = useState<Account[]>([]);
  const [txs, setTxs] = useState<Tx[]>([]);
  const [loading, setLoading] = useState(false);
  const [form, setForm] = useState<TxIn>({
    ts: new Date().toISOString(),
    account_id: 0,
    asset_symbol: "BTC",
    side: "buy",
    qty: "0.1",
    price_quote: "",
    total_quote: "",
    quote_ccy: "USD",
  } as any);

  const load = async () => {
    setLoading(true);
    try {
      const [accts, rows] = await Promise.all([api.accounts.list(), api.tx.list({ limit: 100 })]);
      setAccounts(accts);
      setTxs(rows);
      if (form.account_id === 0 && accts.length > 0) setForm({ ...form, account_id: accts[0].id });
    } catch (e: any) {
      toast.error(e.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const onCreate = async () => {
    if (!form.account_id) { toast.error("Select account"); return; }
    try {
      const body = { ...form, qty: String(form.qty || "0") } as TxIn;
      await api.tx.create(body);
      await load();
      toast.success("Transaction created");
    } catch (e: any) {
      toast.error(e.message);
    }
  };

  const onDelete = async (id: number) => {
    if (!confirm("Delete this transaction?")) return;
    try {
      await api.tx.remove(id);
      await load();
      toast.success("Transaction deleted");
    } catch (e: any) {
      toast.error(e.message);
    }
  };

  return (
    <div className="p-6 space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Add Transaction</CardTitle>
        </CardHeader>
        <CardContent className="grid gap-4 md:grid-cols-6">
          <div>
            <label className="text-sm">Account</label>
            <Select value={String(form.account_id)} onValueChange={(v) => setForm({ ...form, account_id: Number(v) })}>
              <SelectTrigger><SelectValue placeholder="Account" /></SelectTrigger>
              <SelectContent>
                {accounts.map((a) => <SelectItem key={a.id} value={String(a.id)}>{a.name}</SelectItem>)}
              </SelectContent>
            </Select>
          </div>
          <div>
            <label className="text-sm">Asset</label>
            <Input value={form.asset_symbol} onChange={(e) => setForm({ ...form, asset_symbol: e.target.value.toUpperCase() })} />
          </div>
          <div>
            <label className="text-sm">Side</label>
            <Select value={form.side} onValueChange={(v) => setForm({ ...form, side: v as any })}>
              <SelectTrigger><SelectValue /></SelectTrigger>
              <SelectContent>
                {(["buy","sell","transfer_in","transfer_out","stake","reward","fee"] as const).map(s => (
                  <SelectItem key={s} value={s}>{s}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div>
            <label className="text-sm">Qty</label>
            <Input value={String(form.qty ?? "")} onChange={(e) => setForm({ ...form, qty: e.target.value })} />
          </div>
          <div>
            <label className="text-sm">Price</label>
            <Input value={String(form.price_quote ?? "")} onChange={(e) => setForm({ ...form, price_quote: e.target.value })} />
          </div>
          <div>
            <label className="text-sm">Total</label>
            <Input value={String(form.total_quote ?? "")} onChange={(e) => setForm({ ...form, total_quote: e.target.value })} />
          </div>
          <div className="md:col-span-6">
            <Button onClick={onCreate}>Add</Button>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Transactions</CardTitle>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>ID</TableHead>
                <TableHead>TS</TableHead>
                <TableHead>Acct</TableHead>
                <TableHead>Asset</TableHead>
                <TableHead>Side</TableHead>
                <TableHead>Qty</TableHead>
                <TableHead>Price</TableHead>
                <TableHead>Total</TableHead>
                <TableHead>CCY</TableHead>
                <TableHead></TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {txs.map((t) => (
                <TableRow key={t.id}>
                  <TableCell>{t.id}</TableCell>
                  <TableCell>{new Date(t.ts).toLocaleString()}</TableCell>
                  <TableCell>{t.account_id}</TableCell>
                  <TableCell>{t.asset_symbol}</TableCell>
                  <TableCell>{t.side}</TableCell>
                  <TableCell>{t.qty}</TableCell>
                  <TableCell>{t.price_quote ?? ""}</TableCell>
                  <TableCell>{t.total_quote ?? ""}</TableCell>
                  <TableCell>{t.quote_ccy ?? ""}</TableCell>
                  <TableCell className="text-right"><Button variant="destructive" size="sm" onClick={() => onDelete(t.id)}>Delete</Button></TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
}

