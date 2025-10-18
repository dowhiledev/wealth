"use client";
import * as React from "react";
import {
  ColumnDef,
  ColumnFiltersState,
  SortingState,
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
import { formatAmount } from "@/lib/utils";
import type { Tx } from "@/lib/api";

type Row = Tx;

const columns: ColumnDef<Row>[] = [
  { accessorKey: "id", header: "ID" },
  {
    accessorKey: "ts",
    header: "Time",
    cell: ({ row }) => new Date(row.original.ts).toLocaleString(),
    sortingFn: (a, b) => new Date(a.original.ts).getTime() - new Date(b.original.ts).getTime(),
  },
  { accessorKey: "account_id", header: "Acct" },
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
];

export function TransactionsTable({ rows }: { rows: Row[] }) {
  const [sorting, setSorting] = React.useState<SortingState>([{ id: "ts", desc: true }]);
  const [columnFilters, setColumnFilters] = React.useState<ColumnFiltersState>([]);
  const [pageSize, setPageSize] = React.useState<number>(10);

  const table = useReactTable({
    data: rows,
    columns,
    state: { sorting, columnFilters, pagination: { pageIndex: 0, pageSize } },
    onSortingChange: setSorting,
    onColumnFiltersChange: setColumnFilters,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
    getFilteredRowModel: getFilteredRowModel(),
    getPaginationRowModel: getPaginationRowModel(),
  });

  const assetFilter = table.getColumn("asset_symbol");
  const sideFilter = table.getColumn("side");

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
            <TableRow key={row.id} className="hover:bg-muted/50">
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
