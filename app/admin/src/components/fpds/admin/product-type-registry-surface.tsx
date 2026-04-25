"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";

import { AdminPageHeader } from "@/components/fpds/admin/admin-page-header";
import { OfferModal4 } from "@/components/offer-modal4";
import { ProductTypeCreateDialogContent } from "@/components/fpds/admin/product-type-create-dialog-content";
import { ProductTypeDetailDialogContent } from "@/components/fpds/admin/product-type-detail-dialog-content";
import type { ProductTypeItem, ProductTypeListResponse } from "@/lib/admin-api";
import { buildAdminHref, type AdminLocale } from "@/lib/admin-i18n";

export type ProductTypePageFilters = {
  q: string;
  status: string;
};

type ProductTypeRegistrySurfaceProps = {
  productTypes: ProductTypeListResponse;
  filters: ProductTypePageFilters;
  csrfToken: string | null | undefined;
  locale: AdminLocale;
  addModalOpen: boolean;
  activeProductTypeCode: string | null;
  activeProductType: ProductTypeItem | null;
};

export function ProductTypeRegistrySurface({
  productTypes,
  filters,
  csrfToken,
  locale,
  addModalOpen,
  activeProductTypeCode,
  activeProductType,
}: ProductTypeRegistrySurfaceProps) {
  const [addDialogOpen, setAddDialogOpen] = useState(addModalOpen);
  const [selectedProductTypeCode, setSelectedProductTypeCode] = useState(activeProductTypeCode);
  const [selectedProductTypeOverride, setSelectedProductTypeOverride] = useState<ProductTypeItem | null>(activeProductType);
  const baseSearchParams = useMemo(() => buildRegistrySearchParams(filters), [filters]);
  const selectedProductType = useMemo(() => {
    if (!selectedProductTypeCode) {
      return null;
    }
    return (
      productTypes.items.find((item) => item.product_type_code === selectedProductTypeCode) ??
      (selectedProductTypeOverride?.product_type_code === selectedProductTypeCode ? selectedProductTypeOverride : null)
    );
  }, [productTypes.items, selectedProductTypeCode, selectedProductTypeOverride]);
  const detailModalOpen = Boolean(selectedProductTypeCode && selectedProductType);

  useEffect(() => {
    setAddDialogOpen(addModalOpen);
  }, [addModalOpen]);

  useEffect(() => {
    setSelectedProductTypeCode(activeProductTypeCode);
    setSelectedProductTypeOverride(activeProductType);
  }, [activeProductTypeCode, activeProductType]);

  function syncUrlWithParams(params: URLSearchParams, options?: { replace?: boolean }) {
    const href = buildAdminHref("/admin/product-types", params, locale);
    if (options?.replace) {
      window.history.replaceState(null, "", href);
      return;
    }
    window.history.pushState(null, "", href);
  }

  function openAddModal() {
    const params = new URLSearchParams(baseSearchParams);
    params.set("modal", "add");
    params.delete("productType");
    setAddDialogOpen(true);
    setSelectedProductTypeCode(null);
    setSelectedProductTypeOverride(null);
    syncUrlWithParams(params);
  }

  function openProductTypeModal(productTypeCode: string, productType?: ProductTypeItem) {
    const params = new URLSearchParams(baseSearchParams);
    params.set("productType", productTypeCode);
    params.delete("modal");
    setAddDialogOpen(false);
    setSelectedProductTypeCode(productTypeCode);
    setSelectedProductTypeOverride(productType ?? productTypes.items.find((item) => item.product_type_code === productTypeCode) ?? null);
    syncUrlWithParams(params);
  }

  function closeModal() {
    setAddDialogOpen(false);
    setSelectedProductTypeCode(null);
    setSelectedProductTypeOverride(null);
    syncUrlWithParams(new URLSearchParams(baseSearchParams), { replace: true });
  }

  function handleAddDialogChange(open: boolean) {
    if (!open) {
      closeModal();
    }
  }

  function handleDetailDialogChange(open: boolean) {
    if (!open) {
      closeModal();
    }
  }

  function handleProductTypeCreated(productType: ProductTypeItem | null) {
    if (productType?.product_type_code) {
      openProductTypeModal(productType.product_type_code, productType);
      return;
    }
    closeModal();
  }

  return (
    <section className="grid gap-6">
      <AdminPageHeader
        actions={
          <>
            <button
              className="inline-flex h-10 items-center justify-center rounded-xl bg-primary px-4 text-sm font-medium text-primary-foreground transition hover:bg-primary/90"
              onClick={openAddModal}
              type="button"
            >
              Add product type
            </button>
          </>
        }
        description="Operator-managed product type definitions."
        path={["Operations", "Product Types"]}
        title="Product Types"
      />

      <article className="grid gap-4 md:grid-cols-3">
        <StatCard label="Product types" value={String(productTypes.summary.total_items)} />
        <StatCard label="Active" value={String(productTypes.summary.status_counts.active ?? 0)} />
        <StatCard label="Inactive" value={String(productTypes.summary.status_counts.inactive ?? 0)} />
      </article>

      <article className="rounded-[1.75rem] border border-border/80 bg-card/95 p-6 shadow-sm">
        <form action={buildAdminHref("/admin/product-types", new URLSearchParams(), locale)} className="grid gap-4 lg:grid-cols-[1.4fr_minmax(0,220px)_auto]">
          <label className="grid gap-2 text-sm">
            <span className="font-medium text-foreground">Search</span>
            <input
              className="h-10 rounded-xl border border-border bg-background px-3 text-sm"
              defaultValue={filters.q}
              name="q"
              placeholder="name, code, or description"
              type="search"
            />
          </label>
          <FilterSelect defaultValue={filters.status} label="Status" name="status" options={productTypes.facets.statuses} />
          <div className="flex items-end gap-2">
            <button className="inline-flex h-10 items-center justify-center rounded-xl bg-primary px-4 text-sm font-medium text-primary-foreground transition hover:bg-primary/90" type="submit">
              Apply
            </button>
            <Link
              className="inline-flex h-10 items-center justify-center rounded-xl border border-border px-4 text-sm font-medium text-foreground transition hover:border-primary hover:text-primary"
              href={buildAdminHref("/admin/product-types", new URLSearchParams(), locale)}
            >
              Reset
            </Link>
          </div>
        </form>
      </article>

      <article className="rounded-[1.75rem] border border-border/80 bg-card/95 shadow-sm">
        <div className="flex flex-col gap-3 border-b border-border/80 px-6 py-5 lg:flex-row lg:items-center lg:justify-between">
          <div>
            <p className="text-sm font-medium uppercase tracking-[0.18em] text-muted-foreground">Product type list</p>
          </div>
          <div className="flex flex-wrap gap-2">
            <button
              className="inline-flex h-10 items-center justify-center rounded-xl bg-primary px-4 text-sm font-medium text-primary-foreground transition hover:bg-primary/90"
              onClick={openAddModal}
              type="button"
            >
              Add product type
            </button>
          </div>
        </div>

        <div className="overflow-x-auto px-6 py-5">
          <table className="min-w-[980px] table-fixed border-separate border-spacing-0">
            <thead>
              <tr className="text-left text-xs uppercase tracking-[0.16em] text-muted-foreground">
                <th className="border-b border-border px-3 py-3 font-medium">Product type</th>
                <th className="border-b border-border px-3 py-3 font-medium">Code</th>
                <th className="border-b border-border px-3 py-3 font-medium">Status</th>
                <th className="border-b border-border px-3 py-3 font-medium">Fallback policy</th>
                <th className="border-b border-border px-3 py-3 font-medium">Discovery keywords</th>
              </tr>
            </thead>
            <tbody>
              {productTypes.items.length === 0 ? (
                <tr>
                  <td className="px-3 py-8 text-sm text-muted-foreground" colSpan={5}>
                    No product types matched the current filter set.
                  </td>
                </tr>
              ) : (
                productTypes.items.map((item) => (
                  <tr className="align-top text-sm" key={item.product_type_code}>
                    <td className="border-b border-border/70 px-3 py-4">
                      <button
                        className="bg-transparent p-0 text-left font-medium text-foreground underline-offset-4 hover:text-primary hover:underline"
                        onClick={() => openProductTypeModal(item.product_type_code)}
                        type="button"
                      >
                        {item.display_name}
                      </button>
                      <p className="mt-2 text-sm leading-6 text-muted-foreground">{item.description}</p>
                    </td>
                    <td className="border-b border-border/70 px-3 py-4 text-foreground">{item.product_type_code}</td>
                    <td className="border-b border-border/70 px-3 py-4 text-foreground">{item.status}</td>
                    <td className="border-b border-border/70 px-3 py-4 text-foreground">{item.fallback_policy}</td>
                    <td className="border-b border-border/70 px-3 py-4 text-muted-foreground">
                      {item.discovery_keywords.join(", ") || "n/a"}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </article>

      <OfferModal4
        onOpenChange={handleAddDialogChange}
        open={addDialogOpen}
        showPanel={false}
        title="Add product type"
      >
        <ProductTypeCreateDialogContent csrfToken={csrfToken} onCreated={handleProductTypeCreated} />
      </OfferModal4>

      <OfferModal4
        onOpenChange={handleDetailDialogChange}
        open={detailModalOpen}
        showPanel={false}
        title={selectedProductType ? selectedProductType.display_name : "Product type detail"}
      >
        {selectedProductType ? (
          <ProductTypeDetailDialogContent
            csrfToken={csrfToken}
            key={selectedProductType.product_type_code}
            locale={locale}
            productType={selectedProductType}
          />
        ) : null}
      </OfferModal4>
    </section>
  );
}

function buildRegistrySearchParams(filters: ProductTypePageFilters) {
  const params = new URLSearchParams();
  if (filters.q) {
    params.set("q", filters.q);
  }
  if (filters.status) {
    params.set("status", filters.status);
  }
  return params;
}

function StatCard({ label, value }: { label: string; value: string }) {
  return (
    <article className="rounded-lg border border-border/80 bg-background p-4">
      <p className="text-sm font-medium text-muted-foreground">{label}</p>
      <p className="mt-2 text-2xl font-semibold tracking-tight text-foreground">{value}</p>
    </article>
  );
}

function FilterSelect({
  defaultValue,
  label,
  name,
  options,
}: {
  defaultValue: string;
  label: string;
  name: string;
  options: string[];
}) {
  return (
    <label className="grid gap-2 text-sm">
      <span className="font-medium text-foreground">{label}</span>
      <select className="h-10 rounded-xl border border-border bg-background px-3 text-sm" defaultValue={defaultValue} name={name}>
        <option value="">All</option>
        {options.map((option) => (
          <option key={option} value={option}>
            {option}
          </option>
        ))}
      </select>
    </label>
  );
}
