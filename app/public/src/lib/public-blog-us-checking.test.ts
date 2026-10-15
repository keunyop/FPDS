import assert from 'node:assert/strict';
import test from 'node:test';
import { blogContent, blogPresentation, blogSources, blogCatalogHref } from './public-blog-content.ts';
import { BLOG_POSTS, blogHref, blogPostsForCountry } from './public-blog.ts';
import { resolvePublicBankLogo } from './public-bank-logo.ts';

const slug = 'chase-vs-bank-of-america-vs-wells-fargo-checking-fees';
const locales = ['en', 'ko', 'ja'] as const;

test('US checking article keeps base fees separate from conditional waivers, single-deposit boundaries and ATM surcharges', () => {
  for (const locale of locales) {
    const content = blogContent(slug, locale);
    assert.deepEqual(content.rows.map(row => row.fee), ['USD 15', 'USD 12', 'USD 15']);
    assert.match(content.rows[0].detail, /USD 500/);
    assert.match(content.rows[1].detail, locale === 'en' ? /At least one.*USD 250.*each statement cycle/ : locale === 'ko' ? /매 명세 주기.*건당 USD 250.*최소 1회/ : /各明細サイクル.*1回USD 250.*最低1回/);
    assert.match(content.rows[2].detail, /USD 500/);
    const deposits = content.sections.find(section => section.id === 'qualifying-deposits')!.paragraphs.join(' ');
    assert.match(deposits, locale === 'en' ? /two USD 125 deposits do not satisfy/ : locale === 'ko' ? /USD 125씩 두 번으로는.*충족하지 못합니다/ : /USD 125を2回では.*満たしません/);
    assert.match(deposits, /Zelle/);
    const atm = content.sections.find(section => section.id === 'atm-costs')!.paragraphs.join(' ');
    assert.match(atm, /USD 2.50/);
    assert.match(atm, locale === 'en' ? /operator may charge extra/ : locale === 'ko' ? /운영자 수수료는 별도로/ : /運営者の手数料が加わる/);
    assert.match(atm, /overdraft/);
    for (const row of content.rows) assert.ok(resolvePublicBankLogo(row.code, row.bank).asset);
    assert.doesNotMatch(JSON.stringify(content), /CAD|Canadian|캐나다|カナダ/);
  }
});

test('checking fee infographic illustrates twelve charged periods and never promises a first-year or all-in price', () => {
  const costs = [15, 12, 15].map(monthly => monthly * 12);
  for (const locale of locales) {
    const content = blogContent(slug, locale);
    assert.equal(content.infographic?.steps.length, 3);
    assert.deepEqual(content.example.chart?.values, costs);
    assert.deepEqual(content.example.rows.map(row => row[2]), costs.map(value => `USD ${value}`));
    assert.match(content.example.chart!.difference, /USD 36/);
    assert.match(content.example.note, locale === 'en' ? /no waivers or introductory relief.*not a first-year quote.*Excludes ATM, overdraft/ : locale === 'ko' ? /면제나 초기 유예가 없다고 가정.*첫해 비용 견적은 아니며.*ATM·overdraft/ : /免除や当初の猶予がない仮定.*初年度の見積もりではなく.*ATM・overdraft/);
  }
});

test('US checking discovery and catalog preserve country, locale and Filipino editorial fallback', () => {
  assert.equal(BLOG_POSTS.find(post => post.slug === slug)?.country, 'US');
  assert.equal(blogPostsForCountry('US').some(post => post.slug === slug), true);
  assert.equal(blogPostsForCountry('CA').some(post => post.slug === slug), false);
  assert.equal(blogSources(slug).length, 5);
  assert.equal(blogContent(slug, 'fil'), blogContent(slug, 'en'));
  for (const locale of [...locales, 'fil']) {
    const presentation = blogPresentation(slug, locale);
    const url = new URL(blogCatalogHref(slug, locale), 'https://example.test');
    assert.equal(url.searchParams.get('product_type'), 'chequing');
    assert.equal(url.searchParams.get('country_code'), 'US');
    assert.equal(url.searchParams.get('locale'), locale === 'en' ? null : locale);
    assert.equal(url.searchParams.get('sort_by'), 'monthly_fee');
    assert.equal(presentation.guides.length, 0);
    assert.equal(presentation.relatedArticle?.slug, 'ally-vs-capital-one-vs-amex-high-yield-savings');
    assert.equal(new URL(blogHref(slug, locale), 'https://example.test').searchParams.get('country_code'), 'US');
  }
});
