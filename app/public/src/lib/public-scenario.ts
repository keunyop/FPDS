import type { PublicProduct } from './public-api.ts';
import { depositOptions, type DepositOption } from './public-deposit.ts';

export type ScenarioPeriod = { key: string; months: number | null; days: number | null };
export type ScenarioValue = { value: number | null; reason: string | null };
const unavailable = (reason: string): ScenarioValue => ({ value: null, reason });
const valid = (value: number): ScenarioValue => ({ value, reason: null });
const finite = (value: unknown): value is number => typeof value === 'number' && Number.isFinite(value) && value >= 0;
export const SCENARIO_MONTHS = [1, 3, 6, 12];

export function scenarioScope(a: PublicProduct, b: PublicProduct): string | null {
  if (a.product_id === b.product_id) return 'two_products';
  if (a.status !== 'active' || b.status !== 'active') return 'inactive';
  if (a.country_code !== b.country_code || !/^[A-Z]{3}$/.test(a.currency) || a.currency !== b.currency) return 'currency_mismatch';
  if (a.product_type !== b.product_type || !['chequing', 'savings', 'gic'].includes(a.product_type)) return 'type_mismatch';
  return null;
}
function exactPeriod(option: ScenarioPeriod) {
  return (Number.isInteger(option.months) && option.months! > 0 && option.months! <= 120 && option.days === null && option.key === `m${option.months}`)
    || (Number.isInteger(option.days) && option.days! > 0 && option.days! <= 3650 && option.months === null && option.key === `d${option.days}`);
}
export function scenarioPeriods(a: PublicProduct, b: PublicProduct): ScenarioPeriod[] {
  if (scenarioScope(a, b)) return [];
  if (a.product_type !== 'gic') return SCENARIO_MONTHS.map(months => ({ key: `m${months}`, months, days: null }));
  return depositOptions(a).filter(exactPeriod).filter(option => depositOptions(b).some(other => other.key === option.key
    && other.months === option.months && other.days === option.days)).map(({ key, months, days }) => ({ key, months, days }));
}
export function scenarioAmount(input: string): number | null {
  if (input.length > 32 || !/^\d+(?:\.\d{1,2})?$/.test(input.trim())) return null;
  const value = Number(input);
  return finite(value) && value <= 1e12 ? value : null;
}
// Exact decimal arithmetic, including tiny rates serialized in exponent notation.
function fraction(value: number): [bigint, bigint] {
  const [mantissa, exponent = '0'] = String(value).split('e');
  const places = (mantissa.split('.')[1]?.length ?? 0) - Number(exponent);
  const digits = BigInt(mantissa.replace('.', ''));
  return places >= 0 ? [digits, BigInt(10) ** BigInt(places)] : [digits * BigInt(10) ** BigInt(-places), BigInt(1)];
}
function roundedProduct(values: number[], denominator: number) {
  let numerator = BigInt(100), divisor = BigInt(denominator);
  for (const value of values) { const [n, d] = fraction(value); numerator *= n; divisor *= d; }
  const cents = (numerator * BigInt(2) + divisor) / (divisor * BigInt(2));
  return cents <= BigInt(Number.MAX_SAFE_INTEGER) ? Number(cents) / 100 : null;
}
export function scenarioInterest(product: PublicProduct, period: ScenarioPeriod, input: string): ScenarioValue {
  if (!['savings', 'gic'].includes(product.product_type)) return unavailable('interest_unsupported');
  const terms = product.deposit_terms;
  if (!terms || terms.version !== 1) return unavailable('basis_unknown');
  if (terms.reason || terms.calculation_reason) return unavailable(terms.reason ?? terms.calculation_reason!);
  if (terms.basis !== 'annual') return unavailable(terms.basis === 'apy' ? 'apy' : 'basis_unknown');
  if (!exactPeriod(period)) return unavailable('term_unknown');
  const option: DepositOption | undefined = depositOptions(product).find(item => item.key === (product.product_type === 'gic' ? period.key : 'ongoing'));
  if (!option || (product.product_type === 'gic' && (option.months !== period.months || option.days !== period.days))) return unavailable('term_conflict');
  if (product.product_type === 'savings' && (period.days !== null || !SCENARIO_MONTHS.includes(period.months!))) return unavailable('term_unknown');
  const amount = scenarioAmount(input);
  if (amount === null) return unavailable('amount_invalid');
  const minimums = [product.minimum_balance, product.minimum_deposit, option.minimum_deposit];
  if (minimums.some(value => value != null && !finite(value))) return unavailable('conditions_unclear');
  if (amount < Math.max(0, ...minimums.filter(finite))) return unavailable('minimum');
  const result = roundedProduct([amount, option.rate, period.months ?? period.days!], 100 * (period.months !== null ? 12 : 365));
  return result === null ? unavailable('amount_invalid') : valid(result);
}
export function scenarioFee(product: PublicProduct, period: ScenarioPeriod): ScenarioValue {
  // public_display_fee is the approved monthly fee only for these account types.
  if (!['chequing', 'savings'].includes(product.product_type)) return unavailable('fee_unknown');
  if (product.fee_waiver_condition?.trim() || product.deposit_terms?.reason === 'promotional') return unavailable('fee_conditional');
  const fee = product.public_display_fee;
  if (!finite(fee) || fee > 1e12) return unavailable('fee_unknown');
  const [feeNumerator, feeDenominator] = fraction(fee);
  if (feeNumerator * BigInt(100) % feeDenominator !== BigInt(0)) return unavailable('fee_unknown');
  if (!exactPeriod(period) || period.months === null) return unavailable('fee_period');
  const result = roundedProduct([fee, period.months], 1);
  return result === null ? unavailable('fee_unknown') : valid(result);
}
export function scenarioDifference(a: ScenarioValue, b: ScenarioValue): number | null {
  return a.value === null || b.value === null ? null : (Math.round(b.value * 100) - Math.round(a.value * 100)) / 100;
}
export function compareScenario(a: PublicProduct, b: PublicProduct, period: ScenarioPeriod | undefined, input: string) {
  const reason = scenarioScope(a, b) ?? (!period || !scenarioPeriods(a, b).some(p => p.key === period.key && p.months === period.months && p.days === period.days) ? (a.product_type === 'gic' ? a.deposit_terms?.reason ?? b.deposit_terms?.reason ?? 'term_mismatch' : 'term_mismatch') : null);
  const interest = reason ? [unavailable(reason), unavailable(reason)] : [scenarioInterest(a, period!, input), scenarioInterest(b, period!, input)];
  const fees = reason ? [unavailable(reason), unavailable(reason)] : [scenarioFee(a, period!), scenarioFee(b, period!)];
  return { reason, interest, fees, interestDifference: scenarioDifference(interest[0], interest[1]), feeDifference: scenarioDifference(fees[0], fees[1]) };
}
