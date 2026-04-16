import type { ReactNode } from "react";
import type { Metadata } from "next";
import { Suspense } from "react";

import { AdminLocaleDocumentSync } from "@/components/admin-locale-document-sync";
import { TooltipProvider } from "@/components/ui/tooltip";

import "./globals.css";

export const metadata: Metadata = {
  title: "FPDS Admin",
  description: "FPDS admin console login and overview"
};

export default function RootLayout({ children }: Readonly<{ children: ReactNode }>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className="min-h-screen bg-background text-foreground">
        <Suspense fallback={null}>
          <AdminLocaleDocumentSync />
        </Suspense>
        <TooltipProvider>{children}</TooltipProvider>
      </body>
    </html>
  );
}
