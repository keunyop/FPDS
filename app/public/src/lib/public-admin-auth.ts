import 'server-only';

import { createHmac, createHash, randomBytes, timingSafeEqual } from 'crypto';

export const PUBLIC_ADMIN_COOKIE_NAME = 'switchabank_public_admin_session';
export const PUBLIC_ADMIN_SESSION_MAX_AGE_SECONDS = 8 * 60 * 60;

function configuredPassword() {
  return process.env.FPDS_PUBLIC_ADMIN_PASSWORD?.trim() ?? '';
}

function configuredSessionSecret() {
  return process.env.FPDS_PUBLIC_ADMIN_SESSION_SECRET?.trim() ?? '';
}

function safeEqual(left: string, right: string) {
  const leftHash = createHash('sha256').update(left).digest();
  const rightHash = createHash('sha256').update(right).digest();
  return timingSafeEqual(leftHash, rightHash);
}

function signature(value: string) {
  return createHmac('sha256', configuredSessionSecret()).update(value).digest('base64url');
}

export function publicAdminIsConfigured() {
  return Boolean(configuredPassword() && configuredSessionSecret());
}

export function authenticatePublicAdmin(password: string) {
  return publicAdminIsConfigured() && safeEqual(password, configuredPassword());
}

export function createPublicAdminSession() {
  if (!publicAdminIsConfigured()) {
    throw new Error('Public Admin authentication is not configured.');
  }
  const expiresAt = Math.floor(Date.now() / 1000) + PUBLIC_ADMIN_SESSION_MAX_AGE_SECONDS;
  const payload = 'v1.' + expiresAt + '.' + randomBytes(18).toString('base64url');
  return payload + '.' + signature(payload);
}

export function verifyPublicAdminSession(token: string | undefined) {
  if (!token || !publicAdminIsConfigured()) return false;
  const parts = token.split('.');
  if (parts.length !== 4 || parts[0] !== 'v1') return false;
  const payload = parts.slice(0, 3).join('.');
  const expiresAt = Number(parts[1]);
  return Number.isInteger(expiresAt)
    && expiresAt > Math.floor(Date.now() / 1000)
    && safeEqual(parts[3], signature(payload));
}
