"use client";

import { Check, CreditCard, House, Landmark, MapPin, Menu, Search } from "lucide-react";
import Link from "next/link";
import { usePathname, useSearchParams } from "next/navigation";
import { useState, type ComponentType } from "react";

import { usePublishedCountries } from "@/components/fpds/public/use-published-countries";
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
import { getPublicMessages, normalizePublicLocale } from "@/lib/public-locale";
import {
  buildCountryHref,
  buildScopedPublicHrefFromSearchParams,
  normalizeCountryCodeValue,
  type PublicRoutePath
} from "@/lib/public-query";
import { cn } from "@/lib/utils";

export function PublicMobileMenu() {
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const locale = normalizePublicLocale(searchParams.get("locale") ?? "");
  const countryCode = normalizeCountryCodeValue(searchParams.get("country_code") ?? "");
  const copy = getPublicMessages(locale);
  const countryCopy = getPublicCountryCopy(locale);
  const [open, setOpen] = useState(false);
  const countries = usePublishedCountries({ active: open, countryCode, locale });
  const navItems: Array<{
    href: PublicRoutePath;
    icon: ComponentType<{ className?: string }>;
    label: string;
  }> = [
    { href: "/dashboard", icon: House, label: copy.nav.dashboard },
    { href: "/products", icon: Search, label: copy.nav.products },
    { href: "/cards", icon: CreditCard, label: copy.nav.card },
    { href: "/loans", icon: Landmark, label: copy.nav.loan }
  ];

  return (
    <DropdownMenu onOpenChange={setOpen} open={open}>
      <DropdownMenuTrigger asChild>
        <Button
          aria-label={copy.nav.primaryLabel}
          className="size-11 rounded-full border-border bg-card shadow-sm"
          size="icon"
          variant="outline"
        >
          <Menu className="size-5" aria-hidden="true" />
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent
        align="end"
        className="w-[min(20rem,calc(100vw-2rem))] p-1.5"
        sideOffset={8}
      >
        <DropdownMenuLabel className="px-2 py-1.5">{copy.nav.primaryLabel}</DropdownMenuLabel>
        {navItems.map((item) => {
          const active = pathname === item.href || (item.href === "/dashboard" && pathname === "/");
          const Icon = item.icon;
          return (
            <DropdownMenuItem asChild className="min-h-11 px-2.5" key={item.href}>
              <Link
                aria-current={active ? "page" : undefined}
                className={cn(active && "bg-muted font-semibold text-foreground")}
                href={buildScopedPublicHrefFromSearchParams(item.href, searchParams)}
              >
                <Icon className="size-4 text-muted-foreground" aria-hidden="true" />
                <span className="flex-1">{item.label}</span>
                {active ? <Check className="size-4 text-primary" aria-hidden="true" /> : null}
              </Link>
            </DropdownMenuItem>
          );
        })}

        <DropdownMenuSeparator />
        <DropdownMenuLabel className="flex items-center gap-2 px-2 py-1.5">
          <MapPin className="size-3.5" aria-hidden="true" />
          {countryCopy.label}
        </DropdownMenuLabel>
        {countries.map((country) => {
          const active = country.code === countryCode;
          return (
            <DropdownMenuItem asChild className="min-h-11 px-2.5" key={country.code}>
              <Link
                aria-current={active ? "true" : undefined}
                className={cn(active && "bg-muted font-semibold text-foreground")}
                href={buildCountryHref(pathname, searchParams, country.code)}
              >
                <span className="w-8 text-xs font-semibold uppercase text-muted-foreground">
                  {country.code}
                </span>
                <span className="min-w-0 flex-1 truncate">
                  {formatPublicCountryName(country.code, locale)}
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
