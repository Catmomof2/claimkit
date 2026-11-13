"use client";
import { useState } from "react";
import { detentionAmount } from "../services/api";

export default function DetentionCalculator() {
  const [waited, setWaited] = useState(5.5);
  const [free, setFree] = useState(2);
  const [rate, setRate] = useState(75);
  const amount = detentionAmount(waited, free, rate);
  return (
    <section className="rounded-lg border bg-white p-4 shadow-sm">
      <h2 className="font-semibold">Detention calculator</h2>
      <p className="text-sm text-slate-600">Billable hours = max(0, waited − free) × hourly rate.</p>
      <div className="mt-2 grid grid-cols-3 gap-2">
        <label className="text-sm">Waited (h)<input className="w-full rounded border p-1" type="number" step="0.5" value={waited} onChange={(e) => setWaited(Number(e.target.value))} /></label>
        <label className="text-sm">Free (h)<input className="w-full rounded border p-1" type="number" step="0.5" value={free} onChange={(e) => setFree(Number(e.target.value))} /></label>
        <label className="text-sm">Rate ($/h)<input className="w-full rounded border p-1" type="number" value={rate} onChange={(e) => setRate(Number(e.target.value))} /></label>
      </div>
      <p className="mt-2 font-medium">Recoverable detention: ${amount.toFixed(2)}</p>
    </section>
  );
}
