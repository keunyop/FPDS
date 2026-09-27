import assert from 'node:assert/strict';
import test from 'node:test';
import { GUIDE_SLUGS, GUIDE_COMPARISONS, GUIDE_REVIEWED_AT, guideCopy, guideHref, guideCountryDestination, isGuideSlug, isGuideIndexableQuery } from './public-guides.ts';
import { GUIDE_SOURCES, guideContent } from './public-guide-content.ts';
import { isIndexableProductLocale } from './public-url-policy.ts';

test('guides are an exact bounded allowlist with safe localized URLs', () => {
  assert.equal(GUIDE_SLUGS.length, 4);
  for (const slug of GUIDE_SLUGS) {
    assert.equal(isGuideSlug(slug), true);
    for (const locale of ['en', 'ko', 'ja']) {
      const url = new URL(guideHref(slug, locale), 'https://www.switchabank.com');
      assert.equal(url.pathname, `/guides/${slug}`);
      assert.equal(url.searchParams.get('locale'), locale === 'en' ? null : locale);
      assert.equal(url.searchParams.has('country_code'), false);
    }
  }
  for (const slug of ['__proto__', 'constructor', '', 'unknown', 'monthly-fee-waivers/more', '../products']) assert.equal(isGuideSlug(slug), false);
  assert.equal(guideHref(null, 'not-a-locale'), '/guides');
});
test('only authored locale variants are indexable; filters and duplicate query values are not', () => {
  for (const query of [{}, { locale: 'en' }, { locale: 'ko' }, { locale: 'ja' }]) assert.equal(isGuideIndexableQuery(query), true);
  for (const query of [{ locale: 'fr' }, { locale: ['en','ko'] }, { country_code: 'US' }, { country_code: 'CA' }, { q: 'bank' }, { utm_source: 'test' }]) assert.equal(isGuideIndexableQuery(query), false);
  assert.equal(isIndexableProductLocale('ko'), false);
  assert.equal(isIndexableProductLocale('ja'), false);
});
test('changing country leaves Canada-only guidance and preserves the relevant product type and locale', () => {
  for (const locale of ['en', 'ko', 'ja']) {
    for (const slug of GUIDE_SLUGS) {
      const path = `/guides/${slug}`;
      assert.equal(guideCountryDestination(path, locale, 'CA'), null);
      const url = new URL(guideCountryDestination(path, locale, 'US')!, 'https://www.switchabank.com');
      assert.equal(url.pathname, '/products');
      assert.equal(url.searchParams.get('country_code'), 'US');
      assert.equal(url.searchParams.get('locale'), locale === 'en' ? null : locale);
      assert.equal(url.searchParams.get('product_type'), slug === 'base-and-promotional-rates' ? 'savings' : slug === 'gic-maturity-and-withdrawals' ? 'gic' : 'chequing');
    }
  }
  assert.equal(guideCountryDestination('/products', 'ko', 'US'), null);
  assert.equal(guideCountryDestination('/guides', 'ja', 'US'), '/products?country_code=US&locale=ja');
});
test('each original localized guide has complete sourced content and an existing comparison destination', () => {
  assert.match(GUIDE_REVIEWED_AT, /^\d{4}-\d{2}-\d{2}$/);
  for (const slug of GUIDE_SLUGS) {
    assert.ok(['savings-accounts', 'no-monthly-fee-chequing', '1-year-gic'].includes(GUIDE_COMPARISONS[slug]));
    assert.ok(GUIDE_SOURCES[slug].length);
    for (const source of GUIDE_SOURCES[slug]) {
      const url = new URL(source.href);
      assert.equal(url.protocol, 'https:');
      assert.equal(url.hostname, 'www.canada.ca');
      assert.ok(source.title.startsWith('FCAC'));
    }
    for (const locale of ['en','ko','ja']) {
      const content = guideContent(slug, locale);
      assert.equal(content.sections.length, 3);
      for (const text of [content.intro, content.comparison, guideCopy(locale).topics[slug], ...content.sections.flatMap(section => [section.title, section.body])]) assert.ok(text.trim());
      if (locale !== 'en') assert.notEqual(content.intro, guideContent(slug, 'en').intro);
      assert.ok(guideCopy(locale).method.includes('AI'));
      assert.ok(guideCopy(locale).publisher.includes('SwitchaBank'));
    }
  }
  assert.equal(guideContent('monthly-fee-waivers', 'fr'), guideContent('monthly-fee-waivers', 'en'));
});
