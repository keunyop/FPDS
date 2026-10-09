import assert from 'node:assert/strict';
import test from 'node:test';
import { blogContent, blogPresentation, blogSources } from './public-blog-content.ts';
import { blogCountryDestination } from './public-blog.ts';
const slug = 'cashable-vs-non-cashable-gic-canada';
test('GIC article preserves access, 29/30-day boundary and fictional arithmetic in every locale', () => {
  for (const locale of ['en','ko','ja']) {
    const article = blogContent(slug, locale);
    assert.equal(article.rows.length, 3);
    assert.ok(article.tableHeaders?.[1]);
    for (const row of article.rows.slice(0, 2)) { assert.match(row.detail, /29/); assert.match(row.detail, /30/); }
    assert.equal(article.example.rows[0][2], `CAD ${10000 * .03}`);
    assert.equal(article.example.rows[1][2], `CAD ${Math.round(10000 * .035)}`);
    assert.ok(article.example.note.includes('CAD 50'));
    assert.equal(blogPresentation(slug, locale).catalog, '1-year-gic');
    assert.equal(new URL(blogCountryDestination('/blog/' + slug, locale, 'US')!, 'https://example.test').pathname, '/blog');
  }
  assert.equal(blogSources(slug).length, 4);
});
