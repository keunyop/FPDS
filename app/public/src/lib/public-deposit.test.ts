import assert from 'node:assert/strict';
import test from 'node:test';
import type { PublicProduct, PublicProductsResponse } from './public-api.ts';
import { allProductPages, depositCopy, depositGroupKey, depositOptions, depositPeriod, depositRate, estimateDeposit, sameComparisonScope, startingDepositAmount } from './public-deposit.ts';
function product(overrides: Partial<PublicProduct> = {}): PublicProduct {
 return { product_id: 'a', product_type: 'savings', country_code: 'CA', currency: 'CAD', minimum_balance: 0, minimum_deposit: 0,
  deposit_terms: { version: 1, basis: 'annual', reason: null, calculation_reason: null, withdrawal: 'unknown',
   options: [{ key: 'ongoing', months: null, days: null, rate: 3, minimum_deposit: 0 }] }, ...overrides } as PublicProduct;
}
test('currency, country, type, annual basis and term are real comparison gates', () => {
 const current = product();
 assert.ok(sameComparisonScope(current, product({product_id:'b'}), 'ongoing'));
 for (const overrides of [{currency:'USD'}, {country_code:'US'}, {product_type:'gic'}, {deposit_terms:undefined}])
  assert.equal(sameComparisonScope(current, product(overrides), 'ongoing'), false);
 const apy = product(); apy.deposit_terms!.basis='apy';
 assert.equal(sameComparisonScope(current, apy, 'ongoing'), false);
 const gic = product({product_type:'gic'}); gic.deposit_terms!.withdrawal='non_redeemable';
 gic.deposit_terms!.options=[{key:'m12',months:12,days:null,rate:4,minimum_deposit:500}];
 const other = structuredClone(gic); other.deposit_terms!.options[0]={key:'d360',months:null,days:360,rate:5,minimum_deposit:500};
 assert.equal(sameComparisonScope(gic,other,'m12'),false);
 assert.notEqual(depositGroupKey(gic,gic.deposit_terms!.options[0]), depositGroupKey(other,other.deposit_terms!.options[0]));
 other.deposit_terms!.options=structuredClone(gic.deposit_terms!.options); other.deposit_terms!.withdrawal='redeemable';
 assert.equal(sameComparisonScope(gic,other,'m12'),false);
});
test('zero minimum starts at 10000; zero entered explicitly remains valid', () => {
 assert.equal(startingDepositAmount(0, null),10000);
 assert.equal(startingDepositAmount(20000, null),20000);
 const p=product();const o=depositOptions(p)[0];
 assert.equal(estimateDeposit(p,o,'10000',365),300);
 assert.equal(estimateDeposit(p,o,'0',365),0);
 assert.equal(estimateDeposit(p,o,'10000',30),24.66);
 for(const value of ['', ' ', '-1','1e4','Infinity','NaN','1,000','0.001','1000000000001']) assert.equal(estimateDeposit(p,o,value,365),null,value);
 for(const days of [0,-1,366,NaN,Infinity]) assert.equal(estimateDeposit(p,o,'10000',days),null);
});
test('estimates use the selected GIC row and respect its minimum', () => {
 const p=product({product_type:'gic'});p.deposit_terms!.options=[{key:'m18',months:18,days:null,rate:4,minimum_deposit:500}];
 const o=depositOptions(p)[0];
 assert.equal(estimateDeposit(p,o,'10000',365),600);
 assert.equal(estimateDeposit(p,o,'499.99',365),null);
 assert.equal(depositRate(p,'m18'),4);assert.equal(depositRate(p,'m12'),null);
});
test('promotions, APY, conflicts and old responses never fall back to headline arithmetic', () => {
 for(const reason of ['market_linked','promotional','term_conflict','tiered','basis_unknown']) {
  const p=product();p.deposit_terms!.reason=reason;
  assert.deepEqual(depositOptions(p),[]);assert.equal(estimateDeposit(p,p.deposit_terms!.options[0],'10000',365),null);
 }
 for(const reason of ['apy','compound']) {
  const p=product();p.deposit_terms!.calculation_reason=reason;
  assert.equal(estimateDeposit(p,depositOptions(p)[0],'10000',365),null);
 }
 assert.deepEqual(depositOptions(product({deposit_terms:undefined})),[]);
});
test('all locales have real localized reasons and period labels', () => {
 for(const locale of ['en','ko','ja']) {
  const copy=depositCopy(locale);assert.ok(!copy.title.includes('?'));assert.ok(!copy.reasons.market_linked.includes('?'));
  assert.ok(depositPeriod({key:'m12',months:12,days:null,rate:3,minimum_deposit:0},locale).includes('12'));
 }
 assert.match(depositCopy('ko').title, /[가-힣]/);assert.match(depositCopy('ja').title, /[一-龯]/);
});
test('complete pagination includes candidates after page one and rejects changed snapshots', async () => {
 const page=(n:number,snapshot='a')=>({items:[product({product_id:String(n)})],page:n,has_next_page:n===1,freshness:{snapshot_id:snapshot}} as PublicProductsResponse);
 assert.equal((await allProductPages(async n=>page(n))).items.length,2);
 await assert.rejects(()=>allProductPages(async n=>page(n,n===1?'a':'b')),/snapshot changed/);
 await assert.rejects(()=>allProductPages(async n=>{if(n===2)throw Error('API unavailable');return page(n);}),/API unavailable/);
});
