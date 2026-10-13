import importlib.util
import json
import re
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

spec=importlib.util.spec_from_file_location('quick_site',Path(__file__).parents[1]/'tools/quick_site.py')
quick=importlib.util.module_from_spec(spec);spec.loader.exec_module(quick)
ENGINE_PUBLIC=Path(__file__).parents[1]/'templates/electrician/public'

class QuickSiteTests(unittest.TestCase):
    def test_operation_key_is_persisted_and_retry_reuses_completed_site(self):
        key = 'ab' * 32
        with tempfile.TemporaryDirectory() as folder, patch.object(quick.subprocess, 'run', side_effect=AssertionError('Unexpected build')):
            first = quick.create({'name': 'Idempotent', 'phone': '123456789'}, folder, operation_key=key)
            manifest = quick.find_generated(folder, key)
            self.assertEqual(manifest, first)
            self.assertEqual(manifest['operation_key'], key)
            self.assertRegex(manifest['input_digest'], r'^[0-9a-f]{64}$')
            # Models a retry after the staging rename completed but before its caller saved the result.
            with patch.object(quick, 'fingerprint', side_effect=AssertionError('Retry should reuse persisted result')):
                second = quick.create({'name': 'Idempotent', 'phone': '123456789'}, folder, operation_key=key)
            self.assertEqual(second['id'], first['id'])
            self.assertEqual(second['site'], first['site'])
            self.assertEqual(len(list(Path(folder).glob('*/website.json'))), 1)

    def test_operation_key_rejects_unsafe_values_and_conflicting_input(self):
        for key in ('../' + 'a' * 61, 'g' * 64, 'a' * 63, 123):
            with self.subTest(key=key), self.assertRaisesRegex(ValueError, 'operation_key'):
                quick.create({'name': 'Test', 'phone': '123456789'}, '/tmp', operation_key=key)
        with tempfile.TemporaryDirectory() as folder:
            key = 'cd' * 32
            quick.create({'name': 'Original', 'phone': '123456789'}, folder, operation_key=key)
            with self.assertRaisesRegex(ValueError, 'different business input'):
                quick.create({'name': 'Changed', 'phone': '123456789'}, folder, operation_key=key)

    def test_find_generated_requires_matching_key_and_existing_site(self):
        with tempfile.TemporaryDirectory() as folder:
            key = 'ef' * 32
            result = quick.create({'name': 'Lookup', 'phone': '123456789'}, folder, operation_key=key)
            self.assertIsNone(quick.find_generated(folder, '01' * 32))
            Path(result['site']).rename(Path(result['site']).with_name('missing-site'))
            self.assertIsNone(quick.find_generated(folder, key))

    def test_legacy_create_does_not_require_or_write_operation_key(self):
        with tempfile.TemporaryDirectory() as folder:
            result = quick.create({'name': 'Legacy', 'phone': '123456789'}, folder)
            self.assertNotIn('operation_key', result)
            self.assertNotIn('input_digest', json.loads((Path(result['site']).parent / 'website.json').read_text()))

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


class ClimatizacaoProfileTests(unittest.TestCase):
    def test_profile_is_valid_and_defaults_are_minimal(self):
        prof = quick.profile('climatizacao')
        self.assertEqual(prof['segment']['id'], 'climatizacao')
        self.assertEqual(prof['segment']['default_services'], ['split-installation', 'preventive-maintenance', 'aircon-cleaning', 'diagnostics-repair'])
        self.assertTrue(set(prof['segment']['default_services']) <= set(prof['catalog']))
        self.assertRegex(prof['segment']['default_theme_color'], r'^#[0-9a-f]{6}$')
        for path in prof['catalog'].values():
            self.assertRegex(path, r'^/[a-z0-9-]+$')
            self.assertNotRegex(path, r'split|installation|maintenance|cleaning|diagnostics|relocation|piping|commercial')
        self.assertFalse(set(prof['catalog']) & set(quick.profile('electrician')['catalog']))
        self.assertFalse(set(prof['catalog']) & set(quick.profile('serralheria')['catalog']))

    def test_preset_covers_catalog_without_invented_claims(self):
        text = (quick.profile('climatizacao')['folder'] / 'preset.js').read_text()
        for service_id in quick.profile('climatizacao')['catalog']:
            self.assertIn("'%s':" % service_id, text)
        for term in ('projetos realizados', 'garantia', '24h', '24 horas', 'certificad', 'R$', 'autorizada', 'econom', 'elimina', 'urgên', 'diagnóstico remoto'):
            with self.subTest(term=term):
                self.assertNotIn(term, text.lower())

    def test_stock_photos_are_free_and_labelled_illustrative(self):
        folder = quick.profile('climatizacao')['folder']
        for item in json.loads((folder / 'stock-images.json').read_text()):
            self.assertEqual(item['license'], 'https://unsplash.com/license')
            self.assertNotIn('plus.unsplash.com', item['image'])
            self.assertTrue((ENGINE_PUBLIC / item['file']).exists())
        for alt in re.findall(r"alt: '([^']+)'", (folder / 'preset.js').read_text()):
            self.assertIn('imagem ilustrativa', alt)

    def test_climatizacao_site_uses_its_own_build_and_defaults(self):
        with tempfile.TemporaryDirectory() as folder, patch.object(quick.subprocess, 'run', side_effect=AssertionError('Unexpected build')):
            home = quick.create({'name': 'Clima Teste', 'phone': '(14) 99712-3456', 'city': 'Bauru', 'state': 'SP', 'template': 'climatizacao'}, folder)
            site = Path(home['site'])
            business = (site / 'business.js').read_text()
            self.assertIn('#0284c7', business)
            for service_id in quick.profile('climatizacao')['segment']['default_services']:
                self.assertIn(service_id, business)
            self.assertNotIn('ev-charging', business)
            self.assertNotIn('metal-gates', business)
            self.assertNotIn('eletricista', (site / 'index.html').read_text().lower())
            self.assertFalse((site / 'images' / 'electrician').exists())
            self.assertFalse((site / 'images' / 'serralheria').exists())

    def test_other_segments_ids_are_rejected_for_climatizacao(self):
        for bad in ('ev-charging', 'metal-gates'):
            with self.assertRaisesRegex(ValueError, 'enabled_services'):
                quick.validate({'name': 'X', 'phone': '123456789', 'template': 'climatizacao', 'enabled_services': [bad]})

    def test_climatizacao_build_does_not_ship_other_segments(self):
        dist = quick.profile('climatizacao')['dist']
        text = '\n'.join(p.read_text(errors='ignore') for p in dist.rglob('*') if p.suffix in ('.js', '.html', '.css'))
        for term in ('Eletricista', 'Quadro de distribuição', 'Portões de ferro', '/images/electrician', '/images/serralheria'):
            with self.subTest(term=term):
                self.assertNotIn(term, text)
        self.assertFalse((dist / 'images' / 'electrician').exists())
        self.assertFalse((dist / 'images' / 'serralheria').exists())


class ChaveirosProfileTests(unittest.TestCase):
    def test_profile_is_valid_and_defaults_are_minimal(self):
        prof = quick.profile('chaveiros')
        self.assertEqual(prof['segment']['id'], 'chaveiros')
        self.assertEqual(prof['segment']['default_services'], ['door-opening', 'key-duplication', 'lock-replacement', 'car-keys'])
        self.assertTrue(set(prof['segment']['default_services']) <= set(prof['catalog']))
        self.assertRegex(prof['segment']['default_theme_color'], r'^#[0-9a-f]{6}$')
        for path in prof['catalog'].values():
            self.assertRegex(path, r'^/[a-z0-9-]+$')
            self.assertNotRegex(path, r'opening|duplication|replacement|installation|keys|digital|safes')
        self.assertFalse(set(prof['catalog']) & set(quick.profile('electrician')['catalog']))
        self.assertFalse(set(prof['catalog']) & set(quick.profile('serralheria')['catalog']))
        self.assertFalse(set(prof['catalog']) & set(quick.profile('climatizacao')['catalog']))

    def test_preset_covers_catalog_without_invented_claims(self):
        text = (quick.profile('chaveiros')['folder'] / 'preset.js').read_text()
        for service_id in quick.profile('chaveiros')['catalog']:
            self.assertIn("'%s':" % service_id, text)
        for term in ('projetos realizados', 'garantia', '24h', '24 horas', 'certificad', 'R$', 'autorizada', 'emergência', 'emergencia', 'urgên', 'imediat', 'ligar agora'):
            with self.subTest(term=term):
                self.assertNotIn(term, text.lower())

    def test_stock_photos_are_free_and_labelled_illustrative(self):
        folder = quick.profile('chaveiros')['folder']
        for item in json.loads((folder / 'stock-images.json').read_text()):
            self.assertEqual(item['license'], 'https://unsplash.com/license')
            self.assertNotIn('plus.unsplash.com', item['image'])
            self.assertTrue((ENGINE_PUBLIC / item['file']).exists())
        for alt in re.findall(r"alt: '([^']+)'", (folder / 'preset.js').read_text()):
            self.assertIn('imagem ilustrativa', alt)

    def test_chaveiros_site_uses_its_own_build_and_defaults(self):
        with tempfile.TemporaryDirectory() as folder, patch.object(quick.subprocess, 'run', side_effect=AssertionError('Unexpected build')):
            home = quick.create({'name': 'Chaveiro Teste', 'phone': '(14) 99712-3456', 'city': 'Bauru', 'state': 'SP', 'template': 'chaveiros'}, folder)
            site = Path(home['site'])
            business = (site / 'business.js').read_text()
            self.assertIn('#b45309', business)
            for service_id in quick.profile('chaveiros')['segment']['default_services']:
                self.assertIn(service_id, business)
            self.assertNotIn('ev-charging', business)
            self.assertNotIn('metal-gates', business)
            self.assertNotIn('split-installation', business)
            self.assertNotIn('eletricista', (site / 'index.html').read_text().lower())
            self.assertFalse((site / 'images' / 'electrician').exists())
            self.assertFalse((site / 'images' / 'serralheria').exists())
            self.assertFalse((site / 'images' / 'climatizacao').exists())

    def test_other_segments_ids_are_rejected_for_chaveiros(self):
        for bad in ('ev-charging', 'metal-gates', 'split-installation'):
            with self.assertRaisesRegex(ValueError, 'enabled_services'):
                quick.validate({'name': 'X', 'phone': '123456789', 'template': 'chaveiros', 'enabled_services': [bad]})

    def test_chaveiros_build_does_not_ship_other_segments(self):
        dist = quick.profile('chaveiros')['dist']
        text = '\n'.join(p.read_text(errors='ignore') for p in dist.rglob('*') if p.suffix in ('.js', '.html', '.css'))
        for term in ('Eletricista', 'Quadro de distribuição', 'Portões de ferro', '/images/electrician', '/images/serralheria', '/images/climatizacao'):
            with self.subTest(term=term):
                self.assertNotIn(term, text)
        self.assertFalse((dist / 'images' / 'electrician').exists())
        self.assertFalse((dist / 'images' / 'serralheria').exists())
        self.assertFalse((dist / 'images' / 'climatizacao').exists())


class VidracariaProfileTests(unittest.TestCase):
    def test_profile_is_valid_and_defaults_are_minimal(self):
        prof = quick.profile('vidracaria')
        self.assertEqual(prof['segment']['id'], 'vidracaria')
        self.assertEqual(prof['segment']['default_services'], ['shower-enclosures', 'mirrors', 'glass-doors', 'glass-replacement'])
        self.assertTrue(set(prof['segment']['default_services']) <= set(prof['catalog']))
        self.assertRegex(prof['segment']['default_theme_color'], r'^#[0-9a-f]{6}$')
        for path in prof['catalog'].values():
            self.assertRegex(path, r'^/[a-z0-9-]+$')
            self.assertNotRegex(path, r'shower|enclosure|mirror|glass|guardrail|balcony|aluminum|frames|windows')
        self.assertFalse(set(prof['catalog']) & set(quick.profile('electrician')['catalog']))
        self.assertFalse(set(prof['catalog']) & set(quick.profile('serralheria')['catalog']))
        self.assertFalse(set(prof['catalog']) & set(quick.profile('climatizacao')['catalog']))
        self.assertFalse(set(prof['catalog']) & set(quick.profile('chaveiros')['catalog']))

    def test_preset_covers_catalog_without_invented_claims(self):
        text = (quick.profile('vidracaria')['folder'] / 'preset.js').read_text()
        for service_id in quick.profile('vidracaria')['catalog']:
            self.assertIn("'%s':" % service_id, text)
        for term in ('projetos realizados', 'garantia', 'norma', 'acústic', 'térmic', 'resistên', 'blindex', '24h', '24 horas', 'certificad', 'R$', 'autorizada', 'emergência', 'emergencia', 'urgên', 'imediat', 'ligar agora'):
            with self.subTest(term=term):
                self.assertNotIn(term, text.lower())

    def test_stock_photos_are_free_and_labelled_illustrative(self):
        folder = quick.profile('vidracaria')['folder']
        for item in json.loads((folder / 'stock-images.json').read_text()):
            self.assertEqual(item['license'], 'https://unsplash.com/license')
            self.assertNotIn('plus.unsplash.com', item['image'])
            self.assertTrue((ENGINE_PUBLIC / item['file']).exists())
        for alt in re.findall(r"alt: '([^']+)'", (folder / 'preset.js').read_text()):
            self.assertIn('imagem ilustrativa', alt)

    def test_vidracaria_site_uses_its_own_build_and_defaults(self):
        with tempfile.TemporaryDirectory() as folder, patch.object(quick.subprocess, 'run', side_effect=AssertionError('Unexpected build')):
            home = quick.create({'name': 'Vidraçaria Teste', 'phone': '(14) 99712-3456', 'city': 'Bauru', 'state': 'SP', 'template': 'vidracaria'}, folder)
            site = Path(home['site'])
            business = (site / 'business.js').read_text()
            self.assertIn('#0e7490', business)
            for service_id in quick.profile('vidracaria')['segment']['default_services']:
                self.assertIn(service_id, business)
            for other in ('ev-charging', 'metal-gates', 'split-installation', 'door-opening', 'aluminum-frames', 'windows', 'glass-guardrails', 'balcony-enclosures'):
                self.assertNotIn(other, business)
            self.assertNotIn('eletricista', (site / 'index.html').read_text().lower())
            self.assertFalse((site / 'images' / 'electrician').exists())
            self.assertFalse((site / 'images' / 'serralheria').exists())
            self.assertFalse((site / 'images' / 'climatizacao').exists())
            self.assertFalse((site / 'images' / 'chaveiros').exists())

    def test_other_segments_ids_are_rejected_for_vidracaria(self):
        for bad in ('ev-charging', 'metal-gates', 'split-installation', 'door-opening'):
            with self.assertRaisesRegex(ValueError, 'enabled_services'):
                quick.validate({'name': 'X', 'phone': '123456789', 'template': 'vidracaria', 'enabled_services': [bad]})

    def test_vidracaria_build_does_not_ship_other_segments(self):
        dist = quick.profile('vidracaria')['dist']
        text = '\n'.join(p.read_text(errors='ignore') for p in dist.rglob('*') if p.suffix in ('.js', '.html', '.css'))
        for term in ('Eletricista', 'Quadro de distribuição', 'Portões de ferro', '/images/electrician', '/images/serralheria', '/images/climatizacao', '/images/chaveiros'):
            with self.subTest(term=term):
                self.assertNotIn(term, text)
        self.assertFalse((dist / 'images' / 'electrician').exists())
        self.assertFalse((dist / 'images' / 'serralheria').exists())
        self.assertFalse((dist / 'images' / 'climatizacao').exists())
        self.assertFalse((dist / 'images' / 'chaveiros').exists())


class ToldosProfileTests(unittest.TestCase):
    def test_profile_is_valid_and_defaults_are_minimal(self):
        prof = quick.profile('toldos')
        self.assertEqual(prof['segment']['id'], 'toldos')
        self.assertEqual(prof['segment']['default_services'], ['retractable-awnings', 'fixed-awnings', 'polycarbonate-roofs', 'gutters'])
        self.assertTrue(set(prof['segment']['default_services']) <= set(prof['catalog']))
        self.assertRegex(prof['segment']['default_theme_color'], r'^#[0-9a-f]{6}$')
        for path in prof['catalog'].values():
            self.assertRegex(path, r'^/[a-z0-9-]+$')
            self.assertNotRegex(path, r'awning|retractable|fixed|polycarbonate|roof|gutter|flashing|repair|cleaning')
        self.assertFalse(set(prof['catalog']) & set(quick.profile('electrician')['catalog']))
        self.assertFalse(set(prof['catalog']) & set(quick.profile('serralheria')['catalog']))
        self.assertFalse(set(prof['catalog']) & set(quick.profile('climatizacao')['catalog']))
        self.assertFalse(set(prof['catalog']) & set(quick.profile('chaveiros')['catalog']))
        self.assertFalse(set(prof['catalog']) & set(quick.profile('vidracaria')['catalog']))

    def test_preset_covers_catalog_without_invented_claims(self):
        text = (quick.profile('toldos')['folder'] / 'preset.js').read_text()
        for service_id in quick.profile('toldos')['catalog']:
            self.assertIn("'%s':" % service_id, text)
        for term in ('projetos realizados', 'garantia', 'norma', 'impermeabil', 'resistên', 'vedaç', 'infiltraç', '24h', '24 horas', 'certificad', 'R$', 'autorizada', 'emergência', 'emergencia', 'urgên', 'imediat', 'ligar agora'):
            with self.subTest(term=term):
                self.assertNotIn(term, text.lower())

    def test_stock_photos_are_free_and_labelled_illustrative(self):
        folder = quick.profile('toldos')['folder']
        for item in json.loads((folder / 'stock-images.json').read_text()):
            self.assertEqual(item['license'], 'https://unsplash.com/license')
            self.assertNotIn('plus.unsplash.com', item['image'])
            self.assertTrue((ENGINE_PUBLIC / item['file']).exists())
        for alt in re.findall(r"alt: '([^']+)'", (folder / 'preset.js').read_text()):
            self.assertIn('imagem ilustrativa', alt)

    def test_toldos_site_uses_its_own_build_and_defaults(self):
        with tempfile.TemporaryDirectory() as folder, patch.object(quick.subprocess, 'run', side_effect=AssertionError('Unexpected build')):
            home = quick.create({'name': 'Toldos Teste', 'phone': '(14) 99712-3456', 'city': 'Bauru', 'state': 'SP', 'template': 'toldos'}, folder)
            site = Path(home['site'])
            business = (site / 'business.js').read_text()
            self.assertIn('#c2410c', business)
            for service_id in quick.profile('toldos')['segment']['default_services']:
                self.assertIn(service_id, business)
            for other in ('ev-charging', 'metal-gates', 'split-installation', 'door-opening', 'metal-roofs', 'pergolas', 'flashing', 'gutter-repair', 'gutter-cleaning'):
                self.assertNotIn(other, business)
            self.assertNotIn('eletricista', (site / 'index.html').read_text().lower())
            self.assertFalse((site / 'images' / 'electrician').exists())
            self.assertFalse((site / 'images' / 'serralheria').exists())
            self.assertFalse((site / 'images' / 'climatizacao').exists())
            self.assertFalse((site / 'images' / 'chaveiros').exists())
            self.assertFalse((site / 'images' / 'vidracaria').exists())

    def test_other_segments_ids_are_rejected_for_toldos(self):
        for bad in ('ev-charging', 'metal-gates', 'split-installation', 'door-opening'):
            with self.assertRaisesRegex(ValueError, 'enabled_services'):
                quick.validate({'name': 'X', 'phone': '123456789', 'template': 'toldos', 'enabled_services': [bad]})

    def test_toldos_build_does_not_ship_other_segments(self):
        dist = quick.profile('toldos')['dist']
        text = '\n'.join(p.read_text(errors='ignore') for p in dist.rglob('*') if p.suffix in ('.js', '.html', '.css'))
        for term in ('Eletricista', 'Quadro de distribuição', 'Portões de ferro', '/images/electrician', '/images/serralheria', '/images/climatizacao', '/images/chaveiros', '/images/vidracaria'):
            with self.subTest(term=term):
                self.assertNotIn(term, text)
        self.assertFalse((dist / 'images' / 'electrician').exists())
        self.assertFalse((dist / 'images' / 'serralheria').exists())
        self.assertFalse((dist / 'images' / 'climatizacao').exists())
        self.assertFalse((dist / 'images' / 'chaveiros').exists())
        self.assertFalse((dist / 'images' / 'vidracaria').exists())

    def test_service_groups_stay_independent(self):
        catalog = quick.profile('toldos')['catalog']
        text = (quick.profile('toldos')['folder'] / 'preset.js').read_text()
        groups = {'awnings': ('retractable-awnings', 'fixed-awnings'), 'roofs': ('polycarbonate-roofs', 'metal-roofs', 'pergolas'), 'gutters': ('gutters', 'flashing', 'gutter-repair', 'gutter-cleaning')}
        self.assertEqual(set(sum(groups.values(), ())), set(catalog))
        for ids in groups.values():
            quick.validate({'name': 'X', 'phone': '123456789', 'template': 'toldos', 'enabled_services': list(ids)})
        for term in ('calha', 'toldo'):
            for service_id in groups['roofs']:
                block = text.split("'%s': {" % service_id)[1].split('\n    },')[0].split('\n', 2)[2].lower()  # skip the image path line
                with self.subTest(service=service_id, term=term):
                    self.assertNotIn(term, block)


class DedetizacaoProfileTests(unittest.TestCase):
    OTHERS = ('electrician', 'serralheria', 'climatizacao', 'chaveiros', 'vidracaria', 'toldos')

    def test_profile_is_valid_and_defaults_are_minimal(self):
        prof = quick.profile('dedetizacao')
        self.assertEqual(prof['segment']['id'], 'dedetizacao')
        self.assertEqual(prof['segment']['default_services'], ['pest-control', 'cockroaches-ants', 'drain-unclogging', 'sewer-unclogging'])
        self.assertTrue(set(prof['segment']['default_services']) <= set(prof['catalog']))
        self.assertRegex(prof['segment']['default_theme_color'], r'^#[0-9a-f]{6}$')
        for path in prof['catalog'].values():
            self.assertRegex(path, r'^/[a-z0-9-]+$')
            self.assertNotRegex(path, r'pest|control|cockroach|ants|termite|rodent|drain|sewer|grease|storm|unclog')
        for other in self.OTHERS:
            self.assertFalse(set(prof['catalog']) & set(quick.profile(other)['catalog']))

    def test_preset_covers_catalog_without_invented_claims(self):
        text = (quick.profile('dedetizacao')['folder'] / 'preset.js').read_text()
        for service_id in quick.profile('dedetizacao')['catalog']:
            self.assertIn("'%s':" % service_id, text)
        for term in ('projetos realizados', 'garantia', 'norma', 'anvisa', 'licen', 'certificad', 'R$', 'autorizada', 'emergência', 'emergencia', 'urgên', 'imediat', 'ligar agora', '24h', '24 horas',
                     'elimina', '100%', 'sem cheiro', 'inodor', 'seguro para', 'não tóxic', 'nao toxic', 'aprovado', 'definitiv', 'sem resíduo', 'ecológic'):
            with self.subTest(term=term):
                self.assertNotIn(term, text.lower())

    def test_stock_photos_are_free_and_labelled_illustrative(self):
        folder = quick.profile('dedetizacao')['folder']
        for item in json.loads((folder / 'stock-images.json').read_text()):
            self.assertEqual(item['license'], 'https://unsplash.com/license')
            self.assertNotIn('plus.unsplash.com', item['image'])
            self.assertTrue((ENGINE_PUBLIC / item['file']).exists())
        for alt in re.findall(r"alt: '([^']+)'", (folder / 'preset.js').read_text()):
            self.assertIn('imagem ilustrativa', alt)

    def test_dedetizacao_site_uses_its_own_build_and_defaults(self):
        with tempfile.TemporaryDirectory() as folder, patch.object(quick.subprocess, 'run', side_effect=AssertionError('Unexpected build')):
            home = quick.create({'name': 'Pragas Teste', 'phone': '(14) 99712-3456', 'city': 'Bauru', 'state': 'SP', 'template': 'dedetizacao'}, folder)
            site = Path(home['site'])
            business = (site / 'business.js').read_text()
            self.assertIn('#15803d', business)
            for service_id in quick.profile('dedetizacao')['segment']['default_services']:
                self.assertIn(service_id, business)
            for other in ('ev-charging', 'metal-gates', 'split-installation', 'door-opening', 'termites', 'rodents', 'grease-trap', 'storm-drains'):
                self.assertNotIn(other, business)
            self.assertNotIn('eletricista', (site / 'index.html').read_text().lower())
            for other in self.OTHERS:
                self.assertFalse((site / 'images' / other).exists())

    def test_other_segments_ids_are_rejected_for_dedetizacao(self):
        for bad in ('ev-charging', 'metal-gates', 'split-installation', 'door-opening', 'gutters'):
            with self.assertRaisesRegex(ValueError, 'enabled_services'):
                quick.validate({'name': 'X', 'phone': '123456789', 'template': 'dedetizacao', 'enabled_services': [bad]})

    def test_dedetizacao_build_does_not_ship_other_segments(self):
        dist = quick.profile('dedetizacao')['dist']
        text = '\n'.join(p.read_text(errors='ignore') for p in dist.rglob('*') if p.suffix in ('.js', '.html', '.css'))
        for term in ('Eletricista', 'Quadro de distribuição', 'Portões de ferro', 'Toldos retráteis', *('/images/' + o for o in self.OTHERS)):
            with self.subTest(term=term):
                self.assertNotIn(term, text)
        for other in self.OTHERS:
            self.assertFalse((dist / 'images' / other).exists())

    def test_other_builds_do_not_ship_dedetizacao(self):
        for other in self.OTHERS:
            self.assertFalse((quick.profile(other)['dist'] / 'images' / 'dedetizacao').exists(), other)

    def test_service_groups_stay_independent(self):
        catalog = quick.profile('dedetizacao')['catalog']
        text = (quick.profile('dedetizacao')['folder'] / 'preset.js').read_text()
        groups = {'pests': ('pest-control', 'cockroaches-ants', 'termites', 'rodents'), 'drains': ('drain-unclogging', 'sewer-unclogging', 'grease-trap', 'storm-drains')}
        self.assertEqual(set(sum(groups.values(), ())), set(catalog))
        for ids in groups.values():
            quick.validate({'name': 'X', 'phone': '123456789', 'template': 'dedetizacao', 'enabled_services': list(ids)})
        forbidden = {'pests': ('entupi', 'esgoto', 'ralo'), 'drains': ('praga', 'inseto', 'barata', 'formiga', 'cupim', 'rato', 'roedor', 'dedetiza')}
        for group, ids in groups.items():
            for service_id in ids:
                block = text.split("'%s': {" % service_id)[1].split('\n    },')[0].lower()
                block = '\n'.join(l for l in block.split('\n') if not l.strip().startswith(('image:', 'alt:')))  # photo path and alt are not copy
                for term in forbidden[group]:
                    with self.subTest(service=service_id, term=term):
                        self.assertNotIn(term, block)


class HeroProofTests(unittest.TestCase):
    def test_payment_is_a_pill_alone_and_joins_the_bar_only_with_another_fact(self):
        src = (Path(__file__).parents[1] / 'templates/electrician/src/pages/HomePage.jsx').read_text()
        self.assertIn('function proofFacts()', src)
        self.assertIn('payPill', src)
        self.assertIn('base.length && pay', src)


class ProcessStackTests(unittest.TestCase):
    ENGINE = Path(__file__).parents[1] / 'templates/electrician'

    def test_every_profile_has_three_complete_steps(self):
        for seg in ('electrician', 'serralheria', 'climatizacao', 'chaveiros', 'vidracaria', 'toldos', 'dedetizacao'):
            text = (quick.profile(seg)['folder'] / 'preset.js').read_text()
            block = text.split('process: [')[1].split('],')[0]
            with self.subTest(segment=seg):
                self.assertEqual(len(re.findall(r"title: '", block)), 3)
                self.assertEqual(len(re.findall(r"text: '", block)), 3)

    def test_gsap_is_loaded_on_demand_only(self):
        src = self.ENGINE / 'src'
        stack = (src / 'components/ProcessStack.jsx').read_text()
        self.assertIn("import('gsap')", stack)
        self.assertIn("import('gsap/ScrollTrigger')", stack)
        self.assertIn('prefers-reduced-motion', stack)
        for path in src.rglob('*.js*'):
            self.assertNotRegex(path.read_text(), r"^import .* from 'gsap", msg=str(path))  # never a static import
        self.assertIn('ProcessStack', (src / 'pages/HomePage.jsx').read_text())

    def test_step_photos_come_from_enabled_services_only(self):
        stack = (self.ENGINE / 'src/components/ProcessStack.jsx').read_text()
        self.assertIn('SERVICES.filter', stack)
        self.assertIn('imagem ilustrativa', stack)


if __name__=='__main__':unittest.main()
