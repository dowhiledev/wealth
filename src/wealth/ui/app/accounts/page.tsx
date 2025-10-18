"use client";

import { useEffect, useState } from "react";
import { api, type Account, type AccountIn } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { toast } from "sonner";

export default function AccountsPage() {
  const [accounts, setAccounts] = useState<Account[]>([]);
  const [loading, setLoading] = useState(false);
  const [form, setForm] = useState<AccountIn>({ name: "", type: "exchange", currency: "USD", datasource: "", external_id: "" });

  const load = async () => {
    setLoading(true);
    try {
      const rows = await api.accounts.list();
      setAccounts(rows);
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : String(e);
      toast.error(msg);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const onCreate = async () => {
    if (!form.name) {
      toast.error("Name is required");
      return;
    }
    try {
      await api.accounts.create(form);
      setForm({ name: "", type: form.type, currency: form.currency, datasource: form.datasource, external_id: "" });
      await load();
      toast.success("Account created");
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : String(e);
      toast.error(msg);
    }
  };

  const onDelete = async (id: number) => {
    if (!confirm("Delete this account?")) return;
    try {
      await api.accounts.remove(id);
      await load();
      toast.success("Account deleted");
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : String(e);
      toast.error(msg);
    }
  };

  return (
    <div className="p-6 space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Create Account</CardTitle>
        </CardHeader>
        <CardContent className="grid gap-4 md:grid-cols-5">
          <div className="md:col-span-2">
            <label className="text-sm">Name</label>
            <Input value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} placeholder="My Exchange" />
          </div>
          <div>
            <label className="text-sm">Type</label>
            <Select value={form.type} onValueChange={(v) => setForm({ ...form, type: v as AccountIn["type"] })}>
              <SelectTrigger><SelectValue placeholder="Type" /></SelectTrigger>
              <SelectContent>
                <SelectItem value="exchange">Exchange</SelectItem>
                <SelectItem value="wallet">Wallet</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div>
            <label className="text-sm">Currency</label>
            <Input value={form.currency} onChange={(e) => setForm({ ...form, currency: e.target.value })} />
          </div>
          <div className="md:col-span-5 flex gap-2">
            <Button onClick={onCreate}>Create</Button>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Accounts</CardTitle>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>ID</TableHead>
                <TableHead>Name</TableHead>
                <TableHead>Type</TableHead>
                <TableHead>Currency</TableHead>
                <TableHead>Datasource</TableHead>
                <TableHead>Created</TableHead>
                <TableHead></TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {accounts.map((a) => (
                <TableRow key={a.id}>
                  <TableCell>{a.id}</TableCell>
                  <TableCell>{a.name}</TableCell>
                  <TableCell>{a.type}</TableCell>
                  <TableCell>{a.currency}</TableCell>
                  <TableCell>{a.datasource || "-"}</TableCell>
                  <TableCell>{new Date(a.created_at).toLocaleString()}</TableCell>
                  <TableCell className="text-right">
                    <Button variant="destructive" size="sm" onClick={() => onDelete(a.id)}>Delete</Button>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
}
