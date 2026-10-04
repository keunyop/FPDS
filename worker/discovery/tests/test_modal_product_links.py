from pathlib import Path
import unittest
from worker.discovery.fpds_discovery.discovery import extract_links

FIXTURE = Path(__file__).parents[2] / "pipeline/tests/fixtures/golden/coast_card_modal_dom.html"

class ModalProductLinksTests(unittest.TestCase):
    def test_actual_card_confirm_destination_retains_product_label(self):
        links = extract_links(FIXTURE.read_text(encoding="utf8"), base_url="https://www.coastcapitalsavings.com/everyday-banking/credit-cards")
        self.assertTrue(any("card_national-centra-gold-mastercard" in l.normalized_url and l.anchor_text == "Centra Gold Mastercard" for l in links))

    def html(self, script, duplicate=""):
        return '<main><a href="#" data-toggle="modal" data-target="#dialog" title="Everyday Card">Learn more</a><div id="dialog" class="modal"><button id="confirm">OK</button>'+duplicate+'</div><script>'+script+'</script></main>'

    def test_only_literal_click_handlers_on_existing_unambiguous_dialogs(self):
        good = "$('#confirm').on('click', function () { window.location = 'https://issuer.example/cards/everyday';});"
        self.assertEqual(extract_links(self.html(good), base_url="https://bank.example/cards")[0].anchor_text, "Everyday Card")
        for script in [good.replace("https://issuer.example/cards/everyday", "javascript:evil()"),
                       good.replace("'#confirm'", "'#absent'"), good.replace("'click'", "'load'"),
                       good.replace("'https://issuer.example/cards/everyday'", "destination"),
                       "window.location = 'https://issuer.example/cards/everyday';",
                       good + good.replace("everyday", "premium"),
                       "// " + good, "/* " + good + " */", "const example = `" + good + "`;"]:
            self.assertEqual(extract_links(self.html(script), base_url="https://bank.example/cards"), [], script)
        self.assertEqual(extract_links(self.html(good, '<button id="confirm">Duplicate</button>'), base_url="https://bank.example/cards"), [])

    def test_inline_literal_and_duplicate_confirmation_button_limits(self):
        script = "$('#confirm').on('click', function () { window.location = 'https://issuer.example/cards/everyday';});"
        fillers = ''.join('<button id="confirm-'+str(i)+'">OK</button>' for i in range(260))
        self.assertEqual(extract_links(self.html(script, fillers+'<button id="confirm">Duplicate</button>'), base_url="https://bank.example/cards"), [])
        inline = self.html('').replace('id="confirm"', 'id="confirm" onclick="window.open(\'https://issuer.example/cards/everyday\');"')
        self.assertTrue(extract_links(inline, base_url="https://bank.example/cards"))
        ambiguous = inline.replace("everyday');", "everyday'); window.open('https://issuer.example/cards/premium');")
        self.assertFalse(extract_links(ambiguous, base_url="https://bank.example/cards"))

    def test_navigation_caps_and_unrelated_navigation_do_not_hide_card_link(self):
        raw = FIXTURE.read_text(encoding="utf8")
        raw = '<nav>'+''.join('<a href="/nav/'+str(i)+'">Menu</a>' for i in range(300))+'</nav>'+raw
        links = extract_links(raw, base_url="https://bank.example/cards")
        self.assertLessEqual(len(links),256)
        self.assertTrue(any("centra-gold" in l.normalized_url for l in links))
