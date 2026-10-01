import type { PublicProduct } from './public-api.ts';

const copy = {
 en: { costs: 'Transaction costs', each: 'per transaction', extra: 'per extra transaction', included: 'included / month', unlimited: 'Unlimited transactions', withdrawal: 'Early withdrawal', blocked: 'Not permitted before maturity', allowed: 'Permitted', missing: 'Unavailable' },
 ko: { costs: '\uac70\ub798 \ube44\uc6a9', each: '\uac70\ub798\ub2f9', extra: '\ucd08\uacfc \uac70\ub798\ub2f9', included: '\uac74 / \uc6d4 \ud3ec\ud568', unlimited: '\uac70\ub798 \ud69f\uc218 \ubb34\uc81c\ud55c', withdrawal: '\uc911\ub3c4 \uc778\ucd9c', blocked: '\ub9cc\uae30 \uc804 \uc778\ucd9c \ubd88\uac00', allowed: '\uc911\ub3c4 \uc778\ucd9c \uac00\ub2a5', missing: '\ud655\uc778 \ubd88\uac00' },
 ja: { costs: '\u53d6\u5f15\u8cbb\u7528', each: '\u53d6\u5f15\u3054\u3068', extra: '\u8d85\u904e\u53d6\u5f15\u3054\u3068', included: '\u56de / \u6708\u3092\u542b\u3080', unlimited: '\u53d6\u5f15\u56de\u6570\u7121\u5236\u9650', withdrawal: '\u4e2d\u9014\u5f15\u51fa\u3057', blocked: '\u6e80\u671f\u524d\u306e\u5f15\u51fa\u3057\u4e0d\u53ef', allowed: '\u4e2d\u9014\u5f15\u51fa\u3057\u53ef\u80fd', missing: '\u78ba\u8a8d\u4e0d\u53ef' }
};
export function accessCopy(locale: string) { return copy[locale === 'ko' || locale === 'ja' ? locale : 'en']; }
export function transactionCosts(product: PublicProduct, locale: string) {
 const c = accessCopy(locale);
 if (product.unlimited_transactions_flag === true) return c.unlimited;
 const money = (value: number) => new Intl.NumberFormat(locale === 'ko' ? 'ko-KR' : locale === 'ja' ? 'ja-JP' : 'en-CA', { style: 'currency', currency: product.currency }).format(value);
 const count = product.included_transactions;
 const fee = count != null ? product.additional_transaction_fee ?? product.transaction_fee : product.transaction_fee;
 if (count != null) return `${count} ${c.included}; ${fee != null ? money(fee) : c.missing} ${c.extra}`;
 return fee != null ? `${money(fee)} ${c.each}` : c.missing;
}
export function withdrawalConditions(product: PublicProduct, locale: string) {
 const c = accessCopy(locale);
 const access = product.redeemable_flag ?? (product.non_redeemable_flag == null ? null : !product.non_redeemable_flag);
 if (access === false) return c.blocked;
 if (access === true) return `${c.allowed}; ${product.early_withdrawal_penalty || c.missing}`;
 return c.missing;
}
