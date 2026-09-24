import { getComparablePublicRate } from "@/lib/public-rate";
import { ArrowRight, ExternalLink, Landmark, PiggyBank } from "lucide-react";
import Link from "next/link";
import type { ReactNode } from "react";
import { BankLogo } from "@/components/fpds/public/bank-logo";
import { ProductVerification } from "@/components/fpds/public/product-verification";
import { TrackedOfficialBankLink, TrackedProductLink } from "@/components/fpds/public/product-engagement-link";
import { getIntlLocale, getPublicMessages } from "@/lib/public-locale";
import type { PublicProductsResponse } from "@/lib/public-api";
import { buildPublicHref, type DashboardPageFilters } from "@/lib/public-query";

export function ProductTopFive({
  controls,
  rates,
  accent,
  emptyText,
  filters,
  headingId,
  href,
  linkLabel,
  products,
  subtitle,
  title,
  unavailable,
  unavailableText
}: {
  controls?: ReactNode;
  rates?: Record<string, number>;
  accent: "deposit" | "loan";
  emptyText: string;
  filters: DashboardPageFilters;
  headingId: string;
  href: string;
  linkLabel: string;
  products: PublicProductsResponse["items"];
  subtitle: string;
  title: string;
  unavailable: boolean;
  unavailableText: string;
}) {
  const copy = getPublicMessages(filters.locale);
  const accentClass = accent === "loan" ? "text-loan" : "text-primary";
  const articleClass = accent === "loan"
    ? "border-loan/30 border-t-loan"
    : "border-primary/25 border-t-primary";
  const headerClass = accent === "loan" ? "bg-loan/[0.045]" : "bg-primary/[0.04]";
  const iconClass = accent === "loan" ? "bg-loan/10 text-loan" : "bg-primary/10 text-primary";
  const metricClass = accent === "loan" ? "border-loan" : "border-primary";
  const rowClass = accent === "loan" ? "divide-loan/15" : "divide-primary/15";
  const FamilyIcon = accent === "loan" ? Landmark : PiggyBank;

  return (
    <article className={`min-w-0 overflow-hidden border border-t-4 bg-card/70 ${articleClass}`} aria-labelledby={headingId}>
      <div className={`border-b border-border px-4 py-5 md:px-5 md:py-6 ${headerClass}`}>
        <div className="flex items-start gap-3">
          <span className={`grid size-9 shrink-0 place-items-center rounded-full ${iconClass}`} aria-hidden="true">
            <FamilyIcon className="size-4.5" />
          </span>
          <div className="min-w-0">
            <h2 id={headingId} className="text-2xl font-semibold tracking-[-0.025em] text-foreground">{title}</h2>
            <p className="mt-2 max-w-3xl text-sm leading-6 text-muted-foreground">{subtitle}</p>
          </div>
        </div>
      </div>
      {controls}
      {unavailable ? (
        <div className="p-4 md:p-5">
          <EmptyPanel text={unavailableText} />
        </div>
      ) : products.length ? (
        <ol className={`grid divide-y ${rowClass}`}>
          {products.map((product, index) => (
            <li className="grid min-w-0 grid-cols-[1.25rem_auto_minmax(0,1fr)] items-center gap-x-3 px-4 py-4 sm:grid-cols-[1.25rem_auto_minmax(0,1fr)_auto_auto] md:px-5" key={product.product_id}>
              <span className="text-sm font-semibold text-muted-foreground tabular-nums">{index + 1}</span>
              <BankLogo bankCode={product.bank_code} bankName={product.bank_name} size="sm" />
              <div className="min-w-0">
                <TrackedProductLink
                  className="flex min-h-11 min-w-0 items-center text-sm font-semibold text-foreground hover:text-primary [overflow-wrap:anywhere]"
                  countryCode={filters.countryCode}
                  href={buildProductDetailHref(filters, product.product_id)}
                  productId={product.product_id}
                >
                  {product.product_name}
                </TrackedProductLink>
                <p className="truncate text-xs text-muted-foreground">{product.bank_name} · {product.product_type_label}</p>
                <ProductVerification product={product} locale={filters.locale} />
              </div>
              <div className="col-start-3 mt-2 flex min-w-0 flex-wrap items-center justify-between gap-2 sm:col-span-2 sm:col-start-4 sm:mt-0 sm:flex-nowrap">
                <span className={`border-b-2 px-2 py-1 text-base font-semibold text-foreground tabular-nums ${metricClass}`} aria-label={`${copy.grid.metricDisplayRate} ${formatMetricValue(rates?.[product.product_id] ?? getComparablePublicRate(product), "percent", filters.locale)}`}>
                  {formatMetricValue(rates?.[product.product_id] ?? getComparablePublicRate(product), "percent", filters.locale)}
                </span>
                {product.product_url ? (
                  <TrackedOfficialBankLink
                    className="inline-flex min-h-11 items-center justify-center gap-1.5 whitespace-nowrap text-sm font-medium text-primary hover:text-primary/80"
                    countryCode={filters.countryCode}
                    href={product.product_url}
                    productId={product.product_id}
                  >
                    {copy.common.bankPage}
                    <ExternalLink className="size-3.5" aria-hidden="true" />
                  </TrackedOfficialBankLink>
                ) : null}
              </div>
            </li>
          ))}
        </ol>
      ) : (
        <div className="p-4 md:p-5">
          <EmptyPanel text={emptyText} />
        </div>
      )}
      <div className={`border-t px-4 py-2 md:px-5 ${accent === "loan" ? "border-loan/15" : "border-primary/15"}`}>
        <Link className={`inline-flex min-h-11 items-center gap-2 text-sm font-semibold ${accentClass} hover:underline hover:underline-offset-4`} href={href}>
          {linkLabel}
          <ArrowRight className="size-3.5" aria-hidden="true" />
        </Link>
      </div>
    </article>
  );
}

function EmptyPanel({ text }: { text: string }) {
  return <p className="rounded-lg border border-dashed border-border bg-card px-3 py-6 text-center text-sm text-muted-foreground">{text}</p>;
}

function formatMetricValue(value: number | string | null, unit: string, locale: string) {
  const copy = getPublicMessages(locale);
  if (value === null || (typeof value === "number" && !Number.isFinite(value))) {
    return copy.common.notDisclosed;
  }
  if (typeof value === "string") {
    return value;
  }
  if (unit === "percent") {
    return `${value.toFixed(2).replace(/\.?0+$/, "")}%`;
  }
  if (unit === "currency") {
    return new Intl.NumberFormat(getIntlLocale(locale), {
      style: "currency",
      currency: "CAD",
      maximumFractionDigits: Number.isInteger(value) ? 0 : 2
    }).format(value);
  }
  return formatCount(value, locale);
}

function formatCount(value: number, locale: string) {
  return new Intl.NumberFormat(getIntlLocale(locale), {
    maximumFractionDigits: Number.isInteger(value) ? 0 : 2
  }).format(value);
}

function buildProductDetailHref(filters: DashboardPageFilters, productId: string) {
  return buildPublicHref(`/products/${encodeURIComponent(productId)}`, filters);
}
