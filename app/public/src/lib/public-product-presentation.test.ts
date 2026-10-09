import assert from 'node:assert/strict';
import test from 'node:test';
import type { PublicProduct } from './public-api.ts';
import { buildPublicProductMetrics, buildPublicOptionalMetrics, formatPublicProductTerm } from './public-product-presentation.ts';
import { publicFactCopy } from './public-fact-copy.ts';

function product(type: string, extra: Partial<PublicProduct> = {}): PublicProduct {
  return { product_type: type, product_family: ['mortgage', 'personal-loan', 'line-of-credit', 'credit-card'].includes(type) ? 'lending' : 'deposit',
    country_code: 'CA', currency: 'CAD', rate: {kind: 'absolute', comparable_rate: 3.5, source_text: null},
    public_display_fee: 0, annual_fee: 0, term_length_text: '1 year', term_length_days: null, term_rate_table: [],
    rate_type: 'Fixed', unlimited_transactions_flag: true, non_redeemable_flag: true, redeemable_flag: null,
    secured_flag: false, minimum_balance: null, minimum_deposit: null, ...extra } as PublicProduct;
}

test('every supported product lists its essential facts without optional placeholders', () => {
  const labels: Record<string, string[]> = {
    chequing: ['Monthly fee', 'Transaction costs'], savings: ['Interest rate', 'Monthly fee'],
    gic: ['Interest rate', 'Term', 'Early withdrawal'], 'credit-card': ['Annual fee', 'Purchase interest rate'],
    mortgage: ['Interest rate', 'Rate type', 'Term'], 'personal-loan': ['Interest rate', 'Term'],
    'line-of-credit': ['Interest rate', 'Security']
  };
  for (const [type, expected] of Object.entries(labels)) {
    const facts = buildPublicProductMetrics(product(type), 'en', 'card');
    assert.deepEqual(facts.map(f => f.label), expected);
    assert.ok(facts.every(f => f.value && f.value !== 'Unavailable'));
    assert.deepEqual(buildPublicProductMetrics(product(type, {minimum_balance: 1000, minimum_deposit: 500,
      loan_amount_text: '$100,000', credit_limit_text: '$50,000', fee_waiver_condition: 'Verified waiver'}), 'en', 'card'), facts);
  }
});

test('detail omits optional unknowns but preserves zero, false and distinct money meanings', () => {
  assert.deepEqual(buildPublicOptionalMetrics(product('savings'), 'en'), []);
  const facts = buildPublicOptionalMetrics(product('savings', {minimum_balance: 0, minimum_deposit: 500,
    fee_waiver_condition: 'Keep CAD 5,000.', deposit_conditions: {interest_payment_frequency: 'Paid monthly.'}}), 'en');
  assert.equal(facts.length, 4);
  assert.notEqual(facts[0].label, facts[1].label);
  assert.match(facts[0].value, /0/); assert.match(facts[1].value, /500/);
  assert.equal(facts[2].value, 'Keep CAD 5,000.'); assert.equal(facts[3].value, 'Paid monthly.');
  assert.equal(buildPublicOptionalMetrics(product('personal-loan'), 'en').find(f => f.label === 'Security')?.value, 'Unsecured');
  assert.deepEqual(buildPublicOptionalMetrics(product('personal-loan', {secured_flag: undefined}), 'en'), []);
  assert.equal(buildPublicProductMetrics(product('line-of-credit'), 'en')[1].value, 'Unsecured');
});

test('conditional essentials and source qualifications remain visible', () => {
  const cashable = product('gic', {redeemable_flag: true, non_redeemable_flag: null,
    early_withdrawal_penalty: 'Early withdrawal costs 90 days of interest.'});
  assert.match(buildPublicProductMetrics(cashable, 'en', 'card')[2].value, /90 days of interest/);
  const range = product('personal-loan', {rate: {kind: 'range', comparable_rate: null, source_text: 'APR 5% to 10%, depending on credit.'}});
  assert.equal(buildPublicProductMetrics(range, 'en', 'card')[0].value, '5% to 10%');
  assert.equal(buildPublicProductMetrics(range, 'en', 'card')[0].details, range.rate!.source_text);
  const checking = product('chequing', {unlimited_transactions_flag: null, included_transactions: 0, additional_transaction_fee: 0});
  assert.match(buildPublicProductMetrics(checking, 'en')[1].value, /0 included/);
});

test('localized labels and partial information remain readable; literal days stay literal', () => {
  for (const locale of ['en', 'ko', 'ja']) {
    assert.ok(Object.values(publicFactCopy(locale)).every(v => v && !v.includes('??')));
    for (const type of ['chequing','savings','gic','credit-card','mortgage','personal-loan','line-of-credit']) {
      assert.ok(buildPublicProductMetrics(product(type), locale).every(f => f.label && f.value));
    }
  }
  assert.equal(publicFactCopy('ko').additional, '확인된 추가 정보');
  assert.equal(formatPublicProductTerm(product('gic', {term_length_text: null, term_length_days: 360}), 'en'), '360 days');
});


test('a required GIC schedule is shown even without a representative scalar', () => {
  const p = product('gic', {rate: {kind: 'unknown', comparable_rate: null, source_text: null},
    term_length_text: null, term_rate_table: [{term_label: '18 months', term_length_days: null,
      rate: 3.75, minimum_deposit: null, notes: 'Interest paid at maturity.'}]});
  assert.equal(buildPublicProductMetrics(p, 'en', 'card')[0].value, '18 months: 3.75% (Interest paid at maturity.)');
  assert.equal(p.rate!.comparable_rate, null);
});

test('checking detail retains optional deposit interest and full qualifiers after compact bank handoff', () => {
  for (const locale of ['en','ko','ja']) {
    assert.equal(buildPublicOptionalMetrics(product('chequing', {rate:{kind:'absolute',comparable_rate:0,source_text:null}}), locale)[0].value, '0%');
    const source_text = '0.05% on daily deposit balances; overdraft charges are separate.';
    assert.equal(buildPublicOptionalMetrics(product('chequing', {rate:{kind:'conditional',comparable_rate:null,source_text}}), locale)[0].value, source_text);
    assert.deepEqual(buildPublicOptionalMetrics(product('chequing', {rate:{kind:'unknown',comparable_rate:null,source_text:null}}), locale), []);
  }
});
