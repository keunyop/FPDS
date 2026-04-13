import Link from "next/link";
import { redirect } from "next/navigation";

import { fetchAdminSession, getAdminApiOrigin } from "@/lib/admin-api";

import { LogoutButton } from "./LogoutButton";

const navGroups = [
  {
    title: "Overview",
    items: [
      {
        label: "Overview",
        description: "Current triage entrypoint",
        href: "/admin",
        status: "Live",
        live: true
      }
    ]
  },
  {
    title: "Review",
    items: [
      {
        label: "Review Queue",
        description: "Queue, validation, and decision intake",
        status: "Next",
        live: false
      },
      {
        label: "Trace Viewer",
        description: "Evidence inspection and field provenance",
        status: "Planned",
        live: false
      }
    ]
  },
  {
    title: "Operations",
    items: [
      {
        label: "Runs",
        description: "Execution diagnostics and failure context",
        status: "Planned",
        live: false
      },
      {
        label: "Changes",
        description: "Canonical product change chronology",
        status: "Planned",
        live: false
      },
      {
        label: "Publish",
        description: "Retry, pending, and reconciliation monitor",
        status: "Planned",
        live: false
      }
    ]
  },
  {
    title: "Observability",
    items: [
      {
        label: "Usage",
        description: "LLM usage and cost visibility",
        status: "Planned",
        live: false
      },
      {
        label: "Dashboard Health",
        description: "Public serving freshness and completeness",
        status: "Planned",
        live: false
      }
    ]
  }
] as const;

const priorityCards = [
  {
    title: "Review queue",
    copy: "No live queue data is wired yet. The overview reserves the triage slot for WBS 4.2.",
    tone: "warning",
    badge: "Awaiting WBS 4.2"
  },
  {
    title: "Publish monitor",
    copy: "Publish retry and reconciliation states stay visible in the shell design, but runtime data is not connected yet.",
    tone: "info",
    badge: "Shell ready"
  },
  {
    title: "Dashboard health",
    copy: "Serving health remains a dedicated admin surface. This overview keeps a placeholder slot instead of collapsing it into one giant dashboard.",
    tone: "info",
    badge: "Dedicated surface"
  }
] as const;

const timelineItems = [
  {
    title: "Admin session baseline shipped",
    copy: "FastAPI-backed login, logout, and session introspection are live in the protected shell.",
    meta: "Completed in WBS 4.1"
  },
  {
    title: "Design system refresh applied",
    copy: "The admin runtime now consumes the shared FPDS theme and compact operational shell structure.",
    meta: "Completed in this slice"
  },
  {
    title: "Review queue is the next natural surface",
    copy: "The overview intentionally points the next work toward queue-first triage rather than overloading the current page.",
    meta: "Next planned slice"
  }
] as const;

const emptySurfaces = [
  {
    title: "Queued reviews",
    copy: "This panel becomes the high-signal review intake surface once queue APIs are available."
  },
  {
    title: "Recent failures",
    copy: "Run failures will surface here without replacing the dedicated runs diagnostic screen."
  },
  {
    title: "Usage anomalies",
    copy: "Model, agent, and run anomalies will stay on the observability side of the shell."
  }
] as const;

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
      <main className="fpds-admin-shell">
        <section className="fpds-admin-panel fpds-page-header" data-elevated="true">
          <div className="fpds-page-heading">
            <span className="fpds-eyebrow">Admin API unavailable</span>
            <h1 className="fpds-page-title">The admin web shell is up, but the auth service is not reachable.</h1>
            <p className="fpds-page-copy">
              Start the FastAPI service and refresh this page. The protected admin shell depends on
              `/api/admin/auth/session` before it can show operator context, route gating, or next-surface
              state.
            </p>
          </div>
          <div className="fpds-banner" data-tone="danger">
            <strong>What is blocked</strong>
            <span>Protected navigation, current-operator context, and authenticated workflow surfaces.</span>
          </div>
        </section>
      </main>
    );
  }

  const activeSession = session!;
  const expiresAt = new Date(activeSession.user.expires_at).toLocaleString();
  const envLabel = process.env.NODE_ENV === "production" ? "Prod" : "Dev";

  return (
    <main className="fpds-admin-shell">
      <div className="fpds-shell-grid">
        <aside className="fpds-admin-panel fpds-sidebar">
          <div className="fpds-sidebar-footer">
            <span className="fpds-wordmark">FPDS Admin</span>
            <div className="fpds-sidebar-meta">
              <span>Environment</span>
              <span className="fpds-status-badge" data-tone="info">
                {envLabel}
              </span>
            </div>
          </div>

          {navGroups.map((group) => (
            <section className="fpds-sidebar-group" key={group.title}>
              <h2>{group.title}</h2>
              <ul className="fpds-nav-list">
                {group.items.map((item) => (
                  <li key={item.label}>
                    {item.live ? (
                      <Link aria-current="page" className="fpds-nav-link" href={item.href}>
                        <strong className="fpds-nav-label">{item.label}</strong>
                        <span className="fpds-nav-copy">{item.description}</span>
                        <span className="fpds-nav-pill" data-tone="neutral">
                          {item.status}
                        </span>
                      </Link>
                    ) : (
                      <div className="fpds-nav-item">
                        <strong className="fpds-nav-label">{item.label}</strong>
                        <span className="fpds-nav-copy">{item.description}</span>
                        <span className="fpds-nav-pill" data-tone="neutral">
                          {item.status}
                        </span>
                      </div>
                    )}
                  </li>
                ))}
              </ul>
            </section>
          ))}

          <div className="fpds-sidebar-footer">
            <div className="fpds-sidebar-meta">
              <span>Scope</span>
              <span>Compact admin shell</span>
            </div>
            <div className="fpds-sidebar-meta">
              <span>Theme</span>
              <span>Light only</span>
            </div>
          </div>
        </aside>

        <div className="fpds-main">
          <div className="fpds-admin-panel fpds-topbar">
            <div className="fpds-topbar-tools">
              <span className="fpds-search-shell">Search by bank, product, run, or candidate soon</span>
              <span className="fpds-locale-switch">EN / KO / JA</span>
            </div>
            <div className="fpds-session-chip">
              <span>{activeSession.user.display_name}</span>
              <span className="fpds-status-badge" data-tone="info">
                {activeSession.user.role}
              </span>
            </div>
          </div>

          <section className="fpds-admin-panel fpds-page-header" data-elevated="true">
            <div className="fpds-page-head">
              <div className="fpds-page-heading">
                <span className="fpds-eyebrow">Protected overview</span>
                <h1 className="fpds-page-title">Admin triage now lives inside the refreshed FPDS operations shell.</h1>
                <p className="fpds-page-copy">
                  The new design system keeps admin compact, route-oriented, and evidence-aware. This first
                  live overview is the stable entrypoint for review, trace, runs, publish, usage, and dashboard
                  health without collapsing them into one oversized page.
                </p>
              </div>
              <div className="fpds-page-actions">
                <span className="fpds-status-badge" data-tone="success">
                  Session verified
                </span>
                <LogoutButton apiOrigin={getAdminApiOrigin()} />
              </div>
            </div>

            <div className="fpds-banner" data-tone="warning">
              <strong>Current slice boundary</strong>
              <span>
                This redesign refreshes the live admin shell and overview first. Queue, trace, runs, changes,
                publish, usage, and health remain separate surfaces and will be wired in follow-on WBS slices.
              </span>
            </div>

            <div className="fpds-user-grid">
              <div className="fpds-user-tile">
                <span className="fpds-user-label">Operator</span>
                <span className="fpds-user-value">{activeSession.user.display_name}</span>
              </div>
              <div className="fpds-user-tile">
                <span className="fpds-user-label">Email</span>
                <span className="fpds-user-value">{activeSession.user.email}</span>
              </div>
              <div className="fpds-user-tile">
                <span className="fpds-user-label">Role</span>
                <span className="fpds-user-value">{activeSession.user.role}</span>
              </div>
              <div className="fpds-user-tile">
                <span className="fpds-user-label">Session expires</span>
                <span className="fpds-user-value">{expiresAt}</span>
              </div>
            </div>
          </section>

          <section className="fpds-kpi-grid">
            <article className="fpds-admin-panel fpds-kpi-card">
              <div className="fpds-kpi-top">
                <p className="fpds-kpi-label">Auth service</p>
                <span className="fpds-kpi-pill" data-tone="success">
                  Healthy
                </span>
              </div>
              <p className="fpds-kpi-value">1</p>
              <p className="fpds-kpi-note">Protected shell connected to the FastAPI session contract.</p>
            </article>

            <article className="fpds-admin-panel fpds-kpi-card">
              <div className="fpds-kpi-top">
                <p className="fpds-kpi-label">Live admin surfaces</p>
                <span className="fpds-kpi-pill" data-tone="info">
                  WBS 4.1
                </span>
              </div>
              <p className="fpds-kpi-value">2</p>
              <p className="fpds-kpi-note">Login and protected overview are now aligned to the new shell.</p>
            </article>

            <article className="fpds-admin-panel fpds-kpi-card">
              <div className="fpds-kpi-top">
                <p className="fpds-kpi-label">Next implementation route</p>
                <span className="fpds-kpi-pill" data-tone="warning">
                  Next
                </span>
              </div>
              <p className="fpds-kpi-value">/admin/reviews</p>
              <p className="fpds-kpi-note">Queue-first triage remains the next highest-signal admin slice.</p>
            </article>

            <article className="fpds-admin-panel fpds-kpi-card">
              <div className="fpds-kpi-top">
                <p className="fpds-kpi-label">Design mode</p>
                <span className="fpds-kpi-pill" data-tone="info">
                  Compact
                </span>
              </div>
              <p className="fpds-kpi-value">Light only</p>
              <p className="fpds-kpi-note">Shared tokens now drive the admin runtime directly.</p>
            </article>
          </section>

          <section className="fpds-status-grid">
            <article className="fpds-admin-panel fpds-surface-card">
              <div className="fpds-card-header">
                <div className="fpds-card-heading">
                  <h2 className="fpds-card-title">Priority surfaces</h2>
                  <p className="fpds-card-copy">
                    The shell keeps high-risk operational surfaces distinct instead of flattening them into a
                    single dashboard.
                  </p>
                </div>
                <span className="fpds-status-badge" data-tone="info">
                  Route-oriented
                </span>
              </div>

              <div>
                {priorityCards.map((item) => (
                  <div className="fpds-status-row" key={item.title}>
                    <div className="fpds-status-top">
                      <span className="fpds-status-name">{item.title}</span>
                      <span className="fpds-status-badge" data-tone={item.tone}>
                        {item.badge}
                      </span>
                    </div>
                    <p className="fpds-status-copy">{item.copy}</p>
                  </div>
                ))}
              </div>
            </article>

            <article className="fpds-admin-panel fpds-surface-card">
              <div className="fpds-card-header">
                <div className="fpds-card-heading">
                  <h2 className="fpds-card-title">Implementation timeline</h2>
                  <p className="fpds-card-copy">
                    The overview stays honest about what is live, what changed now, and what comes next.
                  </p>
                </div>
                <span className="fpds-status-badge" data-tone="neutral">
                  Resume-friendly
                </span>
              </div>

              <div>
                {timelineItems.map((item) => (
                  <div className="fpds-timeline-row" key={item.title}>
                    <div className="fpds-timeline-top">
                      <span className="fpds-timeline-title">{item.title}</span>
                      <span className="fpds-status-meta">{item.meta}</span>
                    </div>
                    <p className="fpds-timeline-copy">{item.copy}</p>
                  </div>
                ))}
              </div>
            </article>
          </section>

          <section className="fpds-panel-grid">
            {emptySurfaces.map((surface) => (
              <article className="fpds-admin-panel fpds-empty-card" data-dashed="true" key={surface.title}>
                <span className="fpds-status-badge" data-tone="neutral">
                  Empty by design
                </span>
                <strong className="fpds-empty-title">{surface.title}</strong>
                <p className="fpds-empty-copy">{surface.copy}</p>
              </article>
            ))}
          </section>
        </div>
      </div>
    </main>
  );
}
