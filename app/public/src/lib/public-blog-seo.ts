import type { Metadata } from 'next';
import type { BlogPath } from '@/lib/public-blog';
import { buildPublicPageMetadata, buildPublicLanguageAlternates } from '@/lib/public-seo';

export function blogLanguageAlternates(path: BlogPath, country: string) {
  const languages: Record<string, string> = buildPublicLanguageAlternates(path, country);
  if (country === 'US') {
    languages['en-US'] = languages['en-CA'];
    delete languages['en-CA'];
  }
  return languages;
}
export function buildBlogMetadata(input: { title: string; description: string; path: BlogPath; countryCode: string; locale: string; index: boolean }): Metadata {
  const metadata = buildPublicPageMetadata(input);
  return { ...metadata,
    // Article copy already names its market; keep snippets concise.
    title: input.title, description: input.description,
    alternates: { ...metadata.alternates, languages: blogLanguageAlternates(input.path, input.countryCode) },
    openGraph: { ...metadata.openGraph, title: `${input.title} — SwitchaBank`, description: input.description,
      ...(input.countryCode === 'US' ? {
        locale: input.locale === 'ko' ? 'ko_KR' : input.locale === 'ja' ? 'ja_JP' : 'en_US',
        alternateLocale: ['en_US', 'ko_KR', 'ja_JP'].filter(locale => locale !== (input.locale === 'ko' ? 'ko_KR' : input.locale === 'ja' ? 'ja_JP' : 'en_US'))
      } : {}) },
    twitter: { ...metadata.twitter, title: `${input.title} — SwitchaBank`, description: input.description }
  };
}
