"use client";
import { ExternalLink, X } from 'lucide-react';
import { ProductVerification } from '@/components/fpds/public/product-verification';
import { BankLogo } from '@/components/fpds/public/bank-logo';
import { TrackedOfficialBankLink, TrackedProductLink } from '@/components/fpds/public/product-engagement-link';
import { Button } from '@/components/ui/button';
import { getPublicDesignCopy, getPublicMessages } from '@/lib/public-locale';
import type { PublicProduct } from '@/lib/public-api';
import { buildPublicProductMetrics } from '@/lib/public-product-presentation';
import { buildPublicHref, type ProductGridPageFilters } from '@/lib/public-query';
import { comparisonBoundary } from '@/lib/public-comparison';
import { comparisonCopy } from '@/lib/public-comparison-copy';
import { cn } from '@/lib/utils';

export function ComparePanel({
  filters,
  locale,
  onRemove,
  products,
  rowsById
}: {
  filters: ProductGridPageFilters;
  locale: string;
  onRemove: (productId: string) => void;
  products: PublicProduct[];
  rowsById?: Record<string, Array<{ key: string; label: string; value: string }>>;
}) {
  const copy = getPublicMessages(locale);
  const designCopy = getPublicDesignCopy(locale);
  const boundary = comparisonBoundary(products);
  const compareCopy = comparisonCopy(locale);
  const rowsByProduct = products.map((product) => rowsById?.[product.product_id] ?? buildCompareRows(product, locale));
  const differingKeys = new Set(
    rowsByProduct[0]
      ?.filter((row) => {
        const values = new Set(rowsByProduct.map((rows) => rows.find((candidate) => candidate.key === row.key)?.value ?? copy.common.notDisclosed));
        return values.size > 1;
      })
      .map((row) => row.key) ?? []
  );

  return (
    <section className="scroll-mt-32 border-y border-maple/30 bg-card/70 px-3 py-4 md:px-4" aria-label={copy.compare.title}>
      <div className="mb-4 flex flex-col gap-1 border-b border-border pb-3 sm:flex-row sm:items-center sm:justify-between">
        <p className="font-mono text-[10px] font-semibold uppercase tracking-[0.14em] text-maple">{copy.compare.title}</p>
        <p className="text-xs leading-5 text-muted-foreground">{designCopy.compareBoundary}</p>
      </div>
      {boundary ? <p className="mb-4 text-sm text-muted-foreground" role="note">{compareCopy[boundary]}</p> : null}
      <div className={cn("grid gap-3 md:grid-cols-2", products.length === 3 ? "xl:grid-cols-3" : products.length >= 4 ? "xl:grid-cols-4" : "")}>
        {products.map((product, productIndex) => (
          <article className="border border-border bg-background/75 p-4" key={product.product_id}>
            <div className="flex items-start justify-between gap-3">
              <div className="flex min-w-0 items-start gap-3">
                <BankLogo bankCode={product.bank_code} bankName={product.bank_name} size="sm" />
                <div className="min-w-0">
                  <TrackedProductLink className="break-words text-sm font-semibold text-foreground hover:text-primary" countryCode={product.country_code} href={buildProductDetailHref(filters, product.product_id)} productId={product.product_id}>
                    {product.product_name}
                  </TrackedProductLink>
                  <p className="mt-1 text-xs text-muted-foreground">{product.bank_name} · {product.product_type_label}</p>
                </div>
              </div>
              <button className="inline-flex size-11 shrink-0 items-center justify-center rounded-full text-muted-foreground hover:bg-muted hover:text-foreground" onClick={() => onRemove(product.product_id)} type="button" aria-label={`${copy.compare.remove}: ${product.product_name}`}>
                <X className="size-4" aria-hidden="true" />
              </button>
            </div>
            <ProductVerification product={product} locale={locale} />
            <dl className="mt-4 divide-y divide-border border-y border-border">
              {rowsByProduct[productIndex].map((row) => (
                <CompareFact different={!boundary && differingKeys.has(row.key)} key={row.key} label={row.label} value={row.value} />
              ))}
            </dl>
            {product.product_url ? (
              <Button asChild variant="outline" className="mt-4 min-h-11 w-full rounded-full">
                <TrackedOfficialBankLink countryCode={product.country_code} href={product.product_url} productId={product.product_id}>
                  {copy.detail.officialPage}
                  <ExternalLink className="size-3.5" aria-hidden="true" />
                </TrackedOfficialBankLink>
              </Button>
            ) : null}
          </article>
        ))}
      </div>
    </section>
  );
}

function CompareFact({ different, label, value }: { different: boolean; label: string; value: string }) {
  return (
    <div className={cn("px-2 py-3", different && "bg-accent/45")}>
      <dt className="text-[11px] font-medium text-muted-foreground">{label}</dt>
      <dd className="mt-1 break-words text-sm font-semibold text-foreground tabular-nums">{value}</dd>
    </div>
  );
}

function buildCompareRows(product: PublicProduct, locale: string) {
  const copy = getPublicMessages(locale);
  const typeAware = buildPublicProductMetrics(product, locale);
  return [
    { key: "type", label: copy.grid.productTypes, value: product.product_type_label },
    { key: "currency", label: comparisonCopy(locale).currency, value: product.currency || copy.common.notDisclosed },
    ...typeAware.map((metric) => ({
      key: `${product.product_type}:${metric.label}`,
      label: metric.label,
      value: metric.value
    }))
  ];
}

function buildProductDetailHref(filters: ProductGridPageFilters, productId: string) {
  return buildPublicHref(`/products/${encodeURIComponent(productId)}`, filters);
}
