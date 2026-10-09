import type { PublicProduct } from './public-api.ts';
import { getComparablePublicRate } from './public-rate.ts';
import { hasRankingEssentials } from './public-ranking-essentials.ts';

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
    if (product.country_code !== country || product.currency !== currency || !TYPES.includes(product.product_type) || !hasRankingEssentials(product)) continue;
    const rate = getComparablePublicRate(product);
    if (rate === null) continue;
    const conditions: Array<{ key: string; label: string }> = [{ key: '0-all', label: copy.all }];
    // Security is shown with each LOC row; optional mortgage/loan flags never narrow Home ranking.
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

/** Browsing is separate from ranking: never manufacture a comparable rate. */
export function loanBrowseGroups(products: PublicProduct[], country: string): LoanRankingGroup[] {
  const currency = HOME_CURRENCIES[country];
  if (!currency) return [];
  return TYPES.flatMap(type => {
    const items = [...new Map(products.filter(product => product.country_code === country
      && product.currency === currency && product.product_type === type && hasRankingEssentials(product)
      && product.rate && product.rate.kind !== 'unknown' && product.rate.source_text?.trim()
      && (product.rate.kind !== 'absolute' || getComparablePublicRate(product) !== null))
      .map(product => [product.product_id, product])).values()]
      .sort((a, b) => (a.bank_name ?? '').localeCompare(b.bank_name ?? '', 'en')
        || (a.product_name ?? '').localeCompare(b.product_name ?? '', 'en') || a.product_id.localeCompare(b.product_id))
      .slice(0, 5);
    return items.length ? [{ key: `${country}|${type}|browse`, label: items[0].product_type_label, currency, items, rates: {} }] : [];
  });
}
export function loanBrowseCopy(locale: string) {
  return ({
    en: { title: 'Loans to compare', subtitle: 'Explore published rates and terms by loan type.', note: 'Up to five products, ordered by bank name. Rates depend on term, amount or eligibility; this is not a lowest-rate ranking.' },
    ko: { title: '비교할 대출상품', subtitle: '대출 종류별 공개 금리와 조건을 확인하세요.', note: '은행 이름순으로 최대 5개 상품을 표시합니다. 금리는 기간·금액·자격에 따라 달라지며 최저금리 순위가 아닙니다.' },
    ja: { title: '比較するローン商品', subtitle: 'ローンの種類ごとに公開金利と条件を確認できます。', note: '銀行名順に最大5商品を表示します。金利は期間・金額・対象条件によって異なり、最低金利のランキングではありません。' }
  })[locale === 'ko' || locale === 'ja' ? locale : 'en'];
}
