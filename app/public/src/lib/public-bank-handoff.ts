import type { PublicProduct } from './public-api.ts';

const COPY = {
  en: { title: 'Before you visit the bank', action: 'Check latest terms at bank', external: 'External site · new tab', bank: 'Check with the bank', unavailable: 'Official link unavailable', currency: 'Currency', domain: 'Official domain', minimumDeposit: 'Minimum deposit', minimumBalance: 'Minimum balance', minimum: 'Minimum amount', waiver: 'Fee waiver', withdrawal: 'Withdrawal restrictions', penalty: 'Early withdrawal penalty', redeemable: 'Redeemable', nonRedeemable: 'Non-redeemable', term: 'Term', days: 'days', monthlyFee: 'Monthly fee', annualFee: 'Annual fee' },
  ko: { title: '은행 방문 전 확인', action: '은행에서 최신 조건 확인', external: '외부 사이트 · 새 탭', bank: '은행에서 확인', unavailable: '공식 링크 미확인', currency: '통화', domain: '공식 도메인', minimumDeposit: '최소 예치금', minimumBalance: '최소 잔액', minimum: '최소 금액', waiver: '수수료 면제 조건', withdrawal: '인출 제한', penalty: '중도 인출 위약금', redeemable: '중도해지 가능', nonRedeemable: '중도해지 불가', term: '만기', days: '일', monthlyFee: '월 수수료', annualFee: '연회비' },
  ja: { title: '銀行へ進む前に確認', action: '銀行で最新条件を確認', external: '外部サイト・新しいタブ', bank: '銀行で確認', unavailable: '公式リンク未確認', currency: '通貨', domain: '公式ドメイン', minimumDeposit: '最低預入額', minimumBalance: '最低残高', minimum: '最低金額', waiver: '手数料免除条件', withdrawal: '引出制限', penalty: '中途解約ペナルティ', redeemable: '中途解約可', nonRedeemable: '中途解約不可', term: '期間', days: '日', monthlyFee: '月額手数料', annualFee: '年会費' }
} as const;
export function bankHandoffCopy(locale: string) { return COPY[locale === 'ko' || locale === 'ja' ? locale : 'en']; }

/** Only approved Public destinations enter this helper; syntax is not bank verification. */
export function officialDestination(value: string | null | undefined) {
  if (!value || value.trim() !== value || /[\\\s]/.test(value)) return null;
  try {
    const url = new URL(value);
    if (url.protocol !== 'https:' || url.username || url.password || url.port
      || !url.hostname.includes('.') || url.hostname.endsWith('.')
      || /^(?:\d+\.)+\d+$/.test(url.hostname) || url.hostname.includes(':')
      || /(?:^|\.)(?:localhost|local|internal|test|invalid)$/.test(url.hostname)) return null;
    return { href: url.href, domain: url.hostname };
  } catch { return null; }
}

export type HandoffFact = { key: string; label: string; value: string };
function amount(value: number | null | undefined, currency: string, locale: string) {
  if (typeof value !== 'number' || !Number.isFinite(value) || value < 0 || !/^[A-Z]{3}$/.test(currency)) return null;
  return currency + ' ' + new Intl.NumberFormat(locale === 'ko' ? 'ko-KR' : locale === 'ja' ? 'ja-JP' : 'en-CA',
    { maximumFractionDigits: 2 }).format(value);
}
export function handoffConditions(product: PublicProduct, locale: string): HandoffFact[] {
  const copy = bankHandoffCopy(locale);
  const facts: HandoffFact[] = [];
  const add = (key: string, label: string, value: string | null | undefined) =>
    facts.push({ key, label, value: value?.trim() || copy.bank });
  const deposit = ['chequing', 'savings', 'gic'].includes(product.product_type);
  if (deposit) {
    const minimumDeposit = amount(product.minimum_deposit, product.currency, locale);
    const minimumBalance = amount(product.minimum_balance, product.currency, locale);
    if (minimumDeposit) add('deposit', copy.minimumDeposit, minimumDeposit);
    if (minimumBalance) add('balance', copy.minimumBalance, minimumBalance);
    if (product.product_type === 'gic') {
      const rows = (product.term_rate_table ?? []).flatMap(row => {
        const value = amount(row.minimum_deposit, product.currency, locale);
        const term = row.term_label?.trim() || (row.term_length_days ? row.term_length_days + ' ' + copy.days : null);
        return value && term ? [term + ': ' + value] : [];
      });
      const distinctMinimums = new Set((product.term_rate_table ?? []).map(row => amount(row.minimum_deposit, product.currency, locale)).filter(Boolean));
      if (!minimumDeposit || [...distinctMinimums].some(value => value !== minimumDeposit))
        add('termMinimum', copy.minimumDeposit + ' · ' + copy.term, rows.length ? rows.join('; ') : null);
    } else if (!minimumDeposit && !minimumBalance) add('minimum', copy.minimum, null);
  } else {
    add('minimum', copy.minimum, null);
  }
  add('waiver', copy.waiver, product.fee_waiver_condition);
  // A transaction allowance is not a withdrawal rule. Conflicting flags stay unknown.
  const yes = product.redeemable_flag;
  const no = product.non_redeemable_flag;
  let withdrawal: string | null = null;
  if (product.product_type === 'gic' && !(typeof yes === 'boolean' && yes === no)) {
    if (yes === true || no === false) withdrawal = copy.redeemable;
    else if (yes === false || no === true) withdrawal = copy.nonRedeemable;
  }
  add('withdrawal', copy.withdrawal, withdrawal);
  if (product.early_withdrawal_penalty?.trim()) add('penalty', copy.penalty, product.early_withdrawal_penalty);
  return facts;
}
export function handoffCost(product: PublicProduct, locale: string): HandoffFact | null {
  const copy = bankHandoffCopy(locale);
  if (product.product_type === 'credit-card') return { key: 'cost', label: copy.annualFee, value: amount(product.annual_fee, product.currency, locale) ?? copy.bank };
  if (['chequing', 'savings'].includes(product.product_type)) return { key: 'cost', label: copy.monthlyFee, value: amount(product.public_display_fee, product.currency, locale) ?? copy.bank };
  return null;
}
