import type { ProductTypeCollectionFields } from "./admin-api";

export type CollectionFieldConfiguration = ProductTypeCollectionFields;

export type CollectionFieldSelection = Pick<CollectionFieldConfiguration, "required_fields" | "optional_fields">;
export type CollectionFieldMode = "required" | "optional" | "omit";
export const MAX_COLLECTION_FIELD_TARGETS = 60;

export function collectionFieldSelectionError(selection: CollectionFieldSelection): "too_many_fields" | null {
  return selection.required_fields.length + selection.optional_fields.length > MAX_COLLECTION_FIELD_TARGETS ? "too_many_fields" : null;
}

export function canChangeCollectionFieldSelection(previous: CollectionFieldSelection, next: CollectionFieldSelection): boolean {
  return !collectionFieldSelectionError(next) ||
    next.required_fields.length + next.optional_fields.length < previous.required_fields.length + previous.optional_fields.length;
}

export function collectionFieldSelection(configuration: CollectionFieldConfiguration): CollectionFieldSelection {
  return {
    required_fields: [...configuration.required_fields],
    optional_fields: [...configuration.optional_fields],
  };
}

export function collectionFieldMode(selection: CollectionFieldSelection, fieldKey: string): CollectionFieldMode {
  if (selection.required_fields.includes(fieldKey)) return "required";
  return selection.optional_fields.includes(fieldKey) ? "optional" : "omit";
}

export function changeCollectionField(
  configuration: CollectionFieldConfiguration,
  selection: CollectionFieldSelection,
  fieldKey: string,
  mode: CollectionFieldMode,
): CollectionFieldSelection {
  if (configuration.locked_required_fields.includes(fieldKey) ||
      !configuration.field_catalog.some(field => field.field_key === fieldKey)) return selection;
  const next = {
    required_fields: selection.required_fields.filter(key => key !== fieldKey),
    optional_fields: selection.optional_fields.filter(key => key !== fieldKey),
  };
  if (mode === "required") next.required_fields.push(fieldKey);
  if (mode === "optional") next.optional_fields.push(fieldKey);
  return next;
}

export function sameCollectionFieldSelection(a: CollectionFieldSelection, b: CollectionFieldSelection): boolean {
  return (["required_fields", "optional_fields"] as const).every(key =>
    [...a[key]].sort().join("\n") === [...b[key]].sort().join("\n"));
}

const FIELD_LABELS: Record<string, [string, string, string]> = {
  "product_name": [
    "Product name",
    "상품명",
    "商品名"
  ],
  "product_type": [
    "Product type",
    "상품 유형",
    "商品タイプ"
  ],
  "product_url": [
    "Product URL",
    "상품 URL",
    "商品 URL"
  ],
  "currency": [
    "Currency",
    "통화",
    "通貨"
  ],
  "standard_rate": [
    "Standard annual rate",
    "기본 연이율",
    "通常年利"
  ],
  "display_rate": [
    "Display rate",
    "표시 금리",
    "表示金利"
  ],
  "monthly_fee": [
    "Monthly fee",
    "월 수수료",
    "月額手数料"
  ],
  "annual_fee": [
    "Annual fee",
    "연회비",
    "年会費"
  ],
  "purchase_rate": [
    "Purchase interest rate",
    "구매 이자율",
    "ショッピング金利"
  ],
  "cash_advance_rate": [
    "Cash advance rate",
    "현금서비스 금리",
    "キャッシング金利"
  ],
  "balance_transfer_rate": [
    "Balance transfer rate",
    "잔액 이체 금리",
    "残高移行金利"
  ],
  "transaction_fee": [
    "Transaction fee",
    "거래 수수료",
    "取引手数料"
  ],
  "additional_transaction_fee": [
    "Excess transaction fee",
    "초과 거래 수수료",
    "超過取引手数料"
  ],
  "transactions_included": [
    "Included transactions",
    "포함 거래 횟수",
    "無料取引回数"
  ],
  "transaction_limit": [
    "Transaction limit",
    "거래 한도",
    "取引上限"
  ],
  "unlimited_transactions_flag": [
    "Unlimited transactions",
    "무제한 거래 여부",
    "取引回数無制限"
  ],
  "minimum_balance": [
    "Minimum balance",
    "최소 잔액",
    "最低残高"
  ],
  "minimum_deposit": [
    "Minimum deposit",
    "최소 예치금",
    "最低預入額"
  ],
  "fee_waiver_condition": [
    "Fee waiver conditions",
    "수수료 면제 조건",
    "手数料免除条件"
  ],
  "term_months": [
    "Term in months",
    "기간 (개월)",
    "期間（月）"
  ],
  "term_min_months": [
    "Minimum term in months",
    "최소 기간 (개월)",
    "最短期間（月）"
  ],
  "term_max_months": [
    "Maximum term in months",
    "최대 기간 (개월)",
    "最長期間（月）"
  ],
  "term_description": [
    "Term conditions",
    "기간 조건",
    "期間条件"
  ],
  "term_rate_schedule": [
    "Term and rate schedule",
    "기간별 금리",
    "期間別金利"
  ],
  "redeemable_flag": [
    "Early withdrawal allowed",
    "중도 인출 허용 여부",
    "中途解約可否"
  ],
  "non_redeemable_flag": [
    "Early withdrawal prohibited",
    "중도 인출 불가 여부",
    "中途解約不可"
  ],
  "early_withdrawal_penalty": [
    "Early withdrawal consequences",
    "중도 인출 시 불이익",
    "中途解約の条件・負担"
  ],
  "secured_flag": [
    "Secured lending",
    "담보 대출 여부",
    "担保の有無"
  ],
  "security_requirement": [
    "Security requirements",
    "담보 요건",
    "担保要件"
  ],
  "collateral_requirement": [
    "Collateral requirements",
    "담보물 요건",
    "担保物要件"
  ],
  "rate_type": [
    "Rate type",
    "금리 유형",
    "金利タイプ"
  ],
  "rate_min": [
    "Minimum rate",
    "최저 금리",
    "最低金利"
  ],
  "rate_max": [
    "Maximum rate",
    "최고 금리",
    "最高金利"
  ],
  "description_short": [
    "Description",
    "설명",
    "説明"
  ],
  "eligibility_text": [
    "Eligibility",
    "가입 요건",
    "申込条件"
  ],
  "notes": [
    "Notes",
    "추가 조건",
    "補足条件"
  ],
  "application_url": [
    "Application URL",
    "신청 URL",
    "申込 URL"
  ],
  "rewards_text": [
    "Rewards",
    "혜택",
    "特典"
  ],
  "interest_calculation": [
    "Interest calculation",
    "이자 계산 방식",
    "利息計算方法"
  ],
  "interest_payment_frequency": [
    "Interest payment frequency",
    "이자 지급 주기",
    "利払頻度"
  ],
  "promotional_rate": [
    "Promotional rate",
    "우대 금리",
    "優遇金利"
  ],
  "promotional_period": [
    "Promotional period",
    "우대 기간",
    "優遇期間"
  ],
  "maximum_amount": [
    "Maximum amount",
    "최대 금액",
    "上限金額"
  ],
  "minimum_amount": [
    "Minimum amount",
    "최소 금액",
    "最低金額"
  ],
  "credit_limit": [
    "Credit limit",
    "신용 한도",
    "利用限度額"
  ]
};

export function collectionFieldLabel(fieldKey: string, locale: "en" | "ko" | "ja"): string {
  const known = FIELD_LABELS[fieldKey];
  if (known) return known[locale === "ko" ? 1 : locale === "ja" ? 2 : 0];
  return fieldKey.split("_").filter(Boolean).map(word => word.charAt(0).toUpperCase() + word.slice(1)).join(" ");
}
