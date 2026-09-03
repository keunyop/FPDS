'use client';

import Script from 'next/script';
import { usePathname, useSearchParams } from 'next/navigation';
import { useCallback, useEffect, useRef, useState } from 'react';
import { createPortal } from 'react-dom';

import { getPublicAnalyticsConsentCopy, normalizePublicLocale } from '@/lib/public-locale';

const ANALYTICS_CONSENT_STORAGE_KEY = 'switchabank.analytics-consent.v1';

type AnalyticsConsentStatus = 'denied' | 'granted';
type Gtag = (...args: unknown[]) => void;

declare global {
  interface Window {
    dataLayer?: unknown[];
    gtag?: Gtag;
  }
}

function initializeGtag(): Gtag {
  window.dataLayer ??= [];
  window.gtag ??= function gtag(...args: unknown[]) {
    window.dataLayer?.push(args);
  };

  return window.gtag;
}

function grantAnalyticsConsent(command: 'default' | 'update') {
  const gtag = initializeGtag();
  gtag('consent', command, {
    ad_personalization: 'denied',
    ad_storage: 'denied',
    ad_user_data: 'denied',
    analytics_storage: 'granted'
  });
  gtag('set', 'allow_ad_personalization_signals', false);
  gtag('set', 'allow_google_signals', false);
}

function revokeAnalyticsConsent() {
  window.gtag?.('consent', 'update', {
    ad_personalization: 'denied',
    ad_storage: 'denied',
    ad_user_data: 'denied',
    analytics_storage: 'denied'
  });
}

function removeGoogleAnalyticsCookies() {
  const cookieNames = document.cookie
    .split(';')
    .map((cookie) => cookie.split('=', 1)[0]?.trim())
    .filter((name): name is string => Boolean(name && (name === '_ga' || name.startsWith('_ga_'))));

  const hostParts = window.location.hostname.split('.');
  const rootDomain = hostParts.length >= 2 ? hostParts.slice(-2).join('.') : window.location.hostname;
  const domainAttributes = ['', `; Domain=${window.location.hostname}`, `; Domain=${rootDomain}`, `; Domain=.${rootDomain}`];

  for (const name of cookieNames) {
    for (const domainAttribute of domainAttributes) {
      document.cookie = `${name}=; Max-Age=0; Path=/; SameSite=Lax${domainAttribute}`;
    }
  }
}

function readStoredConsent(): AnalyticsConsentStatus | null {
  try {
    const value = window.localStorage.getItem(ANALYTICS_CONSENT_STORAGE_KEY);
    return value === 'granted' || value === 'denied' ? value : null;
  } catch {
    return null;
  }
}

function storeConsent(value: AnalyticsConsentStatus) {
  try {
    window.localStorage.setItem(ANALYTICS_CONSENT_STORAGE_KEY, value);
  } catch {
    // The current-session choice still applies when browser storage is unavailable.
  }
}

export function AnalyticsConsent({ measurementId }: Readonly<{ measurementId: string }>) {
  const pathname = usePathname();
  const isAdminPath = pathname === '/admin' || pathname.startsWith('/admin/');
  const searchParams = useSearchParams();
  const locale = normalizePublicLocale(searchParams.get('locale') ?? '');
  const copy = getPublicAnalyticsConsentCopy(locale);
  const [consent, setConsent] = useState<AnalyticsConsentStatus | null>(null);
  const [footer, setFooter] = useState<HTMLElement | null>(null);
  const [isReady, setIsReady] = useState(false);
  const [isOpen, setIsOpen] = useState(false);
  const previousPageLocation = useRef<string | null>(null);

  const enableAnalytics = useCallback(
    (command: 'default' | 'update') => {
      grantAnalyticsConsent(command);

      if (command === 'default') {
        const gtag = initializeGtag();
        gtag('js', new Date());
        gtag('config', measurementId, { send_page_view: false });
      }
    },
    [measurementId]
  );

  useEffect(() => {
    if (isAdminPath) {
      setIsReady(true);
      return;
    }
    const storedConsent = readStoredConsent();
    if (storedConsent === 'granted') {
      enableAnalytics('default');
    }

    setConsent(storedConsent);
    setIsOpen(storedConsent === null);
    setIsReady(true);
  }, [enableAnalytics, isAdminPath]);

  useEffect(() => {
    if (isAdminPath) return;
    setFooter(document.querySelector('footer'));
  }, [isAdminPath]);

  useEffect(() => {
    if (isAdminPath || consent !== 'granted') {
      return;
    }

    const timeoutId = window.setTimeout(() => {
      const pageLocation = window.location.href;
      const pageTitle = document.title;
      const gtag = initializeGtag();

      gtag('config', measurementId, {
        page_location: pageLocation,
        page_title: pageTitle,
        update: true
      });
      gtag('event', 'page_view', {
        page_location: pageLocation,
        page_title: pageTitle,
        ...(previousPageLocation.current ? { page_referrer: previousPageLocation.current } : {})
      });
      previousPageLocation.current = pageLocation;
    }, 0);

    return () => window.clearTimeout(timeoutId);
  }, [consent, isAdminPath, measurementId, pathname, searchParams]);

  const allowAnalytics = useCallback(() => {
    enableAnalytics(consent === 'granted' ? 'update' : 'default');
    storeConsent('granted');
    setConsent('granted');
    setIsOpen(false);
  }, [consent, enableAnalytics]);

  const declineAnalytics = useCallback(() => {
    const analyticsWasLoaded = consent === 'granted';
    if (analyticsWasLoaded) {
      revokeAnalyticsConsent();
      removeGoogleAnalyticsCookies();
    }

    storeConsent('denied');
    setConsent('denied');
    setIsOpen(false);

    if (analyticsWasLoaded) {
      window.location.reload();
    }
  }, [consent]);

  if (!isReady || isAdminPath) {
    return null;
  }

  return (
    <>
      {consent === 'granted' ? (
        <Script
          id='google-analytics'
          src={`https://www.googletagmanager.com/gtag/js?id=${measurementId}`}
          strategy='afterInteractive'
        />
      ) : null}
      {footer
        ? createPortal(
            <div className='border-t border-background/15 px-4 py-3 md:px-6'>
              <div className='mx-auto flex w-full max-w-7xl justify-end'>
                <button
                  className='inline-flex min-h-11 items-center justify-center text-xs font-medium text-background/70 transition-colors hover:text-background'
                  onClick={() => setIsOpen(true)}
                  type='button'
                >
                  {copy.choices}
                </button>
              </div>
            </div>,
            footer
          )
        : null}
      {isOpen ? (
        <section
          aria-labelledby='analytics-consent-title'
          className='fixed inset-x-3 bottom-3 z-50 mx-auto max-w-3xl rounded-xl border border-foreground/20 bg-popover p-4 text-popover-foreground shadow-2xl shadow-foreground/15 sm:bottom-5 sm:p-5'
        >
          <div className='flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between'>
            <div className='max-w-2xl'>
              <h2 id='analytics-consent-title' className='text-base font-semibold tracking-[-0.01em]'>
                {copy.title}
              </h2>
              <p className='mt-1 text-sm leading-6 text-muted-foreground'>{copy.description}</p>
            </div>
            <div className='flex shrink-0 flex-col-reverse gap-2 min-[420px]:flex-row'>
              <button
                className='inline-flex min-h-11 items-center justify-center rounded-md border border-input bg-background px-4 text-sm font-semibold text-foreground transition-colors hover:bg-muted'
                onClick={declineAnalytics}
                type='button'
              >
                {copy.decline}
              </button>
              <button
                className='inline-flex min-h-11 items-center justify-center rounded-md bg-primary px-4 text-sm font-semibold text-primary-foreground transition-colors hover:bg-primary/90'
                onClick={allowAnalytics}
                type='button'
              >
                {copy.allow}
              </button>
            </div>
          </div>
        </section>
      ) : null}
    </>
  );
}
