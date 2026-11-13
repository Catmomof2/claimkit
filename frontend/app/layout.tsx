import "./globals.css";
import type { ReactNode } from "react";

export const metadata = { title: "ClaimKit — Claims Recovery", description: "Automated business claims recovery for freight brokers." };

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body className="bg-slate-50 text-slate-900">{children}</body>
    </html>
  );
}
