import type { Metadata } from 'next';
import { Suspense } from 'react';
import Link from 'next/link';
import { notFound, permanentRedirect } from 'next/navigation';
import { CuratedComparisonTable } from '@/components/fpds/public/curated-comparison';
import { PublicStructuredData } from '@/components/fpds/public/public-structured-data';
import { Button } from '@/components/ui/button';
import { buildCuratedComparison, curatedCatalogHref, curatedHref, isCuratedSlug, isCuratedIndexableQuery, type CuratedSlug } from '@/lib/public-curated';
import { curatedCopy, curatedNote } from '@/lib/public-curated-copy';
import { fetchCuratedProducts } from '@/lib/public-curated-data';
import { normalizePublicLocale } from '@/lib/public-locale';
import { buildPublicPageMetadata, buildPublicSeoUrl } from '@/lib/public-seo';
import { normalizeCountryCodeValue } from '@/lib/public-query';

type Props = { params: Promise<{ slug: string }>; searchParams: Promise<Record<string, string | string[] | undefined>> };
const scalar = (value: string | string[] | undefined) => Array.isArray(value) ? value[0] : value ?? '';

export async function generateMetadata({ params, searchParams }: Props): Promise<Metadata> {
  const { slug } = await params;
  if (!isCuratedSlug(slug)) return { robots: { index: false, follow: true } };
  const query = await searchParams;
  const locale = normalizePublicLocale(scalar(query.locale));
  const products = await fetchCuratedProducts(locale);
  const ready = products !== null && buildCuratedComparison(slug, products).ready;
  const metadata = buildPublicPageMetadata({ ...curatedCopy(locale).pages[slug], path: `/ca/${slug}`, locale, countryCode: 'CA', index: ready && isCuratedIndexableQuery(query) });
  if (!ready && metadata.alternates) metadata.alternates.languages = undefined;
  return metadata;
}

export default async function CuratedPage({ params, searchParams }: Props) {
  const { slug } = await params;
  if (!isCuratedSlug(slug)) notFound();
  const query = await searchParams;
  const locale = normalizePublicLocale(scalar(query.locale));
  const country = normalizeCountryCodeValue(scalar(query.country_code));
  if (country !== 'CA') permanentRedirect(curatedCatalogHref(slug, locale, country));
  const copy = curatedCopy(locale);
  return <main className="mx-auto w-full min-w-0 max-w-7xl px-4 py-7 md:px-6 md:py-10">
    <header className="mb-7 border-b border-foreground/15 pb-6">
      <p className="mb-3 text-xs font-medium uppercase tracking-wide text-muted-foreground">{copy.scope}</p>
      <h1 className="max-w-4xl text-balance font-display text-3xl font-semibold leading-tight tracking-tight md:text-5xl">{copy.pages[slug].title}</h1>
      <p className="mt-4 max-w-3xl text-sm leading-6 text-muted-foreground">{curatedNote(slug, locale)}</p>
    </header>
    <Suspense fallback={<section aria-busy="true" aria-label={copy.loading} className="grid gap-4 py-4">
      <p role="status" className="text-sm text-muted-foreground">{copy.loading}</p>
      {[0, 1, 2].map(row => <div key={row} aria-hidden="true" className="h-28 animate-pulse border-y border-border bg-muted/40 motion-reduce:animate-none" />)}
    </section>}>
      <ComparisonContent slug={slug} locale={locale} />
    </Suspense>
  </main>;
}

async function ComparisonContent({ slug, locale }: { slug: CuratedSlug; locale: string }) {
  const copy = curatedCopy(locale);
  const products = await fetchCuratedProducts(locale);
  const comparison = buildCuratedComparison(slug, products ?? []);
  const displayed = comparison.ready ? comparison.groups.flatMap(group => group.products) : [];
  const canonical = buildPublicSeoUrl(`/ca/${slug}`, locale, 'CA');
  return <>
    {comparison.ready ? <p className="mb-4 text-xs text-muted-foreground">{copy.coverage.replace('{products}', String(displayed.length)).replace('{banks}', String(new Set(displayed.map(p => p.bank_code)).size))}</p> : null}
    {comparison.ready ? <>
      <PublicStructuredData data={{ '@context': 'https://schema.org', '@type': 'CollectionPage', name: copy.pages[slug].title, description: copy.pages[slug].description, url: canonical, inLanguage: locale, mainEntity: {
        '@type': 'ItemList', numberOfItems: displayed.length, itemListElement: displayed.map((product, index) => ({ '@type': 'ListItem', position: index + 1, name: `${product.bank_name} ${product.product_name}`, url: buildPublicSeoUrl(`/products/${encodeURIComponent(product.product_id)}`, 'en', 'CA') }))
      } }} />
      <CuratedComparisonTable key={`${slug}-${locale}-${displayed.map(p => p.product_id).join(",")}`} comparison={comparison} locale={locale} />
      <p className="mt-7 max-w-3xl text-xs leading-6 text-muted-foreground">{copy.boundary}</p>
    </> : <section className="grid justify-items-start gap-4 py-5" role={products === null ? 'alert' : 'status'}>
      <h2 className="text-xl font-semibold">{products === null ? copy.unavailable : copy.pending}</h2>
      <p className="text-sm text-muted-foreground">{copy.pendingBody}</p>
      <div className="flex flex-wrap gap-3"><Button asChild><Link href={curatedCatalogHref(slug, locale)}>{copy.browse}</Link></Button>
        {products === null ? <Button asChild variant="outline"><a href={curatedHref(slug, locale)}>{copy.retry}</a></Button> : null}</div>
    </section>}
  </>;
}
