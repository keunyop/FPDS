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
    <html lang="en" suppressHydrationWarning>
      <body className="min-h-screen bg-background text-foreground">
        <div className="relative isolate min-h-screen">
          <PublicHeader />
          {children}
        </div>
      </body>
    </html>
  );
}
