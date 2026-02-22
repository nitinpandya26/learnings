import { ExpenseChart } from "@/components/expense-chart";
import { KpiCards } from "@/components/kpi-cards";
import { TransactionsTable } from "@/components/transactions-table";
import { fetchJson } from "@/lib/api";

export default async function Page() {
  const [kpi, txns] = await Promise.all([
    fetchJson<{ income: number; expense: number; net: number; savings_rate: number }>("/dashboard/kpis"),
    fetchJson<any[]>("/transactions")
  ]);

  return (
    <main className="mx-auto max-w-7xl space-y-6 p-6">
      <section className="rounded-2xl border border-slate-800 bg-gradient-to-r from-slate-900 to-slate-800 p-6">
        <h1 className="text-3xl font-bold">Expense Manager 2.0</h1>
        <p className="text-slate-400">Next.js + FastAPI + PostgreSQL architecture with analytics-ready UI.</p>
      </section>
      <KpiCards kpi={kpi} />
      <div className="grid gap-6 lg:grid-cols-2">
        <ExpenseChart rows={txns} />
        <TransactionsTable rows={txns} />
      </div>
    </main>
  );
}
