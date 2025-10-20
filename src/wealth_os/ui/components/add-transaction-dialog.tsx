"use client";
import * as React from "react";
import { useEffect, useState } from "react";
import { Dialog, DialogContent, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Input } from "@/components/ui/input";
import { api, type Account, type TxIn } from "@/lib/api";
import { toast } from "sonner";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { Calendar } from "@/components/ui/calendar";
import { CalendarIcon } from "lucide-react";
import { cn } from "@/lib/utils";

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
  const [dt, setDt] = useState<Date>(new Date());
  const [providers, setProviders] = useState<string[]>([]);
  const [form, setForm] = useState<TxIn>({
    ts: new Date().toISOString(),
    account_id: 0,
    asset_symbol: "BTC",
    side: "buy",
    qty: "0.1",
    quote_ccy: "USD",
  } as TxIn);

  useEffect(() => {
    if (accounts.length && form.account_id === 0) setForm((f) => ({ ...f, account_id: accounts[0].id }));
  }, [accounts, form.account_id]);

  useEffect(() => {
    setForm((f) => ({ ...f, ts: new Date(dt).toISOString() }));
  }, [dt]);

  useEffect(() => {
    const FALLBACK = ["coinmarketcap", "coindesk"];
    api.datasource
      .priceList()
      .then((list) => setProviders(list && list.length ? list : FALLBACK))
      .catch(() => setProviders(FALLBACK));
  }, []);

  const submit = async () => {
    if (!form.account_id) {
      toast.error("Select account");
      return;
    }
    try {
      setLoading(true);
      const body: TxIn = {
        ...form,
        // sanitize optional fields
        qty: String(form.qty || "0"),
        price_quote: form.price_quote && String(form.price_quote).trim() !== "" ? form.price_quote : undefined,
        total_quote: undefined,
      } as unknown as TxIn;
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

  const showPrice = form.side === "buy" || form.side === "sell";

  const fetchLatestPrice = async () => {
    try {
      setLoading(true);
      const q = await api.price.quote(form.asset_symbol, form.quote_ccy || "USD", form.datasource as string | undefined);
      setForm((f) => ({ ...f, price_quote: String(q.price), quote_ccy: q.quote_ccy }));
      toast.success(`Fetched ${q.symbol}/${q.quote_ccy} price`);
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
          <div className="sm:col-span-2">
            <label className="text-sm">Time</label>
            <Popover>
              <PopoverTrigger asChild>
                <Button
                  variant="outline"
                  className={cn(
                    "w-full justify-start text-left font-normal",
                    !dt && "text-muted-foreground"
                  )}
                >
                  <CalendarIcon className="mr-2 h-4 w-4" />
                  {formatDateTime(dt)}
                </Button>
              </PopoverTrigger>
              <PopoverContent className="w-auto p-0">
                <div className="p-3">
                  <Calendar
                    mode="single"
                    selected={dt}
                    onSelect={(d) => d && setDt(mergeDate(d, dt))}
                    initialFocus
                  />
                  <div className="mt-3 flex items-center gap-2">
                    <Input type="time" step={1} className="w-40"
                      value={formatTime(dt)}
                      onChange={(e) => setDt(applyTime(dt, e.target.value))}
                    />
                    <Button variant="outline" size="sm" onClick={() => setDt(new Date())}>Now</Button>
                  </div>
                </div>
              </PopoverContent>
            </Popover>
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
            <label className="text-sm">Datasource</label>
            <Select value={String(form.datasource ?? "auto")} onValueChange={(v) => setForm({ ...form, datasource: v === "auto" ? undefined : v })}>
              <SelectTrigger><SelectValue placeholder="Auto" /></SelectTrigger>
              <SelectContent>
                <SelectItem value="auto">Auto</SelectItem>
                {providers.map((p) => (
                  <SelectItem key={p} value={p}>{p}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div>
            <label className="text-sm">Qty</label>
            <Input value={String(form.qty ?? "")} onChange={(e) => setForm({ ...form, qty: e.target.value })} />
          </div>
          {showPrice && (
            <div className="sm:col-span-2 flex items-end gap-2">
              <div className="grow">
                <label className="text-sm">Price</label>
                <Input value={String(form.price_quote ?? "")} onChange={(e) => setForm({ ...form, price_quote: e.target.value })} />
              </div>
              <Button type="button" variant="outline" className="mb-0" onClick={fetchLatestPrice} disabled={loading}>
                Get latest price
              </Button>
            </div>
          )}
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={() => setOpen(false)} disabled={loading}>Cancel</Button>
          <Button onClick={submit} disabled={loading}>Save</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

function pad(n: number) { return n.toString().padStart(2, "0"); }
function formatDateTime(d: Date) {
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}`;
}
function formatTime(d: Date) {
  return `${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}`;
}
function mergeDate(datePart: Date, base: Date) {
  const d = new Date(base);
  d.setFullYear(datePart.getFullYear(), datePart.getMonth(), datePart.getDate());
  return d;
}
function applyTime(base: Date, timeStr: string) {
  const [hh, mm, ss] = timeStr.split(":").map((v) => parseInt(v || "0", 10));
  const d = new Date(base);
  d.setHours(hh || 0, mm || 0, ss || 0, 0);
  return d;
}
