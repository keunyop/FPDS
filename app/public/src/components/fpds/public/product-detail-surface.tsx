import { publicFactCopy } from "@/lib/public-fact-copy";
import { BankHandoffPanel } from "@/components/fpds/public/bank-handoff-panel";
import { BankHandoffDock } from "@/components/fpds/public/bank-handoff-dock";
import { AddToComparison } from "@/components/fpds/public/comparison-controls";
import { comparisonCopy } from "@/lib/public-comparison-copy";
import { ArrowLeft, ArrowRight, RefreshCw } from "lucide-react";
import Link from "next/link";
import type { ReactNode } from "react";

import { ProductVerification } from "@/components/fpds/public/product-verification";
import { BankLogo } from "@/components/fpds/public/bank-logo";
import { PublicInformationNotice } from "@/components/fpds/public/public-information-notice";
import { PublicFeedbackDialog } from "@/components/fpds/public/public-feedback-dialog";
import { InterestCalculator } from "@/components/fpds/public/interest-calculator";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader } from "@/components/ui/card";
import { getPublicDesignCopy, getPublicMessages } from "@/lib/public-locale";
import type { PublicProduct, PublicProductDetailResponse } from "@/lib/public-api";
import {
  buildPublicProductMetrics,
  buildPublicOptionalMetrics,
  formatPublicCurrency as formatCurrency,
  formatPublicRate as formatRate,
  formatPublicTerm as formatTerm,
  getCardLabel as cardLabel,
  getLoanLabel as loanLabel
} from "@/lib/public-product-presentation";
import { buildPublicHref, type ProductGridPageFilters } from "@/lib/public-query";
import { buildBrandedProductName } from "@/lib/public-seo";
import { cn } from "@/lib/utils";

type ProductDetailSurfaceProps = {
  apiUnavailable: boolean;
  detail: PublicProductDetailResponse | null;
  filters: ProductGridPageFilters;
  relatedProducts: PublicProduct[];
  otherBanksHref?: string | null;
};

type DetailFact = {
  label: string;
  value: string;
};

export function ProductDetailSurface({
  apiUnavailable,
  detail,
  filters,
  relatedProducts,
  otherBanksHref
}: ProductDetailSurfaceProps) {
  const copy = getPublicMessages(filters.locale);
  const designCopy = getPublicDesignCopy(filters.locale);
  const fallbackCatalogPath = filters.catalogProductTypes.includes("credit-card")
    ? "/cards"
    : filters.catalogProductTypes.some((productType) => ["mortgage", "personal-loan", "line-of-credit"].includes(productType))
      ? "/loans"
      : "/products";
  const productsHref = buildPublicHref(fallbackCatalogPath, filters);

  if (apiUnavailable || !detail) {
    return (
      <main className="mx-auto w-full max-w-5xl px-4 py-10 md:px-6">
        <Card className="border-destructive/25">
          <CardHeader>
            <h1 className="text-lg font-semibold">{copy.grid.retryTitle}</h1>
            <CardDescription>{copy.grid.retryBody}</CardDescription>
          </CardHeader>
          <CardContent className="flex flex-wrap gap-2">
            <Button asChild>
              <Link href={productsHref}>
                <RefreshCw className="size-4" aria-hidden="true" />
                {copy.grid.retryButton}
              </Link>
            </Button>
            <Button asChild variant="outline">
              <Link href={productsHref}>
                <ArrowLeft className="size-4" aria-hidden="true" />
                {copy.detail.backToList}
              </Link>
            </Button>
          </CardContent>
        </Card>
      </main>
    );
  }

  const product = detail.product;
  const displayName = buildBrandedProductName(product);
  const catalogPath = product.product_type === "credit-card" ? "/cards" : product.product_family === "lending" ? "/loans" : "/products";
  const catalogHref = buildPublicHref(catalogPath, filters);
  const backToCatalog = product.product_type === "credit-card"
    ? cardLabel("back", filters.locale)
    : product.product_family === "lending"
      ? loanLabel("back", filters.locale)
      : copy.detail.backToList;
  const metricCards = buildMetricCards(product, filters.locale);
  const detailFacts = buildPublicOptionalMetrics(product, filters.locale);
  const factCopy = publicFactCopy(filters.locale);
  const similarHref = buildPublicHref(catalogPath, {
    ...filters,
    bankCodes: [product.bank_code],
    page: 1,
    productTypes: [product.product_type]
  });
  const termRateRows = product.term_rate_table ?? [];

  return (
    <main className="mx-auto w-full max-w-7xl overflow-x-clip px-4 py-7 md:px-6 md:py-9">
      <div className="flex w-full min-w-0 max-w-[calc(100vw-2rem)] flex-col gap-5 md:max-w-full">
        <nav aria-label={breadcrumbLabel(filters.locale)}>
          <ol className="flex min-w-0 flex-wrap items-center gap-2 text-xs text-muted-foreground">
            <li>
              <Link className="underline-offset-4 hover:text-foreground hover:underline" href={buildPublicHref("/", filters)}>
                {copy.nav.dashboard}
              </Link>
            </li>
            <li aria-hidden="true">/</li>
            <li>
              <Link className="underline-offset-4 hover:text-foreground hover:underline" href={catalogHref}>
                {catalogLabel(product, filters.locale)}
              </Link>
            </li>
            <li aria-hidden="true">/</li>
            <li aria-current="page" className="min-w-0 font-medium text-foreground [overflow-wrap:anywhere]">
              {displayName}
            </li>
          </ol>
        </nav>

        <Button asChild variant="ghost" className="w-fit">
          <Link href={catalogHref}>
            <ArrowLeft className="size-4" aria-hidden="true" />
            {backToCatalog}
          </Link>
        </Button>

        <section className="border-y border-foreground/15 py-6 md:py-9" data-seo-product-content>
          <div className="grid min-w-0 grid-cols-[minmax(0,1fr)] gap-5 lg:grid-cols-[minmax(0,1fr)_20rem] lg:items-start">
            <div className="flex min-w-0 flex-col gap-4 sm:flex-row sm:items-start">
              <BankLogo bankCode={product.bank_code} bankName={product.bank_name} />
              <div className="min-w-0 flex-1">
                <p className="font-mono text-[10px] font-semibold uppercase tracking-[0.14em] text-muted-foreground">{product.bank_name}</p>
                <h1 className="text-balance mt-2 font-display text-4xl font-semibold leading-[0.98] tracking-[-0.05em] text-foreground [overflow-wrap:anywhere] md:text-6xl">{displayName}</h1>
                {product.description_short ? <p className="mt-4 max-w-3xl text-sm leading-7 text-muted-foreground md:text-base">{product.description_short}</p> : null}
                <div className="mt-4 flex flex-wrap gap-2">
                  <Badge>{`${product.product_type_label} · ${product.currency}`}</Badge>
                  {product.subtype_label ? <Badge muted>{product.subtype_label}</Badge> : null}
                  {product.product_highlight_badge_label ? <Badge muted>{product.product_highlight_badge_label}</Badge> : null}
                </div>
              </div>
            </div>
            <div className="grid min-w-0 gap-2 sm:flex sm:flex-wrap lg:grid lg:grid-cols-1">
              <AddToComparison product={product} locale={filters.locale} />
              {otherBanksHref ? <Button asChild className="w-full sm:w-auto lg:w-full" variant="outline"><Link href={otherBanksHref}>{comparisonCopy(filters.locale).otherBanks}<ArrowRight className="size-4" aria-hidden="true" /></Link></Button> : null}
              <Button asChild className="w-full sm:w-auto lg:w-full" variant="outline">
                <Link href={similarHref}>
                  {copy.detail.similarProducts}
                  <ArrowRight className="size-4" aria-hidden="true" />
                </Link>
              </Button>
            </div>
          </div>

          <h2 className="mt-7 text-sm font-semibold">{factCopy.core}</h2>
          <dl className={cn("mt-3 grid gap-px border border-border bg-border", metricCards.length === 2 ? "sm:grid-cols-2" : "sm:grid-cols-3")}>
            {metricCards.map((metric, index) => (
              <MetricTile highlight={index === 0} key={metric.label} label={metric.label} value={metric.value} />
            ))}
          </dl>
          <BankHandoffPanel product={product} locale={filters.locale} compact />
        </section>

        <section className="grid gap-7 lg:grid-cols-[minmax(0,1fr)_23rem] lg:items-start">
          <div className="grid gap-4">
            {termRateRows.length ? <TermRateTable currency={product.currency} locale={filters.locale} rows={termRateRows} /> : null}
            <section aria-labelledby="product-facts-title">
              <div className="border-b border-foreground/15 pb-3">
                <p className="font-mono text-[10px] font-semibold uppercase tracking-[0.14em] text-verification">{designCopy.verified}</p>
                <h2 id="product-facts-title" className="mt-2 text-2xl font-semibold tracking-[-0.03em]">{factCopy.additional}</h2>
              </div>
              {detailFacts.length ? <dl className="grid sm:grid-cols-2">
                {detailFacts.map((fact, index) => (
                  <div className={cn("border-b border-border py-4", index % 2 === 0 ? "sm:pr-5" : "sm:pl-5")} key={fact.label}>
                    <Fact label={fact.label} value={fact.value} />
                  </div>
                ))}
              </dl> : <p className="py-4 text-sm text-muted-foreground">{factCopy.empty}</p>}
            </section>

          </div>

          <div className="grid gap-4">
            {['savings', 'gic'].includes(product.product_type) ? (
              <InterestCalculator key={product.product_id} product={product} locale={filters.locale} />
            ) : null}

            <aside className="border border-foreground/20 bg-card/75 p-5 shadow-[8px_8px_0_rgba(28,39,35,0.05)]">
              <p className="font-mono text-[10px] font-semibold uppercase tracking-[0.14em] text-verification">{designCopy.officialRecord}</p>
              <h2 className="mt-2 text-xl font-semibold tracking-[-0.02em]">{copy.detail.disclosureTitle}</h2>
              <ProductVerification product={product} locale={filters.locale} detailed />
              <div className="mt-4 grid gap-2">
                <Button asChild className="min-h-11 w-full rounded-full" size="sm" variant="outline">
                  <Link href={buildPublicHref("/methodology", filters)}>{copy.nav.methodology}</Link>
                </Button>
                <PublicFeedbackDialog
                  countryCode={product.country_code}
                  locale={filters.locale}
                  mode="product_error"
                  product={{
                    bankName: product.bank_name,
                    productId: product.product_id,
                    productName: product.product_name,
                  }}
                />
              </div>
            </aside>
          </div>
        </section>

        <BankHandoffDock products={[product]} locale={filters.locale} />
        <PublicInformationNotice locale={filters.locale} />

        {relatedProducts.length ? (
          <section aria-labelledby="related-products-title" className="border-t border-foreground/15 pt-6">
            <div className="flex flex-wrap items-end justify-between gap-3">
              <div>
                <p className="font-mono text-[10px] font-semibold uppercase tracking-[0.14em] text-muted-foreground">
                  {product.product_type_label}
                </p>
                <h2 id="related-products-title" className="mt-2 text-2xl font-semibold tracking-[-0.03em] [overflow-wrap:anywhere]">
                  {relatedTitle(product.bank_name, filters.locale)}
                </h2>
              </div>
              <Link
                className="inline-flex min-h-11 items-center text-sm font-semibold text-primary underline-offset-4 hover:underline"
                href={similarHref}
              >
                {copy.detail.similarProducts}
                <ArrowRight className="ml-1 size-4" aria-hidden="true" />
              </Link>
            </div>
            <ul className="mt-4 grid gap-px bg-border sm:grid-cols-2 lg:grid-cols-4">
              {relatedProducts.map((relatedProduct) => (
                <li className="bg-background" key={relatedProduct.product_id}>
                  <Link
                    className="flex min-h-24 flex-col justify-between gap-3 p-4 hover:bg-muted/40"
                    href={buildPublicHref(
                      `/products/${encodeURIComponent(relatedProduct.product_id)}`,
                      filters
                    )}
                  >
                    <span className="font-semibold leading-5">
                      {buildBrandedProductName(relatedProduct)}
                    </span>
                    <span className="text-xs text-muted-foreground">
                      {relatedProduct.product_type_label}
                    </span>
                  </Link>
                </li>
              ))}
            </ul>
          </section>
        ) : null}
      </div>
    </main>
  );
}

function breadcrumbLabel(locale: string) {
  if (locale === "ko") {
    return "경로";
  }
  if (locale === "ja") {
    return "パンくず";
  }
  return "Breadcrumb";
}

function catalogLabel(product: PublicProduct, locale: string) {
  const copy = getPublicMessages(locale);
  if (product.product_type === "credit-card") {
    return copy.nav.card;
  }
  return product.product_family === "lending" ? copy.nav.loan : copy.nav.products;
}

function relatedTitle(bankName: string, locale: string) {
  if (locale === "ko") {
    return bankName + "의 관련 상품";
  }
  if (locale === "ja") {
    return bankName + "の関連商品";
  }
  return "Related products from " + bankName;
}

function MetricTile({ highlight, label, value }: { highlight?: boolean; label: string; value: string }) {
  return (
    <div className={cn("min-w-0 bg-card px-4 py-5 sm:px-5", highlight && "bg-verification-soft")}>
      <dt className={cn("text-xs font-semibold", highlight ? "text-verification" : "text-muted-foreground")}>{label}</dt>
      <dd className={cn("mt-2 break-words font-display font-semibold leading-tight tracking-[-0.04em] text-foreground tabular-nums", value.length > 24 ? "text-lg leading-relaxed tracking-normal" : highlight ? "text-4xl" : "text-3xl")}>{value}</dd>
    </div>
  );
}

function Badge({ children, muted = false }: { children: string; muted?: boolean }) {
  return (
    <span className={cn("rounded-md border px-2 py-1 text-xs font-medium", muted ? "border-border bg-background text-muted-foreground" : "border-primary/20 bg-secondary text-secondary-foreground")}>
      {children}
    </span>
  );
}

function Fact({ label, value }: { label: string; value: ReactNode }) {
  return (
    <div>
      <dt className="text-xs font-medium text-muted-foreground">{label}</dt>
      <dd className="mt-1 break-words text-sm font-medium leading-6 text-foreground">{value}</dd>
    </div>
  );
}

function buildMetricCards(product: PublicProduct, locale: string): DetailFact[] {
  return buildPublicProductMetrics(product, locale);
}

function TermRateTable({
  currency,
  locale,
  rows,
}: {
  currency: string;
  locale: string;
  rows: PublicProduct["term_rate_table"];
}) {
  const showMinimum = rows.some(row => row.minimum_deposit != null);
  const showNotes = rows.some(row => row.notes?.trim());
  return (
    <Card className="border-border/80 shadow-sm">
      <CardHeader>
        <h2 className="text-base font-semibold">{getPublicMessages(locale).detail.termRates}</h2>
      </CardHeader>
      <CardContent className="overflow-x-auto">
        <table className="w-full text-left text-sm">
          <thead className="border-b border-border text-xs font-medium text-muted-foreground">
            <tr>
              <th className="py-2 pr-4">{detailLabel("term", locale)}</th>
              <th className="py-2 pr-4">{detailLabel("rate", locale)}</th>
              {showMinimum ? <th className="py-2 pr-4">{detailLabel("minimumDeposit", locale)}</th> : null}
              {showNotes ? <th className="py-2">{detailLabel("notes", locale)}</th> : null}
            </tr>
          </thead>
          <tbody>
            {rows.map((row, index) => (
              <tr className="border-b border-border/60 last:border-0" key={`${row.term_label ?? row.term_length_days ?? "term"}-${index}`}>
                <td className="py-3 pr-4 font-medium text-foreground">{row.term_label ?? formatTerm(row.term_length_days, locale)}</td>
                <td className="py-3 pr-4 text-base font-semibold tabular-nums text-foreground">{formatRate(row.rate, locale)}</td>
                {showMinimum ? <td className="py-3 pr-4 tabular-nums text-muted-foreground">{row.minimum_deposit == null ? publicFactCopy(locale).missing : formatCurrency(row.minimum_deposit, currency, locale)}</td> : null}
                {showNotes ? <td className="py-3 text-muted-foreground">{row.notes || publicFactCopy(locale).missing}</td> : null}
              </tr>
            ))}
          </tbody>
        </table>
      </CardContent>
    </Card>
  );
}

function detailLabel(key: string, locale: string) {
  const labels: Record<string, string> = {
    applicationMethod: "Application method",
    base12MonthRate: "Base rate, 12 months",
    customerTags: "Customer tags",
    depositAmount: "Entry amount",
    depositInsurance: "Deposit insurance",
    eligibility: "Eligibility",
    minimumDeposit: "Minimum deposit",
    notes: "Notes",
    postMaturityRate: "Post-maturity rate",
    rate: "Rate",
    taxBenefits: "Tax benefits",
    term: "Term",
  };
  if (locale === "ko") {
    const koLabels: Record<string, string> = {
      applicationMethod: "가입 방법",
      base12MonthRate: "기본금리(12개월)",
      customerTags: "고객 태그",
      depositAmount: "가입 금액",
      depositInsurance: "예금자 보호",
      eligibility: "가입 대상",
      minimumDeposit: "최소 가입 금액",
      notes: "비고",
      postMaturityRate: "만기 후 이자율",
      rate: "금리",
      taxBenefits: "세제 혜택",
      term: "기간",
    };
    return koLabels[key] ?? labels[key] ?? key;
  }
  if (locale === "ja") {
    const jaLabels: Record<string, string> = {
      applicationMethod: "申込方法",
      base12MonthRate: "12か月基準金利",
      customerTags: "顧客タグ",
      depositAmount: "加入金額",
      depositInsurance: "預金保険",
      eligibility: "対象条件",
      minimumDeposit: "最低預入額",
      notes: "注記",
      postMaturityRate: "満期後金利",
      rate: "金利",
      taxBenefits: "税制優遇",
      term: "期間",
    };
    return jaLabels[key] ?? labels[key] ?? key;
  }
  return labels[key] ?? key;
}
