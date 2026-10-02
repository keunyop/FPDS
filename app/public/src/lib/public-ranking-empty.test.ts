import assert from 'node:assert/strict';
import test from 'node:test';
import type { PublicProduct } from './public-api.ts';
import { rankingEmptyMessage } from './public-ranking-empty.ts';

const product = (overrides: Partial<PublicProduct> = {}) => ({country_code:'CA', currency:'CAD', product_type:'savings', ...overrides}) as PublicProduct;

test('Top 5 distinguishes absent target types from unverified rate basis in every locale', () => {
  for (const [locale, absent, basis] of [['en','No published','basis'], ['ko','공개된','기준'], ['ja','公開済み','基準']]) {
    assert.ok(rankingEmptyMessage([product({product_type:'chequing'}),product({product_type:'credit-card'})], 'deposit','CA',locale).includes(absent));
    assert.ok(rankingEmptyMessage([product()], 'deposit','CA',locale).includes(basis));
  }
});
test('Top 5 keeps country, home currency and loan absence distinct', () => {
  assert.match(rankingEmptyMessage([product({country_code:'US',currency:'USD'})], 'deposit','CA','en'), /No published/);
  assert.match(rankingEmptyMessage([product({currency:'USD'})], 'deposit','CA','en'), /currency/);
  assert.match(rankingEmptyMessage([product()], 'loan','CA','en'), /No published loans/);
  assert.match(rankingEmptyMessage([product({product_type:'line-of-credit'})], 'loan','CA','en'), /comparable full rate/);
});
test('known basis with unresolved terms never reports an absent catalogue or invents a rate', () => {
  const p = product({product_type:'gic', deposit_terms:{version:1, basis:'annual', reason:'term_unknown', calculation_reason:'term_unknown',withdrawal:'unknown',options:[]}});
  assert.match(rankingEmptyMessage([p], 'deposit','CA','en'), /terms and withdrawal/);
  assert.equal(p.deposit_terms?.options.length, 0);
});
