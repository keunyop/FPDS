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
    <main className="fpds-shell">
      <div className="login-grid">
        <section className="fpds-card login-hero">
          <span className="eyebrow">FPDS Admin Console</span>
          <h1>Evidence-first operations start with a protected operator session.</h1>
          <p className="hero-copy">
            This first `WBS 4.1` slice stands up the real admin entrypoint: DB-backed operator accounts,
            server-side sessions, login attempt tracking, and a protected route into the admin overview.
          </p>
          <ul className="detail-list">
            <li>Session auth stays on the server. The browser never stores a bearer token.</li>
            <li>Failed sign-ins are tracked in Postgres and can temporarily lock the account.</li>
            <li>Successful sign-in opens the protected `/admin` shell for the next review and ops slices.</li>
          </ul>
        </section>
        <section className="fpds-card login-panel">
          <h2>Operator Sign-In</h2>
          <p className="hero-copy">
            Admin access is for `admin`, `reviewer`, and `read_only` operator accounts created in the DB.
          </p>
          <LoginForm apiOrigin={getAdminApiOrigin()} nextPath={nextParam ?? "/admin"} />
        </section>
      </div>
    </main>
  );
}
