/** Only the API's explicit comparable full rate can drive rankings or arithmetic.
 * Cached responses from before this contract fail closed until refreshed.
 */
export type PublicRate = {
  kind: 'absolute' | 'range' | 'reference' | 'conditional' | 'promotional' | 'unknown';
  comparable_rate: number | null;
  source_text: string | null;
};

type RateProduct = {
  rate?: PublicRate;
  interest_rate_summary?: string | null;
  purchase_interest_rate_summary?: string | null;
  mortgage_rate?: string | null;
  interest_rate?: string | null;
};

const COPY = {
  en: {
    absolute: 'Interest rate', range: 'Rate range / schedule', reference: 'Reference rate + / − margin',
    conditional: 'Conditional rate / discount', promotional: 'Promotional rate', unknown: 'Rate details',
    unavailable: 'Comparable full rate unavailable', notDisclosed: 'Not disclosed'
  },
  ko: {
    absolute: '금리', range: '금리 범위 / 기간별 금리', reference: '기준금리 + / − 가산·차감',
    conditional: '조건부 금리 / 우대', promotional: '프로모션 금리', unknown: '금리 안내',
    unavailable: '비교 가능한 전체 금리 없음', notDisclosed: '미공개'
  },
  ja: {
    absolute: '金利', range: '金利範囲 / 期間別金利', reference: '基準金利 + / − 上乗せ・差引き',
    conditional: '条件付き金利 / 優遇', promotional: 'キャンペーン金利', unknown: '金利詳細',
    unavailable: '比較可能な全体金利なし', notDisclosed: '非公開'
  }
} as const;

function copyFor(locale: string) {
  return COPY[locale === 'ko' || locale === 'ja' ? locale : 'en'];
}

export function getComparablePublicRate(product: RateProduct): number | null {
  const value = product.rate?.comparable_rate;
  return product.rate?.kind === 'absolute' && typeof value === 'number'
    && Number.isFinite(value) && value >= 0 && value <= 100 ? value : null;
}

export function getPublicRateMetric(product: RateProduct, locale: string) {
  const copy = copyFor(locale);
  const rate = getComparablePublicRate(product);
  const source = product.rate?.source_text || product.purchase_interest_rate_summary
    || product.interest_rate_summary || product.mortgage_rate || product.interest_rate;
  const kind = product.rate?.kind ?? 'unknown';
  return {
    label: copy[kind] ?? copy.unknown,
    value: rate !== null ? `${Number(rate.toFixed(4))}%` : source || copy.notDisclosed
  };
}

export function getRateComparisonUnavailable(locale: string) {
  return copyFor(locale).unavailable;
}
