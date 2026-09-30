import assert from 'node:assert/strict';
import test from 'node:test';
import { BLOG_POSTS, blogHref, isBlogSlug, isBlogIndexableQuery, blogCountryDestination } from './public-blog.ts';
import { BLOG_SOURCES, blogContent } from './public-blog-content.ts';
import { getAnalyticsPage } from './google-analytics.ts';

test('only published blog slugs and clean language variants are discoverable', () => {
  for (const slug of ['__proto__', 'constructor', '', '../products', 'unknown', BLOG_POSTS[0].slug + '/more']) assert.equal(isBlogSlug(slug), false);
  for (const query of [{}, { locale: 'en' }, { locale: 'ko' }, { locale: 'ja' }]) assert.equal(isBlogIndexableQuery(query), true);
  for (const query of [{ locale: ['en', 'ko'] }, { locale: 'fr' }, { q: 'bank' }, { country_code: 'CA' }, { country_code: 'US' }, { utm_source: 'campaign' }]) assert.equal(isBlogIndexableQuery(query), false);
  assert.equal(blogHref(null, 'invalid'), '/blog');
  for (const post of BLOG_POSTS) {
    assert.ok(isBlogSlug(post.slug));
    for (const locale of ['en', 'ko', 'ja']) {
      const url = new URL(blogHref(post.slug, locale), 'https://www.switchabank.com');
      assert.equal(url.pathname, '/blog/' + post.slug);
      assert.equal(url.searchParams.get('locale'), locale === 'en' ? null : locale);
    }
  }
});

test('Canadian article country changes go to the requested market and preserve locale', () => {
  for (const path of ['/blog', '/blog/' + BLOG_POSTS[0].slug]) {
    assert.equal(blogCountryDestination(path, 'ko', 'CA'), null);
    const url = new URL(blogCountryDestination(path, 'ja', 'US')!, 'https://www.switchabank.com');
    assert.equal(url.pathname, '/products');
    assert.equal(url.searchParams.get('country_code'), 'US');
    assert.equal(url.searchParams.get('product_type'), 'savings');
    assert.equal(url.searchParams.get('locale'), 'ja');
  }
  assert.equal(blogCountryDestination('/products', 'en', 'US'), null);
});

test('article citations resolve, anchors are unique, all locales retain financial examples', () => {
  const sources = new Set<string>(BLOG_SOURCES.map(source => source.id));
  for (const post of BLOG_POSTS) {
    assert.ok(post.publishedAt <= post.modifiedAt);
    assert.match(post.sourcesCheckedAt, /^\d{4}-\d{2}-\d{2}$/);
    for (const locale of ['en', 'ko', 'ja']) {
      const article = blogContent(post.slug, locale);
      assert.equal(new Set(article.sections.map(section => section.id)).size, article.sections.length);
      for (const section of article.sections) {
        assert.ok(section.paragraphs.length);
        for (const source of section.sources ?? []) assert.ok(sources.has(source));
      }
      for (const row of article.rows) assert.ok(sources.has(row.source));
      const a = 10000 * 0.05 * 3 / 12 + 10000 * 0.01 * 9 / 12;
      const b = 10000 * 0.03;
      assert.equal(article.example.rows[0][2], `CAD ${a}`);
      assert.equal(article.example.rows[1][2], `CAD ${b}`);
      assert.ok(article.example.note.includes('CAD 100'));
      assert.ok(article.example.note.includes('APY'));
      assert.ok(article.sections.flatMap(section => section.paragraphs).some(paragraph => paragraph.includes('2,000')));
      assert.equal(article.rows.find(row => row.code === 'TD')?.fee, 'CAD 0');
    }
  }
  for (const source of BLOG_SOURCES) assert.equal(new URL(source.href).protocol, 'https:');
});

test('blog page views retain fixed screen types without article identifiers', () => {
  assert.equal(getAnalyticsPage('/blog')?.page_title, 'Blog | SwitchaBank');
  const page = getAnalyticsPage('/blog/private-title')!;
  assert.equal(page.page_location, 'https://www.switchabank.com/blog/article');
  assert.equal(JSON.stringify(page).includes('private-title'), false);
});
