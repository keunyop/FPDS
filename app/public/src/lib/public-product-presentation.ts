import type { PublicProduct } from "@/lib/public-api";
import { getIntlLocale, getPublicMessages, normalizePublicLocale } from "@/lib/public-locale";

export type PublicProductMetric = {
  label: string;
  value: string;
};

type CardLabelKey = "annualFee" | "back" | "purchaseRate";
type EssentialLabelKey = "creditLimit" | "loanAmount" | "redeemability" | "security" | "transactions";
type LoanLabelKey = "amortization" | "back" | "loanAmount" | "payment" | "prepayment" | "rate" | "rateType" | "term";
type MarketLabelKey = "earlyWithdrawalPenalty" | "feeWaiver";

const CARD_LABELS = {
  en: { annualFee: "Annual fee", back: "Back to credit card list", purchaseRate: "Purchase interest rate" },
  ko: { annualFee: "연회비", back: "신용카드 목록으로", purchaseRate: "구매 금리" },
  ja: { annualFee: "年会費", back: "クレジットカード一覧に戻る", purchaseRate: "ショッピング金利" }
} as const;

const ESSENTIAL_LABELS = {
  en: { creditLimit: "Credit limit", loanAmount: "Loan amount", redeemability: "Redeemability", security: "Security", transactions: "Included transactions" },
  ko: { creditLimit: "신용 한도", loanAmount: "대출 금액", redeemability: "중도해지 가능 여부", security: "담보 여부", transactions: "포함 거래 횟수" },
  ja: { creditLimit: "利用限度額", loanAmount: "借入額", redeemability: "中途解約可否", security: "担保", transactions: "無料取引回数" }
} as const;

const LOAN_LABELS = {
  en: { amortization: "Amortization", back: "Back to loan list", loanAmount: "Loan amount / credit limit", payment: "Payment frequency", prepayment: "Prepayment", rate: "Interest rate", rateType: "Rate type", term: "Term" },
  ko: { amortization: "상환 기간", back: "대출 목록으로", loanAmount: "대출 금액 / 한도", payment: "상환 주기", prepayment: "중도상환", rate: "금리", rateType: "금리 유형", term: "기간" },
  ja: { amortization: "償却期間", back: "ローン一覧に戻る", loanAmount: "借入額 / 利用限度額", payment: "返済頻度", prepayment: "繰上返済", rate: "金利", rateType: "金利タイプ", term: "期間" }
} as const;

const MARKET_LABELS = {
  en: { earlyWithdrawalPenalty: "Early withdrawal penalty", feeWaiver: "Fee waiver / qualifying activity" },
  ko: { earlyWithdrawalPenalty: "중도 인출 위약금", feeWaiver: "수수료 면제 조건" },
  ja: { earlyWithdrawalPenalty: "中途解約ペナルティ", feeWaiver: "手数料免除条件" }
} as const;

export function buildPublicProductMetrics(
  product: PublicProduct,
  locale: string,
  presentation: "card" | "comparison" = "comparison"
): PublicProductMetric[] {
  const copy = getPublicMessages(locale);
  const productRate = presentation === "card"
    ? formatPublicRate(product.card_display_rate, locale)
    : formatPublicProductRate(product, locale);

  if (product.product_type === "chequing") {
    return [
      { label: copy.grid.metricMonthlyFee, value: formatPublicCurrency(product.public_display_fee, product.currency, locale) },
      { label: copy.grid.metricMinBalance, value: formatPublicCurrency(product.minimum_balance ?? product.minimum_deposit, product.currency, locale) },
      product.country_code === "US"
        ? { label: getMarketLabel("feeWaiver", locale), value: product.fee_waiver_condition ?? copy.common.notDisclosed }
        : { label: getEssentialLabel("transactions", locale), value: formatPublicTransactions(product, locale) }
    ];
  }

  if (product.product_type === "gic") {
    return [
      { label: copy.grid.metricDisplayRate, value: productRate },
      { label: copy.grid.metricTerm, value: formatPublicProductTerm(product, locale) },
      { label: copy.grid.metricMinDeposit, value: formatPublicCurrency(product.minimum_deposit, product.currency, locale) },
      product.country_code === "US"
        ? { label: getMarketLabel("earlyWithdrawalPenalty", locale), value: product.early_withdrawal_penalty ?? copy.common.notDisclosed }
        : { label: getEssentialLabel("redeemability", locale), value: formatPublicRedeemability(product, locale) }
    ];
  }

  if (product.product_type === "credit-card") {
    return [
      { label: getCardLabel("annualFee", locale), value: formatPublicCurrency(product.annual_fee, product.currency, locale) },
      {
        label: getCardLabel("purchaseRate", locale),
        value: presentation === "card"
          ? formatPublicRate(product.card_display_rate, locale)
          : formatPublicPurchaseRate(product, locale)
      }
    ];
  }

  if (product.product_type === "mortgage") {
    return [
      { label: copy.grid.metricDisplayRate, value: productRate },
      { label: getLoanLabel("rateType", locale), value: product.rate_type ?? copy.common.notDisclosed },
      { label: getLoanLabel("term", locale), value: formatPublicProductTerm(product, locale) }
    ];
  }

  if (product.product_type === "personal-loan") {
    return [
      { label: copy.grid.metricDisplayRate, value: productRate },
      { label: getEssentialLabel("loanAmount", locale), value: product.loan_amount_text ?? copy.common.notDisclosed },
      { label: getLoanLabel("term", locale), value: formatPublicProductTerm(product, locale) }
    ];
  }

  if (product.product_type === "line-of-credit") {
    return [
      { label: copy.grid.metricDisplayRate, value: productRate },
      { label: getEssentialLabel("creditLimit", locale), value: product.credit_limit_text ?? copy.common.notDisclosed },
      { label: getEssentialLabel("security", locale), value: formatPublicSecurity(product, locale) }
    ];
  }

  return [
    { label: copy.grid.metricDisplayRate, value: productRate },
    { label: copy.grid.metricMonthlyFee, value: formatPublicCurrency(product.public_display_fee, product.currency, locale) },
    { label: copy.grid.metricMinBalance, value: formatPublicCurrency(product.minimum_balance, product.currency, locale) }
  ];
}

export function buildPublicSortMetric(product: PublicProduct, locale: string, sortBy: string): PublicProductMetric {
  const copy = getPublicMessages(locale);

  switch (sortBy) {
    case "annual_fee":
      return { label: getCardLabel("annualFee", locale), value: formatPublicCurrency(product.annual_fee, product.currency, locale) };
    case "monthly_fee":
      return { label: copy.grid.metricMonthlyFee, value: formatPublicCurrency(product.public_display_fee, product.currency, locale) };
    case "minimum_balance":
      return { label: copy.grid.metricMinBalance, value: formatPublicCurrency(product.minimum_balance, product.currency, locale) };
    case "minimum_deposit":
      return { label: copy.grid.metricMinDeposit, value: formatPublicCurrency(product.minimum_deposit, product.currency, locale) };
    case "bank_name":
      return { label: copy.grid.sortBankName, value: product.bank_name };
    case "product_name":
      return { label: copy.grid.sortProductName, value: product.product_name };
    case "last_changed_at":
      return { label: copy.grid.metricLastChange, value: product.last_changed_at?.slice(0, 10) ?? copy.common.notDisclosed };
    default:
      return { label: copy.grid.metricDisplayRate, value: formatPublicRate(product.card_display_rate, locale) };
  }
}

export function formatPublicCurrency(value: number | null, currency: string, locale: string) {
  if (value === null || !Number.isFinite(value)) {
    return getPublicMessages(locale).common.notDisclosed;
  }
  return new Intl.NumberFormat(getIntlLocale(locale), {
    style: "currency",
    currency: normalizeCurrency(currency),
    maximumFractionDigits: Number.isInteger(value) ? 0 : 2
  }).format(value);
}

export function formatPublicProductRate(product: PublicProduct, locale: string) {
  if (product.public_display_rate !== null) {
    return formatPublicRate(product.public_display_rate, locale);
  }
  if (product.country_code === "US" && product.product_type === "mortgage" && product.interest_rate_summary) {
    return product.interest_rate_summary;
  }
  return product.mortgage_rate
    ?? product.interest_rate
    ?? product.interest_rate_summary
    ?? getPublicMessages(locale).common.notDisclosed;
}

export function formatPublicProductTerm(product: PublicProduct, locale: string) {
  if (product.term_length_text) {
    return product.term_length_text;
  }
  if (product.term_length_days !== null) {
    return formatPublicTerm(product.term_length_days, locale);
  }
  const firstRow = product.term_rate_table[0];
  if (product.term_rate_table.length === 1 && firstRow) {
    return firstRow.term_label ?? formatPublicTerm(firstRow.term_length_days, locale);
  }
  if (product.term_rate_table.length > 1) {
    return locale === "ko"
      ? `${product.term_rate_table.length}개 기간`
      : locale === "ja"
        ? `${product.term_rate_table.length}期間`
        : `${product.term_rate_table.length} terms`;
  }
  return getPublicMessages(locale).common.notDisclosed;
}

export function formatPublicPurchaseRate(product: PublicProduct, locale: string) {
  return product.purchase_interest_rate_summary ?? formatPublicRate(product.purchase_interest_rate, locale);
}

export function formatPublicRate(value: number | null, locale: string) {
  if (value === null || !Number.isFinite(value)) {
    return getPublicMessages(locale).common.notDisclosed;
  }
  return `${value.toFixed(2).replace(/\.?0+$/, "")}%`;
}

export function formatPublicRedeemability(product: PublicProduct, locale: string) {
  const redeemable = product.redeemable_flag
    ?? (product.non_redeemable_flag === null ? null : !product.non_redeemable_flag);
  if (redeemable === null) {
    return getPublicMessages(locale).common.notDisclosed;
  }
  if (redeemable) {
    return locale === "ko" ? "중도해지 가능" : locale === "ja" ? "中途解約可能" : "Redeemable";
  }
  return locale === "ko" ? "중도해지 불가" : locale === "ja" ? "中途解約不可" : "Non-redeemable";
}

export function formatPublicSecurity(product: PublicProduct, locale: string) {
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

export function formatPublicTransactions(product: PublicProduct, locale: string) {
  if (product.unlimited_transactions_flag === true) {
    return locale === "ko" ? "무제한" : locale === "ja" ? "無制限" : "Unlimited";
  }
  if (product.included_transactions !== null) {
    const count = new Intl.NumberFormat(getIntlLocale(locale)).format(product.included_transactions);
    return locale === "ko" ? `월 ${count}회` : locale === "ja" ? `月${count}回` : `${count} / month`;
  }
  return getPublicMessages(locale).common.notDisclosed;
}

export function getCardLabel(key: CardLabelKey, locale: string) {
  return CARD_LABELS[normalizePublicLocale(locale)][key];
}

export function getEssentialLabel(key: EssentialLabelKey, locale: string) {
  return ESSENTIAL_LABELS[normalizePublicLocale(locale)][key];
}

export function getLoanLabel(key: LoanLabelKey, locale: string) {
  return LOAN_LABELS[normalizePublicLocale(locale)][key];
}

export function getMarketLabel(key: MarketLabelKey, locale: string) {
  return MARKET_LABELS[normalizePublicLocale(locale)][key];
}

export function formatPublicTerm(termLengthDays: number | null, locale: string) {
  if (termLengthDays === null || !Number.isFinite(termLengthDays)) {
    return getPublicMessages(locale).common.notDisclosed;
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

function normalizeCurrency(currency: string) {
  const normalized = currency.trim().toUpperCase();
  return /^[A-Z]{3}$/.test(normalized) ? normalized : "CAD";
}
