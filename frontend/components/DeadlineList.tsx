import type { Claim } from "../services/api";

export default function DeadlineList({ claims }: { claims: Claim[] }) {
  const sorted = [...claims].sort((a, b) => a.filing_deadline.localeCompare(b.filing_deadline));
  return (
    <section className="rounded-lg border bg-white p-4 shadow-sm">
      <h2 className="font-semibold">Claim deadlines</h2>
      <ul className="mt-2 text-sm">
        {sorted.map((c) => (
          <li key={c.id} className="flex justify-between py-1 border-b last:border-0">
            <span>{c.id} — {c.counterparty} ({c.status})</span>
            <span>Due {c.filing_deadline} · ${c.total_claimed.toFixed(2)}</span>
          </li>
        ))}
      </ul>
    </section>
  );
}
