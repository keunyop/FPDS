import assert from 'node:assert/strict';
import test from 'node:test';
import { BLOG_POSTS, blogHref, isBlogSlug, isBlogIndexableQuery, blogCountryDestination, blogPostsForCountry } from './public-blog.ts';
import { blogSources, blogContent } from './public-blog-content.ts';
import { getAnalyticsPage } from './google-analytics.ts';

test('only published blog slugs and clean language variants are discoverable', () => {
  for (const slug of ['__proto__', 'constructor', '', '../products', 'unknown', BLOG_POSTS[0].slug + '/more']) assert.equal(isBlogSlug(slug), false);
  for (const query of [{}, { locale: 'en' }, { locale: 'ko' }, { locale: 'ja' }]) assert.equal(isBlogIndexableQuery(query), true);
  for (const query of [{ locale: ['en', 'ko'] }, { locale: 'fr' }, { q: 'bank' }, { country_code: 'CA' }, { country_code: 'US' }, { utm_source: 'campaign' }]) assert.equal(isBlogIndexableQuery(query), false);
  assert.equal(blogHref(null, 'invalid'), '/blog');
  assert.equal(blogHref(null, 'ko', 'US'), '/blog?locale=ko&country_code=US');
  for (const post of BLOG_POSTS) {
    assert.ok(isBlogSlug(post.slug));
    for (const locale of ['en', 'ko', 'ja']) {
      const url = new URL(blogHref(post.slug, locale), 'https://www.switchabank.com');
      assert.equal(url.pathname, '/blog/' + post.slug);
      assert.equal(url.searchParams.get('country_code'), post.country === 'CA' ? null : post.country);
      assert.equal(url.searchParams.get('locale'), locale === 'en' ? null : locale);
    }
  }
});

test('country selection filters lists and keeps article switches inside the requested blog', () => {
  assert.equal(blogPostsForCountry('CA').length, 3);
  assert.equal(blogPostsForCountry('US').length, 1);
  assert.deepEqual(blogPostsForCountry('JP'), []);
  assert.deepEqual(blogPostsForCountry('us'), []);
  for (const country of ['CA', 'US', 'JP']) {
    assert.equal(blogCountryDestination('/blog', 'ko', country), null);
    assert.equal(blogCountryDestination('/products', 'en', country), null);
    for (const post of BLOG_POSTS) {
      assert.equal(blogCountryDestination('/blog/' + post.slug, 'ja', country),
        post.country === country ? null : blogHref(null, 'ja', country));
    }
  }
  assert.equal(isBlogIndexableQuery({ country_code: 'US', locale: 'ko' }, 'US'), true);
  for (const query of [{ country_code: ['US', 'CA'] }, { country_code: 'CA' }, { country_code: 'us' }, { country_code: 'US', locale: ['en', 'ko'] }, { q: 'bank' }]) {
    assert.equal(isBlogIndexableQuery(query, 'US'), false);
  }
  assert.equal(isBlogIndexableQuery({ country_code: 'JP' }, 'JP'), false);
});

test('article citations resolve, anchors are unique, all locales retain financial examples', () => {
  for (const post of BLOG_POSTS) {
    const sources = new Set<string>(blogSources(post.slug).map(source => source.id));
    assert.equal(sources.size, blogSources(post.slug).length);
    for (const source of blogSources(post.slug)) assert.equal(new URL(source.href).protocol, 'https:');
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
      if (post.productType !== 'savings' || post.country !== 'CA') continue;
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

});

test('blog page views retain fixed screen types without article identifiers', () => {
  assert.equal(getAnalyticsPage('/blog')?.page_title, 'Blog | SwitchaBank');
  const page = getAnalyticsPage('/blog/private-title')!;
  assert.equal(page.page_location, 'https://www.switchabank.com/blog/article');
  assert.equal(JSON.stringify(page).includes('private-title'), false);
});
