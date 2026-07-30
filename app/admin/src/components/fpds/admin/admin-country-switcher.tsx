"use client";

import { Check, ChevronDown, Globe2, Loader2 } from "lucide-react";
import { useEffect, useMemo, useState, useTransition } from "react";

import {
  AlertDialog,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { buildAdminHref, type AdminLocale } from "@/lib/admin-i18n";

type CountryOption = {
  country_code: string;
  country_name: string;
};

type AdminCountrySwitcherProps = {
  countryCode: string;
  csrfToken: string | null | undefined;
  locale: AdminLocale;
};

const copyByLocale = {
  en: {
    label: "Working country",
    loading: "Loading countries...",
    unavailable: "Countries unavailable",
    switchTitle: "Switch working country?",
    switchDescription: (name: string, code: string) =>
      `Switch to ${name} (${code}) and return to Overview. Page filters and any unsaved work on this screen will not carry over.`,
    cancel: "Cancel",
    confirm: "Switch country",
    switching: "Switching...",
    error: "The working country could not be changed. Please try again.",
  },
  ko: {
    label: "\uC5C5\uBB34 \uAD6D\uAC00",
    loading: "\uAD6D\uAC00 \uBAA9\uB85D \uBD88\uB7EC\uC624\uB294 \uC911...",
    unavailable: "\uAD6D\uAC00 \uBAA9\uB85D\uC744 \uBD88\uB7EC\uC624\uC9C0 \uBABB\uD588\uC2B5\uB2C8\uB2E4",
    switchTitle: "\uC5C5\uBB34 \uAD6D\uAC00\uB97C \uBCC0\uACBD\uD560\uAE4C\uC694?",
    switchDescription: (name: string, code: string) =>
      `${name} (${code})(\uC73C)\uB85C \uBCC0\uACBD\uD558\uACE0 \uAC1C\uC694 \uD654\uBA74\uC73C\uB85C \uC774\uB3D9\uD569\uB2C8\uB2E4. \uD604\uC7AC \uD654\uBA74\uC758 \uD544\uD130\uC640 \uC800\uC7A5\uD558\uC9C0 \uC54A\uC740 \uB0B4\uC6A9\uC740 \uC774\uC5B4\uC9C0\uC9C0 \uC54A\uC2B5\uB2C8\uB2E4.`,
    cancel: "\uCDE8\uC18C",
    confirm: "\uAD6D\uAC00 \uBCC0\uACBD",
    switching: "\uBCC0\uACBD \uC911...",
    error: "\uC5C5\uBB34 \uAD6D\uAC00\uB97C \uBCC0\uACBD\uD558\uC9C0 \uBABB\uD588\uC2B5\uB2C8\uB2E4. \uB2E4\uC2DC \uC2DC\uB3C4\uD574\uC8FC\uC138\uC694.",
  },
  ja: {
    label: "\u4F5C\u696D\u5BFE\u8C61\u56FD",
    loading: "\u56FD\u30EA\u30B9\u30C8\u3092\u8AAD\u307F\u8FBC\u307F\u4E2D...",
    unavailable: "\u56FD\u30EA\u30B9\u30C8\u3092\u8AAD\u307F\u8FBC\u3081\u307E\u305B\u3093",
    switchTitle: "\u4F5C\u696D\u5BFE\u8C61\u56FD\u3092\u5909\u66F4\u3057\u307E\u3059\u304B\uff1F",
    switchDescription: (name: string, code: string) =>
      `${name} (${code}) \u306B\u5909\u66F4\u3057\u3001\u6982\u8981\u753B\u9762\u306B\u79FB\u52D5\u3057\u307E\u3059\u3002\u73FE\u5728\u306E\u30D5\u30A3\u30EB\u30BF\u30FC\u3068\u672A\u4FDD\u5B58\u306E\u5185\u5BB9\u306F\u5F15\u304D\u7D99\u304C\u308C\u307E\u305B\u3093\u3002`,
    cancel: "\u30AD\u30E3\u30F3\u30BB\u30EB",
    confirm: "\u56FD\u3092\u5909\u66F4",
    switching: "\u5909\u66F4\u4E2D...",
    error: "\u4F5C\u696D\u5BFE\u8C61\u56FD\u3092\u5909\u66F4\u3067\u304D\u307E\u305B\u3093\u3067\u3057\u305F\u3002\u3082\u3046\u4E00\u5EA6\u304A\u8A66\u3057\u304F\u3060\u3055\u3044\u3002",
  },
} as const;

export function AdminCountrySwitcher({
  countryCode,
  csrfToken,
  locale,
}: AdminCountrySwitcherProps) {
  const copy = copyByLocale[locale];
  const [countries, setCountries] = useState<CountryOption[]>([]);
  const [loadError, setLoadError] = useState(false);
  const [selectedCountry, setSelectedCountry] = useState<CountryOption | null>(null);
  const [mutationError, setMutationError] = useState("");
  const [pending, startTransition] = useTransition();
  const displayNames = useMemo(() => {
    const localeTag = locale === "ko" ? "ko-KR" : locale === "ja" ? "ja-JP" : "en-CA";
    return new Intl.DisplayNames([localeTag], { type: "region" });
  }, [locale]);
  const localizedName = (country: CountryOption) =>
    displayNames.of(country.country_code) ?? country.country_name ?? country.country_code;
  const currentName = displayNames.of(countryCode) ?? countryCode;

  useEffect(() => {
    const controller = new AbortController();
    setLoadError(false);
    fetch("/admin/country-options", { cache: "no-store", signal: controller.signal })
      .then(async (response) => {
        if (!response.ok) throw new Error("country_options_unavailable");
        const payload = await response.json() as { data?: { countries?: CountryOption[] } };
        setCountries(
          (payload.data?.countries ?? [])
            .filter((country) => /^[A-Z]{2}$/.test(country.country_code))
            .sort((left, right) => localizedName(left).localeCompare(localizedName(right), locale)),
        );
      })
      .catch((error: unknown) => {
        if (error instanceof DOMException && error.name === "AbortError") return;
        setLoadError(true);
      });
    return () => controller.abort();
  }, [displayNames, locale]);

  function requestSwitch(country: CountryOption) {
    if (country.country_code === countryCode || pending) return;
    setMutationError("");
    setSelectedCountry(country);
  }

  function confirmSwitch() {
    if (!selectedCountry || pending) return;
    setMutationError("");
    startTransition(async () => {
      try {
        const response = await fetch("/admin/switch-country", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            ...(csrfToken ? { "X-CSRF-Token": csrfToken } : {}),
          },
          body: JSON.stringify({ country_code: selectedCountry.country_code }),
        });
        if (!response.ok) {
          const payload = await response.json().catch(() => null) as { error?: { message?: string } } | null;
          throw new Error(payload?.error?.message || copy.error);
        }
        window.location.assign(buildAdminHref("/admin", new URLSearchParams(), locale));
      } catch (error) {
        setMutationError(error instanceof Error ? error.message : copy.error);
      }
    });
  }

  return (
    <>
      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <button
            aria-label={`${copy.label}: ${currentName}`}
            className="inline-flex min-h-9 items-center gap-2 rounded-md border border-sidebar-border bg-sidebar-accent px-2.5 text-xs font-semibold text-sidebar-foreground transition-colors hover:bg-sidebar-accent/80 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-sidebar-ring"
            type="button"
          >
            <Globe2 aria-hidden="true" className="h-4 w-4 text-sidebar-primary" />
            <span className="hidden max-w-36 truncate lg:inline">{currentName}</span>
            <span>{countryCode}</span>
            <ChevronDown aria-hidden="true" className="h-3.5 w-3.5 text-sidebar-foreground/60" />
          </button>
        </DropdownMenuTrigger>
        <DropdownMenuContent align="end" className="min-w-56">
          <DropdownMenuLabel>{copy.label}</DropdownMenuLabel>
          <DropdownMenuSeparator />
          {countries.length ? countries.map((country) => {
            const current = country.country_code === countryCode;
            return (
              <DropdownMenuItem
                className="min-h-10 cursor-pointer gap-2"
                disabled={pending}
                key={country.country_code}
                onSelect={() => requestSwitch(country)}
              >
                <span className="w-7 font-mono text-xs font-semibold text-muted-foreground">
                  {country.country_code}
                </span>
                <span className="min-w-0 flex-1 truncate">{localizedName(country)}</span>
                {current ? <Check aria-hidden="true" className="h-4 w-4 text-primary" /> : null}
              </DropdownMenuItem>
            );
          }) : (
            <div className="flex min-h-10 items-center gap-2 px-2.5 text-sm text-muted-foreground">
              {!loadError ? <Loader2 aria-hidden="true" className="h-4 w-4 animate-spin" /> : null}
              <span>{loadError ? copy.unavailable : copy.loading}</span>
            </div>
          )}
        </DropdownMenuContent>
      </DropdownMenu>

      <AlertDialog
        onOpenChange={(open) => {
          if (!open && !pending) {
            setSelectedCountry(null);
            setMutationError("");
          }
        }}
        open={Boolean(selectedCountry)}
      >
        <AlertDialogContent className="sm:max-w-md">
          <AlertDialogHeader>
            <AlertDialogTitle>{copy.switchTitle}</AlertDialogTitle>
            <AlertDialogDescription>
              {selectedCountry
                ? copy.switchDescription(localizedName(selectedCountry), selectedCountry.country_code)
                : ""}
            </AlertDialogDescription>
          </AlertDialogHeader>
          {mutationError ? <p className="text-sm font-medium text-destructive" role="alert">{mutationError}</p> : null}
          <AlertDialogFooter>
            <AlertDialogCancel disabled={pending}>{copy.cancel}</AlertDialogCancel>
            <Button disabled={pending} onClick={confirmSwitch} type="button">
              {pending ? copy.switching : copy.confirm}
            </Button>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </>
  );
}
