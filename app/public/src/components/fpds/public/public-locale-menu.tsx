"use client";

import { Check, ChevronDown, Globe2 } from "lucide-react";
import Link from "next/link";
import { usePathname, useSearchParams, type ReadonlyURLSearchParams } from "next/navigation";

import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger
} from "@/components/ui/dropdown-menu";
import { getPublicMessages, normalizePublicLocale, type PublicLocale } from "@/lib/public-locale";
import { cn } from "@/lib/utils";

export function buildLocaleHref(pathname: string, searchParams: ReadonlyURLSearchParams, locale: string) {
  const params = new URLSearchParams(searchParams.toString());
  if (locale === "en") {
    params.delete("locale");
  } else {
    params.set("locale", locale);
  }

  const query = params.toString();
  return query ? `${pathname}?${query}` : pathname;
}

export function PublicLocaleMenu({
  align = "end",
  className,
  triggerClassName
}: {
  align?: "center" | "end" | "start";
  className?: string;
  triggerClassName?: string;
}) {
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const locale = normalizePublicLocale(searchParams.get("locale") ?? "");
  const copy = getPublicMessages(locale);
  const options: PublicLocale[] = ["en", "ko", "ja"];

  return (
    <div className={className}>
      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <Button
            aria-label={copy.nav.localeLabel}
            className={cn("h-10 rounded-full border-border bg-card px-3 text-xs shadow-sm", triggerClassName)}
            size="sm"
            variant="outline"
          >
            <Globe2 className="size-3.5 text-muted-foreground" aria-hidden="true" />
            <span className="hidden sm:inline">{getPublicMessages(locale).localeName}</span>
            <span className="font-semibold uppercase tabular-nums sm:hidden">{locale}</span>
            <ChevronDown className="size-3.5 text-muted-foreground" aria-hidden="true" />
          </Button>
        </DropdownMenuTrigger>
        <DropdownMenuContent align={align} className="min-w-44">
          <DropdownMenuLabel>{copy.nav.localeLabel}</DropdownMenuLabel>
          <DropdownMenuSeparator />
          {options.map((option) => {
            const active = option === locale;
            return (
              <DropdownMenuItem asChild className="min-h-9 cursor-pointer px-2.5" key={option}>
                <Link href={buildLocaleHref(pathname, searchParams, option)}>
                  <span className="flex min-w-0 flex-1 items-center gap-2">
                    <span className="w-7 text-xs font-semibold uppercase text-muted-foreground">{option}</span>
                    <span className="truncate">{getPublicMessages(option).localeName}</span>
                  </span>
                  {active ? <Check className="size-4 text-primary" aria-hidden="true" /> : null}
                </Link>
              </DropdownMenuItem>
            );
          })}
        </DropdownMenuContent>
      </DropdownMenu>
    </div>
  );
}
