"use client";
import * as React from "react";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuCheckboxItem,
  DropdownMenuContent,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";

import type { Account } from "@/lib/api";

function labelForSelection(accounts: Account[], selected: number[]): string {
  if (selected.length === 0) return "All Accounts";
  const map = new Map(accounts.map((a) => [a.id, a.name] as const));
  const names = selected.map((id) => map.get(id) || String(id));
  if (names.length <= 2) return names.join(", ");
  return `${names[0]}, ${names[1]} +${names.length - 2}`;
}

export function AccountMultiSelect({
  accounts,
  value,
  onChange,
  size = "sm",
}: {
  accounts: Account[];
  value: number[];
  onChange: (v: number[]) => void;
  size?: "sm" | "default";
}) {
  const allSelected = value.length > 0 && value.length === accounts.length;
  const currentLabel = labelForSelection(accounts, value);
  const toggleId = (id: number) => {
    if (value.includes(id)) onChange(value.filter((x) => x !== id));
    else onChange([...value, id]);
  };
  const selectAll = () => onChange(accounts.map((a) => a.id));
  const clearAll = () => onChange([]);
  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button
          variant="outline"
          size={size}
          className="min-w-0 max-w-[220px] md:max-w-[280px] lg:max-w-[320px] justify-between overflow-hidden"
        >
          <span className="truncate">{currentLabel}</span>
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent className="w-72">
        <DropdownMenuLabel>Filter Accounts</DropdownMenuLabel>
        <DropdownMenuCheckboxItem checked={value.length === 0} onCheckedChange={clearAll}>
          All Accounts
        </DropdownMenuCheckboxItem>
        <DropdownMenuCheckboxItem checked={allSelected} onCheckedChange={selectAll}>
          Select All
        </DropdownMenuCheckboxItem>
        <DropdownMenuSeparator />
        {accounts.map((a) => (
          <DropdownMenuCheckboxItem key={a.id} checked={value.includes(a.id)} onCheckedChange={() => toggleId(a.id)}>
            {a.name}
          </DropdownMenuCheckboxItem>
        ))}
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
