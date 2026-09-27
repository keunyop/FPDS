import type { Metadata } from 'next';
import Link from 'next/link';
import { ArrowRight } from 'lucide-react';
import { GuideEditorial } from '@/components/fpds/public/guide-editorial';
import { GUIDE_SLUGS, guideCopy, guideHref, isGuideIndexableQuery } from '@/lib/public-guides';
import { guideContent } from '@/lib/public-guide-content';
import { normalizePublicLocale } from '@/lib/public-locale';
import { buildPublicPageMetadata } from '@/lib/public-seo';

type Props = { searchParams: Promise<Record<string, string | string[] | undefined>> };
export async function generateMetadata({ searchParams }: Props): Promise<Metadata> {
  const query = await searchParams;
  const locale = normalizePublicLocale(typeof query.locale === 'string' ? query.locale : '');
  const copy = guideCopy(locale);
  return buildPublicPageMetadata({ title: copy.nav, description: copy.intro, path: '/guides', countryCode: 'CA', locale, index: isGuideIndexableQuery(query) });
}
export default async function GuidesPage({ searchParams }: Props) {
  const query = await searchParams;
  const locale = normalizePublicLocale(typeof query.locale === 'string' ? query.locale : '');
  const copy = guideCopy(locale);
  return <main className="mx-auto w-full min-w-0 max-w-5xl px-4 py-7 md:px-6 md:py-10">
    <header className="mb-7">
      <p className="text-xs font-medium text-muted-foreground">{copy.scope}</p>
      <h1 className="mt-3 text-balance font-display text-3xl font-semibold leading-tight tracking-tight md:text-5xl">{copy.title}</h1>
      <p className="mt-4 max-w-2xl text-sm leading-6 text-muted-foreground">{copy.intro}</p>
    </header>
    <nav aria-label={copy.nav} className="grid border-t border-border md:grid-cols-2" data-guide-list>
      {GUIDE_SLUGS.map((slug, index) => <Link key={slug} href={guideHref(slug, locale)} className={`group grid min-w-0 gap-3 border-b border-border py-6 md:px-5 ${index % 2 === 0 ? 'md:border-r' : ''}`}>
        <h2 className="text-xl font-semibold tracking-tight group-hover:underline group-hover:underline-offset-4">{copy.topics[slug]}</h2>
        <p className="text-sm leading-6 text-muted-foreground">{guideContent(slug, locale).intro}</p>
        <span className="mt-1 flex items-center gap-2 text-sm font-medium text-primary">{copy.read}<ArrowRight className="size-4" aria-hidden="true" /></span>
      </Link>)}
    </nav>
    <GuideEditorial locale={locale} />
  </main>;
}
