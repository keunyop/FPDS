import type { PublicProduct, PublicProductsResponse } from './public-api.ts';
import { depositOptions } from './public-deposit.ts';
import { verificationStatus } from './public-verification.ts';
import { buildProductDetailPath } from './public-url-policy.ts';

// Editorial launch threshold, not a search-engine requirement.
export const CURATED_MIN_BANKS = 3;
export const CURATED_PAGES = {
  'savings-accounts': { productType: 'savings' },
  'no-monthly-fee-chequing': { productType: 'chequing' },
  '1-year-gic': { productType: 'gic' }
} as const;
export type CuratedSlug = keyof typeof CURATED_PAGES;
export type CuratedPath = `/ca/${CuratedSlug}`;
export type CuratedGroup = { key: string; products: PublicProduct[] };
export type CuratedComparison = { slug: CuratedSlug; ready: boolean; bankCount: number; groups: CuratedGroup[] };
export function isCuratedSlug(value: string): value is CuratedSlug {
  return Object.hasOwn(CURATED_PAGES, value);
}
export function curatedHref(slug: CuratedSlug, locale: string) {
  return `/ca/${slug}${locale === 'ko' || locale === 'ja' ? `?locale=${locale}` : ''}`;
}
export function curatedCatalogHref(slug: CuratedSlug, locale: string, country = 'CA') {
  const params = new URLSearchParams({ product_type: CURATED_PAGES[slug].productType });
  if (locale === 'ko' || locale === 'ja') params.set('locale', locale);
  if (country !== 'CA') params.set('country_code', country);
  if (slug === 'no-monthly-fee-chequing') { params.set('sort_by', 'monthly_fee'); params.set('sort_order', 'asc'); }
  return `/products?${params}`;
}
export function curatedCountryPath(path: string, country: string) {
  const slug = path.slice('/ca/'.length);
  return path.startsWith('/ca/') && isCuratedSlug(slug) && country !== 'CA' ? '/products' : path;
}
export function isCuratedIndexableQuery(params: Record<string, string | string[] | undefined>) {
  return Object.entries(params).every(([key, value]) => key === 'locale' && typeof value === 'string' && ['en', 'ko', 'ja'].includes(value));
}
function finiteAmount(value: unknown): value is number {
  return typeof value === 'number' && Number.isFinite(value) && value >= 0;
}
function officialUrl(value: string | null) {
  try { const url = new URL(value ?? ''); return ['https:', 'http:'].includes(url.protocol) && !url.username && !url.password; }
  catch { return false; }
}
function eligible(product: PublicProduct, now: number) {
  const status = verificationStatus(product.verification, now);
  return product.status === 'active' && product.country_code === 'CA' && product.currency === 'CAD'
    && Boolean(product.bank_code?.trim()) && officialUrl(product.product_url)
    && (status === 'within_window' || status === 'review_due');
}
const bankCount = (products: PublicProduct[]) => new Set(products.map(p => p.bank_code.trim().toUpperCase())).size;

/** The same gate owns page content, Home links and sitemap inclusion. No data writes. */
export function buildCuratedComparison(slug: CuratedSlug, products: PublicProduct[], now = Date.now()): CuratedComparison {
  const candidates = products.filter(p => eligible(p, now) && p.product_type === CURATED_PAGES[slug].productType)
    // Honor the existing confirmed-duplicate policy; never attach stale facts to its replacement URL.
    .filter(p => buildProductDetailPath(`/products/${p.product_id}`, 'en', 'CA') === `/products/${p.product_id}`)
    .sort((a, b) => Date.parse(b.verification!.last_verified_at!) - Date.parse(a.verification!.last_verified_at!) || a.product_id.localeCompare(b.product_id));
  const seen = new Set<string>();
  const scoped = candidates.filter(p => {
    // Collapse exact-source duplicates only when all comparison facts also agree.
    const key = JSON.stringify([p.bank_code, p.product_url, p.currency, p.subtype_code,
      p.public_display_fee, p.fee_waiver_condition, p.standard_rate, p.rate, p.deposit_terms,
      p.minimum_balance, p.minimum_deposit, p.included_transactions, p.unlimited_transactions_flag,
      p.redeemable_flag, p.non_redeemable_flag, p.early_withdrawal_penalty, p.target_customer_tags]);
    if (seen.has(key)) return false;
    seen.add(key); return true;
  }).sort((a, b) => a.bank_name.localeCompare(b.bank_name, 'en') || a.product_name.localeCompare(b.product_name, 'en') || a.product_id.localeCompare(b.product_id));
  let groups: CuratedGroup[] = [];
  let primary: PublicProduct[] = [];
  if (slug === 'no-monthly-fee-chequing') {
    const zero = scoped.filter(p => p.public_display_fee === 0 && !p.fee_waiver_condition?.trim());
    const waived = scoped.filter(p => finiteAmount(p.public_display_fee) && p.public_display_fee > 0 && p.fee_waiver_condition?.trim());
    primary = zero;
    groups = [{ key: 'zero', products: zero }, { key: 'waiver', products: waived }];
  } else if (slug === 'savings-accounts') {
    for (const basis of ['annual', 'apy']) {
      const regular = scoped.filter(p => p.deposit_terms?.basis === basis && depositOptions(p).some(o => o.key === 'ongoing'));
      if (bankCount(regular) >= CURATED_MIN_BANKS) {
        groups.push({ key: basis, products: regular }); primary.push(...regular);
      }
    }
    // Keep qualified offers separate; never rank an introductory/tiered rate as a base rate.
    const qualified = scoped.filter(p => p.rate?.source_text?.trim()
      && ['promotional', 'tiered', 'conditions_unclear'].includes(p.deposit_terms?.reason ?? ''));
    groups.push({ key: 'qualified', products: qualified });
  } else {
    for (const basis of ['annual', 'apy']) for (const withdrawal of ['non_redeemable', 'redeemable']) {
      const exact = scoped.filter(p => p.deposit_terms?.basis === basis && p.deposit_terms.withdrawal === withdrawal
        && depositOptions(p).filter(o => o.key === 'm12' && o.months === 12 && o.days === null).length === 1);
      if (bankCount(exact) >= CURATED_MIN_BANKS) {
        groups.push({ key: `${basis}|${withdrawal}`, products: exact }); primary.push(...exact);
      }
    }
  }
  const count = bankCount(primary);
  return { slug, ready: count >= CURATED_MIN_BANKS, bankCount: count, groups: groups.filter(g => g.products.length) };
}

/** A partial or mixed snapshot must not become an indexable comparison. */
export async function loadCuratedProducts(fetchPage: (page: number) => Promise<PublicProductsResponse>) {
  let first: PublicProductsResponse | undefined;
  const products: PublicProduct[] = [];
  for (let page = 1; page <= 50; page++) {
    const response = await fetchPage(page);
    first ??= response;
    if (response.page !== page || !response.freshness.snapshot_id || response.freshness.status === 'unavailable'
      || response.freshness.snapshot_id !== first.freshness.snapshot_id || response.total_items !== first.total_items
      || response.total_pages !== first.total_pages || (response.has_next_page && !response.items.length)) {
      throw new Error('Incomplete or changing public snapshot');
    }
    products.push(...response.items);
    if (!response.has_next_page) {
      const unique = [...new Map(products.map(p => [p.product_id, p])).values()];
      if (unique.length !== response.total_items || products.length !== unique.length) throw new Error('Incomplete public product set');
      return unique;
    }
  }
  throw new Error('Public comparison page limit exceeded');
}
