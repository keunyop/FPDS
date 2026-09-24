import assert from 'node:assert/strict';
import test from 'node:test';
import type { PublicProduct, PublicProductsResponse } from './public-api.ts';
import { allProductPages } from './public-deposit.ts';
import { loanRankingCopy, loanRankingGroups } from './public-loan-ranking.ts';

function loan(id: string, rate = 4, overrides: Partial<PublicProduct> = {}): PublicProduct {
  return { product_id: id, country_code: 'CA', currency: 'CAD', product_type: 'mortgage',
    product_type_label: 'Mortgage', secured_flag: null,
    rate: {kind: 'absolute', comparable_rate: rate, source_text: null}, ...overrides } as PublicProduct;
}
const ids = (group: ReturnType<typeof loanRankingGroups>[number]) => group.items.map(p => p.product_id);

test('Loan Home groups by exact type and explicit security without interpreting names or unknown flags', () => {
  const groups = loanRankingGroups([
    loan('unknown', 3, {product_name: 'Secured mortgage'}), loan('secured', 4, {secured_flag: true}),
    loan('unsecured', 5, {secured_flag: false}), loan('missing', 6, {secured_flag: undefined}),
    loan('personal', 0, {product_type: 'personal-loan', product_type_label: 'Personal Loan'}),
    loan('credit', 8, {product_type: 'line-of-credit', product_type_label: 'Line of Credit', secured_flag: false})
  ], 'CA', 'en');
  assert.equal(groups.length, 6);
  assert.deepEqual(ids(groups[0]), ['unknown', 'secured', 'unsecured', 'missing']);
  assert.deepEqual(ids(groups[1]), ['secured']); assert.deepEqual(ids(groups[2]), ['unsecured']);
  assert.deepEqual(ids(groups[3]), ['personal']); assert.equal(groups[3].rates.personal, 0);
  assert.deepEqual(groups.map(g => g.label), ['Mortgage · All', 'Mortgage · Secured', 'Mortgage · Unsecured',
    'Personal Loan · All', 'Line of Credit · All', 'Line of Credit · Unsecured']);
});

test('Loan groups isolate country and home currency without fallback', () => {
  const rows = [loan('ca'), loan('fx', 1, {currency: 'EUR'}), loan('foreign', 1, {country_code: 'US'}),
    loan('us', 2, {country_code: 'US', currency: 'USD'})];
  assert.deepEqual(ids(loanRankingGroups(rows, 'CA', 'en')[0]), ['ca']);
  const us = loanRankingGroups(rows, 'US', 'en')[0]; assert.deepEqual(ids(us), ['us']); assert.equal(us.currency, 'USD');
  assert.deepEqual(loanRankingGroups(rows, 'JP', 'en'), []);
  assert.deepEqual(loanRankingGroups([rows[1]], 'CA', 'en'), []);
});

test('Loan conditions exclude qualified, invalid and legacy rates and non-loan products', () => {
  const rows = (['range', 'reference', 'conditional', 'promotional', 'unknown'] as const).map(kind =>
    loan(kind, 1, {rate: {kind, comparable_rate: 1, source_text: 'Qualified'}}));
  rows.push(loan('old', 1, {rate: undefined}), loan('deposit', 1, {product_type: 'savings'}));
  for (const value of [NaN, Infinity, -1, 101]) rows.push(loan(String(value), value));
  assert.deepEqual(loanRankingGroups(rows, 'CA', 'en'), []);
  assert.deepEqual(loanRankingGroups([], 'CA', 'en'), []);
});

test('Loan Top 5 sorts ascending with stable ties, deduplicates and preserves inputs', () => {
  const rows = Array.from({length: 8}, (_, i) => loan(String(i), i === 1 ? 0 : i));
  rows.reverse();rows.push(structuredClone(rows[0]));const before = structuredClone(rows);
  assert.deepEqual(ids(loanRankingGroups(rows, 'CA', 'en')[0]), ['0', '1', '2', '3', '4']);
  assert.deepEqual(rows, before);
});

test('Loan ranking reads eligible products beyond page one; failed or changed later pages cannot make a partial ranking', async () => {
  const response = (page: number, snapshot = 'snapshot') => ({
    items: page === 1 ? [loan('mortgage', 4)] : [loan('late-personal', 2, {product_type: 'personal-loan'})],
    page, has_next_page: page === 1, freshness: {snapshot_id: snapshot}
  } as PublicProductsResponse);
  const all = await allProductPages(async page => response(page));
  assert.ok(loanRankingGroups(all.items, 'CA', 'en').some(g => ids(g).includes('late-personal')));
  await assert.rejects(() => allProductPages(async page => response(page, String(page))), /snapshot changed/);
  await assert.rejects(() => allProductPages(async page => {if (page === 2) throw Error('Unavailable'); return response(page);}), /Unavailable/);
});

test('Loan condition labels are translated, unambiguous and use English fallback', () => {
  for (const locale of ['en', 'ko', 'ja']) {
    const copy = loanRankingCopy(locale);
    const groups = loanRankingGroups([loan('yes', 3, {secured_flag: true}), loan('no', 5, {secured_flag: false})], 'CA', locale);
    assert.equal(groups.length, 3); assert.equal(new Set(groups.map(g => g.label)).size, 3);
    assert.ok(groups.every(g => !g.label.includes('?')));
    assert.ok(groups[1].label.endsWith(copy.secured)); assert.ok(groups[2].label.endsWith(copy.unsecured));
  }
  assert.equal(loanRankingCopy('ko').unsecured, '무담보');
  assert.equal(loanRankingCopy('ja').secured, '担保あり');
  assert.deepEqual(loanRankingCopy('fr'), loanRankingCopy('en'));
});
