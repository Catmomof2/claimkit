import DeadlineList from "../../components/DeadlineList";
import DetentionCalculator from "../../components/DetentionCalculator";
import ShipmentCard from "../../components/ShipmentCard";
import UploadForm from "../../components/UploadForm";
import { SAMPLE_CHARGES, SAMPLE_CLAIMS, SAMPLE_SHIPMENTS } from "../../services/sample";

// Dashboard: shipments, recoverable totals, deadlines, claim status.
// Uses labelled SAMPLE data in the starter; with NEXT_PUBLIC_API_URL set,
// fetch the same shapes from GET /shipments, GET /claims, GET /deadlines.
export default function DashboardPage() {
  const recoverableTotal = SAMPLE_CHARGES.reduce((s, c) => s + c.amount, 0);
  const claimedTotal = SAMPLE_CLAIMS.reduce((s, c) => s + c.total_claimed, 0);
  return (
    <main className="mx-auto max-w-5xl p-6">
      <h1 className="text-3xl font-bold">ClaimKit dashboard</h1>
      <p className="text-sm text-slate-600">Sample data — clearly labelled, no real shipments.</p>
      <div className="mt-4 grid grid-cols-3 gap-4">
        <div className="rounded-lg border bg-white p-4"><p className="text-sm text-slate-600">Shipments</p><p className="text-2xl font-bold">{SAMPLE_SHIPMENTS.length}</p></div>
        <div className="rounded-lg border bg-white p-4"><p className="text-sm text-slate-600">Recoverable total</p><p className="text-2xl font-bold">${recoverableTotal.toFixed(2)}</p></div>
        <div className="rounded-lg border bg-white p-4"><p className="text-sm text-slate-600">Claimed total</p><p className="text-2xl font-bold">${claimedTotal.toFixed(2)}</p></div>
      </div>
      <div className="mt-4 grid gap-4 md:grid-cols-2">
        <DetentionCalculator />
        <DeadlineList claims={SAMPLE_CLAIMS} />
      </div>
      <div className="mt-4 grid gap-4">
        {SAMPLE_SHIPMENTS.map((s) => (
          <ShipmentCard key={s.id} shipment={s} charges={SAMPLE_CHARGES.filter((c) => c.shipment_id === s.id)} />
        ))}
      </div>
      <div className="mt-4">
        <UploadForm shipmentId="shp_001" />
      </div>
      <section className="mt-4 rounded-lg border bg-white p-4">
        <h2 className="font-semibold">Claim status</h2>
        <ul className="mt-2 text-sm">{SAMPLE_CLAIMS.map((c) => (<li key={c.id}>{c.id} — {c.status} — ${c.total_claimed.toFixed(2)} claimed, ${c.total_recovered.toFixed(2)} recovered — due {c.filing_deadline}</li>))}</ul>
      </section>
    </main>
  );
}
