import { NextResponse } from "next/server";

import { getPublicApiOrigin } from "@/lib/public-api";

export const revalidate = 300;

export async function GET() {
  try {
    const response = await fetch(new URL("/api/public/countries", getPublicApiOrigin()), {
      next: { revalidate }
    });
    const body = await response.text();
    return new NextResponse(body, {
      status: response.status,
      headers: {
        "content-type": response.headers.get("content-type") ?? "application/json"
      }
    });
  } catch {
    return NextResponse.json(
      {
        error: {
          code: "country_catalog_unavailable",
          message: "Published country options are temporarily unavailable."
        }
      },
      { status: 503 }
    );
  }
}
