"use client";
import { useState } from "react";
import { API_URL } from "../services/api";

// Upload handling for PDF documents and photographs (PDF / JPEG / PNG / WebP).
// Posts multipart form data to POST /documents/upload. With no backend
// configured (NEXT_PUBLIC_API_URL unset) the form explains that instead
// of pretending an upload happened. Sample PDFs/photos are NOT in the
// repo — use your own test files, or the labelled .txt samples.
export default function UploadForm({ shipmentId }: { shipmentId: string }) {
  const [message, setMessage] = useState("");
  async function onSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    if (!API_URL) { setMessage("No backend configured — set NEXT_PUBLIC_API_URL to upload."); return; }
    const form = new FormData(e.currentTarget);
    form.set("shipment_id", shipmentId);
    const res = await fetch(`${API_URL}/documents/upload`, { method: "POST", body: form, headers: { "X-ClaimKit-Role": "staff" } });
    setMessage(res.ok ? "Upload recorded — see evidence list." : `Upload failed: ${await res.text()}`);
  }
  return (
    <form onSubmit={onSubmit} className="rounded-lg border bg-white p-4 shadow-sm">
      <h2 className="font-semibold">Upload document / photo — {shipmentId}</h2>
      <p className="text-sm text-slate-600">PDF, JPEG, PNG, or WebP, max 25 MB.</p>
      <div className="mt-2 flex gap-2">
        <input name="file" type="file" accept=".pdf,.jpg,.jpeg,.png,.webp,.txt" required className="text-sm" />
        <select name="kind" className="rounded border p-1 text-sm">
          <option value="bol">BOL</option><option value="pod">POD</option>
          <option value="invoice">Invoice</option><option value="receipt">Receipt</option>
          <option value="photo">Photo</option><option value="email">Email</option>
        </select>
        <button className="rounded bg-slate-900 px-3 py-1 text-sm text-white" type="submit">Upload</button>
      </div>
      {message && <p className="mt-2 text-sm">{message}</p>}
    </form>
  );
}
