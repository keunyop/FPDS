"use client";

import Link from "next/link";
import { FileText, Layers3, Play } from "lucide-react";
import { useRouter } from "next/navigation";
import { useMemo, useState, type FormEvent } from "react";

import { Button } from "@/components/ui/button";
import { Field, FieldError, FieldLabel } from "@/components/ui/field";
import {
  InputGroup,
  InputGroupAddon,
  InputGroupTextarea,
} from "@/components/ui/input-group";
import type {
  BankDetailResponse,
  ProductTypeItem,
  SourceCatalogCollectionLaunchResponse,
  SourceCatalogItem,
} from "@/lib/admin-api";
import { buildAdminHref, type AdminLocale } from "@/lib/admin-i18n";
import {
  buildAdminProductTypeLabelMap,
  buildAdminProductTypeOptions,
  formatAdminProductType,
} from "@/lib/admin-product-types";

type BankCoverageSectionProps = {
  bankCode: string;
  catalogItems: BankDetailResponse["catalog_items"];
  csrfToken: string | null | undefined;
  locale: AdminLocale;
  productTypes: ProductTypeItem[];
};

type CreateCoverageFormState = {
  product_type: string;
  status: string;
  change_reason: string;
};

const STATUS_OPTIONS = [
  { label: "active", value: "active" },
  { label: "inactive", value: "inactive" },
] as const;

export function BankCoverageSection({
  bankCode,
  catalogItems,
  csrfToken,
  locale,
  productTypes,
}: BankCoverageSectionProps) {
  const router = useRouter();
  const [productTypeSearch, setProductTypeSearch] = useState("");
  const existingTypes = useMemo(
    () => new Set(catalogItems.map((item) => item.product_type)),
    [catalogItems],
  );
  const productTypeOptions = useMemo(
    () => buildAdminProductTypeOptions(productTypes.filter((item) => item.status === "active")),
    [productTypes],
  );
  const availableProductTypes = useMemo(
    () => productTypeOptions.filter((option) => !existingTypes.has(option.value)),
    [existingTypes, productTypeOptions],
  );
  const filteredProductTypes = useMemo(() => {
    const needle = productTypeSearch.trim().toLowerCase();
    if (!needle) {
      return availableProductTypes;
    }
    return availableProductTypes.filter((option) =>
      `${option.label} ${option.value} ${option.description}`.toLowerCase().includes(needle),
    );
  }, [availableProductTypes, productTypeSearch]);
  const productTypeLabelMap = useMemo(() => buildAdminProductTypeLabelMap(productTypes), [productTypes]);
  const [createForm, setCreateForm] = useState<CreateCoverageFormState>({
    product_type: availableProductTypes[0]?.value ?? "",
    status: "active",
    change_reason: "",
  });
  const [createPending, setCreatePending] = useState(false);
  const [collectingId, setCollectingId] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function handleCreate(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!createForm.product_type) {
      return;
    }
    setCreatePending(true);
    setMessage(null);
    setError(null);

    try {
      const response = await fetch("/admin/source-catalog/create", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...(csrfToken ? { "X-CSRF-Token": csrfToken } : {}),
        },
        body: JSON.stringify({
          bank_code: bankCode,
          product_type: createForm.product_type,
          status: createForm.status,
          change_reason: createForm.change_reason,
        }),
      });
      const payload = (await response.json()) as {
        data?: { catalog_item?: SourceCatalogItem };
        error?: { message?: string };
      };
      if (!response.ok) {
        setError(payload.error?.message ?? "Coverage could not be added.");
        return;
      }
      const createdProductType =
        payload.data?.catalog_item?.product_type ?? createForm.product_type;
      setMessage(`${formatProductType(createdProductType, productTypeLabelMap)} coverage was added.`);
      const nextProductTypes = availableProductTypes.filter(
        (option) => option.value !== createdProductType,
      );
      setCreateForm({
        product_type: nextProductTypes[0]?.value ?? "",
        status: "active",
        change_reason: "",
      });
      router.refresh();
    } catch {
      setError("Coverage could not be added. Check the admin API and try again.");
    } finally {
      setCreatePending(false);
    }
  }

  async function handleCollect(item: BankDetailResponse["catalog_items"][number]) {
    setCollectingId(item.catalog_item_id);
    setMessage(null);
    setError(null);

    try {
      const response = await fetch("/admin/source-catalog/collect", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...(csrfToken ? { "X-CSRF-Token": csrfToken } : {}),
        },
        body: JSON.stringify({
          catalog_item_ids: [item.catalog_item_id],
        }),
      });
      const payload = (await response.json()) as {
        data?: SourceCatalogCollectionLaunchResponse;
        error?: { message?: string };
      };
      if (!response.ok) {
        setError(payload.error?.message ?? "Collection could not be started.");
        return;
      }
      setMessage(buildSingleCoverageCollectMessage(item.product_type, payload.data, productTypeLabelMap));
      router.refresh();
    } catch {
      setError("Collection could not be started. Check the admin API and try again.");
    } finally {
      setCollectingId(null);
    }
  }

  return (
    <section className="rounded-[1.5rem] border border-border/80 bg-card/95 p-5 shadow-sm">
      <div className="space-y-2">
        <p className="text-xs font-medium uppercase tracking-[0.16em] text-muted-foreground">
          Coverage
        </p>
        <h2 className="text-xl font-semibold tracking-tight text-foreground">
          Product coverage from this bank homepage
        </h2>
        <p className="text-sm leading-6 text-muted-foreground">
          Operators only choose which product families FPDS should cover. Source URLs are
          generated during collect from the bank homepage, not entered manually here.
        </p>
      </div>

      {message ? (
        <p className="mt-4 rounded-2xl bg-emerald-50 px-4 py-3 text-sm text-emerald-700">
          {message}
        </p>
      ) : null}
      {error ? (
        <p className="mt-4 rounded-2xl bg-destructive/10 px-4 py-3 text-sm text-destructive">
          {error}
        </p>
      ) : null}

      <div className="mt-5 grid gap-3">
        {catalogItems.length === 0 ? (
          <div className="rounded-2xl border border-dashed border-border bg-muted/20 px-4 py-4 text-sm leading-6 text-muted-foreground">
            No coverage has been added for this bank yet.
          </div>
        ) : (
          catalogItems.map((item) => (
            <article
              className="rounded-2xl border border-border/80 bg-background px-4 py-4"
              key={item.catalog_item_id}
            >
              <div className="flex flex-col gap-3 xl:flex-row xl:items-start xl:justify-between">
                <div className="min-w-0">
                  <div className="flex flex-wrap items-center gap-2">
                    <p className="text-base font-semibold text-foreground">
                      {formatProductType(item.product_type, productTypeLabelMap)}
                    </p>
                    <span className="rounded-full bg-muted px-3 py-1 text-xs font-medium text-muted-foreground">
                      {item.status}
                    </span>
                  </div>
                  <p className="mt-2 text-sm leading-6 text-muted-foreground">
                    {item.generated_source_count} generated source(s) currently available for this
                    coverage.
                  </p>
                  {item.change_reason ? (
                    <p className="mt-2 text-sm leading-6 text-muted-foreground">
                      Latest note: {item.change_reason}
                    </p>
                  ) : null}
                </div>

                <div className="flex flex-wrap gap-2">
                  <Link
                    className="inline-flex h-10 items-center justify-center rounded-xl border border-border px-4 text-sm font-medium text-foreground transition hover:border-primary hover:text-primary"
                    href={buildAdminHref(
                      "/admin/sources",
                      new URLSearchParams(
                        `bank_code=${item.bank_code}&product_type=${item.product_type}`,
                      ),
                      locale,
                    )}
                  >
                    View sources
                  </Link>
                  <Button
                    disabled={collectingId === item.catalog_item_id}
                    onClick={() => void handleCollect(item)}
                    type="button"
                  >
                    <Play className="size-4" />
                    {collectingId === item.catalog_item_id ? "Collecting..." : "Collect"}
                  </Button>
                </div>
              </div>
            </article>
          ))
        )}
      </div>

      <div className="mt-5 rounded-2xl border border-border/80 bg-muted/20 p-4">
        <div className="space-y-1">
          <p className="text-sm font-medium text-foreground">Add coverage</p>
          <p className="text-sm leading-6 text-muted-foreground">
            Add only missing product families. FPDS will discover the actual product pages from
            this bank's homepage later.
          </p>
        </div>

        {availableProductTypes.length === 0 ? (
          <p className="mt-4 text-sm leading-6 text-muted-foreground">
            All supported product families are already covered for this bank.
          </p>
        ) : (
          <form className="mt-4 space-y-4" onSubmit={handleCreate}>
            <div className="grid gap-4">
              <label className="grid gap-2 text-sm">
                <span className="font-medium text-foreground">Search product types</span>
                <input
                  className="h-10 rounded-xl border border-border bg-background px-3 text-sm text-foreground"
                  onChange={(event) => setProductTypeSearch(event.target.value)}
                  placeholder="Search by name or description"
                  type="search"
                  value={productTypeSearch}
                />
              </label>
            </div>
            <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-[minmax(0,1fr)_minmax(0,1fr)]">
              <SelectField
                label="Product type"
                onChange={(value) =>
                  setCreateForm((current) => ({ ...current, product_type: value }))
                }
                options={filteredProductTypes.length > 0 ? filteredProductTypes : availableProductTypes}
                value={createForm.product_type}
              />
              <SelectField
                label="Status"
                onChange={(value) =>
                  setCreateForm((current) => ({ ...current, status: value }))
                }
                options={STATUS_OPTIONS}
                value={createForm.status}
              />
            </div>

            <Field data-invalid={Boolean(error)}>
              <FieldLabel>Change reason</FieldLabel>
              <InputGroup className="min-h-20 items-start">
                <InputGroupAddon align="block-start">
                  <FileText className="size-4" />
                </InputGroupAddon>
                <InputGroupTextarea
                  aria-invalid={Boolean(error)}
                  onChange={(event) =>
                    setCreateForm((current) => ({
                      ...current,
                      change_reason: event.target.value,
                    }))
                  }
                  placeholder="Why is this coverage being added?"
                  rows={2}
                  value={createForm.change_reason}
                />
              </InputGroup>
              {error ? <FieldError>{error}</FieldError> : null}
            </Field>

            <div className="flex justify-end">
              <Button
                disabled={createPending || !createForm.product_type}
                type="submit"
              >
                <Layers3 className="size-4" />
                {createPending ? "Adding..." : "Add coverage"}
              </Button>
            </div>
          </form>
        )}
      </div>
    </section>
  );
}

function SelectField({
  label,
  options,
  value,
  onChange,
}: {
  label: string;
  options: ReadonlyArray<{ label: string; value: string }>;
  value: string;
  onChange: (value: string) => void;
}) {
  return (
    <label className="grid gap-2 text-sm">
      <span className="font-medium text-foreground">{label}</span>
      <select
        className="h-10 rounded-xl border border-border bg-background px-3 text-sm text-foreground"
        onChange={(event) => onChange(event.target.value)}
        value={value}
      >
        {options.map((option) => (
          <option key={option.value} value={option.value}>
            {option.label}
          </option>
        ))}
      </select>
    </label>
  );
}

function formatProductType(productType: string, labelMap?: Record<string, string>) {
  return formatAdminProductType(productType, labelMap);
}

function buildSingleCoverageCollectMessage(
  productType: string,
  payload: SourceCatalogCollectionLaunchResponse | undefined,
  labelMap?: Record<string, string>,
) {
  if (payload?.workflow_state === "queued") {
    return [
      `${formatProductType(productType, labelMap)} collection was queued.`,
      "Homepage discovery and source collection are now running on the server in the background.",
      "Open Runs after a short refresh to inspect no-detail, timeout, or collection outcomes.",
    ].join(" ");
  }

  const materializedItem = payload?.materialized_items?.[0];
  const generatedCount = materializedItem?.generated_source_ids?.length ?? 0;
  const firstNote = materializedItem?.discovery_notes?.[0];

  if (!payload?.run_ids?.length || materializedItem?.discovery_status === "no_detail_sources_discovered") {
    return [
      `${formatProductType(productType, labelMap)} homepage discovery completed, but no detail sources were identified for collection.`,
      `Materialized ${generatedCount} source row(s).`,
      firstNote ?? null,
    ]
      .filter(Boolean)
      .join(" ");
  }

  return [
    `${formatProductType(productType, labelMap)} collection started.`,
    `Materialized ${generatedCount} source row(s).`,
    firstNote ?? null,
  ]
    .filter(Boolean)
    .join(" ");
}
