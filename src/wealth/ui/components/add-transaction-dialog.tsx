"use client";
import * as React from "react";
import { useEffect, useState } from "react";
import { Dialog, DialogContent, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Input } from "@/components/ui/input";
import { api, type Account, type TxIn } from "@/lib/api";
import { toast } from "sonner";

export function AddTransactionButton({
  accounts,
  onCreated,
  size = "sm",
}: {
  accounts: Account[];
  onCreated?: () => void;
  size?: "sm" | "default" | "lg";
}) {
  const [open, setOpen] = useState(false);
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
  } as TxIn);

  useEffect(() => {
    if (accounts.length && form.account_id === 0) setForm((f) => ({ ...f, account_id: accounts[0].id }));
  }, [accounts, form.account_id]);

  const submit = async () => {
    if (!form.account_id) {
      toast.error("Select account");
      return;
    }
    try {
      setLoading(true);
      const body: TxIn = { ...form, qty: String(form.qty || "0") };
      await api.tx.create(body);
      toast.success("Transaction created");
      setOpen(false);
      onCreated?.();
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : String(e);
      toast.error(msg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button size={size} className="whitespace-nowrap">Add Transaction</Button>
      </DialogTrigger>
      <DialogContent className="sm:max-w-[520px]">
        <DialogHeader>
          <DialogTitle>Add Transaction</DialogTitle>
        </DialogHeader>
        <div className="grid gap-4 sm:grid-cols-2">
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
            <Select value={form.side} onValueChange={(v) => setForm({ ...form, side: v as TxIn["side"] })}>
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
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={() => setOpen(false)} disabled={loading}>Cancel</Button>
          <Button onClick={submit} disabled={loading}>Save</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
