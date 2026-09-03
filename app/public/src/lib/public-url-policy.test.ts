import assert from "node:assert/strict";
import test from "node:test";

import {
  buildCanonicalProductUrl,
  buildProductDetailPath,
  isIndexableProductLocale,
  normalizeProductDetailRequest
} from "./public-url-policy.ts";

const PRODUCT_PATH = "/products/prod_IbZVSqaogb3BkWBd";

test("keeps the default English Canada product URL clean", () => {
  assert.equal(
    buildProductDetailPath(PRODUCT_PATH, "en", "CA"),
    PRODUCT_PATH
  );
  assert.deepEqual(
    normalizeProductDetailRequest(
      new URL("https://www.switchabank.com" + PRODUCT_PATH)
    ),
    {
      countryCode: "CA",
      indexable: true,
      locale: "en",
      normalizedPath: PRODUCT_PATH
    }
  );
});

test("removes catalog, pagination, and tracking state while preserving meaningful locale and country", () => {
  const policy = normalizeProductDetailRequest(
    new URL(
      "https://www.switchabank.com" + PRODUCT_PATH +
      "?locale=ja&country_code=us&sort_by=display_rate&sort_order=asc" +
      "&bank_code=BMO&product_type=line-of-credit&page=2&utm_source=gsc" +
      "&gclid=abc&fbclid=def"
    )
  );

  assert.equal(
    policy.normalizedPath,
    PRODUCT_PATH + "?locale=ja&country_code=US"
  );
  assert.equal(policy.indexable, false);
});

test("normalizes invalid/default values and duplicate query values deterministically", () => {
  const policy = normalizeProductDetailRequest(
    new URL(
      "https://www.switchabank.com" + PRODUCT_PATH +
      "?locale=xx&locale=ja&country_code=can&country_code=US&sort_by=bank_name"
    )
  );

  assert.equal(policy.locale, "en");
  assert.equal(policy.countryCode, "CA");
  assert.equal(policy.normalizedPath, PRODUCT_PATH);
});

test("uses the clean English route as the canonical for every product locale", () => {
  assert.equal(
    buildCanonicalProductUrl(PRODUCT_PATH, "us"),
    "https://www.switchabank.com" + PRODUCT_PATH + "?country_code=US"
  );
  assert.equal(isIndexableProductLocale("en"), true);
  assert.equal(isIndexableProductLocale("ko"), false);
  assert.equal(isIndexableProductLocale("ja"), false);
});

test("consolidates the confirmed duplicate BMO product on its newer canonical record", () => {
  assert.equal(
    buildProductDetailPath("/products/prod_LuH-Kei2S8uFFOyY", "en", "CA"),
    "/products/prod_SNcPg2yBYt4rgyAt"
  );
});
