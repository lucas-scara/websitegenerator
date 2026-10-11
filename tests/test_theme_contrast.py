import colorsys
import json
from pathlib import Path
import shutil
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / 'templates/electrician'


def lum(c):
    f = lambda n: (n / 255) / 12.92 if n / 255 <= 0.04045 else (((n / 255) + 0.055) / 1.055) ** 2.4
    return 0.2126 * f(c[0]) + 0.7152 * f(c[1]) + 0.0722 * f(c[2])


def contrast(a, b):
    hi, lo = sorted((lum(a), lum(b)), reverse=True)
    return (hi + 0.05) / (lo + 0.05)


def grid():
    for h in range(0, 360, 10):
        for l in (0.15, 0.3, 0.45, 0.6, 0.75, 0.88):
            r, g, b = colorsys.hls_to_rgb(h / 360, l, 0.85)
            yield '#%02x%02x%02x' % (round(r * 255), round(g * 255), round(b * 255))


@unittest.skipUnless(shutil.which('node'), 'node is required')
class ThemeContrastTests(unittest.TestCase):
    def test_every_brand_color_yields_legible_pairs(self):
        colors = list(grid()) + json.loads((TEMPLATE / 'segment.json').read_text())['default_theme_color'].split()
        script = "import {deriveTheme} from './src/themeMath.js'; console.log(JSON.stringify(JSON.parse(process.argv[1]).map(h=>[h,deriveTheme(h)])))"
        out = subprocess.run(['node', '--input-type=module', '-e', script, json.dumps(colors)], cwd=TEMPLATE, capture_output=True, text=True, check=True).stdout
        for hex_, t in json.loads(out):
            on = (0, 0, 0) if t['onPrimary'] == '#000000' else (255, 255, 255)
            with self.subTest(color=hex_):
                self.assertGreaterEqual(contrast(on, t['rgb']), 4.5, 'text on the brand color (buttons)')
                self.assertGreaterEqual(contrast(t['dark'], (247, 249, 252)), 4.5, 'primary-dark text on the light background')
                self.assertGreaterEqual(contrast((255, 255, 255), t['dark']), 4.5, 'white text on primary-dark (button hover)')
                self.assertGreaterEqual(contrast(t['light'], (11, 18, 32)), 7, 'primary-light text on the dark sections')


if __name__ == '__main__':
    unittest.main()
