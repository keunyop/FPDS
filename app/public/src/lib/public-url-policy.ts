export const PUBLIC_SITE_ORIGIN = "https://www.switchabank.com";
export const DEFAULT_PUBLIC_COUNTRY_CODE = "CA";

const PUBLIC_LOCALES = new Set(["en", "ko", "ja"]);
const CANONICAL_PRODUCT_ID_BY_DUPLICATE = new Map([
  ["prod_LuH-Kei2S8uFFOyY", "prod_SNcPg2yBYt4rgyAt"]
]);

export type ProductDetailUrlPolicy = {
  countryCode: string;
  indexable: boolean;
  locale: "en" | "ko" | "ja";
  normalizedPath: string;
};

export function normalizePublicProductLocale(value: string) {
  const locale = value.trim().toLowerCase();
  return (PUBLIC_LOCALES.has(locale) ? locale : "en") as ProductDetailUrlPolicy["locale"];
}

export function normalizePublicProductCountry(value: string) {
  const countryCode = value.trim().toUpperCase();
  return /^[A-Z]{2}$/.test(countryCode)
    ? countryCode
    : DEFAULT_PUBLIC_COUNTRY_CODE;
}

export function isIndexableProductLocale(locale: string) {
  return normalizePublicProductLocale(locale) === "en";
}

export function buildProductDetailPath(
  pathname: string,
  locale: string,
  countryCode: string
) {
  const normalizedLocale = normalizePublicProductLocale(locale);
  const normalizedCountryCode = normalizePublicProductCountry(countryCode);
  const url = new URL(canonicalizeProductPath(pathname), PUBLIC_SITE_ORIGIN);

  url.search = "";
  url.hash = "";
  if (normalizedLocale !== "en") {
    url.searchParams.set("locale", normalizedLocale);
  }
  if (normalizedCountryCode !== DEFAULT_PUBLIC_COUNTRY_CODE) {
    url.searchParams.set("country_code", normalizedCountryCode);
  }

  return url.pathname + url.search;
}

export function normalizeProductDetailRequest(url: URL): ProductDetailUrlPolicy {
  const locale = normalizePublicProductLocale(url.searchParams.get("locale") ?? "");
  const countryCode = normalizePublicProductCountry(
    url.searchParams.get("country_code") ?? ""
  );

  return {
    countryCode,
    indexable: isIndexableProductLocale(locale),
    locale,
    normalizedPath: buildProductDetailPath(url.pathname, locale, countryCode)
  };
}

export function buildCanonicalProductUrl(pathname: string, countryCode: string) {
  return new URL(
    buildProductDetailPath(pathname, "en", countryCode),
    PUBLIC_SITE_ORIGIN
  ).toString();
}

function canonicalizeProductPath(pathname: string) {
  const match = pathname.match(/^\/products\/([^/]+)$/);
  if (!match) {
    return pathname;
  }

  try {
    const productId = decodeURIComponent(match[1]);
    const canonicalProductId = CANONICAL_PRODUCT_ID_BY_DUPLICATE.get(productId);
    return canonicalProductId
      ? "/products/" + encodeURIComponent(canonicalProductId)
      : pathname;
  } catch {
    return pathname;
  }
}
