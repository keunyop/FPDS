'use client';

import { useEffect, useMemo, useState } from 'react';

import { publicCountryOptions } from '@/lib/public-country';
import type { PublicCountryOption } from '@/lib/public-api';
import type { PublicLocale } from '@/lib/public-locale';

type CountriesEnvelope = {
  data?: {
    countries?: PublicCountryOption[];
  };
};

export function usePublishedCountries({
  active = true,
  countryCode,
  locale
}: {
  active?: boolean;
  countryCode: string;
  locale: PublicLocale;
}) {
  const [publishedCountries, setPublishedCountries] = useState<PublicCountryOption[]>([]);

  useEffect(() => {
    if (!active) {
      return;
    }

    const controller = new AbortController();
    fetch('/api/public/countries', { signal: controller.signal })
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
  }, [active]);

  return useMemo(() => publicCountryOptions(publishedCountries, countryCode, locale),
    [countryCode, locale, publishedCountries]);
}
