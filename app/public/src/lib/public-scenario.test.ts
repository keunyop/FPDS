import assert from 'node:assert/strict';
import test from 'node:test';
import type { PublicProduct } from './public-api.ts';
import { compareScenario, scenarioAmount, scenarioDifference, scenarioFee, scenarioInterest, scenarioPeriods, scenarioScope } from './public-scenario.ts';
import { scenarioCopy } from './public-scenario-copy.ts';
import { comparisonHref, comparisonFingerprint, readSavedComparison } from './public-comparison.ts';
const year = { key: 'm12', months: 12, days: null };
function product(id = 'a', rate = 2, overrides: Partial<PublicProduct> = {}): PublicProduct {
  return { product_id: id, product_type: 'savings', status: 'active', country_code: 'CA', currency: 'CAD',
    minimum_balance: 0, minimum_deposit: 0, public_display_fee: 0, fee_waiver_condition: null,
    deposit_terms: { version: 1, basis: 'annual', reason: null, calculation_reason: null, withdrawal: 'unknown',
      options: [{ key: 'ongoing', months: null, days: null, rate, minimum_deposit: 0 }] }, ...overrides } as PublicProduct;
}
function gic(id: string, months = 12, rate = 2) {
  const p = product(id, rate, { product_type: 'gic' });
  p.deposit_terms!.options = [{ key: `m${months}`, months, days: null, rate, minimum_deposit: 500 }];
  return p;
}
test('same 20000 and one year gives 400/600 and a signed 200 difference without netting fees', () => {
  const a = product('a', 2, { public_display_fee: 5 }), b = product('b', 3, { public_display_fee: 10 });
  const result = compareScenario(a, b, year, '20000');
  assert.deepEqual(result.interest.map(x => x.value), [400, 600]);
  assert.deepEqual(result.fees.map(x => x.value), [60, 120]);
  assert.equal(result.interestDifference, 200); assert.equal(result.feeDifference, 60);
  assert.equal(compareScenario(b, a, year, '20000').interestDifference, -200);
  assert.equal(compareScenario(a, product('c', 2), year, '20000').interestDifference, 0);
  assert.ok(!('net' in result));
});
test('zero, empty, exponent, precision, minimum and upper bounds remain distinct', () => {
  const a = product(), b = product('b', 3);
  assert.equal(compareScenario(a, b, year, '0').interestDifference, 0);
  for (const input of ['', ' ', '-1', '1e4', 'NaN', 'Infinity', '1,000', '.5', '0.001', '1000000000000.01', '1'.repeat(33)]) {
    assert.equal(scenarioAmount(input), null, input);
    assert.equal(compareScenario(a, b, year, input).interestDifference, null, input);
  }
  assert.equal(scenarioInterest(a, year, '1000000000000').value, 20000000000);
  assert.equal(scenarioInterest(product('b', 2, { minimum_balance: 500 }), year, '499.99').reason, 'minimum');
  assert.equal(scenarioInterest(product('b', 2, { minimum_balance: 500 }), year, '500').value, 10);
  assert.equal(scenarioInterest(product('b', 2, { minimum_deposit: NaN }), year, '500').value, null);
  assert.equal(scenarioAmount(' 0.01 '), 0.01);
});
test('decimal half-cent rounding and displayed differences are exact', () => {
  assert.equal(scenarioInterest(product('a', 1), year, '100.50').value, 1.01);
  assert.equal(scenarioInterest(product('a', 0.0000001), year, '1000000000000').value, 1000);
  assert.equal(scenarioFee(product('a', 2, { public_display_fee: 10.29 }), { key: 'm3', months: 3, days: null }).value, 30.87);
  assert.equal(scenarioDifference({ value: 1.01, reason: null }, { value: 1.02, reason: null }), 0.01);
  assert.equal(scenarioInterest(product('a', 2), { key: 'm1', months: 1, days: null }, '20000').value, 33.33);
});
test('GIC uses each selected row rate, exact period and row minimum', () => {
  const a = gic('a'), b = gic('b', 12, 3);
  a.deposit_terms!.options.push({ key: 'm24', months: 24, days: null, rate: 4, minimum_deposit: 10000 });
  b.deposit_terms!.options.push({ key: 'm24', months: 24, days: null, rate: 5, minimum_deposit: 10000 });
  const twoYears = { key: 'm24', months: 24, days: null };
  assert.deepEqual(scenarioPeriods(a, b).map(p => p.key), ['m12', 'm24']);
  assert.equal(compareScenario(a, b, twoYears, '20000').interestDifference, 400);
  assert.equal(compareScenario(a, b, twoYears, '9999.99').interestDifference, null);
  assert.equal(compareScenario(a, gic('c', 6), year, '20000').reason, 'term_mismatch');
  const day = { key: 'd365', months: null, days: 365 };
  b.deposit_terms!.options = [{ ...day, rate: 3, minimum_deposit: 0 }];
  assert.equal(compareScenario(a, b, year, '20000').reason, 'term_mismatch');
  a.deposit_terms!.options = [{ ...day, rate: 2, minimum_deposit: 0 }];
  assert.equal(compareScenario(a, b, day, '20000').interestDifference, 200);
  assert.equal(compareScenario(a, b, { ...day, days: 360 }, '20000').reason, 'term_mismatch');
  assert.equal(scenarioInterest(a, { key: 'm0', months: 0, days: null }, '20000').value, null);
  assert.equal(scenarioInterest(a, { key: 'm12', months: 12, days: 365 }, '20000').value, null);
});
test('scope fails closed for currency, country, type, duplicate, inactive and absent periods', () => {
  const a = product();
  for (const overrides of [{ currency: 'USD' }, { currency: '' }, { country_code: 'US' }, { product_type: 'gic' }, { product_type: 'credit-card' }, { status: 'inactive' }]) {
    const b = product('b', 3, overrides);
    assert.ok(scenarioScope(a, b)); assert.equal(compareScenario(a, b, year, '20000').interestDifference, null);
    assert.equal(compareScenario(a, b, year, '20000').feeDifference, null);
  }
  assert.equal(scenarioScope(a, a), 'two_products');
  assert.equal(compareScenario(a, product('b'), undefined, '20000').reason, 'term_mismatch');
});
test('missing/conditional fees are never zero, and fees are independent of unsupported interest', () => {
  const a = product(), b = product('b', 3, { public_display_fee: null });
  assert.equal(compareScenario(a, b, year, '20000').feeDifference, null);
  for (const fee of [NaN, Infinity, -1, 0.001, 0.0000000001]) assert.equal(scenarioFee(product('b', 2, { public_display_fee: fee }), year).value, null);
  assert.equal(scenarioFee(product('b', 2, { fee_waiver_condition: 'Waived above 5000' }), year).reason, 'fee_conditional');
  assert.equal(scenarioFee(a, { key: 'd365', months: null, days: 365 }).reason, 'fee_period');
  const chequing = product('c', 2, { product_type: 'chequing', public_display_fee: 4 });
  assert.equal(scenarioInterest(chequing, year, '20000').value, null);
  assert.equal(scenarioFee(chequing, year).value, 48);
});
test('APY, APR/unknown basis, current/expired promotions, tiers, bonuses and compounding never supply interest', () => {
  for (const reason of ['promotional', 'tiered', 'compound', 'market_linked', 'variable', 'basis_unknown', 'conditions_unclear', 'term_conflict']) {
    const b = product('b'); b.deposit_terms!.reason = reason;
    assert.equal(compareScenario(product(), b, year, '20000').interestDifference, null, reason);
  }
  const apy = product('b'); apy.deposit_terms!.basis = 'apy';
  assert.equal(scenarioInterest(apy, year, '20000').reason, 'apy');
  const missing = product('b', 3, { deposit_terms: undefined });
  assert.equal(scenarioInterest(missing, year, '20000').reason, 'basis_unknown');
  const compound = product('b'); compound.deposit_terms!.calculation_reason = 'compound';
  assert.equal(scenarioInterest(compound, year, '20000').reason, 'compound');
  assert.equal(scenarioInterest(product('b', NaN), year, '20000').value, null);
});
test('comparison URL and saved schema accept identities only; arithmetic never mutates products', async () => {
  const a = product(), b = product('b'); const before = JSON.stringify(a); const hash = await comparisonFingerprint(a);
  compareScenario(a, b, year, '987654.32');
  assert.equal(JSON.stringify(a), before); assert.equal(await comparisonFingerprint(a), hash);
  const href = comparisonHref(['a', 'b'], { countryCode: 'CA', locale: 'en', amount: '987654.32' } as never);
  assert.ok(!href.includes('987654')); assert.deepEqual([...new URLSearchParams(href.split('?')[1]).keys()], ['product_id', 'product_id', 'country_code', 'locale']);
  const saved = readSavedComparison(JSON.stringify({ version: 1, countryCode: 'CA', amount: '987654.32', items: [{ id: 'a', fingerprint: hash, amount: '987654.32' }] }), 'CA');
  assert.ok(!JSON.stringify(saved).includes('987654'));
});
test('scenario UI copy has complete EN/KO/JA coverage', () => {
  assert.match(scenarioCopy('ko').title, /[가-힣]/); assert.match(scenarioCopy('ja').title, /[一-龯]/);
  for (const locale of ['en', 'ko', 'ja']) assert.deepEqual(Object.keys(scenarioCopy(locale).reasons), Object.keys(scenarioCopy('en').reasons));
});
