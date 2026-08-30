import type { Metadata } from 'next';
import { cookies } from 'next/headers';
import type { ReactNode } from 'react';

import {
  PUBLIC_ADMIN_COOKIE_NAME,
  publicAdminIsConfigured,
  verifyPublicAdminSession
} from '@/lib/public-admin-auth';
import { getPublicApiOrigin } from '@/lib/public-api';

export const dynamic = 'force-dynamic';

export const metadata: Metadata = {
  title: 'Public analytics admin',
  robots: { follow: false, index: false }
};

type AdminPageProps = {
  searchParams?: Promise<Record<string, string | string[] | undefined>>;
};

type EngagementRow = {
  bank_code: string;
  bank_name: string;
  country_code: string;
  finder_product_selections: number;
  official_bank_clicks: number;
  product_detail_clicks: number;
  product_id: string;
  product_name: string;
  product_type: string;
};

type EngagementSummary = {
  banks: Array<{
    bank_code: string;
    bank_name: string;
    country_code: string;
    finder_product_selections: number;
    official_bank_clicks: number;
    product_detail_clicks: number;
  }>;
  country_code: string | null;
  daily: Array<{
    event_date: string;
    finder_product_selections: number;
    official_bank_clicks: number;
    product_detail_clicks: number;
  }>;
  products: EngagementRow[];
  retention_days: number;
  totals: {
    finder_product_selections: number;
    first_event_date: string | null;
    last_recorded_at: string | null;
    official_bank_clicks: number;
    product_detail_clicks: number;
    published_products: number;
  };
};

export default async function PublicAdminPage({ searchParams }: AdminPageProps) {
  const resolvedSearchParams = (await searchParams) ?? {};
  const cookieStore = await cookies();
  const authenticated = verifyPublicAdminSession(
    cookieStore.get(PUBLIC_ADMIN_COOKIE_NAME)?.value
  );
  if (!authenticated) {
    return (
      <LoginPanel
        configured={publicAdminIsConfigured()}
        error={singleValue(resolvedSearchParams.error)}
      />
    );
  }

  const requestedCountry = singleValue(resolvedSearchParams.country_code).toUpperCase();
  const countryCode = /^[A-Z]{2}$/.test(requestedCountry) ? requestedCountry : '';
  const summary = await loadEngagementSummary(countryCode);

  return (
    <main className='mx-auto w-full max-w-7xl px-4 py-8 md:px-6 md:py-12'>
      <div className='flex flex-col gap-8'>
        <header className='flex flex-col gap-4 border-b border-foreground/15 pb-6 sm:flex-row sm:items-end sm:justify-between'>
          <div>
            <p className='font-mono text-[10px] font-semibold uppercase tracking-[0.14em] text-verification'>Private · aggregate only</p>
            <h1 className='mt-2 font-display text-4xl font-semibold tracking-[-0.05em] md:text-5xl'>Public product analytics</h1>
            <p className='mt-3 max-w-3xl text-sm leading-6 text-muted-foreground'>
              Daily product counters only. No visitor identity, IP address, cookie, free-text query, or financial profile is stored.
            </p>
          </div>
          <form action='/admin/logout' method='post'>
            <button className='inline-flex min-h-11 items-center rounded-lg border border-border bg-background px-4 text-sm font-semibold hover:bg-muted' type='submit'>Sign out</button>
          </form>
        </header>

        <form className='flex flex-wrap items-end gap-3' method='get'>
          <label className='grid gap-1.5 text-sm font-semibold'>
            Country
            <select className='h-11 rounded-lg border border-input bg-background px-3 font-normal' defaultValue={countryCode} name='country_code'>
              <option value=''>All countries</option>
              <option value='CA'>Canada</option>
              <option value='US'>United States</option>
            </select>
          </label>
          <button className='inline-flex min-h-11 items-center rounded-lg bg-primary px-4 text-sm font-semibold text-primary-foreground' type='submit'>Apply</button>
        </form>

        {summary ? <SummaryContent summary={summary} /> : (
          <section className='border border-destructive/25 bg-destructive/5 p-5'>
            <h2 className='font-semibold text-destructive'>Analytics are temporarily unavailable</h2>
            <p className='mt-2 text-sm text-muted-foreground'>Check the Public API credential, API deployment, and database migration.</p>
          </section>
        )}
      </div>
    </main>
  );
}

function LoginPanel({ configured, error }: { configured: boolean; error: string }) {
  const message = !configured || error === 'config'
    ? 'Public Admin authentication is not configured.'
    : error === 'rate'
      ? 'Too many failed attempts. Try again in 15 minutes.'
      : error === 'invalid'
        ? 'The password is incorrect.'
        : '';
  return (
    <main className='mx-auto grid min-h-[70vh] w-full max-w-md place-items-center px-4 py-10'>
      <section className='w-full rounded-xl border border-foreground/15 bg-card/85 p-6 shadow-[0_18px_48px_rgba(28,39,35,0.08)]'>
        <p className='font-mono text-[10px] font-semibold uppercase tracking-[0.14em] text-verification'>Private access</p>
        <h1 className='mt-2 text-2xl font-semibold tracking-[-0.03em]'>Public analytics admin</h1>
        <p className='mt-2 text-sm leading-6 text-muted-foreground'>Enter the administrator password to continue.</p>
        <form action='/admin/login' className='mt-5 grid gap-4' method='post'>
          <label className='grid gap-1.5 text-sm font-semibold'>
            Password
            <input
              autoComplete='current-password'
              className='h-12 rounded-lg border border-input bg-background px-3 font-normal outline-none focus-visible:border-ring focus-visible:ring-3 focus-visible:ring-ring/50'
              disabled={!configured}
              maxLength={256}
              name='password'
              required
              type='password'
            />
          </label>
          {message ? <p aria-live='polite' className='text-sm text-destructive'>{message}</p> : null}
          <button className='inline-flex min-h-11 items-center justify-center rounded-lg bg-primary px-4 text-sm font-semibold text-primary-foreground disabled:opacity-50' disabled={!configured} type='submit'>Sign in</button>
        </form>
      </section>
    </main>
  );
}

function SummaryContent({ summary }: { summary: EngagementSummary }) {
  const holderRows = [...summary.products].sort((left, right) =>
    right.finder_product_selections - left.finder_product_selections
    || left.product_name.localeCompare(right.product_name)
  );
  return (
    <>
      <section className='grid gap-3 sm:grid-cols-2 xl:grid-cols-4'>
        <Metric label='Product clicks' value={summary.totals.product_detail_clicks} />
        <Metric label='Official-bank visits' value={summary.totals.official_bank_clicks} />
        <Metric label='My product selections' value={summary.totals.finder_product_selections} />
        <Metric label='Published products' value={summary.totals.published_products} />
      </section>

      <section>
        <h2 className='text-xl font-semibold tracking-[-0.02em]'>Most selected as My product</h2>
        <p className='mt-1 text-sm text-muted-foreground'>Selections are a usage proxy, not a count of unique customers or verified ownership.</p>
        <ProductTable rows={holderRows} />
      </section>

      <section>
        <h2 className='text-xl font-semibold tracking-[-0.02em]'>Product engagement</h2>
        <ProductTable rows={summary.products} />
      </section>

      <section>
        <h2 className='text-xl font-semibold tracking-[-0.02em]'>Bank engagement</h2>
        <div className='mt-3 overflow-x-auto border border-border'>
          <table className='w-full min-w-[46rem] text-left text-sm'>
            <thead className='bg-muted/60 text-xs text-muted-foreground'>
              <tr><Th>Bank</Th><Th>Country</Th><Th>Product clicks</Th><Th>Official visits</Th><Th>My product</Th></tr>
            </thead>
            <tbody className='divide-y divide-border'>
              {summary.banks.map((row) => (
                <tr key={row.country_code + '-' + row.bank_code}>
                  <Td>{row.bank_name}</Td><Td>{row.country_code}</Td><Td>{row.product_detail_clicks}</Td><Td>{row.official_bank_clicks}</Td><Td>{row.finder_product_selections}</Td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <section>
        <h2 className='text-xl font-semibold tracking-[-0.02em]'>Last 30 days</h2>
        <div className='mt-3 overflow-x-auto border border-border'>
          <table className='w-full min-w-[40rem] text-left text-sm'>
            <thead className='bg-muted/60 text-xs text-muted-foreground'>
              <tr><Th>Date</Th><Th>Product clicks</Th><Th>Official visits</Th><Th>My product</Th></tr>
            </thead>
            <tbody className='divide-y divide-border'>
              {summary.daily.map((row) => (
                <tr key={row.event_date}>
                  <Td>{row.event_date}</Td><Td>{row.product_detail_clicks}</Td><Td>{row.official_bank_clicks}</Td><Td>{row.finder_product_selections}</Td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <p className='mt-3 text-xs leading-5 text-muted-foreground'>
          Counters are retained for {summary.retention_days} days. First recorded: {summary.totals.first_event_date ?? '—'}. Last recorded: {summary.totals.last_recorded_at ?? '—'}.
        </p>
      </section>
    </>
  );
}

function ProductTable({ rows }: { rows: EngagementRow[] }) {
  return (
    <div className='mt-3 max-h-[34rem] overflow-auto border border-border'>
      <table className='w-full min-w-[58rem] text-left text-sm'>
        <thead className='sticky top-0 bg-muted text-xs text-muted-foreground'>
          <tr><Th>Product</Th><Th>Bank</Th><Th>Type</Th><Th>Country</Th><Th>Product clicks</Th><Th>Official visits</Th><Th>My product</Th></tr>
        </thead>
        <tbody className='divide-y divide-border'>
          {rows.map((row) => (
            <tr key={row.country_code + '-' + row.product_id}>
              <Td>{row.product_name}</Td><Td>{row.bank_name}</Td><Td>{row.product_type}</Td><Td>{row.country_code}</Td><Td>{row.product_detail_clicks}</Td><Td>{row.official_bank_clicks}</Td><Td>{row.finder_product_selections}</Td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function Metric({ label, value }: { label: string; value: number }) {
  return <article className='border border-foreground/15 bg-card/75 p-4'><p className='text-xs font-semibold text-muted-foreground'>{label}</p><p className='mt-2 font-display text-3xl font-semibold tabular-nums'>{value.toLocaleString()}</p></article>;
}
function Th({ children }: { children: ReactNode }) { return <th className='whitespace-nowrap px-3 py-3 font-semibold'>{children}</th>; }
function Td({ children }: { children: ReactNode }) { return <td className='px-3 py-3 tabular-nums'>{children}</td>; }
function singleValue(value: string | string[] | undefined) { return Array.isArray(value) ? value[0] ?? '' : value ?? ''; }

async function loadEngagementSummary(countryCode: string): Promise<EngagementSummary | null> {
  const apiSecret = process.env.FPDS_PUBLIC_APP_API_SECRET?.trim();
  if (!apiSecret) return null;
  const url = new URL('/api/public/admin/engagement-summary', getPublicApiOrigin());
  if (countryCode) url.searchParams.set('country_code', countryCode);
  try {
    const response = await fetch(url, {
      cache: 'no-store',
      headers: { 'x-fpds-public-app-secret': apiSecret }
    });
    if (!response.ok) return null;
    const payload = await response.json() as { data?: EngagementSummary };
    return payload.data ?? null;
  } catch {
    return null;
  }
}
