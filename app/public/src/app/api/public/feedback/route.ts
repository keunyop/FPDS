import { NextResponse } from "next/server";

import { getPublicApiOrigin } from "@/lib/public-api";

export const dynamic = "force-dynamic";

const PRODUCT_CATEGORIES = new Set([
  "broken_link",
  "incorrect_product_details",
  "incorrect_rate_or_fee",
  "missing_information",
  "other",
  "outdated_information",
]);
const SITE_CATEGORIES = new Set([
  "accessibility_issue",
  "content_issue",
  "feature_suggestion",
  "other",
  "usability_issue",
]);

export async function POST(request: Request) {
  const contentLength = Number(request.headers.get("content-length") ?? "0");
  if (Number.isFinite(contentLength) && contentLength > 4096) {
    return NextResponse.json({ error: { code: "payload_too_large" } }, { status: 413 });
  }

  let payload: Record<string, unknown>;
  try {
    payload = await request.json() as Record<string, unknown>;
  } catch {
    return NextResponse.json({ error: { code: "invalid_payload" } }, { status: 400 });
  }

  const countryCode = stringValue(payload.country_code).toUpperCase();
  const submissionType = stringValue(payload.submission_type).toLowerCase();
  const category = stringValue(payload.category).toLowerCase();
  const details = stringValue(payload.details);
  const locale = stringValue(payload.locale).toLowerCase();
  const productId = stringValue(payload.product_id);
  const allowedCategories = submissionType === "product_error"
    ? PRODUCT_CATEGORIES
    : submissionType === "site_feedback"
      ? SITE_CATEGORIES
      : null;

  if (
    !/^[A-Z]{2}$/.test(countryCode)
    || !allowedCategories?.has(category)
    || !["en", "ko", "ja"].includes(locale)
    || details.length > 2000
    || (submissionType === "product_error" && (!productId || productId.length > 120))
    || (submissionType === "site_feedback" && productId.length > 0)
  ) {
    return NextResponse.json({ error: { code: "invalid_payload" } }, { status: 400 });
  }

  const apiSecret = process.env.FPDS_PUBLIC_APP_API_SECRET?.trim();
  if (!apiSecret) {
    return NextResponse.json(
      { error: { code: "public_app_credential_not_configured" } },
      { status: 503 }
    );
  }

  try {
    const response = await fetch(
      new URL("/api/public/feedback", getPublicApiOrigin()),
      {
        body: JSON.stringify({
          category,
          country_code: countryCode,
          details: details || null,
          locale,
          product_id: productId || null,
          submission_type: submissionType,
        }),
        cache: "no-store",
        headers: {
          "content-type": "application/json",
          "x-fpds-public-app-secret": apiSecret,
        },
        method: "POST",
      }
    );
    return new NextResponse(await response.text(), {
      status: response.status,
      headers: {
        "cache-control": "no-store",
        "content-type": response.headers.get("content-type") ?? "application/json",
      },
    });
  } catch {
    return NextResponse.json(
      { error: { code: "public_feedback_unavailable" } },
      { status: 503 }
    );
  }
}

function stringValue(value: unknown) {
  return typeof value === "string" ? value.trim() : "";
}
