import assert from 'node:assert/strict';
import test from 'node:test';
import { blogContent, blogPresentation, blogSources } from './public-blog-content.ts';
import { BLOG_POSTS, blogHref } from './public-blog.ts';
const slug = 'ally-vs-capital-one-vs-amex-high-yield-savings';

test('US article keeps verified access boundaries and APY arithmetic across all locales', () => {
  assert.equal(BLOG_POSTS.find(post => post.slug === slug)?.country, 'US');
  assert.equal(blogSources(slug).length, 4);
  for (const locale of ['en', 'ko', 'ja']) {
    const content = blogContent(slug, locale);
    assert.deepEqual(content.rows.map(row => row.fee), ['USD 0', 'USD 0', 'USD 0']);
    assert.match(content.rows[0].detail, /10/);
    assert.match(content.rows[0].detail, locale === 'en' ? /closure/ : locale === 'ko' ? /해지/ : /閉鎖/);
    assert.match(content.rows[1].detail, /ATM/);
    assert.match(content.rows[2].detail, /ATM/);
    assert.deepEqual(content.example.rows.map(row => row[2]), [3, 4].map(apy => `USD ${10000 * apy / 100}`));
    assert.deepEqual(content.example.chart?.values, [300, 400]);
    assert.match(content.example.chart!.difference, /USD 100/);
    assert.match(content.example.note, /APY/);
    assert.match(content.example.note, locale === 'en' ? /Hypothetical.*unchanged.*no fees or tax/ : locale === 'ko' ? /가상.*일정.*수수료·세금/ : /仮定.*一定.*手数料・税金/);
    assert.equal(content.infographic?.steps.length, 3);
    assert.equal(blogPresentation(slug, locale).guides.length, 0);
    assert.equal(blogPresentation(slug, locale).relatedArticle, null);
    assert.equal(new URL(blogHref(slug, locale), 'https://example.test').searchParams.get('country_code'), 'US');
    const body = content.sections.flatMap(section => section.paragraphs).join(' ');
    assert.doesNotMatch(body, /CAD|Canadian|カナダ|캐나다/);
    assert.match(body, /APY/);
  }
});
