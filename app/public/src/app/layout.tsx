import type { Metadata } from "next";
import { Suspense, type ReactNode } from "react";

import { PublicFooter } from "@/components/fpds/public/public-footer";
import { PublicHeader } from "@/components/fpds/public/public-header";
import { PublicLocaleSync } from "@/components/fpds/public/public-locale-sync";
import { AnalyticsConsent } from "@/components/fpds/public/analytics-consent";
import { getGoogleAnalyticsMeasurementId } from "@/lib/google-analytics";

import "./globals.css";

export const metadata: Metadata = {
  applicationName: "SwitchaBank",
  title: {
    default: "SwitchaBank — Compare banks. Switch smarter.",
    template: "%s — SwitchaBank"
  },
  description: "Compare reviewed deposit, credit card, and loan facts across banks."
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
