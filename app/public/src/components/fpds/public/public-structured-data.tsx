import type { PublicProduct } from "@/lib/public-api";
import {
  getPublicCatalogCopy,
  getPublicMessages,
  normalizePublicLocale
} from "@/lib/public-locale";
import {
  buildPublicSeoUrl,
  PUBLIC_SITE_NAME,
  PUBLIC_SITE_ORIGIN,
  type PublicSeoPath
} from "@/lib/public-seo";

type JsonLd = Record<string, unknown> | Array<Record<string, unknown>>;

export const PUBLIC_SITE_STRUCTURED_DATA: JsonLd = {
  "@context": "https://schema.org",
  "@type": "WebSite",
  "@id": PUBLIC_SITE_ORIGIN + "/#website",
  url: PUBLIC_SITE_ORIGIN + "/",
  name: PUBLIC_SITE_NAME,
  description:
    "Compare reviewed deposit, credit card, and loan facts across banks.",
  inLanguage: ["en", "ko", "ja"]
};

export function PublicStructuredData({ data }: Readonly<{ data: JsonLd }>) {
  return (
    <script
      type="application/ld+json"
      dangerouslySetInnerHTML={{ __html: serializeJsonLd(data) }}
    />
  );
}

export function buildProductStructuredData(
  product: PublicProduct,
  locale: string
): JsonLd {
  const normalizedLocale = normalizePublicLocale(locale);
  const copy = getPublicMessages(normalizedLocale);
  const catalog = product.product_type === "credit-card"
    ? "card"
    : product.product_family === "lending"
      ? "loan"
      : "deposit";
  const catalogPath: PublicSeoPath = catalog === "card"
    ? "/cards"
    : catalog === "loan"
      ? "/loans"
      : "/products";
  const catalogCopy = getPublicCatalogCopy(normalizedLocale, catalog);
  const productPath = (
    "/products/" + encodeURIComponent(product.product_id)
  ) as PublicSeoPath;
  const canonical = buildPublicSeoUrl(
    productPath,
    normalizedLocale,
    product.country_code
  );
  const financialProduct: Record<string, unknown> = {
    "@type": "FinancialProduct",
    "@id": canonical + "#financial-product",
    name: product.product_name,
    url: canonical,
    category: product.product_type_label,
    provider: {
      "@type": "BankOrCreditUnion",
      name: product.bank_name
    },
    areaServed: {
      "@type": "Country",
      identifier: product.country_code
    },
    inLanguage: product.source_language
  };

  return {
    "@context": "https://schema.org",
    "@graph": [
      financialProduct,
      {
        "@type": "BreadcrumbList",
        itemListElement: [
          {
            "@type": "ListItem",
            position: 1,
            name: copy.nav.dashboard,
            item: buildPublicSeoUrl("/", normalizedLocale, product.country_code)
          },
          {
            "@type": "ListItem",
            position: 2,
            name: catalogCopy.pageTitle,
            item: buildPublicSeoUrl(
              catalogPath,
              normalizedLocale,
              product.country_code
            )
          },
          {
            "@type": "ListItem",
            position: 3,
            name: product.product_name,
            item: canonical
          }
        ]
      }
    ]
  };
}

function serializeJsonLd(data: JsonLd) {
  return JSON.stringify(data).replace(/</g, "\\u003c");
}
