'use client';

import Link from 'next/link';
import type { ReactNode } from 'react';

type PublicEngagementEventType =
  | 'finder_product_selected'
  | 'official_bank_click'
  | 'product_detail_click';

type EngagementLinkProps = {
  children: ReactNode;
  className?: string;
  countryCode: string;
  href: string;
  productId: string;
};

export function recordProductEngagement({
  countryCode,
  eventType,
  productId
}: {
  countryCode: string;
  eventType: PublicEngagementEventType;
  productId: string;
}) {
  const body = JSON.stringify({
    country_code: countryCode,
    event_type: eventType,
    product_id: productId
  });

  if (typeof navigator !== 'undefined' && typeof navigator.sendBeacon === 'function') {
    const accepted = navigator.sendBeacon(
      '/api/public/engagement',
      new Blob([body], { type: 'application/json' })
    );
    if (accepted) return;
  }

  void fetch('/api/public/engagement', {
    body,
    cache: 'no-store',
    headers: { 'content-type': 'application/json' },
    keepalive: true,
    method: 'POST'
  }).catch(() => {
    // Analytics is best-effort and must never block product navigation.
  });
}

export function TrackedProductLink({
  children,
  className,
  countryCode,
  href,
  productId
}: EngagementLinkProps) {
  return (
    <Link
      className={className}
      href={href}
      onClick={() => recordProductEngagement({
        countryCode,
        eventType: 'product_detail_click',
        productId
      })}
    >
      {children}
    </Link>
  );
}

export function TrackedOfficialBankLink({
  children,
  className,
  countryCode,
  href,
  productId
}: EngagementLinkProps) {
  return (
    <a
      className={className}
      href={href}
      onClick={() => recordProductEngagement({
        countryCode,
        eventType: 'official_bank_click',
        productId
      })}
      rel='noopener noreferrer'
      target='_blank'
    >
      {children}
    </a>
  );
}
