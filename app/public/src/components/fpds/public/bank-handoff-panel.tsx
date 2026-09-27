import { ExternalLink } from 'lucide-react';
import type { PublicProduct } from '@/lib/public-api';
import { bankHandoffCopy, handoffConditions, handoffCost, officialDestination } from '@/lib/public-bank-handoff';
import { getPublicRateMetric } from '@/lib/public-rate';
import { ProductVerification } from '@/components/fpds/public/product-verification';
import { TrackedOfficialBankLink } from '@/components/fpds/public/product-engagement-link';
import { Button } from '@/components/ui/button';

export function BankHandoffPanel({ product, locale, compact = false }: { product: PublicProduct; locale: string; compact?: boolean }) {
  const copy = bankHandoffCopy(locale);
  const destination = officialDestination(product.product_url);
  const rate = getPublicRateMetric(product, locale);
  const cost = handoffCost(product, locale);
  const conditions = handoffConditions(product, locale);
  const facts = compact ? conditions : [
    { key: 'currency', label: copy.currency, value: product.currency || copy.bank },
    ...((product.product_type !== 'chequing' || product.rate?.source_text || product.rate?.comparable_rate != null) ? [{ key: 'rate', label: rate.label, value: product.rate?.source_text || rate.value }] : []),
    ...(cost ? [cost] : []), ...conditions
  ];
  return <section className="mt-5 min-w-0 border-t border-border pt-4" data-bank-handoff aria-label={copy.title}>
    <h2 className="text-sm font-semibold">{copy.title}</h2>
    <dl className={compact ? 'mt-3 grid gap-3' : 'mt-3 grid grid-cols-2 gap-x-6 gap-y-3 lg:grid-cols-3'}>
      {facts.map(fact => <div key={fact.key} className="min-w-0">
        <dt className="text-xs text-muted-foreground">{fact.label}</dt>
        <dd className="mt-1 text-sm leading-5 [overflow-wrap:anywhere]">{fact.value}</dd>
      </div>)}
    </dl>
    {!compact ? <ProductVerification product={product} locale={locale} /> : null}
    <div className={compact ? 'mt-4 grid gap-2' : 'mt-4 flex flex-wrap items-center gap-x-5 gap-y-2'}>
      {destination ? <>
        <Button asChild variant={compact ? 'outline' : 'default'} className="min-h-11">
          <TrackedOfficialBankLink countryCode={product.country_code} productId={product.product_id} href={destination.href}>
            {copy.action}<ExternalLink className="size-4 shrink-0" aria-hidden="true" />
            <span className="sr-only">({copy.external})</span>
          </TrackedOfficialBankLink>
        </Button>
        <p className="min-w-0 text-xs leading-5 text-muted-foreground [overflow-wrap:anywhere]">
          <span className="sr-only">{copy.domain}: </span>{destination.domain}<span className="block">{copy.external}</span>
        </p>
      </> : <p className="text-xs text-muted-foreground">{copy.unavailable}</p>}
    </div>
  </section>;
}
