import { ArrowLeft, ArrowRight, ExternalLink, FileText, RefreshCw, ShieldCheck } from "lucide-react";
import Link from "next/link";
import type { ReactNode } from "react";

import { BankLogo } from "@/components/fpds/public/bank-logo";
import { InterestCalculator } from "@/components/fpds/public/interest-calculator";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { getIntlLocale, getPublicMessages } from "@/lib/public-locale";
import type { PublicProduct, PublicProductDetailResponse } from "@/lib/public-api";
import { buildPublicHref, type ProductGridPageFilters } from "@/lib/public-query";
import { cn } from "@/lib/utils";

type ProductDetailSurfaceProps = {
  apiUnavailable: boolean;
  detail: PublicProductDetailResponse | null;
  filters: ProductGridPageFilters;
};

type DetailFact = {
  label: string;
  value: string;
};

export function ProductDetailSurface({ apiUnavailable, detail, filters }: ProductDetailSurfaceProps) {
  const copy = getPublicMessages(filters.locale);
  const productsHref = buildPublicHref("/products", filters);

  if (apiUnavailable || !detail) {
    return (
      <main className="mx-auto w-full max-w-5xl px-4 py-10 md:px-6">
        <Card className="border-destructive/25">
          <CardHeader>
            <CardTitle>{copy.grid.retryTitle}</CardTitle>
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
  const metricCards = buildMetricCards(product, filters.locale);
  const detailFacts = buildDetailFacts(product, filters.locale);
  const decisionItems = buildDecisionItems(product, filters.locale);
  const disclosureDate = formatIsoDate(product.last_verified_at ?? detail.freshness.refreshed_at);
  const similarHref = buildPublicHref("/products", {
    ...filters,
    bankCodes: [product.bank_code],
    page: 1,
    productTypes: [product.product_type]
  });
  const termRateRows = product.term_rate_table ?? [];

  return (
    <main className="mx-auto w-full max-w-7xl px-4 py-7 md:px-6 md:py-9">
      <div className="flex flex-col gap-5">
        <Button asChild variant="ghost" className="w-fit">
          <Link href={productsHref}>
            <ArrowLeft className="size-4" aria-hidden="true" />
            {copy.detail.backToList}
          </Link>
        </Button>

        <section className="grid gap-4 lg:grid-cols-[minmax(0,1fr)_22rem] lg:items-start">
          <div className="rounded-xl border border-border bg-card p-4 shadow-sm md:p-5">
            <div className="flex flex-col gap-4 sm:flex-row sm:items-start">
              <BankLogo bankCode={product.bank_code} bankName={product.bank_name} />
              <div className="min-w-0 flex-1">
                <p className="text-sm font-medium text-primary">{product.bank_name}</p>
                <h1 className="mt-2 break-words text-3xl font-semibold tracking-tight text-foreground md:text-4xl">{product.product_name}</h1>
                <div className="mt-4 flex flex-wrap gap-2">
                  <Badge>{product.product_type_label}</Badge>
                  {product.subtype_label ? <Badge muted>{product.subtype_label}</Badge> : null}
                  {product.product_highlight_badge_label ? <Badge muted>{product.product_highlight_badge_label}</Badge> : null}
                </div>
              </div>
            </div>

            <dl className="mt-5 grid gap-3 sm:grid-cols-3">
              {metricCards.map((metric, index) => (
                <MetricTile highlight={index === 0} key={metric.label} label={metric.label} value={metric.value} />
              ))}
            </dl>
          </div>

          <Card className="border-border/80 shadow-sm">
            <CardHeader>
              <CardDescription className="flex items-center gap-2">
                <ShieldCheck className="size-4" aria-hidden="true" />
                {copy.detail.decisionSummary}
              </CardDescription>
              <CardTitle className="text-base">{copy.detail.whatToCheck}</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <dl className="grid gap-3">
                <Fact label={copy.common.verifiedOn} value={formatDate(product.last_verified_at, filters.locale)} />
                <Fact label={copy.common.changedOn} value={formatDate(product.last_changed_at, filters.locale)} />
                <Fact label={copy.detail.sourceLanguage} value={product.source_language.toUpperCase()} />
              </dl>
              <div className="grid gap-2">
                {product.product_url ? (
                  <Button asChild>
                    <a href={product.product_url} target="_blank" rel="noreferrer">
                      {copy.detail.officialPage}
                      <ExternalLink className="size-4" aria-hidden="true" />
                    </a>
                  </Button>
                ) : null}
                <Button asChild variant="outline">
                  <Link href={similarHref}>
                    {copy.detail.similarProducts}
                    <ArrowRight className="size-4" aria-hidden="true" />
                  </Link>
                </Button>
              </div>
            </CardContent>
          </Card>
        </section>

        <section className="grid gap-4 lg:grid-cols-[minmax(0,1fr)_22rem] lg:items-start">
          <div className="grid gap-4">
            <InterestCalculator
              currency={product.currency}
              locale={filters.locale}
              minimumBalance={product.minimum_balance}
              minimumDeposit={product.minimum_deposit}
              productType={product.product_type}
              rate={product.public_display_rate}
              termLengthDays={product.term_length_days}
            />

            <Card className="border-border/80 shadow-sm">
              <CardHeader>
                <CardDescription className="flex items-center gap-2">
                  <FileText className="size-4" aria-hidden="true" />
                  {copy.detail.productFacts}
                </CardDescription>
                <CardTitle className="text-base">{copy.grid.resultSummary}</CardTitle>
              </CardHeader>
              <CardContent>
                <dl className="grid gap-4 sm:grid-cols-2">
                  <Fact label={copy.grid.banks} value={`${product.bank_name} (${product.bank_code})`} />
                  <Fact label={copy.grid.productTypes} value={product.product_type_label} />
                  {detailFacts.map((fact) => (
                    <Fact key={fact.label} label={fact.label} value={fact.value} />
                  ))}
                </dl>
              </CardContent>
            </Card>

            {termRateRows.length ? <TermRateTable currency={product.currency} locale={filters.locale} rows={termRateRows} /> : null}
          </div>

          <div className="grid gap-4">
            <Card className="border-border/80 shadow-sm">
              <CardHeader>
                <CardTitle className="text-base">{copy.detail.keyConditions}</CardTitle>
              </CardHeader>
              <CardContent>
                <dl className="grid gap-4">
                  {decisionItems.map((fact) => (
                    <Fact key={fact.label} label={fact.label} value={fact.value} />
                  ))}
                </dl>
              </CardContent>
            </Card>

            <Card className="border-border/80 bg-muted/20 shadow-sm">
              <CardHeader>
                <CardTitle className="text-base">{copy.detail.disclosureTitle}</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-xs leading-5 text-muted-foreground">{buildDisclosure(disclosureDate, filters.locale)}</p>
              </CardContent>
            </Card>
          </div>
        </section>
      </div>
    </main>
  );
}

function MetricTile({ highlight, label, value }: { highlight?: boolean; label: string; value: string }) {
  return (
    <div className={cn("min-h-24 rounded-lg border p-3", highlight ? "border-primary/25 bg-primary/5" : "border-border bg-muted/30")}>
      <dt className="text-xs font-medium text-muted-foreground">{label}</dt>
      <dd className="mt-2 break-words text-2xl font-semibold leading-tight text-foreground tabular-nums">{value}</dd>
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

  return [
    { label: copy.grid.metricDisplayRate, value: formatRate(product.public_display_rate, locale) },
    { label: copy.grid.metricMinBalance, value: formatCurrency(product.minimum_balance, product.currency, locale) },
    { label: copy.grid.metricKeyDetail, value: buildKeyDetail(product, locale) }
  ];
}

function buildDetailFacts(product: PublicProduct, locale: string) {
  const facts: DetailFact[] = [];
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
  return facts;
}

function buildDecisionItems(product: PublicProduct, locale: string) {
  const facts: DetailFact[] = [];
  addFact(facts, detailLabel("bestFor", locale), buildKeyDetail(product, locale), locale);
  addFact(facts, detailLabel("eligibility", locale), product.eligibility_text, locale);
  addFact(facts, detailLabel("applicationMethod", locale), product.application_method, locale);
  addFact(facts, detailLabel("depositInsurance", locale), product.deposit_insurance, locale);
  if (!facts.length) {
    facts.push({ label: detailLabel("bestFor", locale), value: getPublicMessages(locale).common.notDisclosed });
  }
  return facts.slice(0, 4);
}

function buildKeyDetail(product: PublicProduct, locale: string) {
  const copy = getPublicMessages(locale);
  return product.product_highlight_badge_label ?? product.subtype_label ?? product.target_customer_tag_labels[0] ?? copy.common.notDisclosed;
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
        <CardTitle className="text-base">{getPublicMessages(locale).detail.termRates}</CardTitle>
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
    bestFor: "Best fit signal",
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
      bestFor: "적합 신호",
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
      bestFor: "適合シグナル",
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

function formatDate(value: string | null, locale: string) {
  const copy = getPublicMessages(locale);
  if (!value) {
    return copy.common.noDate;
  }
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }
  return new Intl.DateTimeFormat(getIntlLocale(locale), {
    day: "2-digit",
    month: "short",
    year: "numeric"
  }).format(date);
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
    return `제공되는 정보는 ${date}에 은행 홈페이지에 공시된 내용으로 작성되었으며, 금융상품 광고가 아닙니다. 실제 상품 가입 시점에 변동될 수 있으므로 가입 전 반드시 다시 확인하시기 바랍니다. 본 페이지는 대가 관계 없이 정보제공 목적으로 자체 제작한 게시물입니다. 최신 정보 업데이트에 최선을 다하고 있으며, 해당 금융사 홈페이지 등에서 상품 정보와 이용 조건을 확인하고 신청하시기 바랍니다.`;
  }
  if (locale === "ja") {
    return `表示情報は ${date} 時点の銀行ウェブサイト開示内容に基づきます。金融商品の広告ではありません。実際の申込時には条件が変わる可能性があるため、申込前に必ず金融機関の公式ページで商品情報、条件、申込方法を確認してください。`;
  }
  return `Provided information is based on bank website disclosures as of ${date}. It is not a financial product advertisement. Product terms may change by the actual signup time, so confirm again before applying. FPDS prepared this page independently for information only and without compensation. FPDS works to keep information current, but users should verify product details, conditions, and applications on the financial institution website.`;
}
