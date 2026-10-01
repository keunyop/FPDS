import assert from 'node:assert/strict';
import test from 'node:test';
import type { PublicProduct } from './public-api.ts';
import { transactionCosts, withdrawalConditions } from './public-access.ts';
const product = (p: Partial<PublicProduct>) => ({ currency: 'CAD', ...p }) as PublicProduct;
test('transaction structures retain zero, unknown and excess costs in all locales', () => {
 for (const locale of ['en','ko','ja']) {
  assert.ok(transactionCosts(product({included_transactions:12,additional_transaction_fee:1.5}),locale).includes('1.50'));
  assert.ok(transactionCosts(product({transaction_fee:0}),locale).includes('0.00'));
  assert.ok(!transactionCosts(product({}),locale).includes('0'));
 }
 assert.match(transactionCosts(product({included_transactions:12}), 'en'), /Unavailable/);
 assert.equal(transactionCosts(product({unlimited_transactions_flag:true}), 'en'), 'Unlimited transactions');
});
test('withdrawal rules show access plus complete consequences, never invent penalty', () => {
 assert.equal(withdrawalConditions(product({non_redeemable_flag:true}),'en'),'Not permitted before maturity');
 assert.equal(withdrawalConditions(product({redeemable_flag:false}),'en'),'Not permitted before maturity');
 assert.match(withdrawalConditions(product({redeemable_flag:true,early_withdrawal_penalty:'90 days of interest; principal can be reduced.'}),'en'), /90 days of interest; principal can be reduced/);
 assert.equal(withdrawalConditions(product({early_withdrawal_penalty:'90 days of interest'}),'en'),'Unavailable');
});
