import { Suspense } from 'react';
import type { Metadata } from 'next';
import { ComparisonSurface } from '@/components/fpds/public/comparison-surface';
import { comparisonCopy } from '@/lib/public-comparison-copy';
import { parseComparison } from '@/lib/public-comparison';

type Props = { searchParams: Promise<Record<string, string | string[] | undefined>> };
export async function generateMetadata({ searchParams }: Props): Promise<Metadata> {
  const params = await searchParams;
  const locale = Array.isArray(params.locale) ? params.locale[0] : params.locale;
  const copy = comparisonCopy(parseComparison(new URLSearchParams({ locale: locale ?? 'en' })).locale);
  return { title: copy.title, description: copy.empty, robots: { index: false, follow: true } };
}
export default async function ComparePage({ searchParams }: Props) {
  const params = await searchParams;
  const locale = Array.isArray(params.locale) ? params.locale[0] : params.locale;
  return <Suspense fallback={<main className="mx-auto max-w-7xl px-4 py-8"><h1>{comparisonCopy(locale ?? 'en').title}</h1><p role="status">{comparisonCopy(locale ?? 'en').loading}</p></main>}><ComparisonSurface /></Suspense>;
}
