"use client";

import { CircleCheck, Globe2, Plus, ShieldCheck } from "lucide-react";
import { useMemo, useState, useTransition } from "react";
import { useRouter } from "next/navigation";

import { AdminPageHeader } from "@/components/fpds/admin/admin-page-header";
import { AdminStatStrip } from "@/components/fpds/admin/admin-stat-strip";
import { DestructiveConfirmDialog } from "@/components/fpds/admin/destructive-confirm-dialog";
import { Button } from "@/components/ui/button";
import type { CountryRegistryItem, CountryRegistryResponse } from "@/lib/admin-api";
import type { AdminLocale } from "@/lib/admin-i18n";

type CountryRegistrySurfaceProps = {
  countryRegistry: CountryRegistryResponse;
  csrfToken: string | null | undefined;
  currentCountryCode: string;
  locale: AdminLocale;
};

const copyByLocale = {
  en: {
    title: "Countries",
    description: "Choose which countries FPDS operators can access. Activating a country does not create banks, product types, or collection settings.",
    path: ["Admin", "Countries"],
    active: "Active countries",
    activeNote: "Available at Admin sign-in.",
    available: "Available to add",
    availableNote: "Prepared ISO country list.",
    addTitle: "Add a country",
    addDescription: "Select a country to make it available at Admin sign-in.",
    country: "Country",
    chooseCountry: "Choose a country",
    activate: "Activate",
    activating: "Activating...",
    listTitle: "Active countries",
    listDescription: "Deactivate a country to remove it from future sign-ins. Historical data is preserved.",
    current: "Current",
    protected: "Current sign-in country",
    deactivate: "Deactivate",
    deactivating: "Deactivating...",
    confirmTitle: "Deactivate this country?",
    confirmDescription: (name: string, code: string) => `${name} (${code}) will no longer be available at Admin sign-in. Existing sessions for that country will be signed out.`,
    cancel: "Cancel",
    error: "The country could not be updated. Please try again.",
    allActive: "All prepared countries are active.",
  },
  ko: {
    title: "\uAD6D\uAC00",
    description: "FPDS \uC6B4\uC601\uC790\uAC00 \uC811\uADFC\uD560 \uAD6D\uAC00\uB97C \uC120\uD0DD\uD569\uB2C8\uB2E4. \uAD6D\uAC00\uB97C \uD65C\uC131\uD654\uD574\uB3C4 \uC740\uD589, \uC0C1\uD488 \uC720\uD615, \uC218\uC9D1 \uC124\uC815\uC740 \uC790\uB3D9\uC73C\uB85C \uC0DD\uC131\uB418\uC9C0 \uC54A\uC2B5\uB2C8\uB2E4.",
    path: ["Admin", "\uAD6D\uAC00"],
    active: "\uD65C\uC131 \uAD6D\uAC00",
    activeNote: "Admin \uB85C\uADF8\uC778\uC5D0\uC11C \uC120\uD0DD \uAC00\uB2A5",
    available: "\uCD94\uAC00 \uAC00\uB2A5",
    availableNote: "\uC900\uBE44\uB41C ISO \uAD6D\uAC00 \uBAA9\uB85D",
    addTitle: "\uAD6D\uAC00 \uCD94\uAC00",
    addDescription: "Admin \uB85C\uADF8\uC778\uC5D0\uC11C \uC0AC\uC6A9\uD560 \uAD6D\uAC00\uB97C \uC120\uD0DD\uD558\uC138\uC694.",
    country: "\uAD6D\uAC00",
    chooseCountry: "\uAD6D\uAC00 \uC120\uD0DD",
    activate: "\uD65C\uC131\uD654",
    activating: "\uD65C\uC131\uD654 \uC911...",
    listTitle: "\uD65C\uC131 \uAD6D\uAC00",
    listDescription: "\uBE44\uD65C\uC131\uD654\uD558\uBA74 \uC0C8 \uB85C\uADF8\uC778\uC5D0\uC11C \uC81C\uC678\uB418\uBA70 \uAE30\uC874 \uB370\uC774\uD130\uB294 \uBCF4\uC874\uB429\uB2C8\uB2E4.",
    current: "\uD604\uC7AC",
    protected: "\uD604\uC7AC \uB85C\uADF8\uC778 \uAD6D\uAC00",
    deactivate: "\uBE44\uD65C\uC131\uD654",
    deactivating: "\uBE44\uD65C\uC131\uD654 \uC911...",
    confirmTitle: "\uC774 \uAD6D\uAC00\uB97C \uBE44\uD65C\uC131\uD654\uD560\uAE4C\uC694?",
    confirmDescription: (name: string, code: string) => `${name} (${code})\uC744(\uB97C) Admin \uB85C\uADF8\uC778\uC5D0\uC11C \uC120\uD0DD\uD560 \uC218 \uC5C6\uAC8C \uB429\uB2C8\uB2E4. \uD574\uB2F9 \uAD6D\uAC00\uC758 \uAE30\uC874 \uC138\uC158\uB3C4 \uC885\uB8CC\uB429\uB2C8\uB2E4.`,
    cancel: "\uCDE8\uC18C",
    error: "\uAD6D\uAC00 \uC124\uC815\uC744 \uBCC0\uACBD\uD558\uC9C0 \uBABB\uD588\uC2B5\uB2C8\uB2E4. \uB2E4\uC2DC \uC2DC\uB3C4\uD574\uC8FC\uC138\uC694.",
    allActive: "\uC900\uBE44\uB41C \uBAA8\uB4E0 \uAD6D\uAC00\uAC00 \uD65C\uC131\uD654\uB418\uC5B4 \uC788\uC2B5\uB2C8\uB2E4.",
  },
  ja: {
    title: "\u56FD",
    description: "FPDS \u904B\u7528\u8005\u304C\u30A2\u30AF\u30BB\u30B9\u3067\u304D\u308B\u56FD\u3092\u9078\u629E\u3057\u307E\u3059\u3002\u56FD\u3092\u6709\u52B9\u306B\u3057\u3066\u3082\u3001\u9280\u884C\u3001\u5546\u54C1\u7A2E\u5225\u3001\u53CE\u96C6\u8A2D\u5B9A\u306F\u81EA\u52D5\u4F5C\u6210\u3055\u308C\u307E\u305B\u3093\u3002",
    path: ["Admin", "\u56FD"],
    active: "\u6709\u52B9\u306A\u56FD",
    activeNote: "Admin \u30ED\u30B0\u30A4\u30F3\u3067\u9078\u629E\u53EF\u80FD",
    available: "\u8FFD\u52A0\u53EF\u80FD",
    availableNote: "\u7528\u610F\u3055\u308C\u305F ISO \u56FD\u30EA\u30B9\u30C8",
    addTitle: "\u56FD\u3092\u8FFD\u52A0",
    addDescription: "Admin \u30ED\u30B0\u30A4\u30F3\u3067\u4F7F\u7528\u3059\u308B\u56FD\u3092\u9078\u629E\u3057\u3066\u304F\u3060\u3055\u3044\u3002",
    country: "\u56FD",
    chooseCountry: "\u56FD\u3092\u9078\u629E",
    activate: "\u6709\u52B9\u5316",
    activating: "\u6709\u52B9\u5316\u4E2D...",
    listTitle: "\u6709\u52B9\u306A\u56FD",
    listDescription: "\u7121\u52B9\u306B\u3059\u308B\u3068\u65B0\u3057\u3044\u30ED\u30B0\u30A4\u30F3\u304B\u3089\u9664\u5916\u3055\u308C\u3001\u65E2\u5B58\u30C7\u30FC\u30BF\u306F\u4FDD\u6301\u3055\u308C\u307E\u3059\u3002",
    current: "\u73FE\u5728",
    protected: "\u73FE\u5728\u306E\u30ED\u30B0\u30A4\u30F3\u56FD",
    deactivate: "\u7121\u52B9\u5316",
    deactivating: "\u7121\u52B9\u5316\u4E2D...",
    confirmTitle: "\u3053\u306E\u56FD\u3092\u7121\u52B9\u306B\u3057\u307E\u3059\u304B\uff1F",
    confirmDescription: (name: string, code: string) => `${name} (${code}) \u306F Admin \u30ED\u30B0\u30A4\u30F3\u3067\u9078\u629E\u3067\u304D\u306A\u304F\u306A\u308A\u307E\u3059\u3002\u305D\u306E\u56FD\u306E\u65E2\u5B58\u30BB\u30C3\u30B7\u30E7\u30F3\u3082\u7D42\u4E86\u3057\u307E\u3059\u3002`,
    cancel: "\u30AD\u30E3\u30F3\u30BB\u30EB",
    error: "\u56FD\u306E\u8A2D\u5B9A\u3092\u66F4\u65B0\u3067\u304D\u307E\u305B\u3093\u3067\u3057\u305F\u3002\u3082\u3046\u4E00\u5EA6\u304A\u8A66\u3057\u304F\u3060\u3055\u3044\u3002",
    allActive: "\u7528\u610F\u3055\u308C\u305F\u3059\u3079\u3066\u306E\u56FD\u304C\u6709\u52B9\u3067\u3059\u3002",
  },
} as const;

export function CountryRegistrySurface({
  countryRegistry,
  csrfToken,
  currentCountryCode,
  locale,
}: CountryRegistrySurfaceProps) {
  const copy = copyByLocale[locale];
  const router = useRouter();
  const [selectedCode, setSelectedCode] = useState("");
  const [countryToDeactivate, setCountryToDeactivate] = useState<CountryRegistryItem | null>(null);
  const [error, setError] = useState("");
  const [pending, startTransition] = useTransition();
  const displayNames = useMemo(
    () => new Intl.DisplayNames([locale === "ko" ? "ko-KR" : locale === "ja" ? "ja-JP" : "en"], { type: "region" }),
    [locale],
  );
  const localizedName = (item: CountryRegistryItem) => displayNames.of(item.country_code) ?? item.country_name;
  const activeCountries = useMemo(
    () => countryRegistry.items
      .filter((item) => item.status === "active")
      .sort((left, right) => localizedName(left).localeCompare(localizedName(right), locale)),
    [countryRegistry.items, displayNames, locale],
  );
  const availableCountries = useMemo(
    () => countryRegistry.items
      .filter((item) => item.status !== "active")
      .sort((left, right) => localizedName(left).localeCompare(localizedName(right), locale)),
    [countryRegistry.items, displayNames, locale],
  );

  function mutate(path: string, method: "POST" | "DELETE", onSuccess: () => void) {
    setError("");
    startTransition(async () => {
      try {
        const response = await fetch(path, {
          method,
          headers: csrfToken ? { "X-CSRF-Token": csrfToken } : {},
        });
        if (!response.ok) {
          const payload = await response.json().catch(() => null) as { error?: { message?: string } } | null;
          throw new Error(payload?.error?.message || copy.error);
        }
        onSuccess();
        router.refresh();
      } catch (mutationError) {
        setError(mutationError instanceof Error ? mutationError.message : copy.error);
      }
    });
  }

  function activateSelectedCountry() {
    if (!selectedCode) return;
    mutate(`/admin/countries/${encodeURIComponent(selectedCode)}/activate`, "POST", () => setSelectedCode(""));
  }

  function confirmDeactivation() {
    if (!countryToDeactivate) return;
    mutate(`/admin/countries/${encodeURIComponent(countryToDeactivate.country_code)}/deactivate`, "DELETE", () => {
      setCountryToDeactivate(null);
    });
  }

  return (
    <section className="grid gap-5">
      <AdminPageHeader description={copy.description} path={copy.path} title={copy.title} />

      <AdminStatStrip
        className="[&>div]:md:grid-cols-2 [&>div]:xl:grid-cols-2"
        framed={false}
        items={[
          { label: copy.active, value: String(countryRegistry.summary.active_items), note: copy.activeNote, tone: "success", icon: CircleCheck },
          { label: copy.available, value: String(countryRegistry.summary.available_items), note: copy.availableNote, tone: "info", icon: Globe2 },
        ]}
      />

      <article className="border border-border bg-card p-4 md:p-5">
        <div className="max-w-3xl">
          <h2 className="text-lg font-semibold text-foreground">{copy.addTitle}</h2>
          <p className="mt-1 text-sm leading-6 text-muted-foreground">{copy.addDescription}</p>
        </div>
        <div className="mt-4 grid gap-3 sm:grid-cols-[minmax(0,1fr)_auto] sm:items-end">
          <label className="grid gap-2 text-sm font-medium text-foreground">
            {copy.country}
            <select
              className="h-10 min-w-0 rounded-md border border-input bg-background px-3 text-sm text-foreground outline-none focus:border-primary focus:ring-2 focus:ring-ring/25"
              disabled={pending || availableCountries.length === 0}
              onChange={(event) => setSelectedCode(event.target.value)}
              value={selectedCode}
            >
              <option value="">{availableCountries.length ? copy.chooseCountry : copy.allActive}</option>
              {availableCountries.map((item) => (
                <option key={item.country_code} value={item.country_code}>
                  {localizedName(item)} ({item.country_code})
                </option>
              ))}
            </select>
          </label>
          <Button className="h-10 gap-2 sm:min-w-32" disabled={!selectedCode || pending} onClick={activateSelectedCountry} type="button">
            <Plus className="h-4 w-4" aria-hidden="true" />
            {pending && !countryToDeactivate ? copy.activating : copy.activate}
          </Button>
        </div>
        {error ? <p className="mt-3 text-sm font-medium text-destructive" role="alert">{error}</p> : null}
      </article>

      <article className="border border-border bg-card">
        <div className="border-b border-border px-4 py-4 md:px-5">
          <h2 className="text-lg font-semibold text-foreground">{copy.listTitle}</h2>
          <p className="mt-1 text-sm leading-6 text-muted-foreground">{copy.listDescription}</p>
        </div>
        <div className="divide-y divide-border">
          {activeCountries.map((item) => {
            const isCurrent = item.country_code === currentCountryCode;
            return (
              <div className="flex min-w-0 flex-col gap-3 px-4 py-4 sm:flex-row sm:items-center sm:justify-between md:px-5" key={item.country_code}>
                <div className="flex min-w-0 items-center gap-3">
                  <span className="grid h-10 w-10 shrink-0 place-items-center rounded-md bg-primary/10 font-mono text-sm font-semibold text-primary">
                    {item.country_code}
                  </span>
                  <div className="min-w-0">
                    <p className="truncate font-medium text-foreground">{localizedName(item)}</p>
                    <p className="mt-0.5 text-xs text-muted-foreground">{item.country_code}</p>
                  </div>
                  {isCurrent ? (
                    <span className="inline-flex shrink-0 items-center gap-1 rounded-full bg-success/10 px-2 py-1 text-xs font-semibold text-success">
                      <ShieldCheck className="h-3.5 w-3.5" aria-hidden="true" />
                      {copy.current}
                    </span>
                  ) : null}
                </div>
                <Button
                  className="sm:min-w-28"
                  disabled={isCurrent || pending}
                  onClick={() => setCountryToDeactivate(item)}
                  title={isCurrent ? copy.protected : undefined}
                  type="button"
                  variant="outline"
                >
                  {copy.deactivate}
                </Button>
              </div>
            );
          })}
        </div>
      </article>

      <DestructiveConfirmDialog
        cancelLabel={copy.cancel}
        confirmLabel={copy.deactivate}
        description={countryToDeactivate ? copy.confirmDescription(localizedName(countryToDeactivate), countryToDeactivate.country_code) : ""}
        onConfirm={confirmDeactivation}
        onOpenChange={(open) => {
          if (!open && !pending) setCountryToDeactivate(null);
        }}
        open={Boolean(countryToDeactivate)}
        pending={pending}
        pendingLabel={copy.deactivating}
        title={copy.confirmTitle}
      />
    </section>
  );
}
