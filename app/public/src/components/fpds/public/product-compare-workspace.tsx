"use client";

import { ArrowRight, Check, ExternalLink, GitCompareArrows, Plus, X } from "lucide-react";
import Link from "next/link";
import { useMemo, useState } from "react";

import { BankLogo } from "@/components/fpds/public/bank-logo";
import { Button } from "@/components/ui/button";
import { getIntlLocale, getPublicDesignCopy, getPublicMessages } from "@/lib/public-locale";
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
  const designCopy = getPublicDesignCopy(locale);
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
      <div className="sticky top-16 z-20 flex items-start justify-between gap-3 border-y border-foreground/15 bg-background/95 px-1 py-3 backdrop-blur-xl sm:items-center">
        <div className="min-w-0">
          <h2 id="compare-products-title" className="flex items-center gap-2 text-sm font-semibold text-foreground">
            <GitCompareArrows className="size-4 text-primary" aria-hidden="true" />
            {copy.compare.title}
          </h2>
          <p className="mt-1 hidden text-xs leading-5 text-muted-foreground sm:block">{designCopy.compareDifferences}</p>
        </div>
        <div className="flex shrink-0 flex-col items-end gap-1 sm:flex-row sm:items-center sm:gap-2">
          <div className="flex items-center gap-1" aria-label={copy.compare.selectedCount.replace("{count}", String(selectedProducts.length)).replace("{limit}", String(MAX_COMPARE_PRODUCTS))}>
            {Array.from({ length: MAX_COMPARE_PRODUCTS }).map((_, index) => (
              <span className={cn("h-2.5 w-7 rounded-full transition-colors", index < selectedProducts.length ? "bg-maple" : "bg-muted")} key={index} aria-hidden="true" />
            ))}
          </div>
          {selectedProducts.length ? (
            <Button onClick={() => setSelectedIds([])} size="sm" type="button" variant="ghost">
              <X className="size-4" aria-hidden="true" />
              {copy.compare.clear}
            </Button>
          ) : null}
        </div>
      </div>

      {selectedProducts.length ? (
        <ComparePanel
          filters={filters}
          locale={locale}
          onRemove={(productId) => setSelectedIds((current) => current.filter((id) => id !== productId))}
          products={selectedProducts}
        />
      ) : null}

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
  const metrics = buildComparisonMetrics(product, locale).slice(0, 3);
  const [primaryMetric, ...secondaryMetrics] = metrics;
  const tags = product.target_customer_tag_labels.slice(0, 2);
  const detailHref = buildProductDetailHref(filters, product.product_id);

  return (
    <article
      className={cn(
        "relative h-full overflow-hidden border border-foreground/15 bg-card/80 transition-[border-color,transform,box-shadow] hover:-translate-y-0.5 hover:border-foreground/30 hover:shadow-[0_12px_30px_rgba(28,39,35,0.08)]",
        "before:absolute before:inset-y-0 before:left-0 before:w-1 before:bg-verification/55",
        product.product_family === "lending" && "before:bg-loan/70",
        selected && "border-maple/45 shadow-[0_0_0_1px_rgba(195,74,63,0.2)] before:bg-maple"
      )}
    >
      <div className="px-5 pb-2 pt-5">
        <div className="flex flex-col gap-4">
          <div className="flex items-center justify-between gap-3">
            <div className="flex min-w-0 items-center gap-2">
              <BankLogo bankCode={product.bank_code} bankName={product.bank_name} size="sm" />
              <span className="truncate text-xs font-medium text-muted-foreground">{product.bank_name}</span>
            </div>
            <span className="inline-flex rounded-full bg-muted px-2.5 py-1 font-mono text-[10px] font-semibold uppercase tracking-wide text-muted-foreground">{product.product_type_label}</span>
          </div>
          <div className="min-w-0">
            <h2 className="text-lg font-semibold leading-snug tracking-[-0.02em]">
              <Link className="inline-flex min-h-11 items-center break-words hover:text-primary" href={detailHref}>
                {product.product_name}
              </Link>
            </h2>
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
      </div>
      <div className="px-5 pb-5">
        <dl className="border-y border-border">
          <div className="py-4">
            <dt className="font-mono text-[10px] font-semibold uppercase tracking-wide text-verification">{primaryMetric.label}</dt>
            <dd className={cn(
              "mt-1 break-words font-display font-semibold leading-tight tracking-[-0.04em] text-foreground tabular-nums",
              product.product_family === "lending" && product.public_display_rate === null ? "text-lg" : "text-3xl"
            )}>{primaryMetric.value}</dd>
          </div>
          <div className="grid grid-cols-2 divide-x divide-border border-t border-border">
            {secondaryMetrics.map((metric) => (
              <div className="min-w-0 py-3 first:pr-3 last:pl-3" key={metric.label}>
                <dt className="text-[11px] font-medium text-muted-foreground">{metric.label}</dt>
                <dd className="mt-1 break-words text-sm font-semibold leading-snug text-foreground tabular-nums">{metric.value}</dd>
              </div>
            ))}
          </div>
        </dl>
        <div className="mt-4 flex flex-col gap-2 border-t border-border/70 pt-3 sm:flex-row sm:items-center sm:justify-between">
          <Button aria-pressed={selected} disabled={compareDisabled} onClick={onToggle} size="sm" type="button" variant={selected ? "default" : "outline"} className="min-h-11 justify-center rounded-full px-4">
            {selected ? <Check className="size-4" aria-hidden="true" /> : <Plus className="size-4" aria-hidden="true" />}
            {selected ? copy.compare.selected : copy.compare.select}
          </Button>
          <Link className="inline-flex min-h-11 items-center justify-center gap-1.5 text-sm font-medium text-primary hover:text-primary/80" href={detailHref}>
            {copy.grid.compareDetails}
            <ArrowRight className="size-3.5" aria-hidden="true" />
          </Link>
        </div>
        {compareDisabled ? <p className="mt-2 text-xs leading-5 text-muted-foreground">{copy.compare.limit}</p> : null}
      </div>
    </article>
  );
}

function ComparePanel({
  filters,
  locale,
  onRemove,
  products
}: {
  filters: ProductGridPageFilters;
  locale: string;
  onRemove: (productId: string) => void;
  products: PublicProduct[];
}) {
  const copy = getPublicMessages(locale);
  const designCopy = getPublicDesignCopy(locale);
  const rowsByProduct = products.map((product) => buildCompareRows(product, locale));
  const differingKeys = new Set(
    rowsByProduct[0]
      ?.filter((row) => {
        const values = new Set(rowsByProduct.map((rows) => rows.find((candidate) => candidate.key === row.key)?.value ?? copy.common.notDisclosed));
        return values.size > 1;
      })
      .map((row) => row.key) ?? []
  );

  return (
    <section className="scroll-mt-32 border-y border-maple/30 bg-card/70 px-3 py-4 md:px-4" aria-label={copy.compare.title}>
      <div className="mb-4 flex flex-col gap-1 border-b border-border pb-3 sm:flex-row sm:items-center sm:justify-between">
        <p className="font-mono text-[10px] font-semibold uppercase tracking-[0.14em] text-maple">{copy.compare.title}</p>
        <p className="text-xs leading-5 text-muted-foreground">{designCopy.compareBoundary}</p>
      </div>
      <div className={cn("grid gap-3 md:grid-cols-2", products.length === 3 ? "xl:grid-cols-3" : products.length >= 4 ? "xl:grid-cols-4" : "")}>
        {products.map((product, productIndex) => (
          <article className="border border-border bg-background/75 p-4" key={product.product_id}>
            <div className="flex items-start justify-between gap-3">
              <div className="flex min-w-0 items-start gap-3">
                <BankLogo bankCode={product.bank_code} bankName={product.bank_name} size="sm" />
                <div className="min-w-0">
                  <Link className="break-words text-sm font-semibold text-foreground hover:text-primary" href={buildProductDetailHref(filters, product.product_id)}>
                    {product.product_name}
                  </Link>
                  <p className="mt-1 text-xs text-muted-foreground">{product.bank_name} · {product.product_type_label}</p>
                </div>
              </div>
              <button className="inline-flex size-11 shrink-0 items-center justify-center rounded-full text-muted-foreground hover:bg-muted hover:text-foreground" onClick={() => onRemove(product.product_id)} type="button" aria-label={`${copy.compare.remove}: ${product.product_name}`}>
                <X className="size-4" aria-hidden="true" />
              </button>
            </div>
            <dl className="mt-4 divide-y divide-border border-y border-border">
              {rowsByProduct[productIndex].map((row) => (
                <CompareFact different={differingKeys.has(row.key)} key={row.key} label={row.label} value={row.value} />
              ))}
            </dl>
            {product.product_url ? (
              <Button asChild variant="outline" className="mt-4 min-h-11 w-full rounded-full">
                <a href={product.product_url} target="_blank" rel="noreferrer">
                  {copy.detail.officialPage}
                  <ExternalLink className="size-3.5" aria-hidden="true" />
                </a>
              </Button>
            ) : null}
          </article>
        ))}
      </div>
    </section>
  );
}

function CompareFact({ different, label, value }: { different: boolean; label: string; value: string }) {
  return (
    <div className={cn("px-2 py-3", different && "bg-accent/45")}>
      <dt className="text-[11px] font-medium text-muted-foreground">{label}</dt>
      <dd className="mt-1 break-words text-sm font-semibold text-foreground tabular-nums">{value}</dd>
    </div>
  );
}

function buildCompareRows(product: PublicProduct, locale: string) {
  const copy = getPublicMessages(locale);
  const typeAware = buildComparisonMetrics(product, locale);
  return [
    { key: "type", label: copy.grid.productTypes, value: product.product_type_label },
    ...typeAware.map((metric, index) => ({
      key: `essential-${index}`,
      label: metric.label,
      value: metric.value
    }))
  ];
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
      { label: copy.grid.metricMinBalance, value: formatCurrency(product.minimum_balance ?? product.minimum_deposit, product.currency, locale) },
      product.country_code === "US"
        ? { label: marketMetricLabel("feeWaiver", locale), value: product.fee_waiver_condition ?? copy.common.notDisclosed }
        : { label: essentialMetricLabel("transactions", locale), value: formatTransactions(product, locale) }
    ];
  }

  if (product.product_type === "gic") {
    return [
      { label: copy.grid.metricDisplayRate, value: formatProductRate(product, locale) },
      { label: copy.grid.metricTerm, value: formatProductTerm(product, locale) },
      { label: copy.grid.metricMinDeposit, value: formatCurrency(product.minimum_deposit, product.currency, locale) },
      product.country_code === "US"
        ? { label: marketMetricLabel("earlyWithdrawalPenalty", locale), value: product.early_withdrawal_penalty ?? copy.common.notDisclosed }
        : { label: essentialMetricLabel("redeemability", locale), value: formatRedeemability(product, locale) }
    ];
  }

  if (product.product_type === "mortgage") {
    return [
      { label: copy.grid.metricDisplayRate, value: formatProductRate(product, locale) },
      { label: loanMetricLabel("rateType", locale), value: product.rate_type ?? copy.common.notDisclosed },
      { label: loanMetricLabel("term", locale), value: formatProductTerm(product, locale) }
    ];
  }

  if (product.product_type === "personal-loan") {
    return [
      { label: copy.grid.metricDisplayRate, value: formatProductRate(product, locale) },
      { label: essentialMetricLabel("loanAmount", locale), value: product.loan_amount_text ?? copy.common.notDisclosed },
      { label: loanMetricLabel("term", locale), value: formatProductTerm(product, locale) }
    ];
  }

  if (product.product_type === "line-of-credit") {
    return [
      { label: copy.grid.metricDisplayRate, value: formatProductRate(product, locale) },
      { label: essentialMetricLabel("creditLimit", locale), value: product.credit_limit_text ?? copy.common.notDisclosed },
      { label: essentialMetricLabel("security", locale), value: formatSecurity(product, locale) }
    ];
  }

  return [
    { label: copy.grid.metricDisplayRate, value: formatProductRate(product, locale) },
    { label: copy.grid.metricMonthlyFee, value: formatCurrency(product.public_display_fee, product.currency, locale) },
    { label: copy.grid.metricMinBalance, value: formatCurrency(product.minimum_balance, product.currency, locale) },
  ];
}

function formatProductRate(product: PublicProduct, locale: string) {
  if (product.public_display_rate !== null) {
    return formatRate(product.public_display_rate, locale);
  }
  if (product.country_code === "US" && product.product_type === "mortgage" && product.interest_rate_summary) {
    return product.interest_rate_summary;
  }
  return product.mortgage_rate
    ?? product.interest_rate
    ?? product.interest_rate_summary
    ?? getPublicMessages(locale).common.notDisclosed;
}

function marketMetricLabel(field: "earlyWithdrawalPenalty" | "feeWaiver", locale: string) {
  const labels = {
    en: { earlyWithdrawalPenalty: "Early withdrawal penalty", feeWaiver: "Fee waiver / qualifying activity" },
    ko: { earlyWithdrawalPenalty: "중도 인출 위약금", feeWaiver: "수수료 면제 조건" },
    ja: { earlyWithdrawalPenalty: "中途解約ペナルティ", feeWaiver: "手数料免除条件" }
  };
  return labels[locale as keyof typeof labels]?.[field] ?? labels.en[field];
}

function loanMetricLabel(field: "rateType" | "term", locale: string) {
  const labels = {
    en: { rateType: "Rate type", term: "Term" },
    ko: { rateType: "금리 유형", term: "기간" },
    ja: { rateType: "金利タイプ", term: "期間" }
  };
  return labels[locale as keyof typeof labels]?.[field] ?? labels.en[field];
}

function essentialMetricLabel(field: "creditLimit" | "loanAmount" | "redeemability" | "security" | "transactions", locale: string) {
  const labels = {
    en: { creditLimit: "Credit limit", loanAmount: "Loan amount", redeemability: "Redeemability", security: "Security", transactions: "Included transactions" },
    ko: { creditLimit: "신용 한도", loanAmount: "대출 금액", redeemability: "중도해지 가능 여부", security: "담보 여부", transactions: "포함 거래 횟수" },
    ja: { creditLimit: "利用限度額", loanAmount: "借入額", redeemability: "中途解約可否", security: "担保", transactions: "無料取引回数" }
  };
  return labels[locale as keyof typeof labels]?.[field] ?? labels.en[field];
}

function formatTransactions(product: PublicProduct, locale: string) {
  if (product.unlimited_transactions_flag === true) {
    return locale === "ko" ? "무제한" : locale === "ja" ? "無制限" : "Unlimited";
  }
  if (product.included_transactions !== null) {
    const count = new Intl.NumberFormat(getIntlLocale(locale)).format(product.included_transactions);
    return locale === "ko" ? `월 ${count}회` : locale === "ja" ? `月${count}回` : `${count} / month`;
  }
  return getPublicMessages(locale).common.notDisclosed;
}

function formatRedeemability(product: PublicProduct, locale: string) {
  const redeemable = product.redeemable_flag ?? (product.non_redeemable_flag === null ? null : !product.non_redeemable_flag);
  if (redeemable === null) {
    return getPublicMessages(locale).common.notDisclosed;
  }
  if (redeemable) {
    return locale === "ko" ? "중도해지 가능" : locale === "ja" ? "中途解約可能" : "Redeemable";
  }
  return locale === "ko" ? "중도해지 불가" : locale === "ja" ? "中途解約不可" : "Non-redeemable";
}

function formatSecurity(product: PublicProduct, locale: string) {
  const stated = product.security_requirement ?? product.collateral_text;
  if (stated) {
    return stated;
  }
  if (product.secured_flag === null) {
    return getPublicMessages(locale).common.notDisclosed;
  }
  if (product.secured_flag) {
    return locale === "ko" ? "담보 필요" : locale === "ja" ? "担保あり" : "Secured";
  }
  return locale === "ko" ? "무담보" : locale === "ja" ? "無担保" : "Unsecured";
}

function formatProductTerm(product: PublicProduct, locale: string) {
  if (product.term_length_text) {
    return product.term_length_text;
  }
  if (product.term_length_days !== null) {
    return formatTerm(product.term_length_days, locale);
  }
  const rows = product.term_rate_table;
  const firstRow = rows[0];
  if (rows.length === 1 && firstRow) {
    return firstRow.term_label ?? formatTerm(firstRow.term_length_days, locale);
  }
  if (rows.length > 1) {
    return locale === "ko" ? `${rows.length}개 기간` : locale === "ja" ? `${rows.length}期間` : `${rows.length} terms`;
  }
  return getPublicMessages(locale).common.notDisclosed;
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
