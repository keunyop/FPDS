import assert from "node:assert/strict";
import test from "node:test";
import { collectionPreflightMessage } from "../src/lib/admin-collection-feedback.ts";

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
