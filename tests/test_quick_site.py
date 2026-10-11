import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

spec=importlib.util.spec_from_file_location('quick_site',Path(__file__).parents[1]/'tools/quick_site.py')
quick=importlib.util.module_from_spec(spec);spec.loader.exec_module(quick)

class QuickSiteTests(unittest.TestCase):
    def test_isolation_escaping_and_no_build_per_business(self):
        with tempfile.TemporaryDirectory() as folder, patch.object(quick.subprocess, 'run', side_effect=AssertionError('Unexpected build')):
            a=quick.create({'name':'O\'Brien & Sons </script><script>alert(1)</script>', 'phone':'+44 20 7946 0958'},folder)
            b=quick.create({'name':'Second Electrical','email':'contact@example.com'},folder)
            self.assertNotEqual(a['site'],b['site'])
            self.assertIn('&lt;/script&gt;', (Path(a['site'])/'index.html').read_text())
            payload=(Path(a['site'])/'business.js').read_text().removeprefix('window.WEBSITE_BUSINESS = ').removesuffix(';\n')
            self.assertEqual(json.loads(payload)['name'],a['business']['name'])
            self.assertNotIn('Second Electrical',(Path(a['site'])/'business.js').read_text())
            self.assertNotIn("O'Brien",(Path(b['site'])/'business.js').read_text())
            self.assertFalse((Path(a['site'])/'node_modules').exists())
            self.assertIn('noindex', (Path(a['site'])/'vercel.json').read_text())
    def test_service_catalog_validation_and_safe_legacy_default(self):
        _, legacy = quick.validate({'name': 'Legacy', 'phone': '123456789'})
        self.assertEqual(legacy['enabled_services'], [])
        for services in ('ev-charging', ['unknown'], ['ev-charging', 'ev-charging'], [42]):
            with self.subTest(services=services), self.assertRaisesRegex(ValueError, 'enabled_services'):
                quick.validate({'name': 'Test', 'phone': '123456789', 'enabled_services': services})
        self.assertEqual(set(quick.SERVICE_CATALOG), {
            'electrical-repairs', 'electrical-installation', 'rcd-protection',
            'electrical-enclosures', 'consumer-units', 'rewiring',
            'electrical-contracting', 'extensions', 'renovations',
            'maintenance', 'ev-charging', 'service-entrance',
        })
        for path in quick.SERVICE_CATALOG.values():
            self.assertRegex(path, r'^/[a-z0-9-]+$')
            self.assertNotRegex(path, r'electrical|repairs|charging|maintenance')

    def test_two_service_configs_share_build_but_keep_business_data_separate(self):
        with tempfile.TemporaryDirectory() as folder, patch.object(quick.subprocess, 'run', side_effect=AssertionError('Unexpected build')):
            a = quick.create({'name': 'Without EV', 'phone': '123456789', 'enabled_services': ['maintenance']}, folder)
            b = quick.create({'name': 'With EV', 'phone': '123456789', 'enabled_services': ['ev-charging']}, folder)
            def payload(result):
                return json.loads((Path(result['site']) / 'business.js').read_text().split(' = ', 1)[1].removesuffix(';\n'))
            self.assertEqual(payload(a)['enabled_services'], ['maintenance'])
            self.assertEqual(payload(b)['enabled_services'], ['ev-charging'])
            self.assertEqual(
                sorted(p.name for p in (Path(a['site']) / 'assets').iterdir()),
                sorted(p.name for p in (Path(b['site']) / 'assets').iterdir()),
            )

    def test_public_phone_is_presumed_whatsapp_unless_opted_out(self):
        _, b = quick.validate({'name': 'Teste', 'phone': '(14) 99712-3456'})
        self.assertEqual(b['whatsapp'], '5514997123456')
        _, b = quick.validate({'name': 'Teste', 'phone': '14 3222-1234', 'whatsapp': '+55 (14) 98888-7777'})
        self.assertEqual(b['whatsapp'], '5514988887777')
        _, b = quick.validate({'name': 'Teste', 'phone': '(14) 3222-1234', 'whatsapp': False})
        self.assertIs(b['whatsapp'], False)
        _, b = quick.validate({'name': 'Teste', 'email': 'contato@example.com'})
        self.assertNotIn('whatsapp', b)
        self.assertEqual(quick.whatsapp_number('014 3222-1234'), '551432221234')
        self.assertEqual(quick.whatsapp_number('12345'), '')
        with self.assertRaisesRegex(ValueError, 'whatsapp'):
            quick.validate({'name': 'Teste', 'phone': '(14) 99712-3456', 'whatsapp': '123'})

    def test_brazilian_fields(self):
        _, b = quick.validate({'name': 'Teste', 'phone': '(14) 99712-3456', 'state': 'sp', 'zip': '17010-000', 'cnpj': '11.222.333/0001-81', 'payment_methods': ['Pix', 'Cartão']})
        self.assertEqual((b['state'], b['cnpj'], b['payment_methods']), ('SP', '11.222.333/0001-81', ['Pix', 'Cartão']))
        for bad in ({'state': 'XX'}, {'zip': '1701'}, {'cnpj': '11.222.333/0001-80'}, {'payment_methods': 'Pix'}, {'founded_year': 1800}):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                quick.validate({'name': 'Teste', 'phone': '(14) 99712-3456', **bad})

    def test_social_proof_requires_a_public_source(self):
        base = {'name': 'Teste', 'phone': '(14) 99712-3456'}
        for bad in ({'google_rating': 4.8}, {'reviews': [{'author': 'Ana', 'text': 'Ótimo'}]}, {'reviews': [{'author': 'Ana', 'text': 'Ótimo', 'source_url': 'http://x.com'}]}):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                quick.validate({**base, **bad})
        _, b = quick.validate({**base, 'google_rating': 4.8, 'google_reviews_count': 31, 'google_reviews_url': 'https://maps.google.com/?cid=1'})
        self.assertEqual(b['google_reviews_count'], 31)

    def test_static_head_names_business_and_city(self):
        with tempfile.TemporaryDirectory() as folder:
            result = quick.create({'name': 'Elétrica <Silva>', 'phone': '(14) 99712-3456', 'city': 'Bauru', 'state': 'SP'}, folder)
            page = (Path(result['site']) / 'index.html').read_text()
            self.assertIn('<title>Eletricista em Bauru | Elétrica &lt;Silva&gt;</title>', page)
            self.assertIn('og:title" content="Eletricista em Bauru | Elétrica &lt;Silva&gt;"', page)
            self.assertNotIn('Your Company', page)

    def test_prepared_build_has_no_legacy_or_placeholder_content(self):
        dist = quick.TEMPLATES['electrician']['path'] / 'dist'
        text = '\n'.join(p.read_text(errors='ignore') for p in dist.rglob('*') if p.suffix in ('.js', '.html', '.css') or p.name == '_redirects')
        for term in ('you@example.com', 'Inspiração', 'elektriker', 'ladeboks', 'authNumber', 'Converse conosco sobre o serviço elétrico', 'Prévia do formulário'):
            with self.subTest(term=term):
                self.assertNotIn(term, text)

    def test_invalid_input(self):
        for data in ({'name':'Business'}, {'name':'Business','phone':'javascript:alert(1)'}, {'name':'Business','email':'invalid'}, {'name':'Business','phone':'12345','template':'../outside'}):
            with self.assertRaises(ValueError): quick.validate(data)
    def test_theme_color_is_validated_and_saved(self):
        for color in ('red', '#fff', '#123456;bad', None):
            with self.assertRaisesRegex(ValueError, 'Theme color'):
                quick.validate({'name':'Test','phone':'123456789','theme_color':color})
        with tempfile.TemporaryDirectory() as folder:
            result=quick.create({'name':'Test','phone':'123456789','theme_color':'#7C3AED'},folder)
            self.assertEqual(result['business']['theme_color'],'#7c3aed')
            self.assertIn('#7c3aed',(Path(result['site'])/'business.js').read_text())

    def test_stale_template_requires_preparation(self):
        with patch.object(quick,'fingerprint',return_value='changed'):
            with self.assertRaisesRegex(ValueError,'preparation'):quick.create({'name':'Business','phone':'123456789'})

if __name__=='__main__':unittest.main()
