import type { PublicProduct } from './public-api.ts';

const COPY = {
  en: {
    deposits: 'No published savings accounts or GICs/CDs yet.',
    loans: 'No published loans yet.',
    currency: 'No comparable products in this market’s currency.',
    basis: 'Published savings accounts or GICs/CDs need a verified annual rate or APY basis before ranking.',
    depositsUnclear: 'Published deposits do not yet have comparable rates, terms and withdrawal conditions.',
    loansUnclear: 'Published loans do not yet have a comparable full rate.'
  },
  ko: {
    deposits: '아직 공개된 저축예금·GIC/CD 상품이 없습니다.',
    loans: '아직 공개된 대출 상품이 없습니다.',
    currency: '해당 국가의 기준 통화로 비교할 수 있는 상품이 없습니다.',
    basis: '공개된 저축예금·GIC/CD의 연 금리 또는 APY 기준이 확인되어야 순위를 표시할 수 있습니다.',
    depositsUnclear: '공개된 예금의 금리·기간·중도해지 조건을 아직 동일한 기준으로 비교할 수 없습니다.',
    loansUnclear: '공개된 대출에 순위 비교가 가능한 단일 금리가 없습니다.'
  },
  ja: {
    deposits: '公開済みの普通預金・GIC/CDはまだありません。',
    loans: '公開済みのローンはまだありません。',
    currency: 'この国の基準通貨で比較できる商品がありません。',
    basis: '公開済みの普通預金・GIC/CDの年利またはAPYの基準を確認後、順位を表示できます。',
    depositsUnclear: '公開済み預金の金利・期間・中途解約条件を同じ基準で比較できません。',
    loansUnclear: '公開済みローンに順位比較できる単一の金利がありません。'
  }
} as const;

/** Used only after the complete snapshot loaded successfully and no group exists. */
export function rankingEmptyMessage(products: PublicProduct[], family: 'deposit' | 'loan', country: string, locale: string) {
  const copy = COPY[locale === 'ko' || locale === 'ja' ? locale : 'en'];
  const types = family === 'deposit' ? ['savings', 'gic'] : ['mortgage', 'personal-loan', 'line-of-credit'];
  const candidates = products.filter(p => p.country_code === country && types.includes(p.product_type));
  if (!candidates.length) return family === 'deposit' ? copy.deposits : copy.loans;
  const currency = ({ CA: 'CAD', US: 'USD' } as Record<string, string>)[country];
  const domestic = candidates.filter(p => p.currency === currency);
  if (!domestic.length) return copy.currency;
  if (family === 'loan') return copy.loansUnclear;
  if (domestic.every(p => p.deposit_terms?.reason === 'basis_unknown'
      || p.deposit_terms?.basis === 'unknown' || !p.deposit_terms)) return copy.basis;
  // No inferred basis or maturity. Existing qualified rates remain excluded.
  return copy.depositsUnclear;
}
