import { ArrowDown, ArrowRight } from 'lucide-react';
import type { BlogContent } from '@/lib/public-blog-content';

export function BlogInfographic({ infographic }: { infographic: NonNullable<BlogContent['infographic']> }) {
  return <figure data-blog-infographic className="mt-8 border-y border-border bg-secondary/40 px-5 py-6 md:px-6">
    <figcaption className="text-sm font-semibold">{infographic.title}</figcaption>
    <ol className="mt-5 grid gap-5 md:grid-cols-3 md:gap-6">
      {infographic.steps.map((step, index) => <li key={step.title} className="relative flex min-w-0 items-start gap-3 md:block">
        <span className="inline-flex size-8 shrink-0 items-center justify-center rounded-full bg-primary font-mono text-xs font-semibold text-primary-foreground">0{index + 1}</span>
        <div className="md:mt-3"><p className="text-xl font-semibold tracking-tight">{step.title}</p><p className="mt-1 text-sm leading-6 text-muted-foreground">{step.text}</p></div>
        {index < infographic.steps.length - 1 ? <><ArrowRight aria-hidden="true" className="absolute right-0 top-2 hidden size-4 text-primary md:block" /><ArrowDown aria-hidden="true" className="absolute left-2 top-10 size-4 text-primary md:hidden" /></> : null}
      </li>)}
    </ol>
  </figure>;
}

export function BlogYieldChart({ example }: { example: BlogContent['example'] }) {
  const chart = example.chart;
  if (!chart) return null;
  const maximum = Math.max(...chart.values);
  return <div data-blog-yield-chart className="mt-5">
    <dl className="grid gap-5">{example.rows.map((row, index) => <div key={row[0]}>
      <div className="flex flex-wrap items-baseline justify-between gap-2"><dt className="text-sm font-semibold">{row[0]}</dt><dd className="font-mono text-xl font-semibold text-primary">{row[2]}</dd></div>
      <div aria-hidden="true" className="mt-2 h-5 bg-muted"><div className="h-full bg-primary" style={{ width: `${chart.values[index] / maximum * 100}%` }} /></div>
      <dd className="mt-2 font-mono text-xs leading-6 text-muted-foreground">{row[1]}</dd>
    </div>)}</dl>
    <p className="mt-5 border-t border-border pt-4 text-base font-semibold">{chart.difference}</p>
  </div>;
}
