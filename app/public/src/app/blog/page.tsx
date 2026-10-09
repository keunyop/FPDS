import type { Metadata } from 'next';
import Link from 'next/link';
import { ArrowRight } from 'lucide-react';
import { BlogVisual } from '@/components/fpds/public/blog-visual';
import { PublicStructuredData } from '@/components/fpds/public/public-structured-data';
import { blogPostsForCountry, blogCopy, blogMarketCopy, blogHref, isBlogIndexableQuery } from '@/lib/public-blog';
import { blogContent, blogPresentation } from '@/lib/public-blog-content';
import { guideCopy, guideHref } from '@/lib/public-guides';
import { normalizePublicLocale } from '@/lib/public-locale';
import { buildPublicSeoUrl } from '@/lib/public-seo';
import { buildBlogMetadata } from '@/lib/public-blog-seo';
import { formatPublicCountryName } from '@/lib/public-country';
import { normalizeCountryCodeValue } from '@/lib/public-query';

type Props = { searchParams: Promise<Record<string, string | string[] | undefined>> };
export async function generateMetadata({ searchParams }: Props): Promise<Metadata> {
  const query = await searchParams;
  const locale = normalizePublicLocale(typeof query.locale === 'string' ? query.locale : '');
  const copy = blogCopy(locale);
  const country = normalizeCountryCodeValue(typeof query.country_code === 'string' ? query.country_code : '');
  return buildBlogMetadata({ title: `${formatPublicCountryName(country, locale)} · ${copy.nav}`, description: copy.intro, path: '/blog', countryCode: country, locale, index: isBlogIndexableQuery(query, country) });
}
export default async function BlogPage({ searchParams }: Props) {
  const query = await searchParams;
  const locale = normalizePublicLocale(typeof query.locale === 'string' ? query.locale : '');
  const copy = blogCopy(locale);
  const country = normalizeCountryCodeValue(typeof query.country_code === 'string' ? query.country_code : '');
  const posts = blogPostsForCountry(country);
  const marketCopy = blogMarketCopy(locale);
  return <main className="mx-auto w-full min-w-0 max-w-6xl px-4 py-8 md:px-6 md:py-12">
    <header className="max-w-3xl pb-9 md:pb-12">
      <p className="text-xs font-semibold uppercase tracking-widest text-primary">SwitchaBank · {copy.nav} · {formatPublicCountryName(country, locale)}</p>
      <h1 className="mt-4 text-balance font-display text-4xl font-semibold leading-tight tracking-tight md:text-6xl">{copy.heading}</h1>
      <p className="mt-5 max-w-2xl text-base leading-7 text-muted-foreground">{copy.intro}</p>
    </header>
    <section aria-labelledby="blog-latest" className="border-t border-border">
      <h2 id="blog-latest" className="py-4 text-xs font-semibold uppercase tracking-widest text-muted-foreground">{copy.latest}</h2>
      {posts.length === 0 ? <div className="border-b border-border py-10"><h3 className="text-xl font-semibold">{marketCopy.empty}</h3><p className="mt-3 text-sm leading-7 text-muted-foreground">{marketCopy.emptyBody}</p></div> : null}
      {posts.map(post => {
        const article = blogContent(post.slug, locale);
        const presentation = blogPresentation(post.slug, locale);
        return <article key={post.slug} className="grid gap-6 border-b border-border py-8 md:grid-cols-[1fr_1.15fr] md:gap-10 md:pb-10">
          <BlogVisual banks={article.rows} issue={post.issue} />
          <div className="flex flex-col items-start justify-center">
            <p className="text-xs font-medium text-primary">{presentation.scope}</p>
            <h3 className="mt-3 text-balance text-2xl font-semibold leading-snug tracking-tight md:text-3xl">
              <Link href={blogHref(post.slug, locale)} className="underline-offset-4 hover:underline">{article.title}</Link>
            </h3>
            <p className="mt-4 text-sm leading-7 text-muted-foreground">{article.intro}</p>
            <p className="mt-4 text-xs text-muted-foreground"><time dateTime={post.publishedAt}>{post.publishedAt}</time> · {post.minutes} {copy.minutes}</p>
            <Link href={blogHref(post.slug, locale)} className="mt-4 inline-flex min-h-11 items-center gap-2 text-sm font-semibold text-primary hover:underline">{copy.read}<ArrowRight className="size-4" aria-hidden="true" /></Link>
          </div>
        </article>;
      })}
    </section>
    {country === 'CA' ? <aside className="mt-8 flex flex-col items-start justify-between gap-3 border-b border-border pb-6 sm:flex-row sm:items-center">
      <h2 className="text-lg font-semibold">{copy.related}</h2>
      <Link className="inline-flex min-h-11 items-center gap-2 text-sm font-medium text-primary hover:underline" href={guideHref(null, locale)}>{guideCopy(locale).nav}<ArrowRight className="size-4" aria-hidden="true" /></Link>
    </aside> : null}
    <PublicStructuredData data={{ '@context': 'https://schema.org', '@type': 'CollectionPage', name: copy.heading,
      description: copy.intro, url: buildPublicSeoUrl('/blog', locale, country), inLanguage: locale,
      mainEntity: { '@type': 'ItemList', itemListElement: posts.map((post, i) => ({
        '@type': 'ListItem', position: i + 1, url: buildPublicSeoUrl(`/blog/${post.slug}`, locale, post.country), name: blogContent(post.slug, locale).title
      })) } }} />
  </main>;
}
