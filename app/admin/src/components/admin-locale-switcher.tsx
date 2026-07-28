"use client";

import Link from "next/link";
import { usePathname, useSearchParams } from "next/navigation";

import { buildAdminHref, getAdminLocaleLabel, normalizeAdminLocale, type AdminLocale } from "@/lib/admin-i18n";
import { cn } from "@/lib/utils";

const LOCALE_ORDER: AdminLocale[] = ["en", "ko", "ja"];

type AdminLocaleSwitcherProps = {
  locale: AdminLocale;
};

export function AdminLocaleSwitcher({ locale }: AdminLocaleSwitcherProps) {
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const currentLocale = locale ?? normalizeAdminLocale(searchParams.get("locale"));

  return (
    <div className="flex min-h-10 items-center gap-0.5 rounded-md border border-border/80 bg-card p-1 text-xs text-muted-foreground">
      {LOCALE_ORDER.map((nextLocale) => {
        const href = buildAdminHref(pathname, new URLSearchParams(searchParams.toString()), nextLocale);
        const active = nextLocale === currentLocale;

        return (
          <Link
            key={nextLocale}
            href={href}
            className={cn(
              "inline-flex min-h-10 min-w-10 items-center justify-center rounded-sm px-2 font-semibold transition-colors",
              active ? "bg-primary text-primary-foreground" : "hover:bg-muted hover:text-foreground",
            )}
            aria-current={active ? "page" : undefined}
          >
            {getAdminLocaleLabel(nextLocale)}
          </Link>
        );
      })}
    </div>
  );
}
