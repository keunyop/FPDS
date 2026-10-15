import assert from 'node:assert/strict';
import test from 'node:test';
import { blogContent, blogSources, blogPresentation, blogCatalogHref } from './public-blog-content.ts';
import { BLOG_POSTS, blogPostsForCountry } from './public-blog.ts';
const ca = 'credit-card-cashback-welcome-bonuses-canada';
const us = 'credit-card-cashback-welcome-bonuses-us';
const locales = ['en', 'ko', 'ja'] as const;

test('Canadian card example preserves two versus conditional three categories and all welcome deadlines', () => {
  assert.equal(blogSources(ca).length, 2);
  for (const locale of locales) {
    const content = blogContent(ca, locale);
    assert.equal(content.rows[0].fee, 'CAD 0');
    assert.match(content.rows[0].detail, /2%/);
    assert.match(content.rows[0].detail, /0.5%/);
    assert.match(content.rows[0].detail, /Tangerine Savings Account/);
    const offer = content.sections.find(section => section.id === 'welcome-offer')!.paragraphs.join(' ');
    for (const boundary of [/45/, /60/, /2026/, /30/, /CAD 1,000/, /CAD 100/, /10%/]) assert.match(offer, boundary);
    assert.match(offer, locale === 'en' ? /on top of regular rewards/ : locale === 'ko' ? /기본 적립에 더해지는/ : /通常還元に加わる/);
    assert.match(offer, locale === 'en' ? /open and in good standing.*1–2 statement cycles/ : locale === 'ko' ? /열려 있고 정상 상태.*1~2주기/ : /開設中で正常.*1〜2サイクル/);
    assert.doesNotMatch(JSON.stringify(content), /USD|CFPB/);
  }
});

test('US offer keeps months, prior-holder limits, cash-value points and specific prepaid exclusions', () => {
  assert.equal(blogSources(us).length, 3);
  for (const locale of locales) {
    const content = blogContent(us, locale);
    assert.deepEqual(content.rows.map(row => row.fee), ['USD 0', 'USD 0']);
    assert.match(content.rows[0].detail, /1.5%/);
    assert.match(content.rows[1].detail, /2%/);
    const offer = content.sections.find(section => section.id === 'welcome-offer')!.paragraphs.join(' ');
    for (const boundary of [/20,000/, /USD 200/, /USD 500/, /24/, /6[–~〜]8/]) assert.match(offer, boundary);
    assert.match(offer, locale === 'en' ? /first 3 months from account opening/ : locale === 'ko' ? /계좌 개설 후 첫 3개월/ : /開設後最初の3か月/);
    assert.match(offer, locale === 'en' ? /current holders.*previous holders/ : locale === 'ko' ? /현재.*보유자.*과거 보유자/ : /現在.*会員.*元会員/);
    const exclusions = content.sections.find(section => section.id === 'excluded-spending')!.paragraphs.join(' ');
    assert.match(exclusions, locale === 'en' ? /Wells Fargo Active Cash explicitly excludes pre-paid gift cards/ : locale === 'ko' ? /Wells Fargo Active Cash는 선불 상품권.*명시적으로 제외/ : /Wells Fargo Active Cashはプリペイドギフトカード.*明示的に除外/);
    assert.doesNotMatch(JSON.stringify(content), /CAD|FCAC/);
  }
});

test('reward charts count a separate one-time bonus once and disclose hypothetical rates and zero costs', () => {
  for (const [slug, currency, bonus] of [[ca, 'CAD', 100], [us, 'USD', 200]] as const) {
    for (const locale of locales) {
      const content = blogContent(slug, locale);
      assert.deepEqual(content.example.chart?.values, [12000 * 0.02 + bonus, 12000 * 0.02]);
      assert.deepEqual(content.example.rows.map(row => row[2]), [`${currency} ${240 + bonus}`, `${currency} 240`]);
      assert.match(content.example.note, locale === 'en' ? /not either card’s quoted return.*zero annual fee, interest.*only once/ : locale === 'ko' ? /위 카드의 수익 견적이 아닙니다.*연회비·이자·기타 비용 0.*한 번만/ : /上記カードの還元見積もりではありません.*年会費・利息・その他費用ゼロ.*一度だけ/);
      assert.equal(content.infographic?.steps.length, 3);
      assert.equal(new URL(content.inspiration!.href).hostname, 'www.banksalad.com');
      assert.ok(!blogSources(slug).some(source => source.href.includes('banksalad')));
    }
  }
});

test('card articles use the native /cards catalog in every UI locale while deposit links remain unchanged', () => {
  for (const [slug, country] of [[ca, 'CA'], [us, 'US']] as const) {
    assert.equal(BLOG_POSTS.find(post => post.slug === slug)?.productType, 'credit_card');
    assert.ok(blogPostsForCountry(country).some(post => post.slug === slug));
    assert.ok(!blogPostsForCountry(country === 'CA' ? 'US' : 'CA').some(post => post.slug === slug));
    for (const locale of [...locales, 'fil', 'invalid']) {
      const url = new URL(blogCatalogHref(slug, locale), 'https://example.test');
      assert.equal(url.pathname, '/cards');
      assert.equal(url.searchParams.get('country_code'), country === 'CA' ? null : 'US');
      assert.equal(url.searchParams.get('locale'), ['ko', 'ja', 'fil'].includes(locale) ? locale : null);
      assert.equal(url.searchParams.get('product_type'), null);
      assert.equal(blogPresentation(slug, locale).guides.length, 0);
    }
    assert.equal(blogContent(slug, 'fil'), blogContent(slug, 'en'));
  }
  assert.equal(blogCatalogHref('eq-bank-vs-tangerine-vs-td-savings', 'ko'), '/products?product_type=savings&locale=ko');
  assert.equal(blogCatalogHref('high-yield-savings-vs-cds-us', 'ja'), '/products?product_type=gic&locale=ja&country_code=US');
});
