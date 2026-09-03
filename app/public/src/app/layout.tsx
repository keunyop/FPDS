import type { Metadata } from "next";
import { headers } from "next/headers";
import { Suspense, type ReactNode } from "react";

import { PublicFooter } from "@/components/fpds/public/public-footer";
import { PublicHeader } from "@/components/fpds/public/public-header";
import { AnalyticsConsent } from "@/components/fpds/public/analytics-consent";
import {
  PUBLIC_SITE_STRUCTURED_DATA,
  PublicStructuredData
} from "@/components/fpds/public/public-structured-data";
import { getGoogleAnalyticsMeasurementId } from "@/lib/google-analytics";
import { PUBLIC_SITE_ORIGIN } from "@/lib/public-seo";
import { normalizePublicProductLocale } from "@/lib/public-url-policy";

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

export default async function RootLayout({ children }: Readonly<{ children: ReactNode }>) {
  const googleAnalyticsMeasurementId = getGoogleAnalyticsMeasurementId();
  const requestHeaders = await headers();
  const locale = normalizePublicProductLocale(
    requestHeaders.get("x-switchabank-public-locale") ?? ""
  );

  return (
    <html lang={locale} suppressHydrationWarning>
      <body className="min-h-screen bg-background text-foreground">
        <PublicStructuredData data={PUBLIC_SITE_STRUCTURED_DATA} />
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
