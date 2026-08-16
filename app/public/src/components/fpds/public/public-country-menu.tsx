"use client";

import { Check, ChevronDown, MapPin } from "lucide-react";
import Link from "next/link";
import { usePathname, useSearchParams } from "next/navigation";
import { useEffect, useMemo, useState } from "react";

import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger
} from "@/components/ui/dropdown-menu";
import { formatPublicCountryName, getPublicCountryCopy } from "@/lib/public-country";
import { normalizePublicLocale } from "@/lib/public-locale";
import type { PublicCountryOption } from "@/lib/public-api";
import { buildCountryHref, normalizeCountryCodeValue } from "@/lib/public-query";

type CountriesEnvelope = {
  data?: {
    countries?: PublicCountryOption[];
  };
};

export function PublicCountryMenu() {
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const locale = normalizePublicLocale(searchParams.get("locale") ?? "");
  const countryCode = normalizeCountryCodeValue(searchParams.get("country_code") ?? "");
  const copy = getPublicCountryCopy(locale);
  const [publishedCountries, setPublishedCountries] = useState<PublicCountryOption[]>([]);

  useEffect(() => {
    const controller = new AbortController();

    fetch("/api/public/countries", { signal: controller.signal })
      .then((response) => (response.ok ? response.json() as Promise<CountriesEnvelope> : null))
      .then((payload) => {
        const countries = payload?.data?.countries;
        if (Array.isArray(countries)) {
          setPublishedCountries(
            countries.filter((country) => /^[A-Z]{2}$/.test(country.code) && country.count > 0)
          );
        }
      })
      .catch(() => undefined);

    return () => controller.abort();
  }, []);

  const countries = useMemo(() => {
    const options = new Map(publishedCountries.map((country) => [country.code, country]));
    if (!options.has(countryCode)) {
      options.set(countryCode, { code: countryCode, count: 0 });
    }
    return [...options.values()].sort((left, right) =>
      formatPublicCountryName(left.code, locale).localeCompare(formatPublicCountryName(right.code, locale), locale)
    );
  }, [countryCode, locale, publishedCountries]);

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button
          aria-label={`${copy.label}: ${formatPublicCountryName(countryCode, locale)}`}
          className="h-11 max-w-44 whitespace-nowrap rounded-full border-border bg-card px-3 text-xs shadow-sm"
          size="sm"
          variant="outline"
        >
          <MapPin className="size-3.5 shrink-0 text-muted-foreground" aria-hidden="true" />
          <span className="hidden truncate font-medium min-[380px]:inline">
            {formatPublicCountryName(countryCode, locale)}
          </span>
          <span className="font-semibold uppercase min-[380px]:hidden">{countryCode}</span>
          <ChevronDown className="size-3.5 shrink-0 text-muted-foreground" aria-hidden="true" />
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="min-w-56">
        <DropdownMenuLabel>{copy.label}</DropdownMenuLabel>
        <DropdownMenuSeparator />
        {countries.map((country) => {
          const active = country.code === countryCode;
          return (
            <DropdownMenuItem asChild className="min-h-11 cursor-pointer px-2.5" key={country.code}>
              <Link href={buildCountryHref(pathname, searchParams, country.code)}>
                <span className="flex min-w-0 flex-1 items-center gap-2">
                  <span className="w-7 text-xs font-semibold uppercase text-muted-foreground">{country.code}</span>
                  <span className="min-w-0">
                    <span className="block truncate">{formatPublicCountryName(country.code, locale)}</span>
                    {country.count === 0 ? (
                      <span className="block text-[11px] text-muted-foreground">{copy.unavailable}</span>
                    ) : null}
                  </span>
                </span>
                {active ? <Check className="size-4 text-primary" aria-hidden="true" /> : null}
              </Link>
            </DropdownMenuItem>
          );
        })}
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
