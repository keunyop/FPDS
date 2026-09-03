import {
  fetchPublicCountries,
  fetchPublicProducts,
  type PublicProduct
} from "@/lib/public-api";
import {
  buildPublicLanguageAlternates,
  buildPublicProductLanguageAlternates,
  buildPublicSeoUrl,
  type PublicSeoPath
} from "@/lib/public-seo";
import { buildCanonicalProductUrl } from "@/lib/public-url-policy";

export const dynamic = "force-static";
export const revalidate = 3600;

type SitemapEntry = {
  url: string;
  lastModified?: string;
  changeFrequency: "daily" | "weekly" | "monthly";
  priority: number;
  alternates: Record<string, string>;
};

const STATIC_ROUTES: Array<{
  path: PublicSeoPath;
  changeFrequency: SitemapEntry["changeFrequency"];
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

export async function GET() {
  const entries = await buildSitemapEntries();

  return new Response(serializeSitemap(entries), {
    headers: {
      "Content-Type": "application/xml; charset=utf-8"
    }
  });
}

async function buildSitemapEntries(): Promise<SitemapEntry[]> {
  const countries = await loadPublishedCountryCodes();
  const staticEntries = countries.flatMap((countryCode) =>
    STATIC_ROUTES.map(({ path, changeFrequency, priority }) => ({
      url: buildPublicSeoUrl(path, "en", countryCode),
      changeFrequency,
      priority,
      alternates: buildPublicLanguageAlternates(path, countryCode)
    }))
  );
  const productResults = await Promise.allSettled(
    countries.map((countryCode) => loadCountryProducts(countryCode))
  );
  const productEntries = productResults.flatMap((result) =>
    result.status === "fulfilled"
      ? result.value
          .filter((product) => product.status === "active")
          .map((product) => productSitemapEntry(product))
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

function productSitemapEntry(product: PublicProduct): SitemapEntry {
  const path = (
    "/products/" + encodeURIComponent(product.product_id)
  ) as PublicSeoPath;
  const lastModified = normalizeLastModified(
    product.last_changed_at ?? product.last_verified_at
  );

  return {
    url: buildCanonicalProductUrl(path, product.country_code),
    lastModified,
    changeFrequency: "weekly",
    priority: 0.7,
    alternates: buildPublicProductLanguageAlternates(path, product.country_code)
  };
}

export function serializeSitemap(entries: SitemapEntry[]) {
  const lines = [
    '<?xml version="1.0" encoding="UTF-8"?>',
    '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xhtml="http://www.w3.org/1999/xhtml">'
  ];

  for (const entry of entries) {
    lines.push("<url>", `<loc>${escapeXml(entry.url)}</loc>`);
    for (const [language, href] of Object.entries(entry.alternates)) {
      lines.push(
        `<xhtml:link rel="alternate" hreflang="${escapeXml(language)}" href="${escapeXml(href)}" />`
      );
    }
    if (entry.lastModified) {
      lines.push(`<lastmod>${escapeXml(entry.lastModified)}</lastmod>`);
    }
    lines.push(
      `<changefreq>${entry.changeFrequency}</changefreq>`,
      `<priority>${entry.priority}</priority>`,
      "</url>"
    );
  }

  lines.push("</urlset>", "");
  return lines.join("\n");
}

function escapeXml(value: string) {
  return value
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&apos;");
}

function normalizeLastModified(value: string | null) {
  if (!value) {
    return undefined;
  }

  const parsed = new Date(value);
  return Number.isNaN(parsed.getTime()) ? undefined : parsed.toISOString();
}

function deduplicateEntries(entries: SitemapEntry[]) {
  return [...new Map(entries.map((entry) => [entry.url, entry])).values()];
}
