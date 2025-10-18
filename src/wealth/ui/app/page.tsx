"use client";
import { WealthKPIs } from "@/components/wealth-kpis";
import { WealthAllocation } from "@/components/wealth-allocation";
import { WealthLatest } from "@/components/wealth-latest";
import { WealthPnL } from "@/components/wealth-pnl";
import { useDashboard } from "@/components/dashboard-provider";
import { WealthTopAssets } from "@/components/wealth-top-assets";
import { WealthVolume } from "@/components/wealth-volume";

export default function Home() {
  const { selected, reloadKey } = useDashboard();

  return (
    <div className="flex flex-1 flex-col gap-4 py-4 md:gap-6 md:py-6">
      <WealthKPIs accountIds={selected} key={`kpi-${reloadKey}`} />

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <WealthAllocation accountIds={selected} key={`alloc-${reloadKey}`} />
        <WealthPnL accountIds={selected} key={`pnl-${reloadKey}`} />
        <WealthTopAssets accountIds={selected} key={`top-${reloadKey}`} />
        <WealthVolume accountIds={selected} key={`vol-${reloadKey}`} />
      </div>

      <WealthLatest accountIds={selected} key={`latest-${reloadKey}`} />
    </div>
  );
}
