import { redirect } from "next/navigation";

import { fetchAdminSession, getAdminApiOrigin } from "@/lib/admin-api";

import { LogoutButton } from "./LogoutButton";

export default async function AdminOverviewPage() {
  let session: Awaited<ReturnType<typeof fetchAdminSession>> = null;
  let apiUnavailable = false;
  try {
    session = await fetchAdminSession();
  } catch {
    apiUnavailable = true;
  }

  if (!session && !apiUnavailable) {
    redirect("/admin/login?next=/admin");
  }

  if (apiUnavailable) {
    return (
      <main className="fpds-shell">
        <div className="overview-grid">
          <section className="fpds-card overview-card">
            <span className="eyebrow">Admin API Unavailable</span>
            <h1>The web shell is up, but the FastAPI auth service is not reachable.</h1>
            <p className="hero-copy">
              Start the API service and refresh this page. The protected admin overview depends on
              `/api/admin/auth/session` to validate the current operator session.
            </p>
          </section>
        </div>
      </main>
    );
  }

  const activeSession = session!;

  return (
    <main className="fpds-shell">
      <div className="overview-grid">
        <div className="overview-topbar">
          <span className="eyebrow">Protected Overview</span>
          <div className="session-pill">
            <span>Signed in as {activeSession.user.display_name}</span>
            <strong>{activeSession.user.role}</strong>
          </div>
        </div>

        <section className="fpds-card overview-card">
          <h1>Admin login is now live on the real runtime stack.</h1>
          <p className="hero-copy">
            The admin web now authenticates against the FastAPI service, which validates DB-backed operator
            accounts, issues the shared session cookie, records auth audit events, and exposes the current
            session snapshot for protected routes.
          </p>
          <div className="meta-grid">
            <div className="meta-tile">
              <p className="meta-label">Operator</p>
              <p className="meta-value">{activeSession.user.display_name}</p>
            </div>
            <div className="meta-tile">
              <p className="meta-label">Email</p>
              <p className="meta-value">{activeSession.user.email}</p>
            </div>
            <div className="meta-tile">
              <p className="meta-label">Role</p>
              <p className="meta-value">{activeSession.user.role}</p>
            </div>
            <div className="meta-tile">
              <p className="meta-label">Session Expires</p>
              <p className="meta-value">{new Date(activeSession.user.expires_at).toLocaleString()}</p>
            </div>
          </div>
        </section>

        <div className="overview-panels">
          <aside className="fpds-card overview-rail">
            <h2>What This Slice Added</h2>
            <ul className="overview-list">
              <li>Postgres tables for operator accounts, login attempts, and admin sessions.</li>
              <li>`/api/admin/auth/login`, `/logout`, and `/session` running on FastAPI.</li>
              <li>Protected `/admin` entry backed by the shared session cookie contract.</li>
            </ul>
          </aside>
          <aside className="fpds-card overview-rail">
            <h2>Next WBS Entry Points</h2>
            <ul className="overview-list">
              <li>Review queue and review detail can now build on a real authenticated shell.</li>
              <li>Role-aware write gating can reuse the current session actor payload.</li>
              <li>Future admin mutations can pick up the stored CSRF token path.</li>
            </ul>
            <LogoutButton apiOrigin={getAdminApiOrigin()} />
          </aside>
        </div>
      </div>
    </main>
  );
}
