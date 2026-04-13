import { redirect } from "next/navigation";

import { fetchAdminSession, getAdminApiOrigin } from "@/lib/admin-api";

import { LoginForm } from "./LoginForm";

type LoginPageProps = {
  searchParams?: Promise<Record<string, string | string[] | undefined>>;
};

export default async function LoginPage({ searchParams }: LoginPageProps) {
  const resolvedSearchParams = (await searchParams) ?? {};
  const nextParam = Array.isArray(resolvedSearchParams.next)
    ? resolvedSearchParams.next[0]
    : resolvedSearchParams.next;
  let session: Awaited<ReturnType<typeof fetchAdminSession>> = null;
  try {
    session = await fetchAdminSession();
  } catch {
    session = null;
  }

  if (session) {
    redirect("/admin");
  }

  return (
    <main className="fpds-login-shell">
      <div className="fpds-login-wrap">
        <div className="fpds-login-brand">
          <span className="fpds-wordmark">FPDS Admin</span>
          <span className="fpds-eyebrow">Protected operations console</span>
          <h1 className="fpds-login-title">Evidence-first review work begins in a secure operator shell.</h1>
          <p className="fpds-login-subtitle">
            The admin console now follows the refreshed FPDS design system: compact, light-only, and
            structured around review, trace, runs, publish, usage, and health surfaces.
          </p>
        </div>

        <section className="fpds-admin-panel fpds-login-card" data-elevated="true">
          <div className="fpds-page-stack">
            <div className="fpds-card-heading">
              <h2 className="fpds-card-title">Operator sign-in</h2>
              <p className="fpds-card-copy">
                Access is limited to `admin`, `reviewer`, and `read_only` accounts created in the FPDS
                database.
              </p>
            </div>
            <ul className="fpds-support-list">
              <li className="fpds-support-item">
                <strong>Server-managed session</strong>
                <span>The browser never stores a bearer token for admin access.</span>
              </li>
              <li className="fpds-support-item">
                <strong>Tracked sign-in attempts</strong>
                <span>Lockout-ready login attempt history stays in Postgres with the auth service.</span>
              </li>
              <li className="fpds-support-item">
                <strong>Next shell ready</strong>
                <span>Successful sign-in opens the protected overview for the next admin slices.</span>
              </li>
            </ul>
          </div>
          <LoginForm apiOrigin={getAdminApiOrigin()} nextPath={nextParam ?? "/admin"} />
        </section>

        <p className="fpds-login-footnote">
          SSO and extended remember-me behavior are intentionally deferred until the auth roadmap explicitly
          approves them.
        </p>
      </div>
    </main>
  );
}
