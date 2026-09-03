import { CreditCard, FilterX, Landmark, PiggyBank } from "lucide-react";
import Link from "next/link";
import type { ReactNode } from "react";

import { Button } from "@/components/ui/button";
import { getPublicDesignCopy, getPublicMessages } from "@/lib/public-locale";
import { buildPublicHref, type DashboardPageFilters } from "@/lib/public-query";

export function DashboardHero({
  filters,
  finder
}: {
  filters: DashboardPageFilters;
  finder: ReactNode;
}) {
  const copy = getPublicMessages(filters.locale);
  const designCopy = getPublicDesignCopy(filters.locale);
  const productsHref = buildPublicHref("/products", { ...filters, page: 1 });
  const cardsHref = buildPublicHref("/cards", { ...filters, page: 1 });
  const loansHref = buildPublicHref("/loans", { ...filters, page: 1 });
  const clearHref = buildPublicHref("/", {
    ...filters,
    bankCodes: [],
    productTypes: [],
    targetCustomerTags: [],
    feeBucket: "",
    minimumBalanceBucket: "",
    minimumDepositBucket: "",
    termBucket: "",
    axisPreset: ""
  });

  return (
    <section className="border-y border-foreground/15 py-10 md:py-14">
      <div className="grid min-w-0 gap-10 lg:grid-cols-[minmax(0,0.95fr)_minmax(23rem,0.72fr)] lg:items-start">
        <div className="min-w-0 max-w-3xl">
          <h1 className="text-balance max-w-4xl font-display text-[clamp(2.5rem,6vw,4.75rem)] font-semibold leading-[1.02] tracking-[-0.055em] text-foreground [overflow-wrap:anywhere]">
            {designCopy.homeTitle}
          </h1>
          <p className="mt-5 max-w-xl text-base leading-7 text-muted-foreground [overflow-wrap:anywhere] md:text-lg">
            {designCopy.homeBody}
          </p>
          <div className="mt-7 flex flex-wrap gap-2.5">
            <Button asChild size="lg" variant="outline" className="min-h-12 rounded-full border-foreground/20 bg-transparent px-5">
              <Link href={productsHref}>
                <PiggyBank className="size-4" aria-hidden="true" />
                {copy.nav.products}
              </Link>
            </Button>
            <Button asChild size="lg" variant="outline" className="min-h-12 rounded-full border-foreground/20 bg-transparent px-5">
              <Link href={cardsHref}>
                <CreditCard className="size-4" aria-hidden="true" />
                {copy.nav.card}
              </Link>
            </Button>
            <Button asChild size="lg" variant="outline" className="min-h-12 rounded-full border-foreground/20 bg-transparent px-5">
              <Link href={loansHref}>
                <Landmark className="size-4" aria-hidden="true" />
                {copy.nav.loan}
              </Link>
            </Button>
            {hasActiveDashboardScope(filters) ? (
              <Button asChild variant="ghost">
                <Link href={clearHref}>
                  <FilterX className="size-4" aria-hidden="true" />
                  {copy.common.clearFilters}
                </Link>
              </Button>
            ) : null}
          </div>
        </div>
        {finder}
      </div>
    </section>
  );
}

export function DashboardFinderFallback() {
  return (
    <div
      aria-hidden="true"
      className="min-h-[28rem] animate-pulse rounded-xl border border-primary/20 bg-card/60"
    >
      <div className="h-24 border-b border-primary/10 bg-primary/[0.035]" />
      <div className="grid gap-4 p-5">
        <div className="h-12 rounded-lg bg-muted" />
        <div className="h-12 rounded-lg bg-muted" />
        <div className="h-12 rounded-lg bg-muted" />
        <div className="h-12 rounded-lg bg-muted" />
      </div>
    </div>
  );
}

function hasActiveDashboardScope(filters: DashboardPageFilters) {
  return Boolean(
    filters.bankCodes.length ||
    filters.productTypes.length ||
    filters.targetCustomerTags.length ||
    filters.feeBucket ||
    filters.minimumBalanceBucket ||
    filters.minimumDepositBucket ||
    filters.termBucket ||
    filters.axisPreset
  );
}
