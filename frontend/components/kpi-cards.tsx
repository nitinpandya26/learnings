import { Card } from "@/components/ui/card";

export type KPI = { income: number; expense: number; net: number; savings_rate: number };

export function KpiCards({ kpi }: { kpi: KPI }) {
  const entries = [
    ["Income", kpi.income],
    ["Expense", kpi.expense],
    ["Net", kpi.net],
    ["Savings Rate %", kpi.savings_rate]
  ];
  return (
    <div className="grid gap-4 md:grid-cols-4">
      {entries.map(([label, value]) => (
        <Card key={label as string}>
          <p className="text-xs text-slate-400">{label as string}</p>
          <p className="text-2xl font-bold">₹{Number(value).toLocaleString()}</p>
        </Card>
      ))}
    </div>
  );
}
