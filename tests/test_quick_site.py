import importlib.util
import json
from pathlib import Path
import re
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

    def test_services_are_explicit_validated_and_isolated(self):
        base = {'name': 'Empresa', 'phone': '123456789'}
        self.assertEqual(quick.validate(base)[1]['enabled_services'], [])
        for enabled in ('ev-charging', ['unknown'], ['ev-charging', 'ev-charging'], [1]):
            with self.assertRaisesRegex(ValueError, 'enabled_services'):
                quick.validate({**base, 'enabled_services': enabled})
        with tempfile.TemporaryDirectory() as folder:
            a = quick.create({**base, 'enabled_services': ['electrical-repairs']}, folder)
            b = quick.create({**base, 'enabled_services': ['electrical-repairs', 'ev-charging']}, folder)
            self.assertEqual(a['business']['enabled_services'], ['electrical-repairs'])
            self.assertEqual(b['business']['enabled_services'], ['electrical-repairs', 'ev-charging'])
            self.assertNotIn('ev-charging', (Path(a['site'])/'business.js').read_text())
            self.assertIn('ev-charging', (Path(b['site'])/'business.js').read_text())

    def test_catalog_covers_every_service_page(self):
        content = quick.TEMPLATES['electrician']['path'] / 'src/content'
        paths = set()
        for page in content.glob('*.js'):
            match = re.search(r'"path": "(/[^\"]+)"', page.read_text())
            self.assertIsNotNone(match, page.name)
            paths.add(match.group(1))
        catalog = json.loads((quick.TEMPLATES['electrician']['path'] / 'services.json').read_text())
        self.assertEqual(set(catalog.values()), paths)

if __name__=='__main__':unittest.main()
