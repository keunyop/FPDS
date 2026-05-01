import { NextResponse } from "next/server";

import { getAdminApiOrigin, type ReviewDecisionAction } from "@/lib/admin-api";

const ACTION_PATHS: Record<ReviewDecisionAction, string> = {
  approve: "approve",
  reject: "reject",
  edit_approve: "edit-approve",
  defer: "defer",
};
const DECISION_REQUEST_TIMEOUT_MS = 12_000;

export async function POST(
  request: Request,
  context: {
    params: Promise<{
      reviewTaskId: string;
    }>;
  },
) {
  const { reviewTaskId } = await context.params;
  const body = (await request.json()) as {
    action_type?: ReviewDecisionAction;
    reason_code?: string | null;
    reason_text?: string | null;
    override_payload?: Record<string, unknown>;
  };

  if (!body.action_type || !ACTION_PATHS[body.action_type]) {
    return NextResponse.json(
      {
        error: {
          message: "Unsupported review action.",
        },
      },
      { status: 400 },
    );
  }

  let apiResponse: Response;
  try {
    apiResponse = await fetch(
      new URL(`/api/admin/review-tasks/${reviewTaskId}/${ACTION_PATHS[body.action_type]}`, getAdminApiOrigin()),
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...(request.headers.get("cookie") ? { cookie: request.headers.get("cookie") as string } : {}),
          ...(request.headers.get("x-csrf-token") ? { "X-CSRF-Token": request.headers.get("x-csrf-token") as string } : {}),
        },
        body: JSON.stringify({
          reason_code: body.reason_code ?? null,
          reason_text: body.reason_text ?? null,
          override_payload: body.override_payload ?? {},
        }),
        cache: "no-store",
        signal: AbortSignal.timeout(DECISION_REQUEST_TIMEOUT_MS),
      },
    );
  } catch {
    return NextResponse.json(
      {
        error: {
          message: "Review action timed out. Refresh the queue before retrying because the decision may still complete server-side.",
        },
      },
      { status: 504 },
    );
  }

  const text = await apiResponse.text();
  return new NextResponse(text, {
    status: apiResponse.status,
    headers: {
      "Content-Type": apiResponse.headers.get("content-type") ?? "application/json",
    },
  });
}
