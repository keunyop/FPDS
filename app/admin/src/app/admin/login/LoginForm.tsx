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
    <form className="form-grid" onSubmit={handleSubmit}>
      <label className="field-label">
        Work email
        <input
          autoComplete="email"
          name="email"
          onChange={(event) => setEmail(event.target.value)}
          placeholder="admin@example.com"
          required
          type="email"
          value={email}
        />
      </label>
      <label className="field-label">
        Password
        <input
          autoComplete="current-password"
          name="password"
          onChange={(event) => setPassword(event.target.value)}
          required
          type="password"
          value={password}
        />
      </label>
      <button className="primary-button" disabled={pending} type="submit">
        {pending ? "Signing in..." : "Sign in to FPDS Admin"}
      </button>
      {error ? <div className="error-banner">{error}</div> : null}
      <div className="hint-banner">
        Use an operator account created through the bootstrap CLI after the admin auth migration is applied.
      </div>
    </form>
  );
}
