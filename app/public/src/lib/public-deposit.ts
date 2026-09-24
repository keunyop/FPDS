import type { PublicProduct, PublicProductsResponse } from './public-api.ts';

export type DepositOption = { key: string; months: number | null; days: number | null; rate: number; minimum_deposit: number | null };
export type DepositTerms = {
  version: 1; basis: 'annual' | 'apy' | 'unknown'; reason: string | null;
  calculation_reason: string | null; withdrawal: 'redeemable' | 'non_redeemable' | 'unknown'; options: DepositOption[];
};

export function depositOptions(product: Pick<PublicProduct, 'deposit_terms'>): DepositOption[] {
  const terms = product.deposit_terms;
  if (terms?.version !== 1 || terms.reason || !['annual', 'apy'].includes(terms.basis)) return [];
  return terms.options.filter(option => Number.isFinite(option.rate) && option.rate >= 0 && option.rate <= 100
    && (option.key === 'ongoing' || (option.months !== null && option.months > 0) || (option.days !== null && option.days > 0)));
}

export function sameComparisonScope(current: PublicProduct, candidate: PublicProduct, key: string) {
  if (current.country_code !== candidate.country_code || current.product_type !== candidate.product_type
    || !/^[A-Z]{3}$/.test(current.currency) || current.currency !== candidate.currency) return false;
  if (!['savings', 'gic'].includes(current.product_type)) return true;
  if (current.deposit_terms?.basis !== candidate.deposit_terms?.basis) return false;
  if (current.product_type === 'gic' && (current.deposit_terms?.withdrawal === 'unknown'
    || current.deposit_terms?.withdrawal !== candidate.deposit_terms?.withdrawal)) return false;
  return depositOptions(current).some(option => option.key === key)
    && depositOptions(candidate).some(option => option.key === key);
}

export function depositRate(product: PublicProduct, key: string) {
  return depositOptions(product).find(option => option.key === key)?.rate ?? null;
}

export function startingDepositAmount(minimumBalance: number | null, minimumDeposit: number | null) {
  return Math.max(10000, ...[minimumBalance, minimumDeposit].filter((value): value is number => typeof value === 'number' && Number.isFinite(value) && value >= 0));
}

export function estimateDeposit(product: PublicProduct, option: DepositOption | undefined, input: string, days: number) {
  if (product.deposit_terms?.version !== 1 || product.deposit_terms.reason || product.deposit_terms.calculation_reason
    || product.deposit_terms.basis !== 'annual' || !option || !depositOptions(product).some(item => item.key === option.key && item.rate === option.rate)) return null;
  if (!/^\d+(?:\.\d{1,2})?$/.test(input.trim())) return null;
  const amount = Number(input);
  const minimum = Math.max(product.minimum_balance ?? 0, product.minimum_deposit ?? 0, option.minimum_deposit ?? 0);
  if (!Number.isFinite(amount) || amount < minimum || amount > 1e12 || !Number.isInteger(days) || days < 1 || days > 365) return null;
  const years = product.product_type === 'gic' ? option.months !== null ? option.months / 12 : (option.days ?? 0) / 365 : days / 365;
  if (years <= 0) return null;
  const interest = amount * (option.rate / 100) * years;
  return Number.isFinite(interest) ? Math.round((interest + Number.EPSILON) * 100) / 100 : null;
}

export function depositPeriod(option: DepositOption, locale: string) {
  const copy = depositCopy(locale);
  return option.key === 'ongoing' ? copy.ongoing : option.months !== null
    ? `${option.months} ${copy.months}` : `${option.days} ${copy.days}`;
}

export function depositGroupKey(product: PublicProduct, option: DepositOption) {
  return [product.product_type, product.currency, product.deposit_terms?.basis, option.key,
    product.product_type === 'gic' ? product.deposit_terms?.withdrawal : ''].join('|');
}

const COPY = {
 en: { scope: 'Comparison conditions', term: 'Term', currency: 'Currency', annual: 'Annual rate', apy: 'APY', ongoing: 'Current rate', months: 'months', days: 'days', redeemable: 'Redeemable', non_redeemable: 'Non-redeemable', unknown: 'Withdrawal terms unknown', unavailable: 'Estimate unavailable', bank: 'Check with the bank', amount: 'Deposit amount', period: 'Estimate period', title: 'Estimate interest', interest: 'Estimated interest', note: 'Simple interest at an unchanged rate; excludes compounding, fees and tax.', inputError: 'Enter an amount within the published minimum and 1 trillion, with up to 2 decimals.', empty: 'No comparable rates for these conditions.', noMatch: 'No higher rate with the same conditions.', reasons: {
  market_linked: 'Returns depend on market performance.', promotional: 'Promotional rate or duration needs verification.', tiered: 'Balance tiers or bonus conditions need verification.', currency_unknown: 'Currency needs verification.', basis_unknown: 'Annual rate basis needs verification.', term_unknown: 'A rate for this term is unavailable.', term_conflict: 'Published terms or rates conflict.', rate_unclear: 'A single applicable rate is unavailable.', variable: 'The GIC rate can change.', conditions_unclear: 'Rate conditions need verification.', apy: 'APY requires a compound-interest calculation.', compound: 'Compounding terms need a separate calculation.' } },
 ko: { scope: '비교 조건', term: '만기', currency: '통화', annual: '연 금리', apy: 'APY', ongoing: '현재 금리', months: '개월', days: '일', redeemable: '중도해지 가능', non_redeemable: '중도해지 불가', unknown: '중도해지 조건 미확인', unavailable: '계산 불가', bank: '은행에서 확인', amount: '예금 금액', period: '계산 기간', title: '예상 이자 계산', interest: '예상 이자', note: '금리가 유지된다는 가정의 단리 추정입니다. 복리·수수료·세금은 제외합니다.', inputError: '공개된 최소 금액 이상, 1조 이하로 입력하세요. 소수 둘째 자리까지 가능합니다.', empty: '이 조건으로 비교할 수 있는 금리가 없습니다.', noMatch: '같은 조건의 더 높은 금리가 없습니다.', reasons: {
  market_linked: '시장 성과에 따라 수익이 달라집니다.', promotional: '프로모션 금리·적용 기간 확인이 필요합니다.', tiered: '잔액 구간·우대 조건 확인이 필요합니다.', currency_unknown: '통화 확인이 필요합니다.', basis_unknown: '연 금리 기준 확인이 필요합니다.', term_unknown: '해당 만기의 금리가 없습니다.', term_conflict: '공개된 만기 또는 금리가 서로 다릅니다.', rate_unclear: '적용 금리를 확정할 수 없습니다.', variable: 'GIC 금리가 변동될 수 있습니다.', conditions_unclear: '금리 적용 조건 확인이 필요합니다.', apy: 'APY는 복리 계산이 필요합니다.', compound: '복리 조건에 맞는 별도 계산이 필요합니다.' } },
 ja: { scope: '比較条件', term: '期間', currency: '通貨', annual: '年利', apy: 'APY', ongoing: '現在の金利', months: 'か月', days: '日', redeemable: '中途解約可', non_redeemable: '中途解約不可', unknown: '中途解約条件未確認', unavailable: '計算不可', bank: '銀行で確認', amount: '預入金額', period: '計算期間', title: '利息を概算', interest: '予想利息', note: '金利が変わらないと仮定した単利概算です。複利・手数料・税金は含みません。', inputError: '公開された最低金額以上、1兆以下で入力してください。小数は2桁までです。', empty: 'この条件で比較できる金利はありません。', noMatch: '同じ条件でより高い金利はありません。', reasons: {
  market_linked: '収益は市場の動向で変わります。', promotional: 'キャンペーン金利・適用期間の確認が必要です。', tiered: '残高区分・優遇条件の確認が必要です。', currency_unknown: '通貨の確認が必要です。', basis_unknown: '年利の基準の確認が必要です。', term_unknown: 'この期間の金利がありません。', term_conflict: '公開された期間または金利が一致しません。', rate_unclear: '適用金利を確定できません。', variable: 'GICの金利は変動する可能性があります。', conditions_unclear: '金利の適用条件の確認が必要です。', apy: 'APYには複利計算が必要です。', compound: '複利条件に合わせた別の計算が必要です。' } }
} as const;
export function depositCopy(locale: string) { return COPY[locale === 'ko' || locale === 'ja' ? locale : 'en']; }
export function depositReason(reason: string | null | undefined, locale: string) {
 const reasons = depositCopy(locale).reasons;
 return reasons[reason as keyof typeof reasons] ?? reasons.basis_unknown;
}

/** Do not claim a complete ranking from one page, or mix changing snapshots. */
export async function allProductPages(fetchPage: (page: number) => Promise<PublicProductsResponse>) {
  const first = await fetchPage(1);
  const items = [...first.items];
  let response = first;
  while (response.has_next_page) {
    const page = response.page + 1;
    if (page > 100) throw new Error('Product scope exceeds supported pagination');
    response = await fetchPage(page);
    if (response.page !== page || response.freshness.snapshot_id !== first.freshness.snapshot_id || !response.items.length)
      throw new Error('Public snapshot changed; retry');
    items.push(...response.items);
  }
  return { ...first, items: [...new Map(items.map(product => [product.product_id, product])).values()], has_next_page: false };
}
