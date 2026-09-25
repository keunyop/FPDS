import { curatedCatalogHref, isCuratedSlug } from "@/lib/public-curated";
import type { NextRequest } from "next/server";
import { NextResponse } from "next/server";

import {
  normalizeProductDetailRequest,
  normalizePublicProductLocale,
  normalizePublicProductCountry
} from "@/lib/public-url-policy";

const PRODUCT_DETAIL_PREFIX = "/products/";
const PUBLIC_LOCALE_HEADER = "x-switchabank-public-locale";
const PUBLIC_API_TIMEOUT_MS = 2_000;

export async function proxy(request: NextRequest) {
  const requestHeaders = new Headers(request.headers);
  requestHeaders.set(
    PUBLIC_LOCALE_HEADER,
    normalizePublicProductLocale(request.nextUrl.searchParams.get("locale") ?? "")
  );
  // Resolve the bounded route/country before streaming, preserving real HTTP status codes.
  if (request.nextUrl.pathname.startsWith("/ca/")) {
    const slug = request.nextUrl.pathname.slice("/ca/".length);
    if (!isCuratedSlug(slug)) {
      return NextResponse.rewrite(new URL("/_not-found", request.url), { status: 404 });
    }
    const country = normalizePublicProductCountry(request.nextUrl.searchParams.get("country_code") ?? "");
    if (country !== "CA") {
      return NextResponse.redirect(new URL(curatedCatalogHref(slug,
        normalizePublicProductLocale(request.nextUrl.searchParams.get("locale") ?? ""), country), request.url), 308);
    }
  }
  const productId = readProductId(request.nextUrl.pathname);
  if (!productId) {
    return NextResponse.next({
      request: { headers: requestHeaders }
    });
  }

  const policy = normalizeProductDetailRequest(request.nextUrl);
  let response: Response;
  try {
    const apiUrl = new URL(
      "/api/public/products/" + encodeURIComponent(productId),
      process.env.FPDS_PUBLIC_API_ORIGIN ?? "http://localhost:4000"
    );
    apiUrl.searchParams.set("locale", policy.locale);
    apiUrl.searchParams.set("country_code", policy.countryCode);

    response = await fetch(apiUrl, {
      headers: { accept: "application/json" },
      signal: AbortSignal.timeout(PUBLIC_API_TIMEOUT_MS)
    });
  } catch {
    return NextResponse.next({
      request: { headers: requestHeaders }
    });
  }

  if (response.status === 404) {
    void response.body?.cancel();
    return NextResponse.rewrite(new URL("/_not-found", request.url), {
      status: 404
    });
  }

  void response.body?.cancel();
  const currentPath = request.nextUrl.pathname + request.nextUrl.search;
  if (response.ok && currentPath !== policy.normalizedPath) {
    return NextResponse.redirect(
      new URL(policy.normalizedPath, request.url),
      308
    );
  }

  return NextResponse.next({
    request: { headers: requestHeaders }
  });
}

export const config = {
  matcher: [
    "/((?!api/|_next/|icon.svg|manifest.webmanifest|robots.txt|sitemap.xml|opengraph-image).*)"
  ]
};

function readProductId(pathname: string) {
  if (!pathname.startsWith(PRODUCT_DETAIL_PREFIX)) {
    return null;
  }

  const encodedProductId = pathname.slice(PRODUCT_DETAIL_PREFIX.length);
  if (!encodedProductId || encodedProductId.includes("/")) {
    return null;
  }

  try {
    return decodeURIComponent(encodedProductId);
  } catch {
    return null;
  }
}
