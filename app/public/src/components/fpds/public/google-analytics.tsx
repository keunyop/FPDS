'use client';

import Script from 'next/script';
import { usePathname, useSearchParams } from 'next/navigation';
import { useEffect, useRef, useState } from 'react';
import { getAnalyticsPage } from '@/lib/google-analytics';

type Gtag = (...args: unknown[]) => void;
declare global {
  interface Window { dataLayer?: unknown[]; gtag?: Gtag; }
}

export function GoogleAnalytics({ measurementId }: Readonly<{ measurementId: string }>) {
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const [readyId, setReadyId] = useState<string | null>(null);
  const initializedId = useRef<string | null>(null);

  useEffect(() => {
    const page = getAnalyticsPage(pathname);
    if (!page) return;
    window.dataLayer ??= [];
    window.gtag ??= function () {
      // Google's command queue expects an Arguments object.
      // eslint-disable-next-line prefer-rest-params
      window.dataLayer?.push(arguments);
    };
    const gtag = window.gtag;
    if (initializedId.current !== measurementId) {
      gtag('consent', 'default', {
        ad_personalization: 'denied', ad_storage: 'denied', ad_user_data: 'denied',
        analytics_storage: 'granted'
      });
      gtag('set', 'allow_ad_personalization_signals', false);
      gtag('set', 'allow_google_signals', false);
      gtag('set', page);
      gtag('js', new Date());
      gtag('config', measurementId, { ...page, send_page_view: false });
      initializedId.current = measurementId;
      setReadyId(measurementId);
    }
    const timeoutId = window.setTimeout(() => {
      gtag('set', page);
      gtag('config', measurementId, { ...page, send_page_view: false, update: true });
      gtag('event', 'page_view', page);
    }, 0);
    return () => window.clearTimeout(timeoutId);
  }, [measurementId, pathname, searchParams]);

  if (!getAnalyticsPage(pathname) || readyId !== measurementId) return null;
  return <Script id='google-analytics'
    src={`https://www.googletagmanager.com/gtag/js?id=${measurementId}`}
    referrerPolicy='no-referrer' strategy='afterInteractive' />;
}
