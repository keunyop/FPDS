import { ArrowRight, BadgeDollarSign, Landmark, PiggyBank, ShieldCheck, TimerReset } from "lucide-react";
import Link from "next/link";
import type { ReactNode } from "react";

import { getPublicMessages } from "@/lib/public-locale";
import { buildPublicHref, type PublicScopeFilters } from "@/lib/public-query";

type PurposeEntryPointsProps = {
  filters: PublicScopeFilters;
  freshnessLabel?: string;
  locale: string;
};

export function PurposeEntryPoints({ filters, freshnessLabel, locale }: PurposeEntryPointsProps) {
  const copy = getPublicMessages(locale);
  const cards = [
    {
      action: copy.purpose.everydayAction,
      body: copy.purpose.everydayBody,
      href: buildPurposeHref(filters, {
        minimumDepositBucket: "",
        productTypes: ["chequing"],
        sortBy: "monthly_fee",
        sortOrder: "asc",
        termBucket: ""
      }),
      icon: BadgeDollarSign,
      title: copy.purpose.everydayTitle
    },
    {
      action: copy.purpose.savingsAction,
      body: copy.purpose.savingsBody,
      href: buildPurposeHref(filters, {
        minimumDepositBucket: "",
        productTypes: ["savings"],
        sortBy: "display_rate",
        sortOrder: "desc",
        termBucket: ""
      }),
      icon: PiggyBank,
      title: copy.purpose.savingsTitle
    },
    {
      action: copy.purpose.termAction,
      body: copy.purpose.termBody,
      href: buildPurposeHref(filters, {
        feeBucket: "",
        minimumBalanceBucket: "",
        productTypes: ["gic"],
        sortBy: "display_rate",
        sortOrder: "desc"
      }),
      icon: TimerReset,
      title: copy.purpose.termTitle
    },
    {
      action: copy.purpose.lowEntryAction,
      body: copy.purpose.lowEntryBody,
      href: buildPurposeHref(filters, {
        productTypes: [],
        sortBy: "minimum_balance",
        sortOrder: "asc",
        termBucket: ""
      }),
      icon: Landmark,
      title: copy.purpose.lowEntryTitle
    }
  ];

  return (
    <section className="grid gap-4" aria-labelledby="purpose-entry-title">
      <div className="grid gap-2 md:grid-cols-[minmax(0,1fr)_minmax(16rem,0.4fr)] md:items-end">
        <div>
          <p className="text-sm font-medium text-primary">{copy.purpose.eyebrow}</p>
          <h2 id="purpose-entry-title" className="mt-1 text-2xl font-semibold tracking-normal text-foreground">
            {copy.purpose.title}
          </h2>
        </div>
        <p className="text-sm leading-6 text-muted-foreground md:text-right">{copy.purpose.description}</p>
      </div>

      <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
        {cards.map((card) => (
          <Link
            className="group grid min-h-48 content-between gap-4 rounded-lg border border-border bg-card p-4 shadow-sm transition hover:-translate-y-0.5 hover:border-primary/30 hover:shadow-md"
            href={card.href}
            key={card.title}
          >
            <span className="flex size-10 items-center justify-center rounded-lg border border-primary/15 bg-primary/5 text-primary">
              <card.icon className="size-5" aria-hidden="true" />
            </span>
            <span>
              <span className="block text-base font-semibold leading-snug text-foreground">{card.title}</span>
              <span className="mt-2 block text-sm leading-6 text-muted-foreground">{card.body}</span>
            </span>
            <span className="inline-flex items-center gap-1.5 text-sm font-medium text-primary">
              {card.action}
              <ArrowRight className="size-3.5 transition-transform group-hover:translate-x-0.5" aria-hidden="true" />
            </span>
          </Link>
        ))}
      </div>

      <div className="grid gap-3 rounded-lg border border-border bg-muted/20 p-4 md:grid-cols-3">
        <TrustItem icon={<ShieldCheck className="size-4" aria-hidden="true" />} title={copy.purpose.trustScopeTitle}>
          {copy.purpose.trustScopeBody}
        </TrustItem>
        <TrustItem icon={<TimerReset className="size-4" aria-hidden="true" />} title={copy.purpose.trustFreshnessTitle}>
          {freshnessLabel ? `${copy.purpose.trustFreshnessBody} ${freshnessLabel}` : copy.purpose.trustFreshnessBody}
        </TrustItem>
        <TrustItem icon={<Landmark className="size-4" aria-hidden="true" />} title={copy.purpose.trustOfficialTitle}>
          {copy.purpose.trustOfficialBody}
        </TrustItem>
      </div>
    </section>
  );
}

function TrustItem({ children, icon, title }: { children: ReactNode; icon: ReactNode; title: string }) {
  return (
    <div className="grid gap-2">
      <div className="flex items-center gap-2 text-sm font-semibold text-foreground">
        <span className="flex size-7 items-center justify-center rounded-md border border-border bg-background text-primary">{icon}</span>
        {title}
      </div>
      <p className="text-sm leading-6 text-muted-foreground">{children}</p>
    </div>
  );
}

function buildPurposeHref(
  filters: PublicScopeFilters,
  overrides: Partial<PublicScopeFilters> & {
    sortBy: string;
    sortOrder: "asc" | "desc";
  }
) {
  return buildPublicHref("/products", {
    ...filters,
    ...overrides,
    page: 1
  });
}

