import { NextRequest, NextResponse } from 'next/server';

import {
  authenticatePublicAdmin,
  createPublicAdminSession,
  PUBLIC_ADMIN_COOKIE_NAME,
  PUBLIC_ADMIN_SESSION_MAX_AGE_SECONDS,
  publicAdminIsConfigured
} from '@/lib/public-admin-auth';

const attempts = new Map<string, number[]>();
const WINDOW_MS = 15 * 60 * 1000;
const MAX_ATTEMPTS = 5;

function requesterKey(request: NextRequest) {
  return request.headers.get('x-forwarded-for')?.split(',')[0]?.trim()
    || request.headers.get('x-real-ip')
    || 'unknown';
}

function isRateLimited(key: string) {
  const cutoff = Date.now() - WINDOW_MS;
  const recent = (attempts.get(key) ?? []).filter((attemptedAt) => attemptedAt > cutoff);
  attempts.set(key, recent);
  return recent.length >= MAX_ATTEMPTS;
}

function recordFailure(key: string) {
  attempts.set(key, [...(attempts.get(key) ?? []), Date.now()].slice(-MAX_ATTEMPTS));
}

function redirectWithError(request: NextRequest, error: string) {
  const url = new URL('/admin', request.url);
  url.searchParams.set('error', error);
  return NextResponse.redirect(url, 303);
}

export async function POST(request: NextRequest) {
  if (!publicAdminIsConfigured()) return redirectWithError(request, 'config');

  const key = requesterKey(request);
  if (isRateLimited(key)) return redirectWithError(request, 'rate');

  const formData = await request.formData();
  const password = String(formData.get('password') ?? '').slice(0, 256);
  if (!authenticatePublicAdmin(password)) {
    recordFailure(key);
    return redirectWithError(request, 'invalid');
  }

  attempts.delete(key);
  const response = NextResponse.redirect(new URL('/admin', request.url), 303);
  response.cookies.set(PUBLIC_ADMIN_COOKIE_NAME, createPublicAdminSession(), {
    httpOnly: true,
    maxAge: PUBLIC_ADMIN_SESSION_MAX_AGE_SECONDS,
    path: '/admin',
    sameSite: 'strict',
    secure: process.env.NODE_ENV === 'production'
  });
  return response;
}
