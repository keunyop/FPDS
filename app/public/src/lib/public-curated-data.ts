import { cache } from 'react';
import { fetchPublicProducts } from '@/lib/public-api';
import { loadCuratedProducts } from '@/lib/public-curated';

export const fetchCuratedProducts = cache(async (locale = 'en') => {
  try {
    return await loadCuratedProducts(page => {
      const params = new URLSearchParams({
      country_code: 'CA', locale,
      page: String(page), page_size: '100', sort_by: 'product_name', sort_order: 'asc'
      });
      for (const type of ['chequing', 'savings', 'gic']) params.append('product_type', type);
      return fetchPublicProducts(params);
    });
  } catch { return null; }
});
