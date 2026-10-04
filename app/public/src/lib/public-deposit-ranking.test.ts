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

test('Home uses required fees and does not offer optional balance presets', () => {
  const groups = depositRankingGroups([
    savings('free'), savings('paid', 4, {public_display_fee: 5, minimum_balance: 100}),
    savings('missing', 5, {public_display_fee: null, minimum_balance: null}),
    savings('waived', 6, {fee_waiver_condition: 'Keep 5,000', minimum_balance: 5000}),
    savings('balance-only', 2, {public_display_fee: null}),
    savings('fee-only', 1, {minimum_balance: null})
  ], 'CA', 'en');
  assert.equal(groups.length, 2);
  assert.deepEqual(ids(groups[0]), ['waived', 'paid', 'free', 'fee-only']);
  assert.deepEqual(ids(groups[1]), ['free', 'fee-only']);
  assert.deepEqual(groups.map(g => g.label), ['Savings · All', 'Savings · No monthly fee']);
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
    assert.equal(groups.length, 4);
    assert.ok(groups.every(g => !g.label.includes('?')));
    assert.equal(new Set(groups.map(g => g.label)).size, 4);
    assert.ok(groups.every(g => g.items.length === 1));
    assert.ok(groups.some(g => g.label.endsWith('APY')));
    if (locale === 'ko') assert.ok(groups.some(g => g.label.includes('월 수수료 없음')));
    if (locale === 'ja') assert.ok(groups.some(g => g.label.includes('月額手数料なし')));
  }
});

test('GIC groups rank the exact term and redemption category without headline rates', () => {
  const gic = savings('gic', 99, {product_type: 'gic', product_type_label: 'GIC', non_redeemable_flag: true});
  gic.deposit_terms!.withdrawal = 'non_redeemable';
  gic.deposit_terms!.options = [
    {key: 'm12', months: 12, days: null, rate: 2, minimum_deposit: 500},
    {key: 'm24', months: 24, days: null, rate: 4, minimum_deposit: 500},
    {key: 'd360', months: null, days: 360, rate: 1, minimum_deposit: 500}
  ];
  const other = structuredClone(gic); other.product_id = 'other';
  other.deposit_terms!.options[0].rate = 3; other.deposit_terms!.options[1].rate = 3;
  const redeemable = structuredClone(gic); redeemable.product_id = 'redeemable'; redeemable.deposit_terms!.withdrawal = 'redeemable'; redeemable.non_redeemable_flag = null; redeemable.redeemable_flag = true; redeemable.early_withdrawal_penalty = 'No interest is paid when redeemed within 30 days.';
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
  assert.ok(groups.every(g => ids(g).join() === 'zero' && g.values.zero === 0));
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


test('optional balance and deposit omissions cannot change Home rankings', () => {
  const rows = [savings('a', 4), savings('b', 3)];
  const before = depositRankingGroups(rows, 'CA', 'en').map(g => [g.key, ids(g)]);
  for (const p of rows) { p.minimum_balance = null; p.minimum_deposit = null; p.deposit_terms!.options[0].minimum_deposit = null; }
  assert.deepEqual(depositRankingGroups(rows, 'CA', 'en').map(g => [g.key, ids(g)]), before);
});

function checking(id: string, fee = 0, overrides: Partial<PublicProduct> = {}): PublicProduct {
  return savings(id, 99, {product_type: 'chequing', product_type_label: 'Chequing', public_display_fee: fee,
    unlimited_transactions_flag: true, deposit_terms: undefined, rate: undefined, ...overrides});
}

test('Chequing Top5 orders required monthly fees ascending without using optional interest or total-cost guesses', () => {
  const rows = [checking('b', 0, {transaction_fee: 4}), checking('a', 0), checking('waived', 15, {fee_waiver_condition: 'Waived with CAD 5,000.'}),
    checking('one', 1), checking('two', 2), checking('three', 3), checking('four', 4), checking('five', 5)];
  const before = structuredClone(rows);
  rows.push(structuredClone(rows[0]));
  const group = depositRankingGroups(rows, 'CA', 'en')[0];
  assert.equal(group.metric, 'monthly_fee'); assert.equal(group.basis, null);
  assert.equal(group.currency, 'CAD'); assert.deepEqual(ids(group), ['a','b','one','two','three']);
  assert.equal(group.values.a, 0);
  assert.deepEqual(rows.slice(0,-1), before);
  const qualified = depositRankingGroups([checking('waived', 15, {fee_waiver_condition:'Waived with CAD 5,000.'})], 'CA', 'en')[0];
  assert.equal(qualified.values.waived, 15);
});

test('Chequing requires native monthly fees and proven transaction costs, preserving explicit zeros', () => {
  const rows = [checking('unlimited'), checking('finite', 1, {unlimited_transactions_flag: null, included_transactions:12, additional_transaction_fee:1.5}),
    checking('zero-allowance',2,{unlimited_transactions_flag:false,included_transactions:0,additional_transaction_fee:0}),
    checking('per-use',3,{unlimited_transactions_flag:null,transaction_fee:0}),
    checking('missing-cost',0,{unlimited_transactions_flag:null}), checking('missing-excess',0,{unlimited_transactions_flag:null,included_transactions:12}),
    checking('invalid-count',0,{unlimited_transactions_flag:null,included_transactions:1.5,additional_transaction_fee:1}),
    checking('missing-fee',0,{public_display_fee:null}), checking('negative',-1), checking('nan',NaN),
    checking('string',0,{public_display_fee:'0' as unknown as number}), checking('bool',0,{public_display_fee:false as unknown as number})];
  assert.deepEqual(ids(depositRankingGroups(rows,'CA','en')[0]), ['unlimited','finite','zero-allowance','per-use']);
});

test('Chequing retains country/currency isolation and optional omissions cannot change eligibility or order', () => {
  const rows = [checking('ca',0),checking('foreign',0,{currency:'USD'}),checking('us',0,{country_code:'US',currency:'USD'})];
  assert.deepEqual(ids(depositRankingGroups(rows,'CA','en')[0]), ['ca']);
  assert.deepEqual(ids(depositRankingGroups(rows,'US','ko')[0]), ['us']);
  const before=depositRankingGroups(rows,'CA','en').map(g=>[g.key,ids(g)]);
  rows.forEach(p=>{p.minimum_balance=null;p.minimum_deposit=null;p.fee_waiver_condition=null;p.rate=undefined;});
  assert.deepEqual(depositRankingGroups(rows,'CA','en').map(g=>[g.key,ids(g)]), before);
});

test('GIC rankings require complete matching withdrawal essentials but never optional deposits', () => {
  const base=checking('fixed');base.product_type='gic';base.product_type_label='GIC';base.non_redeemable_flag=true;
  base.deposit_terms={version:1,basis:'annual',reason:null,calculation_reason:null,withdrawal:'non_redeemable',
    options:[{key:'m12',months:12,days:null,rate:3,minimum_deposit:null}]};
  const cashable=structuredClone(base);cashable.product_id='cashable';cashable.non_redeemable_flag=null;cashable.redeemable_flag=true;
  cashable.early_withdrawal_penalty='No interest is paid when redeemed within 30 days.';cashable.deposit_terms!.withdrawal='redeemable';
  const missing=structuredClone(cashable);missing.product_id='missing';missing.early_withdrawal_penalty=null;
  const conflict=structuredClone(cashable);conflict.product_id='conflict';conflict.non_redeemable_flag=true;
  const mismatch=structuredClone(cashable);mismatch.product_id='mismatch';mismatch.deposit_terms!.withdrawal='non_redeemable';
  const groups=depositRankingGroups([base,cashable,missing,conflict,mismatch],'CA','en');
  assert.deepEqual(groups.flatMap(ids).sort(),['cashable','fixed']);
});

test('Chequing contradictory unlimited and finite transaction declarations cannot enter Top5', () => {
  const rows=[checking('valid'),checking('finite',1,{unlimited_transactions_flag:false,included_transactions:12,additional_transaction_fee:0}),
    checking('conflict',0,{unlimited_transactions_flag:true,included_transactions:12,additional_transaction_fee:1}),
    checking('zero-conflict',0,{unlimited_transactions_flag:true,included_transactions:0,additional_transaction_fee:0})];
  assert.deepEqual(ids(depositRankingGroups(rows,'CA','en')[0]),['valid','finite']);
});
