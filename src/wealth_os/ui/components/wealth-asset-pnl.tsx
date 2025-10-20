"use client";
import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { formatAmount } from "@/lib/utils";

type Position = { asset: string; qty: number; value?: number; cost_open?: number; unrealized?: number; realized?: number };

export function WealthAssetPnL({ accountId }: { accountId: number }) {
  const [rows, setRows] = useState<Position[]>([]);

  useEffect(() => {
    const base = process.env.NEXT_PUBLIC_API_BASE || "http://127.0.0.1:8001";
    const load = async () => {
      const s: { positions: Array<{ asset: string; qty: number | string; value?: number | string; cost_open?: number | string; unrealized_pnl?: number | string; realized_pnl?: number | string }> } = await fetch(`${base}/portfolio/summary?account_id=${accountId}`).then(r => r.json());
      const ds = s.positions.map(p => ({
        asset: p.asset,
        qty: Number(p.qty ?? 0),
        value: p.value != null ? Number(p.value) : undefined,
        cost_open: p.cost_open != null ? Number(p.cost_open) : undefined,
        unrealized: p.unrealized_pnl != null ? Number(p.unrealized_pnl) : undefined,
        realized: p.realized_pnl != null ? Number(p.realized_pnl) : undefined,
      }));
      ds.sort((a, b) => (Number(b.unrealized ?? 0) - Number(a.unrealized ?? 0)));
      setRows(ds);
    };
    load().catch(() => {});
  }, [accountId]);

  return (
    <Card>
      <CardHeader>
        <CardTitle>Asset-wise PnL</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-5 gap-2 text-xs font-medium text-muted-foreground mb-2">
          <div>Asset</div>
          <div className="text-right">Qty</div>
          <div className="text-right">Value</div>
          <div className="text-right">Unrealized</div>
          <div className="text-right">Realized</div>
        </div>
        <div className="space-y-1">
          {rows.map((r) => (
            <div key={r.asset} className="grid grid-cols-5 gap-2 text-sm">
              <div className="truncate" title={r.asset}>{r.asset}</div>
              <div className="text-right">{formatAmount(r.qty)}</div>
              <div className="text-right">{r.value != null ? formatAmount(r.value) : "-"}</div>
              <div className="text-right">{r.unrealized != null ? formatAmount(r.unrealized) : "-"}</div>
              <div className="text-right">{r.realized != null ? formatAmount(r.realized) : "-"}</div>
            </div>
          ))}
          {rows.length === 0 && <div className="text-sm text-muted-foreground">No assets</div>}
        </div>
      </CardContent>
    </Card>
  );
}

