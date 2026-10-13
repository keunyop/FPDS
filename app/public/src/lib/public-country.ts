import type { PublicCountryOption } from "./public-api.ts";
import type { PublicLocale } from "./public-locale.ts";
import { normalizePublicProductCountry } from "./public-url-policy.ts";

const COUNTRY_COPY: Record<PublicLocale, { label: string; unavailable: string }> = {
  fil: { label: "Bansa", unavailable: "Wala pang nakalathalang produkto" },
  en: { label: "Country", unavailable: "No published products" },
  ko: { label: "국가", unavailable: "공개된 상품 없음" },
  ja: { label: "国", unavailable: "公開商品なし" }
};

const INTL_LOCALES: Record<PublicLocale, string> = {
  fil: "fil-PH",
  en: "en-CA",
  ko: "ko-KR",
  ja: "ja-JP"
};

export function getPublicCountryCopy(locale: PublicLocale) {
  return COUNTRY_COPY[locale];
}

export function formatPublicCountryName(countryCode: string, locale: PublicLocale) {
  const normalized = normalizePublicProductCountry(countryCode);
  try {
    return new Intl.DisplayNames([INTL_LOCALES[locale]], { type: "region" }).of(normalized) ?? normalized;
  } catch {
    return normalized;
  }
}

/** Requested Public markets remain selectable before their first publication. */
export function publicCountryOptions(published: PublicCountryOption[], selected: string, locale: PublicLocale): PublicCountryOption[] {
  const options = new Map<string, PublicCountryOption>([["PH", { code: "PH", count: 0 }]]);
  for (const country of published) {
    if (/^[A-Z]{2}$/.test(country.code) && Number.isFinite(country.count) && country.count > 0) {
      options.set(country.code, country);
    }
  }
  const code = normalizePublicProductCountry(selected);
  if (!options.has(code)) options.set(code, { code, count: 0 });
  return [...options.values()].sort((left, right) =>
    formatPublicCountryName(left.code, locale).localeCompare(formatPublicCountryName(right.code, locale), INTL_LOCALES[locale])
  );
}

/** Presentation currency for Home groups; never a missing-product currency default. */
export function publicMarketCurrency(country: string): string | undefined {
  return ({ CA: "CAD", US: "USD", PH: "PHP" } as Record<string, string>)[country];
}
