import process from "node:process";

const PRODUCTION_ORIGIN = "https://www.switchabank.com";
const AUDIT_ORIGIN = new URL(
  process.env.SEO_AUDIT_ORIGIN ?? "http://127.0.0.1:3000"
);
const FORBIDDEN_PRODUCT_PARAMS = new Set([
  "q",
  "bank_code",
  "product_type",
  "target_customer_tag",
  "fee_bucket",
  "minimum_balance_bucket",
  "minimum_deposit_bucket",
  "term_bucket",
  "sort_by",
  "sort_order",
  "view",
  "page",
  "page_size",
  "gclid",
  "fbclid"
]);
const PRIORITY_PRODUCTS = [
  "prod_IbZVSqaogb3BkWBd",
  "prod_vIoiSSdl3kwJjM1d",
  "prod_g-yAIYCGJyxWOm8d",
  "prod_h18VyAGREB3optuJ",
  "prod_OOVZNobikI65DAAF"
];

async function main() {
  const robots = await readResponse("/robots.txt");
  check(robots.status === 200, "robots.txt must return 200");
  check(
    robots.body.includes("Sitemap: " + PRODUCTION_ORIGIN + "/sitemap.xml"),
    "robots.txt must reference the production sitemap"
  );
  check(!/noindex/i.test(robots.body), "robots.txt must not contain noindex");
  check(!/Disallow:\s*\/$/mi.test(robots.body), "production robots.txt must allow the public site");

  const sitemap = await readResponse("/sitemap.xml");
  check(sitemap.status === 200, "sitemap.xml must return 200");
  const sitemapEntries = parseSitemap(sitemap.body);
  check(sitemapEntries.length > 0, "sitemap.xml must contain URLs");
  validateSitemapEntries(sitemapEntries);

  const representativePaths = [
    "/",
    "/products",
    "/cards",
    "/loans",
    "/methodology",
    ...PRIORITY_PRODUCTS.map((id) => "/products/" + id)
  ];

  const representativePages = [];
  for (const path of representativePaths) {
    representativePages.push(
      await auditIndexablePage(path, productionUrl(path))
    );
  }

  const depositCatalog = representativePages.find((page) => page.path === "/products");
  const cardCatalog = representativePages.find((page) => page.path === "/cards");
  for (const [label, catalog] of [["deposit", depositCatalog], ["credit-card", cardCatalog]]) {
    const productPath = extractCleanProductHrefs(catalog.body)[0];
    check(productPath, label + " catalog must expose a server-rendered product link");
    await auditIndexablePage(productPath, productionUrl(productPath));
  }

  await auditLocalizedStaticPage("/loans?locale=ja", "ja");
  await auditNoindexCatalogVariant(
    "/loans?sort_by=display_rate&sort_order=asc&bank_code=BMO",
    PRODUCTION_ORIGIN + "/loans"
  );
  await auditNoindexProductLocale(
    "/products/prod_IbZVSqaogb3BkWBd?locale=ja",
    "ja",
    PRODUCTION_ORIGIN + "/products/prod_IbZVSqaogb3BkWBd"
  );
  await auditNoindexProductLocale(
    "/products/prod_vIoiSSdl3kwJjM1d?locale=ko",
    "ko",
    PRODUCTION_ORIGIN + "/products/prod_vIoiSSdl3kwJjM1d"
  );

  await assertRedirect(
    "/products/prod_IbZVSqaogb3BkWBd?locale=ja&sort_by=display_rate&sort_order=asc&utm_source=gsc",
    "/products/prod_IbZVSqaogb3BkWBd?locale=ja"
  );
  await assertRedirect(
    "/products/prod_vIoiSSdl3kwJjM1d?sort_by=display_rate&sort_order=asc&bank_code=CIBC&page=2",
    "/products/prod_vIoiSSdl3kwJjM1d"
  );
  await assertRedirect(
    "/products/prod_OOVZNobikI65DAAF?sort_by=display_rate&sort_order=asc",
    "/products/prod_OOVZNobikI65DAAF"
  );
  await assertRedirect(
    "/products/prod_LuH-Kei2S8uFFOyY",
    "/products/prod_SNcPg2yBYt4rgyAt"
  );

  const missing = await readResponse(
    "/products/not-a-real-product?sort_by=display_rate",
    "manual"
  );
  check(
    missing.status === 404 || missing.status === 410,
    "invalid product route must return 404 or 410 before redirecting"
  );

  const priorityByPath = new Map(
    representativePages.map((page) => [page.path, page])
  );
  check(
    priorityByPath.get("/products/prod_IbZVSqaogb3BkWBd").title.includes(
      "BMO Professional Student Line of Credit: Rate, Limits & Details"
    ),
    "BMO priority page must use the line-of-credit title template"
  );
  check(
    /BMO.+Prime Rate plus 0\.5%/i.test(
      priorityByPath.get("/products/prod_IbZVSqaogb3BkWBd").body
    ),
    "BMO priority page must render its verified prime-rate basis"
  );
  check(
    priorityByPath.get("/products/prod_IbZVSqaogb3BkWBd").description.includes(
      "low-interest rate based on BMO’s Prime Rate plus 0.5%"
    ),
    "BMO priority metadata must preserve the verified rate-basis wording"
  );
  check(
    /variable flex mortgage/i.test(
      priorityByPath.get("/products/prod_vIoiSSdl3kwJjM1d").body
    ),
    "CIBC priority page must render its product-specific variable-flex context"
  );
  check(
    /Vancity Fast and Fair Loan/i.test(
      priorityByPath.get("/products/prod_g-yAIYCGJyxWOm8d").body
    ),
    "Vancity priority page must explain the natural alternate search wording"
  );
  check(
    priorityByPath.get("/products/prod_OOVZNobikI65DAAF").title.includes(
      "The Long and Short Mortgage"
    ),
    "resolved GSC priority product must retain its product identity"
  );

  const auditedSitemapPages = await mapWithConcurrency(
    sitemapEntries,
    8,
    async (entry) => {
      const remote = new URL(entry.loc);
      return auditIndexablePage(
        remote.pathname + remote.search,
        entry.loc,
        true
      );
    }
  );
  assertUniquePageField(auditedSitemapPages, "title", "title");
  assertUniquePageField(
    auditedSitemapPages,
    "description",
    "meta description"
  );

  console.log(
    "SEO audit passed: " +
    auditedSitemapPages.length +
    " sitemap URLs and " +
    representativePaths.length +
    " representative routes."
  );
}

async function auditIndexablePage(path, expectedCanonical, quiet = false) {
  const response = await readResponse(path, "manual");
  check(response.status === 200, path + " must return 200 without redirect");
  const page = parsePage(path, response.body);
  check(
    page.titles.length === 1,
    path + " must have exactly one title; found " + page.titles.length +
      (page.titles.length ? ": " + page.titles.join(" | ") : "")
  );
  check(page.title.length > 0, path + " must have a non-empty title");
  check(page.descriptions.length === 1, path + " must have one meta description");
  check(page.description.length > 0, path + " must have a non-empty meta description");
  check(page.canonicals.length === 1, path + " must have exactly one canonical");
  check(
    normalizeComparableUrl(page.canonical) === normalizeComparableUrl(expectedCanonical),
    path + " canonical mismatch"
  );
  check(new URL(page.canonical).origin === PRODUCTION_ORIGIN, path + " canonical host mismatch");
  check(!/noindex/i.test(page.robots), path + " must be indexable");
  check(page.h1Count === 1, path + " must have exactly one H1");
  check(page.lang === expectedLang(path), path + " html lang mismatch");
  validateJsonLd(page, path);
  validateProductLinks(page.body, path);
  if (path.startsWith("/products/")) {
    check(
      page.body.includes("data-seo-product-content"),
      path + " must render primary product content in initial HTML"
    );
    const languages = new Set(page.alternates.map((item) => item.hreflang));
    check(languages.has("en-CA"), path + " must declare en-CA");
    check(languages.has("x-default"), path + " must declare x-default");
    check(!languages.has("ko") && !languages.has("ja"), path + " must exclude incomplete product locales");
  }
  if (!quiet) {
    console.log("checked " + path);
  }
  return page;
}

async function auditLocalizedStaticPage(path, locale) {
  const page = await auditIndexablePage(path, productionUrl(path));
  check(page.lang === locale, path + " must server-render the requested html lang");
  const languages = new Set(page.alternates.map((item) => item.hreflang));
  for (const language of ["en-CA", "ko", "ja", "x-default"]) {
    check(languages.has(language), path + " missing hreflang " + language);
  }
}

async function auditNoindexCatalogVariant(path, expectedCanonical) {
  const response = await readResponse(path, "manual");
  check(response.status === 200, path + " must remain usable");
  const page = parsePage(path, response.body);
  check(/noindex/i.test(page.robots) && /follow/i.test(page.robots), path + " must be noindex,follow");
  check(page.canonical === expectedCanonical, path + " must canonicalize to the clean catalog");
}

async function auditNoindexProductLocale(path, locale, expectedCanonical) {
  const response = await readResponse(path, "manual");
  check(response.status === 200, path + " must remain usable");
  const page = parsePage(path, response.body);
  check(page.lang === locale, path + " must server-render the locale");
  check(/noindex/i.test(page.robots) && /follow/i.test(page.robots), path + " must be noindex,follow");
  check(page.canonical === expectedCanonical, path + " must canonicalize to English");
  check(page.alternates.length === 0, path + " must not join an hreflang cluster");
  check(page.h1Count === 1, path + " must retain one visible H1");
}

async function assertRedirect(path, expectedLocation) {
  const response = await readResponse(path, "manual");
  check(response.status === 308, path + " must return a permanent 308");
  const location = response.headers.get("location");
  check(Boolean(location), path + " redirect must include Location");
  const resolved = new URL(location, AUDIT_ORIGIN);
  check(
    resolved.pathname + resolved.search === expectedLocation,
    path + " redirect target mismatch: " + location
  );
}

function parseSitemap(xml) {
  return [...xml.matchAll(/<url>([\s\S]*?)<\/url>/g)].map((match) => {
    const block = match[1];
    const locMatch = block.match(/<loc>([\s\S]*?)<\/loc>/);
    check(locMatch, "sitemap URL entry missing loc");
    return {
      loc: decodeEntities(locMatch[1].trim()),
      alternates: [...block.matchAll(/<xhtml:link\b([^>]*)\/>/g)].map((item) => ({
        hreflang: attribute(item[0], "hreflang"),
        href: decodeEntities(attribute(item[0], "href"))
      }))
    };
  });
}

function validateSitemapEntries(entries) {
  assertUnique(entries.map((entry) => entry.loc), "sitemap URL");
  for (const entry of entries) {
    const url = new URL(entry.loc);
    check(url.origin === PRODUCTION_ORIGIN, entry.loc + " uses an unexpected host");
    validateAllowedIndexUrl(url, "sitemap URL");
    if (url.pathname.startsWith("/products/")) {
      check(!url.searchParams.has("locale"), entry.loc + " must use the English product canonical");
      const languages = new Set(entry.alternates.map((item) => item.hreflang));
      check(languages.size === 2, entry.loc + " product alternates must contain only English and x-default");
      check(languages.has("en-CA") && languages.has("x-default"), entry.loc + " product alternates are incomplete");
      for (const alternate of entry.alternates) {
        check(!new URL(alternate.href).searchParams.has("locale"), alternate.href + " must exclude incomplete product locales");
      }
    }
  }
}

function validateAllowedIndexUrl(url, context) {
  for (const key of url.searchParams.keys()) {
    check(key === "country_code", context + " contains forbidden parameter " + key);
  }
}

function parsePage(path, body) {
  const metadataDocument = body.replace(
    /<(script|style|svg)\b[^>]*>[\s\S]*?<\/\1>/gi,
    ""
  );
  const titles = [...metadataDocument.matchAll(/<title\b[^>]*>([\s\S]*?)<\/title>/gi)]
    .map((match) => textContent(match[1]));
  const h1Count = [...body.matchAll(/<h1\b[^>]*>/gi)].length;
  const htmlTag = body.match(/<html\b[^>]*>/i)?.[0] ?? "";
  const metaTags = [...metadataDocument.matchAll(/<meta\b[^>]*>/gi)].map((match) => match[0]);
  const linkTags = [...metadataDocument.matchAll(/<link\b[^>]*>/gi)].map((match) => match[0]);
  const descriptions = metaTags
    .filter((tag) => attribute(tag, "name").toLowerCase() === "description")
    .map((tag) => decodeEntities(attribute(tag, "content")));
  const robotValues = metaTags
    .filter((tag) => ["robots", "googlebot"].includes(attribute(tag, "name").toLowerCase()))
    .map((tag) => attribute(tag, "content"));
  const canonicals = linkTags
    .filter((tag) => attribute(tag, "rel").toLowerCase() === "canonical")
    .map((tag) => decodeEntities(attribute(tag, "href")));
  const alternates = linkTags
    .filter((tag) => attribute(tag, "rel").toLowerCase() === "alternate" && attribute(tag, "hreflang"))
    .map((tag) => ({
      hreflang: attribute(tag, "hreflang"),
      href: decodeEntities(attribute(tag, "href"))
    }));
  return {
    path,
    body,
    titles,
    title: titles[0] ?? "",
    descriptions,
    description: descriptions[0] ?? "",
    canonicals,
    canonical: canonicals[0] ?? "",
    alternates,
    robots: robotValues.join(","),
    h1Count,
    lang: attribute(htmlTag, "lang"),
    jsonLd: [...body.matchAll(/<script\b[^>]*type=["']application\/ld\+json["'][^>]*>([\s\S]*?)<\/script>/gi)]
      .map((match) => match[1])
  };
}

function validateJsonLd(page, path) {
  check(page.jsonLd.length > 0, path + " must contain server-rendered JSON-LD");
  for (const payload of page.jsonLd) {
    try {
      JSON.parse(payload);
    } catch (error) {
      throw new Error(path + " contains invalid JSON-LD: " + error.message);
    }
  }
}

function validateProductLinks(body, sourcePath) {
  for (const href of extractCleanProductHrefs(body)) {
    const url = new URL(href, PRODUCTION_ORIGIN);
    for (const key of url.searchParams.keys()) {
      check(
        (key === "locale" || key === "country_code") &&
        !key.toLowerCase().startsWith("utm_") &&
        !FORBIDDEN_PRODUCT_PARAMS.has(key),
        sourcePath + " leaks " + key + " into product link " + href
      );
    }
  }
}

function extractCleanProductHrefs(body) {
  return [...body.matchAll(/<a\b[^>]*href=["']([^"']+)["'][^>]*>/gi)]
    .map((match) => decodeEntities(match[1]))
    .filter((href) => {
      try {
        return new URL(href, PRODUCTION_ORIGIN).pathname.startsWith("/products/");
      } catch {
        return false;
      }
    });
}

async function readResponse(path, redirect = "manual") {
  const url = new URL(path, AUDIT_ORIGIN);
  const response = await fetch(url, {
    redirect,
    headers: {
      accept: path.endsWith(".xml") ? "application/xml" : "text/html",
      "user-agent": "Googlebot/2.1 (+http://www.google.com/bot.html)"
    }
  });
  return {
    status: response.status,
    headers: response.headers,
    body: await response.text()
  };
}

function productionUrl(path) {
  const url = new URL(path, PRODUCTION_ORIGIN);
  return url.pathname === "/" && !url.search
    ? PRODUCTION_ORIGIN
    : url.toString();
}

function normalizeComparableUrl(value) {
  const url = new URL(value);
  return url.origin + (url.pathname === "/" ? "" : url.pathname) + url.search;
}

function expectedLang(path) {
  return new URL(path, PRODUCTION_ORIGIN).searchParams.get("locale") ?? "en";
}

function attribute(tag, name) {
  const normalizedName = name.toLowerCase();
  for (const match of tag.matchAll(/([:\w-]+)\s*=\s*(["'])(.*?)\2/g)) {
    if (match[1].toLowerCase() === normalizedName) {
      return match[3];
    }
  }
  return "";
}

function textContent(value) {
  return decodeEntities(value.replace(/<[^>]+>/g, "")).trim();
}

function decodeEntities(value) {
  return value
    .replace(/&amp;/g, "&")
    .replace(/&quot;/g, '"')
    .replace(/&#x27;|&#39;/g, "'")
    .replace(/&lt;/g, "<")
    .replace(/&gt;/g, ">");
}

function assertUnique(values, label) {
  const duplicates = [
    ...new Set(values.filter((value, index) => values.indexOf(value) !== index))
  ];
  check(
    duplicates.length === 0,
    "duplicate " + label + " values: " + duplicates.slice(0, 5).join(" | ")
  );
}

function assertUniquePageField(pages, field, label) {
  const pathsByValue = new Map();
  for (const page of pages) {
    const paths = pathsByValue.get(page[field]) ?? [];
    paths.push(page.path);
    pathsByValue.set(page[field], paths);
  }
  const duplicates = [...pathsByValue.entries()]
    .filter(([, paths]) => paths.length > 1)
    .map(([value, paths]) => value + " => " + paths.join(", "));
  check(
    duplicates.length === 0,
    "duplicate " + label + " values: " + duplicates.slice(0, 5).join(" | ")
  );
}

async function mapWithConcurrency(items, concurrency, worker) {
  const results = new Array(items.length);
  let nextIndex = 0;
  async function run() {
    while (nextIndex < items.length) {
      const index = nextIndex;
      nextIndex += 1;
      results[index] = await worker(items[index], index);
    }
  }
  await Promise.all(
    Array.from({ length: Math.min(concurrency, items.length) }, run)
  );
  return results;
}

function check(condition, message) {
  if (!condition) {
    throw new Error(message);
  }
}

main().catch((error) => {
  console.error("SEO audit failed:", error.message);
  process.exitCode = 1;
});
