import { NextResponse } from "next/server";

import { getAdminApiOrigin } from "@/lib/admin-api";

export async function GET() {
  const apiResponse = await fetch(new URL("/api/admin/auth/countries", getAdminApiOrigin()), {
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
