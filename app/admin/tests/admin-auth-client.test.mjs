import assert from "node:assert/strict";
import test from "node:test";
import { safeAdminReturnPath, adminEnvironmentLabel, requestAdminLogout } from "../src/lib/admin-auth-client.ts";

test("login returns to internal work with the selected locale and filters", () => {
  assert.equal(safeAdminReturnPath("/admin/reviews?q=bank&page=2&locale=en#row", "ko"),
    "/admin/reviews?q=bank&page=2&locale=ko#row");
});
test("login rejects external, malformed, encoded and non-Admin destinations", () => {
  for (const value of ["https://evil.invalid", "//evil.invalid", "/\\evil.invalid",
    "/\t/evil.invalid", "/admin/../../outside", "/%2f%2fevil.invalid", "/admin/%5cfoo",
    "/admin/%00foo", "/administrator", "/admin/login", "/admin/signup", "/admin/%", "javascript:alert(1)"]) {
    assert.equal(safeAdminReturnPath(value, "ja"), "/admin?locale=ja", value);
  }
});
test("environment comes from the API, with no production-build inference", () => {
  assert.equal(adminEnvironmentLabel("dev"), "Dev");
  assert.equal(adminEnvironmentLabel("prod"), "Prod");
  assert.equal(adminEnvironmentLabel(), "—");
  assert.equal(adminEnvironmentLabel("unexpected"), "—");
});
test("logout includes credentials, CSRF and a timeout", async () => {
  await requestAdminLogout("https://api.invalid", "csrf-test", async (url, options) => {
    assert.equal(url, "https://api.invalid/api/admin/auth/logout");
    assert.equal(options.method, "POST");
    assert.equal(options.credentials, "include");
    assert.equal(options.headers["X-CSRF-Token"], "csrf-test");
    assert.ok(options.signal instanceof AbortSignal);
    return new Response(null, { status: 200 });
  });
});
test("logout propagates HTTP and transport failures", async () => {
  for (const status of [401, 403, 500, 503]) {
    await assert.rejects(requestAdminLogout("", "csrf-test",
      async () => new Response(null, { status })), /logout_failed/);
  }
  await assert.rejects(requestAdminLogout("", null, async () => {
    throw new Error("network unavailable");
  }), /network unavailable/);
});
