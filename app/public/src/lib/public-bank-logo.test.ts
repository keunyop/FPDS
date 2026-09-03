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
  assert.deepEqual(resolvePublicBankLogo("VANCITY", "Vancity"), {
    asset: null,
    fallbackCode: "VANC",
    normalizedCode: "VANCITY"
  });
});

test("derives a fallback when a bank code is missing", () => {
  assert.deepEqual(resolvePublicBankLogo("", "Example Bank"), {
    asset: null,
    fallbackCode: "EX",
    normalizedCode: ""
  });
});
