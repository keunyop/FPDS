"use client";
import { useState } from "react";
import { ProductTopFive } from "@/components/fpds/public/product-top-five";
import { depositCopy, depositOptions, depositPeriod, depositGroupKey } from "@/lib/public-deposit";
import { getPublicMessages } from "@/lib/public-locale";
import type { PublicProduct } from "@/lib/public-api";
import { buildPublicHref, type DashboardPageFilters } from "@/lib/public-query";

export function DepositTopFive({ products, filters, unavailable }: { products: PublicProduct[]; filters: DashboardPageFilters; unavailable: boolean }) {
  const copy = getPublicMessages(filters.locale).dashboard;
  const labels = depositCopy(filters.locale);
  const groups = new Map<string, { label: string; items: PublicProduct[]; rates: Record<string, number> }>();
  for (const product of products) {
    if (product.country_code !== filters.countryCode || !/^[A-Z]{3}$/.test(product.currency)
      || (product.product_type === 'gic' && product.deposit_terms?.withdrawal === 'unknown')) continue;
    for (const option of depositOptions(product)) {
      const key = depositGroupKey(product, option);
      const label = `${product.product_type_label} · ${product.currency} · ${product.deposit_terms?.basis === 'apy' ? labels.apy : labels.annual}`
        + (product.product_type === 'gic' ? ` · ${depositPeriod(option, filters.locale)} · ${labels[product.deposit_terms!.withdrawal]}` : '');
      const group = groups.get(key) ?? { label, items: [], rates: {} };
      group.items.push(product); group.rates[product.product_id] = option.rate;
      groups.set(key, group);
    }
  }
  const ordered = [...groups].sort(([a], [b]) => {
    const preferred = filters.countryCode === 'US' ? 'USD' : 'CAD';
    const priority = (key: string) => (key.startsWith('savings|') ? 0 : 2) + (key.split('|')[1] === preferred ? 0 : 1);
    return priority(a) - priority(b) || a.localeCompare(b, undefined, { numeric: true });
  });
  const [selected, setSelected] = useState('');
  const key = groups.has(selected) ? selected : ordered[0]?.[0] ?? '';
  const group = groups.get(key);
  const ranked = [...(group?.items ?? [])].sort((a, b) => (group?.rates[b.product_id] ?? 0) - (group?.rates[a.product_id] ?? 0) || a.product_id.localeCompare(b.product_id)).slice(0, 5);
  return <ProductTopFive accent="deposit" filters={filters} headingId="deposit-top-title" title={copy.depositTopTitle}
    subtitle={copy.depositTopSubtitle} products={ranked} rates={group?.rates}
    href={buildPublicHref('/products', { ...filters, page: 1 })} linkLabel={copy.moreDeposits}
    unavailable={unavailable} unavailableText={copy.depositTopUnavailable} emptyText={labels.empty}
    controls={ordered.length ? <label className="grid min-w-0 gap-1.5 border-b border-border px-4 py-3 text-xs font-medium md:px-5">{labels.scope}
      <select className="min-h-11 w-full min-w-0 max-w-full rounded-md border border-input bg-background px-2 text-sm" value={key} onChange={event => setSelected(event.target.value)}>
        {ordered.map(([value, entry]) => <option key={value} value={value}>{entry.label}</option>)}
      </select>
    </label> : null} />;
}
