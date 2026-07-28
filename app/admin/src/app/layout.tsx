import type { ReactNode } from "react";
import type { Metadata } from "next";
import { Suspense } from "react";

import { AdminLocaleDocumentSync } from "@/components/admin-locale-document-sync";
import { TooltipProvider } from "@/components/ui/tooltip";

import "./globals.css";

export const metadata: Metadata = {
  title: {
    default: "FPDS Admin",
    template: "%s · FPDS Admin",
  },
  description: "Evidence-backed financial product operations console"
};

export default function RootLayout({ children }: Readonly<{ children: ReactNode }>) {
  return (
    <html lang="en-CA" suppressHydrationWarning>
      <head>
        <script
          dangerouslySetInnerHTML={{
            __html: `(function(){try{var value=new URLSearchParams(location.search).get("locale");var locale=value==="ko"?"ko":value==="ja"?"ja":"en";document.documentElement.lang=locale==="ko"?"ko-KR":locale==="ja"?"ja-JP":"en-CA";document.documentElement.dataset.locale=locale;}catch(_){}})();`,
          }}
        />
      </head>
      <body className="min-h-screen bg-background text-foreground">
        <Suspense fallback={null}>
          <AdminLocaleDocumentSync />
        </Suspense>
        <TooltipProvider>{children}</TooltipProvider>
      </body>
    </html>
  );
}
