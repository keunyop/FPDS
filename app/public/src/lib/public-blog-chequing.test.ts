import assert from 'node:assert/strict';
import test from 'node:test';
import { readFileSync } from 'node:fs';
import { BLOG_POSTS } from './public-blog.ts';
import { blogContent, blogPresentation, blogSources } from './public-blog-content.ts';
import { curatedCatalogHref } from './public-curated.ts';

const slug = 'tangerine-vs-simplii-vs-cibc-chequing-fees';

test('new chequing article retains base fee, complete balance condition and separate hypothetical costs in all languages', () => {
  for (const locale of ['en', 'ko', 'ja']) {
    const content = blogContent(slug, locale);
    assert.deepEqual(content.rows.map(row => row.fee), ['CAD 0', 'CAD 0', 'CAD 16.95']);
    const cibc = content.rows.find(row => row.code === 'CIBC')!;
    assert.ok(cibc.name.includes('Tier 1'));
    assert.ok(cibc.detail.includes('4,000'));
    assert.match(cibc.detail, locale === 'en' ? /each day of the month.*up to three/ : locale === 'ko' ? /그 달 매일 마감.*최대 세/ : /その月の毎日の終業時.*最大3/);
    assert.deepEqual(content.example.rows.map(row => row[2]), [
      'CAD ' + (16.95 * 12).toFixed(2), 'CAD ' + (16.95 * 3).toFixed(2), 'CAD ' + (4000 * 0.03)
    ]);
    assert.ok(content.example.note.includes('3%'));
    assert.ok(content.example.note.includes('APY'));
    assert.match(content.example.note, locale === 'en' ? /not added together/ : locale === 'ko' ? /합산하지/ : /合算しません/);
    assert.match(content.example.note, locale === 'en' ? /hypothetical/ : locale === 'ko' ? /가정/ : /仮定/);
    assert.equal(content.faq.length, 4);
  }
});

test('chequing calls to action preserve language, the proper product type and related savings article', () => {
  for (const locale of ['en', 'ko', 'ja']) {
    const presentation = blogPresentation(slug, locale);
    const url = new URL(curatedCatalogHref(presentation.catalog, locale), 'https://www.switchabank.com');
    assert.equal(url.searchParams.get('product_type'), 'chequing');
    assert.equal(url.searchParams.get('sort_by'), 'monthly_fee');
    assert.equal(url.searchParams.get('locale'), locale === 'en' ? null : locale);
    assert.equal(presentation.relatedArticle?.slug, 'eq-bank-vs-tangerine-vs-td-savings');
    assert.ok(presentation.compareBody.includes('SwitchaBank'));
    assert.equal(blogPresentation('eq-bank-vs-tangerine-vs-td-savings', locale).catalog, 'savings-accounts');
    assert.ok(blogSources(slug).some(source => source.id === 'cibc-smart'));
    assert.ok(!blogSources('eq-bank-vs-tangerine-vs-td-savings').some(source => source.id === 'cibc-smart'));
  }
});

test('registry, route allowlist and dates remain consistent without resetting the older article', () => {
  const manifest = JSON.parse(readFileSync(new URL('../../routes.manifest.json', import.meta.url), 'utf8'));
  const route = manifest.routes.find((item: { route: string }) => item.route === '/blog/[slug]');
  assert.deepEqual(new Set(route.allowed_slugs), new Set(BLOG_POSTS.map(post => post.slug)));
  assert.equal(BLOG_POSTS.find(post => post.slug === slug)?.publishedAt, '2026-10-05');
  assert.deepEqual(BLOG_POSTS.map(post => post.publishedAt), BLOG_POSTS.map(post => post.publishedAt).sort().reverse());
  assert.equal(BLOG_POSTS.find(post => post.productType === 'savings')?.sourcesCheckedAt, '2026-09-30');
});
