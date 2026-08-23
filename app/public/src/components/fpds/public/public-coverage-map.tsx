import { Check } from "lucide-react";

import { formatPublicCountryName } from "@/lib/public-country";
import type { PublicCountryOption } from "@/lib/public-api";
import {
  formatPublicMessage,
  getIntlLocale,
  getPublicCoverageCopy,
  normalizePublicLocale
} from "@/lib/public-locale";
import { cn } from "@/lib/utils";

const COUNTRY_MARKERS: Record<string, { x: number; y: number }> = {
  AU: { x: 526, y: 226 },
  BR: { x: 208, y: 205 },
  CA: { x: 112, y: 78 },
  CN: { x: 470, y: 132 },
  DE: { x: 352, y: 102 },
  FR: { x: 338, y: 114 },
  GB: { x: 327, y: 94 },
  IN: { x: 439, y: 161 },
  JP: { x: 527, y: 130 },
  KR: { x: 510, y: 132 },
  MX: { x: 137, y: 151 },
  NZ: { x: 569, y: 239 },
  SG: { x: 472, y: 194 },
  US: { x: 127, y: 116 }
};

export function PublicCoverageMap({
  countries,
  currentCountryCode,
  locale,
  unavailable
}: {
  countries: PublicCountryOption[];
  currentCountryCode: string;
  locale: string;
  unavailable: boolean;
}) {
  const normalizedLocale = normalizePublicLocale(locale);
  const copy = getPublicCoverageCopy(normalizedLocale);
  const publishedCountries = countries
    .filter((country) => /^[A-Z]{2}$/.test(country.code) && country.count > 0)
    .sort((left, right) =>
      formatPublicCountryName(left.code, normalizedLocale).localeCompare(
        formatPublicCountryName(right.code, normalizedLocale),
        normalizedLocale
      )
    );
  const markers = publishedCountries.filter((country) => COUNTRY_MARKERS[country.code]);

  return (
    <aside
      aria-labelledby="coverage-map-title"
      className="min-w-0 border-y border-foreground/20 bg-card/55 px-4 py-4 md:px-5"
    >
      <div className="flex items-end justify-between gap-4">
        <div>
          <h2 id="coverage-map-title" className="text-lg font-semibold tracking-[-0.02em]">
            {copy.title}
          </h2>
          <p className="mt-1 text-xs text-muted-foreground">{copy.description}</p>
        </div>
        <span className="font-mono text-[10px] font-semibold uppercase tracking-[0.14em] text-primary">
          {publishedCountries.length}
        </span>
      </div>

      <div className="mt-4 overflow-hidden rounded-lg border border-border/80 bg-background/45 p-2">
        <svg
          aria-label={copy.title}
          className="aspect-[2.15/1] w-full"
          role="img"
          viewBox="0 0 600 280"
        >
          <g className="fill-none stroke-border/60" strokeWidth="1">
            <path d="M20 70H580M20 140H580M20 210H580" strokeDasharray="3 7" />
            <path d="M150 24V256M300 24V256M450 24V256" strokeDasharray="3 7" />
          </g>
          <g className="fill-muted stroke-foreground/20" strokeLinejoin="round" strokeWidth="1.4">
            <path d="M44 58 82 34l69 8 42 30-9 28-27 9-19 31-31 13-17-31-28-16-22-24Z" />
            <path d="m170 153 39 10 24 34-8 38-24 33-15-40-22-31Z" />
            <path d="m302 72 42-18 50 12 24 25-27 17-43-3-30 15-26-18Z" />
            <path d="m349 116 44 8 26 35-17 64-33 27-24-49-17-46Z" />
            <path d="m393 72 79-26 83 25 20 34-31 31-47-2-28 31-39-12-16-35-28-24Z" />
            <path d="m486 200 39-20 48 20-9 37-49 11-34-25Z" />
            <path d="m81 24 30-13 29 13-16 19-33 3Z" />
          </g>
          {markers.map((country) => {
            const point = COUNTRY_MARKERS[country.code];
            const active = country.code === currentCountryCode;
            return (
              <g aria-hidden="true" key={country.code}>
                <circle
                  className={cn(active ? "fill-maple stroke-background" : "fill-primary stroke-background")}
                  cx={point.x}
                  cy={point.y}
                  r={active ? 6.5 : 5}
                  strokeWidth="3"
                />
                <text
                  className="fill-foreground font-mono text-[10px] font-bold"
                  textAnchor="middle"
                  x={point.x}
                  y={point.y - 10}
                >
                  {country.code}
                </text>
              </g>
            );
          })}
        </svg>
      </div>

      {unavailable || !publishedCountries.length ? (
        <p className="mt-3 rounded-md border border-dashed border-border px-3 py-3 text-sm text-muted-foreground">
          {copy.unavailable}
        </p>
      ) : (
        <ul className="mt-3 grid gap-2 sm:grid-cols-2">
          {publishedCountries.map((country) => {
            const active = country.code === currentCountryCode;
            const countryName = formatPublicCountryName(country.code, normalizedLocale);
            const productCount = formatPublicMessage(copy.products, {
              count: new Intl.NumberFormat(getIntlLocale(normalizedLocale)).format(country.count)
            });
            return (
              <li
                aria-current={active ? "true" : undefined}
                className={cn(
                  "flex min-h-11 items-center gap-2 rounded-md border px-3 py-2 text-sm",
                  active ? "border-maple/35 bg-maple/5" : "border-border bg-background/55"
                )}
                key={country.code}
              >
                <span className="w-7 font-mono text-xs font-bold text-muted-foreground">
                  {country.code}
                </span>
                <span className="min-w-0 flex-1">
                  <span className="block truncate font-medium">{countryName}</span>
                  <span className="mt-0.5 block whitespace-nowrap text-xs font-semibold tabular-nums text-muted-foreground">
                    {productCount}
                  </span>
                </span>
                {active ? <Check className="size-3.5 shrink-0 text-maple" aria-hidden="true" /> : null}
              </li>
            );
          })}
        </ul>
      )}
    </aside>
  );
}
