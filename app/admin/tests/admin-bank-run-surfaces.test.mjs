import assert from "node:assert/strict";
import test from "node:test";
import React from "react";
import { renderToStaticMarkup } from "react-dom/server";
import { loadComponent } from "./render-component.mjs";

const {BankRegistrySurface} = loadComponent("components/fpds/admin/bank-registry-surface.tsx");
const {BankDetailDialogContent} = loadComponent("components/fpds/admin/bank-detail-dialog-content.tsx");
const {BankCoverageSection} = loadComponent("components/fpds/admin/bank-coverage-section.tsx");
const {RunStatusSurface} = loadComponent("components/fpds/admin/run-status-surface.tsx");
const render = (Component, props) => renderToStaticMarkup(React.createElement(Component, props));
const coverage = {catalog_item_id:"qa-coverage", bank_code:"QA", bank_name:"QA Bank", country_code:"CA", product_type:"savings", status:"active", generated_source_count:8, has_completed_collection:true,
  collection_preparation:{status:"run_created",run_id:"private-run"}};
const bank = {bank_code:"QA",bank_name:"QA Bank",country_code:"CA",status:"active",source_language:"en",catalog_product_types:["savings"],catalog_items:[coverage],generated_source_count:8,published_product_count:3};
const productTypes = [{product_type_code:"savings",display_name:"Savings",description:"Savings accounts",status:"active"}];
const banksProps = locale => ({banks:{items:[bank],summary:{total_items:1},facets:{statuses:["active","inactive"]}},filters:{q:"",status:""},locale,csrfToken:null,activeBankCode:null,activeBankDetail:null,addModalOpen:false,aiAddModalOpen:false,countryCode:"CA",productTypes,userRole:"admin"});
const filters = {q:"",states:["started","completed","failed"],runType:"",partialOnly:false,startedFrom:"",startedTo:"",sortBy:"started_at",sortOrder:"desc",page:1};
const run = {run_id:"qa-run",run_status:"queued",run_type:"snapshot_capture",bank_code:"QA",product_type:"savings",trigger_type:"manual",started_at:"2026-10-04T16:00:00Z",source_item_count:8,success_count:0,failure_count:0,candidate_count:0,review_queued_count:0};
const runs = {items:[run],summary:{run_type_counts:{}},page:1,page_size:20,total_items:21,total_pages:2,has_next_page:true};

for (const [locale,label,refresh] of [["en","Published products","Auto refresh"],["ko","공개된 상품","자동 새로고침"],["ja","公開商品","自動更新"]]) {
  test(`Banks ${locale}: published count alongside sources, no per-type Run status, locale-preserving search`, () => {
    const html = render(BankRegistrySurface, banksProps(locale));
    assert.ok(html.includes(label));
    assert.match(html, new RegExp(`name="locale"[^>]*value="${locale}"`));
    assert.ok(!html.includes(refresh));
    assert.ok(!html.includes("private-run"));
    const row = html.match(/<tbody>(.*?)<\/tbody>/s)[1];
    const cells = [...row.matchAll(/<td\b[^>]*>(.*?)<\/td>/gs)].map(match=>match[1]);
    assert.equal(cells.length,5);
    assert.equal(cells.at(-2),"8");
    assert.equal(cells.at(-1).trim(),"3");
  });
  test(`Coverage ${locale}: still offers collection and sources without Run links`, () => {
    const html = render(BankCoverageSection,{bankCode:"QA",canManage:true,catalogItems:[coverage],csrfToken:null,locale,productTypes});
    assert.ok(html.includes(`/admin/sources?bank_code=QA&amp;product_type=savings${locale === "en" ? "" : `&amp;locale=${locale}`}`));
    assert.ok(!html.includes("private-run"));
    assert.ok(!html.includes("/admin/runs/"));
    assert.ok(html.includes('type="button"'));
  });
  test(`Runs ${locale}: refresh restored, filters initially closed with saved values and pagination`, () => {
    const html = render(RunStatusSurface,{locale,filters,runs});
    assert.ok(html.includes(refresh));
    assert.match(html, /<details[^>]*>/);
    assert.ok(!/<details[^>]*\bopen/.test(html));
    for (const state of filters.states) assert.match(html,new RegExp(`name="state"[^>]*checked=""[^>]*value="${state}"`));
    assert.ok(html.includes("page=2"));
    assert.match(html, new RegExp(`name="locale"[^>]*value="${locale}"`));
    const advanced = render(RunStatusSurface,{locale,filters:{...filters,startedFrom:"2026-10-01",states:["failed"],sortOrder:"asc"},runs});
    assert.ok(!/<details[^>]*\bopen/.test(advanced));
    const dateInput = advanced.match(/<input[^>]*name="started_from"[^>]*>/)[0];
    assert.ok(dateInput.includes('value="2026-10-01"'));
    assert.ok(dateInput.includes('type="date"'));
  });
}

test("Banks distinguishes a proven zero count from an older API with no count", () => {
  for (const [count,expected] of [[0,"0"],[undefined,"—"]]) {
    const props = banksProps("en");props.banks.items=[{...bank,published_product_count:count}];
    const html=render(BankRegistrySurface,props);
    assert.equal([...html.matchAll(/<td\b[^>]*>(.*?)<\/td>/gs)].at(-1)[1].trim(),expected);
  }
  const props=banksProps("en");props.banks.items=[];
  assert.match(render(BankRegistrySurface,props), /colSpan="5"/i);
});

test("Runs terminal and empty states retain localized diagnostics and reset actions", () => {
  for (const locale of ["en","ko","ja"]) {
    const html=render(RunStatusSurface,{locale,filters,runs:{...runs,items:[{...run,run_status:"failed",error_summary:"Official source unavailable",failure_count:1},{...run,run_id:"skip",run_status:"skipped",preparation_reason_codes:["no_eligible_detail"]}]}});
    assert.ok(html.includes("Official source unavailable"));
    assert.ok(html.includes("bg-warning-soft"));
    const empty=render(RunStatusSurface,{locale,filters,runs:{...runs,items:[],total_items:0,total_pages:0,has_next_page:false}});
    assert.ok(empty.includes(`href="/admin/runs${locale === "en" ? "" : `?locale=${locale}`}"`));
    assert.ok(!empty.includes("qa-run"));
  }
});


test("Read-only Banks users can inspect identity, coverage and source links without mutation controls", () => {
  for (const [locale,add,collect,save,remove] of [["en","Add bank","Collect selected","Save bank","Delete bank"],["ko","은행 추가","선택 항목 수집","은행 저장","은행 삭제"],["ja","銀行を追加","選択項目を収集","銀行を保存","銀行を削除"]]) {
    const list=render(BankRegistrySurface,{...banksProps(locale),userRole:"read_only",addModalOpen:true});
    assert.ok(!list.includes(add)); assert.ok(!list.includes(collect));
    assert.ok(!list.includes('type="checkbox"'));
    const detail=render(BankDetailDialogContent,{canManage:false,detail:{bank,catalog_items:[coverage]},locale,csrfToken:null,productTypes});
    assert.ok(detail.includes("QA Bank")); assert.match(detail,/<fieldset[^>]*disabled/);
    assert.ok(!detail.includes(save)); assert.ok(!detail.includes(remove));
    assert.ok(detail.includes("/admin/sources?"));
    assert.ok(!detail.includes('type="submit"'));
  }
});

test("Bank detail profile inputs expose matching label associations and localized logo fields", () => {
  for (const [locale,logo] of [["en","Logo preview"],["ko","로고 미리보기"],["ja","ロゴプレビュー"]]) {
    const html=render(BankDetailDialogContent,{canManage:true,detail:{bank,catalog_items:[coverage]},locale,csrfToken:null,productTypes});
    assert.ok(html.includes(logo));
    const labelIds=[...html.matchAll(/<label[^>]*for="([^"]+)"/g)].map(match=>match[1]);
    assert.ok(labelIds.length>=3);
    for (const id of labelIds) assert.ok(html.includes(`id="${id}"`));
  }
});
