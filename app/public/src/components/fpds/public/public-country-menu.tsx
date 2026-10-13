"use client";

import { Check, ChevronDown, MapPin } from "lucide-react";
import Link from "next/link";
import { usePathname, useSearchParams } from "next/navigation";
import { usePublishedCountries } from "./use-published-countries";

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
import { buildCountryHref, normalizeCountryCodeValue } from "@/lib/public-query";

export function PublicCountryMenu() {
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const locale = normalizePublicLocale(searchParams.get("locale") ?? "");
  const countryCode = normalizeCountryCodeValue(searchParams.get("country_code") ?? "");
  const copy = getPublicCountryCopy(locale);
  const countries = usePublishedCountries({ countryCode, locale });

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button
          className="h-11 max-w-44 whitespace-nowrap rounded-full border-border bg-card px-3 text-xs shadow-sm"
          size="sm"
          variant="outline"
        >
          <span className="sr-only">{copy.label}: </span>
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
