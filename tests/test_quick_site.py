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
            'maintenance', 'ev-charging',
        })

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
