// Pure resolver shared by the server API client and focused configuration tests.
export function resolveAdminApiOrigin(
  configured: string | undefined,
  hosted: boolean,
): string {
  const value = configured?.trim() || (hosted ? "" : "http://localhost:4000");
  if (!value) throw new Error("FPDS_ADMIN_API_ORIGIN is required on Vercel.");
  const url = new URL(value);
  if (!['http:', 'https:'].includes(url.protocol) || url.username || url.password ||
      url.pathname !== '/' || url.search || url.hash) {
    throw new Error("FPDS_ADMIN_API_ORIGIN must be an HTTP(S) origin without credentials or a path.");
  }
  const loopback = ['localhost', '127.0.0.1', '[::1]'].includes(url.hostname) || url.hostname.endsWith('.localhost');
  if (hosted && (url.protocol !== 'https:' || loopback)) {
    throw new Error("FPDS_ADMIN_API_ORIGIN must be a remote HTTPS origin on Vercel.");
  }
  return url.origin;
}
