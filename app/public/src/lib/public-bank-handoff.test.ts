import assert from 'node:assert/strict';
import test from 'node:test';
import type { PublicProduct } from './public-api.ts';
import { bankHandoffCopy, handoffConditions, handoffCost, officialDestination } from './public-bank-handoff.ts';
function product(overrides: Partial<PublicProduct> = {}) {
  return { product_type: 'savings', currency: 'CAD', minimum_balance: null, minimum_deposit: null,
    fee_waiver_condition: null, redeemable_flag: null, non_redeemable_flag: null,
    early_withdrawal_penalty: null, public_display_fee: null, term_rate_table: [], ...overrides } as PublicProduct;
}
test('safe approved destinations retain exact domain/path/query and reject unsafe URLs', () => {
  assert.deepEqual(officialDestination('https://www.td.com/product?q=one#fees'), { href: 'https://www.td.com/product?q=one#fees', domain: 'www.td.com' });
  for (const url of [null, '', 'http://bank.ca/p', '//bank.ca', 'javascript:alert(1)', 'https://u:p@bank.ca', 'https://127.0.0.1/p', 'https://[::1]/', 'https://localhost/', 'https://bank.local/a', 'https://bank.ca:8443/a', ' https://bank.ca', 'https://bank.ca/a b', 'https://bank.ca\\@evil.com']) assert.equal(officialDestination(url), null, String(url));
});
test('zero, missing, invalid and distinct amount meanings stay separate', () => {
  const facts = handoffConditions(product({ minimum_deposit: 0, minimum_balance: 5000 }), 'en');
  assert.equal(facts[0].value, 'CAD 0'); assert.equal(facts[1].value, 'CAD 5,000');
  assert.notEqual(facts[0].label, facts[1].label);
  assert.equal(handoffCost(product({ public_display_fee: 0 }), 'en')?.value, 'CAD 0');
  for (const value of [null, NaN, Infinity, -1]) {
    assert.equal(handoffConditions(product({ minimum_deposit: value }), 'en')[0].value, 'Check with the bank');
    assert.equal(handoffCost(product({ public_display_fee: value }), 'en')?.value, 'Check with the bank');
  }
  assert.equal(handoffCost(product({ currency: '', public_display_fee: 5 }), 'en')?.value, 'Check with the bank');
});
test('waivers retain source language and never turn base costs into zero', () => {
  const p = product({ public_display_fee: 15, fee_waiver_condition: 'Waived with CAD 5,000 daily balance.' });
  for (const locale of ['en','ko','ja']) assert.equal(handoffConditions(p, locale).find(f => f.key === 'waiver')?.value, p.fee_waiver_condition);
  assert.equal(handoffCost(p, 'en')?.value, 'CAD 15');
  assert.equal(handoffCost(product({ product_type: 'credit-card', annual_fee: 120 }), 'en')?.value, 'CAD 120');
  assert.equal(handoffCost(product({ product_type: 'mortgage' }), 'en'), null);
});
test('transactions never imply unrestricted withdrawals; conflicting GIC flags fail closed', () => {
  const p = product({ unlimited_transactions_flag: true, included_transactions: 99, redeemable_flag: true });
  assert.equal(handoffConditions(p, 'en').find(f => f.key === 'withdrawal')?.value, 'Check with the bank');
  for (const value of [true, false]) assert.equal(handoffConditions(product({ product_type: 'gic', redeemable_flag: value, non_redeemable_flag: value }), 'en').find(f => f.key === 'withdrawal')?.value, 'Check with the bank');
  assert.equal(handoffConditions(product({ product_type: 'gic', non_redeemable_flag: true, early_withdrawal_penalty: '90 days of interest.' }), 'en').find(f => f.key === 'withdrawal')?.value, 'Non-redeemable');
  assert.equal(handoffConditions(product({ product_type: 'gic', early_withdrawal_penalty: '90 days of interest.' }), 'en').find(f => f.key === 'penalty')?.value, '90 days of interest.');
});
test('GIC row minimums preserve their own term and never become an account-wide minimum', () => {
  const p = product({ product_type: 'gic', term_rate_table: [
    { term_label: '1 year', term_length_days: 365, rate: 2, minimum_deposit: 1000, notes: null },
    { term_label: '2 years', term_length_days: 730, rate: 3, minimum_deposit: 5000, notes: null }
  ] });
  assert.equal(handoffConditions(p, 'en').find(f => f.key === 'termMinimum')?.value, '1 year: CAD 1,000; 2 years: CAD 5,000');
  assert.equal(p.minimum_deposit, null);
  p.minimum_deposit = 1000;
  assert.match(handoffConditions(p, 'en').find(f => f.key === 'termMinimum')!.value, /2 years: CAD 5,000/);
});
test('all locales have native action, external-site, unknown and checklist labels', () => {
  for (const locale of ['en','ko','ja']) {
    const copy = bankHandoffCopy(locale);
    assert.ok(copy.action && copy.external && copy.bank);
    assert.equal(handoffConditions(product(), locale).length, 3);
    assert.equal(handoffConditions(product(), locale)[0].value, copy.bank);
  }
  assert.match(bankHandoffCopy('ko').action, /[가-힣]/);
  assert.match(bankHandoffCopy('ja').action, /[一-龯]/);
});
