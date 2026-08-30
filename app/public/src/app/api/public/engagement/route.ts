import { NextResponse } from 'next/server';

import { getPublicApiOrigin } from '@/lib/public-api';

export const dynamic = 'force-dynamic';

const EVENT_TYPES = new Set([
  'finder_product_selected',
  'official_bank_click',
  'product_detail_click'
]);

export async function POST(request: Request) {
  const contentLength = Number(request.headers.get('content-length') ?? '0');
  if (Number.isFinite(contentLength) && contentLength > 1024) {
    return NextResponse.json({ error: { code: 'payload_too_large' } }, { status: 413 });
  }

  let payload: Record<string, unknown>;
  try {
    payload = await request.json() as Record<string, unknown>;
  } catch {
    return NextResponse.json({ error: { code: 'invalid_payload' } }, { status: 400 });
  }

  const countryCode = typeof payload.country_code === 'string'
    ? payload.country_code.trim().toUpperCase()
    : '';
  const eventType = typeof payload.event_type === 'string'
    ? payload.event_type.trim().toLowerCase()
    : '';
  const productId = typeof payload.product_id === 'string'
    ? payload.product_id.trim()
    : '';
  if (
    !/^[A-Z]{2}$/.test(countryCode)
    || !EVENT_TYPES.has(eventType)
    || !productId
    || productId.length > 120
  ) {
    return NextResponse.json({ error: { code: 'invalid_payload' } }, { status: 400 });
  }

  const apiSecret = process.env.FPDS_PUBLIC_APP_API_SECRET?.trim();
  if (!apiSecret) {
    return NextResponse.json(
      { error: { code: 'public_app_credential_not_configured' } },
      { status: 503 }
    );
  }

  try {
    const response = await fetch(
      new URL('/api/public/engagement', getPublicApiOrigin()),
      {
        body: JSON.stringify({
          country_code: countryCode,
          event_type: eventType,
          product_id: productId
        }),
        cache: 'no-store',
        headers: {
          'content-type': 'application/json',
          'x-fpds-public-app-secret': apiSecret
        },
        method: 'POST'
      }
    );
    return new NextResponse(await response.text(), {
      status: response.status,
      headers: {
        'cache-control': 'no-store',
        'content-type': response.headers.get('content-type') ?? 'application/json'
      }
    });
  } catch {
    return NextResponse.json(
      { error: { code: 'public_engagement_unavailable' } },
      { status: 503 }
    );
  }
}
