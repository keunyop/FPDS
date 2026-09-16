import { readFileSync } from "node:fs";
import assert from "node:assert/strict";
import test from "node:test";

import { resolvePublicBankLogo } from "./public-bank-logo.ts";

test("uses only same-origin verified logo assets", () => {
  assert.deepEqual(resolvePublicBankLogo(" bmo ", "BMO"), {
    asset: "/bank-logos/bmo.svg",
    fallbackCode: "BMO",
    normalizedCode: "BMO"
  });
});

test("uses a stable text mark instead of a remote image", () => {
  assert.deepEqual(resolvePublicBankLogo("UNKNOWN", "Example Bank"), {
    asset: null,
    fallbackCode: "UNKN",
    normalizedCode: "UNKNOWN"
  });
});

test("derives a fallback when a bank code is missing", () => {
  assert.deepEqual(resolvePublicBankLogo("", "Example Bank"), {
    asset: null,
    fallbackCode: "EX",
    normalizedCode: ""
  });
});

test("Top 5 bank mappings point to actual local image files", () => {
  for (const code of ["AB", "RB", "FCB", "KEYBANK", "BOAN", "USBN", "VANCITY", "MANULIFE", "LAURENTIAN", "BMO", "CIBC", "RBC", "SCOTIA", "TD"]) {
    const { asset } = resolvePublicBankLogo(code.toLowerCase(), code);
    assert.ok(asset?.startsWith("/bank-logos/"), code);
    const bytes = readFileSync(new URL("../../public" + asset, import.meta.url));
    assert.ok(bytes.length > 100, code);
    if (asset.endsWith(".svg")) {
      assert.match(bytes.toString(), /<svg[\s>]/);
      assert.doesNotMatch(bytes.toString(), /<script|<foreignObject|(?:href|src)=["']https?:/i);
    }
  }
});
