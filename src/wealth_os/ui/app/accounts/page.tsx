"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { api, type Account } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { CreateAccountButton } from "@/components/create-account-dialog";

export default function AccountsPage() {
  const [accounts, setAccounts] = useState<Account[]>([]);
  const [loading, setLoading] = useState(false);
  const load = async () => {
    setLoading(true);
    try {
      const rows = await api.accounts.list();
      setAccounts(rows);
    } finally {
      setLoading(false);
    }
  };
  useEffect(() => { void load(); }, []);

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
        {accounts.map((a) => (
          <Link key={a.id} href={`/accounts/${a.id}`}>
            <Card className="hover:bg-accent/40 transition-colors">
              <CardHeader>
                <CardTitle className="text-lg font-semibold">{a.name}</CardTitle>
              </CardHeader>
              <CardContent className="text-sm text-muted-foreground">
                <div>Type: {a.type}</div>
                <div>Currency: {a.currency}</div>
                <div>Created: {new Date(a.created_at).toLocaleDateString()}</div>
              </CardContent>
            </Card>
          </Link>
        ))}
        {!loading && accounts.length === 0 && (
          <Card>
            <CardContent className="p-6 text-sm text-muted-foreground">No accounts yet. Create one to get started.</CardContent>
          </Card>
        )}
      </div>
    </div>
  );
}
