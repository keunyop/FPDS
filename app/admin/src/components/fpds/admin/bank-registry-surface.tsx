"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useMemo } from "react";

import { OfferModal4 } from "@/components/offer-modal4";
import { BankCreateDialogContent } from "@/components/fpds/admin/bank-create-dialog-content";
import { BankDetailDialogContent } from "@/components/fpds/admin/bank-detail-dialog-content";
import type { BankDetailResponse, BankItem, BankListResponse } from "@/lib/admin-api";
import { buildAdminHref, type AdminLocale } from "@/lib/admin-i18n";

export type BankRegistryPageFilters = {
  q: string;
  status: string;
};

type BankRegistrySurfaceProps = {
  banks: BankListResponse;
  filters: BankRegistryPageFilters;
  locale: AdminLocale;
  csrfToken: string | null | undefined;
  activeBankCode: string | null;
  activeBankDetail: BankDetailResponse | null;
  addModalOpen: boolean;
};

export function BankRegistrySurface({
  banks,
  filters,
  locale,
  csrfToken,
  activeBankCode,
  activeBankDetail,
  addModalOpen,
}: BankRegistrySurfaceProps) {
  const router = useRouter();
  const detailModalOpen = Boolean(activeBankCode && activeBankDetail);
  const baseSearchParams = useMemo(() => buildRegistrySearchParams(filters), [filters]);

  function navigateWithParams(params: URLSearchParams, options?: { replace?: boolean }) {
    const href = buildAdminHref("/admin/banks", params, locale);
    if (options?.replace) {
      router.replace(href, { scroll: false });
      return;
    }
    router.push(href, { scroll: false });
  }

  function openAddModal() {
    const params = new URLSearchParams(baseSearchParams);
    params.set("modal", "add");
    params.delete("bank");
    navigateWithParams(params);
  }

  function openBankModal(bankCode: string) {
    const params = new URLSearchParams(baseSearchParams);
    params.set("bank", bankCode);
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

  function handleBankCreated(bank: BankItem | null) {
    if (bank?.bank_code) {
      openBankModal(bank.bank_code);
      return;
    }
    closeModal();
  }

  return (
    <section className="grid gap-6">
      <article className="rounded-[1.75rem] border border-border/80 bg-card/95 p-6 shadow-sm md:p-8">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
          <div className="max-w-3xl">
            <p className="text-sm font-medium uppercase tracking-[0.18em] text-muted-foreground">Banks</p>
            <h1 className="mt-3 text-balance text-3xl font-semibold tracking-tight text-foreground md:text-4xl">
              Manage the bank list once, then reuse it in source catalog coverage.
            </h1>
            <p className="mt-3 text-sm leading-7 text-muted-foreground md:text-base">
              Bank code is generated automatically. Operators only need the visible bank name, homepage URL, and basic
              status metadata here.
            </p>
          </div>
          <div className="flex flex-wrap gap-2">
            <button className="inline-flex h-10 items-center justify-center rounded-xl bg-primary px-4 text-sm font-medium text-primary-foreground transition hover:bg-primary/90" onClick={openAddModal} type="button">
              Add bank
            </button>
            <Link className="inline-flex h-10 items-center justify-center rounded-xl border border-border px-4 text-sm font-medium text-foreground transition hover:border-primary hover:text-primary" href={buildAdminHref("/admin/source-catalog", new URLSearchParams(), locale)}>
              Go to source catalog
            </Link>
          </div>
        </div>
      </article>

      <article className="grid gap-4 md:grid-cols-3">
        <StatCard label="Banks" note="Current list scope" value={String(banks.summary.total_items)} />
        <StatCard label="Active" note="Available for catalog coverage" value={String(banks.summary.status_counts.active ?? 0)} />
        <StatCard label="Managed" note="Created or edited from admin" value={String(banks.items.filter((item) => item.managed_flag).length)} />
      </article>

      <article className="rounded-[1.75rem] border border-border/80 bg-card/95 p-6 shadow-sm">
        <form action={buildAdminHref("/admin/banks", new URLSearchParams(), locale)} className="grid gap-4 lg:grid-cols-[1.4fr_minmax(0,220px)_auto]">
          <label className="grid gap-2 text-sm">
            <span className="font-medium text-foreground">Search</span>
            <input className="h-10 rounded-xl border border-border bg-background px-3 text-sm" defaultValue={filters.q} name="q" placeholder="bank name or homepage URL" type="search" />
          </label>
          <FilterSelect defaultValue={filters.status} label="Status" name="status" options={banks.facets.statuses} />
          <div className="flex items-end gap-2">
            <button className="inline-flex h-10 items-center justify-center rounded-xl bg-primary px-4 text-sm font-medium text-primary-foreground transition hover:bg-primary/90" type="submit">
              Apply
            </button>
            <Link className="inline-flex h-10 items-center justify-center rounded-xl border border-border px-4 text-sm font-medium text-foreground transition hover:border-primary hover:text-primary" href={buildAdminHref("/admin/banks", new URLSearchParams(), locale)}>
              Reset
            </Link>
          </div>
        </form>
      </article>

      <article className="rounded-[1.75rem] border border-border/80 bg-card/95 shadow-sm">
        <div className="flex flex-col gap-3 border-b border-border/80 px-6 py-5 lg:flex-row lg:items-center lg:justify-between">
          <div>
            <p className="text-sm font-medium uppercase tracking-[0.18em] text-muted-foreground">Bank list</p>
            <p className="mt-2 text-sm leading-6 text-muted-foreground">
              Review the current bank registry under the active search filter, then open add or detail work in a modal
              without leaving this page.
            </p>
          </div>
          <button className="inline-flex h-10 items-center justify-center rounded-xl bg-primary px-4 text-sm font-medium text-primary-foreground transition hover:bg-primary/90" onClick={openAddModal} type="button">
            Add bank
          </button>
        </div>
        <div className="overflow-x-auto px-6 py-5">
          <table className="min-w-[880px] table-fixed border-separate border-spacing-0">
            <thead>
              <tr className="text-left text-xs uppercase tracking-[0.16em] text-muted-foreground">
                <th className="border-b border-border px-3 py-3 font-medium">Bank</th>
                <th className="border-b border-border px-3 py-3 font-medium">Code</th>
                <th className="border-b border-border px-3 py-3 font-medium">Homepage</th>
                <th className="border-b border-border px-3 py-3 font-medium">Status</th>
                <th className="border-b border-border px-3 py-3 font-medium">Catalog items</th>
                <th className="border-b border-border px-3 py-3 font-medium">Generated sources</th>
              </tr>
            </thead>
            <tbody>
              {banks.items.length === 0 ? (
                <tr>
                  <td className="px-3 py-8 text-sm text-muted-foreground" colSpan={6}>
                    No banks matched the current filter set.
                  </td>
                </tr>
              ) : (
                banks.items.map((item) => (
                  <tr className="align-top text-sm" key={item.bank_code}>
                    <td className="border-b border-border/70 px-3 py-4">
                      <button className="bg-transparent p-0 text-left font-medium text-foreground underline-offset-4 hover:text-primary hover:underline" onClick={() => openBankModal(item.bank_code)} type="button">
                        {item.bank_name}
                      </button>
                    </td>
                    <td className="border-b border-border/70 px-3 py-4 text-foreground">{item.bank_code}</td>
                    <td className="border-b border-border/70 px-3 py-4">
                      {item.homepage_url ? (
                        <a className="text-primary underline-offset-4 hover:underline" href={item.homepage_url} rel="noreferrer" target="_blank">
                          {item.homepage_url}
                        </a>
                      ) : (
                        <span className="text-muted-foreground">n/a</span>
                      )}
                    </td>
                    <td className="border-b border-border/70 px-3 py-4 text-foreground">{item.status}</td>
                    <td className="border-b border-border/70 px-3 py-4 text-foreground">{item.catalog_item_count}</td>
                    <td className="border-b border-border/70 px-3 py-4 text-foreground">{item.generated_source_count}</td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </article>

      <OfferModal4
        description="Add a bank profile without leaving the current bank list."
        footer={
          <p className="text-center text-xs leading-relaxed text-muted-foreground">
            Bank code is generated automatically after save, and the current search context stays in place.
          </p>
        }
        onOpenChange={handleAddDialogChange}
        open={addModalOpen}
        panelBadge="Admin workflow"
        panelDescription="Capture the public bank profile here, then reuse it from source catalog coverage and generated source inspection."
        panelStats={[
          { label: "Current scope", value: `${banks.summary.total_items} banks` },
          { label: "Active banks", value: `${banks.summary.status_counts.active ?? 0}` },
        ]}
        panelTitle="Bank registry workflow"
        title="Add bank"
      >
        <BankCreateDialogContent csrfToken={csrfToken} onCreated={handleBankCreated} />
      </OfferModal4>

      <OfferModal4
        description={
          activeBankDetail
            ? "Review and update the public bank profile while keeping search and list context anchored on /admin/banks."
            : undefined
        }
        footer={
          activeBankDetail ? (
            <p className="text-center text-xs leading-relaxed text-muted-foreground">
              Bank code and country stay read-only here. Source coverage work continues from source catalog.
            </p>
          ) : undefined
        }
        onOpenChange={handleDetailDialogChange}
        open={detailModalOpen}
        panelBadge={activeBankDetail?.bank.status === "active" ? "Active bank" : "Inactive bank"}
        panelDescription={
          activeBankDetail
            ? "Open detail editing in place, then jump to source catalog when you want to expand product coverage for this bank."
            : "Bank detail is loading."
        }
        panelStats={
          activeBankDetail
            ? [
                { label: "Catalog items", value: `${activeBankDetail.bank.catalog_item_count}` },
                { label: "Generated sources", value: `${activeBankDetail.bank.generated_source_count}` },
              ]
            : []
        }
        panelTitle={activeBankDetail ? activeBankDetail.bank.bank_name : "Bank detail"}
        title={activeBankDetail ? activeBankDetail.bank.bank_name : "Bank detail"}
      >
        {activeBankDetail ? (
          <BankDetailDialogContent
            csrfToken={csrfToken}
            detail={activeBankDetail}
            locale={locale}
          />
        ) : null}
      </OfferModal4>
    </section>
  );
}

function StatCard({ label, value, note }: { label: string; value: string; note: string }) {
  return (
    <article className="rounded-[1.5rem] border border-border/80 bg-card/95 p-5 shadow-sm">
      <p className="text-sm font-medium uppercase tracking-[0.16em] text-muted-foreground">{label}</p>
      <p className="mt-3 text-3xl font-semibold tracking-tight text-foreground">{value}</p>
      <p className="mt-2 text-sm text-muted-foreground">{note}</p>
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
      <select className="h-10 rounded-xl border border-border bg-background px-3 text-sm text-foreground" defaultValue={defaultValue} name={name}>
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

function buildRegistrySearchParams(filters: BankRegistryPageFilters) {
  const params = new URLSearchParams();
  if (filters.q) {
    params.set("q", filters.q);
  }
  if (filters.status) {
    params.set("status", filters.status);
  }
  return params;
}
