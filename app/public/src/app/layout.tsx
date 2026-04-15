import type { Metadata } from "next";
import type { ReactNode } from "react";

import { PublicHeader } from "@/components/fpds/public/public-header";

import "./globals.css";

export const metadata: Metadata = {
  title: "FPDS Public",
  description: "FPDS public product catalog for Canada deposit products"
};

export default function RootLayout({ children }: Readonly<{ children: ReactNode }>) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-background text-foreground">
        <div className="relative isolate min-h-screen">
          <div className="pointer-events-none absolute inset-x-0 top-0 h-72 bg-[radial-gradient(circle_at_top,_rgb(67_56_202_/_0.12),_transparent_56%)]" />
          <PublicHeader />
          {children}
        </div>
      </body>
    </html>
  );
}
