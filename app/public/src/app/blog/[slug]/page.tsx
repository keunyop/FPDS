import type { Metadata } from 'next';
import Link from 'next/link';
import { notFound } from 'next/navigation';
import { ArrowRight, ArrowUpRight } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { BankLogo } from '@/components/fpds/public/bank-logo';
import { PublicFeedbackDialog } from '@/components/fpds/public/public-feedback-dialog';
import { PublicStructuredData } from '@/components/fpds/public/public-structured-data';
import { BLOG_POSTS, blogCopy, blogHref, isBlogSlug, isBlogIndexableQuery } from '@/lib/public-blog';
import { BLOG_SOURCES, blogContent } from '@/lib/public-blog-content';
import { curatedCatalogHref } from '@/lib/public-curated';
import { guideCopy, guideHref, type GuideSlug } from '@/lib/public-guides';
import { normalizePublicLocale } from '@/lib/public-locale';
import { buildPublicPageMetadata, buildPublicSeoUrl, PUBLIC_SITE_ORIGIN } from '@/lib/public-seo';

type Props = { params: Promise<{ slug: string }>; searchParams: Promise<Record<string, string | string[] | undefined>> };
export async function generateMetadata({ params, searchParams }: Props): Promise<Metadata> {
  const { slug } = await params;
  if (!isBlogSlug(slug)) return { robots: { index: false, follow: true } };
  const query = await searchParams;
  const locale = normalizePublicLocale(typeof query.locale === 'string' ? query.locale : '');
  const content = blogContent(slug, locale);
  const post = BLOG_POSTS.find(item => item.slug === slug)!;
  const metadata = buildPublicPageMetadata({ title: content.title, description: content.description, path: `/blog/${slug}`, countryCode: 'CA', locale, index: isBlogIndexableQuery(query) });
  const images = [{ url: `${PUBLIC_SITE_ORIGIN}/blog/opengraph-image`, width: 1200, height: 630, alt: content.title }];
  return { ...metadata, authors: [{ name: 'SwitchaBank', url: `${PUBLIC_SITE_ORIGIN}/blog` }],
    openGraph: { ...metadata.openGraph, type: 'article', publishedTime: post.publishedAt, modifiedTime: post.modifiedAt, authors: ['SwitchaBank'], images },
    twitter: { ...metadata.twitter, images: images.map(image => image.url) }
  };
}
export default async function BlogArticlePage({ params, searchParams }: Props) {
  const { slug } = await params;
  if (!isBlogSlug(slug)) notFound();
  const query = await searchParams;
  const locale = normalizePublicLocale(typeof query.locale === 'string' ? query.locale : '');
  const copy = blogCopy(locale);
  const content = blogContent(slug, locale);
  const post = BLOG_POSTS.find(item => item.slug === slug)!;
  const url = buildPublicSeoUrl(`/blog/${slug}`, locale, 'CA');
  return <main className="mx-auto w-full min-w-0 max-w-6xl px-4 py-6 md:px-6 md:py-9">
    <nav aria-label={copy.nav} className="mb-5 flex flex-wrap items-center gap-2 text-xs text-muted-foreground">
      <Link className="inline-flex min-h-11 items-center hover:underline" href={locale === 'en' ? '/' : `/?locale=${locale}`}>{copy.home}</Link>
      <span aria-hidden="true">/</span><Link className="inline-flex min-h-11 items-center hover:underline" href={blogHref(null, locale)}>{copy.nav}</Link>
      <span aria-hidden="true">/</span><span>{copy.scope}</span>
    </nav>
    <article>
      <header className="max-w-4xl border-b border-border pb-7">
        <p className="text-xs font-semibold tracking-wide text-primary">{copy.scope}</p>
        <h1 className="mt-4 text-balance font-display text-3xl font-semibold leading-tight tracking-tight md:text-5xl">{content.title}</h1>
        <p className="mt-5 max-w-3xl text-base leading-8 text-muted-foreground md:text-lg">{content.intro}</p>
        <div className="mt-5 flex flex-wrap gap-x-4 gap-y-2 text-xs leading-5 text-muted-foreground">
          <span className="font-medium text-foreground">{copy.by}</span>
          <span>{copy.published} <time dateTime={post.publishedAt}>{post.publishedAt}</time></span>
          <span>{post.minutes} {copy.minutes}</span>
        </div>
        <p className="mt-2 text-xs leading-5 text-muted-foreground">{copy.checked} <time dateTime={post.sourcesCheckedAt}>{post.sourcesCheckedAt}</time></p>
      </header>
      <div className="mt-8 grid min-w-0 gap-8 lg:grid-cols-[13rem_minmax(0,1fr)] lg:gap-12">
        <aside className="min-w-0">
          <nav aria-label={copy.contents} className="border-y border-border py-4 lg:sticky lg:top-24">
            <p className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">{copy.contents}</p>
            <ol className="mt-2 grid">
              <li><Link href="#account-comparison" className="inline-flex min-h-11 items-center text-sm leading-6 hover:text-primary hover:underline">{copy.comparison}</Link></li>
              {content.sections.map(section => <li key={section.id}><Link href={`#${section.id}`} className="inline-flex min-h-11 items-center py-2 text-sm leading-6 hover:text-primary hover:underline">{section.title}</Link></li>)}
              <li><Link href="#article-sources" className="inline-flex min-h-11 items-center text-sm hover:text-primary hover:underline">{copy.sources}</Link></li>
            </ol>
          </nav>
        </aside>
        <div className="min-w-0 max-w-3xl">
          <section className="border-l-4 border-primary bg-secondary/50 px-5 py-5" aria-labelledby="article-takeaway">
            <h2 id="article-takeaway" className="text-xs font-semibold uppercase tracking-wider text-primary">{copy.takeaway}</h2>
            <p className="mt-2 text-base font-medium leading-8">{content.takeaway}</p>
          </section>
          <section id="account-comparison" className="mt-9 scroll-mt-24" aria-labelledby="account-comparison-title">
            <h2 id="account-comparison-title" className="text-xl font-semibold tracking-tight">{copy.comparison}</h2>
            <p className="mt-2 text-xs leading-6 text-muted-foreground">{copy.checked}: {post.sourcesCheckedAt} · CAD</p>
            <table className="mt-4 block w-full border-y border-border text-left text-sm md:table">
              <caption className="sr-only">{copy.comparison}</caption>
              <thead className="sr-only md:not-sr-only md:table-header-group"><tr>{copy.tableHeaders.map(label => <th key={label} scope="col" className="border-b border-border bg-muted/60 px-3 py-3 text-xs font-semibold">{label}</th>)}</tr></thead>
              <tbody className="block md:table-row-group">{content.rows.map(row => <tr key={row.code} className="grid gap-3 border-b border-border py-5 last:border-0 md:table-row md:py-0">
                <th scope="row" className="flex items-center gap-3 text-left md:table-cell md:w-44 md:px-3 md:py-5 md:align-top">
                  <BankLogo bankCode={row.code} bankName={row.bank} size="sm" />
                  <span className="block text-sm font-semibold leading-6">{row.bank}<span lang="en" className="block text-xs font-normal text-muted-foreground">{row.name}</span></span>
                </th>
                <td className="md:px-3 md:py-5 md:align-top"><span className="mr-3 text-xs text-muted-foreground md:hidden">{copy.tableHeaders[1]}</span><span className="whitespace-nowrap font-mono font-semibold">{row.fee}</span></td>
                <td className="leading-7 md:px-3 md:py-5 md:align-top">{row.detail} <SourceLink id={row.source} /></td>
              </tr>)}</tbody>
            </table>
          </section>
          <div className="mt-10 grid gap-10">
            {content.sections.map(section => <section id={section.id} key={section.id} className="scroll-mt-24">
              <h2 className="text-xl font-semibold leading-snug tracking-tight md:text-2xl">{section.title}</h2>
              <div className="mt-4 grid gap-4 text-base leading-8">{section.paragraphs.map(paragraph => <p key={paragraph}>{paragraph}</p>)}</div>
              {section.sources ? <p className="mt-2 text-xs text-muted-foreground">{copy.sources}: {section.sources.map(id => <SourceLink key={id} id={id} />)}</p> : null}
              {section.id === 'worked-example' ? <figure className="mt-5 border-y border-border bg-card px-4 py-5 md:px-6">
                <p className="text-xs font-medium text-primary">{copy.example}</p>
                <figcaption className="mt-2 text-base font-semibold leading-7">{content.example.title}</figcaption>
                <p className="mt-2 text-sm leading-7 text-muted-foreground">{content.example.intro}</p>
                <dl className="mt-4 divide-y divide-border">{content.example.rows.map(row => <div key={row[0]} className="grid gap-2 py-4">
                  <dt className="text-sm font-semibold">{row[0]}</dt><dd className="break-words font-mono text-xs leading-6 text-muted-foreground">{row[1]}</dd>
                  <dd className="text-lg font-semibold text-primary">{content.example.headers[2]}: {row[2]}</dd>
                </div>)}</dl>
                <p className="mt-3 text-xs leading-6 text-muted-foreground">{content.example.note}</p>
              </figure> : null}
            </section>)}
          </div>
          <section className="mt-10 border-t border-border pt-7" aria-labelledby="article-checklist">
            <h2 id="article-checklist" className="text-xl font-semibold">{copy.checklist}</h2>
            <ol className="mt-4 list-decimal space-y-3 pl-5 text-base leading-8">{content.checklist.map(item => <li key={item} className="pl-2">{item}</li>)}</ol>
          </section>
          <section className="mt-9 bg-secondary/60 px-5 py-6 md:px-7" aria-labelledby="blog-compare">
            <h2 id="blog-compare" className="text-xl font-semibold leading-8">{copy.compare}</h2>
            <p className="mt-3 text-sm leading-7">{copy.compareBody}</p>
            <Button asChild className="mt-5 h-auto min-h-11 whitespace-normal py-3"><Link data-blog-comparison href={curatedCatalogHref('savings-accounts', locale)}>{copy.action}<ArrowRight className="size-4 shrink-0" aria-hidden="true" /></Link></Button>
          </section>
          <section className="mt-10" aria-labelledby="blog-faq">
            <h2 id="blog-faq" className="text-xl font-semibold">{copy.faq}</h2>
            <div className="mt-4 divide-y divide-border">{content.faq.map(item => <div key={item.question} className="py-4">
              <h3 className="text-base font-semibold leading-7">{item.question}</h3><p className="mt-2 text-sm leading-7">{item.answer}</p>
            </div>)}</div>
          </section>
          <section className="mt-8 border-t border-border pt-6" aria-labelledby="blog-related">
            <h2 id="blog-related" className="text-lg font-semibold">{copy.related}</h2>
            <ul className="mt-2">{(['base-and-promotional-rates', 'monthly-fee-waivers', 'switching-bank-accounts'] as GuideSlug[]).map(guide => <li key={guide}>
              <Link href={guideHref(guide, locale)} className="inline-flex min-h-11 items-center gap-2 py-2 text-sm text-primary hover:underline">{guideCopy(locale).topics[guide]}<ArrowRight className="size-4 shrink-0" aria-hidden="true" /></Link>
            </li>)}</ul>
          </section>
          <section id="article-sources" className="mt-8 scroll-mt-24 border-t border-border pt-6">
            <h2 className="text-lg font-semibold">{copy.sources}</h2>
            <p className="mt-2 text-xs leading-6 text-muted-foreground">{copy.sourcesNote}</p>
            <ol className="mt-3 list-decimal pl-5 text-sm">{BLOG_SOURCES.map(source => <li key={source.id}>
              <a href={source.href} lang="en" className="inline-flex min-h-11 items-center gap-2 py-2 leading-6 underline underline-offset-4">{source.title}<ArrowUpRight className="size-4 shrink-0" aria-hidden="true" /></a>
            </li>)}</ol>
          </section>
          <section className="mt-7 border-t border-border pt-5 text-xs leading-6 text-muted-foreground" aria-labelledby="blog-editorial">
            <h2 id="blog-editorial" className="text-sm font-semibold text-foreground">{copy.editorial}</h2>
            <p className="mt-2">{copy.method}</p><p className="mt-2">{copy.disclosure}</p>
            <p className="mt-2">{copy.correction}</p>
            <div className="mt-3"><PublicFeedbackDialog countryCode="CA" locale={locale} mode="site_feedback" /></div>
          </section>
          <Link href={blogHref(null, locale)} className="mt-6 inline-flex min-h-11 items-center text-sm font-medium text-primary hover:underline">{copy.all}</Link>
        </div>
      </div>
    </article>
    <PublicStructuredData data={{ '@context': 'https://schema.org', '@graph': [
      { '@type': 'BlogPosting', '@id': `${url}#article`, headline: content.title, description: content.description, inLanguage: locale, url, mainEntityOfPage: url,
        datePublished: post.publishedAt, dateModified: post.modifiedAt, image: [`${PUBLIC_SITE_ORIGIN}/blog/opengraph-image`],
        author: { '@type': 'Organization', name: 'SwitchaBank', url: `${buildPublicSeoUrl('/blog', locale, 'CA')}` },
        publisher: { '@id': `${PUBLIC_SITE_ORIGIN}/#organization` }, citation: BLOG_SOURCES.map(source => source.href), about: 'Canadian savings account comparisons' },
      { '@type': 'BreadcrumbList', itemListElement: [
        { '@type': 'ListItem', position: 1, name: copy.home, item: buildPublicSeoUrl('/', locale, 'CA') },
        { '@type': 'ListItem', position: 2, name: copy.nav, item: buildPublicSeoUrl('/blog', locale, 'CA') },
        { '@type': 'ListItem', position: 3, name: content.title, item: url }
      ] }
    ] }} />
  </main>;
}
function SourceLink({ id }: { id: typeof BLOG_SOURCES[number]['id'] }) {
  const index = BLOG_SOURCES.findIndex(source => source.id === id);
  const source = BLOG_SOURCES[index];
  return <a href={source.href} aria-label={source.title} className="inline-flex min-h-11 min-w-11 items-center justify-center text-xs font-medium text-primary underline underline-offset-4">[{index + 1}]</a>;
}
