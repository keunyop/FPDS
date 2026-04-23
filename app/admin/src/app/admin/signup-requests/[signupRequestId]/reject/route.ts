import { NextResponse } from "next/server";

import { getAdminApiOrigin } from "@/lib/admin-api";

export async function POST(
  request: Request,
  context: {
    params: Promise<{
      signupRequestId: string;
    }>;
  },
) {
  const { signupRequestId } = await context.params;
  const body = (await request.json()) as {
    reason_text?: string | null;
  };

  const apiResponse = await fetch(
    new URL(`/api/admin/auth/signup-requests/${signupRequestId}/reject`, getAdminApiOrigin()),
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...(request.headers.get("cookie") ? { cookie: request.headers.get("cookie") as string } : {}),
        ...(request.headers.get("x-csrf-token") ? { "X-CSRF-Token": request.headers.get("x-csrf-token") as string } : {}),
      },
      body: JSON.stringify({
        reason_text: body.reason_text ?? null,
      }),
      cache: "no-store",
    },
  );

  const text = await apiResponse.text();
  return new NextResponse(text, {
    status: apiResponse.status,
    headers: {
      "Content-Type": apiResponse.headers.get("content-type") ?? "application/json",
    },
  });
}
