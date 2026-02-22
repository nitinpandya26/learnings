"use client";

import { Card } from "@/components/ui/card";
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

type Txn = { txn_type: string; amount: number };

export function ExpenseChart({ rows }: { rows: Txn[] }) {
  const expense = rows.filter((r) => r.txn_type === "expense").reduce((a, b) => a + b.amount, 0);
  const income = rows.filter((r) => r.txn_type === "income").reduce((a, b) => a + b.amount, 0);
  const data = [
    { name: "Income", amount: income },
    { name: "Expense", amount: expense }
  ];

  return (
    <Card>
      <h3 className="mb-3 text-lg font-semibold">Income vs Expense</h3>
      <div className="h-72">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data}>
            <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
            <XAxis dataKey="name" stroke="#cbd5e1" />
            <YAxis stroke="#cbd5e1" />
            <Tooltip />
            <Bar dataKey="amount" fill="#06b6d4" radius={[8, 8, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </Card>
  );
}
