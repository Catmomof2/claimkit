import Link from "next/link";

export default function Home() {
  return (
    <main className="mx-auto max-w-3xl p-6">
      <h1 className="text-3xl font-bold">ClaimKit</h1>
      <p className="mt-2">Automated business claims recovery for freight brokers — detention, delays, extra delivery costs, missed appointments, and unexpected transport costs, recovered from the documents you already have.</p>
      <p className="mt-4"><Link className="rounded bg-slate-900 px-4 py-2 text-white" href="/dashboard">Open the dashboard</Link></p>
      <p className="mt-4 text-sm text-slate-600">Sample data only in this starter. No real credentials or customer data.</p>
    </main>
  );
}
