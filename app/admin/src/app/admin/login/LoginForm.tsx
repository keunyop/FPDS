"use client";

import { useRouter } from "next/navigation";
import { FormEvent, useMemo, useState } from "react";

type LoginFormProps = {
  apiOrigin: string;
  nextPath: string;
};

export function LoginForm({ apiOrigin, nextPath }: LoginFormProps) {
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
    <form className="fpds-form-grid" onSubmit={handleSubmit}>
      <label className="fpds-field">
        <span className="fpds-field-label">Work email</span>
        <input
          autoComplete="email"
          className="fpds-field-input"
          name="email"
          onChange={(event) => setEmail(event.target.value)}
          placeholder="admin@example.com"
          required
          type="email"
          value={email}
        />
      </label>
      <label className="fpds-field">
        <span className="fpds-field-label">Password</span>
        <input
          autoComplete="current-password"
          className="fpds-field-input"
          name="password"
          onChange={(event) => setPassword(event.target.value)}
          placeholder="Enter your password"
          required
          type="password"
          value={password}
        />
      </label>
      <div className="fpds-inline-row">
        <p className="fpds-form-note">Server-side session sign-in with DB-backed operator accounts.</p>
        <span className="fpds-status-badge" data-tone="info">
          Secure session
        </span>
      </div>
      <button className="fpds-button fpds-button-primary" disabled={pending} type="submit">
        {pending ? "Signing in..." : "Sign in to FPDS Admin"}
      </button>
      {error ? (
        <div className="fpds-feedback" data-tone="danger">
          <strong>Sign-in failed</strong>
          <span>{error}</span>
        </div>
      ) : null}
      <div className="fpds-feedback" data-tone="info">
        <strong>Operator-only access</strong>
        <span>
          Use an operator account created through the bootstrap CLI after the admin auth migration is
          applied.
        </span>
      </div>
    </form>
  );
}
