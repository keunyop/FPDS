"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import type { SignupRequestItem, SignupRequestListResponse } from "@/lib/admin-api";
import { formatAdminDateTime, type AdminLocale } from "@/lib/admin-i18n";

type SignupRequestReviewPanelProps = {
  csrfToken: string | null | undefined;
  locale: AdminLocale;
  requests: SignupRequestListResponse | null;
};

type ReviewAction = "approve" | "reject";

type PanelCopy = {
  eyebrow: string;
  title: string;
  description: string;
  unavailable: string;
  empty: string;
  pendingCount: string;
  requestedAt: string;
  loginId: string;
  displayName: string;
  role: string;
  note: string;
  notePlaceholder: string;
  approve: string;
  approving: string;
  reject: string;
  rejecting: string;
  approved: string;
  rejected: string;
  reviewFailed: string;
};

const BASE_COPY: PanelCopy = {
  eyebrow: "Access requests",
  title: "Pending signup requests",
  description: "Approve a request with a role, or reject it.",
  unavailable: "Access requests could not be loaded.",
  empty: "No pending signup requests.",
  pendingCount: "Pending",
  requestedAt: "Requested",
  loginId: "Id",
  displayName: "Name",
  role: "Role",
  note: "Note",
  notePlaceholder: "Optional note",
  approve: "Approve",
  approving: "Approving...",
  reject: "Reject",
  rejecting: "Rejecting...",
  approved: "Request approved.",
  rejected: "Request rejected.",
  reviewFailed: "Request review failed.",
};

const PANEL_COPY: Record<AdminLocale, PanelCopy> = {
  en: BASE_COPY,
  ko: BASE_COPY,
  ja: BASE_COPY,
};

export function SignupRequestReviewPanel({ csrfToken, locale, requests }: SignupRequestReviewPanelProps) {
  const copy = PANEL_COPY[locale];

  return (
    <section className="rounded-[1.75rem] border border-border/80 bg-card/95 p-6 shadow-sm md:p-8">
      <div className="flex flex-col gap-3 border-b border-border/80 pb-5 md:flex-row md:items-end md:justify-between">
        <div className="max-w-3xl">
          <p className="text-sm font-medium uppercase tracking-[0.18em] text-muted-foreground">{copy.eyebrow}</p>
          <h2 className="mt-2 text-2xl font-semibold tracking-tight text-foreground">{copy.title}</h2>
          <p className="mt-2 text-sm leading-6 text-muted-foreground">{copy.description}</p>
        </div>
        <div className="inline-flex items-center rounded-full bg-info-soft px-3 py-1 text-xs font-medium text-info">
          {copy.pendingCount}: {requests?.summary.pending_items ?? 0}
        </div>
      </div>

      {!requests ? (
        <div className="mt-6 rounded-2xl border border-dashed border-border bg-background px-4 py-4 text-sm text-muted-foreground">
          {copy.unavailable}
        </div>
      ) : requests.items.length === 0 ? (
        <div className="mt-6 rounded-2xl border border-dashed border-border bg-background px-4 py-4 text-sm text-muted-foreground">
          {copy.empty}
        </div>
      ) : (
        <div className="mt-6 grid gap-4">
          {requests.items.map((item) => (
            <SignupRequestReviewCard csrfToken={csrfToken} item={item} key={item.signup_request_id} locale={locale} />
          ))}
        </div>
      )}
    </section>
  );
}

function SignupRequestReviewCard({
  csrfToken,
  item,
  locale,
}: {
  csrfToken: string | null | undefined;
  item: SignupRequestItem;
  locale: AdminLocale;
}) {
  const router = useRouter();
  const copy = PANEL_COPY[locale];
  const [role, setRole] = useState("reviewer");
  const [reasonText, setReasonText] = useState("");
  const [pendingAction, setPendingAction] = useState<ReviewAction | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function handleReview(action: ReviewAction) {
    setPendingAction(action);
    setMessage(null);
    setError(null);

    try {
      const response = await fetch(`/admin/signup-requests/${item.signup_request_id}/${action}`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...(csrfToken ? { "X-CSRF-Token": csrfToken } : {}),
        },
        body: JSON.stringify({
          role: action === "approve" ? role : null,
          reason_text: reasonText || null,
        }),
      });

      const payload = (await response.json()) as { error?: { message?: string } };
      if (!response.ok) {
        setError(payload.error?.message ?? copy.reviewFailed);
        return;
      }

      setMessage(action === "approve" ? copy.approved : copy.rejected);
      router.refresh();
    } catch {
      setError(copy.reviewFailed);
    } finally {
      setPendingAction(null);
    }
  }

  return (
    <article className="rounded-2xl border border-border/80 bg-background p-4">
      <div className="grid gap-4 lg:grid-cols-[minmax(0,1fr)_minmax(18rem,22rem)]">
        <div className="grid gap-3">
          <DataRow label={copy.loginId} value={item.login_id} />
          <DataRow label={copy.displayName} value={item.display_name} />
          <DataRow label={copy.requestedAt} value={formatAdminDateTime(locale, item.requested_at)} />
        </div>

        <div className="grid gap-3">
          <label className="grid gap-2 text-sm">
            <span className="font-medium text-foreground">{copy.role}</span>
            <select
              className="h-10 rounded-xl border border-input bg-background px-3 text-sm text-foreground outline-none"
              onChange={(event) => setRole(event.target.value)}
              value={role}
            >
              <option value="reviewer">reviewer</option>
              <option value="read_only">read_only</option>
              <option value="admin">admin</option>
            </select>
          </label>

          <label className="grid gap-2 text-sm">
            <span className="font-medium text-foreground">{copy.note}</span>
            <Input onChange={(event) => setReasonText(event.target.value)} placeholder={copy.notePlaceholder} value={reasonText} />
          </label>

          <div className="flex flex-wrap gap-2">
            <Button disabled={pendingAction !== null} onClick={() => handleReview("approve")} type="button">
              {pendingAction === "approve" ? copy.approving : copy.approve}
            </Button>
            <Button disabled={pendingAction !== null} onClick={() => handleReview("reject")} type="button" variant="outline">
              {pendingAction === "reject" ? copy.rejecting : copy.reject}
            </Button>
          </div>

          {message ? <p className="text-sm text-success">{message}</p> : null}
          {error ? <p className="text-sm text-destructive">{error}</p> : null}
        </div>
      </div>
    </article>
  );
}

function DataRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-2xl border border-border/80 bg-card px-4 py-3">
      <p className="text-xs font-medium uppercase tracking-[0.14em] text-muted-foreground">{label}</p>
      <p className="mt-2 text-sm font-medium text-foreground">{value}</p>
    </div>
  );
}
