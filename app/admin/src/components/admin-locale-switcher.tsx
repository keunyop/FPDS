"use client";

import { Check, ChevronDown, Globe2 } from "lucide-react";
import Link from "next/link";
import { usePathname, useSearchParams } from "next/navigation";

import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
  buildAdminHref,
  getAdminLanguageLabel,
  getAdminLocaleLabel,
  getAdminLocaleName,
  normalizeAdminLocale,
  type AdminLocale,
} from "@/lib/admin-i18n";
import { cn } from "@/lib/utils";

const LOCALE_ORDER: AdminLocale[] = ["en", "ko", "ja"];

type AdminLocaleSwitcherProps = {
  align?: "center" | "end" | "start";
  className?: string;
  locale: AdminLocale;
  triggerClassName?: string;
  variant?: "menu" | "standalone";
};

export function AdminLocaleSwitcher({
  align = "end",
  className,
  locale,
  triggerClassName,
  variant = "standalone",
}: AdminLocaleSwitcherProps) {
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const currentLocale = locale ?? normalizeAdminLocale(searchParams.get("locale"));
  const languageLabel = getAdminLanguageLabel(currentLocale);

  const localeItems = LOCALE_ORDER.map((nextLocale) => {
    const href = buildAdminHref(pathname, new URLSearchParams(searchParams.toString()), nextLocale);
    const active = nextLocale === currentLocale;

    return (
      <DropdownMenuItem asChild className="min-h-10 cursor-pointer px-2.5" key={nextLocale}>
        <Link aria-current={active ? "page" : undefined} href={href}>
          <span className="flex min-w-0 flex-1 items-center gap-2">
            <span className="w-7 text-xs font-semibold uppercase text-muted-foreground">
              {getAdminLocaleLabel(nextLocale)}
            </span>
            <span className="truncate">{getAdminLocaleName(nextLocale)}</span>
          </span>
          {active ? <Check aria-hidden="true" className="size-4 text-primary" /> : null}
        </Link>
      </DropdownMenuItem>
    );
  });

  if (variant === "menu") {
    return (
      <div className={className}>
        <DropdownMenuLabel className="flex min-h-9 items-center gap-2 px-2.5">
          <Globe2 aria-hidden="true" className="size-4" />
          <span>{languageLabel}</span>
        </DropdownMenuLabel>
        {localeItems}
      </div>
    );
  }

  return (
    <div className={className}>
      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <Button
            aria-label={languageLabel}
            className={cn(
              "h-11 min-w-40 justify-between border-border bg-card px-3 text-sm shadow-xs",
              triggerClassName,
            )}
            size="sm"
            variant="outline"
          >
            <span className="flex min-w-0 items-center gap-2">
              <Globe2 aria-hidden="true" className="size-4 text-muted-foreground" />
              <span className="truncate">{getAdminLocaleName(currentLocale)}</span>
            </span>
            <ChevronDown aria-hidden="true" className="size-4 text-muted-foreground" />
          </Button>
        </DropdownMenuTrigger>
        <DropdownMenuContent align={align} className="min-w-44">
          <DropdownMenuLabel>{languageLabel}</DropdownMenuLabel>
          <DropdownMenuSeparator />
          {localeItems}
        </DropdownMenuContent>
      </DropdownMenu>
    </div>
  );
}
