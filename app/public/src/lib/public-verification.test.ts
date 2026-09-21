import assert from "node:assert/strict";
import test from "node:test";
import { getVerificationCopy, verificationDate, verificationStatus, type ProductVerification } from "./public-verification.ts";

const record: ProductVerification = {
  status: "within_window", last_verified_at: "2026-09-01T00:00:00Z",
  review_due_at: "2026-09-08T00:00:00Z", expires_at: "2026-10-01T00:00:00Z",
  evaluated_at: "2026-09-01T00:00:00Z", review_interval_days: 7, expiry_days: 30,
};

test("cached product contracts expire at exact UTC boundaries", () => {
  assert.equal(verificationStatus(record, Date.parse("2026-09-07T23:59:59Z")), "within_window");
  assert.equal(verificationStatus(record, Date.parse(record.review_due_at!)), "review_due");
  assert.equal(verificationStatus(record, Date.parse(record.expires_at!)), "expired");
});

test("legacy, malformed, missing, future and unknown verification fail closed", () => {
  const now = Date.parse("2026-09-02T00:00:00Z");
  assert.equal(verificationStatus(undefined, now), "unknown");
  for (const changes of [{last_verified_at: null}, {last_verified_at: "bad"}, {last_verified_at: "2027-01-01"}, {expires_at: null}, {status: "unknown" as const}, {review_due_at: record.expires_at}]) {
    assert.equal(verificationStatus({...record, ...changes}, now), "unknown");
  }
  assert.equal(verificationDate("bad", "Unknown"), "Unknown");
  assert.equal(verificationDate(null, "Unknown"), "Unknown");
  assert.equal(verificationDate("2026-09-21T01:00:00+01:00", "Unknown"), "2026-09-21");
});

test("all locales distinguish snapshot generation from product checks and expiry", () => {
  for (const locale of ["en", "ko", "ja"]) {
    const copy = getVerificationCopy(locale);
    assert.notEqual(copy.snapshot, copy.checked);
    assert.notEqual(copy.within_window, copy.completed);
    assert.notEqual(copy.review_due, copy.expired);
    assert.ok(copy.notice);
    assert.ok(!Object.values(copy).some(value => value.includes("??")));
  }
  assert.equal(getVerificationCopy("invalid"), getVerificationCopy("en"));
});
