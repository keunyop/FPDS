"use client";
import { useState } from "react";
import { rankingEmptyMessage } from "@/lib/public-ranking-empty";
import { ProductTopFive } from "@/components/fpds/public/product-top-five";
import { loanRankingGroups, loanRankingCopy, loanBrowseGroups, loanBrowseCopy } from "@/lib/public-loan-ranking";
import { getPublicMessages } from "@/lib/public-locale";
import type { PublicProduct } from "@/lib/public-api";
import { buildPublicHref, type DashboardPageFilters } from "@/lib/public-query";

export function LoanTopFive({ products, filters, unavailable }: { products: PublicProduct[]; filters: DashboardPageFilters; unavailable: boolean }) {
  const copy = getPublicMessages(filters.locale).dashboard;
  const labels = loanRankingCopy(filters.locale);
  const ranked = unavailable ? [] : loanRankingGroups(products, filters.countryCode, filters.locale);
  const browsing = !unavailable && !ranked.length;
  const browseCopy = loanBrowseCopy(filters.locale);
  const groups = browsing ? loanBrowseGroups(products, filters.countryCode) : ranked;
  const [selected, setSelected] = useState('');
  const group = groups.find(entry => entry.key === selected) ?? groups[0];
  return <ProductTopFive accent="loan" filters={filters} headingId="loan-top-title" title={browsing && group ? browseCopy.title : copy.loanTopTitle}
    browsing={browsing} rankingNote={browsing ? browseCopy.note : undefined}
    subtitle={browsing ? browseCopy.subtitle : copy.loanTopSubtitle} products={group?.items ?? []} values={group?.rates}
    href={buildPublicHref('/loans', { ...filters, page: 1 })} linkLabel={copy.moreLoans}
    unavailable={unavailable} unavailableText={copy.loanTopUnavailable} emptyText={rankingEmptyMessage(products, "loan", filters.countryCode, filters.locale)}
    controls={group ? <label className="grid min-w-0 gap-1.5 border-b border-border px-4 py-3 text-xs font-medium md:px-5">
      <span className="flex flex-wrap items-center justify-between gap-x-3 gap-y-1">
        <span>{labels.scope}</span>
        <span className="font-normal text-muted-foreground">{group.currency}</span>
      </span>
      <select aria-label={labels.scope} className="min-h-11 w-full min-w-0 max-w-full rounded-md border border-input bg-background px-2 text-sm focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-ring" value={group.key} onChange={event => setSelected(event.target.value)}>
        {groups.map(entry => <option key={entry.key} value={entry.key}>{entry.label}</option>)}
      </select>
    </label> : null} />;
}
