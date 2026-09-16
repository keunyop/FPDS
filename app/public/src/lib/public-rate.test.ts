import assert from 'node:assert/strict';
import test from 'node:test';
import { getComparablePublicRate, getPublicRateMetric, getRateComparisonUnavailable, type PublicRate } from './public-rate.ts';

test('only explicit full rates including zero drive arithmetic', () => {
  for (const value of [0, 0.5, 6.625, 100]) {
    assert.equal(getComparablePublicRate({ rate: { kind: 'absolute', comparable_rate: value, source_text: null } }), value);
  }
  for (const value of [NaN, Infinity, -1, 101, null]) {
    assert.equal(getComparablePublicRate({ rate: { kind: 'absolute', comparable_rate: value, source_text: null } }), null);
  }
  assert.equal(getComparablePublicRate({}), null, 'old cached API responses fail closed');
});

test('qualified rates never drive arithmetic even if a response includes a scalar', () => {
  for (const kind of ['reference', 'range', 'conditional', 'promotional', 'unknown'] as PublicRate['kind'][]) {
    assert.equal(getComparablePublicRate({ rate: { kind, comparable_rate: .5, source_text: 'Prime plus .5%' } }), null);
  }
});

test('source conditions and rate categories are visible in EN, KO and JA', () => {
  const source = 'Variable low-interest rate based on BMO’s Prime Rate plus 0.5% while you’re in school.';
  for (const locale of ['en', 'ko', 'ja']) {
    const metric = getPublicRateMetric({ rate: { kind: 'reference', comparable_rate: null, source_text: source } }, locale);
    assert.equal(metric.value, source);
    assert.notEqual(metric.label, getPublicRateMetric({ rate: { kind: 'absolute', comparable_rate: .5, source_text: null } }, locale).label);
    assert.ok(getRateComparisonUnavailable(locale));
    assert.equal(getPublicRateMetric({ rate: { kind: 'absolute', comparable_rate: 6.625, source_text: null } }, locale).value, '6.625%');
  }
});

test('an old response retains qualifying summary without guessing a full rate', () => {
  assert.equal(getPublicRateMetric({ interest_rate_summary: 'Prime minus .25%' }, 'en').value, 'Prime minus .25%');
});
