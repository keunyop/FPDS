"use client";
import { Check, GitCompareArrows, Plus, X } from 'lucide-react';
import Link from 'next/link';
import { usePathname, useSearchParams } from 'next/navigation';
import { Button } from '@/components/ui/button';
import { ComparePanel } from '@/components/fpds/public/compare-panel';
import { useComparison } from '@/components/fpds/public/comparison-provider';
import type { PublicProduct } from '@/lib/public-api';
import { comparisonHref, MAX_COMPARE_PRODUCTS, parseComparison } from '@/lib/public-comparison';
import { comparisonCopy } from '@/lib/public-comparison-copy';
import type { ProductGridPageFilters } from '@/lib/public-query';

export function AddToComparison({ product, locale }: { product: PublicProduct; locale: string }) {
  const { entries, toggle } = useComparison(product.country_code);
  const copy = comparisonCopy(locale);
  const selected = entries.some(item => item.id === product.product_id);
  const limited = !selected && entries.length >= MAX_COMPARE_PRODUCTS;
  return <div className="grid gap-1">
    <Button type="button" variant={selected ? 'secondary' : 'outline'} aria-pressed={selected} disabled={limited} onClick={() => toggle(product)}>
      {selected ? <Check className="size-4" aria-hidden="true" /> : <Plus className="size-4" aria-hidden="true" />}{selected ? copy.selected : copy.add}
    </Button>
    {limited ? <p className="text-xs text-muted-foreground">{copy.limit}</p> : null}

  </div>;
}

export function ComparisonSelection({ filters, locale, rowsById }: { filters: ProductGridPageFilters; locale: string; rowsById?: Record<string, Array<{ key: string; label: string; value: string }>> }) {
  const { entries, remove, refresh } = useComparison(filters.countryCode);
  const copy = comparisonCopy(locale);
  const products = entries.flatMap(item => item.status === 'ready' && item.product ? [item.product] : []);
  const notices = entries.filter(item => item.status !== 'ready' || item.changed);
  return <>
    {notices.length ? <ul className="grid gap-2" aria-live="polite" data-comparison-status>
      {notices.map(item => <li key={item.id} className="flex min-w-0 flex-wrap items-center justify-between gap-x-3 border-b border-border py-2 text-sm">
        <span className="min-w-0 break-words"><span className="font-medium [overflow-wrap:anywhere]">{item.product?.product_name ?? item.name ?? item.id}</span><span className="ml-2 text-muted-foreground">{item.status === 'ready' ? copy.changed : copy[item.status]}</span></span>
        <div className="flex items-center gap-1">
          {item.status === 'error' ? <Button size="sm" variant="outline" onClick={refresh}>{copy.retry}</Button> : null}
          {item.status !== 'ready' ? <Button size="icon" variant="ghost" aria-label={`${copy.remove}: ${item.product?.product_name ?? item.name ?? item.id}`} onClick={() => remove(item.id)}><X className="size-4" aria-hidden="true" /></Button> : null}
        </div>
      </li>)}
    </ul> : null}
    {products.length ? <ComparePanel filters={filters} locale={locale} products={products} onRemove={remove} rowsById={rowsById} /> : null}
  </>;
}

export function ComparisonDock() {
  const pathname = usePathname();
  const params = useSearchParams();
  const scope = parseComparison(new URLSearchParams(params.toString()));
  const { entries } = useComparison(scope.countryCode);
  const copy = comparisonCopy(scope.locale);
  if (!entries.length || pathname === '/compare' || pathname.startsWith('/admin')) return null;
  return <>
    <div className="h-20 md:hidden" aria-hidden="true" />
    <div data-comparison-dock className="fixed inset-x-0 bottom-0 z-40 border-t border-border bg-background/95 px-4 pb-[max(0.75rem,env(safe-area-inset-bottom))] pt-3 backdrop-blur-xl md:hidden">
      <Link className="flex min-h-11 items-center justify-center gap-2 rounded-full bg-primary px-4 text-sm font-semibold text-primary-foreground" href={comparisonHref(entries.map(item => item.id), scope)}>
        <GitCompareArrows className="size-4" aria-hidden="true" /><span>{copy.count.replace('{count}', String(entries.length))} · {copy.view}</span>
      </Link>
    </div>
  </>;
}

export function ComparisonHeaderLink() {
  const params = useSearchParams();
  const scope = parseComparison(new URLSearchParams(params.toString()));
  const { entries } = useComparison(scope.countryCode);
  const copy = comparisonCopy(scope.locale);
  return <Link href={comparisonHref(entries.map(item => item.id), scope)} aria-label={`${copy.title}${entries.length ? ` · ${copy.count.replace('{count}', String(entries.length))}` : ''}`} title={copy.title} className="inline-flex min-h-11 min-w-11 shrink-0 items-center justify-center gap-1 rounded-full px-2 text-primary hover:bg-muted" data-comparison-header>
    <GitCompareArrows className="size-5" aria-hidden="true" />{entries.length ? <span className="text-xs font-semibold tabular-nums">{entries.length}</span> : null}
  </Link>;
}
