import assert from 'node:assert/strict';
import test from 'node:test';
import type { PublicProduct, PublicProductsResponse } from './public-api.ts';
import { buildCuratedComparison, curatedHref, curatedCatalogHref, curatedCountryPath, isCuratedIndexableQuery, isCuratedSlug, loadCuratedProducts } from './public-curated.ts';
import { curatedCopy } from './public-curated-copy.ts';
const NOW = Date.parse('2026-09-25T12:00:00Z');
function product(id: string, overrides: Partial<PublicProduct> = {}): PublicProduct {
  return { product_id: id, bank_code: id, bank_name: id, product_name: id, country_code: 'CA', currency: 'CAD', product_type: 'savings', status: 'active', product_url: `https://${id}.example/account`,
    public_display_fee: 0, fee_waiver_condition: null, last_verified_at: '2026-09-20T00:00:00Z',
    verification: { status: 'within_window', last_verified_at: '2026-09-20T00:00:00Z', review_due_at: '2026-09-27T00:00:00Z', expires_at: '2026-10-20T00:00:00Z', review_interval_days: 7, expiry_days: 30, evaluated_at: '2026-09-25T00:00:00Z' },
    deposit_terms: { version: 1, basis: 'annual', reason: null, calculation_reason: null, withdrawal: 'unknown', options: [{ key: 'ongoing', months: null, days: null, rate: 2, minimum_deposit: 0 }] },
    ...overrides } as PublicProduct;
}
const savings = () => ['a','b','c'].map(id => product(id));
const ids = (result: ReturnType<typeof buildCuratedComparison>, group: string) => result.groups.find(g => g.key === group)?.products.map(p => p.product_id) ?? [];
function gic(id: string, withdrawal: 'redeemable' | 'non_redeemable' | 'unknown' = 'non_redeemable') {
  const p = product(id, { product_type: 'gic' }); p.deposit_terms!.withdrawal = withdrawal;
  p.deposit_terms!.options = [{ key: 'm12', months: 12, days: null, rate: 2, minimum_deposit: 1000 }]; return p;
}
function response(items: PublicProduct[], overrides: Partial<PublicProductsResponse> = {}): PublicProductsResponse {
  return {items, page: 1, page_size: 100, total_items: items.length, total_pages: 1, has_next_page: false, freshness: {snapshot_id: 'one', status: 'stale'}, ...overrides} as PublicProductsResponse;
}

test('readiness requires three distinct banks with active CA CAD products and safe official links', () => {
  assert.equal(buildCuratedComparison('savings-accounts', savings(), NOW).ready, true);
  for (const override of [{ bank_code: 'a' }, { country_code: 'US' }, { currency: 'USD' }, { status: 'inactive' }, { product_url: null }, { product_url: 'javascript:alert(1)' }, { product_url: 'https://user:pass@bank.example' }, { bank_code: '' }]) {
    assert.equal(buildCuratedComparison('savings-accounts', [product('a'), product('b'), product('c', override)], NOW).ready, false, JSON.stringify(override));
  }
  assert.equal(buildCuratedComparison('savings-accounts', [...savings().slice(0,2), product('a')], NOW).ready, false);
});

test('unknown, expired and future verification cannot launch a curated page; due remains visibly eligible', () => {
  for (const value of [undefined, { ...product('x').verification!, status: 'unknown' as const }, { ...product('x').verification!, expires_at: new Date(NOW).toISOString() }, { ...product('x').verification!, last_verified_at: '2026-10-01T00:00:00Z' }]) {
    assert.equal(buildCuratedComparison('savings-accounts', [product('a'), product('b'), product('c', { verification: value })], NOW).ready, false);
  }
  const due = product('c'); due.verification!.review_due_at = new Date(NOW).toISOString();
  assert.equal(buildCuratedComparison('savings-accounts', [product('a'), product('b'), due], NOW).ready, true);
});

test('chequing separates explicit zero base fees and positive fees with source waiver conditions', () => {
  const rows = ['a','b','c'].map(id => product(id, { product_type: 'chequing' }));
  rows.push(product('waiver', { product_type: 'chequing', public_display_fee: 15, fee_waiver_condition: 'Keep CAD 5,000' }));
  for (const [id,fee,condition] of [['ambiguous',0,'Keep 5,000'],['unknown',null,null],['negative',-1,null],['invalid',NaN,null],['paid',15,null]] as const)
    rows.push(product(id, { product_type: 'chequing', public_display_fee: fee, fee_waiver_condition: condition }));
  const result = buildCuratedComparison('no-monthly-fee-chequing', rows, NOW);
  assert.equal(result.ready, true); assert.deepEqual(ids(result,'zero'),['a','b','c']); assert.deepEqual(ids(result,'waiver'),['waiver']);
  assert.equal(buildCuratedComparison('no-monthly-fee-chequing', rows.slice(2), NOW).ready, false);
});

test('Savings groups never mix annual and APY, or promote qualified offers into base rates', () => {
  const apy = product('apy'); apy.deposit_terms!.basis = 'apy';
  const promo = product('promo', { rate: { kind: 'promotional', comparable_rate: null, source_text: '5% for 90 days' } }); promo.deposit_terms!.reason = 'promotional';
  let result = buildCuratedComparison('savings-accounts', [product('a'),product('b'),apy,promo], NOW);
  assert.equal(result.ready,false);
  result = buildCuratedComparison('savings-accounts', [...savings(),apy,promo], NOW);
  assert.equal(result.ready,true);assert.deepEqual(ids(result,'annual'),['a','b','c']);assert.deepEqual(ids(result,'qualified'),['promo']);assert.deepEqual(ids(result,'apy'),[]);
  for (const reason of ['tiered','market_linked','basis_unknown','term_conflict']) {
    const bad=product('c');bad.deposit_terms!.reason=reason;
    assert.equal(buildCuratedComparison('savings-accounts',[product('a'),product('b'),bad],NOW).ready,false);
  }
});

test('GIC requires a single exact m12 row with matched basis/redemption and three banks per group', () => {
  const rows=['a','b','c'].map(id=>gic(id));
  assert.equal(buildCuratedComparison('1-year-gic',rows,NOW).ready,true);
  for (const option of [
    {key:'d360',months:null,days:360,rate:9,minimum_deposit:0},
    {key:'m24',months:24,days:null,rate:9,minimum_deposit:0},
    {key:'m12',months:12,days:365,rate:9,minimum_deposit:0},
    {key:'m12',months:12,days:null,rate:Infinity,minimum_deposit:0}
  ]) { const bad=gic('c');bad.deposit_terms!.options=[option]; assert.equal(buildCuratedComparison('1-year-gic',[rows[0],rows[1],bad],NOW).ready,false); }
  for(const withdrawal of ['redeemable','unknown'] as const) assert.equal(buildCuratedComparison('1-year-gic',[rows[0],rows[1],gic('c',withdrawal)],NOW).ready,false);
  const apy=gic('c');apy.deposit_terms!.basis='apy';assert.equal(buildCuratedComparison('1-year-gic',[rows[0],rows[1],apy],NOW).ready,false);
  const duplicate=gic('c');duplicate.deposit_terms!.options.push({...duplicate.deposit_terms!.options[0],rate:9});assert.equal(buildCuratedComparison('1-year-gic',[rows[0],rows[1],duplicate],NOW).ready,false);
});

test('complete snapshot loader rejects later failures, missing/duplicate rows, snapshot changes and page drift', async () => {
  const pages = [response([product('a')], {total_items:2,total_pages:2,has_next_page:true}),response([product('b')],{page:2,total_items:2,total_pages:2})];
  assert.deepEqual((await loadCuratedProducts(async page=>pages[page-1])).map(p=>p.product_id),['a','b']);
  await assert.rejects(loadCuratedProducts(async page=>{if(page===2) throw new Error('offline');return pages[0];}));
  for(const override of [ {page:1}, {items:[]}, {items:[product('a')]}, {total_items:3}, {freshness:{snapshot_id:'changed',status:'stale'}} ] as Partial<PublicProductsResponse>[])
    await assert.rejects(loadCuratedProducts(async page=>page===1?pages[0]:{...pages[1],...override}));
  await assert.rejects(loadCuratedProducts(async()=>response([product('a')],{total_items:2})));
  await assert.rejects(loadCuratedProducts(async()=>response([], {freshness:{snapshot_id:null,status:'unavailable'}} as Partial<PublicProductsResponse>)));
  assert.deepEqual(await loadCuratedProducts(async()=>response([])),[]);
});

test('only curated slugs and clean locale URLs index; country switches leave Canada routes', () => {
  assert.ok(isCuratedSlug('savings-accounts')); assert.ok(!isCuratedSlug('toString'));assert.ok(!isCuratedSlug('best-rates'));
  assert.ok(isCuratedIndexableQuery({}));
  for(const locale of ['en','ko','ja']) {assert.ok(isCuratedIndexableQuery({locale}));assert.ok(curatedCopy(locale).pages['1-year-gic'].title);}
  for(const query of [{q:'bank'}, {sort_by:'display_rate'}, {country_code:'US'}, {country_code:'CA'}, {locale:['en','ko']}, {locale:'fr'}]) assert.ok(!isCuratedIndexableQuery(query));
  assert.equal(curatedHref('savings-accounts','ko'),'/ca/savings-accounts?locale=ko');
  assert.equal(curatedCountryPath('/ca/savings-accounts','US'),'/products');
  assert.equal(curatedCountryPath('/ca/savings-accounts','CA'),'/ca/savings-accounts');
  assert.equal(curatedCountryPath('/cards','US'),'/cards');
  assert.ok(curatedCatalogHref('1-year-gic','ja','US').includes('country_code=US'));
});

test('curated rows honor confirmed canonical duplicates and exact-source duplicate facts without merging variants', () => {
  const rows = ['a','b','c'].map(id=>product(id,{product_type:'chequing'}));
  const duplicate = {...rows[0],product_id:'duplicate',product_name:'Another source title'};
  const variant = {...rows[0],product_id:'variant',public_display_fee:15,fee_waiver_condition:'Keep 5,000'};
  const retiredAlias=product('prod_LuH-Kei2S8uFFOyY',{product_type:'chequing'});
  const result=buildCuratedComparison('no-monthly-fee-chequing',[...rows,duplicate,variant,retiredAlias],NOW);
  assert.equal(result.ready,true);assert.deepEqual(ids(result,'zero'),['a','b','c']);assert.deepEqual(ids(result,'waiver'),['variant']);
});
