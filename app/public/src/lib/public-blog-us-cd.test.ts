import assert from 'node:assert/strict';
import test from 'node:test';
import { blogContent, blogPresentation, blogSources } from './public-blog-content.ts';
import { BLOG_POSTS, blogHref, blogPostsForCountry } from './public-blog.ts';
import { curatedCatalogHref } from './public-curated.ts';

const slug = 'high-yield-savings-vs-cds-us';
const locales = ['en', 'ko', 'ja'] as const;

test('US CD comparison retains the one-year penalty boundary and no-penalty waiting/full-balance conditions in all locales', () => {
  for (const locale of locales) {
    const content = blogContent(slug, locale);
    assert.match(content.rows[0].fee, locale === 'en' ? /Variable/ : locale === 'ko' ? /변동/ : /変動/);
    assert.match(content.rows[0].detail, /ATM/);
    assert.match(content.rows[1].detail, /USD 500/);
    assert.match(content.rows[1].detail, locale === 'en' ? /before maturity.*penalty/ : locale === 'ko' ? /만기 전.*위약금/ : /満期前.*違約金/);
    assert.match(content.rows[2].detail, /11/);
    assert.match(content.rows[2].detail, locale === 'en' ? /full balance and interest.*after the first 6 days following funding/ : locale === 'ko' ? /입금일 이후 첫 6일이 지난 뒤 원금 전액과 이자/ : /入金日.*6日間が経過した後、残高全額と利息/);
    const penalty = content.sections.find(section => section.id === 'worked-example')!;
    assert.match(penalty.paragraphs.join(' '), locale === 'en' ? /90 days.*up to and including one year, 180 days.*over one through five years.*270 days.*over five years/ : locale === 'ko' ? /1년 이하면 90일분, 1년 초과~5년 이하면 180일분, 5년 초과면 270일분/ : /1年以下なら90日分、1年超〜5年以下なら180日分、5年超なら270日分/);
    assert.equal(content.infographic?.steps.length, 3);
    assert.doesNotMatch(JSON.stringify(content), /CAD|Canadian|캐나다|カナダ/);
  }
});

test('penalty infographic uses annual interest, original principal and explicit 365/366-day assumptions rather than APY earnings', () => {
  const penalties = [90, 180].map(days => Math.round(10000 * 0.04 / 365 * days * 100) / 100);
  assert.deepEqual(penalties, [98.63, 197.26]);
  for (const locale of locales) {
    const example = blogContent(slug, locale).example;
    assert.deepEqual(example.chart?.values, penalties);
    assert.deepEqual(example.rows.map(row => row[2]), penalties.map(value => `USD ${value.toFixed(2)}`));
    assert.match(example.chart!.difference, /\+USD 98.63/);
    assert.match(example.note, /4.00%/);
    assert.match(example.note, /APY/);
    assert.match(example.note, /365/);
    assert.match(example.note, /366/);
    assert.match(example.note, locale === 'en' ? /not APY or a current Marcus quote/ : locale === 'ko' ? /APY나 Marcus의 현재 제안이 아닙니다/ : /APYやMarcusの現在の提示金利ではありません/);
    assert.match(example.intro, locale === 'en' ? /penalties, not earnings/ : locale === 'ko' ? /수익이 아닌 위약금/ : /収益ではなく違約金/);
  }
});

test('US CD article is discoverable only in its native market with matching localized catalog links', () => {
  assert.equal(BLOG_POSTS.find(post => post.slug === slug)?.country, 'US');
  assert.equal(blogPostsForCountry('US').some(post => post.slug === slug), true);
  assert.equal(blogPostsForCountry('CA').some(post => post.slug === slug), false);
  assert.equal(blogSources(slug).length, 4);
  for (const locale of locales) {
    const presentation = blogPresentation(slug, locale);
    const href = blogHref(slug, locale);
    assert.equal(new URL(href, 'https://example.test').searchParams.get('country_code'), 'US');
    const catalog = new URL(curatedCatalogHref(presentation.catalog, locale, 'US'), 'https://example.test');
    assert.equal(catalog.searchParams.get('product_type'), 'gic');
    assert.equal(catalog.searchParams.get('country_code'), 'US');
    assert.equal(presentation.guides.length, 0);
    assert.equal(presentation.relatedArticle?.slug, 'ally-vs-capital-one-vs-amex-high-yield-savings');
  }
});
