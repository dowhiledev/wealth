"use client";
import * as React from "react";
import { Dialog, DialogContent, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Input } from "@/components/ui/input";
import { api, type AccountIn } from "@/lib/api";
import { toast } from "sonner";

export function CreateAccountButton({ onCreated, size = "sm" }: { onCreated?: () => void; size?: "sm" | "default" | "lg" }) {
  const [open, setOpen] = React.useState(false);
  const [loading, setLoading] = React.useState(false);
  const [form, setForm] = React.useState<AccountIn>({ name: "", type: "exchange", currency: "USD", datasource: "", external_id: "" });

  const submit = async () => {
    if (!form.name) { toast.error("Name is required"); return; }
    try {
      setLoading(true);
      await api.accounts.create(form);
      toast.success("Account created");
      setOpen(false);
      onCreated?.();
      setForm({ name: "", type: form.type, currency: form.currency, datasource: "", external_id: "" });
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
        <Button size={size} className="whitespace-nowrap">Create Account</Button>
      </DialogTrigger>
      <DialogContent className="sm:max-w-[520px]">
        <DialogHeader>
          <DialogTitle>Create Account</DialogTitle>
        </DialogHeader>
        <div className="grid gap-4 sm:grid-cols-2">
          <div className="sm:col-span-2">
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
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={() => setOpen(false)} disabled={loading}>Cancel</Button>
          <Button onClick={submit} disabled={loading}>Create</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

