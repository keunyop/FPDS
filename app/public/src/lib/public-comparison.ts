import type { PublicProduct, PublicProductDetailResponse } from './public-api.ts';
import { sameComparisonScope, depositOptions } from './public-deposit.ts';

export const MAX_COMPARE_PRODUCTS = 4;
export const COMPARISON_STORAGE_KEY = 'switchabank.comparison.v1';
export type ComparisonScope = { countryCode: string; locale: string };
export type ComparisonResult = { id: string; status: 'ready' | 'missing' | 'error'; product?: PublicProduct };
export type SavedComparison = { countryCode: string; items: { id: string; fingerprint: string; name?: string }[] };
export const validComparisonId = (id: string) => /^[A-Za-z0-9_-]{1,128}$/.test(id);

export function parseComparison(params: URLSearchParams) {
  const ids = [...new Set(params.getAll('product_id'))];
  const countryCode = (params.get('country_code') || 'CA').toUpperCase();
  const locale = (params.get('locale') || 'en').toLowerCase();
  return { ids, countryCode: /^[A-Z]{2}$/.test(countryCode) ? countryCode : 'CA',
    locale: ['en', 'ko', 'ja'].includes(locale) ? locale : 'en',
    valid: ids.length <= MAX_COMPARE_PRODUCTS && ids.every(validComparisonId) };
}

export function comparisonHref(ids: string[], scope: ComparisonScope) {
  const params = new URLSearchParams();
  for (const id of [...new Set(ids)].filter(validComparisonId).slice(0, MAX_COMPARE_PRODUCTS)) params.append('product_id', id);
  params.set('country_code', /^[A-Z]{2}$/.test(scope.countryCode) ? scope.countryCode : 'CA');
  params.set('locale', ['en', 'ko', 'ja'].includes(scope.locale) ? scope.locale : 'en');
  return `/compare?${params}`;
}

/** A bounded current-projection read. A failed read is never a removed product. */
export async function loadComparison(ids: string[], countryCode: string,
  fetchProduct: (id: string) => Promise<PublicProductDetailResponse>): Promise<ComparisonResult[]> {
  if (ids.length > MAX_COMPARE_PRODUCTS || !ids.every(validComparisonId)) throw new Error('Invalid comparison');
  const snapshots = new Set<string>();
  const results = await Promise.all(ids.map(async (id): Promise<ComparisonResult> => {
    try {
      const data = await fetchProduct(id);
      const product = data.product;
      if (product.product_id !== id || product.country_code !== countryCode || !data.freshness.snapshot_id || data.freshness.status === 'unavailable') return { id, status: 'error' };
      snapshots.add(data.freshness.snapshot_id);
      return product.status === 'active' ? { id, status: 'ready', product } : { id, status: 'missing' };
    } catch (error) {
      return { id, status: error instanceof Error && 'status' in error && error.status === 404 ? 'missing' : 'error' };
    }
  }));
  return snapshots.size > 1 ? ids.map(id => ({ id, status: 'error' })) : results;
}

// Only approved source facts; exclude localized labels, snapshot/check timestamps,
// elapsed freshness and all user-entered values. Never persist a product payload.
const FACT_KEYS = [
  'bank_code', 'product_name', 'product_type', 'subtype_code', 'currency',
  'standard_rate', 'base_12_month_rate', 'public_display_rate', 'public_display_fee',
  'annual_fee', 'purchase_interest_rate', 'purchase_interest_rate_summary', 'rate', 'deposit_terms',
  'minimum_balance', 'minimum_deposit', 'fee_waiver_condition', 'included_transactions',
  'unlimited_transactions_flag', 'redeemable_flag', 'non_redeemable_flag', 'early_withdrawal_penalty',
  'secured_flag', 'eligibility_text', 'application_method', 'post_maturity_interest_rate',
  'tax_benefits', 'deposit_insurance', 'mortgage_rate', 'interest_rate', 'interest_rate_summary',
  'rate_type', 'term_length_text', 'amortization_text', 'payment_frequency', 'prepayment_privileges',
  'loan_amount_text', 'monthly_payment_text', 'credit_limit_text', 'security_requirement',
  'collateral_text', 'term_rate_table', 'term_length_days', 'target_customer_tags'
] as const satisfies readonly (keyof PublicProduct)[];
function stable(value: unknown): unknown {
  if (Array.isArray(value)) return value.map(stable);
  if (value && typeof value === 'object') return Object.fromEntries(Object.entries(value).sort(([a], [b]) => a.localeCompare(b)).map(([key, item]) => [key, stable(item)]));
  return value ?? null;
}
export async function comparisonFingerprint(product: PublicProduct) {
  const value = JSON.stringify(FACT_KEYS.map(key => stable(product[key])));
  const digest = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(value));
  return Array.from(new Uint8Array(digest), b => b.toString(16).padStart(2, '0')).join('');
}
export function readSavedComparison(raw: string | null, countryCode: string): SavedComparison | null {
  if (!raw || raw.length > 6000) return null;
  try {
    const data = JSON.parse(raw);
    if (data.version !== 1 || data.countryCode !== countryCode || !/^[A-Z]{2}$/.test(data.countryCode)
      || !Array.isArray(data.items) || !data.items.length || data.items.length > MAX_COMPARE_PRODUCTS) return null;
    if (!data.items.every((item: { id?: unknown; fingerprint?: unknown }) => item && typeof item.id === 'string'
      && validComparisonId(item.id) && typeof item.fingerprint === 'string' && /^[a-f0-9]{64}$/.test(item.fingerprint))) return null;
    if (new Set(data.items.map((item: { id: string }) => item.id)).size !== data.items.length) return null;
    return { countryCode, items: data.items.map((item: { id: string; fingerprint: string; name?: unknown }) => ({ id: item.id, fingerprint: item.fingerprint, ...(typeof item.name === 'string' ? { name: item.name.slice(0, 300) } : {}) })) };
  } catch { return null; }
}
export function comparisonBoundary(products: PublicProduct[]): 'mixed' | 'conditions' | null {
  if (products.length < 2) return null;
  const first = products[0];
  if (!/^[A-Z]{3}$/.test(first.currency) || products.some(p => p.product_type !== first.product_type || p.currency !== first.currency || p.country_code !== first.country_code)) return 'mixed';
  if (['savings', 'gic'].includes(first.product_type)
    && !depositOptions(first).some(option => products.every(p => sameComparisonScope(first, p, option.key)))) return 'conditions';
  return null;
}
