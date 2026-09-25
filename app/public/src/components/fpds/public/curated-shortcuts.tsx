import { ArrowRight } from 'lucide-react';
import Link from 'next/link';
import { Button } from '@/components/ui/button';
import type { PublicProductsResponse } from '@/lib/public-api';
import { buildCuratedComparison, curatedCatalogHref, curatedHref, type CuratedSlug } from '@/lib/public-curated';
import { curatedCopy } from '@/lib/public-curated-copy';

export function CuratedShortcutLinks({ locale, ready = [] }: { locale: string; ready?: CuratedSlug[] }) {
  const copy = curatedCopy(locale);
  const items: [CuratedSlug, string][] = [['no-monthly-fee-chequing', copy.feeLink], ['savings-accounts', copy.savingsLink], ['1-year-gic', copy.gicLink]];
  return (
    <nav
      aria-label={copy.shortcuts}
      className="mt-5 grid gap-2 border-t border-border pt-5 sm:grid-cols-3"
      data-curated-shortcuts
    >
      {items.map(([slug, label]) => (
        <Button
          key={slug}
          asChild
          variant="secondary"
          className="h-auto min-h-14 min-w-0 justify-between gap-3 whitespace-normal border-primary/25 px-4 py-3 text-left text-base font-semibold hover:border-primary hover:bg-primary hover:text-primary-foreground sm:min-h-20"
        >
          <Link href={ready.includes(slug) ? curatedHref(slug, locale) : curatedCatalogHref(slug, locale)}>
            <span>{label}</span>
            <ArrowRight className="size-4" aria-hidden="true" />
          </Link>
        </Button>
      ))}
    </nav>
  );
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
