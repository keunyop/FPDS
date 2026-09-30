import assert from "node:assert/strict";
import test from "node:test";
import { collectionPreflightMessage, collectionPreparationMessage } from "../src/lib/admin-collection-feedback.ts";

const skipped = [{catalog_item_id:"one", bank_code:"BANK", product_type:"savings",
  reason_codes:["review_deferred"], revalidation:"precision_rediscovery"}];

test("old responses retain existing collection feedback", () => {
  assert.equal(collectionPreflightMessage("en", undefined), null);
  assert.equal(collectionPreflightMessage("ko", {run_ids:["run"], skipped_items:[]}), null);
});

test("all skipped and mixed launches report actual runs and revalidation in every locale", () => {
  for (const [locale, reason, retry] of [["en", "previously deferred review", "precision rediscovery"],
    ["ko", "이전 review 보류", "정밀 재탐색"], ["ja", "以前のレビュー保留", "精密再探索"]]) {
    for (const run_ids of [[], ["run"]]) {
      const text = collectionPreflightMessage(locale, {run_ids, skipped_items:skipped});
      assert.ok(text.includes(reason)); assert.ok(text.includes(retry));
      assert.ok(text.includes("BANK")); assert.ok(text.includes(String(run_ids.length)));
    }
  }
});

test("unknown reason codes do not expose internal implementation details", () => {
  const text = collectionPreflightMessage("en", {run_ids:[], skipped_items:[{...skipped[0],reason_codes:["private_internal_reason"]}]});
  assert.ok(text.includes("source needs revalidation"));
  assert.ok(!text.includes("private_internal_reason"));
});


test("preparation response announces checks without claiming a run exists", () => {
  for (const locale of ["en", "ko", "ja"]) {
    const message = collectionPreflightMessage(locale, { workflow_state: "preparing", run_ids: [], groups: [], skipped_items: [] });
    assert.ok(message);
    assert.notEqual(message, collectionPreparationMessage(locale, { status: "run_created", run_id: "run" }));
  }
});

test("preparation terminal, transient, stale and missing states remain distinguishable", () => {
  assert.equal(collectionPreparationMessage("en", undefined), null);
  assert.ok(collectionPreparationMessage("en", {status:"skipped",reason_codes:["no_eligible_detail"]}).includes("did not start"));
  assert.ok(collectionPreparationMessage("en", {status:"unavailable",retryable:true}).includes("request collection again"));
  assert.ok(collectionPreparationMessage("en", {status:"checking",updated_at:"2020-01-01T00:00:00Z"}).includes("interrupted"));
  assert.ok(collectionPreparationMessage("en", {status:"run_created",run_id:"run",excluded_sources:[{source_id:"fees",reason_code:"terminal_source_failure"}]}).includes("Excluded 1"));
});
