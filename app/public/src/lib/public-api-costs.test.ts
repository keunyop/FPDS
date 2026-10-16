import assert from 'node:assert/strict';
import test from 'node:test';
import { fetchPublicProductDetail, fetchPublicProducts, isPublicApiError } from './public-api.ts';

test('ordinary catalog reads keep bounded Next caching and native query scope', async t => {
  let requested: URL | undefined;
  let options: RequestInit & { next?: { revalidate: number } } = {};
  t.mock.method(globalThis, 'fetch', async (input: URL, init: typeof options) => {
    requested = new URL(input);
    options = init;
    return Response.json({ data: { items: [], total_items: 0 } });
  });
  const scope = new URLSearchParams({ country_code: 'PH', locale: 'fil', q: 'Savings' });
  await fetchPublicProducts(scope);
  assert.equal(requested?.pathname, '/api/public/products');
  assert.equal(requested?.searchParams.get('country_code'), 'PH');
  assert.equal(requested?.searchParams.get('locale'), 'fil');
  assert.equal(requested?.searchParams.has('fresh'), false);
  assert.deepEqual(options.next, { revalidate: 300 });
  assert.equal(options.cache, undefined);
  assert.equal(scope.has('fresh'), false);
});

test('live comparison reads bypass both Next and API CDN without mutating saved scope', async t => {
  let requested: URL | undefined;
  let options: RequestInit & { next?: unknown } = {};
  t.mock.method(globalThis, 'fetch', async (input: URL, init: typeof options) => {
    requested = new URL(input);
    options = init;
    return Response.json({ data: { product: { product_id: 'prod_AbC' } } });
  });
  const scope = new URLSearchParams({ country_code: 'US', locale: 'ja' });
  const result = await fetchPublicProductDetail('prod_AbC', scope, true);
  assert.equal(result.product.product_id, 'prod_AbC');
  assert.equal(requested?.pathname, '/api/public/products/prod_AbC');
  assert.equal(requested?.searchParams.get('fresh'), '1');
  assert.equal(requested?.searchParams.get('country_code'), 'US');
  assert.equal(options.cache, 'no-store');
  assert.equal(options.next, undefined);
  assert.equal(scope.has('fresh'), false);
});

test('ordinary details retain the existing revalidation window', async t => {
  t.mock.method(globalThis, 'fetch', async (input: URL, init: RequestInit & { next?: unknown }) => {
    assert.equal(new URL(input).searchParams.has('fresh'), false);
    assert.deepEqual(init.next, { revalidate: 300 });
    return Response.json({ data: { product: { product_id: 'prod_One' } } });
  });
  await fetchPublicProductDetail('prod_One', new URLSearchParams({ country_code: 'CA' }));
});

test('removed products and upstream failures remain errors during fresh checks', async t => {
  for (const status of [404, 503]) {
    t.mock.method(globalThis, 'fetch', async () => new Response('Unavailable', { status }));
    await assert.rejects(fetchPublicProductDetail('missing', new URLSearchParams({ country_code: 'US' }), true), error => isPublicApiError(error, status));
    t.mock.restoreAll();
  }
});
