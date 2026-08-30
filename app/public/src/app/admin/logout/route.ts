import { NextRequest, NextResponse } from 'next/server';

import { PUBLIC_ADMIN_COOKIE_NAME } from '@/lib/public-admin-auth';

export async function POST(request: NextRequest) {
  const response = NextResponse.redirect(new URL('/admin', request.url), 303);
  response.cookies.set(PUBLIC_ADMIN_COOKIE_NAME, '', {
    expires: new Date(0),
    httpOnly: true,
    path: '/admin',
    sameSite: 'strict',
    secure: process.env.NODE_ENV === 'production'
  });
  return response;
}
