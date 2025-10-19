"use client";
import Link from "next/link";
import { Fragment } from "react";
import { Separator } from "@/components/ui/separator";
import { SidebarTrigger } from "@/components/ui/sidebar";
import { useDashboard } from "@/components/dashboard-provider";
import { AccountMultiSelect } from "@/components/account-multi-select";
import { AddTransactionButton } from "@/components/add-transaction-dialog";
import { CreateAccountButton } from "@/components/create-account-dialog";
import { EditAccountButton } from "@/components/edit-account-dialog";
import { Breadcrumb, BreadcrumbItem, BreadcrumbLink, BreadcrumbList, BreadcrumbPage, BreadcrumbSeparator } from "@/components/ui/breadcrumb";
import { usePathname } from "next/navigation";

export function SiteHeader() {
  const { accounts, selected, setSelected, triggerReload } = useDashboard();
  const pathname = usePathname();
  const actions = () => {
    if (pathname === "/") {
      return (
        <div className="flex items-center gap-2">
          <AccountMultiSelect accounts={accounts} value={selected} onChange={setSelected} size="sm" />
          <AddTransactionButton accounts={accounts} onCreated={triggerReload} size="sm" />
        </div>
      );
    }
    if (pathname === "/accounts") {
      return (
        <div>
          <CreateAccountButton onCreated={triggerReload} />
        </div>
      );
    }
    if (pathname === "/transactions") {
      return (
        <div className="flex items-center gap-2">
          <AddTransactionButton accounts={accounts} onCreated={triggerReload} size="sm" />
        </div>
      );
    }
    const match = pathname.match(/^\/accounts\/(\d+)/);
    if (match) {
      const id = Number(match[1]);
      const acct = accounts.find((a) => a.id === id);
      return (
        <div className="flex items-center gap-2">
          {acct && <EditAccountButton account={acct} onSaved={() => {}} onDeleted={() => {}} />}
          <AddTransactionButton accounts={acct ? [acct] : []} onCreated={triggerReload} size="sm" />
        </div>
      );
    }
    return null;
  };

  const crumbs = () => {
    const list: { label: string; href?: string }[] = [];
    if (pathname === "/") {
      list.push({ label: "Dashboard" });
    } else if (pathname === "/accounts") {
      list.push({ label: "Dashboard", href: "/" });
      list.push({ label: "Accounts" });
    } else if (pathname.startsWith("/accounts/")) {
      const id = Number((pathname.split("/")[2] || "").trim());
      const acct = accounts.find((a) => a.id === id);
      list.push({ label: "Dashboard", href: "/" });
      list.push({ label: "Accounts", href: "/accounts" });
      list.push({ label: acct?.name || `#${id}` });
    } else if (pathname === "/transactions") {
      list.push({ label: "Dashboard", href: "/" });
      list.push({ label: "Transactions" });
    } else {
      list.push({ label: "Dashboard", href: "/" });
    }
    return (
      <Breadcrumb>
        <BreadcrumbList>
          {list.map((c, idx) => (
            <Fragment key={`crumb-${idx}`}>
              <BreadcrumbItem>
                {c.href ? (
                  <BreadcrumbLink asChild>
                    <Link href={c.href}>{c.label}</Link>
                  </BreadcrumbLink>
                ) : (
                  <BreadcrumbPage>{c.label}</BreadcrumbPage>
                )}
              </BreadcrumbItem>
              {idx < list.length - 1 && <BreadcrumbSeparator />}
            </Fragment>
          ))}
        </BreadcrumbList>
      </Breadcrumb>
    );
  };

  return (
    <header className="flex h-(--header-height) shrink-0 items-center gap-2 border-b transition-[width,height] ease-linear group-has-data-[collapsible=icon]/sidebar-wrapper:h-(--header-height)">
      <div className="flex w-full items-center gap-2 px-4 lg:gap-2 lg:px-6">
        <SidebarTrigger className="-ml-1" />
        <Separator orientation="vertical" className="mx-2 data-[orientation=vertical]:h-4" />
        <div className="flex w-full items-center justify-between gap-2">
          <div className="min-w-0">{crumbs()}</div>
          <div className="flex items-center gap-2">{actions()}</div>
        </div>
      </div>
    </header>
  );
}
