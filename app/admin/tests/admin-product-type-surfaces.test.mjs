import assert from "node:assert/strict";
import test from "node:test";
import React from "react";
import { renderToStaticMarkup } from "react-dom/server";
import { loadComponent } from "./render-component.mjs";

const { ProductTypeCollectionFields } = loadComponent("components/fpds/admin/product-type-collection-fields.tsx");
const { ProductTypeDetailDialogContent } = loadComponent("components/fpds/admin/product-type-detail-dialog-content.tsx");
const { ProductTypeRegistrySurface } = loadComponent("components/fpds/admin/product-type-registry-surface.tsx");
const render = (Component, props) => renderToStaticMarkup(React.createElement(Component, props));
const configuration = {
  country_code: "CA", configured: false,
  required_fields: ["product_name", "currency", "monthly_fee", "transactions_included", "unlimited_transactions_flag", "additional_transaction_fee"],
  optional_fields: ["minimum_balance", "notes"],
  locked_required_fields: ["product_name", "currency", "monthly_fee", "transactions_included", "unlimited_transactions_flag", "additional_transaction_fee"],
  requirements: [{key:"monthly_fee",alternatives:["monthly_fee"],required_when:"always"},
    {key:"transaction_structure", alternatives:["transactions_included","unlimited_transactions_flag"],required_when:"always"},
    {key:"excess_transaction_cost", alternatives:["additional_transaction_fee"],required_when:"limited_transactions"}],
  field_catalog: ["product_name","currency","monthly_fee","transactions_included","unlimited_transactions_flag","additional_transaction_fee","minimum_balance","notes","eligibility_text"].map(field_key =>
    ({field_key,value_type:field_key.endsWith("flag") ? "boolean" : field_key === "notes" || field_key === "eligibility_text" ? "string" : "decimal", unit:field_key.includes("fee") || field_key === "minimum_balance" ? "currency_amount" : null})),
};
const item = {product_type_code:"chequing", product_family:"deposit", display_name:"Chequing", description:"Source-language type description",status:"active",managed_flag:true,discovery_keywords:["chequing"],expected_fields:configuration.required_fields,fallback_policy:"guarded_generic",created_at:null,updated_at:null,collection_fields:configuration};
const registry = {items:[item],summary:{total_items:1,status_counts:{active:1}},facets:{statuses:["active","inactive"]}};

for (const [locale,required,optional,condition] of [["en","Required information","Optional information","When the transaction allowance is limited"],
  ["ko","필수 수집 정보","선택 수집 정보","포함 거래 횟수가 제한된 경우"],
  ["ja","必須の収集情報","任意の収集情報","無料取引回数に上限がある場合"]]) {
  test(`Collection fields ${locale}: protected grouped alternatives and typed editable targets`, () => {
    const html = render(ProductTypeCollectionFields,{configuration,selection:configuration,disabled:false,locale,onChange(){}});
    assert.ok(html.includes(required));assert.ok(html.includes(optional));assert.ok(html.includes(condition));
    assert.match(html,/currency_amount/);
    assert.equal((html.match(/<select\b/g) ?? []).length,3,"only unlocked registered fields have controls");
    assert.equal((html.match(/<option value="optional" selected=""/g) ?? []).length,2);
    assert.equal((html.match(/<option value="omit" selected=""/g) ?? []).length,1);
    assert.ok(!html.includes('<option value="required" selected=""'));
    for (const match of html.matchAll(/<select[^>]*id="([^"]+)"[^>]*>/g)) assert.ok(html.includes(`for="${match[1]}"`));
    assert.ok(!/<details[^>]*\bopen/.test(html));
  });

  test(`Product Types ${locale}: admin registry controls and locale-preserving search`, () => {
    const html=render(ProductTypeRegistrySurface,{productTypes:registry,filters:{q:"",status:""},canManage:true,csrfToken:"fixture",locale,addModalOpen:false,activeProductTypeCode:null,activeProductType:null});
    assert.match(html,new RegExp(`name="locale"[^>]*value="${locale}"`));
    assert.ok(html.includes("Chequing"));
    const readonly=render(ProductTypeRegistrySurface,{productTypes:registry,filters:{q:"",status:""},canManage:false,csrfToken:"fixture",locale,addModalOpen:true,activeProductTypeCode:null,activeProductType:null});
    assert.ok(!readonly.includes({en:"Add product type",ko:"상품 유형 추가",ja:"商品タイプを追加"}[locale]));
  });
}

test("read-only Product Type detail shows collection rules but no mutation action", () => {
  const html=render(ProductTypeDetailDialogContent,{productType:item,canManage:false,csrfToken:"fixture",locale:"en"});
  assert.ok(html.includes("Required information"));assert.ok(html.includes("Source-language type description"));
  assert.ok(!html.includes("Save product type"));assert.ok(!html.includes("Delete product type"));
  for (const match of html.matchAll(/<(input|select|textarea)\b[^>]*>/g)) {
    if (!match[0].includes('type="search"')) assert.ok(match[0].includes('disabled=""'),match[0]);
  }
});

test("pristine detail is clean, save is disabled and associated profile labels remain accessible", () => {
  const html=render(ProductTypeDetailDialogContent,{productType:item,canManage:true,csrfToken:"fixture",locale:"en"});
  assert.ok(html.includes('data-admin-dirty="false"'));
  assert.match(html,/<button[^>]*disabled=""[^>]*>Save product type<\/button>/);
  for (const match of html.matchAll(/<(input|textarea)\b[^>]*id="([^"]+)"[^>]*>/g)) assert.ok(html.includes(`for="${match[2]}"`));
});

test("older API omits collection settings without fabricating empty editable arrays", () => {
  const html=render(ProductTypeDetailDialogContent,{productType:{...item,collection_fields:undefined},canManage:true,csrfToken:"fixture",locale:"en"});
  assert.ok(html.includes("Collection settings are unavailable"));
  assert.ok(!html.includes("Optional &amp; additional information"));
  assert.equal((html.match(/<select\b/g) ?? []).length,1,"only profile status remains editable");
});
