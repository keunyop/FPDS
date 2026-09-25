import test from 'node:test';
import { comparisonCopy } from './public-comparison-copy.ts';
import assert from 'node:assert/strict';
import type { PublicProduct, PublicProductDetailResponse } from './public-api.ts';
import { comparisonBoundary, comparisonFingerprint, comparisonHref, loadComparison, parseComparison, readSavedComparison } from './public-comparison.ts';
const product = (patch: Partial<PublicProduct> = {}) => ({ product_id: 'prod_a', country_code: 'CA', status: 'active', product_type: 'savings', currency: 'CAD', product_name: 'Savings', public_display_fee: 0, deposit_terms: { version: 1, basis: 'annual', reason: null, calculation_reason: null, withdrawal: 'unknown', options: [{ key: 'ongoing', months: null, days: null, rate: 2, minimum_deposit: 0 }] }, ...patch } as PublicProduct);
const detail = (p: PublicProduct, snapshot = 's1') => ({ product: p, freshness: { snapshot_id: snapshot } } as PublicProductDetailResponse);

test('sharing round-trips exact case-sensitive IDs, country and locale only', () => {
  const url = comparisonHref(['prod_a', 'prod_B-2', 'prod_a'], { countryCode: 'US', locale: 'ja', balance: 99999 } as never);
  const params = new URL(url, 'https://example.test').searchParams;
  assert.deepEqual([...new Set(params.keys())], ['product_id', 'country_code', 'locale']);
  assert.deepEqual(parseComparison(params), { ids: ['prod_a', 'prod_B-2'], countryCode: 'US', locale: 'ja', valid: true });
  assert.equal(url.includes('99999'), false);
});
test('URL parser bounds IDs and rejects paths or excess products', () => {
  assert.equal(parseComparison(new URLSearchParams('product_id=../../admin')).valid, false);
  assert.equal(parseComparison(new URLSearchParams('product_id='+ 'a'.repeat(129))).valid, false);
  assert.equal(parseComparison(new URLSearchParams('product_id=a&product_id=b&product_id=c&product_id=d&product_id=e')).valid, false);
  assert.deepEqual(parseComparison(new URLSearchParams('country_code=../&locale=invalid')), { countryCode: 'CA', locale: 'en', ids: [], valid: true });
});
test('fresh projection load retains input order; inactive/404 are missing and failures retry', async () => {
  const items = await loadComparison(['prod_a', 'inactive', 'gone', 'failure'], 'CA', async id => {
    if (id === 'gone') throw Object.assign(new Error('gone'), { status: 404 });
    if (id === 'failure') throw Object.assign(new Error('busy'), { status: 503 });
    return detail(product({ product_id: id, status: id === 'inactive' ? 'inactive' : 'active' }));
  });
  assert.deepEqual(items.map(item => [item.id, item.status]), [['prod_a', 'ready'], ['inactive', 'missing'], ['gone', 'missing'], ['failure', 'error']]);
  assert.equal(items[1].product, undefined);
});
test('cross-country/incorrect identity/missing snapshot fail closed', async () => {
  for (const response of [detail(product({ country_code: 'US' })), detail(product({ product_id: 'other' })), detail(product(), '')]) {
    assert.deepEqual(await loadComparison(['prod_a'], 'CA', async () => response), [{ id: 'prod_a', status: 'error' }]);
  }
});
test('mixed successful snapshots cannot produce a composite comparison', async () => {
  const result = await loadComparison(['a', 'b'], 'CA', async id => detail(product({ product_id: id }), id));
  assert.deepEqual(result, [{ id: 'a', status: 'error' }, { id: 'b', status: 'error' }]);
});
test('excess comparison requests cause no upstream calls', async () => {
  let calls = 0;
  await assert.rejects(loadComparison(['a','b','c','d','e'], 'CA', async () => { calls++; return detail(product()); }));
  assert.equal(calls, 0);
});
test('fingerprint ignores language, freshness and recheck dates but detects terms and zero/null', async () => {
  const p = product(); const baseline = await comparisonFingerprint(p);
  assert.match(baseline, /^[a-f0-9]{64}$/);
  assert.equal(await comparisonFingerprint({ ...p, product_type_label: '??', last_verified_at: '2026-09-25', last_changed_at: '2026-09-25' }), baseline);
  for (const change of [{ public_display_fee: 15 }, { public_display_fee: null }, { currency: 'USD' }, { fee_waiver_condition: 'Keep 5000' }]) assert.notEqual(await comparisonFingerprint({ ...p, ...change }), baseline);
  const { options, ...terms } = p.deposit_terms!;
  assert.equal(await comparisonFingerprint({ ...p, deposit_terms: { options, ...terms } }), baseline);
});
test('saved data validates country, version, duplicate IDs, hashes and size; strips unknown input', async () => {
  const fingerprint = await comparisonFingerprint(product());
  const value = { version: 1, countryCode: 'CA', items: [{ id: 'prod_a', fingerprint, name: 'Savings', balance: 1234 }], income: 1234 };
  const saved = readSavedComparison(JSON.stringify(value), 'CA');
  assert.deepEqual(saved, { countryCode: 'CA', items: [{ id: 'prod_a', fingerprint, name: 'Savings' }] });
  assert.equal(JSON.stringify(saved).includes('1234'), false);
  for (const input of [null, '{oops', 'x'.repeat(6001), JSON.stringify({ ...value, version: 2 }), JSON.stringify({ ...value, items: [...value.items, ...value.items] }), JSON.stringify({ ...value, items: [{ id: 'prod_a', fingerprint: 'invalid' }] })]) assert.equal(readSavedComparison(input, 'CA'), null);
  assert.equal(readSavedComparison(JSON.stringify(value), 'US'), null);
});
test('comparison boundaries distinguish mixed type/currency from unclear deposit conditions', () => {
  const p = product();
  assert.equal(comparisonBoundary([p, product({ currency: 'USD' })]), 'mixed');
  assert.equal(comparisonBoundary([p, product({ product_type: 'credit-card' })]), 'mixed');
  assert.equal(comparisonBoundary([p, product({ deposit_terms: null })]), 'conditions');
  assert.equal(comparisonBoundary([p, product()]), null);
  const gic = product({ product_type: 'gic' });
  assert.equal(comparisonBoundary([gic, gic]), 'conditions');
});

test('comparison copy preserves EN/KO/JA scripts without replacement characters', () => {
  assert.match(comparisonCopy('ko').title, /\p{Script=Hangul}/u);
  assert.match(comparisonCopy('ja').title, /\p{Script=Han}/u);
  for (const locale of ['en', 'ko', 'ja']) for (const value of Object.values(comparisonCopy(locale))) {
    assert.equal(value.includes('?'), false);
    assert.equal(value.includes('\uFFFD'), false);
  }
});
