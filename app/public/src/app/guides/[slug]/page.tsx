import type { Metadata } from 'next';
import Link from 'next/link';
import { notFound } from 'next/navigation';
import { Suspense } from 'react';
import { ArrowLeft, ArrowRight } from 'lucide-react';
import { GuideEditorial } from '@/components/fpds/public/guide-editorial';
import { PublicStructuredData } from '@/components/fpds/public/public-structured-data';
import { Button } from '@/components/ui/button';
import { GUIDE_COMPARISONS, GUIDE_REVIEWED_AT, guideCopy, guideHref, isGuideSlug, isGuideIndexableQuery, type GuideSlug } from '@/lib/public-guides';
import { GUIDE_SOURCES, guideContent } from '@/lib/public-guide-content';
import { buildCuratedComparison, curatedCatalogHref, curatedHref } from '@/lib/public-curated';
import { fetchCuratedProducts } from '@/lib/public-curated-data';
import { normalizePublicLocale } from '@/lib/public-locale';
import { buildPublicPageMetadata, buildPublicSeoUrl } from '@/lib/public-seo';

type Props = { params: Promise<{ slug: string }>; searchParams: Promise<Record<string, string | string[] | undefined>> };
export async function generateMetadata({ params, searchParams }: Props): Promise<Metadata> {
  const { slug } = await params;
  if (!isGuideSlug(slug)) return { robots: { index: false, follow: true } };
  const query = await searchParams;
  const locale = normalizePublicLocale(typeof query.locale === 'string' ? query.locale : '');
  return buildPublicPageMetadata({ title: guideCopy(locale).topics[slug], description: guideContent(slug, locale).intro, path: `/guides/${slug}`, countryCode: 'CA', locale, index: isGuideIndexableQuery(query) });
}
export default async function GuidePage({ params, searchParams }: Props) {
  const { slug } = await params;
  if (!isGuideSlug(slug)) notFound();
  const query = await searchParams;
  const locale = normalizePublicLocale(typeof query.locale === 'string' ? query.locale : '');
  const copy = guideCopy(locale);
  const content = guideContent(slug, locale);
  return <main className="mx-auto w-full min-w-0 max-w-4xl px-4 py-7 md:px-6 md:py-10">
    <Link href={guideHref(null, locale)} className="mb-5 inline-flex min-h-11 items-center gap-2 text-sm text-muted-foreground hover:text-foreground"><ArrowLeft className="size-4" aria-hidden="true" />{copy.nav}</Link>
    <article>
      <header className="border-b border-border pb-6">
        <p className="text-xs font-medium text-muted-foreground">{copy.scope}</p>
        <h1 className="mt-3 text-balance font-display text-3xl font-semibold leading-tight tracking-tight md:text-5xl">{copy.topics[slug]}</h1>
        <p className="mt-4 text-base leading-7 text-muted-foreground">{content.intro}</p>
        <p className="mt-4 text-xs leading-5 text-muted-foreground">SwitchaBank · {copy.checked} <time dateTime={GUIDE_REVIEWED_AT}>{GUIDE_REVIEWED_AT}</time></p>
      </header>
      <div className="grid gap-6 py-7">
        {content.sections.map(section => <section key={section.title}>
          <h2 className="text-lg font-semibold tracking-tight">{section.title}</h2>
          <p className="mt-2 max-w-3xl text-sm leading-7 text-muted-foreground">{section.body}</p>
        </section>)}
      </div>
      <section className="border-y border-primary/20 bg-accent/35 px-4 py-5 md:px-6" aria-labelledby="guide-compare">
        <h2 id="guide-compare" className="text-lg font-semibold">{copy.compare}</h2>
        <p className="mt-2 text-sm leading-6 text-muted-foreground">{content.comparison}</p>
        <div className="mt-4"><Suspense fallback={<ComparisonLink slug={slug} locale={locale} ready={false} />}>
          <GuideComparisonLink slug={slug} locale={locale} />
        </Suspense></div>
        <p className="mt-3 text-xs leading-6 text-muted-foreground">{copy.next}</p>
      </section>
      <section className="mt-7" aria-labelledby="guide-sources">
        <h2 id="guide-sources" className="text-sm font-semibold">{copy.sources} <span className="font-normal text-muted-foreground">· {copy.sourceLanguage}</span></h2>
        <ul className="mt-2 grid gap-2 text-sm leading-6">
          {GUIDE_SOURCES[slug].map(source => <li key={source.href}><a className="inline-flex min-h-11 items-center underline decoration-border underline-offset-4 hover:decoration-foreground" href={source.href} lang="en">{source.title}</a></li>)}
        </ul>
      </section>
      <GuideEditorial locale={locale} />
    </article>
    <PublicStructuredData data={{ '@context': 'https://schema.org', '@type': 'Article', headline: copy.topics[slug], description: content.intro, inLanguage: locale, url: buildPublicSeoUrl(`/guides/${slug}`, locale, 'CA'), dateModified: GUIDE_REVIEWED_AT, author: { '@type': 'Organization', name: 'SwitchaBank', url: buildPublicSeoUrl('/guides', locale, 'CA') }, citation: GUIDE_SOURCES[slug].map(source => source.href) }} />
  </main>;
}
function ComparisonLink({ slug, locale, ready }: { slug: GuideSlug; locale: string; ready: boolean }) {
  const comparison = GUIDE_COMPARISONS[slug];
  const copy = guideCopy(locale);
  return <Button asChild className="h-auto min-h-11 whitespace-normal py-3"><Link data-guide-comparison href={ready ? curatedHref(comparison, locale) : curatedCatalogHref(comparison, locale)}>{ready ? copy.table : copy.browse}<ArrowRight className="size-4 shrink-0" aria-hidden="true" /></Link></Button>;
}
async function GuideComparisonLink({ slug, locale }: { slug: GuideSlug; locale: string }) {
  const products = await fetchCuratedProducts(locale);
  return <ComparisonLink slug={slug} locale={locale} ready={products !== null && buildCuratedComparison(GUIDE_COMPARISONS[slug], products).ready} />;
}
