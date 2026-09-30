"""Blog SEO, navigation and responsive checks against a local production build.
Run: uv run --with playwright python app/public/scripts/blog-audit.py
Override FPDS_UI_TEST_ORIGIN when needed. Browser writes and external requests are blocked.
"""
import json
import os
from pathlib import Path
from urllib.parse import urlparse
import xml.etree.ElementTree as ET
from playwright.sync_api import expect, sync_playwright

ORIGIN = os.environ.get('FPDS_UI_TEST_ORIGIN', 'http://localhost:3000').rstrip('/')
assert urlparse(ORIGIN).hostname in {'localhost', '127.0.0.1', '::1'}
SLUG = 'eq-bank-vs-tangerine-vs-td-savings'
PROD = 'https://www.switchabank.com'
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
            for path in ['/blog', '/blog/' + SLUG]:
                response = page.goto(ORIGIN + path + suffix, wait_until='networkidle')
                assert response.status == 200
                expect(page.locator('html')).to_have_attribute('lang', locale)
                expect(page.locator('main h1')).to_have_count(1)
                assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
                assert '\ufffd' not in page.locator('main').inner_text()
                expect(page.locator('link[rel=canonical]')).to_have_attribute('href', PROD + path + suffix)
                assert 'noindex' not in page.locator('meta[name=robots]').get_attribute('content')
                assert page.locator('link[rel=alternate][hreflang]').count() == 4
                assert page.locator('meta[property="og:image"]').count() >= 1
                assert page.locator('meta[name=description]').get_attribute('content')
                for img in page.locator('main img').all():
                    img.scroll_into_view_if_needed()
                    expect(img).to_be_visible()
                    assert img.evaluate('(img) => img.complete && img.naturalWidth > 0')
                if path != '/blog':
                    graph = [json.loads(text) for text in page.locator('script[type="application/ld+json"]').all_text_contents()]
                    article = next(node for entry in graph for node in entry.get('@graph', []) if node.get('@type') == 'BlogPosting')
                    assert article['headline'] == page.locator('h1').inner_text()
                    assert article['url'] == PROD + path + suffix
                    assert article['datePublished'] == article['dateModified'] == '2026-09-30'
                    assert len(article['citation']) == 4
                    expect(page.locator('meta[property="og:type"]')).to_have_attribute('content', 'article')
                    assert page.locator('table tbody tr').count() == 3
                    expect(page.locator('[data-blog-comparison]')).to_have_attribute('href', '/products?product_type=savings' + ('' if locale == 'en' else '&locale=' + locale))
                    toc = page.locator('a[href="#worked-example"]')
                    toc.click()
                    expect(page).to_have_url(ORIGIN + path + suffix + '#worked-example')
                    page.wait_for_timeout(200)
                    assert page.locator('#worked-example').bounding_box()['y'] >= 64
                    page.locator('main h1').scroll_into_view_if_needed()
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
                    page.screenshot(path=str(screens / (('index' if path == '/blog' else 'article') + '-' + str(width) + '.png')), full_page=True)
                passed(f'{path} {locale} {width}')

    # Routes and crawler signals are checked through raw HTTP as well as hydrated DOM.
    for path in ['/blog/unknown', '/blog/constructor', '/blog/' + SLUG + '/extra']:
        assert context.request.get(ORIGIN + path).status == 404
        passed('404 ' + path)
    for query in ['?locale=fr', '?locale=ko&locale=ja', '?q=bank', '?utm_source=test', '?country_code=CA']:
        page.goto(ORIGIN + '/blog/' + SLUG + query, wait_until='domcontentloaded')
        assert 'noindex' in page.locator('meta[name=robots]').get_attribute('content')
        passed('noindex ' + query)
    for path in ['/blog', '/blog/' + SLUG]:
        response = context.request.get(ORIGIN + path + '?country_code=US&locale=ko', max_redirects=0)
        assert response.status == 308
        assert response.headers['location'].endswith('/products?country_code=US&product_type=savings&locale=ko')
        passed('country ' + path)
    response = context.request.get(ORIGIN + '/blog/opengraph-image')
    assert response.status == 200 and response.headers['content-type'].startswith('image/png')
    passed('social preview PNG')
    sitemap = ET.fromstring(context.request.get(ORIGIN + '/sitemap.xml').text())
    ns = {'s': 'http://www.sitemaps.org/schemas/sitemap/0.9', 'x': 'http://www.w3.org/1999/xhtml'}
    entries = [entry for entry in sitemap.findall('s:url', ns) if '/blog' in entry.find('s:loc', ns).text]
    assert len(entries) == 6
    for entry in entries:
        assert entry.find('s:lastmod', ns).text == '2026-09-30'
        assert len(entry.findall('x:link', ns)) == 4
    passed('six sitemap URLs and reciprocal alternates')

    # JavaScript-free readers/crawlers receive the entire article.
    plain = browser.new_context(java_script_enabled=False)
    plain.route('**/*', intercept)
    static_page = plain.new_page()
    for locale in ['en', 'ko', 'ja']:
        for path in ['/blog', '/blog/' + SLUG]:
            static_page.goto(ORIGIN + path + '?locale=' + locale, wait_until='domcontentloaded')
            expect(static_page.locator('main h1')).to_be_visible()
            if path != '/blog':
                expect(static_page.locator('#worked-example')).to_be_visible()
                assert 'CAD 200' in static_page.locator('main').inner_text()
            passed('without JavaScript ' + path + ' ' + locale)
    plain.close()

    # Failed country lookup does not hide editorial content or comparison links.
    context.route('**/api/public/countries*', lambda route: route.fulfill(status=503, body='{}'))
    page.set_viewport_size({'width': 390, 'height': 844})
    page.goto(ORIGIN + '/blog/' + SLUG + '?locale=ko', wait_until='networkidle')
    expect(page.locator('[data-blog-comparison]')).to_be_visible()
    page.locator('[data-blog-comparison]').click()
    expect(page).to_have_url(ORIGIN + '/products?product_type=savings&locale=ko')
    expect(page.locator('main h1')).to_have_count(1, timeout=20000)
    passed('article-to-catalog flow with country lookup unavailable')
    assert not errors, errors
    browser.close()
print(json.dumps({'checks': len(checks), 'browser_errors': errors}, ensure_ascii=False))
