import { redirect } from "next/navigation";

import { ApplicationShell5 } from "@/components/application-shell5";
import { Banner1 } from "@/components/banner1";
import { Stats5 } from "@/components/stats5";
import { fetchAdminSession, getAdminApiOrigin } from "@/lib/admin-api";

import { LogoutButton } from "./LogoutButton";

const timelineItems = [
  {
    title: "Admin session baseline shipped",
    copy: "FastAPI-backed login, logout, and session introspection are live in the protected shell.",
    meta: "Completed in WBS 4.1"
  },
  {
    title: "Shadcnblocks UI foundation applied",
    copy: "The admin runtime now uses a vendor-first shell, login block, and shared shadcn primitives.",
    meta: "Completed in this slice"
  },
  {
    title: "Review queue is the next natural surface",
    copy: "The overview keeps the next work pointed at queue-first triage rather than overloading the current page.",
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
      <main className="mx-auto flex min-h-screen w-full max-w-5xl items-center px-4 py-8 md:px-6">
        <section className="w-full rounded-[1.75rem] border border-destructive/20 bg-card/95 p-6 shadow-sm md:p-8">
          <div className="max-w-3xl">
            <p className="text-sm font-medium uppercase tracking-[0.18em] text-destructive">Admin API unavailable</p>
            <h1 className="mt-3 text-3xl font-semibold tracking-tight text-foreground">
              The admin web shell is up, but the auth service is not reachable.
            </h1>
            <p className="mt-3 text-sm leading-7 text-muted-foreground">
              Start the FastAPI service and refresh this page. The protected admin shell depends on
              `/api/admin/auth/session` before it can show operator context, route gating, or next-surface state.
            </p>
          </div>
          <div className="mt-6 rounded-2xl border border-destructive/20 bg-critical-soft px-4 py-3 text-sm text-destructive">
            <strong className="block font-medium">What is blocked</strong>
            <span className="mt-1 block leading-6">
              Protected navigation, current-operator context, and authenticated workflow surfaces.
            </span>
          </div>
        </section>
      </main>
    );
  }

  const activeSession = session!;
  const expiresAt = new Date(activeSession.user.expires_at).toLocaleString();
  const envLabel = process.env.NODE_ENV === "production" ? "Prod" : "Dev";
  const statItems = [
    {
      label: "Auth service",
      value: "Healthy",
      note: "Protected shell is connected to the FastAPI session contract.",
      tone: "success" as const
    },
    {
      label: "Live admin surfaces",
      value: "2",
      note: "Login and protected overview now sit on Shadcnblocks-based shell primitives.",
      tone: "info" as const
    },
    {
      label: "Next route",
      value: "/admin/reviews",
      note: "Queue-first triage remains the highest-signal follow-on surface.",
      tone: "warning" as const
    },
    {
      label: "Theme mode",
      value: "radix-nova",
      note: "Admin stays compact, light-first, and route-oriented by design.",
      tone: "neutral" as const
    }
  ];

  return (
    <ApplicationShell5
      environmentLabel={envLabel}
      headerActions={<LogoutButton apiOrigin={getAdminApiOrigin()} />}
      user={{
        name: activeSession.user.display_name,
        email: activeSession.user.email,
        role: activeSession.user.role
      }}
    >
      <section className="grid gap-6">
        <div className="rounded-[1.75rem] border border-border/80 bg-card/95 p-6 shadow-sm md:p-8">
          <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
            <div className="max-w-3xl">
              <p className="text-sm font-medium uppercase tracking-[0.18em] text-muted-foreground">Protected overview</p>
              <h1 className="mt-3 text-balance text-3xl font-semibold tracking-tight text-foreground md:text-4xl">
                Admin triage now lives inside the Shadcnblocks-based FPDS operations shell.
              </h1>
              <p className="mt-3 text-sm leading-7 text-muted-foreground md:text-base">
                The live overview keeps admin compact, route-oriented, and evidence aware. It is the stable entrypoint
                for review, trace, runs, publish, usage, and dashboard health without collapsing them into one oversized
                page.
              </p>
            </div>

            <div className="inline-flex items-center rounded-full bg-success-soft px-3 py-1 text-xs font-medium text-success">
              Session verified
            </div>
          </div>

          <div className="mt-6">
            <Banner1
              defaultVisible={true}
              description="This slice refreshes the live admin shell and overview first. Queue, trace, runs, publish, usage, and health remain separate surfaces and will be wired in follow-on WBS slices."
              dismissible={false}
              title="Current slice boundary"
              tone="warning"
            />
          </div>

          <div className="mt-6 grid gap-4 md:grid-cols-2 xl:grid-cols-4">
            <div className="rounded-2xl border border-border/80 bg-background px-4 py-4">
              <p className="text-xs font-medium uppercase tracking-[0.14em] text-muted-foreground">Operator</p>
              <p className="mt-2 text-sm font-medium text-foreground">{activeSession.user.display_name}</p>
            </div>
            <div className="rounded-2xl border border-border/80 bg-background px-4 py-4">
              <p className="text-xs font-medium uppercase tracking-[0.14em] text-muted-foreground">Email</p>
              <p className="mt-2 text-sm font-medium text-foreground">{activeSession.user.email}</p>
            </div>
            <div className="rounded-2xl border border-border/80 bg-background px-4 py-4">
              <p className="text-xs font-medium uppercase tracking-[0.14em] text-muted-foreground">Role</p>
              <p className="mt-2 text-sm font-medium text-foreground">{activeSession.user.role}</p>
            </div>
            <div className="rounded-2xl border border-border/80 bg-background px-4 py-4">
              <p className="text-xs font-medium uppercase tracking-[0.14em] text-muted-foreground">Session expires</p>
              <p className="mt-2 text-sm font-medium text-foreground">{expiresAt}</p>
            </div>
          </div>
        </div>

        <Stats5 items={statItems} />

        <section className="grid gap-6 xl:grid-cols-[1.05fr_0.95fr]">
          <article className="rounded-[1.75rem] border border-border/80 bg-card/95 p-6 shadow-sm">
            <div className="flex items-start justify-between gap-4 border-b border-border/80 pb-5">
              <div>
                <p className="text-sm font-medium uppercase tracking-[0.18em] text-muted-foreground">Priority surfaces</p>
                <h2 className="mt-2 text-2xl font-semibold tracking-tight text-foreground">Route-oriented by design</h2>
                <p className="mt-2 text-sm leading-6 text-muted-foreground">
                  The shell keeps high-risk operational surfaces distinct instead of flattening them into a single
                  dashboard.
                </p>
              </div>
              <span className="rounded-full bg-info-soft px-3 py-1 text-xs font-medium text-info">Next slices ready</span>
            </div>

            <div className="mt-6 grid gap-4">
              {emptySurfaces.map((surface) => (
                <div className="rounded-2xl border border-dashed border-border bg-background px-4 py-4" key={surface.title}>
                  <div className="flex items-center justify-between gap-3">
                    <p className="font-medium text-foreground">{surface.title}</p>
                    <span className="rounded-full bg-muted px-2.5 py-1 text-[10px] font-medium uppercase tracking-[0.12em] text-muted-foreground">
                      Empty by design
                    </span>
                  </div>
                  <p className="mt-2 text-sm leading-6 text-muted-foreground">{surface.copy}</p>
                </div>
              ))}
            </div>
          </article>

          <article className="rounded-[1.75rem] border border-border/80 bg-card/95 p-6 shadow-sm">
            <div className="border-b border-border/80 pb-5">
              <p className="text-sm font-medium uppercase tracking-[0.18em] text-muted-foreground">Implementation timeline</p>
              <h2 className="mt-2 text-2xl font-semibold tracking-tight text-foreground">Resume-friendly context</h2>
              <p className="mt-2 text-sm leading-6 text-muted-foreground">
                The overview stays explicit about what is live, what changed now, and what comes next.
              </p>
            </div>

            <div className="mt-6 grid gap-4">
              {timelineItems.map((item) => (
                <div className="rounded-2xl border border-border/80 bg-background px-4 py-4" key={item.title}>
                  <div className="flex items-start justify-between gap-3">
                    <p className="font-medium text-foreground">{item.title}</p>
                    <span className="text-xs text-muted-foreground">{item.meta}</span>
                  </div>
                  <p className="mt-2 text-sm leading-6 text-muted-foreground">{item.copy}</p>
                </div>
              ))}
            </div>
          </article>
        </section>
      </section>
    </ApplicationShell5>
  );
}
