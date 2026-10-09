import type { PublicProductMetric } from '@/lib/public-product-presentation';
import { ratePresentationCopy } from '@/lib/public-rate-presentation';

export function ProductMetricValue({ metric, locale }: { metric: PublicProductMetric; locale: string }) {
  return <>
    <span className={metric.entries?.length ? "block text-sm font-medium tracking-normal text-muted-foreground" : undefined}>{metric.value}</span>
    {metric.entries?.length ? <dl className="mt-3 grid gap-2 text-sm font-normal tracking-normal">
      {metric.entries.slice(0, 2).map((entry, i) => <div key={i} className="flex flex-wrap items-baseline justify-between gap-x-3 gap-y-1 border-t border-border pt-2">
        <dt className="min-w-0 break-words leading-6">{entry.label}</dt><dd className="text-2xl font-semibold tabular-nums">{entry.value}</dd>
      </div>)}
    </dl> : null}
    {metric.details ? <details data-rate-details className="mt-3 text-sm font-normal leading-7 tracking-normal text-foreground">
      <summary className="min-h-11 cursor-pointer py-2 font-medium text-primary underline-offset-4 hover:underline focus-visible:outline-2 focus-visible:outline-ring">{ratePresentationCopy(locale).conditions}</summary>
      {metric.entries && metric.entries.length > 2 ? <dl className="mb-4 grid gap-2">
        {metric.entries.slice(2).map((entry, i) => <div key={i} className="flex flex-wrap justify-between gap-x-3 border-t border-border pt-2"><dt>{entry.label}</dt><dd className="text-base font-semibold tabular-nums">{entry.value}</dd></div>)}
      </dl> : null}
      <p className="whitespace-pre-line break-words border-l-2 border-border pl-3">{metric.details}</p>
    </details> : null}
  </>;
}
