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
    <div className="flex items-center gap-1 rounded-full border border-border/80 bg-card px-1.5 py-1 text-xs text-muted-foreground">
      {LOCALE_ORDER.map((nextLocale) => {
        const href = buildAdminHref(pathname, new URLSearchParams(searchParams.toString()), nextLocale);
        const active = nextLocale === currentLocale;

        return (
          <Link
            key={nextLocale}
            href={href}
            className={cn(
              "rounded-full px-2.5 py-1 font-medium transition-colors",
              active ? "bg-muted text-foreground" : "hover:bg-muted/70 hover:text-foreground",
            )}
          >
            {getAdminLocaleLabel(nextLocale)}
          </Link>
        );
      })}
    </div>
  );
}
