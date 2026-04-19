"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useMemo } from "react";

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
  const router = useRouter();
  const detailModalOpen = Boolean(activeProductTypeCode && activeProductType);
  const baseSearchParams = useMemo(() => buildRegistrySearchParams(filters), [filters]);

  function navigateWithParams(params: URLSearchParams, options?: { replace?: boolean }) {
    const href = buildAdminHref("/admin/product-types", params, locale);
    if (options?.replace) {
      router.replace(href, { scroll: false });
      return;
    }
    router.push(href, { scroll: false });
  }

  function openAddModal() {
    const params = new URLSearchParams(baseSearchParams);
    params.set("modal", "add");
    params.delete("productType");
    navigateWithParams(params);
  }

  function openProductTypeModal(productTypeCode: string) {
    const params = new URLSearchParams(baseSearchParams);
    params.set("productType", productTypeCode);
    params.delete("modal");
    navigateWithParams(params);
  }

  function closeModal() {
    navigateWithParams(new URLSearchParams(baseSearchParams), { replace: true });
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
      openProductTypeModal(productType.product_type_code);
      return;
    }
    closeModal();
  }

  return (
    <section className="grid gap-6">
      <article className="rounded-[1.75rem] border border-border/80 bg-card/95 p-6 shadow-sm md:p-8">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
          <div className="max-w-3xl">
            <p className="text-sm font-medium uppercase tracking-[0.18em] text-muted-foreground">Product Types</p>
            <h1 className="mt-3 text-balance text-3xl font-semibold tracking-tight text-foreground md:text-4xl">
              Manage dynamic product type onboarding rules from one list.
            </h1>
            <p className="mt-3 text-sm leading-7 text-muted-foreground md:text-base">
              Operators define product types once, then reuse them in bank coverage search, homepage-first discovery,
              and the generic AI fallback path for dynamic deposit products.
            </p>
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
      </article>

      <article className="grid gap-4 md:grid-cols-3">
        <StatCard label="Product types" note="Current list scope" value={String(productTypes.summary.total_items)} />
        <StatCard label="Built-in" note="Canonical parser coverage" value={String(productTypes.summary.built_in_count)} />
        <StatCard label="Dynamic" note="Generic AI fallback path" value={String(productTypes.summary.total_items - productTypes.summary.built_in_count)} />
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
            <p className="mt-2 text-sm leading-6 text-muted-foreground">
              Review the current registry under the active search filter, then open create or detail work in a modal
              without leaving this page.
            </p>
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
                <th className="border-b border-border px-3 py-3 font-medium">Mode</th>
                <th className="border-b border-border px-3 py-3 font-medium">Fallback policy</th>
                <th className="border-b border-border px-3 py-3 font-medium">Discovery keywords</th>
              </tr>
            </thead>
            <tbody>
              {productTypes.items.length === 0 ? (
                <tr>
                  <td className="px-3 py-8 text-sm text-muted-foreground" colSpan={6}>
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
                    <td className="border-b border-border/70 px-3 py-4 text-foreground">
                      {item.built_in_flag ? "Built-in" : "Dynamic"}
                    </td>
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
        description="Add a product type without leaving the current registry list."
        footer={
          <p className="text-center text-xs leading-relaxed text-muted-foreground">
            New dynamic types feed homepage-first discovery and stay review-first downstream.
          </p>
        }
        onOpenChange={handleAddDialogChange}
        open={addModalOpen}
        showPanel={false}
        title="Add product type"
      >
        <ProductTypeCreateDialogContent csrfToken={csrfToken} onCreated={handleProductTypeCreated} />
      </OfferModal4>

      <OfferModal4
        description={
          activeProductType
            ? "Review and update the product type definition while keeping search and list context anchored on /admin/product-types."
            : undefined
        }
        footer={
          activeProductType ? (
            <p className="text-center text-xs leading-relaxed text-muted-foreground">
              Built-in types stay read-only, while dynamic types can be updated or deleted from this modal.
            </p>
          ) : undefined
        }
        onOpenChange={handleDetailDialogChange}
        open={detailModalOpen}
        showPanel={false}
        title={activeProductType ? activeProductType.display_name : "Product type detail"}
      >
        {activeProductType ? (
          <ProductTypeDetailDialogContent csrfToken={csrfToken} locale={locale} productType={activeProductType} />
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

function StatCard({ label, note, value }: { label: string; note: string; value: string }) {
  return (
    <article className="rounded-[1.5rem] border border-border/80 bg-card/95 p-5 shadow-sm">
      <p className="text-sm font-medium uppercase tracking-[0.16em] text-muted-foreground">{label}</p>
      <p className="mt-3 text-3xl font-semibold tracking-tight text-foreground">{value}</p>
      <p className="mt-2 text-sm leading-6 text-muted-foreground">{note}</p>
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
