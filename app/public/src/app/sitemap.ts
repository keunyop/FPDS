import type { MetadataRoute } from "next";

import {
  fetchPublicCountries,
  fetchPublicProducts,
  type PublicProduct
} from "@/lib/public-api";
import {
  buildPublicLanguageAlternates,
  buildPublicSeoUrl,
  type PublicSeoPath
} from "@/lib/public-seo";

export const revalidate = 3600;

const STATIC_ROUTES: Array<{
  path: PublicSeoPath;
  changeFrequency: "daily" | "weekly" | "monthly";
  priority: number;
}> = [
  { path: "/", changeFrequency: "daily", priority: 1 },
  { path: "/products", changeFrequency: "daily", priority: 0.9 },
  { path: "/cards", changeFrequency: "daily", priority: 0.9 },
  { path: "/loans", changeFrequency: "daily", priority: 0.9 },
  { path: "/methodology", changeFrequency: "monthly", priority: 0.6 }
];

const SITEMAP_PAGE_SIZE = 100;
const SITEMAP_PAGE_LIMIT = 50;

export default async function sitemap(): Promise<MetadataRoute.Sitemap> {
  const countries = await loadPublishedCountryCodes();
  const staticEntries = countries.flatMap((countryCode) =>
    STATIC_ROUTES.map(({ path, changeFrequency, priority }) => ({
      url: buildPublicSeoUrl(path, "en", countryCode),
      changeFrequency,
      priority,
      alternates: {
        languages: buildPublicLanguageAlternates(path, countryCode)
      }
    }))
  );
  const productResults = await Promise.allSettled(
    countries.map((countryCode) => loadCountryProducts(countryCode))
  );
  const productEntries = productResults.flatMap((result) =>
    result.status === "fulfilled"
      ? result.value.map((product) => productSitemapEntry(product))
      : []
  );

  return deduplicateEntries([...staticEntries, ...productEntries]);
}

async function loadPublishedCountryCodes() {
  try {
    const response = await fetchPublicCountries();
    const countryCodes = response.countries
      .map((country) => country.code.trim().toUpperCase())
      .filter((countryCode) => /^[A-Z]{2}$/.test(countryCode));
    return countryCodes.length ? [...new Set(countryCodes)] : ["CA"];
  } catch {
    return ["CA"];
  }
}

async function loadCountryProducts(countryCode: string) {
  const products: PublicProduct[] = [];

  for (let page = 1; page <= SITEMAP_PAGE_LIMIT; page += 1) {
    const searchParams = new URLSearchParams({
      locale: "en",
      country_code: countryCode,
      page: String(page),
      page_size: String(SITEMAP_PAGE_SIZE),
      sort_by: "last_changed_at",
      sort_order: "desc"
    });
    const response = await fetchPublicProducts(searchParams);
    products.push(...response.items);

    if (!response.has_next_page || page >= response.total_pages) {
      break;
    }
  }

  return products;
}

function productSitemapEntry(
  product: PublicProduct
): MetadataRoute.Sitemap[number] {
  const path = (
    "/products/" + encodeURIComponent(product.product_id)
  ) as PublicSeoPath;
  const lastModified = normalizeLastModified(
    product.last_changed_at ?? product.last_verified_at
  );

  return {
    url: buildPublicSeoUrl(path, "en", product.country_code),
    lastModified,
    changeFrequency: "weekly",
    priority: 0.7,
    alternates: {
      languages: buildPublicLanguageAlternates(path, product.country_code)
    }
  };
}

function normalizeLastModified(value: string | null) {
  if (!value) {
    return undefined;
  }

  const parsed = new Date(value);
  return Number.isNaN(parsed.getTime()) ? undefined : parsed.toISOString();
}

function deduplicateEntries(entries: MetadataRoute.Sitemap) {
  return [...new Map(entries.map((entry) => [entry.url, entry])).values()];
}
