import assert from 'node:assert/strict';
import test from 'node:test';
import { readFileSync } from 'node:fs';
import { presentPublicRate } from './public-rate-presentation.ts';
import { getComparablePublicRate, type PublicRate } from './public-rate.ts';
import { loanBrowseGroups, loanRankingGroups } from './public-loan-ranking.ts';
import type { PublicProduct } from './public-api.ts';
const records = JSON.parse(readFileSync(new URL('./fixtures/published-loans-2026-10-08.json', import.meta.url), 'utf8')) as PublicProduct[];
const product = (kind: PublicRate['kind'], text: string) => ({ rate: { kind, source_text: text, comparable_rate: null } });

test('all seven published Canadian loans retain full conditions without manufacturing ranking rates', () => {
  const before = structuredClone(records);
  for (const locale of ['en', 'ko', 'ja']) for (const record of records) {
    const metric = presentPublicRate(record, locale);
    assert.equal(metric.details, record.rate!.source_text);
    assert.ok(metric.value.length < 70);
    assert.equal(getComparablePublicRate(record), null);
    assert.ok(metric.entries?.length || /\d/.test(metric.value), record.product_name);
  }
  assert.deepEqual(records, before);
  assert.deepEqual(loanRankingGroups(records, 'CA', 'en'), []);
});
test('literal ranges retain both ends; absolute zero and unknown prose do not become guesses', () => {
  assert.equal(presentPublicRate(product('range', 'APR 5% to 10%, depending on credit.'), 'en').value, '5% to 10%');
  const zero = { rate: { kind: 'absolute' as const, source_text: '0%', comparable_rate: 0 } };
  assert.equal(presentPublicRate(zero, 'en').value, '0%');
  assert.equal(getComparablePublicRate(product('reference', 'Prime + 2%')), null);
  assert.equal(presentPublicRate(product('reference', 'Prime + 2%'), 'en').value, 'Prime + 2%');
  assert.equal(presentPublicRate(product('unknown', '30% down payment; credit terms on application.'), 'en').entries, undefined);
  assert.equal(presentPublicRate(product('conditional', '5-year Smart fixed\n4.94%\n4.96% APR 6'), 'en').value, '4.94% · APR 4.96%');
});
test('schedules keep exact term, redemption scope and formulas attached to their numbers', () => {
  const fixed = records.find(x => x.product_name === 'FIXED-RATE MORTGAGE')!;
  const entries = presentPublicRate(fixed, 'en').entries!;
  assert.equal(entries.length, 16);
  assert.deepEqual(entries[0], { label: 'Open (1 to 4 units) · 6 months', value: '9.150%' });
  assert.ok(entries.some(x => x.label.includes('Promotional rate - 5 years') && x.value === '5.190%'));
  const mixed = records.find(x => x.product_name.includes('Bank Select'))!;
  assert.ok(presentPublicRate(mixed, 'en').entries!.some(x => x.label.includes('prime + 1.00%') && x.value.startsWith('5.45%')));
  const unrelated = product('reference', 'A 5-year closed loan requires 20% down payment. Prime varies.');
  assert.equal(presentPublicRate(unrelated, 'en').entries, undefined);
  assert.equal(presentPublicRate(product('reference', '5-year closed 20% down payment required.'), 'en').entries, undefined);
  assert.ok(presentPublicRate(mixed, 'en').entries!.every(row => row.value.endsWith(' APR')));
});
test('home browse fallback has five mortgage records, alphabetic order and independent scopes', () => {
  const groups = loanBrowseGroups(records, 'CA');
  assert.deepEqual(groups.map(x => x.items.length), [5, 1, 1]);
  assert.deepEqual(groups[0].items.map(x => x.bank_code), ['BMO','LAURENTIAN','LAURENTIAN','MANULIFE','MANULIFE']);
  assert.deepEqual(groups[0].rates, {});
  assert.deepEqual(loanBrowseGroups(records, 'US'), []);
  assert.deepEqual(loanBrowseGroups(records, 'JP'), []);
  assert.deepEqual(loanBrowseGroups([], 'CA'), []);
  assert.deepEqual(loanBrowseGroups(records.map(x => ({ ...x, rate: { kind: 'absolute', comparable_rate: NaN, source_text: 'Invalid cached rate' } })), 'CA'), []);
  assert.deepEqual(loanBrowseGroups(records.map(x => ({ ...x, currency: 'USD' })), 'CA'), []);
  assert.deepEqual(loanBrowseGroups(records.map(x => ({ ...x, rate_type: null, term_length_text: null, security_requirement: null, collateral_text: null, secured_flag: null })), 'CA'), []);
  assert.equal(loanBrowseGroups([...records,...records], 'CA')[0].items.length, 5);
});
