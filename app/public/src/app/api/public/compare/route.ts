import { NextRequest, NextResponse } from 'next/server';
import { fetchPublicProductDetail } from '@/lib/public-api';
import { loadComparison, parseComparison } from '@/lib/public-comparison';

export const dynamic = 'force-dynamic';
export async function GET(request: NextRequest) {
  const params = request.nextUrl.searchParams;
  const { ids, countryCode, locale, valid } = parseComparison(params);
  const headers = { 'cache-control': 'no-store', 'x-robots-tag': 'noindex' };
  if (!valid || !ids.length || params.toString().length > 1000
    || [...params.keys()].some(key => !['product_id', 'country_code', 'locale'].includes(key))) {
    return NextResponse.json({ error: 'Invalid comparison' }, { status: 400, headers });
  }
  const scope = new URLSearchParams({ country_code: countryCode, locale });
  const items = await loadComparison(ids, countryCode, id => fetchPublicProductDetail(id, scope, true));
  return NextResponse.json({ items }, { headers });
}
