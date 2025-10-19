"use client";
import * as React from "react";
import { Dialog, DialogContent, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Input } from "@/components/ui/input";
import { api, type Tx, type TxIn, type Account } from "@/lib/api";
import { toast } from "sonner";

export function EditTransactionDialog({ tx, trigger, children, onSaved }: { tx: Tx; trigger?: React.ReactNode; children?: React.ReactNode; onSaved?: () => void }) {
  const [open, setOpen] = React.useState(false);
  const [loading, setLoading] = React.useState(false);
  const [accounts, setAccounts] = React.useState<Account[]>([]);
  const [form, setForm] = React.useState<TxIn>({
    id: tx.id,
    ts: tx.ts,
    account_id: tx.account_id,
    asset_symbol: tx.asset_symbol,
    side: tx.side,
    qty: String(tx.qty ?? ""),
    price_quote: tx.price_quote ?? "",
    total_quote: tx.total_quote ?? "",
    quote_ccy: tx.quote_ccy ?? "USD",
    fee_qty: tx.fee_qty ?? "",
    fee_asset: tx.fee_asset ?? "",
    note: tx.note ?? "",
    tx_hash: tx.tx_hash ?? "",
    datasource: tx.datasource ?? "",
    import_batch_id: tx.import_batch_id ?? undefined,
    tags: tx.tags ?? "",
  } as unknown as TxIn);

  React.useEffect(() => {
    api.accounts.list().then(setAccounts).catch(() => {});
  }, []);

  const submit = async () => {
    try {
      setLoading(true);
      const body: TxIn = { ...form, qty: String(form.qty || "0") };
      await api.tx.update(tx.id, body);
      toast.success("Transaction updated");
      setOpen(false);
      onSaved?.();
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
        {trigger ? trigger : (children ? children : <Button variant="ghost" size="sm">Edit</Button>)}
      </DialogTrigger>
      <DialogContent className="sm:max-w-[640px]">
        <DialogHeader>
          <DialogTitle>Edit Transaction #{tx.id}</DialogTitle>
        </DialogHeader>
        <div className="grid gap-4 md:grid-cols-3">
          <div>
            <label className="text-sm">Time</label>
            <Input value={String(form.ts ?? "")} onChange={(e) => setForm({ ...form, ts: e.target.value })} />
          </div>
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
            <label className="text-sm">Asset</label>
            <Input value={form.asset_symbol} onChange={(e) => setForm({ ...form, asset_symbol: e.target.value.toUpperCase() })} />
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
          <div>
            <label className="text-sm">CCY</label>
            <Input value={String(form.quote_ccy ?? "")} onChange={(e) => setForm({ ...form, quote_ccy: e.target.value })} />
          </div>
          <div>
            <label className="text-sm">Fee Qty</label>
            <Input value={String(form.fee_qty ?? "")} onChange={(e) => setForm({ ...form, fee_qty: e.target.value })} />
          </div>
          <div>
            <label className="text-sm">Fee Asset</label>
            <Input value={String(form.fee_asset ?? "")} onChange={(e) => setForm({ ...form, fee_asset: e.target.value })} />
          </div>
          <div className="md:col-span-3">
            <label className="text-sm">Note</label>
            <Input value={String(form.note ?? "")} onChange={(e) => setForm({ ...form, note: e.target.value })} />
          </div>
          <div className="md:col-span-3">
            <label className="text-sm">Tx Hash</label>
            <Input value={String(form.tx_hash ?? "")} onChange={(e) => setForm({ ...form, tx_hash: e.target.value })} />
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
