"use client";

import { ArrowRight, Database, ShieldCheck, Workflow } from "lucide-react";
import { useRouter } from "next/navigation";
import { FormEvent, useMemo, useState } from "react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { cn } from "@/lib/utils";

type LoginSupportItem = {
  title: string;
  description: string;
};

interface Login2Props {
  apiOrigin: string;
  nextPath: string;
  heading?: string;
  description?: string;
  supportItems?: LoginSupportItem[];
  className?: string;
}

const defaultSupportItems: LoginSupportItem[] = [
  {
    title: "Server-managed session",
    description: "The browser signs in with an opaque cookie instead of a bearer token."
  },
  {
    title: "Tracked sign-in attempts",
    description: "Lockout-ready login attempts stay in Postgres alongside the admin auth service."
  },
  {
    title: "Review shell ready",
    description: "A successful sign-in opens the protected FPDS operations shell for the next admin slices."
  }
];

const supportIcons = [ShieldCheck, Database, Workflow] as const;

const Login2 = ({
  apiOrigin,
  nextPath,
  heading = "Operator sign-in",
  description = "Evidence-first review work begins in a secure FPDS admin shell that stays compact, route-oriented, and session aware.",
  supportItems = defaultSupportItems,
  className
}: Login2Props) => {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [pending, setPending] = useState(false);

  const safeNextPath = useMemo(() => {
    if (!nextPath.startsWith("/")) {
      return "/admin";
    }
    return nextPath;
  }, [nextPath]);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setPending(true);
    setError(null);

    try {
      const response = await fetch(`${apiOrigin}/api/admin/auth/login`, {
        method: "POST",
        credentials: "include",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({ email, password })
      });

      if (!response.ok) {
        const payload = (await response.json()) as { error?: { message?: string } };
        setError(payload.error?.message ?? "Login failed.");
        return;
      }

      router.replace(safeNextPath);
      router.refresh();
    } catch {
      setError("The admin API is unavailable. Check the FastAPI service and try again.");
    } finally {
      setPending(false);
    }
  }

  return (
    <section className={cn("min-h-screen px-4 py-8 md:px-6 md:py-10", className)}>
      <div className="mx-auto flex min-h-[calc(100vh-4rem)] w-full max-w-6xl items-center justify-center">
        <div className="grid w-full gap-6 lg:grid-cols-[1.08fr_0.92fr]">
          <div className="rounded-[1.75rem] border border-border/80 bg-gradient-to-b from-primary/10 via-background to-background p-6 shadow-sm sm:p-8">
            <div className="mb-8 inline-flex items-center gap-2 rounded-full border border-primary/20 bg-primary/5 px-3 py-1 text-xs font-semibold uppercase tracking-[0.18em] text-primary">
              <span className="h-2 w-2 rounded-full bg-primary" />
              FPDS Admin
            </div>

            <div className="max-w-xl space-y-4">
              <p className="text-sm font-medium uppercase tracking-[0.18em] text-muted-foreground">
                Protected operations console
              </p>
              <h1 className="text-balance text-4xl font-semibold tracking-tight text-foreground sm:text-5xl">
                {heading}
              </h1>
              <p className="max-w-2xl text-pretty text-base leading-7 text-muted-foreground sm:text-lg">
                {description}
              </p>
            </div>

            <div className="mt-8 grid gap-4">
              {supportItems.map((item, index) => {
                const Icon = supportIcons[index % supportIcons.length];

                return (
                  <div
                    className="flex items-start gap-4 rounded-2xl border border-border/80 bg-card/85 p-4 shadow-sm"
                    key={item.title}
                  >
                    <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl bg-primary/10 text-primary">
                      <Icon className="h-5 w-5" />
                    </div>
                    <div className="space-y-1">
                      <p className="font-medium text-foreground">{item.title}</p>
                      <p className="text-sm leading-6 text-muted-foreground">{item.description}</p>
                    </div>
                  </div>
                );
              })}
            </div>

            <div className="mt-8 rounded-2xl border border-border/80 bg-card/70 p-4 text-sm text-muted-foreground">
              SSO and remember-me behavior remain intentionally deferred until the FPDS auth roadmap explicitly
              approves them.
            </div>
          </div>

          <div className="flex items-center">
            <form
              className="w-full rounded-[1.75rem] border border-border/80 bg-card/95 p-6 shadow-sm backdrop-blur sm:p-8"
              onSubmit={handleSubmit}
            >
              <div className="space-y-2">
                <p className="text-sm font-medium uppercase tracking-[0.18em] text-muted-foreground">
                  Session sign-in
                </p>
                <h2 className="text-2xl font-semibold tracking-tight text-foreground">Enter your operator account</h2>
                <p className="text-sm leading-6 text-muted-foreground">
                  Access is limited to `admin`, `reviewer`, and `read_only` accounts provisioned through the FPDS
                  bootstrap flow.
                </p>
              </div>

              <div className="mt-8 grid gap-5">
                <div className="grid gap-2">
                  <Label htmlFor="email">Work email</Label>
                  <Input
                    autoComplete="email"
                    id="email"
                    name="email"
                    onChange={(event) => setEmail(event.target.value)}
                    placeholder="admin@example.com"
                    required
                    type="email"
                    value={email}
                  />
                </div>

                <div className="grid gap-2">
                  <Label htmlFor="password">Password</Label>
                  <Input
                    autoComplete="current-password"
                    id="password"
                    name="password"
                    onChange={(event) => setPassword(event.target.value)}
                    placeholder="Enter your password"
                    required
                    type="password"
                    value={password}
                  />
                </div>

                <div className="flex flex-wrap items-center justify-between gap-3 rounded-2xl border border-border/80 bg-muted/40 px-4 py-3 text-sm">
                  <span className="text-muted-foreground">Server-side session sign-in with DB-backed operator accounts.</span>
                  <span className="inline-flex items-center gap-2 rounded-full bg-info-soft px-3 py-1 text-xs font-medium text-info">
                    <span className="h-2 w-2 rounded-full bg-info" />
                    Secure session
                  </span>
                </div>

                <Button className="h-11 w-full rounded-xl text-sm font-medium" disabled={pending} type="submit">
                  {pending ? "Signing in..." : "Sign in to FPDS Admin"}
                  <ArrowRight className="h-4 w-4" />
                </Button>

                {error ? (
                  <div className="rounded-2xl border border-destructive/20 bg-critical-soft px-4 py-3 text-sm text-destructive">
                    <p className="font-medium">Sign-in failed</p>
                    <p className="mt-1 leading-6">{error}</p>
                  </div>
                ) : null}

                <div className="rounded-2xl border border-border/80 bg-background px-4 py-3 text-sm text-muted-foreground">
                  Use an operator account created after the admin auth migration is applied. Successful sign-in returns
                  you to <span className="font-medium text-foreground">{safeNextPath}</span>.
                </div>
              </div>
            </form>
          </div>
        </div>
      </div>
    </section>
  );
};

export { Login2 };
