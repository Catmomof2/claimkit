// Clearly labelled SAMPLE data, used when no backend is configured
// (NEXT_PUBLIC_API_URL unset). No real shipments, customers, or amounts.
import type { Charge, Claim, Shipment } from "./api";

export const SAMPLE_SHIPMENTS: Shipment[] = [
  { id: "shp_001", reference: "SAMPLE-1001", origin: "Tacoma, WA", destination: "Portland, OR", carrier: "Sample Carrier LLC", pickup_date: "2026-11-03", delivery_date: "2026-11-04" },
  { id: "shp_002", reference: "SAMPLE-1002", origin: "Spokane, WA", destination: "Boise, ID", carrier: "Sample Carrier LLC", pickup_date: "2026-11-05", delivery_date: "2026-11-06" },
  { id: "shp_003", reference: "SAMPLE-1003", origin: "Lakewood, WA", destination: "Seattle, WA", carrier: "Sample Carrier LLC", pickup_date: "2026-11-07", delivery_date: "2026-11-07" },
];
export const SAMPLE_CHARGES: Charge[] = [
  { id: "chg_001", shipment_id: "shp_001", type: "detention", description: "Detention at delivery: waited 5.5h, 2h free", amount: 262.5, basis: "3.5 billable hrs x $75/hr", status: "included" },
  { id: "chg_002", shipment_id: "shp_001", type: "additional_delivery", description: "Re-delivery fee after missed dock appointment", amount: 185, basis: "Receipt: re-delivery invoice", status: "included" },
  { id: "chg_003", shipment_id: "shp_002", type: "loading_delay", description: "Loading delay: 4h at shipper, 1h free", amount: 195, basis: "3.0 billable hrs x $65/hr", status: "evidence_missing" },
  { id: "chg_004", shipment_id: "shp_003", type: "missed_appointment", description: "Missed delivery appointment (no fault of carrier)", amount: 250, basis: "Contract accessorial schedule", status: "identified" },
];
export const SAMPLE_CLAIMS: Claim[] = [
  { id: "clm_001", shipment_id: "shp_001", counterparty: "Sample Shipper Inc.", status: "ready", filing_deadline: "2026-12-04", total_claimed: 447.5, total_recovered: 0 },
  { id: "clm_002", shipment_id: "shp_002", counterparty: "Sample Shipper Inc.", status: "draft", filing_deadline: "2026-11-20", total_claimed: 195, total_recovered: 0 },
  { id: "clm_003", shipment_id: "shp_003", counterparty: "Sample Receiver Co.", status: "draft", filing_deadline: "2026-11-18", total_claimed: 250, total_recovered: 0 },
];
