import importlib.util
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location('brand_color', Path(__file__).parents[1] / 'tools/brand_color.py')
brand = importlib.util.module_from_spec(spec)
spec.loader.exec_module(brand)


class BrandColorTests(unittest.TestCase):
    def test_css_variable_beats_neutral_theme_color(self):
        found = brand.detect('<meta name="theme-color" content="#ffffff"><style>:root{--primary-color:#e8590c}a{color:#333}</style>')
        self.assertEqual((found['color'], found['source'], found['confidence']), ('#e8590c', 'css-var', 'alta'))

    def test_theme_color_meta_is_high_confidence_when_chromatic(self):
        found = brand.detect('<meta name="theme-color" content="#0d6efd">')
        self.assertEqual((found['color'], found['confidence']), ('#0d6efd', 'alta'))

    def test_repeated_chromatic_color_in_stylesheet_is_a_candidate(self):
        found = brand.detect('<p>x</p>', ['.a{color:#c81e1e}.b{background:rgb(200,30,30)}.c{border-color:#c81e1e}.d{color:#222}'])
        self.assertEqual(found['color'], '#c81e1e')
        self.assertIn(found['confidence'], ('média', 'baixa'))

    def test_neutrals_and_nothing_return_none_so_the_default_applies(self):
        self.assertIsNone(brand.detect('<style>a{color:#444;background:#f5f5f5;border:1px solid #000}</style>'))
        self.assertIsNone(brand.detect(''))

    def test_stylesheet_discovery_is_bounded(self):
        html = ''.join(f'<link rel="stylesheet" href="/s{i}.css">' for i in range(6))
        self.assertEqual(brand.stylesheet_urls(html, 'https://example.com/a/'), [f'https://example.com/s{i}.css' for i in range(3)])


if __name__ == '__main__':
    unittest.main()
