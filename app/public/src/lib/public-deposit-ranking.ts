import type { PublicProduct } from './public-api.ts';
import { depositCopy, depositGroupKey, depositOptions, depositPeriod } from './public-deposit.ts';

const HOME_CURRENCIES: Record<string, string> = { CA: 'CAD', US: 'USD' };
const CONDITIONS = {
  en: { all: 'All', noMonthlyFee: 'No monthly fee', noMinimumBalance: 'No minimum balance' },
  ko: { all: '전체', noMonthlyFee: '월 수수료 없음', noMinimumBalance: '최소 잔액 없음' },
  ja: { all: 'すべて', noMonthlyFee: '月額手数料なし', noMinimumBalance: '最低残高なし' }
} as const;

type DepositRankingGroup = {
  key: string;
  label: string;
  currency: string;
  basis: string;
  items: PublicProduct[];
  rates: Record<string, number>;
};

/** Home-only presets. Never widen a comparison to fill five places. */
export function depositRankingGroups(products: PublicProduct[], country: string, locale: string): DepositRankingGroup[] {
  const currency = HOME_CURRENCIES[country];
  if (!currency) return [];
  const copy = CONDITIONS[locale === 'ko' || locale === 'ja' ? locale : 'en'];
  const labels = depositCopy(locale);
  const groups = new Map<string, DepositRankingGroup>();
  for (const product of products) {
    if (product.country_code !== country || product.currency !== currency
      || !['savings', 'gic'].includes(product.product_type)) continue;
    const terms = product.deposit_terms;
    if (product.product_type === 'gic' && !['redeemable', 'non_redeemable'].includes(terms?.withdrawal ?? '')) continue;
    for (const option of depositOptions(product)) {
      const conditions: Array<{ key: string; label: string }> = [{ key: '0-all', label: copy.all }];
      if (product.product_type === 'savings') {
        // A conditional fee waiver is not an unconditional zero monthly fee.
        if (product.public_display_fee === 0 && !product.fee_waiver_condition?.trim())
          conditions.push({ key: '1-no-monthly-fee', label: copy.noMonthlyFee });
        if (product.minimum_balance === 0)
          conditions.push({ key: '2-no-minimum-balance', label: copy.noMinimumBalance });
      }
      for (const condition of conditions) {
        const key = `${country}|${depositGroupKey(product, option)}|${condition.key}`;
        const label = product.product_type === 'gic'
          ? `${product.product_type_label} · ${depositPeriod(option, locale)} · ${labels[terms!.withdrawal]}`
          : `${product.product_type_label} · ${condition.label}`;
        const group = groups.get(key) ?? {
          key, label, currency, basis: terms!.basis === 'apy' ? labels.apy : labels.annual, items: [], rates: {}
        };
        if (!group.items.some(item => item.product_id === product.product_id)) group.items.push(product);
        group.rates[product.product_id] = option.rate;
        groups.set(key, group);
      }
    }
  }
  const ordered = [...groups.values()].sort((a, b) => {
    const savingsFirst = (group: DepositRankingGroup) => group.items[0].product_type === 'savings' ? 0 : 1;
    return savingsFirst(a) - savingsFirst(b) || a.key.localeCompare(b.key, 'en', { numeric: true });
  });
  return ordered.map(group => ({
    ...group,
    label: ordered.some(other => other !== group && other.label === group.label && other.basis !== group.basis)
      ? `${group.label} · ${group.basis}` : group.label,
    items: [...group.items].sort((a, b) => group.rates[b.product_id] - group.rates[a.product_id]
      || a.product_id.localeCompare(b.product_id)).slice(0, 5)
  }));
}
