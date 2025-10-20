"use client";
import { useEffect, useMemo, useState } from "react";
import { Card, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { api, type Account } from "@/lib/api";
import { toast } from "sonner";

export default function SettingsPage() {
  const [accounts, setAccounts] = useState<Account[]>([]);
  const [providers, setProviders] = useState<string[]>([]);
  const [accountId, setAccountId] = useState<number | "">("");
  const [quote, setQuote] = useState<string>("USD");
  const [providersOrder, setProvidersOrder] = useState<string>("");
  const [datasource, setDatasource] = useState<string>("auto");
  const [exportAccount, setExportAccount] = useState<number | "">("");
  const base = process.env.NEXT_PUBLIC_API_BASE || "http://127.0.0.1:8001";

  useEffect(() => {
    api.accounts.list().then(setAccounts).catch(() => {});
    const FALLBACK = ["coinmarketcap", "coindesk"];
    api.datasource.priceList().then((l) => setProviders(l && l.length ? l : FALLBACK)).catch(() => setProviders(FALLBACK));
    api.context.get().then((ctx) => {
      setAccountId((ctx.account_id as number) ?? "");
      setQuote(ctx.quote || "USD");
      setProvidersOrder(ctx.providers || "");
      setDatasource(ctx.datasource || "auto");
      setExportAccount((ctx.account_id as number) ?? "");
    }).catch(() => {});
  }, []);

  const exportHref = useMemo(() => {
    const q = new URLSearchParams();
    if (exportAccount !== "") q.set("account_id", String(exportAccount));
    const qs = q.toString();
    return `${base}/export/transactions.csv${qs ? `?${qs}` : ""}`;
  }, [exportAccount, base]);

  return (
    <div className="grid gap-4 lg:grid-cols-2">
      <Card>
        <CardHeader>
          <CardTitle>Defaults</CardTitle>
          <CardDescription>Save commonly used defaults for the app</CardDescription>
        </CardHeader>
        <div className="px-6 pb-6 grid gap-4 sm:grid-cols-2">
          <div>
            <label className="text-sm">Default Account</label>
            <Select value={String(accountId)} onValueChange={(v) => setAccountId(v === "none" ? "" : Number(v))}>
              <SelectTrigger><SelectValue placeholder="None" /></SelectTrigger>
              <SelectContent>
                <SelectItem value="none">None</SelectItem>
                {accounts.map((a) => (
                  <SelectItem key={a.id} value={String(a.id)}>{a.name}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div>
            <label className="text-sm">Quote Currency</label>
            <Input value={quote} onChange={(e) => setQuote(e.target.value.toUpperCase())} />
          </div>
          <div className="sm:col-span-2">
            <label className="text-sm">Price Provider Order</label>
            <Input placeholder="coinmarketcap,coindesk" value={providersOrder} onChange={(e) => setProvidersOrder(e.target.value)} />
          </div>
          <div>
            <label className="text-sm">Default Datasource</label>
            <Select value={String(datasource)} onValueChange={(v) => setDatasource(v)}>
              <SelectTrigger><SelectValue placeholder="Auto" /></SelectTrigger>
              <SelectContent>
                <SelectItem value="auto">Auto</SelectItem>
                {providers.map((p) => (
                  <SelectItem key={p} value={p}>{p}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div className="flex items-end">
            <Button
              onClick={async () => {
                try {
                  await api.context.update({
                    account_id: accountId === "" ? null : accountId,
                    quote,
                    providers: providersOrder.trim() || null,
                    datasource: datasource === "auto" ? null : datasource,
                  });
                  toast.success("Settings saved");
                } catch (e: unknown) {
                  toast.error(e instanceof Error ? e.message : String(e));
                }
              }}
            >
              Save
            </Button>
          </div>
        </div>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Export / Import (CSV)</CardTitle>
          <CardDescription>Download or upload CSV of transactions</CardDescription>
        </CardHeader>
        <div className="px-6 pb-6 grid gap-4">
          <div className="grid gap-2 sm:grid-cols-3">
            <div className="sm:col-span-2">
              <label className="text-sm">Export Account</label>
              <Select value={String(exportAccount)} onValueChange={(v) => setExportAccount(v === "all" ? "" : Number(v))}>
                <SelectTrigger><SelectValue placeholder="All accounts" /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All accounts</SelectItem>
                  {accounts.map((a) => (
                    <SelectItem key={a.id} value={String(a.id)}>{a.name}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="flex items-end">
              <a href={exportHref} target="_blank" rel="noreferrer">
                <Button variant="outline">Download CSV</Button>
              </a>
            </div>
          </div>

          <div className="grid gap-2 sm:grid-cols-3">
            <div className="sm:col-span-2">
              <label className="text-sm">Import CSV</label>
              <input id="csvFile" type="file" accept="text/csv,.csv" className="block w-full text-sm" />
            </div>
            <div className="flex items-end">
              <Button
                variant="default"
                onClick={async () => {
                  const input = document.getElementById("csvFile") as HTMLInputElement | null;
                  if (!input || !input.files || input.files.length === 0) {
                    toast.error("Choose a CSV file");
                    return;
                  }
                  const file = input.files[0];
                  const form = new FormData();
                  form.append("file", file);
                  if (accountId !== "") form.append("account_id", String(accountId));
                  if (datasource && datasource !== "auto") form.append("datasource", String(datasource));
                  form.append("dedupe_by", "external_id");
                  try {
                    const res = await fetch(`${base}/import/transactions.csv`, { method: "POST", body: form });
                    if (!res.ok) throw new Error(await res.text());
                    const j = await res.json();
                    toast.success(`Imported ${j.inserted} rows, skipped ${j.skipped}`);
                  } catch (e: unknown) {
                    toast.error(e instanceof Error ? e.message : String(e));
                  }
                }}
              >
                Upload
              </Button>
            </div>
          </div>
          <div className="text-xs text-muted-foreground">
            Expected columns: timestamp, account (ignored), asset, side, qty, price_quote (optional), total_quote (optional), quote_ccy (optional)
          </div>
        </div>
      </Card>
    </div>
  );
}
