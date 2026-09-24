import assert from 'node:assert/strict';
import test from 'node:test';
import type { PublicProduct } from './public-api.ts';
import { depositRankingGroups } from './public-deposit-ranking.ts';

function savings(id: string, rate = 3, overrides: Partial<PublicProduct> = {}): PublicProduct {
  return {
    product_id: id, product_type: 'savings', product_type_label: 'Savings', country_code: 'CA', currency: 'CAD',
    public_display_fee: 0, fee_waiver_condition: null, minimum_balance: 0,
    deposit_terms: { version: 1, basis: 'annual', reason: null, calculation_reason: null, withdrawal: 'unknown',
      options: [{ key: 'ongoing', months: null, days: null, rate, minimum_deposit: 0 }] },
    ...overrides
  } as PublicProduct;
}
const ids = (group: ReturnType<typeof depositRankingGroups>[number]) => group.items.map(p => p.product_id);

test('Home conditions use exact disclosed zeros, excluding unknowns and fee waivers', () => {
  const groups = depositRankingGroups([
    savings('free'), savings('paid', 4, {public_display_fee: 5, minimum_balance: 100}),
    savings('missing', 5, {public_display_fee: null, minimum_balance: null}),
    savings('waived', 6, {fee_waiver_condition: 'Keep 5,000', minimum_balance: 5000}),
    savings('balance-only', 2, {public_display_fee: null}),
    savings('fee-only', 1, {minimum_balance: null})
  ], 'CA', 'en');
  assert.equal(groups.length, 3);
  assert.deepEqual(ids(groups[0]), ['waived', 'missing', 'paid', 'free', 'balance-only']);
  assert.deepEqual(ids(groups[1]), ['free', 'fee-only']);
  assert.deepEqual(ids(groups[2]), ['free', 'balance-only']);
  assert.deepEqual(groups.map(g => g.label), ['Savings · All', 'Savings · No monthly fee', 'Savings · No minimum balance']);
});

test('Home currency follows country, never falls back to foreign or unknown-country products', () => {
  const rows = [savings('ca'), savings('fx', 99, {currency: 'EUR'}), savings('fx-usd', 99, {currency: 'USD'}),
    savings('us', 2, {country_code: 'US', currency: 'USD'}), savings('wrong', 99, {country_code: 'US'})];
  for (const [country, id, currency] of [['CA', 'ca', 'CAD'], ['US', 'us', 'USD']]) {
    const groups = depositRankingGroups(rows, country, 'en');
    assert.ok(groups.length);
    for (const group of groups) { assert.deepEqual(ids(group), [id]); assert.equal(group.currency, currency); }
  }
  assert.deepEqual(depositRankingGroups(rows, 'JP', 'en'), []);
  assert.deepEqual(depositRankingGroups(rows.slice(1, 3), 'CA', 'en'), []);
});

test('annual and APY conditions stay separate and have distinct localized labels', () => {
  const apy = savings('apy'); apy.deposit_terms!.basis = 'apy';
  for (const locale of ['en', 'ko', 'ja']) {
    const groups = depositRankingGroups([savings('annual'), apy], 'CA', locale);
    assert.equal(groups.length, 6);
    assert.ok(groups.every(g => !g.label.includes('?')));
    assert.equal(new Set(groups.map(g => g.label)).size, 6);
    assert.ok(groups.every(g => g.items.length === 1));
    assert.ok(groups.some(g => g.label.endsWith('APY')));
    if (locale === 'ko') assert.ok(groups.some(g => g.label.includes('월 수수료 없음')));
    if (locale === 'ja') assert.ok(groups.some(g => g.label.includes('最低残高なし')));
  }
});

test('GIC groups rank the exact term and redemption category without headline rates', () => {
  const gic = savings('gic', 99, {product_type: 'gic', product_type_label: 'GIC'});
  gic.deposit_terms!.withdrawal = 'non_redeemable';
  gic.deposit_terms!.options = [
    {key: 'm12', months: 12, days: null, rate: 2, minimum_deposit: 500},
    {key: 'm24', months: 24, days: null, rate: 4, minimum_deposit: 500},
    {key: 'd360', months: null, days: 360, rate: 1, minimum_deposit: 500}
  ];
  const other = structuredClone(gic); other.product_id = 'other';
  other.deposit_terms!.options[0].rate = 3; other.deposit_terms!.options[1].rate = 3;
  const redeemable = structuredClone(gic); redeemable.product_id = 'redeemable'; redeemable.deposit_terms!.withdrawal = 'redeemable';
  const unknown = structuredClone(gic); unknown.product_id = 'unknown'; unknown.deposit_terms!.withdrawal = 'unknown';
  const groups = depositRankingGroups([gic, other, redeemable, unknown], 'CA', 'en');
  assert.equal(groups.length, 6);
  assert.deepEqual(ids(groups.find(g => g.key.includes('|m12|non_redeemable|'))!), ['other', 'gic']);
  assert.deepEqual(ids(groups.find(g => g.key.includes('|m24|non_redeemable|'))!), ['gic', 'other']);
  assert.ok(groups.every(g => !ids(g).includes('unknown')));
});

test('invalid, unavailable and unrelated product conditions remain excluded; zero rates remain valid', () => {
  const invalid = ['promotional', 'tiered', 'market_linked', 'term_conflict', 'basis_unknown'].map(reason => {
    const p = savings(reason, 99); p.deposit_terms!.reason = reason; return p;
  });
  invalid.push(savings('old', 99, {deposit_terms: undefined}), savings('loan', 99, {product_type: 'mortgage'}));
  const unknown = savings('unknown'); unknown.deposit_terms!.basis = 'unknown'; invalid.push(unknown);
  const nan = savings('nan', NaN); invalid.push(nan);
  const groups = depositRankingGroups([...invalid, savings('zero', 0)], 'CA', 'en');
  assert.ok(groups.every(g => ids(g).join() === 'zero' && g.rates.zero === 0));
  assert.deepEqual(depositRankingGroups(invalid, 'CA', 'en'), []);
  assert.deepEqual(depositRankingGroups([], 'CA', 'en'), []);
});

test('Top 5 deduplicates, orders ties deterministically and does not mutate input', () => {
  const rows = Array.from({length: 7}, (_, i) => savings(String(i), i === 6 ? 5 : i));
  rows.push(structuredClone(rows[6]));
  const before = structuredClone(rows);
  assert.deepEqual(ids(depositRankingGroups(rows, 'CA', 'en')[0]), ['5', '6', '4', '3', '2']);
  assert.deepEqual(rows, before);
});
