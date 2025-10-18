"use client";
import { Separator } from "@/components/ui/separator";
import { SidebarTrigger } from "@/components/ui/sidebar";
import { useDashboard } from "@/components/dashboard-provider";
import { AccountMultiSelect } from "@/components/account-multi-select";
import { AddTransactionButton } from "@/components/add-transaction-dialog";

export function SiteHeader() {
  const { accounts, selected, setSelected, triggerReload } = useDashboard();
  return (
    <header className="flex h-(--header-height) shrink-0 items-center gap-2 border-b transition-[width,height] ease-linear group-has-data-[collapsible=icon]/sidebar-wrapper:h-(--header-height)">
      <div className="flex w-full items-center gap-2 px-4 lg:gap-2 lg:px-6">
        <SidebarTrigger className="-ml-1" />
        <Separator orientation="vertical" className="mx-2 data-[orientation=vertical]:h-4" />
        <div className="ml-auto flex items-center gap-2">
          <AccountMultiSelect accounts={accounts} value={selected} onChange={setSelected} size="sm" />
          <AddTransactionButton accounts={accounts} onCreated={triggerReload} size="sm" />
        </div>
      </div>
    </header>
  );
}
