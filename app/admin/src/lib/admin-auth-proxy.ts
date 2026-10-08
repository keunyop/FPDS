// This is deliberately a four-action proxy, never an arbitrary API/URL relay.
const AUTH_METHODS: Record<string, string> = {
  countries: "GET",
  login: "POST",
  "signup-requests": "POST",
  logout: "POST",
};

function failure(status: number, code: string) {
  return Response.json({ error: { code, message: "Admin authentication request failed." } }, {
    status,
    headers: { "Cache-Control": "no-store" },
  });
}

export async function proxyAdminAuth(
  request: Request,
  action: string,
  apiOrigin: () => string,
  fetcher: typeof fetch = fetch,
): Promise<Response> {
  if (!Object.hasOwn(AUTH_METHODS, action)) return failure(404, "not_found");
  if (request.method !== AUTH_METHODS[action]) return failure(405, "method_not_allowed");
  // Next's internal URL can use localhost behind a proxy or next start.
  // Host is the browser-facing authority; Vercel supplies the HTTPS protocol.
  const internalUrl = new URL(request.url);
  const protocol = request.headers.get("x-forwarded-proto") === "https" ? "https:" : internalUrl.protocol;
  const host = request.headers.get("host") ?? internalUrl.host;
  const browserOrigin = `${protocol}//${host}`;
  // Require the actual browser origin on writes, including login (login CSRF).
  if (request.method === "POST" && request.headers.get("origin") !== browserOrigin) {
    return failure(403, "origin_forbidden");
  }
  const headers = new Headers();
  for (const name of ["content-type", "cookie", "x-csrf-token", "user-agent", "x-forwarded-for"]) {
    const value = request.headers.get(name);
    if (value) headers.set(name, value);
  }
  try {
    const upstream = await fetcher(new URL(`/api/admin/auth/${action}`, apiOrigin()), {
      method: request.method,
      headers,
      body: request.method === "POST" ? await request.text() : undefined,
      cache: "no-store",
      redirect: "manual",
      signal: AbortSignal.timeout(15_000),
    });
    if (upstream.status >= 300 && upstream.status < 400) return failure(502, "upstream_redirect");
    const outgoing = new Headers({
      "Content-Type": upstream.headers.get("content-type") ?? "application/json",
      "Cache-Control": "no-store",
    });
    // Separate Set-Cookie headers preserve Expires commas and logout deletions.
    for (const cookie of upstream.headers.getSetCookie()) {
      if (!/^fpds_admin_(session|csrf)=/.test(cookie)) continue;
      let hostCookie = cookie.replace(/;\s*domain=[^;]*/gi, "");
      if (protocol === "https:" && !/;\s*secure(?:;|$)/i.test(hostCookie)) {
        hostCookie += "; Secure";
      }
      outgoing.append("Set-Cookie", hostCookie);
    }
    return new Response(await upstream.text(), { status: upstream.status, headers: outgoing });
  } catch {
    // No upstream address, credentials, body or cookie appears in the error.
    return failure(503, "admin_api_unavailable");
  }
}
