import { NextResponse } from "next/server";

import { getAdminApiOrigin } from "@/lib/admin-api";

type RouteContext = {
  params: Promise<{ catalogItemId: string }>;
};

export async function GET(request: Request, context: RouteContext) {
  const { catalogItemId } = await context.params;
  const apiResponse = await fetch(new URL(`/api/admin/source-catalog/${catalogItemId}`, getAdminApiOrigin()), {
    method: "GET",
    headers: {
      ...(request.headers.get("cookie") ? { cookie: request.headers.get("cookie") as string } : {}),
    },
    cache: "no-store",
  });

  const text = await apiResponse.text();
  return new NextResponse(text, {
    status: apiResponse.status,
    headers: {
      "Content-Type": apiResponse.headers.get("content-type") ?? "application/json",
    },
  });
}
