import type { PublicProduct } from './public-api.ts';

const money = (value: unknown): value is number => typeof value === 'number' && Number.isFinite(value) && value >= 0;
const text = (value: unknown): value is string => typeof value === 'string' && Boolean(value.trim());
const term = (product: PublicProduct) => text(product.term_length_text)
  || (Number.isInteger(product.term_length_days) && product.term_length_days! > 0);

/** Defensive checks for older projections; optional omissions never narrow a ranking. */
export function hasRankingEssentials(product: PublicProduct): boolean {
  switch (product.product_type) {
    case 'chequing': {
      if (!money(product.public_display_fee)) return false;
      if (product.unlimited_transactions_flag === true) return product.included_transactions == null;
      if (product.included_transactions != null) {
        return Number.isInteger(product.included_transactions) && product.included_transactions >= 0
          && money(product.additional_transaction_fee ?? product.transaction_fee);
      }
      return money(product.transaction_fee);
    }
    case 'savings':
      return money(product.public_display_fee);
    case 'gic': {
      if (typeof product.redeemable_flag === 'boolean' && typeof product.non_redeemable_flag === 'boolean'
        && product.redeemable_flag === product.non_redeemable_flag) return false;
      const access = typeof product.redeemable_flag === 'boolean' ? product.redeemable_flag
        : typeof product.non_redeemable_flag === 'boolean' ? !product.non_redeemable_flag : null;
      if (access === null || (access && !text(product.early_withdrawal_penalty))) return false;
      return product.deposit_terms?.withdrawal === (access ? 'redeemable' : 'non_redeemable');
    }
    case 'mortgage':
      return text(product.rate_type) && term(product);
    case 'personal-loan':
      return term(product);
    case 'line-of-credit': {
      const meanings = [securityMeaning(product.security_requirement), securityMeaning(product.collateral_text)];
      if (typeof product.secured_flag === 'boolean') meanings.push(product.secured_flag);
      return meanings.some(value => value !== null) && !(meanings.includes(true) && meanings.includes(false));
    }
    default:
      return false;
  }
}

/** Mirror fpds_approval_policy.security_meaning; no new source-language acceptance patterns. */
function securityMeaning(value: unknown): boolean | null {
  if (typeof value !== 'string' || /\b(?:may|might|could|optional|depending)\b|not unsecured/i.test(value)) return null;
  const unsecured = /\bunsecured\b|no collateral (?:is )?required|\bnot secured\b/i.test(value);
  const positiveContext = value.replace(/\bnot secured\b|\bno collateral (?:is )?required\b/gi, '');
  const secured = /(?<!un)\bsecured\b|\bcollateral (?:is )?required\b/i.test(positiveContext);
  return secured === unsecured ? null : secured;
}
