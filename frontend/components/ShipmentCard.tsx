import type { Charge, Shipment } from "../services/api";

export default function ShipmentCard({ shipment, charges }: { shipment: Shipment; charges: Charge[] }) {
  const total = charges.reduce((s, c) => s + c.amount, 0);
  return (
    <article className="rounded-lg border bg-white p-4 shadow-sm">
      <h3 className="font-semibold">{shipment.reference} — {shipment.origin} → {shipment.destination}</h3>
      <p className="text-sm text-slate-600">{shipment.carrier} · Pickup {shipment.pickup_date} · Delivery {shipment.delivery_date}</p>
      <ul className="mt-2 text-sm">
        {charges.map((c) => (
          <li key={c.id} className="flex justify-between"><span>{c.type.replaceAll("_", " ")} — {c.description}</span><span>${c.amount.toFixed(2)}</span></li>
        ))}
      </ul>
      <p className="mt-2 font-medium">Recoverable total: ${total.toFixed(2)}</p>
    </article>
  );
}
