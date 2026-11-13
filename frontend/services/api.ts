// Typed API client for the ClaimKit FastAPI backend.
// Set NEXT_PUBLIC_API_URL=http://localhost:8000 to use a live backend;
// otherwise callers fall back to the labelled sample data in lib/sample.ts.
export const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "";

export type Shipment = {
  id: string; reference: string; origin: string; destination: string;
  carrier: string; pickup_date: string; delivery_date: string;
};
export type Charge = {
  id: string; shipment_id: string; type: string; description: string;
  amount: number; basis?: string | null; status: string;
};
export type Claim = {
  id: string; shipment_id: string; counterparty: string; status: string;
  filing_deadline: string; total_claimed: number; total_recovered: number;
};

export async function fetchJson<T>(path: string, role = "viewer"): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, {
    headers: { "X-ClaimKit-Role": role },
  });
  if (!res.ok) throw new Error(`ClaimKit API ${res.status}: ${await res.text()}`);
  return res.json() as Promise<T>;
}

export function detentionAmount(waitedHours: number, freeHours: number, hourlyRate: number): number {
  return Math.round(Math.max(0, waitedHours - freeHours) * hourlyRate * 100) / 100;
}
