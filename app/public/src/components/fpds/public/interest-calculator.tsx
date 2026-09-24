"use client";

import { Calculator, ExternalLink } from "lucide-react";
import { useId, useState } from "react";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { TrackedOfficialBankLink } from "@/components/fpds/public/product-engagement-link";
import type { PublicProduct } from "@/lib/public-api";
import { depositCopy, depositOptions, depositPeriod, depositReason, estimateDeposit, startingDepositAmount } from "@/lib/public-deposit";
import { formatPublicCurrency } from "@/lib/public-product-presentation";

export function InterestCalculator({ product, locale }: { product: PublicProduct; locale: string }) {
  const copy = depositCopy(locale);
  const options = depositOptions(product);
  const [amount, setAmount] = useState(String(startingDepositAmount(product.minimum_balance, Math.max(product.minimum_deposit ?? 0, options[0]?.minimum_deposit ?? 0))));
  const [term, setTerm] = useState(options[0]?.key ?? '');
  const [days, setDays] = useState(365);
  const option = options.find(item => item.key === term);
  const reason = !product.deposit_terms ? 'basis_unknown' : product.deposit_terms.reason ?? product.deposit_terms.calculation_reason
    ?? (!option ? 'term_unknown' : null);
  const unavailable = !product.deposit_terms || Boolean(reason);
  const estimate = estimateDeposit(product, option, amount, days);
  const errorId = useId();
  return (
    <Card data-deposit-calculator>
      <CardHeader>
        <h2 className="flex items-center gap-2 text-base font-semibold"><Calculator className="size-4" aria-hidden="true" />{copy.title}</h2>
      </CardHeader>
      <CardContent className="grid gap-4">
        {unavailable ? <p className="text-sm text-muted-foreground">{copy.unavailable} · {depositReason(reason, locale)}</p> : <>
          <label className="grid gap-2 text-sm font-medium">{copy.amount} ({product.currency})
            <Input className="min-h-11" inputMode="decimal" type="text" value={amount} aria-invalid={estimate === null} aria-describedby={estimate === null ? errorId : undefined} onChange={event => setAmount(event.target.value)} />
          </label>
          <label className="grid gap-2 text-sm font-medium">{product.product_type === 'gic' ? copy.term : copy.period}
            {product.product_type === 'gic' ? <select className="min-h-11 min-w-0 rounded-md border border-input bg-background px-3" value={term} onChange={event => setTerm(event.target.value)}>
              {options.map(item => <option value={item.key} key={item.key}>{depositPeriod(item, locale)}</option>)}
            </select> : <select className="min-h-11 rounded-md border border-input bg-background px-3" value={days} onChange={event => setDays(Number(event.target.value))}>
              {[30, 90, 180, 365].map(value => <option key={value} value={value}>{value} {copy.days}</option>)}
            </select>}
          </label>
          {estimate === null ? <p id={errorId} role="status" className="text-xs text-destructive">{copy.inputError}</p> : null}
          <dl className="grid grid-cols-2 gap-3 border-y border-border py-4" aria-live="polite">
            <div><dt className="text-xs text-muted-foreground">{copy.annual}</dt><dd className="mt-1 font-semibold tabular-nums">{option?.rate}%</dd></div>
            <div><dt className="text-xs text-muted-foreground">{copy.interest}</dt><dd className="mt-1 font-semibold tabular-nums">{estimate === null ? '—' : formatPublicCurrency(estimate, product.currency, locale)}</dd></div>
          </dl>
          <p className="text-xs leading-5 text-muted-foreground">{copy.note}</p>
        </>}
        {product.product_url ? <TrackedOfficialBankLink className="inline-flex min-h-11 items-center gap-1.5 text-sm font-medium text-primary hover:underline" countryCode={product.country_code} productId={product.product_id} href={product.product_url}>
          {copy.bank}<ExternalLink className="size-3.5" aria-hidden="true" />
        </TrackedOfficialBankLink> : null}
      </CardContent>
    </Card>
  );
}
