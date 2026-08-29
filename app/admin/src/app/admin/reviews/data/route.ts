import { NextResponse } from "next/server";

import { getAdminApiOrigin } from "@/lib/admin-api";
import { buildReviewQueueApiSearchParams, parseReviewQueueFilters } from "@/lib/review-queue-query";

const REQUEST_TIMEOUT_MS = 12_000;

export async function GET(request: Request) {
  const requestUrl = new URL(request.url);
  const filters = parseReviewQueueFilters(requestUrl.searchParams);
  const apiUrl = new URL("/api/admin/review-tasks", getAdminApiOrigin());
  apiUrl.search = buildReviewQueueApiSearchParams(filters).toString();

  try {
    const apiResponse = await fetch(apiUrl, {
      method: "GET",
      headers: {
        ...(request.headers.get("cookie") ? { cookie: request.headers.get("cookie") as string } : {}),
      },
      cache: "no-store",
      signal: AbortSignal.timeout(REQUEST_TIMEOUT_MS),
    });
    const text = await apiResponse.text();
    return new NextResponse(text, {
      status: apiResponse.status,
      headers: {
        "Cache-Control": "no-store",
        "Content-Type": apiResponse.headers.get("content-type") ?? "application/json",
      },
    });
  } catch {
    return NextResponse.json(
      { error: { message: "Review queue request timed out." } },
      { status: 504, headers: { "Cache-Control": "no-store" } },
    );
  }
}
