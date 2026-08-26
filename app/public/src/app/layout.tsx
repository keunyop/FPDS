import type { Metadata } from "next";
import { Suspense, type ReactNode } from "react";

import { PublicFooter } from "@/components/fpds/public/public-footer";
import { PublicHeader } from "@/components/fpds/public/public-header";
import { PublicLocaleSync } from "@/components/fpds/public/public-locale-sync";
import { AnalyticsConsent } from "@/components/fpds/public/analytics-consent";
import {
  PUBLIC_SITE_STRUCTURED_DATA,
  PublicStructuredData
} from "@/components/fpds/public/public-structured-data";
import { getGoogleAnalyticsMeasurementId } from "@/lib/google-analytics";
import { PUBLIC_SITE_ORIGIN } from "@/lib/public-seo";

import "./globals.css";

export const metadata: Metadata = {
  metadataBase: new URL(PUBLIC_SITE_ORIGIN),
  applicationName: "SwitchaBank",
  title: {
    default: "Compare Banks & Financial Products — SwitchaBank",
    template: "%s — SwitchaBank"
  },
  description: "Compare reviewed deposit, credit card, and loan facts across banks.",
  category: "finance",
  creator: "SwitchaBank",
  publisher: "SwitchaBank",
  manifest: "/manifest.webmanifest",
  referrer: "strict-origin-when-cross-origin",
  formatDetection: {
    address: false,
    email: false,
    telephone: false
  }
};

export default function RootLayout({ children }: Readonly<{ children: ReactNode }>) {
  const googleAnalyticsMeasurementId = getGoogleAnalyticsMeasurementId();

  return (
    <html lang="en" suppressHydrationWarning>
      <head>
        <script
          dangerouslySetInnerHTML={{
            __html: "(()=>{const l=new URLSearchParams(location.search).get('locale');document.documentElement.lang=l==='ko'||l==='ja'?l:'en'})()"
          }}
        />
      </head>
      <body className="min-h-screen bg-background text-foreground">
        <PublicStructuredData data={PUBLIC_SITE_STRUCTURED_DATA} />
        <Suspense fallback={null}>
          <PublicLocaleSync />
        </Suspense>
        <div className="relative isolate min-h-screen">
          <PublicHeader />
          <div className="min-h-[calc(100vh-4rem)]">{children}</div>
          <PublicFooter />
        </div>
        {googleAnalyticsMeasurementId ? (
          <Suspense fallback={null}>
            <AnalyticsConsent measurementId={googleAnalyticsMeasurementId} />
          </Suspense>
        ) : null}
      </body>
    </html>
  );
}
