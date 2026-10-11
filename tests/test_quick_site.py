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
        self.assertEqual(legacy['enabled_services'], quick.SEGMENT['default_services'])
        self.assertTrue(set(legacy['enabled_services']) <= set(quick.SERVICE_CATALOG))
        _, none = quick.validate({'name': 'None', 'phone': '123456789', 'enabled_services': []})
        self.assertEqual(none['enabled_services'], [])
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

    def test_favicon_is_the_page_logo_in_the_theme_color(self):
        # Colors match deriveTheme('#e11d48') in src/themeMath.js: dark [203,26,65], light [245,183,197].
        with tempfile.TemporaryDirectory() as folder:
            result = quick.create({'name': 'Teste', 'phone': '(14) 99712-3456', 'theme_color': '#E11D48'}, folder)
            site = Path(result['site'])
            icon = (site / 'favicon.svg').read_text()
            for color in ('#e11d48', '#cb1a41', '#f5b7c5'):
                self.assertIn(color, icon)
            self.assertNotIn('#F7B500', icon)
            page = (site / 'index.html').read_text()
            self.assertIn('name="theme-color" content="#e11d48"', page)
            self.assertNotIn('alternate icon', page)
        for name in quick.TEMPLATES:
            mark = json.loads((quick.profile(name)['folder'] / 'segment.json').read_text())['mark']
            icon = quick.render_favicon('#e11d48', mark)
            for path in mark.values():
                self.assertIn(path, icon)

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

    def test_default_theme_color_applies_when_not_detected(self):
        self.assertEqual(quick.DEFAULT_THEME_COLOR, '#2563eb')
        for data in ({'name': 'Test', 'phone': '123456789'}, {'name': 'Test', 'phone': '123456789', 'theme_color': ''}):
            self.assertEqual(quick.validate(data)[1]['theme_color'], '#2563eb')

    def test_stale_template_requires_preparation(self):
        with patch.object(quick,'fingerprint',return_value='changed'):
            with self.assertRaisesRegex(ValueError,'preparation'):quick.create({'name':'Business','phone':'123456789'})

class SerralheriaProfileTests(unittest.TestCase):
    def test_profile_is_valid_and_defaults_are_minimal(self):
        prof = quick.profile('serralheria')
        self.assertEqual(prof['segment']['id'], 'serralheria')
        self.assertEqual(prof['segment']['default_services'], ['metal-gates', 'grilles', 'railings', 'welding-repairs'])
        self.assertTrue(set(prof['segment']['default_services']) <= set(prof['catalog']))
        self.assertRegex(prof['segment']['default_theme_color'], r'^#[0-9a-f]{6}$')
        for path in prof['catalog'].values():
            self.assertRegex(path, r'^/[a-z0-9-]+$')
            self.assertNotRegex(path, r'metal-|gates|grilles|railings|welding|stairs|fences')
        self.assertFalse(set(prof['catalog']) & set(quick.profile('electrician')['catalog']))

    def test_preset_covers_catalog_without_invented_claims(self):
        text = (quick.profile('serralheria')['folder'] / 'preset.js').read_text()
        for service_id in quick.profile('serralheria')['catalog']:
            self.assertIn("'%s':" % service_id, text)
        for term in ('projetos realizados', 'garantia', '24h', '24 horas', 'certificad', 'R$', 'eletric', 'elétric'):
            with self.subTest(term=term):
                self.assertNotIn(term, text.lower())

    def test_serralheria_site_uses_its_own_build_and_defaults(self):
        with tempfile.TemporaryDirectory() as folder, patch.object(quick.subprocess, 'run', side_effect=AssertionError('Unexpected build')):
            home = quick.create({'name': 'Serralheria Teste', 'phone': '(14) 99712-3456', 'city': 'Bauru', 'state': 'SP', 'template': 'serralheria'}, folder)
            site = Path(home['site'])
            business = (site / 'business.js').read_text()
            self.assertIn('#ea580c', business)
            for service_id in quick.profile('serralheria')['segment']['default_services']:
                self.assertIn(service_id, business)
            self.assertNotIn('ev-charging', business)
            page = (site / 'index.html').read_text()
            self.assertIn('Serralheria', page)
            self.assertNotIn('eletricista', page.lower())
            self.assertFalse((site / 'images' / 'electrician').exists())
            self.assertIn('M24 25l3.2 4.2L24 33.4l-3.2-4.2z', (site / 'favicon.svg').read_text())

    def test_electrician_service_ids_are_rejected_for_serralheria(self):
        with self.assertRaisesRegex(ValueError, 'enabled_services'):
            quick.validate({'name': 'X', 'phone': '123456789', 'template': 'serralheria', 'enabled_services': ['ev-charging']})

    def test_electrician_build_does_not_ship_serralheria_content(self):
        text = '\n'.join(p.read_text(errors='ignore') for p in quick.profile('electrician')['dist'].rglob('*') if p.suffix in ('.js', '.html'))
        self.assertNotIn('Portões de ferro', text)

    def test_serralheria_build_does_not_ship_electrician_content(self):
        dist = quick.profile('serralheria')['dist']
        text = '\n'.join(p.read_text(errors='ignore') for p in dist.rglob('*') if p.suffix in ('.js', '.html', '.css'))
        for term in ('Eletricista', 'Quadro de distribuição', 'Electrician', '/images/electrician'):
            with self.subTest(term=term):
                self.assertNotIn(term, text)
        self.assertFalse((dist / 'images' / 'electrician').exists())


if __name__=='__main__':unittest.main()
