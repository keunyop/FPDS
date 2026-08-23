"use client";

import { Check, ExternalLink, GitCompareArrows, LoaderCircle, Plus, RefreshCw, X } from "lucide-react";
import Link from "next/link";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";

import { BankLogo } from "@/components/fpds/public/bank-logo";
import { Button } from "@/components/ui/button";
import { formatPublicMessage, getPublicDesignCopy, getPublicDiscoveryCopy, getPublicMessages } from "@/lib/public-locale";
import type { PublicProduct, PublicProductsResponse } from "@/lib/public-api";
import { buildPublicProductMetrics, buildPublicSortMetric } from "@/lib/public-product-presentation";
import { buildPublicHref, type ProductGridPageFilters } from "@/lib/public-query";
import { cn } from "@/lib/utils";

const MAX_COMPARE_PRODUCTS = 4;

type ProductCompareWorkspaceProps = {
  filters: ProductGridPageFilters;
  initialProducts: PublicProductsResponse;
  locale: string;
  productsQuery: string;
};

type ProductPresentationProps = {
  compareDisabled: boolean;
  filters: ProductGridPageFilters;
  locale: string;
  onToggle: () => void;
  product: PublicProduct;
  selected: boolean;
};

type PublicProductsEnvelope = {
  data: PublicProductsResponse;
};

type LoadState = "idle" | "loading" | "error";

export function ProductCompareWorkspace({
  filters,
  initialProducts,
  locale,
  productsQuery
}: ProductCompareWorkspaceProps) {
  const copy = getPublicMessages(locale);
  const discoveryCopy = getPublicDiscoveryCopy(locale);
  const [products, setProducts] = useState<PublicProduct[]>(initialProducts.items);
  const [selectedIds, setSelectedIds] = useState<string[]>([]);
  const [nextPage, setNextPage] = useState(initialProducts.page + 1);
  const [hasNextPage, setHasNextPage] = useState(initialProducts.has_next_page);
  const [loadState, setLoadState] = useState<LoadState>("idle");
  const [resolvedViewMode, setResolvedViewMode] = useState<"grid" | "list">(
    filters.viewMode === "list" ? "list" : "grid"
  );
  const requestRef = useRef<AbortController | null>(null);
  const sentinelRef = useRef<HTMLDivElement | null>(null);
  const selectedProducts = useMemo(
    () => selectedIds.map((productId) => products.find((product) => product.product_id === productId)).filter((product): product is PublicProduct => Boolean(product)),
    [products, selectedIds]
  );

  useEffect(() => {
    if (filters.viewMode !== "auto") {
      setResolvedViewMode(filters.viewMode);
      return;
    }

    const media = window.matchMedia("(max-width: 767px)");
    const update = () => setResolvedViewMode(media.matches ? "list" : "grid");
    update();
    media.addEventListener("change", update);
    return () => media.removeEventListener("change", update);
  }, [filters.viewMode]);

  useEffect(() => {
    requestRef.current?.abort();
    requestRef.current = null;
    setProducts(initialProducts.items);
    setSelectedIds([]);
    setNextPage(initialProducts.page + 1);
    setHasNextPage(initialProducts.has_next_page);
    setLoadState("idle");
  }, [productsQuery]);

  useEffect(() => {
    return () => requestRef.current?.abort();
  }, []);

  const loadMore = useCallback(async () => {
    if (!hasNextPage || loadState === "loading") {
      return;
    }

    const controller = new AbortController();
    requestRef.current?.abort();
    requestRef.current = controller;
    setLoadState("loading");

    try {
      const params = new URLSearchParams(productsQuery);
      params.set("page", String(nextPage));
      const response = await fetch(`/api/public/products?${params.toString()}`, {
        cache: "no-store",
        signal: controller.signal
      });
      if (!response.ok) {
        throw new Error("More public products could not be loaded.");
      }

      const envelope = await response.json() as PublicProductsEnvelope;
      const nextProducts = envelope.data;
      if (nextProducts.page !== nextPage) {
        throw new Error("The public products page did not match the requested page.");
      }

      setProducts((current) => {
        const existingIds = new Set(current.map((product) => product.product_id));
        return [
          ...current,
          ...nextProducts.items.filter((product) => !existingIds.has(product.product_id))
        ];
      });
      setNextPage(nextProducts.page + 1);
      setHasNextPage(nextProducts.has_next_page);
      setLoadState("idle");
    } catch (error) {
      if (error instanceof DOMException && error.name === "AbortError") {
        return;
      }
      setLoadState("error");
    } finally {
      if (requestRef.current === controller) {
        requestRef.current = null;
      }
    }
  }, [hasNextPage, loadState, nextPage, productsQuery]);

  useEffect(() => {
    const sentinel = sentinelRef.current;
    if (!sentinel || !hasNextPage || loadState === "error") {
      return;
    }

    const observer = new IntersectionObserver(
      (entries) => {
        if (entries.some((entry) => entry.isIntersecting)) {
          void loadMore();
        }
      },
      { rootMargin: "320px 0px" }
    );
    observer.observe(sentinel);
    return () => observer.disconnect();
  }, [hasNextPage, loadMore, loadState]);

  function toggleProduct(productId: string) {
    setSelectedIds((current) => {
      if (current.includes(productId)) {
        return current.filter((id) => id !== productId);
      }
      if (current.length >= MAX_COMPARE_PRODUCTS) {
        return current;
      }
      return [...current, productId];
    });
  }

  return (
    <section className="grid gap-4" aria-labelledby="compare-products-title">
      <div className="sticky top-16 z-20 flex items-center justify-between gap-3 border-y border-foreground/15 bg-background/95 px-1 py-2.5 backdrop-blur-xl">
        <div className="min-w-0">
          <h2 id="compare-products-title" className="flex items-center gap-2 whitespace-nowrap text-xs font-semibold text-foreground sm:text-sm">
            <GitCompareArrows className="size-4 text-primary" aria-hidden="true" />
            {copy.compare.title}
          </h2>
        </div>
        <div className="flex shrink-0 items-center gap-1 sm:gap-2">
          <span className="whitespace-nowrap font-mono text-[11px] font-semibold text-muted-foreground" aria-label={copy.compare.selectedCount.replace("{count}", String(selectedProducts.length)).replace("{limit}", String(MAX_COMPARE_PRODUCTS))}>
            {copy.compare.selectedCount.replace("{count}", String(selectedProducts.length)).replace("{limit}", String(MAX_COMPARE_PRODUCTS))}
          </span>
          {selectedProducts.length ? (
            <Button onClick={() => setSelectedIds([])} size="sm" type="button" variant="ghost">
              <X className="size-4" aria-hidden="true" />
              {copy.compare.clear}
            </Button>
          ) : null}
        </div>
      </div>

      {selectedProducts.length ? (
        <ComparePanel
          filters={filters}
          locale={locale}
          onRemove={(productId) => setSelectedIds((current) => current.filter((id) => id !== productId))}
          products={selectedProducts}
        />
      ) : null}

      <section className={cn("grid", resolvedViewMode === "list" ? "gap-2" : "gap-5 md:grid-cols-2 xl:grid-cols-3")}>
        {products.map((product) => {
          const selected = selectedIds.includes(product.product_id);
          const compareDisabled = !selected && selectedIds.length >= MAX_COMPARE_PRODUCTS;
          const presentationProps = {
            compareDisabled,
            filters,
            locale,
            onToggle: () => toggleProduct(product.product_id),
            product,
            selected
          };

          return resolvedViewMode === "list" ? (
            <ProductCompareListItem
              {...presentationProps}
              key={product.product_id}
            />
          ) : (
            <ProductCompareCard
              {...presentationProps}
              key={product.product_id}
            />
          );
        })}
      </section>

      <div className="flex min-h-16 items-center justify-center border-t border-border pt-4" ref={sentinelRef}>
        {loadState === "loading" ? (
          <p className="inline-flex items-center gap-2 text-sm text-muted-foreground" role="status">
            <LoaderCircle className="size-4 animate-spin motion-reduce:animate-none" aria-hidden="true" />
            {discoveryCopy.loadingMore}
          </p>
        ) : loadState === "error" ? (
          <div className="flex flex-wrap items-center justify-center gap-3" role="alert">
            <p className="text-sm text-muted-foreground">{discoveryCopy.loadMoreError}</p>
            <Button onClick={() => void loadMore()} size="sm" type="button" variant="outline">
              <RefreshCw className="size-4" aria-hidden="true" />
              {discoveryCopy.retryLoadMore}
            </Button>
          </div>
        ) : !hasNextPage ? (
          <p className="text-xs text-muted-foreground" role="status">{formatPublicMessage(discoveryCopy.allProductsLoaded, { count: initialProducts.total_items })}</p>
        ) : null}
      </div>

      <p className="sr-only" aria-live="polite">
        {selectedProducts.length
          ? copy.compare.selectedCount.replace("{count}", String(selectedProducts.length)).replace("{limit}", String(MAX_COMPARE_PRODUCTS))
          : copy.compare.emptyTitle}
      </p>
    </section>
  );
}

function ProductCompareListItem({
  compareDisabled,
  filters,
  locale,
  onToggle,
  product,
  selected
}: ProductPresentationProps) {
  const copy = getPublicMessages(locale);
  const sortMetric = buildPublicSortMetric(product, locale, filters.sortBy);
  const detailHref = buildProductDetailHref(filters, product.product_id);

  return (
    <article
      className={cn(
        "relative overflow-hidden border border-foreground/15 bg-card/80 transition-colors hover:border-foreground/30",
        "before:absolute before:inset-y-0 before:left-0 before:w-1 before:bg-verification/55",
        product.product_family === "lending" && "before:bg-loan/70",
        selected && "border-maple/45 before:bg-maple"
      )}
    >
      <div className="grid gap-4 px-4 py-4 sm:grid-cols-[minmax(0,1fr)_minmax(8.5rem,auto)_auto] sm:items-center sm:px-5">
        <div className="grid min-w-0 grid-cols-[auto_minmax(0,1fr)] items-center gap-3">
          <BankLogo bankCode={product.bank_code} bankName={product.bank_name} size="sm" />
          <div className="min-w-0">
            <div className="flex min-w-0 flex-wrap items-center gap-x-2 gap-y-1">
              <span className="truncate text-xs font-medium text-muted-foreground">{product.bank_name}</span>
              <span className="whitespace-nowrap rounded-full bg-muted px-2 py-0.5 font-mono text-[10px] font-semibold uppercase tracking-wide text-muted-foreground">
                {product.product_type_label}
              </span>
            </div>
            <h2 className="mt-0.5 text-sm font-semibold leading-snug text-foreground sm:text-base">
              <Link className="flex min-h-11 min-w-0 items-center hover:text-primary [overflow-wrap:anywhere]" href={detailHref}>
                {product.product_name}
              </Link>
            </h2>
          </div>
        </div>

        <dl className={cn(
          "border-l-2 pl-3",
          product.product_family === "lending" ? "border-loan" : "border-primary",
          selected && "border-maple"
        )}>
          <dt className="font-mono text-[10px] font-semibold uppercase tracking-wide text-muted-foreground">{sortMetric.label}</dt>
          <dd className={cn(
            "mt-1 max-w-64 break-words font-display text-xl font-semibold leading-tight tracking-[-0.03em] text-primary tabular-nums",
            product.product_family === "lending" && "text-loan",
            selected && "text-maple"
          )}>
            {sortMetric.value}
          </dd>
        </dl>

        <div className="flex flex-wrap items-center gap-2 sm:justify-end">
          <Button aria-pressed={selected} className="min-h-11 rounded-full px-4" disabled={compareDisabled} onClick={onToggle} size="sm" type="button" variant={selected ? "default" : "outline"}>
            {selected ? <Check className="size-4" aria-hidden="true" /> : <Plus className="size-4" aria-hidden="true" />}
            {selected ? copy.compare.selected : copy.compare.select}
          </Button>
          {product.product_url ? (
            <a className="inline-flex min-h-11 items-center gap-1.5 whitespace-nowrap px-1 text-sm font-medium text-primary hover:text-primary/80" href={product.product_url} target="_blank" rel="noopener noreferrer">
              {copy.common.bankPage}
              <ExternalLink className="size-3.5" aria-hidden="true" />
            </a>
          ) : null}
        </div>
      </div>
      {compareDisabled ? <p className="px-4 pb-3 text-xs leading-5 text-muted-foreground sm:px-5">{copy.compare.limit}</p> : null}
    </article>
  );
}

function ProductCompareCard({
  compareDisabled,
  filters,
  locale,
  onToggle,
  product,
  selected
}: ProductPresentationProps) {
  const copy = getPublicMessages(locale);
  const metrics = buildPublicProductMetrics(product, locale, "card").slice(0, 3);
  const [primaryMetric, ...secondaryMetrics] = metrics;
  const detailHref = buildProductDetailHref(filters, product.product_id);

  return (
    <article
      className={cn(
        "relative h-full overflow-hidden border border-foreground/15 bg-card/80 transition-[border-color,transform,box-shadow] hover:-translate-y-0.5 hover:border-foreground/30 hover:shadow-[0_12px_30px_rgba(28,39,35,0.08)]",
        "before:absolute before:inset-y-0 before:left-0 before:w-1 before:bg-verification/55",
        product.product_family === "lending" && "before:bg-loan/70",
        selected && "border-maple/45 shadow-[0_0_0_1px_rgba(195,74,63,0.2)] before:bg-maple"
      )}
    >
      <div className="px-5 pb-2 pt-5">
        <div className="flex flex-col gap-4">
          <div className="flex items-center justify-between gap-3">
            <div className="flex min-w-0 items-center gap-2">
              <BankLogo bankCode={product.bank_code} bankName={product.bank_name} size="sm" />
              <span className="truncate text-xs font-medium text-muted-foreground">{product.bank_name}</span>
            </div>
            <span className="inline-flex whitespace-nowrap rounded-full bg-muted px-2.5 py-1 font-mono text-[10px] font-semibold uppercase tracking-wide text-muted-foreground">{product.product_type_label}</span>
          </div>
          <div className="min-w-0">
            <h2 className="text-lg font-semibold leading-snug tracking-[-0.02em]">
              <Link className="inline-flex min-h-11 items-center break-words hover:text-primary" href={detailHref}>
                {product.product_name}
              </Link>
            </h2>
          </div>
        </div>
      </div>
      <div className="px-5 pb-5">
        <dl className="border-y border-border">
          <div className="py-4">
            <dt className="font-mono text-[10px] font-semibold uppercase tracking-wide text-verification">{primaryMetric.label}</dt>
            <dd className={cn(
              "mt-1 break-words font-display font-semibold leading-tight tracking-[-0.04em] text-foreground tabular-nums",
              product.product_family === "lending" && !Number.isFinite(product.card_display_rate) ? "text-lg" : "text-3xl"
            )}>{primaryMetric.value}</dd>
          </div>
          <div className={cn("grid border-t border-border", secondaryMetrics.length > 1 && "grid-cols-2 divide-x divide-border")}>
            {secondaryMetrics.map((metric) => (
              <div className={cn("min-w-0 py-3", secondaryMetrics.length > 1 && "first:pr-3 last:pl-3")} key={metric.label}>
                <dt className="text-[11px] font-medium text-muted-foreground">{metric.label}</dt>
                <dd className="mt-1 break-words text-sm font-semibold leading-snug text-foreground tabular-nums">{metric.value}</dd>
              </div>
            ))}
          </div>
        </dl>
        <div className="mt-4 flex flex-col gap-2 border-t border-border/70 pt-3 sm:flex-row sm:items-center sm:justify-between">
          <Button aria-pressed={selected} disabled={compareDisabled} onClick={onToggle} size="sm" type="button" variant={selected ? "default" : "outline"} className="min-h-11 justify-center rounded-full px-4">
            {selected ? <Check className="size-4" aria-hidden="true" /> : <Plus className="size-4" aria-hidden="true" />}
            {selected ? copy.compare.selected : copy.compare.select}
          </Button>
          {product.product_url ? (
            <a
              className="inline-flex min-h-11 items-center justify-center gap-1.5 whitespace-nowrap text-sm font-medium text-primary hover:text-primary/80"
              href={product.product_url}
              target="_blank"
              rel="noopener noreferrer"
            >
              {copy.common.bankPage}
              <ExternalLink className="size-3.5" aria-hidden="true" />
            </a>
          ) : null}
        </div>
        {compareDisabled ? <p className="mt-2 text-xs leading-5 text-muted-foreground">{copy.compare.limit}</p> : null}
      </div>
    </article>
  );
}

function ComparePanel({
  filters,
  locale,
  onRemove,
  products
}: {
  filters: ProductGridPageFilters;
  locale: string;
  onRemove: (productId: string) => void;
  products: PublicProduct[];
}) {
  const copy = getPublicMessages(locale);
  const designCopy = getPublicDesignCopy(locale);
  const rowsByProduct = products.map((product) => buildCompareRows(product, locale));
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
      <div className={cn("grid gap-3 md:grid-cols-2", products.length === 3 ? "xl:grid-cols-3" : products.length >= 4 ? "xl:grid-cols-4" : "")}>
        {products.map((product, productIndex) => (
          <article className="border border-border bg-background/75 p-4" key={product.product_id}>
            <div className="flex items-start justify-between gap-3">
              <div className="flex min-w-0 items-start gap-3">
                <BankLogo bankCode={product.bank_code} bankName={product.bank_name} size="sm" />
                <div className="min-w-0">
                  <Link className="break-words text-sm font-semibold text-foreground hover:text-primary" href={buildProductDetailHref(filters, product.product_id)}>
                    {product.product_name}
                  </Link>
                  <p className="mt-1 text-xs text-muted-foreground">{product.bank_name} · {product.product_type_label}</p>
                </div>
              </div>
              <button className="inline-flex size-11 shrink-0 items-center justify-center rounded-full text-muted-foreground hover:bg-muted hover:text-foreground" onClick={() => onRemove(product.product_id)} type="button" aria-label={`${copy.compare.remove}: ${product.product_name}`}>
                <X className="size-4" aria-hidden="true" />
              </button>
            </div>
            <dl className="mt-4 divide-y divide-border border-y border-border">
              {rowsByProduct[productIndex].map((row) => (
                <CompareFact different={differingKeys.has(row.key)} key={row.key} label={row.label} value={row.value} />
              ))}
            </dl>
            {product.product_url ? (
              <Button asChild variant="outline" className="mt-4 min-h-11 w-full rounded-full">
                <a href={product.product_url} target="_blank" rel="noopener noreferrer">
                  {copy.detail.officialPage}
                  <ExternalLink className="size-3.5" aria-hidden="true" />
                </a>
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
    ...typeAware.map((metric, index) => ({
      key: `essential-${index}`,
      label: metric.label,
      value: metric.value
    }))
  ];
}

function buildProductDetailHref(filters: ProductGridPageFilters, productId: string) {
  return buildPublicHref(`/products/${encodeURIComponent(productId)}`, filters);
}
