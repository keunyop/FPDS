"use client";
import { useEffect, useState } from 'react';
import { useSearchParams } from 'next/navigation';
import Link from 'next/link';
import { ExternalLink, RefreshCw } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { useComparison } from '@/components/fpds/public/comparison-provider';
import { TrackedOfficialBankLink } from '@/components/fpds/public/product-engagement-link';
import { ProductVerification } from '@/components/fpds/public/product-verification';
import { comparisonHref, parseComparison, type ComparisonResult } from '@/lib/public-comparison';
import { comparisonCopy } from '@/lib/public-comparison-copy';
import { depositCopy, depositOptions, depositPeriod, depositReason } from '@/lib/public-deposit';
import { compareScenario, scenarioAmount, scenarioPeriods, type ScenarioValue } from '@/lib/public-scenario';
import { scenarioCopy } from '@/lib/public-scenario-copy';
import { formatPublicCurrency } from '@/lib/public-product-presentation';
import type { PublicProduct } from '@/lib/public-api';

export function ScenarioSurface() {
  const params = useSearchParams();
  const scope = parseComparison(new URLSearchParams(params.toString()));
  const comparison = useComparison(scope.countryCode);
  const ids = scope.ids.length ? scope.ids : comparison.entries.map(item => item.id);
  const href = comparisonHref(ids, scope);
  const copy = scenarioCopy(scope.locale), listCopy = comparisonCopy(scope.locale);
  const [revision, setRevision] = useState(0);
  const requestKey = `${href}:${revision}`;
  const [loaded, setLoaded] = useState<{ key: string; items: ComparisonResult[] } | null>(null);
  useEffect(() => {
    if (!scope.valid || ids.length < 2) return;
    const controller = new AbortController();
    let disposed = false;
    const timer = window.setTimeout(() => controller.abort(), 12000);
    async function read() {
      try {
        const response = await fetch(href.replace('/compare?', '/api/public/compare?'), { cache: 'no-store', signal: controller.signal });
        if (!response.ok) throw Error('Unavailable');
        const data = await response.json() as { items: ComparisonResult[] };
        const expected = parseComparison(new URLSearchParams(href.split('?')[1])).ids;
        if (!Array.isArray(data.items) || data.items.length !== expected.length || data.items.some((item, i) => item.id !== expected[i]
          || !['ready', 'missing', 'error'].includes(item.status) || (item.status === 'ready' && (!item.product || item.product.product_id !== item.id
            || item.product.country_code !== scope.countryCode || item.product.status !== 'active')))) throw Error('Invalid response');
        if (!disposed) setLoaded({ key: requestKey, items: data.items });
      } catch {
        if (!disposed) setLoaded({ key: requestKey, items: parseComparison(new URLSearchParams(href.split('?')[1])).ids.map(id => ({ id, status: 'error' })) });
      } finally { window.clearTimeout(timer); }
    }
    void read();
    return () => { disposed = true; controller.abort(); window.clearTimeout(timer); };
  }, [href, requestKey, scope.valid, scope.countryCode, ids.length]);
  useEffect(() => {
    const refresh = () => { if (document.visibilityState === 'visible') setRevision(value => value + 1); };
    document.addEventListener('visibilitychange', refresh);
    return () => document.removeEventListener('visibilitychange', refresh);
  }, []);
  const items = loaded?.key === requestKey ? loaded.items : null;
  const previousItems = loaded?.key.startsWith(`${href}:`) ? loaded.items : null;
  return <main className="mx-auto min-h-[60vh] w-full max-w-5xl px-4 py-8 md:px-6" data-scenario-page>
    <div className="mb-6 flex flex-wrap items-start justify-between gap-3 border-b border-border pb-5">
      <div><h1 className="font-display text-3xl font-semibold tracking-tight">{copy.title}</h1><p className="mt-2 text-sm text-muted-foreground">{copy.intro}</p></div>
      <Button asChild variant="outline"><Link href={href}>{listCopy.view}</Link></Button>
    </div>
    {!scope.valid ? <p role="alert">{listCopy.invalid}</p> : ids.length < 2 ? <p className="py-8 text-muted-foreground">{copy.choose}</p>
      : !items && !previousItems ? <p role="status" className="py-8">{listCopy.loading}</p>
      : <ScenarioInputs key={href} items={items ?? previousItems!} loading={!items} locale={scope.locale} />}
    {scope.valid && ids.length >= 2 ? <Button variant="ghost" className="mt-5" disabled={!items} onClick={() => setRevision(value => value + 1)}><RefreshCw className="size-4" aria-hidden="true" />{listCopy.refresh}</Button> : null}
  </main>;
}

function ScenarioInputs({ items, locale, loading }: { items: ComparisonResult[]; locale: string; loading: boolean }) {
  const copy = scenarioCopy(locale), deposit = depositCopy(locale), list = comparisonCopy(locale);
  const [first, setFirst] = useState(items[0]?.id ?? '');
  const [second, setSecond] = useState(items[1]?.id ?? '');
  const [amount, setAmount] = useState('20000');
  const [term, setTerm] = useState('');
  const a = items.find(item => item.id === first), b = items.find(item => item.id === second);
  const products = [!loading && a?.status === 'ready' ? a.product : undefined, !loading && b?.status === 'ready' ? b.product : undefined];
  const periods = products[0] && products[1] ? scenarioPeriods(products[0], products[1]) : [];
  const period = term ? periods.find(p => p.key === term) : periods.find(p => p.key === 'm12') ?? periods[0];
  const result = products[0] && products[1] ? compareScenario(products[0], products[1], period, amount) : null;
  function reasonText(reason: string | null) { return copy.reasons[reason as keyof typeof copy.reasons] ?? depositReason(reason, locale); }
  function money(value: number | null, product: PublicProduct, signed = false) {
    return value === null ? '—' : `${signed && value > 0 ? '+' : ''}${formatPublicCurrency(value, product.currency, locale)}`;
  }
  function metric(label: string, value: ScenarioValue, product: PublicProduct) {
    return <div className="min-w-0 border-t border-border py-4"><dt className="text-xs text-muted-foreground">{label}</dt>
      <dd className="mt-2 break-words text-xl font-semibold tabular-nums">{money(value.value, product)}</dd>
      {value.reason ? <p className="mt-1 text-xs text-muted-foreground">{reasonText(value.reason)}</p> : null}</div>;
  }
  return <div className="grid gap-5">
    <div className="grid gap-4 sm:grid-cols-2">
      {[{ value: first, other: second, set: setFirst, label: copy.first }, { value: second, other: first, set: setSecond, label: copy.second }].map(control => <label key={control.label} className="grid min-w-0 gap-2 text-sm font-medium">{control.label}
        <select className="min-h-11 w-full min-w-0 rounded-md border border-input bg-background px-3" aria-label={control.label} disabled={loading} value={control.value} onChange={event => { control.set(event.target.value); setTerm(''); }}>
          {items.map(item => <option key={item.id} value={item.id} disabled={item.id === control.other}>{item.product?.product_name ?? `${item.id} · ${list[item.status === 'missing' ? 'missing' : 'error']}`}</option>)}
        </select></label>)}
    </div>
    {result?.reason ? <p role="status" className="text-sm text-muted-foreground">{reasonText(result.reason)}</p> : null}
    {periods.length ? <div className="grid gap-4 border-y border-border py-5 sm:grid-cols-2">
      <label className="grid gap-2 text-sm font-medium">{deposit.amount} ({products[0]?.currency})
        <Input data-scenario-amount className="min-h-11" type="text" inputMode="decimal" autoComplete="off" maxLength={32} value={amount} aria-invalid={scenarioAmount(amount) === null} aria-describedby={scenarioAmount(amount) === null ? "scenario-privacy scenario-input-error" : "scenario-privacy"} onChange={event => setAmount(event.target.value)} />
      </label>
      <label className="grid gap-2 text-sm font-medium">{deposit.period}
        <select className="min-h-11 min-w-0 rounded-md border border-input bg-background px-3" aria-label={deposit.period} value={period?.key ?? term} onChange={event => setTerm(event.target.value)}>{!period ? <option value={term} disabled>{copy.reasons.term_mismatch}</option> : null}{periods.map(p => <option key={p.key} value={p.key}>{depositPeriod({ ...p, rate: 0, minimum_deposit: null }, locale)}</option>)}</select>
      </label>
      {scenarioAmount(amount) === null ? <p id="scenario-input-error" role="status" className="text-xs text-destructive sm:col-span-2">{copy.reasons.amount_invalid}</p> : null}
      <p id="scenario-privacy" className="text-xs text-muted-foreground sm:col-span-2">{copy.privacy}</p>
    </div> : null}
    <div className="grid gap-5 sm:grid-cols-2" aria-live="polite">
      {[a, b].map((item, index) => {
        const product = products[index];
        return <article key={index} className="min-w-0 border border-border bg-card p-5" data-scenario-result>
          <p className="text-xs font-medium text-muted-foreground">{index === 0 ? copy.first : copy.second}{product ? ` · ${product.currency}` : ''}</p>
          {product ? <><h2 className="mt-2 break-words text-lg font-semibold">{product.product_name}</h2><p className="mt-1 text-sm text-muted-foreground">{product.bank_name}</p><ProductVerification product={product} locale={locale} />
            {result && !result.interest[index].reason ? <p className="mt-3 text-xs text-muted-foreground">{deposit.annual}: {depositOptions(product).find(option => option.key === (product.product_type === 'gic' ? period?.key : 'ongoing'))?.rate}%</p> : null}
            {result && !result.reason ? <dl className="mt-4">{metric(deposit.interest, result.interest[index], product)}{metric(copy.fees, result.fees[index], product)}</dl> : null}
            {product.product_url ? <TrackedOfficialBankLink className="inline-flex min-h-11 items-center gap-1.5 text-sm font-medium text-primary hover:underline" countryCode={product.country_code} productId={product.product_id} href={product.product_url}>{deposit.bank}<ExternalLink className="size-3.5" aria-hidden="true" /></TrackedOfficialBankLink> : null}
          </> : <p role="status" className="mt-3 text-sm">{loading ? list.loading : item?.status === 'missing' ? list.missing : list.error}</p>}
        </article>;
      })}
    </div>
    {result && products[0] && !result.reason ? <section className="border-y border-border py-5" aria-live="polite" data-scenario-difference>
      <div className="flex flex-wrap items-baseline justify-between gap-2"><h2 className="text-base font-semibold">{copy.difference}</h2><span className="text-xs text-muted-foreground">{copy.direction}</span></div>
      <dl className="mt-4 grid gap-4 sm:grid-cols-2">{[[copy.interestDifference, result.interestDifference], [copy.feeDifference, result.feeDifference]].map(([label, value]) => <div key={String(label)}><dt className="text-xs text-muted-foreground">{label}</dt><dd className="mt-1 break-words text-2xl font-semibold tabular-nums">{money(value as number | null, products[0]!, true)}</dd></div>)}</dl>
    </section> : null}
    <p className="text-xs leading-5 text-muted-foreground">{copy.note}</p>
    <details className="text-xs leading-5 text-muted-foreground"><summary className="min-h-11 cursor-pointer py-3 font-medium text-foreground">{copy.assumptions}</summary><p>{copy.formula}</p></details>
  </div>;
}
