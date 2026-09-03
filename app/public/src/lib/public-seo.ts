import type { Metadata } from "next";

import { formatPublicCountryName } from "@/lib/public-country";
import type { PublicProduct } from "@/lib/public-api";
import {
  normalizePublicLocale,
  type PublicLocale
} from "@/lib/public-locale";
import {
  normalizeCountryCodeValue
} from "@/lib/public-query";
import {
  buildCanonicalProductUrl,
  DEFAULT_PUBLIC_COUNTRY_CODE,
  isIndexableProductLocale,
  PUBLIC_SITE_ORIGIN
} from "@/lib/public-url-policy";

export const PUBLIC_SITE_NAME = "SwitchaBank";
export { PUBLIC_SITE_ORIGIN };

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
  const isProductDetail = path.startsWith("/products/");
  const countryName = formatPublicCountryName(
    normalizedCountryCode,
    normalizedLocale
  );
  const scopedTitle = normalizedCountryCode === DEFAULT_PUBLIC_COUNTRY_CODE
    ? title
    : title + " | " + countryName;
  const scopedDescription = normalizedCountryCode === DEFAULT_PUBLIC_COUNTRY_CODE
    ? description
    : description + " Current scope: " + countryName + ".";
  const canonical = isProductDetail
    ? buildCanonicalProductUrl(path, normalizedCountryCode)
    : buildPublicSeoUrl(path, normalizedLocale, normalizedCountryCode);
  const shouldIndex = index && (
    !isProductDetail || isIndexableProductLocale(normalizedLocale)
  );
  const languageAlternates = isProductDetail
    ? isIndexableProductLocale(normalizedLocale)
      ? buildPublicProductLanguageAlternates(path, normalizedCountryCode)
      : undefined
    : buildPublicLanguageAlternates(path, normalizedCountryCode);
  const socialTitle = scopedTitle.includes(PUBLIC_SITE_NAME)
    ? scopedTitle
    : scopedTitle + " — " + PUBLIC_SITE_NAME;
  const alternateLocales = Object.values(OPEN_GRAPH_LOCALES).filter(
    (value) => value !== OPEN_GRAPH_LOCALES[normalizedLocale]
  );

  return {
    title: scopedTitle,
    description: scopedDescription,
    alternates: {
      canonical,
      languages: languageAlternates
    },
    openGraph: {
      type: "website",
      url: canonical,
      siteName: PUBLIC_SITE_NAME,
      title: socialTitle,
      description: scopedDescription,
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
      description: scopedDescription,
      images: [new URL("/opengraph-image", PUBLIC_SITE_ORIGIN)]
    },
    robots: {
      index: shouldIndex,
      follow: true,
      googleBot: {
        index: shouldIndex,
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
    "en-CA": buildPublicSeoUrl(path, "en", countryCode),
    ko: buildPublicSeoUrl(path, "ko", countryCode),
    ja: buildPublicSeoUrl(path, "ja", countryCode),
    "x-default": buildPublicSeoUrl(path, "en", countryCode)
  };
}

export function buildPublicProductLanguageAlternates(
  path: PublicSeoPath,
  countryCode: string
) {
  const canonical = buildCanonicalProductUrl(path, countryCode);
  return {
    "en-CA": canonical,
    "x-default": canonical
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
  const displayName = buildBrandedProductName(product);
  const verifiedDate = formatSeoDate(product.last_verified_at);
  let description: string;

  if (normalizedLocale === "ko") {
    description =
      displayName + "의 공개된 금리·수수료·주요 조건을 SwitchaBank의 검토된 " +
      country + " 스냅샷에서 비교하세요." +
      (verifiedDate ? " 검증일 " + verifiedDate + "." : "");
  } else if (normalizedLocale === "ja") {
    description =
      displayName + "の公開金利・手数料・主な条件をSwitchaBankの確認済み" +
      country + "スナップショットで比較できます。" +
      (verifiedDate ? " 確認日 " + verifiedDate + "。" : "");
  } else {
    const facts = buildProductSeoFacts(product).slice(0, 2);
    const factSummary = facts.length ? ", including " + facts.join(" and ") : "";
    const verification = verifiedDate
      ? " Public snapshot verified " + verifiedDate + "; confirm current terms with " + product.bank_name + "."
      : " Confirm current terms with " + product.bank_name + ".";
    description =
      "Compare " + displayName + factSummary + " in SwitchaBank's reviewed " +
      country + " data." + verification;
  }

  return truncateDescription(description, 200);
}

export function buildProductSeoTitle(product: PublicProduct) {
  const displayName = buildBrandedProductName(product);
  const descriptor = product.product_type === "mortgage"
    ? "Rate, Term & Prepayment"
    : product.product_type === "credit-card"
      ? "Fees & Purchase Rate"
      : product.product_type === "line-of-credit"
        ? "Rate, Limits & Details"
        : product.product_type === "personal-loan"
          ? "Rate, Amount & Term"
          : product.product_type === "gic"
            ? "Rate, Term & Details"
            : "Rates, Fees & Details";
  return displayName + ": " + descriptor;
}

export function buildBrandedProductName(product: PublicProduct) {
  const productName = product.product_name.trim();
  const bankName = product.bank_name.trim();
  return productName.toLocaleLowerCase().startsWith(bankName.toLocaleLowerCase())
    ? productName
    : bankName + " " + productName;
}

function buildProductSeoFacts(product: PublicProduct) {
  const candidates: Array<string | null> = [];

  if (product.product_type === "mortgage") {
    candidates.push(
      product.rate_type ? product.rate_type + " rate" : null,
      product.term_length_text,
      isCleanSummary(product.prepayment_privileges)
        ? product.prepayment_privileges
        : null
    );
  } else if (product.product_type === "line-of-credit") {
    candidates.push(product.interest_rate_summary, product.credit_limit_text);
  } else if (product.product_type === "personal-loan") {
    candidates.push(
      product.loan_amount_text ? "loan amount " + product.loan_amount_text : null,
      product.term_length_text ? "term " + product.term_length_text : null,
      product.interest_rate_summary
    );
  } else if (product.product_type === "credit-card") {
    candidates.push(
      product.annual_fee !== null
        ? product.currency + " " + product.annual_fee + " annual fee"
        : null,
      product.purchase_interest_rate_summary
    );
  } else {
    candidates.push(
      product.public_display_rate !== null
        ? product.public_display_rate + "% published rate"
        : null,
      product.public_display_fee !== null
        ? product.currency + " " + product.public_display_fee + " published fee"
        : null,
      product.minimum_deposit !== null
        ? product.currency + " " + product.minimum_deposit + " minimum deposit"
        : null,
      product.minimum_balance !== null
        ? product.currency + " " + product.minimum_balance + " minimum balance"
        : null
    );
  }

  return candidates
    .filter((value): value is string => Boolean(value?.trim()))
    .map((value) => truncateFact(value));
}

function isCleanSummary(value: string | null) {
  return Boolean(
    value &&
    value.length <= 120 &&
    !/(calculator|view tool|click|learn more)/i.test(value)
  );
}

function truncateFact(value: string, maxLength = 72) {
  const normalized = value.replace(/\s+/g, " ").trim().replace(/[.]+$/, "");
  if (normalized.length <= maxLength) {
    return normalized;
  }
  const shortened = normalized.slice(0, maxLength - 1);
  const lastSpace = shortened.lastIndexOf(" ");
  return (lastSpace > maxLength * 0.65 ? shortened.slice(0, lastSpace) : shortened) + "…";
}

function formatSeoDate(value: string | null) {
  if (!value) {
    return "";
  }
  const parsed = new Date(value);
  return Number.isNaN(parsed.getTime()) ? "" : parsed.toISOString().slice(0, 10);
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
