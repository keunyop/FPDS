import assert from 'node:assert/strict';
import test from 'node:test';
import { PUBLIC_LOCALES, normalizePublicLocale, getIntlLocale, getPublicMessages, getPublicDesignCopy, getPublicCatalogCopy, getPublicDiscoveryCopy, getPublicCoverageCopy, getPublicInformationNotice, getPublicRecommendationCopy, getPublicFeedbackCopy } from './public-locale.ts';
import { publicCountryOptions, formatPublicCountryName, publicMarketCurrency } from './public-country.ts';
import { parseProductGridPageFilters, buildCountryHref } from './public-query.ts';
import { buildProductDetailPath, normalizeProductDetailRequest, isIndexableProductLocale } from './public-url-policy.ts';
import { parseComparison, comparisonHref } from './public-comparison.ts';
import { comparisonCopy } from './public-comparison-copy.ts';
import { depositCopy } from './public-deposit.ts';
import { scenarioCopy } from './public-scenario-copy.ts';
import { publicFactCopy } from './public-fact-copy.ts';
import { getVerificationCopy } from './public-verification.ts';
import { accessCopy, transactionCosts } from './public-access.ts';
import { bankHandoffCopy, handoffConditions } from './public-bank-handoff.ts';
import { depositRankingGroups } from './public-deposit-ranking.ts';
import type { PublicProduct } from './public-api.ts';

function leaves(value: unknown, key = ''): Record<string, string> {
  if (typeof value === 'string') return { [key]: value };
  return Object.fromEntries(Object.entries(value as object).flatMap(([name, child]) => Object.entries(leaves(child, key + '.' + name))));
}

test('Filipino has complete UI keys and unchanged interpolation contracts', () => {
  const getters = [getPublicMessages, getPublicDesignCopy, getPublicDiscoveryCopy, getPublicCoverageCopy, getPublicInformationNotice, getPublicRecommendationCopy, getPublicFeedbackCopy, comparisonCopy, depositCopy, scenarioCopy, publicFactCopy, getVerificationCopy, accessCopy, bankHandoffCopy];
  for (const getter of getters) {
    const en = leaves(getter('en')), fil = leaves(getter('fil'));
    assert.deepEqual(Object.keys(fil).sort(), Object.keys(en).sort());
    for (const [key, text] of Object.entries(fil)) {
      assert.ok(!text.includes('\uFFFD'), key);
      assert.deepEqual(text.match(/\{\w+\}/g)?.sort(), en[key].match(/\{\w+\}/g)?.sort(), key);
      assert.ok(text || en[key] === '', key);
    }
  }
  assert.equal(getPublicMessages('fil').localeName, 'Filipino');
  assert.equal(getPublicMessages('fil').nav.localeLabel, 'Wika');
  for (const type of ['deposit', 'card', 'loan'] as const) assert.match(getPublicCatalogCopy('fil', type).title, /Ihambing/);
  assert.equal(normalizePublicLocale('tl'), 'en');
  assert.equal(normalizePublicLocale('unknown'), 'en');
  assert.equal(getIntlLocale('fil'), 'fil-PH');
  assert.equal(PUBLIC_LOCALES.length, 4);
});

test('PH is selectable through initial loading, empty and failed country responses', () => {
  for (const published of [[], [{ code: 'US', count: 3 }], [{ code: 'PH', count: 0 }]]) {
    const options = publicCountryOptions(published, 'CA', 'fil');
    assert.deepEqual(options.find(c => c.code === 'PH'), { code: 'PH', count: 0 });
    assert.ok(options.some(c => c.code === 'CA'));
  }
  assert.equal(formatPublicCountryName('PH', 'fil'), 'Pilipinas');
});

test('published PH counts replace preparation counts and invalid countries stay excluded', () => {
  const options = publicCountryOptions([{ code: 'PH', count: 8, bank_count: 2 }, { code: 'US', count: 4 }, { code: 'ZZZ', count: 9 }, { code: 'JP', count: -1 }], 'PH', 'fil');
  assert.equal(options.filter(c => c.code === 'PH').length, 1);
  assert.deepEqual(options.find(c => c.code === 'PH'), { code: 'PH', count: 8, bank_count: 2 });
  assert.deepEqual(options.map(c => c.code).sort(), ['PH', 'US']);
});

test('country, catalog, detail, comparison and calculator navigation retain Filipino', () => {
  assert.equal(parseProductGridPageFilters({ locale: 'fil', country_code: 'PH' }).locale, 'fil');
  const changed = buildCountryHref('/products', new URLSearchParams('locale=fil&country_code=CA&bank_code=old&product_type=gic&q=old&page=5'), 'PH');
  const country = new URL(changed, 'https://example.test');
  assert.equal(country.searchParams.get('locale'), 'fil');
  assert.equal(country.searchParams.get('country_code'), 'PH');
  assert.equal(country.searchParams.has('bank_code'), false);
  assert.equal(buildProductDetailPath('/products/Exact_ID', 'fil', 'PH'), '/products/Exact_ID?locale=fil&country_code=PH');
  assert.equal(normalizeProductDetailRequest(new URL('https://example.test/products/Exact_ID?locale=fil&country_code=PH')).locale, 'fil');
  assert.equal(isIndexableProductLocale('fil'), false);
  const parsed = parseComparison(new URL(comparisonHref(['Exact_ID'], { locale: 'fil', countryCode: 'PH' }), 'https://example.test').searchParams);
  assert.equal(parsed.locale, 'fil'); assert.equal(parsed.countryCode, 'PH'); assert.deepEqual(parsed.ids, ['Exact_ID']);
});

test('Filipino presentation preserves original conditions, zero and unknown', () => {
  const product = { currency: 'PHP', product_type: 'chequing', unlimited_transactions_flag: false, included_transactions: 3, transaction_fee: 0, additional_transaction_fee: null, fee_waiver_condition: 'Maintain PHP 5,000', minimum_balance: null } as PublicProduct;
  const metrics = transactionCosts(product, 'fil');
  assert.match(JSON.stringify(metrics), /₱|PHP/);
  assert.ok(!JSON.stringify(metrics).includes('CAD'));
  assert.ok(handoffConditions(product, 'fil').some(f => f.value === 'Maintain PHP 5,000'));
  assert.equal(product.additional_transaction_fee, null);
});

test('PH Home groups require explicit PHP, with original rate/fee gates intact', () => {
  const savings = { product_id: 'php', country_code: 'PH', currency: 'PHP', product_type: 'savings', product_type_label: 'Savings account', public_display_fee: 0, fee_waiver_condition: null, deposit_terms: { version: 1, basis: 'annual', reason: null, calculation_reason: null, withdrawal: 'unknown', options: [{ key: 'ongoing', months: null, days: null, rate: 2, minimum_deposit: 0 }] } } as PublicProduct;
  const groups = depositRankingGroups([savings, { ...savings, product_id: 'missing', currency: '' }, { ...savings, product_id: 'foreign', currency: 'USD' }, { ...savings, product_id: 'other', country_code: 'CA' }], 'PH', 'fil');
  assert.ok(groups.length);
  for (const group of groups) { assert.equal(group.currency, 'PHP'); assert.deepEqual(group.items.map(p => p.product_id), ['php']); }
  assert.equal(publicMarketCurrency('PH'), 'PHP'); assert.equal(publicMarketCurrency('ZZ'), undefined);
});
