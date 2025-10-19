"use client";
import * as React from "react";
import {
  ColumnDef,
  ColumnFiltersState,
  SortingState,
  VisibilityState,
  getCoreRowModel,
  getFilteredRowModel,
  getPaginationRowModel,
  getSortedRowModel,
  useReactTable,
  flexRender,
} from "@tanstack/react-table";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Checkbox } from "@/components/ui/checkbox";
import {
  DropdownMenu,
  DropdownMenuCheckboxItem,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { formatAmount } from "@/lib/utils";
import type { Tx } from "@/lib/api";
import { EditTransactionDialog } from "@/components/edit-transaction-dialog";
import { api } from "@/lib/api";
import Link from "next/link";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from "@/components/ui/alert-dialog";

type Row = Tx;

export function TransactionsTable({ rows, onChanged }: { rows: Row[]; onChanged?: () => void }) {
  const [sorting, setSorting] = React.useState<SortingState>([{ id: "ts", desc: true }]);
  const [columnFilters, setColumnFilters] = React.useState<ColumnFiltersState>([]);
  const [columnVisibility, setColumnVisibility] = React.useState<VisibilityState>({ fee_qty: false, fee_asset: false, tx_hash: false });
  const [rowSelection, setRowSelection] = React.useState({});
  const [pageSize, setPageSize] = React.useState<number>(10);
  const [acctMap, setAcctMap] = React.useState<Record<number, string>>({});

  React.useEffect(() => {
    api.accounts
      .list()
      .then((list) => {
        const m: Record<number, string> = {};
        for (const a of list) m[a.id] = a.name;
        setAcctMap(m);
      })
      .catch(() => {});
  }, []);

  const columns: ColumnDef<Row>[] = React.useMemo(() => [
  {
    id: "select",
    header: ({ table }) => (
      <Checkbox
        checked={table.getIsAllPageRowsSelected() || (table.getIsSomePageRowsSelected() && "indeterminate")}
        onCheckedChange={(value) => table.toggleAllPageRowsSelected(!!value)}
        aria-label="Select all"
      />
    ),
    cell: ({ row }) => (
      <Checkbox
        checked={row.getIsSelected()}
        onCheckedChange={(value) => row.toggleSelected(!!value)}
        aria-label="Select row"
      />
    ),
    enableSorting: false,
    enableHiding: false,
    size: 24,
  },
  { accessorKey: "id", header: "ID" },
  {
    accessorKey: "ts",
    header: "Time",
    cell: ({ row }) => new Date(row.original.ts).toLocaleString(),
    sortingFn: (a, b) => new Date(a.original.ts).getTime() - new Date(b.original.ts).getTime(),
  },
  {
    accessorKey: "account_id",
    header: "Acct",
    cell: ({ row }) => {
      const id = row.original.account_id;
      const name = acctMap[id] ?? `#${id}`;
      return (
        <Link href={`/accounts/${id}`} className="underline">
          {name}
        </Link>
      );
    },
  },
  { accessorKey: "asset_symbol", header: "Asset" },
  {
    accessorKey: "side",
    header: "Side",
    cell: ({ row }) => (
      <Badge variant={row.original.side === "sell" ? "destructive" : row.original.side === "buy" ? "default" : "secondary"}>
        {row.original.side}
      </Badge>
    ),
  },
  { accessorKey: "qty", header: "Qty", cell: ({ row }) => formatAmount(row.original.qty) },
  { accessorKey: "price_quote", header: "Price", cell: ({ row }) => (row.original.price_quote != null ? formatAmount(row.original.price_quote) : "") },
  { accessorKey: "total_quote", header: "Total", cell: ({ row }) => (row.original.total_quote != null ? formatAmount(row.original.total_quote) : "") },
  { accessorKey: "quote_ccy", header: "CCY" },
  { accessorKey: "fee_qty", header: "Fee Qty", cell: ({ row }) => (row.original.fee_qty != null ? formatAmount(row.original.fee_qty) : "") },
  { accessorKey: "fee_asset", header: "Fee Asset" },
  { accessorKey: "note", header: "Note", cell: ({ row }) => <span className="max-w-[240px] truncate inline-block align-top" title={row.original.note ?? undefined}>{row.original.note ?? ""}</span> },
  { accessorKey: "tx_hash", header: "Hash", cell: ({ row }) => <span className="max-w-[240px] truncate inline-block align-top" title={row.original.tx_hash ?? undefined}>{row.original.tx_hash ?? ""}</span> },
  { accessorKey: "datasource", header: "Source" },
  {
    id: "actions",
    enableHiding: false,
    cell: ({ row }) => {
      const tx = row.original;
      return (
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="ghost" className="h-8 w-8 p-0">
              <span className="sr-only">Open menu</span>
              ⋯
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end">
            <DropdownMenuLabel>Actions</DropdownMenuLabel>
            <EditTransactionDialog
              tx={tx}
              onSaved={onChanged}
              trigger={<DropdownMenuItem onSelect={(e) => e.preventDefault()}>Edit</DropdownMenuItem>}
            />
            <DropdownMenuSeparator />
            <DropdownMenuItem onClick={async () => { await api.tx.remove(tx.id); onChanged?.(); }}>Delete</DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      );
    },
  },
  ], [onChanged, acctMap]);

  const table = useReactTable({
    data: rows,
    columns,
    state: { sorting, columnFilters, columnVisibility, rowSelection, pagination: { pageIndex: 0, pageSize } },
    onSortingChange: setSorting,
    onColumnFiltersChange: setColumnFilters,
    onColumnVisibilityChange: setColumnVisibility,
    onRowSelectionChange: setRowSelection,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
    getFilteredRowModel: getFilteredRowModel(),
    getPaginationRowModel: getPaginationRowModel(),
  });

  const assetFilter = table.getColumn("asset_symbol");
  const sideFilter = table.getColumn("side");
  const selectedIds = table.getSelectedRowModel().rows.map((r) => (r.original as Row).id);

  return (
    <div className="space-y-3">
      <div className="flex flex-wrap items-center gap-2">
        <Input
          placeholder="Filter asset..."
          value={(assetFilter?.getFilterValue() as string) ?? ""}
          onChange={(e) => assetFilter?.setFilterValue(e.target.value)}
          className="h-8 w-44"
        />
        <Select value={(sideFilter?.getFilterValue() as string) ?? "all"} onValueChange={(v) => sideFilter?.setFilterValue(v === "all" ? undefined : v)}>
          <SelectTrigger className="h-8 w-36"><SelectValue placeholder="Side" /></SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All sides</SelectItem>
            <SelectItem value="buy">buy</SelectItem>
            <SelectItem value="sell">sell</SelectItem>
            <SelectItem value="transfer_in">transfer_in</SelectItem>
            <SelectItem value="transfer_out">transfer_out</SelectItem>
            <SelectItem value="stake">stake</SelectItem>
            <SelectItem value="reward">reward</SelectItem>
            <SelectItem value="fee">fee</SelectItem>
          </SelectContent>
        </Select>
        <Select value={String(pageSize)} onValueChange={(v) => setPageSize(Number(v))}>
          <SelectTrigger className="h-8 w-32"><SelectValue placeholder="Rows" /></SelectTrigger>
          <SelectContent>
            <SelectItem value="10">10 rows</SelectItem>
            <SelectItem value="25">25 rows</SelectItem>
            <SelectItem value="50">50 rows</SelectItem>
          </SelectContent>
        </Select>
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="outline" className="ml-auto h-8">Columns</Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end">
            {table
              .getAllColumns()
              .filter((column) => column.getCanHide())
              .map((column) => {
                return (
                  <DropdownMenuCheckboxItem
                    key={column.id}
                    className="capitalize"
                    checked={column.getIsVisible()}
                    onCheckedChange={(value) => column.toggleVisibility(!!value)}
                  >
                    {column.id}
                  </DropdownMenuCheckboxItem>
                );
              })}
          </DropdownMenuContent>
        </DropdownMenu>
        {selectedIds.length > 0 && (
          <AlertDialog>
            <AlertDialogTrigger asChild>
              <Button variant="destructive" className="h-8">Delete Selected ({selectedIds.length})</Button>
            </AlertDialogTrigger>
            <AlertDialogContent>
              <AlertDialogHeader>
                <AlertDialogTitle>Delete selected transactions?</AlertDialogTitle>
                <AlertDialogDescription>
                  This action cannot be undone.
                </AlertDialogDescription>
              </AlertDialogHeader>
              <AlertDialogFooter>
                <AlertDialogCancel>Cancel</AlertDialogCancel>
                <AlertDialogAction
                  className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
                  onClick={async () => {
                    for (const id of selectedIds) {
                      await api.tx.remove(id);
                    }
                    table.resetRowSelection();
                    onChanged?.();
                  }}
                >
                  Delete
                </AlertDialogAction>
              </AlertDialogFooter>
            </AlertDialogContent>
          </AlertDialog>
        )}
      </div>

      <Table>
        <TableHeader>
          {table.getHeaderGroups().map((headerGroup) => (
            <TableRow key={headerGroup.id} className="hover:bg-transparent">
              {headerGroup.headers.map((header) => (
                <TableHead
                  key={header.id}
                  onClick={header.column.getToggleSortingHandler?.()}
                  className="cursor-pointer select-none"
                >
                  {header.isPlaceholder
                    ? null
                    : flexRender(
                        header.column.columnDef.header,
                        header.getContext()
                      )}
                </TableHead>
              ))}
            </TableRow>
          ))}
        </TableHeader>
        <TableBody>
          {table.getRowModel().rows.map((row) => (
            <TableRow key={row.id} className="hover:bg-muted/50" data-state={row.getIsSelected() && "selected"}>
              {row.getVisibleCells().map((cell) => (
                <TableCell key={cell.id}>
                  {flexRender(cell.column.columnDef.cell, cell.getContext())}
                </TableCell>
              ))}
            </TableRow>
          ))}
        </TableBody>
      </Table>

      <div className="flex items-center justify-between">
        <div className="text-xs text-muted-foreground">
          Page {table.getState().pagination.pageIndex + 1} of {table.getPageCount() || 1}
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline" size="sm" onClick={() => table.previousPage()} disabled={!table.getCanPreviousPage()}>
            Prev
          </Button>
          <Button variant="outline" size="sm" onClick={() => table.nextPage()} disabled={!table.getCanNextPage()}>
            Next
          </Button>
        </div>
      </div>
    </div>
  );
}
