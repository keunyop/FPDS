import type { PublicLocale } from "@/lib/public-locale";
import { normalizeCountryCodeValue } from "@/lib/public-query";

const COUNTRY_COPY: Record<PublicLocale, { label: string; unavailable: string }> = {
  en: { label: "Country", unavailable: "No published products" },
  ko: { label: "국가", unavailable: "공개된 상품 없음" },
  ja: { label: "国", unavailable: "公開商品なし" }
};

const INTL_LOCALES: Record<PublicLocale, string> = {
  en: "en-CA",
  ko: "ko-KR",
  ja: "ja-JP"
};

export function getPublicCountryCopy(locale: PublicLocale) {
  return COUNTRY_COPY[locale];
}

export function formatPublicCountryName(countryCode: string, locale: PublicLocale) {
  const normalized = normalizeCountryCodeValue(countryCode);
  try {
    return new Intl.DisplayNames([INTL_LOCALES[locale]], { type: "region" }).of(normalized) ?? normalized;
  } catch {
    return normalized;
  }
}
