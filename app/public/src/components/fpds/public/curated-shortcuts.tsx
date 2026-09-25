import { ArrowUpRight } from 'lucide-react';
import Link from 'next/link';
import type { PublicProductsResponse } from '@/lib/public-api';
import { buildCuratedComparison, curatedCatalogHref, curatedHref, type CuratedSlug } from '@/lib/public-curated';
import { curatedCopy } from '@/lib/public-curated-copy';

export function CuratedShortcutLinks({ locale, ready = [] }: { locale: string; ready?: CuratedSlug[] }) {
  const copy = curatedCopy(locale);
  const items: [CuratedSlug, string][] = [['no-monthly-fee-chequing', copy.feeLink], ['savings-accounts', copy.savingsLink], ['1-year-gic', copy.gicLink]];
  return <nav aria-label={copy.shortcuts} className="mt-5 flex flex-wrap gap-x-5 gap-y-1 border-t border-border pt-3" data-curated-shortcuts>
    {items.map(([slug, label]) => <Link key={slug} href={ready.includes(slug) ? curatedHref(slug, locale) : curatedCatalogHref(slug, locale)} className="inline-flex min-h-11 items-center gap-1 text-sm font-medium text-primary hover:underline">{label}<ArrowUpRight className="size-3.5" aria-hidden="true" /></Link>)}
  </nav>;
}
export async function CuratedShortcuts({ locale, productsPromise }: { locale: string; productsPromise: Promise<PublicProductsResponse> }) {
  let ready: CuratedSlug[] = [];
  try {
    const response = await productsPromise;
    if (response.freshness.snapshot_id && response.items.length === response.total_items) {
      ready = (['no-monthly-fee-chequing', 'savings-accounts', '1-year-gic'] as const).filter(slug => buildCuratedComparison(slug, response.items).ready);
    }
  } catch { /* Keep all three ordinary catalog paths available during an API failure. */ }
  return <CuratedShortcutLinks locale={locale} ready={ready} />;
}
