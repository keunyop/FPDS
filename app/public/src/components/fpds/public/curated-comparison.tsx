"use client";

import { Check, ExternalLink, Plus, X } from 'lucide-react';
import Link from 'next/link';
import { useComparison } from '@/components/fpds/public/comparison-provider';
import { ComparisonSelection } from '@/components/fpds/public/comparison-controls';
import { comparisonHref } from '@/lib/public-comparison';
import { BankLogo } from '@/components/fpds/public/bank-logo';
import { ProductVerification } from '@/components/fpds/public/product-verification';
import { TrackedOfficialBankLink, TrackedProductLink } from '@/components/fpds/public/product-engagement-link';
import { Button } from '@/components/ui/button';
import type { PublicProduct } from '@/lib/public-api';
import type { CuratedComparison, CuratedSlug } from '@/lib/public-curated';
import { curatedCopy, curatedGroupTitle } from '@/lib/public-curated-copy';
import { depositOptions } from '@/lib/public-deposit';
import { getPublicMessages } from '@/lib/public-locale';
import { formatPublicCurrency, formatPublicRate, formatPublicTransactions } from '@/lib/public-product-presentation';
import { buildPublicHref, parseProductGridPageFilters } from '@/lib/public-query';

function facts(product: PublicProduct, slug: CuratedSlug, locale: string) {
  const copy = curatedCopy(locale);
  const missing = getPublicMessages(locale).common.notDisclosed;
  const options = depositOptions(product);
  const transactions = formatPublicTransactions(product, locale);
  if (slug === 'no-monthly-fee-chequing') return [
    { label: copy.monthlyFee, value: formatPublicCurrency(product.public_display_fee, 'CAD', locale) },
    { label: copy.transactions, value: transactions },
    { label: copy.conditions, value: [product.fee_waiver_condition, ...(product.target_customer_tag_labels ?? []), product.minimum_balance !== null ? `${copy.minimumBalance}: ${formatPublicCurrency(product.minimum_balance, 'CAD', locale)}` : null].filter(Boolean).join(' · ') || missing }
  ];
  if (slug === 'savings-accounts') return [
    { label: copy.baseRate, value: formatPublicRate(options.find(o => o.key === 'ongoing')?.rate ?? null, locale) },
    { label: copy.offer, value: product.rate?.source_text || missing },
    { label: copy.withdrawals, value: product.early_withdrawal_penalty || missing }
  ];
  const option = options.find(o => o.key === 'm12');
  return [
    { label: copy.termRate, value: formatPublicRate(option?.rate ?? null, locale) },
    { label: copy.minimum, value: formatPublicCurrency(option?.minimum_deposit ?? product.minimum_deposit, 'CAD', locale) },
    { label: copy.conditions, value: [product.deposit_terms?.withdrawal === 'redeemable' ? copy.redeemable : copy.non_redeemable, product.early_withdrawal_penalty].filter(Boolean).join(' · ') }
  ];
}

export function CuratedComparisonTable({ comparison, locale }: { comparison: CuratedComparison; locale: string }) {
  const copy = curatedCopy(locale);
  const messages = getPublicMessages(locale);
  const selection = useComparison('CA');
  const selected = selection.entries.map(item => item.id);
  const filters = parseProductGridPageFilters({ locale });
  const rowsById = Object.fromEntries(selection.entries.flatMap(entry => {
    const product = entry.product;
    const group = comparison.groups.find(group => group.products.some(p => p.product_id === entry.id));
    if (!product || !group || entry.changed || product.country_code !== 'CA' || product.currency !== 'CAD') return [];
    return [[entry.id, [
      { key: 'scope', label: copy.scopeLabel, value: `${copy.scope} · ${curatedGroupTitle(group.key, locale)}` },
      ...facts(product, comparison.slug, locale).map(fact => ({ ...fact, key: fact.label }))
    ]]];
  }));
  function toggle(product: PublicProduct) { selection.toggle(product); }

  return (
    <div className="grid min-w-0 gap-8" data-curated-comparison={comparison.slug}>
      <div className="sticky top-16 z-20 flex min-h-14 flex-wrap items-center justify-between gap-2 border-y border-foreground/15 bg-background/95 px-1 py-2 backdrop-blur-xl">
        <span className="text-xs font-semibold tabular-nums" role="status">{messages.compare.selectedCount.replace('{count}', String(selected.length)).replace('{limit}', '4')}</span>
        <div className="flex items-center gap-1">
          <Button asChild size="sm" variant="ghost"><Link href={comparisonHref(selected, filters)}>{copy.viewCompare}</Link></Button>
          {selected.length ? <Button type="button" size="sm" variant="ghost" onClick={selection.clear}><X className="size-4" aria-hidden="true" />{messages.compare.clear}</Button> : null}
        </div>
      </div>
      <div className="min-w-0 scroll-mt-36" hidden={!selected.length}>
        {selected.length ? <ComparisonSelection filters={filters} locale={locale} rowsById={rowsById} /> : null}
      </div>
      {comparison.groups.map(group => (
        <section key={group.key} className="min-w-0" aria-labelledby={`curated-${group.key}`}>
          <h2 id={`curated-${group.key}`} className="mb-3 text-lg font-semibold tracking-tight">{curatedGroupTitle(group.key, locale)}</h2>
          <table className="block w-full table-fixed border-collapse text-left lg:table" role="table">
            <caption className="sr-only">{copy.pages[comparison.slug].title} · {curatedGroupTitle(group.key, locale)}</caption>
            <thead className="sr-only lg:not-sr-only" role="rowgroup"><tr role="row" className="border-y border-border text-xs text-muted-foreground">
              <th scope="col" className="w-[27%] px-3 py-3 font-medium">{copy.product}</th>
              {facts(group.products[0], comparison.slug, locale).map((fact, index) => <th scope="col" className={index === 0 ? 'w-[13%] px-3 py-3 font-medium' : 'px-3 py-3 font-medium'} key={fact.label}>{fact.label}</th>)}
              <th scope="col" className="w-[15%] px-3 py-3 font-medium">{copy.actions}</th>
            </tr></thead>
            <tbody className="block divide-y divide-border border-y border-border lg:table-row-group lg:border-0" role="rowgroup">
              {group.products.map(product => {
                const added = selected.includes(product.product_id);
                return <tr role="row" key={product.product_id} data-product-id={product.product_id} className="grid min-w-0 gap-x-5 gap-y-3 py-5 sm:grid-cols-2 lg:table-row lg:py-0">
                  <th scope="row" role="rowheader" className="min-w-0 text-left font-normal sm:col-span-2 lg:px-3 lg:py-5 lg:align-top">
                    <div className="flex min-w-0 items-start gap-3"><BankLogo bankCode={product.bank_code} bankName={product.bank_name} size="sm" /><div className="min-w-0">
                      <p className="text-xs text-muted-foreground">{product.bank_name}</p>
                      <TrackedProductLink className="inline-flex min-h-11 items-center break-words text-sm font-semibold hover:text-primary" countryCode="CA" productId={product.product_id} href={buildPublicHref(`/products/${encodeURIComponent(product.product_id)}`, filters)}>{product.product_name}</TrackedProductLink>
                    </div></div>
                    <ProductVerification product={product} locale={locale} />
                  </th>
                  {facts(product, comparison.slug, locale).map((fact, index) => <td role="cell" key={fact.label} className="min-w-0 text-sm leading-6 [overflow-wrap:anywhere] lg:px-3 lg:py-5 lg:align-top">
                    <span className="mb-0.5 block text-xs text-muted-foreground lg:hidden">{fact.label}</span>
                    <span className={index === 0 ? 'font-mono text-lg font-semibold tabular-nums' : ''}>{fact.value}</span>
                  </td>)}
                  <td role="cell" className="min-w-0 sm:col-span-2 lg:px-3 lg:py-5 lg:align-top"><div className="flex flex-wrap items-center gap-x-4 gap-y-1 lg:flex-col lg:items-start">
                    <Button type="button" size="sm" variant={added ? 'secondary' : 'outline'} aria-pressed={added} aria-label={`${added ? copy.selected : copy.compare}: ${product.product_name}`} disabled={!added && selected.length >= 4} onClick={() => toggle(product)} className="min-h-11">
                      {added ? <Check className="size-4" aria-hidden="true" /> : <Plus className="size-4" aria-hidden="true" />}{added ? copy.selected : messages.compare.select}
                    </Button>
                    <TrackedOfficialBankLink className="inline-flex min-h-11 items-center gap-1 text-xs font-semibold text-primary hover:underline" countryCode="CA" productId={product.product_id} href={product.product_url!}>{copy.checkBank}<ExternalLink className="size-3.5 shrink-0" aria-hidden="true" /></TrackedOfficialBankLink>
                  </div></td>
                </tr>;
              })}
            </tbody>
          </table>
        </section>
      ))}
    </div>
  );
}
