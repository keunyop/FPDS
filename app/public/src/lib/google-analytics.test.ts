import assert from 'node:assert/strict';
import test from 'node:test';
import { getAnalyticsPage, getGoogleAnalyticsMeasurementId } from './google-analytics.ts';

test('analytics sends fixed page metadata without dynamic identifiers', () => {
  for (const path of ['/products/private-id', '/guides/private-slug', '/ca/private-slug']) {
    const page = getAnalyticsPage(path)!;
    assert.ok(page);
    assert.equal(JSON.stringify(page).includes('private'), false);
    assert.equal(page.page_referrer, '');
  }
  assert.equal(getAnalyticsPage('/')?.page_title, 'Home | SwitchaBank');
});
test('private, unknown and URL-like input cannot produce analytics metadata', () => {
  for (const path of ['/admin', '/admin/login', '/api/public/feedback', '/unknown', '/?email=private', 'https://example.com/']) {
    assert.equal(getAnalyticsPage(path), null);
  }
});
test('missing and invalid measurement IDs disable the integration', () => {
  const old = process.env.NEXT_PUBLIC_GOOGLE_ANALYTICS_ID;
  try {
    delete process.env.NEXT_PUBLIC_GOOGLE_ANALYTICS_ID;
    assert.equal(getGoogleAnalyticsMeasurementId(), null);
    for (const value of ['', 'invalid', 'G-123<script>']) {
      process.env.NEXT_PUBLIC_GOOGLE_ANALYTICS_ID = value;
      assert.equal(getGoogleAnalyticsMeasurementId(), null);
    }
    process.env.NEXT_PUBLIC_GOOGLE_ANALYTICS_ID = ' G-TEST123456 ';
    assert.equal(getGoogleAnalyticsMeasurementId(), 'G-TEST123456');
  } finally {
    if (old === undefined) delete process.env.NEXT_PUBLIC_GOOGLE_ANALYTICS_ID;
    else process.env.NEXT_PUBLIC_GOOGLE_ANALYTICS_ID = old;
  }
});
