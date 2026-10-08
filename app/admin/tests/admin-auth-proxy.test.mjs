import assert from "node:assert/strict";
import test from "node:test";
import { proxyAdminAuth } from "../src/lib/admin-auth-proxy.ts";
import { resolveAdminApiOrigin } from "../src/lib/admin-api-origin.ts";

const web = "https://admin.example";
const api = () => "https://api.example";
function request(action, method = "POST", headers = {}, body = '{"country_code":"CA"}') {
  return new Request(`${web}/api/admin/auth/${action}`, {
    method,
    headers: { origin: web, "content-type": "application/json", ...headers },
    ...(method === "POST" ? { body } : {}),
  });
}

test("local defaults and configured origins stay server targets", () => {
  assert.equal(resolveAdminApiOrigin(undefined, false), "http://localhost:4000");
  assert.equal(resolveAdminApiOrigin(" https://api.example/ ", true), "https://api.example");
  assert.equal(resolveAdminApiOrigin("http://127.0.0.1:4000", false), "http://127.0.0.1:4000");
});

test("hosted configuration rejects missing, insecure, loopback and non-origin targets", () => {
  for (const value of [undefined, "", "  ", "http://api.example", "https://localhost", "https://127.0.0.1",
    "https://[::1]", "https://a.localhost", "https://api.example/private", "https://api.example?key=secret",
    "https://api.example#private", "https://user:password@api.example", "file:///private", "//api.example"]) {
    assert.throws(() => resolveAdminApiOrigin(value, true), undefined, String(value));
  }
});

for (const [action, method, status] of [["countries", "GET", 200], ["login", "POST", 200],
  ["signup-requests", "POST", 201], ["logout", "POST", 200]]) {
  test(`${action} forwards the exact method/body and upstream status without caching`, async () => {
    let called = 0;
    const result = await proxyAdminAuth(request(action, method, {
      cookie: "fpds_admin_session=session-token; fpds_admin_csrf=csrf-token",
      "x-csrf-token": "csrf-token", "user-agent": "Fixture Browser", "x-forwarded-for": "203.0.113.7", authorization: "never-forward", "x-country-code": "US",
    }), action, api, async (url, options) => {
      called++;
      assert.equal(String(url), `https://api.example/api/admin/auth/${action}`);
      assert.equal(options.method, method);
      assert.equal(options.body, method === "POST" ? '{"country_code":"CA"}' : undefined);
      assert.equal(options.headers.get("cookie"), "fpds_admin_session=session-token; fpds_admin_csrf=csrf-token");
      assert.equal(options.headers.get("x-csrf-token"), "csrf-token");
      assert.equal(options.headers.get("user-agent"), "Fixture Browser");
      assert.equal(options.headers.get("x-forwarded-for"), "203.0.113.7");
      assert.equal(options.headers.get("authorization"), null);
      assert.equal(options.headers.get("x-country-code"), null);
      assert.equal(options.cache, "no-store");
      assert.equal(options.redirect, "manual");
      assert.ok(options.signal instanceof AbortSignal);
      return Response.json({ data: { ok: true } }, { status });
    });
    assert.equal(called, 1);
    assert.equal(result.status, status);
    assert.equal(result.headers.get("cache-control"), "no-store");
    assert.deepEqual(await result.json(), { data: { ok: true } });
  });
}

test("login keeps independent host cookies and their HttpOnly, SameSite, Secure and expiry attributes", async () => {
  const cookies = [
    "fpds_admin_session=token; Path=/; Domain=api.example; HttpOnly; Secure; SameSite=Lax",
    "fpds_admin_csrf=csrf; Path=/; SameSite=Lax; Expires=Wed, 21 Oct 2026 07:28:00 GMT",
    "unrelated=private; Path=/",
  ];
  const result = await proxyAdminAuth(request("login"), "login", api, async () => {
    const headers = new Headers({ "content-type": "application/json" });
    for (const cookie of cookies) headers.append("set-cookie", cookie);
    return new Response('{"data":{"ok":true}}', { headers });
  });
  assert.deepEqual(result.headers.getSetCookie(), [
    cookies[0].replace("; Domain=api.example", ""), cookies[1] + "; Secure",
  ]);
});

test("logout forwards both expired-cookie deletions without splitting Expires commas", async () => {
  const cookies = ["fpds_admin_session=; Path=/; Max-Age=0; Expires=Thu, 01 Jan 1970 00:00:00 GMT; HttpOnly; SameSite=Lax",
    "fpds_admin_csrf=; Path=/; Max-Age=0; SameSite=Lax"];
  const result = await proxyAdminAuth(request("logout"), "logout", api, async () => {
    const headers = new Headers();
    for (const cookie of cookies) headers.append("set-cookie", cookie);
    return new Response('{"data":{"logged_out":true}}', { headers });
  });
  assert.deepEqual(result.headers.getSetCookie(), cookies.map(cookie => cookie + "; Secure"));
});

test("HTTP local development preserves non-Secure API cookies", async () => {
  const result = await proxyAdminAuth(new Request("http://localhost:3001/api/admin/auth/login", {
    method: "POST", headers: { origin: "http://localhost:3001" }, body: "{}",
  }), "login", api, async () => new Response("{}", {
    headers: { "set-cookie": "fpds_admin_session=token; Path=/; HttpOnly; SameSite=Lax" },
  }));
  assert.equal(result.headers.getSetCookie()[0], "fpds_admin_session=token; Path=/; HttpOnly; SameSite=Lax");
});

test("bad credentials, CSRF/permission rejection and validation errors remain API-owned", async () => {
  for (const status of [400, 401, 403, 409, 422, 429, 500, 503]) {
    const body = JSON.stringify({ error: { code: "original_api_error" } });
    const result = await proxyAdminAuth(request("logout"), "logout", api,
      async () => new Response(body, { status }));
    assert.equal(result.status, status);
    assert.equal(await result.text(), body);
    assert.equal(result.headers.getSetCookie().length, 0);
  }
});

test("unknown actions and wrong methods cannot reach the API", async () => {
  const unreachable = async () => { assert.fail("must not fetch"); };
  for (const action of ["session", "country", "signup-requests/123/approve", "../login", "https://evil.example", "__proto__", "constructor"]) {
    assert.equal((await proxyAdminAuth(request("login"), action, api, unreachable)).status, 404);
  }
  assert.equal((await proxyAdminAuth(request("login", "GET"), "login", api, unreachable)).status, 405);
  assert.equal((await proxyAdminAuth(request("countries"), "countries", api, unreachable)).status, 405);
});

test("cross-origin, null and absent origins cannot perform login/signup/logout", async () => {
  for (const action of ["login", "signup-requests", "logout"]) {
    for (const origin of ["https://evil.example", "null", ""]) {
      const result = await proxyAdminAuth(request(action, "POST", { origin }), action, api,
        async () => { assert.fail("must not fetch"); });
      assert.equal(result.status, 403);
    }
    const absent = request(action);
    absent.headers.delete("origin");
    assert.equal((await proxyAdminAuth(absent, action, api,
      async () => { assert.fail("must not fetch"); })).status, 403);
  }
});

test("upstream redirects are rejected instead of sending credentials onward", async () => {
  const result = await proxyAdminAuth(request("login"), "login", api, async () =>
    new Response(null, { status: 307, headers: { location: "https://evil.example" } }));
  assert.equal(result.status, 502);
  assert.equal(result.headers.get("location"), null);
});

test("transport, timeout and missing-hosted-config errors are bounded and redact private details", async () => {
  for (const error of [new Error("private https://api.example secret-token"), new DOMException("timed out", "TimeoutError")]) {
    const result = await proxyAdminAuth(request("login"), "login", api, async () => { throw error; });
    assert.equal(result.status, 503);
    assert.doesNotMatch(await result.text(), /api\.example|secret-token|timed out/);
  }
  const result = await proxyAdminAuth(request("login"), "login", () => resolveAdminApiOrigin(undefined, true),
    async () => { assert.fail("must not fetch"); });
  assert.equal(result.status, 503);
});


test("browser Host and HTTPS forwarding survive Next's internal localhost URL", async () => {
  const req = new Request("http://localhost:3000/api/admin/auth/login", {
    method: "POST",
    headers: { host: "admin.example", "x-forwarded-proto": "https", origin: "https://admin.example" },
    body: "{}",
  });
  const result = await proxyAdminAuth(req, "login", api, async () => new Response("{}", {
    headers: { "set-cookie": "fpds_admin_session=token; Path=/; HttpOnly; SameSite=Lax" },
  }));
  assert.equal(result.status, 200);
  assert.match(result.headers.getSetCookie()[0], /; Secure$/);
  req.headers.set("origin", "http://localhost:3000");
  assert.equal((await proxyAdminAuth(req, "login", api,
    async () => { assert.fail("must not fetch internal-origin writes"); })).status, 403);
});

test("direct next start accepts its browser Host without HTTPS forwarding", async () => {
  const result = await proxyAdminAuth(new Request("http://localhost:44517/api/admin/auth/login", {
    method: "POST", headers: { host: "127.0.0.1:44517", origin: "http://127.0.0.1:44517" }, body: "{}",
  }), "login", api, async () => new Response("{}"));
  assert.equal(result.status, 200);
});
