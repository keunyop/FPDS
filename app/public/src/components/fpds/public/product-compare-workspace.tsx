"use client";

import { ArrowRight, Check, ExternalLink, GitCompareArrows, Plus, X } from "lucide-react";
import Link from "next/link";
import { useMemo, useState } from "react";

import { BankLogo } from "@/components/fpds/public/bank-logo";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { getIntlLocale, getPublicMessages } from "@/lib/public-locale";
import type { PublicProduct } from "@/lib/public-api";
import { buildPublicHref, type ProductGridPageFilters } from "@/lib/public-query";
import { cn } from "@/lib/utils";

const MAX_COMPARE_PRODUCTS = 4;

type ProductCompareWorkspaceProps = {
  filters: ProductGridPageFilters;
  locale: string;
  products: PublicProduct[];
};

export function ProductCompareWorkspace({ filters, locale, products }: ProductCompareWorkspaceProps) {
  const copy = getPublicMessages(locale);
  const [selectedIds, setSelectedIds] = useState<string[]>([]);
  const selectedProducts = useMemo(
    () => selectedIds.map((productId) => products.find((product) => product.product_id === productId)).filter((product): product is PublicProduct => Boolean(product)),
    [products, selectedIds]
  );

  function toggleProduct(productId: string) {
    setSelectedIds((current) => {
      if (current.includes(productId)) {
        return current.filter((id) => id !== productId);
      }
      if (current.length >= MAX_COMPARE_PRODUCTS) {
        return current;
      }
      return [...current, productId];
    });
  }

  return (
    <section className="grid gap-4" aria-labelledby="compare-products-title">
      <ComparePanel
        filters={filters}
        locale={locale}
        onClear={() => setSelectedIds([])}
        onRemove={(productId) => setSelectedIds((current) => current.filter((id) => id !== productId))}
        products={selectedProducts}
      />

      <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        {products.map((product) => {
          const selected = selectedIds.includes(product.product_id);
          const compareDisabled = !selected && selectedIds.length >= MAX_COMPARE_PRODUCTS;
          return (
            <ProductCompareCard
              compareDisabled={compareDisabled}
              filters={filters}
              key={product.product_id}
              locale={locale}
              onToggle={() => toggleProduct(product.product_id)}
              product={product}
              selected={selected}
            />
          );
        })}
      </section>
      <p className="sr-only" aria-live="polite">
        {selectedProducts.length
          ? copy.compare.selectedCount.replace("{count}", String(selectedProducts.length)).replace("{limit}", String(MAX_COMPARE_PRODUCTS))
          : copy.compare.emptyTitle}
      </p>
    </section>
  );
}

function ProductCompareCard({
  compareDisabled,
  filters,
  locale,
  onToggle,
  product,
  selected
}: {
  compareDisabled: boolean;
  filters: ProductGridPageFilters;
  locale: string;
  onToggle: () => void;
  product: PublicProduct;
  selected: boolean;
}) {
  const copy = getPublicMessages(locale);
  const metrics = buildComparisonMetrics(product, locale);
  const tags = product.target_customer_tag_labels.slice(0, 2);
  const detailHref = buildProductDetailHref(filters, product.product_id);

  return (
    <Card
      className={cn(
        "h-full gap-3 overflow-hidden border-border/80 shadow-sm transition-all hover:-translate-y-0.5 hover:shadow-md hover:ring-1 hover:ring-primary/15",
        selected && "border-primary/35 ring-1 ring-primary/20"
      )}
    >
      <CardHeader className="pb-2">
        <div className="flex flex-col gap-4">
          <div className="flex items-start justify-between gap-3">
            <BankLogo bankCode={product.bank_code} bankName={product.bank_name} size="sm" />
            {product.product_url ? (
              <Button asChild variant="outline" size="xs" className="shrink-0">
                <a href={product.product_url} target="_blank" rel="noreferrer">
                  {copy.common.bankPage}
                  <ExternalLink className="size-3" aria-hidden="true" />
                </a>
              </Button>
            ) : null}
          </div>
          <div className="min-w-0">
            <CardDescription className="mb-2">
              <span className="inline-flex rounded-md bg-primary/5 px-2 py-1 text-[11px] font-semibold uppercase text-primary">{product.product_type_label}</span>
            </CardDescription>
            <CardTitle className="text-lg leading-snug">
              <Link className="break-words hover:text-primary" href={detailHref}>
                {product.product_name}
              </Link>
            </CardTitle>
          </div>
        </div>
        {product.product_highlight_badge_label || tags.length ? (
          <div className="flex flex-wrap gap-2 pt-2">
            {product.product_highlight_badge_label ? <Badge>{product.product_highlight_badge_label}</Badge> : null}
            {tags.map((tag) => (
              <Badge key={tag} muted>
                {tag}
              </Badge>
            ))}
          </div>
        ) : null}
      </CardHeader>
      <CardContent className="pt-0">
        <dl className="grid gap-2 sm:grid-cols-3">
          {metrics.map((metric, index) => (
            <div key={metric.label} className={cn("min-h-24 rounded-lg border p-3", index === 0 ? "border-primary/25 bg-primary/5" : "border-border bg-muted/30")}>
              <dt className="text-xs font-medium text-muted-foreground">{metric.label}</dt>
              <dd className="mt-2 break-words text-lg font-semibold tabular-nums leading-tight text-foreground">{metric.value}</dd>
            </div>
          ))}
        </dl>
        <div className="mt-4 flex flex-col gap-2 border-t border-border/70 pt-3 sm:flex-row sm:items-center sm:justify-between">
          <Button disabled={compareDisabled} onClick={onToggle} size="sm" type="button" variant={selected ? "default" : "outline"} className="justify-center">
            {selected ? <Check className="size-4" aria-hidden="true" /> : <Plus className="size-4" aria-hidden="true" />}
            {selected ? copy.compare.selected : copy.compare.select}
          </Button>
          <Link className="inline-flex items-center justify-center gap-1.5 text-sm font-medium text-primary hover:text-primary/80" href={detailHref}>
            {copy.grid.compareDetails}
            <ArrowRight className="size-3.5" aria-hidden="true" />
          </Link>
        </div>
        {compareDisabled ? <p className="mt-2 text-xs leading-5 text-muted-foreground">{copy.compare.limit}</p> : null}
      </CardContent>
    </Card>
  );
}

function ComparePanel({
  filters,
  locale,
  onClear,
  onRemove,
  products
}: {
  filters: ProductGridPageFilters;
  locale: string;
  onClear: () => void;
  onRemove: (productId: string) => void;
  products: PublicProduct[];
}) {
  const copy = getPublicMessages(locale);

  return (
    <section className="overflow-hidden rounded-xl border border-border/80 bg-card shadow-sm" aria-labelledby="compare-products-title">
      <div className="grid gap-3 border-b border-border/70 bg-muted/25 px-4 py-4 md:grid-cols-[minmax(0,1fr)_auto] md:items-center">
        <div className="min-w-0">
          <p className="flex items-center gap-2 text-sm font-medium text-primary">
            <GitCompareArrows className="size-4" aria-hidden="true" />
            {copy.compare.eyebrow}
          </p>
          <h2 id="compare-products-title" className="mt-1 text-xl font-semibold leading-tight text-foreground">
            {copy.compare.title}
          </h2>
          <p className="mt-1 text-sm leading-6 text-muted-foreground">{copy.compare.subtitle}</p>
        </div>
        <div className="flex flex-wrap items-center gap-2 md:justify-end">
          <span className="rounded-md border border-border bg-background px-2.5 py-1 text-xs font-medium text-muted-foreground">
            {copy.compare.selectedCount.replace("{count}", String(products.length)).replace("{limit}", String(MAX_COMPARE_PRODUCTS))}
          </span>
          {products.length ? (
            <Button onClick={onClear} size="sm" type="button" variant="outline">
              <X className="size-4" aria-hidden="true" />
              {copy.compare.clear}
            </Button>
          ) : null}
        </div>
      </div>
      {products.length ? (
        <div className="overflow-x-auto">
          <table className="w-full min-w-[58rem] text-left text-sm">
            <thead className="border-b border-border bg-background text-xs font-medium text-muted-foreground">
              <tr>
                <th className="px-4 py-3">{copy.compare.tableProduct}</th>
                <th className="px-4 py-3">{copy.compare.tableWhy}</th>
                <th className="px-4 py-3">{copy.grid.metricDisplayRate}</th>
                <th className="px-4 py-3">{copy.grid.metricMonthlyFee}</th>
                <th className="px-4 py-3">{copy.compare.entryAmount}</th>
                <th className="px-4 py-3">{copy.grid.metricTerm}</th>
                <th className="px-4 py-3">{copy.compare.application}</th>
                <th className="px-4 py-3">{copy.compare.officialPage}</th>
              </tr>
            </thead>
            <tbody>
              {products.map((product) => (
                <tr className="border-b border-border/70 last:border-0" key={product.product_id}>
                  <td className="px-4 py-3 align-top">
                    <div className="flex min-w-52 gap-3">
                      <BankLogo bankCode={product.bank_code} bankName={product.bank_name} size="sm" />
                      <div className="min-w-0">
                        <Link className="break-words font-semibold text-foreground hover:text-primary" href={buildProductDetailHref(filters, product.product_id)}>
                          {product.product_name}
                        </Link>
                        <p className="mt-1 text-xs font-medium text-muted-foreground">{product.product_type_label}</p>
                        <button className="mt-2 inline-flex items-center gap-1 text-xs font-medium text-muted-foreground hover:text-foreground" onClick={() => onRemove(product.product_id)} type="button">
                          <X className="size-3" aria-hidden="true" />
                          {copy.compare.remove}
                        </button>
                      </div>
                    </div>
                  </td>
                  <td className="max-w-56 px-4 py-3 align-top leading-6 text-muted-foreground">{buildComparisonReason(product, locale)}</td>
                  <td className="px-4 py-3 align-top font-semibold tabular-nums text-foreground">{formatRate(product.public_display_rate, locale)}</td>
                  <td className="px-4 py-3 align-top tabular-nums text-foreground">{formatCurrency(product.public_display_fee, product.currency, locale)}</td>
                  <td className="px-4 py-3 align-top tabular-nums text-foreground">{formatEntryAmount(product, locale)}</td>
                  <td className="px-4 py-3 align-top text-foreground">{formatTerm(product.term_length_days, locale)}</td>
                  <td className="max-w-56 px-4 py-3 align-top leading-6 text-muted-foreground">{product.application_method ?? copy.common.notDisclosed}</td>
                  <td className="px-4 py-3 align-top">
                    {product.product_url ? (
                      <Button asChild variant="outline" size="xs">
                        <a href={product.product_url} target="_blank" rel="noreferrer">
                          {copy.common.open}
                          <ExternalLink className="size-3" aria-hidden="true" />
                        </a>
                      </Button>
                    ) : (
                      <span className="text-muted-foreground">{copy.common.notDisclosed}</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <div className="px-4 py-6">
          <p className="text-sm font-medium text-foreground">{copy.compare.emptyTitle}</p>
          <p className="mt-1 max-w-2xl text-sm leading-6 text-muted-foreground">{copy.compare.emptyBody}</p>
        </div>
      )}
    </section>
  );
}

function Badge({ children, muted = false }: { children: string; muted?: boolean }) {
  return (
    <span className={cn("rounded-md border px-2 py-1 text-xs font-medium", muted ? "border-border bg-background text-muted-foreground" : "border-primary/20 bg-secondary text-secondary-foreground")}>
      {children}
    </span>
  );
}

function buildComparisonMetrics(product: PublicProduct, locale: string) {
  const copy = getPublicMessages(locale);
  if (product.product_type === "chequing") {
    return [
      { label: copy.grid.metricMonthlyFee, value: formatCurrency(product.public_display_fee, product.currency, locale) },
      { label: copy.grid.metricMinBalance, value: formatCurrency(product.minimum_balance, product.currency, locale) },
      { label: copy.grid.metricKeyDetail, value: buildKeyDetail(product, locale) }
    ];
  }

  if (product.product_type === "gic") {
    return [
      { label: copy.grid.metricDisplayRate, value: formatRate(product.public_display_rate, locale) },
      { label: copy.grid.metricTerm, value: formatTerm(product.term_length_days, locale) },
      { label: copy.grid.metricMinDeposit, value: formatCurrency(product.minimum_deposit, product.currency, locale) }
    ];
  }

  if (product.product_family === "lending") {
    return [
      { label: copy.grid.metricDisplayRate, value: formatRate(product.public_display_rate, locale) },
      { label: loanMetricLabel("rateType", locale), value: product.rate_type ?? copy.common.notDisclosed },
      { label: loanMetricLabel("term", locale), value: product.term_length_text ?? copy.common.notDisclosed }
    ];
  }

  return [
    { label: copy.grid.metricDisplayRate, value: formatRate(product.public_display_rate, locale) },
    { label: copy.grid.metricMinBalance, value: formatCurrency(product.minimum_balance, product.currency, locale) },
    { label: copy.grid.metricKeyDetail, value: buildKeyDetail(product, locale) }
  ];
}

function buildKeyDetail(product: PublicProduct, locale: string) {
  const copy = getPublicMessages(locale);
  return product.product_highlight_badge_label ?? product.subtype_label ?? product.target_customer_tag_labels[0] ?? copy.common.notDisclosed;
}

function loanMetricLabel(field: "rateType" | "term", locale: string) {
  const labels = {
    en: { rateType: "Rate type", term: "Term" },
    ko: { rateType: "금리 유형", term: "기간" },
    ja: { rateType: "金利タイプ", term: "期間" }
  };
  return labels[locale as keyof typeof labels]?.[field] ?? labels.en[field];
}

function buildComparisonReason(product: PublicProduct, locale: string) {
  const copy = getPublicMessages(locale);
  if (product.public_display_fee === 0) {
    return copy.compare.reasonNoMonthlyFee;
  }
  if (product.product_type === "chequing" && product.public_display_fee !== null) {
    return copy.compare.reasonFeeKnown;
  }
  if (product.product_type === "gic" && product.public_display_rate !== null && product.term_length_days !== null) {
    return copy.compare.reasonTermRate;
  }
  if (product.public_display_rate !== null) {
    return copy.compare.reasonRateKnown;
  }
  if (product.minimum_deposit !== null || product.minimum_balance !== null) {
    return copy.compare.reasonLowEntry;
  }
  return product.product_highlight_badge_label ?? product.subtype_label ?? copy.compare.reasonFallback;
}

function buildProductDetailHref(filters: ProductGridPageFilters, productId: string) {
  return buildPublicHref(`/products/${encodeURIComponent(productId)}`, filters);
}

function formatCurrency(value: number | null, currency: string, locale: string) {
  const copy = getPublicMessages(locale);
  if (value === null || !Number.isFinite(value)) {
    return copy.common.notDisclosed;
  }
  const safeCurrency = normalizeCurrency(currency);
  return new Intl.NumberFormat(getIntlLocale(locale), {
    style: "currency",
    currency: safeCurrency,
    maximumFractionDigits: Number.isInteger(value) ? 0 : 2
  }).format(value);
}

function formatEntryAmount(product: PublicProduct, locale: string) {
  const amount = product.minimum_deposit ?? product.minimum_balance;
  return formatCurrency(amount, product.currency, locale);
}

function formatRate(value: number | null, locale: string) {
  const copy = getPublicMessages(locale);
  if (value === null || !Number.isFinite(value)) {
    return copy.common.notDisclosed;
  }
  return `${value.toFixed(2).replace(/\.?0+$/, "")}%`;
}

function normalizeCurrency(currency: string) {
  const normalized = currency.trim().toUpperCase();
  return /^[A-Z]{3}$/.test(normalized) ? normalized : "CAD";
}

function formatTerm(termLengthDays: number | null, locale: string) {
  const copy = getPublicMessages(locale);
  if (termLengthDays === null || !Number.isFinite(termLengthDays)) {
    return copy.common.notDisclosed;
  }
  if (termLengthDays % 365 === 0) {
    const years = termLengthDays / 365;
    if (locale === "ko") {
      return `${years}년`;
    }
    if (locale === "ja") {
      return `${years}年`;
    }
    return `${years} year${years === 1 ? "" : "s"}`;
  }
  if (termLengthDays % 30 === 0) {
    const months = Math.round(termLengthDays / 30);
    if (locale === "ko") {
      return `${months}개월`;
    }
    if (locale === "ja") {
      return `${months}か月`;
    }
    return `${months} month${months === 1 ? "" : "s"}`;
  }
  if (locale === "ko") {
    return `${termLengthDays}일`;
  }
  if (locale === "ja") {
    return `${termLengthDays}日`;
  }
  return `${termLengthDays} days`;
}
