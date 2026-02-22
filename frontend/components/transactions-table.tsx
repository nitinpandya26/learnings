"use client";

import { useMemo } from "react";
import { ColumnDef, flexRender, getCoreRowModel, useReactTable } from "@tanstack/react-table";
import { Card } from "@/components/ui/card";

type Txn = {
  id: number;
  txn_date: string;
  txn_type: string;
  amount: number;
  payment_mode: string;
  counterparty?: string;
};

export function TransactionsTable({ rows }: { rows: Txn[] }) {
  const columns = useMemo<ColumnDef<Txn>[]>(
    () => [
      { header: "Date", accessorKey: "txn_date" },
      { header: "Type", accessorKey: "txn_type" },
      { header: "Amount", accessorKey: "amount" },
      { header: "Mode", accessorKey: "payment_mode" },
      { header: "Counterparty", accessorKey: "counterparty" }
    ],
    []
  );

  const table = useReactTable({ data: rows, columns, getCoreRowModel: getCoreRowModel() });

  return (
    <Card>
      <h3 className="mb-3 text-lg font-semibold">Transactions</h3>
      <table className="w-full text-sm">
        <thead>
          {table.getHeaderGroups().map((hg) => (
            <tr key={hg.id} className="border-b border-slate-800">
              {hg.headers.map((h) => (
                <th key={h.id} className="px-2 py-2 text-left text-slate-400">
                  {flexRender(h.column.columnDef.header, h.getContext())}
                </th>
              ))}
            </tr>
          ))}
        </thead>
        <tbody>
          {table.getRowModel().rows.map((r) => (
            <tr key={r.id} className="border-b border-slate-900">
              {r.getVisibleCells().map((c) => (
                <td key={c.id} className="px-2 py-2">
                  {flexRender(c.column.columnDef.cell, c.getContext())}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </Card>
  );
}
