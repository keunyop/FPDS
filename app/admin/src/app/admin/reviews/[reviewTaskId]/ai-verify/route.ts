import { NextResponse } from "next/server";

import { getAdminApiOrigin } from "@/lib/admin-api";

const AI_VERIFICATION_TIMEOUT_MS = 110_000;

export async function POST(
  request: Request,
  context: {
    params: Promise<{
      reviewTaskId: string;
    }>;
  },
) {
  const { reviewTaskId } = await context.params;
  let apiResponse: Response;
  try {
    apiResponse = await fetch(
      new URL(`/api/admin/review-tasks/${reviewTaskId}/ai-verify`, getAdminApiOrigin()),
      {
        method: "POST",
        headers: {
          ...(request.headers.get("cookie") ? { cookie: request.headers.get("cookie") as string } : {}),
          ...(request.headers.get("x-csrf-token")
            ? { "X-CSRF-Token": request.headers.get("x-csrf-token") as string }
            : {}),
        },
        cache: "no-store",
        signal: AbortSignal.timeout(AI_VERIFICATION_TIMEOUT_MS),
      },
    );
  } catch {
    return NextResponse.json(
      {
        error: {
          message: "AI verification timed out before the official-source comparison completed.",
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
