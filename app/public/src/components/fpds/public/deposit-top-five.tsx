"use client";
import { useState } from "react";
import { rankingEmptyMessage } from "@/lib/public-ranking-empty";
import { ProductTopFive } from "@/components/fpds/public/product-top-five";
import { depositCopy } from "@/lib/public-deposit";
import { depositRankingGroups } from "@/lib/public-deposit-ranking";
import { getPublicMessages } from "@/lib/public-locale";
import type { PublicProduct } from "@/lib/public-api";
import { buildPublicHref, type DashboardPageFilters } from "@/lib/public-query";

export function DepositTopFive({ products, filters, unavailable }: { products: PublicProduct[]; filters: DashboardPageFilters; unavailable: boolean }) {
  const copy = getPublicMessages(filters.locale).dashboard;
  const labels = depositCopy(filters.locale);
  const groups = unavailable ? [] : depositRankingGroups(products, filters.countryCode, filters.locale);
  const [selected, setSelected] = useState('');
  const group = groups.find(entry => entry.key === selected) ?? groups[0];
  return <ProductTopFive accent="deposit" filters={filters} headingId="deposit-top-title" title={copy.depositTopTitle}
    subtitle={copy.depositTopSubtitle} products={group?.items ?? []} values={group?.values} metric={group?.metric} termLabel={group?.term}
    href={buildPublicHref('/products', { ...filters, page: 1 })} linkLabel={copy.moreDeposits}
    unavailable={unavailable} unavailableText={copy.depositTopUnavailable} emptyText={rankingEmptyMessage(products, "deposit", filters.countryCode, filters.locale)}
    controls={group ? <label className="grid min-w-0 gap-1.5 border-b border-border px-4 py-3 text-xs font-medium md:px-5">
      <span className="flex flex-wrap items-center justify-between gap-x-3 gap-y-1">
        <span>{labels.scope}</span>
        <span className="font-normal text-muted-foreground">{group.currency} · {group.basis}</span>
      </span>
      <select aria-label={labels.scope} className="min-h-11 w-full min-w-0 max-w-full rounded-md border border-input bg-background px-2 text-sm focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-ring" value={group.key} onChange={event => setSelected(event.target.value)}>
        {groups.map(entry => <option key={entry.key} value={entry.key}>{entry.label}</option>)}
      </select>
    </label> : null} />;
}
