import type { Metadata } from "next";
import type { ReactNode } from "react";

import { PublicFooter } from "@/components/fpds/public/public-footer";
import { PublicHeader } from "@/components/fpds/public/public-header";

import "./globals.css";

export const metadata: Metadata = {
  title: "FPDS",
  description: "FPDS deposit product catalog"
};

export default function RootLayout({ children }: Readonly<{ children: ReactNode }>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className="min-h-screen bg-background text-foreground">
        <div className="relative isolate min-h-screen">
          <PublicHeader />
          <div className="min-h-[calc(100vh-4rem)]">{children}</div>
          <PublicFooter />
        </div>
      </body>
    </html>
  );
}
