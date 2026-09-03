import { ArrowLeft, ArrowRight, ExternalLink, RefreshCw } from "lucide-react";
import Link from "next/link";
import type { ReactNode } from "react";

import { BankLogo } from "@/components/fpds/public/bank-logo";
import { TrackedOfficialBankLink } from "@/components/fpds/public/product-engagement-link";
import { PublicInformationNotice } from "@/components/fpds/public/public-information-notice";
import { PublicFeedbackDialog } from "@/components/fpds/public/public-feedback-dialog";
import { InterestCalculator } from "@/components/fpds/public/interest-calculator";
import { PublicFreshness } from "@/components/fpds/public/public-freshness";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader } from "@/components/ui/card";
import { getPublicDesignCopy, getPublicMessages } from "@/lib/public-locale";
import type { PublicProduct, PublicProductDetailResponse } from "@/lib/public-api";
import {
  buildPublicProductMetrics,
  formatPublicCurrency as formatCurrency,
  formatPublicPurchaseRate as formatPurchaseRate,
  formatPublicRate as formatRate,
  formatPublicRedeemability as formatRedeemability,
  formatPublicSecurity as formatSecurity,
  formatPublicTerm as formatTerm,
  formatPublicTransactions as formatTransactions,
  getCardLabel as cardLabel,
  getEssentialLabel as essentialLabel,
  getLoanLabel as loanLabel,
  getMarketLabel as marketTextLabel
} from "@/lib/public-product-presentation";
import { buildPublicHref, type ProductGridPageFilters } from "@/lib/public-query";
import { buildBrandedProductName } from "@/lib/public-seo";
import { cn } from "@/lib/utils";

type ProductDetailSurfaceProps = {
  apiUnavailable: boolean;
  detail: PublicProductDetailResponse | null;
  filters: ProductGridPageFilters;
  relatedProducts: PublicProduct[];
};

type DetailFact = {
  label: string;
  value: string;
};

export function ProductDetailSurface({
  apiUnavailable,
  detail,
  filters,
  relatedProducts
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
  const detailFacts = buildDetailFacts(product, filters.locale);
  const disclosureDate = formatIsoDate(product.last_verified_at ?? detail.freshness.refreshed_at);
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

        <section className="border-y border-foreground/15 py-6 md:py-9">
          <div className="grid min-w-0 grid-cols-[minmax(0,1fr)] gap-5 lg:grid-cols-[minmax(0,1fr)_auto] lg:items-start">
            <div className="flex min-w-0 flex-col gap-4 sm:flex-row sm:items-start">
              <BankLogo bankCode={product.bank_code} bankName={product.bank_name} />
              <div className="min-w-0 flex-1">
                <p className="font-mono text-[10px] font-semibold uppercase tracking-[0.14em] text-muted-foreground">{product.bank_name}</p>
                <h1 className="text-balance mt-2 font-display text-4xl font-semibold leading-[0.98] tracking-[-0.05em] text-foreground [overflow-wrap:anywhere] md:text-6xl">{displayName}</h1>
                {product.description_short ? <p className="mt-4 max-w-3xl text-sm leading-7 text-muted-foreground md:text-base">{product.description_short}</p> : null}
                <div className="mt-4 flex flex-wrap gap-2">
                  <Badge>{product.product_type_label}</Badge>
                  {product.subtype_label ? <Badge muted>{product.subtype_label}</Badge> : null}
                  {product.product_highlight_badge_label ? <Badge muted>{product.product_highlight_badge_label}</Badge> : null}
                </div>
              </div>
            </div>
            <div className="grid min-w-0 gap-2 sm:flex sm:flex-wrap lg:justify-end">
              {product.product_url ? (
                <Button asChild className="w-full sm:w-auto">
                  <TrackedOfficialBankLink countryCode={product.country_code} href={product.product_url} productId={product.product_id}>
                    {copy.detail.officialPage}
                    <ExternalLink className="size-4" aria-hidden="true" />
                  </TrackedOfficialBankLink>
                </Button>
              ) : null}
              <Button asChild className="w-full sm:w-auto" variant="outline">
                <Link href={similarHref}>
                  {copy.detail.similarProducts}
                  <ArrowRight className="size-4" aria-hidden="true" />
                </Link>
              </Button>
            </div>
          </div>

          <dl className="mt-7 grid border-y border-border sm:grid-cols-3 sm:divide-x sm:divide-border">
            {metricCards.map((metric, index) => (
              <MetricTile highlight={index === 0} key={metric.label} label={metric.label} value={metric.value} />
            ))}
          </dl>
        </section>

        <section
          aria-labelledby="product-overview-title"
          className="min-w-0 border-b border-foreground/15 pb-6"
          data-seo-product-content
        >
          <p className="font-mono text-[10px] font-semibold uppercase tracking-[0.14em] text-verification">
            {designCopy.verified}
          </p>
          <h2
            id="product-overview-title"
            className="mt-2 text-2xl font-semibold tracking-[-0.03em] [overflow-wrap:anywhere]"
          >
            {overviewTitle(displayName, filters.locale)}
          </h2>
          <div className="mt-3 grid max-w-4xl gap-3 text-sm leading-7 text-muted-foreground md:text-base">
            {buildProductOverview(product, disclosureDate, filters.locale).map((paragraph) => (
              <p key={paragraph}>{paragraph}</p>
            ))}
          </div>
        </section>

        <section className="grid gap-7 lg:grid-cols-[minmax(0,1fr)_23rem] lg:items-start">
          <div className="grid gap-4">
            <section aria-labelledby="product-facts-title">
              <div className="border-b border-foreground/15 pb-3">
                <p className="font-mono text-[10px] font-semibold uppercase tracking-[0.14em] text-verification">{designCopy.verified}</p>
                <h2 id="product-facts-title" className="mt-2 text-2xl font-semibold tracking-[-0.03em]">{designCopy.availableFacts}</h2>
              </div>
              <dl className="grid sm:grid-cols-2">
                <div className="border-b border-border py-4 sm:pr-5">
                  <Fact label={copy.grid.productTypes} value={product.product_type_label} />
                </div>
                {detailFacts.map((fact, index) => (
                  <div className={cn("border-b border-border py-4", index % 2 === 0 ? "sm:pl-5" : "sm:pr-5")} key={fact.label}>
                    <Fact label={fact.label} value={fact.value} />
                  </div>
                ))}
              </dl>
            </section>

            {termRateRows.length ? <TermRateTable currency={product.currency} locale={filters.locale} rows={termRateRows} /> : null}
          </div>

          <div className="grid gap-4">
            {product.product_family === "deposit" && product.public_display_rate !== null ? (
              <InterestCalculator
                currency={product.currency}
                locale={filters.locale}
                minimumBalance={product.minimum_balance}
                minimumDeposit={product.minimum_deposit}
                productType={product.product_type}
                rate={product.public_display_rate}
                termLengthDays={product.term_length_days}
              />
            ) : null}

            <aside className="border border-foreground/20 bg-card/75 p-5 shadow-[8px_8px_0_rgba(28,39,35,0.05)]">
              <p className="font-mono text-[10px] font-semibold uppercase tracking-[0.14em] text-verification">{designCopy.officialRecord}</p>
              <h2 className="mt-2 text-xl font-semibold tracking-[-0.02em]">{copy.detail.disclosureTitle}</h2>
              <PublicFreshness className="mt-4" freshness={detail.freshness} locale={filters.locale} />
              <p className="mt-4 text-xs leading-5 text-muted-foreground">{buildDisclosure(disclosureDate, filters.locale)}</p>
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
              <p className="mt-4 border-t border-border pt-4 text-xs leading-5 text-muted-foreground">{designCopy.evidenceBoundary}</p>
            </aside>
          </div>
        </section>

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

function overviewTitle(displayName: string, locale: string) {
  if (locale === "ko") {
    return displayName + " 개요";
  }
  if (locale === "ja") {
    return displayName + "の概要";
  }
  return "About " + displayName;
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

function buildProductOverview(
  product: PublicProduct,
  verifiedDate: string,
  locale: string
) {
  const displayName = buildBrandedProductName(product);
  const intro = localizedOverviewIntro(
    displayName,
    product.product_type_label,
    verifiedDate,
    locale
  );
  const details: string[] = [];

  if (product.product_id === "prod_IbZVSqaogb3BkWBd") {
    addSentence(details, product.interest_rate_summary);
    addSentence(details, product.credit_limit_text);
    addSentence(details, product.collateral_text);
  } else if (product.product_id === "prod_vIoiSSdl3kwJjM1d") {
    addSentence(details, product.description_short);
    addLabeledSentence(details, "Available terms", product.term_length_text);
    addSentence(details, cleanPublicSummary(product.prepayment_privileges));
  } else if (product.product_id === "prod_g-yAIYCGJyxWOm8d") {
    details.push(
      'The verified product name is Vancity Fair and Fast Loan™; this is the Vancity loan sometimes searched as "Vancity Fast and Fair Loan."'
    );
    addLabeledSentence(details, "Published loan amount", product.loan_amount_text);
    addLabeledSentence(details, "Published term", product.term_length_text);
  } else if (product.product_id === "prod_h18VyAGREB3optuJ") {
    addSentence(details, product.description_short);
    addLabeledSentence(details, "Eligibility", product.eligibility_text);
    addLabeledSentence(details, "Available terms", product.term_length_text);
    addLabeledSentence(details, "Payment frequency", product.payment_frequency);
    addLabeledSentence(details, "Application method", product.application_method);
  } else {
    addSentence(details, product.description_short);
    addLabeledSentence(details, "Rate type", product.rate_type);
    addLabeledSentence(details, "Available terms", product.term_length_text);
    addLabeledSentence(details, "Published amount or limit", product.loan_amount_text ?? product.credit_limit_text);
  }

  return [intro, ...details.slice(0, 4)];
}

function localizedOverviewIntro(
  displayName: string,
  productType: string,
  verifiedDate: string,
  locale: string
) {
  if (locale === "ko") {
    return `SwitchaBank의 검토된 공개 스냅샷은 ${displayName}을(를) ${productType} 상품으로 표시합니다. 최종 검증일은 ${verifiedDate}입니다.`;
  }
  if (locale === "ja") {
    return `SwitchaBankの確認済み公開スナップショットでは、${displayName}を${productType}商品として掲載しています。最終確認日は${verifiedDate}です。`;
  }
  return `SwitchaBank lists ${displayName} as a ${productType} in its reviewed public snapshot, last verified ${verifiedDate}.`;
}

function addSentence(sentences: string[], value: string | null) {
  const normalized = cleanPublicSummary(value);
  if (normalized) {
    sentences.push(withTerminalPunctuation(normalized));
  }
}

function addLabeledSentence(
  sentences: string[],
  label: string,
  value: string | null
) {
  const normalized = cleanPublicSummary(value);
  if (normalized) {
    sentences.push(`${label}: ${withTerminalPunctuation(normalized)}`);
  }
}

function cleanPublicSummary(value: string | null) {
  if (
    !value ||
    value.length > 260 ||
    /(calculator|view tool|click|learn more)/i.test(value)
  ) {
    return null;
  }
  return value.replace(/\s+/g, " ").trim();
}

function withTerminalPunctuation(value: string) {
  return /[.!?]$/.test(value) ? value : value + ".";
}

function MetricTile({ highlight, label, value }: { highlight?: boolean; label: string; value: string }) {
  return (
    <div className={cn("min-h-28 px-1 py-5 sm:px-5", highlight && "bg-verification-soft/45")}>
      <dt className={cn("font-mono text-[10px] font-semibold uppercase tracking-wide", highlight ? "text-verification" : "text-muted-foreground")}>{label}</dt>
      <dd className="mt-2 break-words font-display text-3xl font-semibold leading-tight tracking-[-0.04em] text-foreground tabular-nums">{value}</dd>
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
  return buildPublicProductMetrics(product, locale).slice(0, 3);
}

function buildDetailFacts(product: PublicProduct, locale: string) {
  const facts: DetailFact[] = [];
  if (product.product_type === "credit-card") {
    addFact(facts, cardLabel("annualFee", locale), formatCurrency(product.annual_fee, product.currency, locale), locale);
    addFact(facts, cardLabel("purchaseRate", locale), formatPurchaseRate(product, locale), locale);
    addFact(facts, detailLabel("eligibility", locale), product.eligibility_text, locale);
    addFact(facts, detailLabel("applicationMethod", locale), product.application_method, locale);
    addFact(facts, getPublicDesignCopy(locale).sourceLanguage, product.source_language, locale);
    return facts;
  }
  if (product.product_family === "lending") {
    addFact(
      facts,
      loanLabel("rate", locale),
      product.interest_rate_summary ?? product.mortgage_rate ?? product.interest_rate,
      locale
    );
    addFact(facts, loanLabel("rateType", locale), product.rate_type, locale);
    addFact(facts, loanLabel("term", locale), product.term_length_text, locale);
    addFact(facts, loanLabel("amortization", locale), product.amortization_text, locale);
    addFact(facts, loanLabel("payment", locale), product.payment_frequency, locale);
    addFact(facts, loanLabel("prepayment", locale), product.prepayment_privileges, locale);
    addFact(facts, loanLabel("loanAmount", locale), product.loan_amount_text ?? product.credit_limit_text, locale);
    addFact(facts, getPublicDesignCopy(locale).monthlyPayment, product.monthly_payment_text, locale);
    addFact(facts, getPublicDesignCopy(locale).securityRequirement, formatSecurity(product, locale), locale);
    addFact(facts, detailLabel("eligibility", locale), product.eligibility_text, locale);
    addFact(facts, detailLabel("applicationMethod", locale), product.application_method, locale);
    addFact(facts, getPublicDesignCopy(locale).sourceLanguage, product.source_language, locale);
    return facts;
  }
  if (product.product_type === "chequing") {
    addFact(facts, essentialLabel("transactions", locale), formatTransactions(product, locale), locale);
  }
  if (product.product_type === "gic") {
    if (product.country_code === "US") {
      addFact(facts, marketTextLabel("earlyWithdrawalPenalty", locale), product.early_withdrawal_penalty, locale);
    } else {
      addFact(facts, essentialLabel("redeemability", locale), formatRedeemability(product, locale), locale);
    }
  }
  const depositAmount = product.minimum_deposit ?? product.minimum_balance;
  if (depositAmount != null) {
    addFact(facts, detailLabel("depositAmount", locale), formatCurrency(depositAmount, product.currency, locale), locale);
  }
  if (product.base_12_month_rate != null) {
    addFact(facts, detailLabel("base12MonthRate", locale), formatRate(product.base_12_month_rate, locale), locale);
  }
  addFact(facts, detailLabel("customerTags", locale), product.target_customer_tag_labels.join(", "), locale);
  addFact(facts, detailLabel("eligibility", locale), product.eligibility_text, locale);
  addFact(facts, detailLabel("applicationMethod", locale), product.application_method, locale);
  addFact(facts, detailLabel("postMaturityRate", locale), product.post_maturity_interest_rate, locale);
  addFact(facts, detailLabel("taxBenefits", locale), product.tax_benefits, locale);
  addFact(facts, detailLabel("depositInsurance", locale), product.deposit_insurance, locale);
  addFact(facts, getPublicDesignCopy(locale).sourceLanguage, product.source_language, locale);
  return facts;
}

function addFact(facts: DetailFact[], label: string, value: string | null, locale = "en") {
  const notDisclosed = getPublicMessages(locale).common.notDisclosed;
  if (value && value.trim() && value !== notDisclosed) {
    facts.push({ label, value });
  }
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
  return (
    <Card className="border-border/80 shadow-sm">
      <CardHeader>
        <h2 className="text-base font-semibold">{getPublicMessages(locale).detail.termRates}</h2>
      </CardHeader>
      <CardContent className="overflow-x-auto">
        <table className="w-full min-w-[36rem] text-left text-sm">
          <thead className="border-b border-border text-xs font-medium text-muted-foreground">
            <tr>
              <th className="py-2 pr-4">{detailLabel("term", locale)}</th>
              <th className="py-2 pr-4">{detailLabel("rate", locale)}</th>
              <th className="py-2 pr-4">{detailLabel("minimumDeposit", locale)}</th>
              <th className="py-2">{detailLabel("notes", locale)}</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((row, index) => (
              <tr className="border-b border-border/60 last:border-0" key={`${row.term_label ?? row.term_length_days ?? "term"}-${index}`}>
                <td className="py-3 pr-4 font-medium text-foreground">{row.term_label ?? formatTerm(row.term_length_days, locale)}</td>
                <td className="py-3 pr-4 tabular-nums text-foreground">{formatRate(row.rate, locale)}</td>
                <td className="py-3 pr-4 tabular-nums text-muted-foreground">{formatCurrency(row.minimum_deposit ?? null, currency, locale)}</td>
                <td className="py-3 text-muted-foreground">{row.notes ?? ""}</td>
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

function formatIsoDate(value: string | null) {
  if (!value) {
    return "unknown date";
  }
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value.slice(0, 10);
  }
  return date.toISOString().slice(0, 10);
}

function buildDisclosure(date: string, locale: string) {
  if (locale === "ko") {
    return `${date} 기준 공개 스냅샷입니다. 금리와 가입 조건은 변경될 수 있으므로 신청 전 은행 공식 페이지에서 다시 확인하세요.`;
  }
  if (locale === "ja") {
    return `${date} 時点の公開スナップショットです。金利や申込条件は変更される場合があるため、申込前に銀行の公式ページで再確認してください。`;
  }
  return `Public snapshot as of ${date}. Rates and eligibility can change, so confirm them on the bank's official page before applying.`;
}
