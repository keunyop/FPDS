import type { Metadata } from "next";

import { formatPublicCountryName } from "@/lib/public-country";
import type { PublicProduct } from "@/lib/public-api";
import {
  normalizePublicLocale,
  type PublicLocale
} from "@/lib/public-locale";
import {
  DEFAULT_PUBLIC_COUNTRY_CODE,
  normalizeCountryCodeValue
} from "@/lib/public-query";

export const PUBLIC_SITE_ORIGIN = "https://www.switchabank.com";
export const PUBLIC_SITE_NAME = "SwitchaBank";

export type PublicSeoPath =
  | "/"
  | "/products"
  | "/cards"
  | "/loans"
  | "/methodology"
  | `/products/${string}`;

type PublicPageMetadataInput = {
  title: string;
  description: string;
  path: PublicSeoPath;
  locale: string;
  countryCode: string;
  index?: boolean;
};

const OPEN_GRAPH_LOCALES: Record<PublicLocale, string> = {
  en: "en_CA",
  ko: "ko_KR",
  ja: "ja_JP"
};

const CANONICAL_SEARCH_KEYS = new Set(["locale", "country_code"]);

export function buildPublicPageMetadata({
  title,
  description,
  path,
  locale,
  countryCode,
  index = true
}: PublicPageMetadataInput): Metadata {
  const normalizedLocale = normalizePublicLocale(locale);
  const normalizedCountryCode = normalizeCountryCodeValue(countryCode);
  const canonical = buildPublicSeoUrl(path, normalizedLocale, normalizedCountryCode);
  const socialTitle = title.includes(PUBLIC_SITE_NAME)
    ? title
    : title + " — " + PUBLIC_SITE_NAME;
  const alternateLocales = Object.values(OPEN_GRAPH_LOCALES).filter(
    (value) => value !== OPEN_GRAPH_LOCALES[normalizedLocale]
  );

  return {
    title,
    description,
    alternates: {
      canonical,
      languages: buildPublicLanguageAlternates(path, normalizedCountryCode)
    },
    openGraph: {
      type: "website",
      url: canonical,
      siteName: PUBLIC_SITE_NAME,
      title: socialTitle,
      description,
      locale: OPEN_GRAPH_LOCALES[normalizedLocale],
      alternateLocale: alternateLocales,
      images: [{
        url: new URL("/opengraph-image", PUBLIC_SITE_ORIGIN),
        width: 1200,
        height: 630,
        alt: "SwitchaBank — compare banks and financial products"
      }]
    },
    twitter: {
      card: "summary_large_image",
      title: socialTitle,
      description,
      images: [new URL("/opengraph-image", PUBLIC_SITE_ORIGIN)]
    },
    robots: {
      index,
      follow: true,
      googleBot: {
        index,
        follow: true,
        "max-image-preview": "large",
        "max-snippet": -1,
        "max-video-preview": -1
      }
    }
  };
}

export function buildPublicSeoUrl(
  path: PublicSeoPath,
  locale: string,
  countryCode: string
) {
  const normalizedLocale = normalizePublicLocale(locale);
  const normalizedCountryCode = normalizeCountryCodeValue(countryCode);
  const url = new URL(path, PUBLIC_SITE_ORIGIN);

  if (normalizedLocale !== "en") {
    url.searchParams.set("locale", normalizedLocale);
  }
  if (normalizedCountryCode !== DEFAULT_PUBLIC_COUNTRY_CODE) {
    url.searchParams.set("country_code", normalizedCountryCode);
  }

  return url.toString();
}

export function buildPublicLanguageAlternates(
  path: PublicSeoPath,
  countryCode: string
) {
  return {
    en: buildPublicSeoUrl(path, "en", countryCode),
    ko: buildPublicSeoUrl(path, "ko", countryCode),
    ja: buildPublicSeoUrl(path, "ja", countryCode),
    "x-default": buildPublicSeoUrl(path, "en", countryCode)
  };
}

export function hasNonCanonicalSearchParams(
  searchParams: Record<string, string | string[] | undefined>
) {
  return Object.keys(searchParams).some((key) => !CANONICAL_SEARCH_KEYS.has(key));
}

export function buildProductSeoDescription(
  product: PublicProduct,
  locale: string
) {
  const normalizedLocale = normalizePublicLocale(locale);
  const country = formatPublicCountryName(product.country_code, normalizedLocale);
  let description: string;

  if (normalizedLocale === "ko") {
    description =
      product.bank_name + "의 " + product.product_name +
      " 금리·수수료·주요 조건을 SwitchaBank의 검토된 " + country +
      " 공개 스냅샷에서 비교하세요.";
  } else if (normalizedLocale === "ja") {
    description =
      product.bank_name + "の" + product.product_name +
      "について、金利・手数料・主な条件をSwitchaBankの確認済み" + country +
      "公開スナップショットで比較できます。";
  } else {
    description =
      "Compare published rates, fees, and key conditions for " +
      product.product_name + " from " + product.bank_name +
      " in SwitchaBank's reviewed " + country + " snapshot.";
  }

  return truncateDescription(description);
}

function truncateDescription(value: string, maxLength = 170) {
  const normalized = value.replace(/\s+/g, " ").trim();
  if (normalized.length <= maxLength) {
    return normalized;
  }

  const shortened = normalized.slice(0, maxLength - 1);
  const lastSpace = shortened.lastIndexOf(" ");
  return (lastSpace > maxLength * 0.7 ? shortened.slice(0, lastSpace) : shortened) + "…";
}
