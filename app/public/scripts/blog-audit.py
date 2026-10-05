"""Verify authored blog routes against a local production build.
Run: uv run --with playwright python app/public/scripts/blog-audit.py
Set FPDS_UI_TEST_ORIGIN to override localhost:3000. External calls and writes are blocked.
"""
import json
import os
import struct
from pathlib import Path
from urllib.parse import urlparse
import xml.etree.ElementTree as ET
from playwright.sync_api import expect, sync_playwright

ORIGIN = os.environ.get('FPDS_UI_TEST_ORIGIN', 'http://localhost:3000').rstrip('/')
assert urlparse(ORIGIN).hostname in {'localhost', '127.0.0.1', '::1'}
PROD = 'https://www.switchabank.com'
POSTS = {
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
checks, errors = [], []
screens = Path('tmp/blog-audit')
screens.mkdir(parents=True, exist_ok=True)

def passed(name):
    checks.append(name)
    print('PASS', name, flush=True)

def intercept(route):
    if not route.request.url.startswith(ORIGIN + '/') or route.request.method not in {'GET', 'HEAD'}:
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
            for path in PATHS:
                response = page.goto(ORIGIN + path + suffix, wait_until='networkidle')
                assert response.status == 200
                expect(page.locator('html')).to_have_attribute('lang', locale)
                expect(page.locator('main h1')).to_have_count(1)
                assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
                assert chr(65533) not in page.locator('main').inner_text()
                expect(page.locator('link[rel=canonical]')).to_have_attribute('href', PROD + path + suffix)
                assert 'noindex' not in page.locator('meta[name=robots]').get_attribute('content')
                alternates = {a.get_attribute('hreflang'): a.get_attribute('href') for a in page.locator('link[rel=alternate][hreflang]').all()}
                assert alternates == {'en-CA': PROD + path, 'ko': PROD + path + '?locale=ko', 'ja': PROD + path + '?locale=ja', 'x-default': PROD + path}
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
                    expect(page.locator('[data-blog-related]')).to_have_attribute('href', '/blog/' + post['related'] + suffix)
                    if 'chequing' in slug:
                        expect(page.locator('[data-blog-shortlist]')).to_have_attribute('href', catalog(post, locale))
                        assert 'Tier 1' in page.locator('table').inner_text()
                    page.locator('a[href="#worked-example"]').click()
                    expect(page).to_have_url(ORIGIN + path + suffix + '#worked-example')
                    page.wait_for_timeout(200)
                    assert page.locator('#worked-example').bounding_box()['y'] >= 64
                    page.locator('main h1').scroll_into_view_if_needed()
                else:
                    assert page.locator('main article').count() == 2
                    expect(page.locator('main article h3 a').first).to_have_attribute('href', '/blog/' + next(iter(POSTS)) + suffix)
                    graph = [json.loads(text) for text in page.locator('script[type="application/ld+json"]').all_text_contents()]
                    listing = next(node for node in graph if node.get('@type') == 'CollectionPage')
                    assert len(listing['mainEntity']['itemListElement']) == 2
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
                    name = 'index' if path == '/blog' else ('chequing' if 'chequing' in path else 'savings')
                    page.screenshot(path=str(screens / (name + '-' + str(width) + '.png')), full_page=True)
                    if name == 'chequing' and width in [390, 1440]:
                        page.screenshot(path=str(screens / (name + '-hero-' + str(width) + '.png')))
                        page.locator('#account-comparison').screenshot(path=str(screens / (name + '-table-' + str(width) + '.png')))
                passed(f'{path} {locale} {width}')

    for path in ['/blog/unknown', '/blog/constructor', '/blog/unknown/opengraph-image',
                 *['/blog/' + slug + '/extra' for slug in POSTS]]:
        assert context.request.get(ORIGIN + path).status == 404
        passed('404 ' + path)
    for slug in POSTS:
        for query in ['?locale=fr', '?locale=ko&locale=ja', '?q=bank', '?utm_source=test', '?country_code=CA']:
            page.goto(ORIGIN + '/blog/' + slug + query, wait_until='domcontentloaded')
            assert 'noindex' in page.locator('meta[name=robots]').get_attribute('content')
            passed('noindex ' + slug + query)
    for path in PATHS:
        response = context.request.get(ORIGIN + path + '?country_code=US&locale=ko', max_redirects=0)
        assert response.status == 308
        product_type = 'chequing' if 'chequing' in path else 'savings'
        assert response.headers['location'].endswith('/products?country_code=US&product_type=' + product_type + '&locale=ko')
        passed('country ' + path)
    previews = []
    for path in PATHS:
        response = context.request.get(ORIGIN + path + '/opengraph-image')
        assert response.status == 200 and response.headers['content-type'].startswith('image/png')
        body = response.body()
        assert body[:8] == bytes([137, 80, 78, 71, 13, 10, 26, 10])
        assert struct.unpack('>II', body[16:24]) == (1200, 630)
        previews.append(body)
        passed('social preview PNG ' + path)
    assert len(set(previews)) == 3
    sitemap = ET.fromstring(context.request.get(ORIGIN + '/sitemap.xml').text())
    ns = {'s': 'http://www.sitemaps.org/schemas/sitemap/0.9', 'x': 'http://www.w3.org/1999/xhtml'}
    entries = [entry for entry in sitemap.findall('s:url', ns) if '/blog' in entry.find('s:loc', ns).text]
    expected = {PROD + path + ('' if locale == 'en' else '?locale=' + locale) for path in PATHS for locale in ['en', 'ko', 'ja']}
    assert {entry.find('s:loc', ns).text for entry in entries} == expected
    for entry in entries:
        url = entry.find('s:loc', ns).text
        old = 'eq-bank-vs-tangerine-vs-td-savings' in url
        assert entry.find('s:lastmod', ns).text == ('2026-09-30' if old else '2026-10-05')
        assert len(entry.findall('x:link', ns)) == 4
    passed('nine sitemap URLs, explicit dates and reciprocal alternates')

    plain = browser.new_context(java_script_enabled=False)
    plain.route('**/*', intercept)
    static_page = plain.new_page()
    for locale in ['en', 'ko', 'ja']:
        for path in PATHS:
            static_page.goto(ORIGIN + path + '?locale=' + locale, wait_until='domcontentloaded')
            expect(static_page.locator('main h1')).to_be_visible()
            if path != '/blog':
                expect(static_page.locator('#worked-example')).to_be_visible()
                for amount in POSTS[path.rsplit('/', 1)[1]]['amounts']:
                    assert amount in static_page.locator('main').inner_text()
            passed('without JavaScript ' + path + ' ' + locale)
    plain.close()

    context.route('**/api/public/countries*', lambda route: route.fulfill(status=503, body='{}'))
    page.set_viewport_size({'width': 390, 'height': 844})
    for slug, post in POSTS.items():
        page.goto(ORIGIN + '/blog/' + slug + '?locale=ko', wait_until='networkidle')
        expect(page.locator('[data-blog-comparison]')).to_be_visible()
        page.locator('[data-blog-comparison]').click()
        expect(page).to_have_url(ORIGIN + catalog(post, 'ko'))
        expect(page.locator('main h1')).to_have_count(1, timeout=20000)
        passed('article-to-catalog with country lookup unavailable ' + slug)
    assert not errors, errors
    browser.close()
print(json.dumps({'checks': len(checks), 'browser_errors': errors}, ensure_ascii=False))
