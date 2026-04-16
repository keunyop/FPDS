import { NextResponse } from "next/server";

import { getAdminApiOrigin } from "@/lib/admin-api";

export async function POST(request: Request) {
  const apiResponse = await fetch(new URL("/api/admin/banks", getAdminApiOrigin()), {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...(request.headers.get("cookie") ? { cookie: request.headers.get("cookie") as string } : {}),
      ...(request.headers.get("x-csrf-token") ? { "X-CSRF-Token": request.headers.get("x-csrf-token") as string } : {}),
    },
    body: await request.text(),
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
