'use client';

import { ArrowRight, ExternalLink, RefreshCw, Search } from 'lucide-react';
import Link from 'next/link';
import { FormEvent, useEffect, useMemo, useRef, useState } from 'react';

import { BankLogo } from '@/components/fpds/public/bank-logo';
import { Button } from '@/components/ui/button';
import { formatPublicCurrency, formatPublicRate } from '@/lib/public-product-presentation';
import { formatPublicMessage, getIntlLocale, getPublicMessages, getPublicRecommendationCopy } from '@/lib/public-locale';
import type { PublicDashboardSummaryResponse, PublicProduct, PublicProductsResponse } from '@/lib/public-api';
import { buildPublicHref } from '@/lib/public-query';

type RecommendationRule = {
  direction: 'higher' | 'lower';
  metric: 'annual_fee' | 'card_display_rate' | 'public_display_fee';
  metricKind: 'annualFee' | 'monthlyFee' | 'rate';
  sortBy: 'annual_fee' | 'display_rate' | 'monthly_fee';
  sortOrder: 'asc' | 'desc';
};

type ResultState =
  | { status: 'idle' }
  | { currentProduct: PublicProduct; status: 'loading' | 'metric-unavailable' | 'error' }
  | { currentProduct: PublicProduct; recommendations: PublicProduct[]; rule: RecommendationRule; status: 'ready' };

const RECOMMENDATION_RULES: Record<string, RecommendationRule> = {
  chequing: { direction: 'lower', metric: 'public_display_fee', metricKind: 'monthlyFee', sortBy: 'monthly_fee', sortOrder: 'asc' },
  savings: { direction: 'higher', metric: 'card_display_rate', metricKind: 'rate', sortBy: 'display_rate', sortOrder: 'desc' },
  gic: { direction: 'higher', metric: 'card_display_rate', metricKind: 'rate', sortBy: 'display_rate', sortOrder: 'desc' },
  'credit-card': { direction: 'lower', metric: 'annual_fee', metricKind: 'annualFee', sortBy: 'annual_fee', sortOrder: 'asc' },
  mortgage: { direction: 'lower', metric: 'card_display_rate', metricKind: 'rate', sortBy: 'display_rate', sortOrder: 'asc' },
  'personal-loan': { direction: 'lower', metric: 'card_display_rate', metricKind: 'rate', sortBy: 'display_rate', sortOrder: 'asc' },
  'line-of-credit': { direction: 'lower', metric: 'card_display_rate', metricKind: 'rate', sortBy: 'display_rate', sortOrder: 'asc' }
};

export function ProductRecommendationFinder({
  banks,
  countryCode,
  locale
}: {
  banks: PublicDashboardSummaryResponse['breakdowns']['products_by_bank'];
  countryCode: string;
  locale: string;
}) {
  const copy = getPublicRecommendationCopy(locale);
  const [bankCode, setBankCode] = useState('');
  const [bankLoadAttempt, setBankLoadAttempt] = useState(0);
  const [productType, setProductType] = useState('');
  const [productQuery, setProductQuery] = useState('');
  const [productId, setProductId] = useState('');
  const [bankProducts, setBankProducts] = useState<PublicProduct[]>([]);
  const [productsStatus, setProductsStatus] = useState<'idle' | 'loading' | 'ready' | 'error'>('idle');
  const [result, setResult] = useState<ResultState>({ status: 'idle' });
  const recommendationController = useRef<AbortController | null>(null);

  const bankOptions = useMemo(
    () => [...banks].sort((left, right) => left.bank_name.localeCompare(right.bank_name, locale)),
    [banks, locale]
  );
  const productTypeOptions = useMemo(
    () => [...new Map(bankProducts.map((product) => [
      product.product_type,
      { label: product.product_type_label, value: product.product_type }
    ])).values()].sort((left, right) => left.label.localeCompare(right.label, locale)),
    [bankProducts, locale]
  );
  const productMatches = useMemo(() => {
    const query = normalizeProductSearch(productQuery, locale);
    if (!productType || !query) return [];

    return bankProducts
      .filter((product) => product.product_type === productType)
      .filter((product) => normalizeProductSearch(product.product_name, locale).includes(query))
      .sort((left, right) => left.product_name.localeCompare(right.product_name, locale))
      .slice(0, 8);
  }, [bankProducts, locale, productQuery, productType]);

  useEffect(() => {
    recommendationController.current?.abort();
    setProductType('');
    setProductQuery('');
    setProductId('');
    setBankProducts([]);
    setResult({ status: 'idle' });
    if (!bankCode) {
      setProductsStatus('idle');
      return;
    }

    const controller = new AbortController();
    setProductsStatus('loading');
    void loadBankProducts({ bankCode, countryCode, locale, signal: controller.signal })
      .then((products) => {
        setBankProducts(products);
        setProductsStatus('ready');
      })
      .catch((error: unknown) => {
        if (!isAbortError(error)) setProductsStatus('error');
      });
    return () => controller.abort();
  }, [bankCode, bankLoadAttempt, countryCode, locale]);

  useEffect(() => () => recommendationController.current?.abort(), []);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const currentProduct = bankProducts.find((product) => product.product_id === productId);
    if (!currentProduct) return;

    const rule = RECOMMENDATION_RULES[currentProduct.product_type];
    const currentMetric = rule ? readMetric(currentProduct, rule) : null;
    if (!rule || currentMetric === null) {
      setResult({ currentProduct, status: 'metric-unavailable' });
      return;
    }

    recommendationController.current?.abort();
    const controller = new AbortController();
    recommendationController.current = controller;
    setResult({ currentProduct, status: 'loading' });

    try {
      const response = await fetchProductPage({
        countryCode,
        locale,
        page: 1,
        pageSize: 100,
        productType: currentProduct.product_type,
        signal: controller.signal,
        sortBy: rule.sortBy,
        sortOrder: rule.sortOrder
      });
      const recommendations = response.items
        .filter((candidate) => candidate.product_id !== currentProduct.product_id)
        .filter((candidate) => isStrictImprovement(currentMetric, readMetric(candidate, rule), rule))
        .slice(0, 3);
      setResult({ currentProduct, recommendations, rule, status: 'ready' });
    } catch (error: unknown) {
      if (!isAbortError(error)) setResult({ currentProduct, status: 'error' });
    }
  }

  function resetFinder() {
    recommendationController.current?.abort();
    setBankCode('');
    setBankLoadAttempt(0);
    setProductType('');
    setProductQuery('');
    setProductId('');
    setBankProducts([]);
    setProductsStatus('idle');
    setResult({ status: 'idle' });
  }

  const selectedProduct = bankProducts.find((product) => product.product_id === productId) ?? null;
  const busy = productsStatus === 'loading' || result.status === 'loading';

  return (
    <section aria-labelledby='product-finder-title' className='min-w-0 overflow-hidden rounded-xl border border-primary/25 bg-card/80 shadow-[0_18px_48px_rgba(28,39,35,0.08)]'>
      <div className='border-b border-primary/15 bg-primary/[0.045] px-4 py-4 md:px-5'>
        <h2 id='product-finder-title' className='text-xl font-semibold tracking-[-0.03em] text-foreground'>{copy.title}</h2>
      </div>

      <form className='grid gap-4 px-4 py-5 md:px-5' onSubmit={handleSubmit}>
        <FinderSelect
          disabled={busy || !bankOptions.length}
          label={copy.bankLabel}
          onChange={setBankCode}
          options={bankOptions.map((bank) => ({ label: bank.bank_name, value: bank.bank_code }))}
          placeholder={copy.bankPlaceholder}
          value={bankCode}
        />
        <FinderSelect
          disabled={!bankCode || busy || productsStatus !== 'ready' || !productTypeOptions.length}
          label={copy.productTypeLabel}
          onChange={(value) => {
            recommendationController.current?.abort();
            setProductType(value);
            setProductQuery('');
            setProductId('');
            setResult({ status: 'idle' });
          }}
          options={productTypeOptions}
          placeholder={productsStatus === 'loading' ? copy.loadingProducts : copy.productTypePlaceholder}
          value={productType}
        />
        <ProductSearch
          disabled={!productType || busy || productsStatus !== 'ready'}
          label={copy.productSearchLabel}
          matches={productMatches}
          noMatches={copy.noProductMatches}
          onChange={(value) => {
            recommendationController.current?.abort();
            setProductQuery(value);
            if (selectedProduct?.product_name !== value) setProductId('');
            setResult({ status: 'idle' });
          }}
          onSelect={(product) => {
            setProductQuery(product.product_name);
            setProductId(product.product_id);
            setResult({ status: 'idle' });
          }}
          placeholder={copy.productSearchPlaceholder}
          query={productQuery}
          selectedProductId={productId}
        />

        {productsStatus === 'error' ? (
          <div className='grid gap-2'>
            <FinderMessage tone='error'>{copy.loadProductsError}</FinderMessage>
            <Button className='justify-self-start' onClick={() => setBankLoadAttempt((attempt) => attempt + 1)} size='sm' type='button' variant='outline'>
              <RefreshCw className='size-3.5' aria-hidden='true' />
              {copy.retryProducts}
            </Button>
          </div>
        ) : null}
        {productsStatus === 'ready' && bankCode && !bankProducts.length ? <FinderMessage>{copy.noProducts}</FinderMessage> : null}

        <div className='flex flex-wrap gap-2'>
          <Button className='min-w-0 flex-1' disabled={!selectedProduct || busy} type='submit'>
            {result.status === 'loading' ? <RefreshCw className='size-4 animate-spin' aria-hidden='true' /> : <Search className='size-4' aria-hidden='true' />}
            {result.status === 'loading' ? copy.loadingRecommendations : copy.submit}
          </Button>
          {bankCode ? <Button aria-label={copy.reset} onClick={resetFinder} type='button' variant='ghost'>{copy.reset}</Button> : null}
        </div>
      </form>

      {result.status !== 'idle' ? (
        <div aria-live='polite' className='border-t border-border bg-background/35'>
          <div className='px-4 py-4 md:px-5'>
            <RecommendationResult countryCode={countryCode} locale={locale} result={result} />
          </div>
          <p className='border-t border-border px-4 py-3 text-xs leading-5 text-muted-foreground md:px-5'>{copy.caveat}</p>
        </div>
      ) : null}
    </section>
  );
}

function RecommendationResult({
  countryCode,
  locale,
  result
}: {
  countryCode: string;
  locale: string;
  result: ResultState;
}) {
  const copy = getPublicRecommendationCopy(locale);
  const commonCopy = getPublicMessages(locale).common;

  if (result.status === 'idle') return null;
  if (result.status === 'loading') return <FinderMessage>{copy.loadingRecommendations}</FinderMessage>;

  const rule = result.status === 'ready'
    ? result.rule
    : RECOMMENDATION_RULES[result.currentProduct.product_type];
  const readyResult = result.status === 'ready' ? result : null;

  return (
    <div className='grid gap-4'>
      <div className='flex min-w-0 items-center gap-3'>
        <BankLogo bankCode={result.currentProduct.bank_code} bankName={result.currentProduct.bank_name} size='sm' />
        <div className='min-w-0 flex-1'>
          <p className='text-[11px] font-semibold uppercase tracking-[0.08em] text-muted-foreground'>{copy.currentProduct}</p>
          <p className='mt-1 text-sm font-semibold text-foreground [overflow-wrap:anywhere]'>{result.currentProduct.product_name}</p>
          <p className='mt-0.5 text-xs text-muted-foreground'>{result.currentProduct.bank_name} · {result.currentProduct.product_type_label}</p>
        </div>
        {rule ? (
          <span className='shrink-0 border-b-2 border-maple px-1.5 py-1 text-sm font-semibold tabular-nums text-foreground'>
            {formatMetric(result.currentProduct, rule, locale)}
          </span>
        ) : null}
      </div>

      {result.status === 'metric-unavailable' ? (
        <FinderMessage>{copy.metricUnavailable}</FinderMessage>
      ) : result.status === 'error' ? (
        <FinderMessage tone='error'>{copy.recommendationsError}</FinderMessage>
      ) : readyResult && readyResult.recommendations.length ? (
        <div>
          <div className='mb-2 flex flex-wrap items-end justify-between gap-2'>
            <div>
              <h3 className='text-sm font-semibold text-foreground'>{copy.resultTitle}</h3>
              <p className='mt-0.5 text-xs text-muted-foreground'>
                {formatPublicMessage(copy.resultBasis, {
                  basis: metricLabel(readyResult.rule, locale),
                  type: result.currentProduct.product_type_label
                })}
              </p>
            </div>
            <span className='font-mono text-[10px] font-semibold text-primary'>{readyResult.recommendations.length}</span>
          </div>
          <ol className='grid divide-y divide-primary/15 border-y border-primary/20'>
            {readyResult.recommendations.map((product) => (
              <li className='grid min-w-0 gap-3 py-3' key={product.product_id}>
                <div className='flex min-w-0 items-center gap-3'>
                  <BankLogo bankCode={product.bank_code} bankName={product.bank_name} size='sm' />
                  <div className='min-w-0 flex-1'>
                    <Link
                      className='inline-flex min-h-11 items-center text-sm font-semibold text-foreground hover:text-primary [overflow-wrap:anywhere]'
                      href={buildProductHref(product.product_id, countryCode, locale)}
                    >
                      {product.product_name}
                    </Link>
                    <p className='text-xs text-muted-foreground'>{product.bank_name}</p>
                  </div>
                  <div className='shrink-0 text-right'>
                    <p className='text-base font-semibold tabular-nums text-primary'>{formatMetric(product, readyResult.rule, locale)}</p>
                    <p className='mt-0.5 text-[11px] font-semibold text-muted-foreground'>
                      {formatImprovement(result.currentProduct, product, readyResult.rule, locale)}
                    </p>
                  </div>
                </div>
                <div className='flex flex-wrap items-center gap-x-4 gap-y-1 sm:pl-[5.5rem]'>
                  <Link className='inline-flex min-h-11 items-center gap-1.5 text-xs font-semibold text-primary hover:underline' href={buildProductHref(product.product_id, countryCode, locale)}>
                    {copy.viewDetails}
                    <ArrowRight className='size-3.5' aria-hidden='true' />
                  </Link>
                  {product.product_url ? (
                    <a className='inline-flex min-h-11 items-center gap-1.5 text-xs font-semibold text-primary hover:underline' href={product.product_url} rel='noopener noreferrer' target='_blank'>
                      {commonCopy.bankPage}
                      <ExternalLink className='size-3.5' aria-hidden='true' />
                    </a>
                  ) : null}
                </div>
              </li>
            ))}
          </ol>
        </div>
      ) : (
        <FinderMessage>{formatPublicMessage(copy.noImprovement, { basis: metricLabel(rule, locale) })}</FinderMessage>
      )}
    </div>
  );
}

function FinderSelect({
  disabled,
  label,
  onChange,
  options,
  placeholder,
  value
}: {
  disabled: boolean;
  label: string;
  onChange: (value: string) => void;
  options: Array<{ label: string; value: string }>;
  placeholder: string;
  value: string;
}) {
  return (
    <label className='grid gap-1.5'>
      <span className='text-sm font-semibold text-foreground'>{label}</span>
      <select
        className='h-12 w-full min-w-0 rounded-lg border border-input bg-background px-3 text-sm text-foreground outline-none transition focus-visible:border-ring focus-visible:ring-3 focus-visible:ring-ring/50 disabled:cursor-not-allowed disabled:bg-muted/50 disabled:text-muted-foreground'
        disabled={disabled}
        onChange={(event) => onChange(event.target.value)}
        value={value}
      >
        <option value=''>{placeholder}</option>
        {options.map((option) => <option key={option.value} value={option.value}>{option.label}</option>)}
      </select>
    </label>
  );
}

function ProductSearch({
  disabled,
  label,
  matches,
  noMatches,
  onChange,
  onSelect,
  placeholder,
  query,
  selectedProductId
}: {
  disabled: boolean;
  label: string;
  matches: PublicProduct[];
  noMatches: string;
  onChange: (value: string) => void;
  onSelect: (product: PublicProduct) => void;
  placeholder: string;
  query: string;
  selectedProductId: string;
}) {
  const selectedMatch = matches.find((product) => product.product_id === selectedProductId);
  const showMatches = Boolean(query.trim()) && selectedMatch?.product_name !== query;

  return (
    <div className='grid gap-1.5'>
      <label className='text-sm font-semibold text-foreground' htmlFor='current-product-search'>{label}</label>
      <div className='relative'>
        <Search className='pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground' aria-hidden='true' />
        <input
          aria-autocomplete='list'
          aria-controls='current-product-options'
          aria-expanded={showMatches && matches.length > 0}
          autoComplete='off'
          className='h-12 w-full min-w-0 rounded-lg border border-input bg-background pl-10 pr-3 text-sm text-foreground outline-none transition placeholder:text-muted-foreground focus-visible:border-ring focus-visible:ring-3 focus-visible:ring-ring/50 disabled:cursor-not-allowed disabled:bg-muted/50 disabled:text-muted-foreground'
          disabled={disabled}
          id='current-product-search'
          onChange={(event) => onChange(event.target.value)}
          placeholder={placeholder}
          role='combobox'
          type='search'
          value={query}
        />
      </div>
      {showMatches ? (
        matches.length ? (
          <ul className='max-h-56 overflow-y-auto rounded-lg border border-border bg-background p-1' id='current-product-options' role='listbox'>
            {matches.map((product) => (
              <li key={product.product_id} role='none'>
                <button
                  aria-selected={product.product_id === selectedProductId}
                  className='flex min-h-11 w-full min-w-0 items-center rounded-md px-3 py-2 text-left text-sm font-medium text-foreground hover:bg-accent focus-visible:bg-accent focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring'
                  onClick={() => onSelect(product)}
                  role='option'
                  type='button'
                >
                  <span className='[overflow-wrap:anywhere]'>{product.product_name}</span>
                </button>
              </li>
            ))}
          </ul>
        ) : (
          <p className='px-1 py-2 text-sm text-muted-foreground'>{noMatches}</p>
        )
      ) : null}
    </div>
  );
}

function FinderMessage({ children, tone = 'neutral' }: { children: React.ReactNode; tone?: 'error' | 'neutral' }) {
  return (
    <p className={tone === 'error'
      ? 'rounded-lg border border-destructive/25 bg-destructive/5 px-3 py-3 text-sm leading-6 text-destructive'
      : 'rounded-lg border border-dashed border-border bg-card/55 px-3 py-3 text-sm leading-6 text-muted-foreground'
    }>
      {children}
    </p>
  );
}

async function loadBankProducts({
  bankCode,
  countryCode,
  locale,
  signal
}: {
  bankCode: string;
  countryCode: string;
  locale: string;
  signal: AbortSignal;
}) {
  const products: PublicProduct[] = [];
  let page = 1;
  let hasNextPage = true;

  while (hasNextPage && page <= 5) {
    const response = await fetchProductPage({
      bankCode,
      countryCode,
      locale,
      page,
      pageSize: 100,
      signal,
      sortBy: 'product_name',
      sortOrder: 'asc'
    });
    products.push(...response.items);
    hasNextPage = response.has_next_page;
    page += 1;
  }
  return [...new Map(products.map((product) => [product.product_id, product])).values()];
}

async function fetchProductPage({
  bankCode,
  countryCode,
  locale,
  page,
  pageSize,
  productType,
  signal,
  sortBy,
  sortOrder
}: {
  bankCode?: string;
  countryCode: string;
  locale: string;
  page: number;
  pageSize: number;
  productType?: string;
  signal: AbortSignal;
  sortBy: string;
  sortOrder: 'asc' | 'desc';
}) {
  const params = new URLSearchParams({
    country_code: countryCode,
    locale,
    page: String(page),
    page_size: String(pageSize),
    sort_by: sortBy,
    sort_order: sortOrder
  });
  if (bankCode) params.append('bank_code', bankCode);
  if (productType) params.append('product_type', productType);

  const response = await fetch(`/api/public/products?${params.toString()}`, { signal });
  if (!response.ok) throw new Error(`Public products request failed (${response.status}).`);
  const payload = await response.json() as { data?: PublicProductsResponse };
  if (!payload.data || !Array.isArray(payload.data.items)) throw new Error('Public products response was invalid.');
  return payload.data;
}

function readMetric(product: PublicProduct, rule: RecommendationRule) {
  const value = product[rule.metric];
  return typeof value === 'number' && Number.isFinite(value) ? value : null;
}

function isStrictImprovement(currentValue: number, candidateValue: number | null, rule: RecommendationRule) {
  if (candidateValue === null) return false;
  return rule.direction === 'higher' ? candidateValue > currentValue : candidateValue < currentValue;
}

function metricLabel(rule: RecommendationRule, locale: string) {
  const labels = getPublicRecommendationCopy(locale).metricLabels;
  if (rule.metricKind === 'annualFee') return labels.annualFee;
  if (rule.metricKind === 'monthlyFee') return labels.monthlyFee;
  return rule.direction === 'higher' ? labels.higherRate : labels.lowerRate;
}

function formatMetric(product: PublicProduct, rule: RecommendationRule, locale: string) {
  const value = readMetric(product, rule);
  return rule.metricKind === 'rate'
    ? formatPublicRate(value, locale)
    : formatPublicCurrency(value, product.currency, locale);
}

function formatImprovement(current: PublicProduct, candidate: PublicProduct, rule: RecommendationRule, locale: string) {
  const currentValue = readMetric(current, rule);
  const candidateValue = readMetric(candidate, rule);
  if (currentValue === null || candidateValue === null) return '';

  const difference = Math.abs(candidateValue - currentValue);
  const copy = getPublicRecommendationCopy(locale);
  if (rule.metricKind === 'rate') {
    const value = new Intl.NumberFormat(getIntlLocale(locale), { maximumFractionDigits: 2 }).format(difference);
    return formatPublicMessage(rule.direction === 'higher' ? copy.rateHigher : copy.rateLower, { value });
  }

  const value = formatPublicCurrency(difference, candidate.currency, locale);
  return formatPublicMessage(rule.metricKind === 'annualFee' ? copy.annualFeeLower : copy.monthlyFeeLower, { value });
}

function buildProductHref(productId: string, countryCode: string, locale: string) {
  return buildPublicHref(`/products/${productId}`, {
    bankCodes: [],
    countryCode,
    feeBucket: '',
    locale,
    minimumBalanceBucket: '',
    minimumDepositBucket: '',
    productTypes: [],
    searchQuery: '',
    targetCustomerTags: [],
    termBucket: ''
  });
}

function isAbortError(error: unknown) {
  return error instanceof DOMException && error.name === 'AbortError';
}

function normalizeProductSearch(value: string, locale: string) {
  return value.trim().replace(/\s+/g, ' ').toLocaleLowerCase(getIntlLocale(locale));
}
