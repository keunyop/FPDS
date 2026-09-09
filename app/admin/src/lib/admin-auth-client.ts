// Browser-safe auth behavior shared by the UI and focused Node tests.
export function safeAdminReturnPath(value: string, locale: string): string {
  const fallback = "/admin?locale=" + locale;
  if (!value.startsWith("/") || value.startsWith("//") || /[\\\u0000-\u0020\u007f]/.test(value)) return fallback;
  try {
    const base = "https://admin.invalid";
    const url = new URL(value, base);
    const path = decodeURIComponent(url.pathname);
    if (url.origin !== base || /[\\\u0000-\u0020\u007f]/.test(path)) return fallback;
    if (path !== "/admin" && !path.startsWith("/admin/")) return fallback;
    if (path === "/admin/login" || path === "/admin/signup") return fallback;
    url.searchParams.set("locale", locale);
    return url.pathname + url.search + url.hash;
  } catch {
    return fallback;
  }
}
export function adminEnvironmentLabel(environment?: string): string {
  if (environment === "prod") return "Prod";
  if (environment === "dev") return "Dev";
  return "—";
}
export async function requestAdminLogout(
  apiOrigin: string,
  csrfToken: string | null | undefined,
  fetcher: typeof fetch = fetch,
): Promise<void> {
  const response = await fetcher(apiOrigin + "/api/admin/auth/logout", {
    method: "POST",
    credentials: "include",
    headers: csrfToken ? { "X-CSRF-Token": csrfToken } : {},
    signal: AbortSignal.timeout(15_000),
  });
  if (!response.ok) throw new Error("logout_failed");
}
