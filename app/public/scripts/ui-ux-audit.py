"""Public interaction regressions against a running local build with approved data.

From the repository root:
  $env:FPDS_UI_TEST_ORIGIN='http://localhost:3000'
  uv run --with playwright python app/public/scripts/ui-ux-audit.py
Chrome must be installed. All browser writes and external requests are stubbed.
"""
import json
import os
import re
from urllib.parse import urlencode, urlparse

from playwright.sync_api import expect, sync_playwright

ORIGIN = os.environ.get('FPDS_UI_TEST_ORIGIN', 'http://localhost:3000').rstrip('/')
if urlparse(ORIGIN).hostname not in {'localhost', '127.0.0.1', '::1'}:
    raise ValueError('Run this audit against a local build.')
checks = []
errors = []


def passed(name):
    checks.append(name)
    print('PASS', name, flush=True)


def intercept(route):
    request = route.request
    if not request.url.startswith(ORIGIN + '/') or request.method not in {'GET', 'HEAD'}:
        route.fulfill(status=200, content_type='application/json', body='{}')
    else:
        route.continue_()


def goto(page, path, locale='en', **params):
    response = page.goto(ORIGIN + path + '?' + urlencode({'locale': locale, **params}, doseq=True), wait_until='domcontentloaded')
    assert response.status == 200, (path, response.status)
    expect(page.locator('main h1')).to_have_count(1)
    expect(page.locator('html')).to_have_attribute('lang', locale)
    page.wait_for_load_state('networkidle')


def settled(page):
    expect(page.locator('form[action]').first).to_have_attribute('aria-busy', 'false', timeout=20000)


def layout(page):
    assert page.evaluate('document.documentElement.scrollWidth <= innerWidth'), page.url
    assert '\ufffd' not in page.locator('main').inner_text(), page.url


with sync_playwright() as pw:
    browser = pw.chromium.launch(channel='chrome', headless=True)
    context = browser.new_context(viewport={'width': 1440, 'height': 900}, reduced_motion='reduce')
    context.route('**/*', intercept)
    page = context.new_page()
    page.on('pageerror', lambda error: errors.append(str(error)))
    page.on('console', lambda message: errors.append(message.text) if re.search(r'hydration|did not match|unique.*key|Minified React', message.text, re.I) else None)
    data = context.request.get(ORIGIN + '/api/public/products?product_type=savings&page_size=100').json()['data']['items']
    assert len(data) >= 2, 'Provide at least two approved savings products for the comparison regression.'
    data = [product for product in data if product['currency'] == 'CAD']
    assert len(data) >= 2, 'Provide two CAD savings products for the same-currency calculator.'
    ids = [product['product_id'] for product in data[:2]]
    for locale in ['en', 'ko', 'ja']:
        for width in [390, 768, 1440]:
            page.set_viewport_size({'width': width, 'height': 900})
            for path in ['/', '/products', '/cards', '/loans', '/products/' + ids[0], '/compare', '/calculator', '/guides', '/methodology']:
                params = {'product_id': ids} if path in {'/compare', '/calculator'} else {}
                goto(page, path, locale, **params)
                if path == '/':
                    expect(page.locator('#current-product-search')).to_be_visible(timeout=20000)
                if path in {'/products', '/cards', '/loans'}:
                    search = page.locator('input[name=q]')
                    expect(search).to_be_visible()
                    assert search.bounding_box()['height'] >= 44
                    for control in page.locator('main a[href*="view="]').all():
                        box = control.bounding_box()
                        assert box['width'] >= 44 and box['height'] >= 44
                        assert box['x'] >= 0 and box['x'] + box['width'] <= width
                if path == '/compare':
                    expect(page.locator('[data-bank-handoff]')).to_have_count(2, timeout=20000)
                if path == '/calculator':
                    expect(page.locator('input[inputmode=decimal]')).to_be_visible(timeout=20000)
                layout(page)
                passed(f'layout {path} {locale} {width}')
            # Tablet uses the same labelled menu as mobile; desktop labels remain visible.
            if width < 1024:
                menu = page.locator('header button[aria-haspopup=menu]:visible')
                menu.click()
                expect(page.get_by_role('menu')).to_be_visible()
                assert page.get_by_role('menuitem').count() >= 4
                page.keyboard.press('Escape')
                expect(menu).to_be_focused()
            else:
                links = page.locator('header nav a')
                assert links.count() == 4
                assert all(link.get_attribute('aria-label') for link in links.all())
            passed(f'navigation names and menu focus {locale} {width}')

        # All three catalogs share the filter form. Updating results must retain focus.
        for path in ['/products', '/cards', '/loans']:
            goto(page, path, locale)
            search = page.locator('input[name=q]')
            search.fill('Bank')
            expect(page).to_have_url(re.compile(r'[?&]q=Bank(?:&|$)'), timeout=20000)
            settled(page)
            expect(search).to_be_focused()
            expect(page.locator('details')).not_to_have_attribute('open', '')
            page.keyboard.type(' nevermatches')
            expect(page).to_have_url(re.compile(r'q=Bank\+nevermatches'), timeout=20000)
            settled(page)
            expect(search).to_be_focused()
            assert page.locator('main article').count() == 0
            search.fill('')
            settled(page)
            expect(search).to_be_focused()
            assert 'q=' not in page.url
            # Korean/Japanese composition must not publish unfinished text to the URL.
            search.dispatch_event('compositionstart')
            search.fill('Bank')
            page.wait_for_timeout(500)
            assert 'q=' not in page.url
            search.dispatch_event('compositionend', {'data': 'Bank'})
            expect(page).to_have_url(re.compile(r'[?&]q=Bank(?:&|$)'), timeout=20000)
            settled(page)
            expect(search).to_be_focused()
            passed(f'search focus, empty state, clear, IME {path} {locale}')

        goto(page, '/products', locale, q='Bank')
        page.locator('main a[href*="sort_by=monthly_fee"]').click()
        page.wait_for_load_state('networkidle')
        search = page.locator('input[name=q]')
        search.fill('Savings')
        expect(page).to_have_url(re.compile(r'q=Savings'), timeout=20000)
        settled(page)
        page.go_back(wait_until='domcontentloaded')
        expect(search).to_have_value('Bank')
        expect(search).to_be_focused()
        page.go_forward(wait_until='domcontentloaded')
        expect(search).to_have_value('Savings')
        passed(f'focused search restores on back/forward {locale}')

        goto(page, '/products', locale)
        page.locator('details summary').click()
        checkbox = page.locator('input[name=bank_code]').first
        value = checkbox.get_attribute('value')
        assert value and value != 'on', 'Filter fixture must provide API value fields.'
        checkbox.focus()
        page.keyboard.press('Space')
        settled(page)
        expect(checkbox).to_be_checked()
        expect(checkbox).to_be_focused()
        page.keyboard.press('Space')
        settled(page)
        expect(checkbox).not_to_be_checked()
        expect(checkbox).to_be_focused()
        expect(page.locator('details')).to_have_attribute('open', '')
        passed(f'bank filter keyboard toggle without focus loss {locale}')

        goto(page, '/', locale)
        field = page.locator('#current-product-search')
        field.focus()
        expect(page.get_by_role('option').first).to_be_visible(timeout=20000)
        page.keyboard.press('ArrowDown')
        expect(field).to_have_attribute('aria-activedescendant', 'current-product-option-0')
        name = page.get_by_role('option').first.locator('span').first.inner_text()
        page.keyboard.press('Enter')
        expect(field).to_have_value(name)
        expect(field).to_be_focused()
        expect(field).to_have_attribute('aria-expanded', 'false')
        page.keyboard.press('ArrowDown')
        expect(field).to_have_attribute('aria-expanded', 'true')
        page.keyboard.press('Escape')
        expect(field).to_have_attribute('aria-expanded', 'false')
        page.keyboard.press('ArrowDown')
        page.keyboard.press('Tab')
        expect(field).to_have_attribute('aria-expanded', 'false')
        passed(f'finder keyboard select, reopen, escape, tab {locale}')

        goto(page, '/products', locale)
        skip = page.locator('a[href="#main-content"]')
        skip.focus()
        box = skip.bounding_box()
        assert box['y'] >= 0 and box['height'] >= 44
        page.keyboard.press('Enter')
        expect(page.locator('#main-content')).to_be_focused()
        passed(f'skip to content {locale}')

    assert not errors, errors
    browser.close()
print(json.dumps({'passed': len(checks), 'browser_errors': errors}))
