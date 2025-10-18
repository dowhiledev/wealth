"use client";
import { WealthKPIs } from "@/components/wealth-kpis";
import { WealthAllocation } from "@/components/wealth-allocation";
import { WealthLatest } from "@/components/wealth-latest";

export default function Page() {
  return (
    <div className="flex flex-1 flex-col gap-4 py-4 md:gap-6 md:py-6">
      <WealthKPIs />
      <WealthAllocation />
      <WealthLatest />
    </div>
  );
}
