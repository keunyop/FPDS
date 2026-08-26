import type { NextRequest } from "next/server";
import { NextResponse } from "next/server";

const PRODUCT_DETAIL_PREFIX = "/products/";
const PUBLIC_LOCALES = new Set(["en", "ko", "ja"]);
const PUBLIC_API_TIMEOUT_MS = 2_000;

export async function proxy(request: NextRequest) {
  const productId = readProductId(request.nextUrl.pathname);
  if (!productId) {
    return NextResponse.next();
  }

  let response: Response;
  try {
    const apiUrl = new URL(
      "/api/public/products/" + encodeURIComponent(productId),
      process.env.FPDS_PUBLIC_API_ORIGIN ?? "http://localhost:4000"
    );
    const requestedLocale = request.nextUrl.searchParams.get("locale") ?? "en";
    const requestedCountry = (
      request.nextUrl.searchParams.get("country_code") ?? "CA"
    ).trim().toUpperCase();
    apiUrl.searchParams.set(
      "locale",
      PUBLIC_LOCALES.has(requestedLocale) ? requestedLocale : "en"
    );
    apiUrl.searchParams.set(
      "country_code",
      /^[A-Z]{2}$/.test(requestedCountry) ? requestedCountry : "CA"
    );

    response = await fetch(apiUrl, {
      headers: { accept: "application/json" },
      signal: AbortSignal.timeout(PUBLIC_API_TIMEOUT_MS)
    });
  } catch {
    return NextResponse.next();
  }

  if (response.status !== 404) {
    void response.body?.cancel();
    return NextResponse.next();
  }

  void response.body?.cancel();
  return NextResponse.rewrite(new URL("/_not-found", request.url), {
    status: 404
  });
}

export const config = {
  matcher: "/products/:productId"
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
