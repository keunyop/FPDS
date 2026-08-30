import type { NextRequest } from "next/server";
import { NextResponse } from "next/server";

import { getPublicApiOrigin } from "@/lib/public-api";

export const dynamic = "force-dynamic";
export const revalidate = 300;

const ALLOWED_QUERY_KEYS = new Set([
  "locale",
  "country_code",
  "q",
  "product_name",
  "bank_code",
  "product_type",
  "subtype_code",
  "target_customer_tag",
  "fee_bucket",
  "minimum_balance_bucket",
  "minimum_deposit_bucket",
  "term_bucket",
  "sort_by",
  "sort_order",
  "page",
  "page_size"
]);

export async function GET(request: NextRequest) {
  const apiUrl = new URL("/api/public/products", getPublicApiOrigin());

  for (const [key, value] of request.nextUrl.searchParams.entries()) {
    if (ALLOWED_QUERY_KEYS.has(key)) {
      apiUrl.searchParams.append(
        key,
        key === "q" || key === "product_name" ? value.slice(0, 120) : value
      );
    }
  }

  try {
    const response = await fetch(apiUrl, { next: { revalidate } });
    const body = await response.text();
    return new NextResponse(body, {
      status: response.status,
      headers: {
        "cache-control": "public, s-maxage=300, stale-while-revalidate=60",
        "content-type": response.headers.get("content-type") ?? "application/json"
      }
    });
  } catch {
    return NextResponse.json(
      {
        error: {
          code: "public_products_unavailable",
          message: "Published products are temporarily unavailable."
        }
      },
      { status: 503 }
    );
  }
}
