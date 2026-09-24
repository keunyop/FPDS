import type { PublicProduct } from './public-api.ts';
import { getComparablePublicRate } from './public-rate.ts';

const HOME_CURRENCIES: Record<string, string> = { CA: 'CAD', US: 'USD' };
const TYPES = ['mortgage', 'personal-loan', 'line-of-credit'];
const COPY = {
  en: { scope: 'Comparison conditions', all: 'All', secured: 'Secured', unsecured: 'Unsecured' },
  ko: { scope: '비교 조건', all: '전체', secured: '담보', unsecured: '무담보' },
  ja: { scope: '比較条件', all: 'すべて', secured: '担保あり', unsecured: '担保なし' }
} as const;
export function loanRankingCopy(locale: string) { return COPY[locale === 'ko' || locale === 'ja' ? locale : 'en']; }

type LoanRankingGroup = {
  key: string; label: string; currency: string; items: PublicProduct[]; rates: Record<string, number>;
};

/** Home presets use only disclosed public facts, within one type and currency. */
export function loanRankingGroups(products: PublicProduct[], country: string, locale: string): LoanRankingGroup[] {
  const currency = HOME_CURRENCIES[country];
  if (!currency) return [];
  const copy = loanRankingCopy(locale);
  const groups = new Map<string, LoanRankingGroup>();
  for (const product of products) {
    if (product.country_code !== country || product.currency !== currency || !TYPES.includes(product.product_type)) continue;
    const rate = getComparablePublicRate(product);
    if (rate === null) continue;
    const conditions: Array<{ key: string; label: string }> = [{ key: '0-all', label: copy.all }];
    // Missing flags and source-language text never imply secured/unsecured.
    if (product.secured_flag === true) conditions.push({ key: '1-secured', label: copy.secured });
    if (product.secured_flag === false) conditions.push({ key: '2-unsecured', label: copy.unsecured });
    for (const condition of conditions) {
      const key = `${country}|${product.product_type}|${currency}|${condition.key}`;
      const group = groups.get(key) ?? {
        key, label: `${product.product_type_label} · ${condition.label}`, currency, items: [], rates: {}
      };
      if (!group.items.some(item => item.product_id === product.product_id)) group.items.push(product);
      group.rates[product.product_id] = rate;
      groups.set(key, group);
    }
  }
  return [...groups.values()].sort((a, b) =>
    TYPES.indexOf(a.items[0].product_type) - TYPES.indexOf(b.items[0].product_type) || a.key.localeCompare(b.key, 'en')
  ).map(group => ({
    ...group,
    items: [...group.items].sort((a, b) => group.rates[a.product_id] - group.rates[b.product_id]
      || a.product_id.localeCompare(b.product_id)).slice(0, 5)
  }));
}
