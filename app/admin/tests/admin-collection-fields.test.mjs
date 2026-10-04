import assert from "node:assert/strict";
import test from "node:test";
import { collectionFieldSelection, collectionFieldMode, changeCollectionField,
  sameCollectionFieldSelection, collectionFieldLabel, collectionFieldSelectionError, canChangeCollectionFieldSelection } from "../src/lib/admin-collection-fields.ts";

const configuration = {
  required_fields: ["product_name", "currency", "monthly_fee"],
  optional_fields: ["minimum_balance", "notes"],
  locked_required_fields: ["product_name", "currency", "monthly_fee"],
  requirements: [], country_code: "CA", configured: false,
  field_catalog: ["product_name", "currency", "monthly_fee", "minimum_balance", "notes"].map(field_key =>
    ({field_key, value_type: "string", unit: null})),
};

test("selection copies arrays and keeps missing optional information unselected", () => {
  const draft = collectionFieldSelection(configuration);
  draft.optional_fields.pop();
  assert.deepEqual(configuration.optional_fields, ["minimum_balance", "notes"]);
  assert.equal(collectionFieldMode(draft, "notes"), "omit");
});

test("registered additional fields can move between required, optional and omitted", () => {
  let draft = collectionFieldSelection(configuration);
  draft = changeCollectionField(configuration, draft, "minimum_balance", "required");
  assert.equal(collectionFieldMode(draft, "minimum_balance"), "required");
  assert.ok(!draft.optional_fields.includes("minimum_balance"));
  draft = changeCollectionField(configuration, draft, "minimum_balance", "optional");
  assert.equal(collectionFieldMode(draft, "minimum_balance"), "optional");
  draft = changeCollectionField(configuration, draft, "minimum_balance", "omit");
  assert.equal(collectionFieldMode(draft, "minimum_balance"), "omit");
});

test("financial essentials and unregistered fields cannot change through the editor", () => {
  const draft = collectionFieldSelection(configuration);
  for (const key of ["currency", "monthly_fee", "invented_rate"]) {
    for (const mode of ["optional", "omit", "required"]) {
      assert.equal(changeCollectionField(configuration, draft, key, mode), draft);
    }
  }
});

test("same required/optional selection ignores row order but detects changed meaning", () => {
  const draft = collectionFieldSelection(configuration);
  assert.ok(sameCollectionFieldSelection(draft, {required_fields:[...draft.required_fields].reverse(), optional_fields:[...draft.optional_fields].reverse()}));
  assert.ok(!sameCollectionFieldSelection(draft, changeCollectionField(configuration, draft, "notes", "required")));
});

test("localized labels preserve canonical field identity and safely render extensions", () => {
  assert.equal(collectionFieldLabel("monthly_fee", "ko"), "월 수수료");
  assert.equal(collectionFieldLabel("currency", "ja"), "通貨");
  assert.equal(collectionFieldLabel("registered_optional_text", "ja"), "Registered Optional Text");
});


test("collection request limit accepts 60 targets and rejects 61 without changing omissions", () => {
  const required_fields=Array.from({length:10},(_,i)=>`required_${i}`);
  const optional_fields=Array.from({length:50},(_,i)=>`optional_${i}`);
  assert.equal(collectionFieldSelectionError({required_fields,optional_fields}),null);
  assert.equal(collectionFieldSelectionError({required_fields,optional_fields:[...optional_fields,"one_more"]}),"too_many_fields");
});


test("legacy over-budget targets can be reduced until valid without allowing equal or larger over-budget drafts", () => {
  const previous={required_fields:["identity"],optional_fields:Array.from({length:62},(_,i)=>`optional_${i}`)};
  const reducing={...previous,optional_fields:previous.optional_fields.slice(0,61)};
  assert.ok(canChangeCollectionFieldSelection(previous,reducing));
  assert.equal(collectionFieldSelectionError(reducing),"too_many_fields","still invalid for saving");
  assert.ok(!canChangeCollectionFieldSelection(previous,{...previous,optional_fields:[...previous.optional_fields]}));
  assert.ok(!canChangeCollectionFieldSelection(previous,{...previous,optional_fields:[...previous.optional_fields,"new"]}));
  const valid={...previous,optional_fields:previous.optional_fields.slice(0,59)};
  assert.ok(canChangeCollectionFieldSelection(reducing,valid));assert.equal(collectionFieldSelectionError(valid),null);
});
