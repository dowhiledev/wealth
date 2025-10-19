"use client";
import { useEffect, useMemo, useState } from "react";
import { useParams } from "next/navigation";
import { api, type Account, type Tx } from "@/lib/api";
import { WealthKPIs } from "@/components/wealth-kpis";
import { WealthAllocation } from "@/components/wealth-allocation";
import { WealthPnL } from "@/components/wealth-pnl";
import { WealthTopAssets } from "@/components/wealth-top-assets";
import { WealthVolume } from "@/components/wealth-volume";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { TransactionsTable } from "@/components/transactions-table";
import { EditAccountButton } from "@/components/edit-account-dialog";
import { AddTransactionButton } from "@/components/add-transaction-dialog";

export default function AccountDetailPage() {
  const params = useParams<{ id: string }>();
  const idNum = useMemo(() => Number(params.id), [params.id]);
  const [account, setAccount] = useState<Account | null>(null);
  const [rows, setRows] = useState<Tx[]>([]);
  const [reloadKey, setReloadKey] = useState(0);

  const load = async () => {
    const accounts = await api.accounts.list();
    const found = accounts.find((a) => a.id === idNum) || null;
    setAccount(found);
    const txs = await api.tx.list({ account_id: idNum, limit: 1000 });
    setRows(txs);
  };

  useEffect(() => { void load(); }, [idNum, reloadKey]);

  if (!idNum || !Number.isFinite(idNum)) return <div className="p-6">Invalid account id</div>;

  return (
    <div className="space-y-4">
      <WealthKPIs accountIds={[idNum]} showAccountsKPI={false} key={`kpi-${reloadKey}`} />

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <WealthAllocation accountIds={[idNum]} key={`alloc-${reloadKey}`} />
        <WealthPnL accountIds={[idNum]} key={`pnl-${reloadKey}`} />
        <WealthTopAssets accountIds={[idNum]} key={`top-${reloadKey}`} />
        <WealthVolume accountIds={[idNum]} key={`vol-${reloadKey}`} />
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Transactions</CardTitle>
        </CardHeader>
        <CardContent>
          <TransactionsTable rows={rows} onChanged={load} />
        </CardContent>
      </Card>
    </div>
  );
}
