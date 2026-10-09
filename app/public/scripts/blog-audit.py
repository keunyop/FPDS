"""Verify authored blog routes against a local production build.
Run: uv run --with playwright python app/public/scripts/blog-audit.py
Set FPDS_UI_TEST_ORIGIN to override localhost:3000. External calls and writes are blocked.
"""
import json
import os
import struct
from pathlib import Path
from urllib.parse import urlparse, urljoin
import xml.etree.ElementTree as ET
from playwright.sync_api import expect, sync_playwright

ORIGIN = os.environ.get('FPDS_UI_TEST_ORIGIN', 'http://localhost:3000').rstrip('/')
assert urlparse(ORIGIN).hostname in {'localhost', '127.0.0.1', '::1'}
PROD = 'https://www.switchabank.com'
POSTS = {
    'ally-vs-capital-one-vs-amex-high-yield-savings': {
        'country': 'US', 'date': '2026-10-09', 'citations': 4,
        'catalog': '/products?product_type=savings', 'tail': '&country_code=US',
        'related': None, 'amounts': ['USD 300', 'USD 400', 'USD 100'],
    },
    'cashable-vs-non-cashable-gic-canada': {
        'date': '2026-10-08', 'citations': 4,
        'catalog': '/products?product_type=gic', 'tail': '',
        'related': 'eq-bank-vs-tangerine-vs-td-savings',
        'amounts': ['CAD 300', 'CAD 350', 'CAD 50'],
    },
    'tangerine-vs-simplii-vs-cibc-chequing-fees': {
        'date': '2026-10-05', 'citations': 8,
        'catalog': '/products?product_type=chequing',
        'tail': '&sort_by=monthly_fee&sort_order=asc',
        'related': 'eq-bank-vs-tangerine-vs-td-savings',
        'amounts': ['CAD 203.40', 'CAD 50.85', 'CAD 120'],
    },
    'eq-bank-vs-tangerine-vs-td-savings': {
        'date': '2026-09-30', 'citations': 4,
        'catalog': '/products?product_type=savings', 'tail': '',
        'related': 'tangerine-vs-simplii-vs-cibc-chequing-fees',
        'amounts': ['CAD 200', 'CAD 300'],
    },
}
PATHS = ['/blog', *['/blog/' + slug for slug in POSTS]]
CASES = [('/blog', 'CA'), ('/blog', 'US'), *[('/blog/' + slug, post.get('country', 'CA')) for slug, post in POSTS.items()]]
def suffix_for(locale, country):
    params = []
    if locale != 'en':
        params.append('locale=' + locale)
    if country != 'CA':
        params.append('country_code=' + country)
    return '?' + '&'.join(params) if params else ''
checks, errors = [], []
screens = Path('tmp/blog-audit')
screens.mkdir(parents=True, exist_ok=True)

def passed(name):
    checks.append(name)
    print('PASS', name, flush=True)

def intercept(route):
    if route.request.url.startswith(ORIGIN + '/api/public/countries'):
        route.fulfill(status=200, content_type='application/json', body=json.dumps({'data': {'countries': [{'code': 'CA', 'count': 3}, {'code': 'US', 'count': 1}]}}))
    elif not route.request.url.startswith(ORIGIN + '/') or route.request.method not in {'GET', 'HEAD'}:
        route.fulfill(status=200, content_type='application/json', body='{}')
    else:
        route.continue_()

def catalog(post, locale):
    return post['catalog'] + ('' if locale == 'en' else '&locale=' + locale) + post['tail']

with sync_playwright() as pw:
    browser = pw.chromium.launch(channel='chrome', headless=True)
    context = browser.new_context(reduced_motion='reduce')
    context.route('**/*', intercept)
    page = context.new_page()
    page.on('pageerror', lambda e: errors.append(str(e)))
    for locale in ['en', 'ko', 'ja']:
        suffix = '' if locale == 'en' else '?locale=' + locale
        for width in [390, 768, 1440]:
            page.set_viewport_size({'width': width, 'height': 900})
            for path, country in CASES:
                suffix = suffix_for(locale, country)
                response = page.goto(ORIGIN + path + suffix, wait_until='networkidle')
                assert response.status == 200
                expect(page.locator('html')).to_have_attribute('lang', locale)
                expect(page.locator('main h1')).to_have_count(1)
                assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
                assert chr(65533) not in page.locator('main').inner_text()
                expect(page.locator('link[rel=canonical]')).to_have_attribute('href', PROD + path + suffix)
                assert 'noindex' not in page.locator('meta[name=robots]').get_attribute('content')
                alternates = {a.get_attribute('hreflang'): a.get_attribute('href') for a in page.locator('link[rel=alternate][hreflang]').all()}
                assert alternates == {('en-US' if country == 'US' else 'en-CA'): PROD + path + suffix_for('en', country), 'ko': PROD + path + suffix_for('ko', country), 'ja': PROD + path + suffix_for('ja', country), 'x-default': PROD + path + suffix_for('en', country)}
                assert page.locator('meta[name=description]').get_attribute('content')
                for img in page.locator('main img').all():
                    img.scroll_into_view_if_needed()
                    expect(img).to_be_visible()
                    assert img.evaluate('(img) => img.complete && img.naturalWidth > 0')
                if path != '/blog':
                    slug = path.rsplit('/', 1)[1]
                    post = POSTS[slug]
                    graph = [json.loads(text) for text in page.locator('script[type="application/ld+json"]').all_text_contents()]
                    article = next(node for entry in graph for node in entry.get('@graph', []) if node.get('@type') == 'BlogPosting')
                    assert article['headline'] == page.locator('h1').inner_text()
                    assert article['url'] == PROD + path + suffix
                    assert article['datePublished'] == article['dateModified'] == post['date']
                    assert len(article['citation']) == post['citations']
                    assert article['image'] == [PROD + path + '/opengraph-image']
                    assert page.locator('#article-sources li').count() == post['citations']
                    for source in page.locator('#article-sources a').all():
                        assert source.get_attribute('href') in article['citation']
                    expect(page.locator('meta[property="og:type"]')).to_have_attribute('content', 'article')
                    expect(page.locator('meta[property="og:image"]').first).to_have_attribute('content', PROD + path + '/opengraph-image')
                    assert page.locator('table tbody tr').count() == 3
                    for amount in post['amounts']:
                        assert amount in page.locator('#worked-example').inner_text()
                    expect(page.locator('[data-blog-comparison]')).to_have_attribute('href', catalog(post, locale))
                    if post['related']:
                        expect(page.locator('[data-blog-related]')).to_have_attribute('href', '/blog/' + post['related'] + suffix)
                    else:
                        expect(page.locator('[data-blog-related]')).to_have_count(0)
                    if country == 'US':
                        expect(page.locator('[data-blog-infographic]')).to_be_visible()
                        expect(page.locator('[data-blog-yield-chart]')).to_be_visible()
                        assert page.locator('[data-blog-infographic] li').count() == 3
                        assert 'CAD' not in page.locator('main').inner_text()
                        assert 'en_CA' not in [item.get_attribute('content') for item in page.locator('meta[property="og:locale:alternate"]').all()]
                        expect(page.locator('meta[property="og:locale"]')).to_have_attribute('content', 'en_US' if locale == 'en' else 'ko_KR' if locale == 'ko' else 'ja_JP')
                    if 'chequing' in slug:
                        expect(page.locator('[data-blog-shortlist]')).to_have_attribute('href', catalog(post, locale))
                        assert 'Tier 1' in page.locator('table').inner_text()
                    page.locator('a[href="#worked-example"]').click()
                    expect(page).to_have_url(ORIGIN + path + suffix + '#worked-example')
                    page.wait_for_timeout(200)
                    assert page.locator('#worked-example').bounding_box()['y'] >= 64
                    page.locator('main h1').scroll_into_view_if_needed()
                else:
                    matching = [slug for slug, post in POSTS.items() if post.get('country', 'CA') == country]
                    assert page.locator('main article').count() == len(matching)
                    assert [a.get_attribute('href') for a in page.locator('main article h3 a').all()] == ['/blog/' + slug + suffix for slug in matching]
                    graph = [json.loads(text) for text in page.locator('script[type="application/ld+json"]').all_text_contents()]
                    listing = next(node for node in graph if node.get('@type') == 'CollectionPage')
                    assert len(listing['mainEntity']['itemListElement']) == len(matching)
                    assert [item['url'] for item in listing['mainEntity']['itemListElement']] == [PROD + '/blog/' + slug + suffix for slug in matching]
                if width < 1024:
                    menu = page.locator('header button[aria-haspopup=menu]:visible')
                    menu.click()
                    blog = page.get_by_role('menu').locator('a[aria-current="page"][href="/blog' + suffix + '"]')
                    expect(blog).to_have_attribute('aria-current', 'page')
                    page.keyboard.press('Escape')
                    expect(menu).to_be_focused()
                else:
                    expect(page.locator('header nav a[href="/blog' + suffix + '"]')).to_have_attribute('aria-current', 'page')
                    assert page.get_by_role('banner').evaluate('(el) => el.scrollWidth <= innerWidth')
                page.evaluate('window.scrollTo(0, 0)')
                if locale == 'ko':
                    name = ('index-' + country) if path == '/blog' else 'us-savings' if country == 'US' else ('gic' if 'gic-canada' in path else 'chequing' if 'chequing' in path else 'savings')
                    page.screenshot(path=str(screens / (name + '-' + str(width) + '.png')), full_page=True)
                    if name == 'chequing' and width in [390, 1440]:
                        page.screenshot(path=str(screens / (name + '-hero-' + str(width) + '.png')))
                        page.locator('#account-comparison').screenshot(path=str(screens / (name + '-table-' + str(width) + '.png')))
                expect(page.locator('footer a[href="/blog' + suffix + '"]')).to_have_count(1)
                passed(f'{path} {country} {locale} {width}')

    for path in ['/blog/unknown', '/blog/constructor', '/blog/unknown/opengraph-image',
                 *['/blog/' + slug + '/extra' for slug in POSTS]]:
        assert context.request.get(ORIGIN + path).status == 404
        passed('404 ' + path)
    for slug, post in POSTS.items():
        country = post.get('country', 'CA')
        for query in ['locale=fr', 'locale=ko&locale=ja', 'q=bank', 'utm_source=test', 'country_code=CA' if country == 'CA' else 'country_code=US&country_code=US']:
            query = ('country_code=US&' if country == 'US' and not query.startswith('country_code=') else '') + query
            page.goto(ORIGIN + '/blog/' + slug + '?' + query, wait_until='domcontentloaded')
            assert 'noindex' in page.locator('meta[name=robots]').get_attribute('content')
            passed('noindex ' + slug + '?' + query)
        other = 'US' if country == 'CA' else 'CA'
        response = context.request.get(ORIGIN + '/blog/' + slug + '?country_code=' + other + '&locale=ko', max_redirects=0)
        assert response.status == 308
        assert urljoin(ORIGIN, response.headers['location']) == ORIGIN + '/blog' + suffix_for('ko', other)
        passed('cross-country article returns to selected blog ' + slug)
        if country == 'US':
            response = context.request.get(ORIGIN + '/blog/' + slug, max_redirects=0)
            assert response.status == 308
            assert urljoin(ORIGIN, response.headers['location']) == ORIGIN + '/blog/' + slug + '?country_code=US'
            passed('bare US article resolves its native country')
    for locale in ['en', 'ko', 'ja']:
        page.goto(ORIGIN + '/blog' + suffix_for(locale, 'JP'), wait_until='networkidle')
        expect(page.locator('main h1')).to_be_visible()
        expect(page.locator('main article')).to_have_count(0)
        assert 'noindex' in page.locator('meta[name=robots]').get_attribute('content')
        passed('localized empty blog ' + locale)
    # Exercise the actual header controls in both desktop and mobile layouts.
    for width in [390, 1440]:
        page.set_viewport_size({'width': width, 'height': 900})
        page.goto(ORIGIN + '/blog/ally-vs-capital-one-vs-amex-high-yield-savings?locale=ko&country_code=US', wait_until='networkidle')
        page.locator('header button[aria-haspopup=menu]:visible').click()
        page.get_by_role('menu').locator('a[href="/blog?locale=ko"]').click()
        expect(page).to_have_url(ORIGIN + '/blog?locale=ko')
        expect(page.locator('main article')).to_have_count(3)
        page.locator('header button[aria-haspopup=menu]:visible').click()
        page.get_by_role('menu').locator('a[href="/blog?locale=ko&country_code=US"]').click()
        expect(page).to_have_url(ORIGIN + '/blog?locale=ko&country_code=US')
        expect(page.locator('main article')).to_have_count(1)
        page.locator('footer button[aria-haspopup=menu]').click()
        page.get_by_role('menu').locator('a[href="/blog?country_code=US"]').click()
        expect(page).to_have_url(ORIGIN + '/blog?country_code=US')
        expect(page.locator('html')).to_have_attribute('lang', 'en')
        passed('country and locale controls ' + str(width))
    previews = []
    for path in PATHS:
        response = context.request.get(ORIGIN + path + '/opengraph-image')
        assert response.status == 200 and response.headers['content-type'].startswith('image/png')
        body = response.body()
        assert body[:8] == bytes([137, 80, 78, 71, 13, 10, 26, 10])
        assert struct.unpack('>II', body[16:24]) == (1200, 630)
        previews.append(body)
        passed('social preview PNG ' + path)
    assert len(set(previews)) == len(PATHS)
    sitemap = ET.fromstring(context.request.get(ORIGIN + '/sitemap.xml').text())
    ns = {'s': 'http://www.sitemaps.org/schemas/sitemap/0.9', 'x': 'http://www.w3.org/1999/xhtml'}
    entries = [entry for entry in sitemap.findall('s:url', ns) if '/blog' in entry.find('s:loc', ns).text]
    expected = {PROD + path + suffix_for(locale, country) for path, country in CASES for locale in ['en', 'ko', 'ja']}
    assert {entry.find('s:loc', ns).text for entry in entries} == expected
    for entry in entries:
        url = entry.find('s:loc', ns).text
        old = 'eq-bank-vs-tangerine-vs-td-savings' in url
        assert entry.find('s:lastmod', ns).text == ('2026-09-30' if old else '2026-10-05' if 'chequing-fees' in url else '2026-10-09' if 'country_code=US' in url else '2026-10-08')
        assert len(entry.findall('x:link', ns)) == 4
    passed('eighteen country-scoped sitemap URLs, explicit dates and reciprocal alternates')

    plain = browser.new_context(java_script_enabled=False)
    plain.route('**/*', intercept)
    static_page = plain.new_page()
    for locale in ['en', 'ko', 'ja']:
        for path, country in CASES:
            static_page.goto(ORIGIN + path + suffix_for(locale, country), wait_until='domcontentloaded')
            expect(static_page.locator('main h1')).to_be_visible()
            if path != '/blog':
                expect(static_page.locator('#worked-example')).to_be_visible()
                for amount in POSTS[path.rsplit('/', 1)[1]]['amounts']:
                    assert amount in static_page.locator('main').inner_text()
            if country == 'US' and path != '/blog':
                expect(static_page.locator('[data-blog-infographic]')).to_be_visible()
                expect(static_page.locator('[data-blog-yield-chart]')).to_be_visible()
            passed('without JavaScript ' + path + ' ' + locale)
    plain.close()

    context.route('**/api/public/countries*', lambda route: route.fulfill(status=503, body='{}'))
    page.set_viewport_size({'width': 390, 'height': 844})
    for slug, post in POSTS.items():
        page.goto(ORIGIN + '/blog/' + slug + suffix_for('ko', post.get('country', 'CA')), wait_until='networkidle')
        expect(page.locator('[data-blog-comparison]')).to_be_visible()
        page.locator('[data-blog-comparison]').click()
        expect(page).to_have_url(ORIGIN + catalog(post, 'ko'))
        expect(page.locator('main h1')).to_have_count(1, timeout=30000)
        passed('article-to-catalog with country lookup unavailable ' + slug)
    assert not errors, errors
    browser.close()
print(json.dumps({'checks': len(checks), 'browser_errors': errors}, ensure_ascii=False))
