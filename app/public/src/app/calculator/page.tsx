import { Suspense } from 'react';
import type { Metadata } from 'next';
import { ScenarioSurface } from '@/components/fpds/public/scenario-surface';
import { scenarioCopy } from '@/lib/public-scenario-copy';
import { comparisonCopy } from '@/lib/public-comparison-copy';
type Props = { searchParams: Promise<Record<string, string | string[] | undefined>> };
export async function generateMetadata({ searchParams }: Props): Promise<Metadata> {
  const params = await searchParams;
  const locale = Array.isArray(params.locale) ? params.locale[0] : params.locale;
  const copy = scenarioCopy(locale ?? 'en');
  return { title: copy.title, description: copy.intro, robots: { index: false, follow: true } };
}
export default async function CalculatorPage({ searchParams }: Props) {
  const params = await searchParams;
  const locale = Array.isArray(params.locale) ? params.locale[0] : params.locale;
  return <Suspense fallback={<main className="mx-auto max-w-5xl px-4 py-8"><h1>{scenarioCopy(locale ?? 'en').title}</h1><p role="status">{comparisonCopy(locale ?? 'en').loading}</p></main>}><ScenarioSurface /></Suspense>;
}
