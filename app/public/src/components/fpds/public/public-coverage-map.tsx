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

const COUNTRY_MARKERS: Record<
  string,
  { x: number; y: number; labelDx?: number; labelDy?: number }
> = {
  AU: { x: 848.24, y: 366.6 },
  BR: { x: 360.39, y: 327.33 },
  CA: { x: 273.07, y: 87.58 },
  CN: { x: 758.23, y: 148.07 },
  DE: { x: 523.3, y: 101.1, labelDx: 18, labelDy: -8 },
  FR: { x: 505.13, y: 115.47, labelDx: -19, labelDy: 19 },
  GB: { x: 492.62, y: 89.56, labelDx: -17, labelDy: -12 },
  IN: { x: 708.87, y: 200.43 },
  JP: { x: 841.98, y: 146.95, labelDx: 17, labelDy: -10 },
  KR: { x: 816.56, y: 147.92, labelDx: -17, labelDy: 19 },
  MX: { x: 231.43, y: 189.7 },
  NZ: { x: 920.57, y: 418.71 },
  SG: { x: 783.27, y: 270.31, labelDy: 19 },
  US: { x: 261.32, y: 135.25 }
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
      className="min-w-0 rounded-xl border border-foreground/15 bg-card/70 p-4 md:p-5"
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

      <div className="mt-4 overflow-hidden rounded-lg border border-border/80 bg-background/45">
        <svg
          aria-label={copy.title}
          className="mx-auto block aspect-[2/1] w-full"
          preserveAspectRatio="xMidYMid meet"
          role="img"
          viewBox="55 27.5 890 445"
        >
          <title>{copy.title}</title>
          <g className="fill-none stroke-border/70" strokeDasharray="2 11" strokeWidth="1.25">
            <path d="M68 135Q500 91 932 135M48 250H952M68 365Q500 409 932 365" />
            <path d="M250 32Q166 250 250 468M500 24V476M750 32Q834 250 750 468" />
          </g>
          <image
            aria-hidden="true"
            height="500"
            href="/world-map-equal-earth.svg"
            preserveAspectRatio="xMidYMid meet"
            width="1000"
          />
          {markers.map((country) => {
            const point = COUNTRY_MARKERS[country.code];
            const active = country.code === currentCountryCode;
            const labelX = point.x + (point.labelDx ?? 0);
            const labelY = point.y + (point.labelDy ?? -15);
            return (
              <g aria-hidden="true" key={country.code}>
                <circle
                  className={cn(active ? "fill-maple/15" : "fill-primary/12")}
                  cx={point.x}
                  cy={point.y}
                  r={active ? 18 : 14}
                />
                <circle
                  className={cn(active ? "fill-maple stroke-background" : "fill-primary stroke-background")}
                  cx={point.x}
                  cy={point.y}
                  r={active ? 8 : 6.5}
                  strokeWidth="4"
                />
                <text
                  className="fill-foreground font-mono text-[21px] font-bold"
                  style={{
                    paintOrder: "stroke",
                    stroke: "var(--card)",
                    strokeLinejoin: "round",
                    strokeWidth: 7
                  }}
                  textAnchor="middle"
                  x={labelX}
                  y={labelY}
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
            const bankCount =
              typeof country.bank_count === "number"
                ? formatPublicMessage(copy.banks, {
                    count: new Intl.NumberFormat(getIntlLocale(normalizedLocale)).format(
                      Math.max(0, country.bank_count)
                    )
                  })
                : null;
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
                  <span className="mt-0.5 flex flex-wrap items-center gap-x-1.5 gap-y-0.5 text-xs font-semibold tabular-nums text-muted-foreground">
                    <span className="whitespace-nowrap">{productCount}</span>
                    {bankCount ? (
                      <>
                        <span aria-hidden="true" className="text-border">·</span>
                        <span className="whitespace-nowrap">{bankCount}</span>
                      </>
                    ) : null}
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
