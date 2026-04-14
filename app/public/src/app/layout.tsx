import type { Metadata } from "next";
import type { ReactNode } from "react";
import Link from "next/link";

import { PublicNav } from "@/components/fpds/public/public-nav";

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
          <header className="sticky top-0 z-30 border-b border-border/70 bg-background/88 backdrop-blur-xl">
            <div className="mx-auto flex w-full max-w-7xl items-center justify-between px-4 py-4 md:px-6">
              <div>
                <Link href="/products" className="text-sm font-semibold tracking-[0.18em] text-primary uppercase">
                  FPDS Public
                </Link>
                <p className="mt-1 text-sm text-muted-foreground">Canada deposit product catalog and comparison surface</p>
              </div>
              <PublicNav />
            </div>
          </header>
          {children}
        </div>
      </body>
    </html>
  );
}
