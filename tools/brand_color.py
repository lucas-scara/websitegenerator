#!/usr/bin/env python3
"""Suggest a brand color for `theme_color` from pages the workflow already scraped.

Zero Firecrawl credits: it reads the cached HTML and, optionally, up to three linked
stylesheets with a plain HTTP GET (SSRF-safe fetch from site_assets). The result is a
*candidate*: the agent confirms it against the screenshot or falls back to the default.
"""
import argparse
import colorsys
import json
from pathlib import Path
import re
import sys
from urllib.parse import urljoin

sys.path.insert(0, str(Path(__file__).resolve().parent))

HEX = re.compile(r'#([0-9a-fA-F]{6}|[0-9a-fA-F]{3})\b')
RGB = re.compile(r'rgba?\(\s*(\d{1,3})\s*[, ]\s*(\d{1,3})\s*[, ]\s*(\d{1,3})')
VAR = re.compile(r'--[\w-]*?(?:primary|brand|main|accent|theme)[\w-]*\s*:\s*([^;}\n]+)', re.I)
META = re.compile(r'<meta[^>]+name=["\'](?:theme-color|msapplication-TileColor)["\'][^>]*>', re.I)
MASK = re.compile(r'<link[^>]+rel=["\']mask-icon["\'][^>]*>', re.I)
CONTENT = re.compile(r'(?:content|color)=["\']([^"\']+)["\']', re.I)
STYLE = re.compile(r'<style[^>]*>(.*?)</style>|style=["\']([^"\']*)["\']|(?:fill|stroke)=["\']([^"\']+)["\']', re.I | re.S)
SHEETS = re.compile(r'<link[^>]+rel=["\']stylesheet["\'][^>]*>', re.I)
HREF = re.compile(r'href=["\']([^"\']+)["\']', re.I)


def parse_colors(text):
    found = []
    for m in HEX.finditer(text):
        h = m.group(1)
        h = ''.join(c * 2 for c in h) if len(h) == 3 else h
        found.append(tuple(int(h[i:i + 2], 16) for i in (0, 2, 4)))
    for m in RGB.finditer(text):
        rgb = tuple(int(g) for g in m.groups())
        if max(rgb) <= 255:
            found.append(rgb)
    return found


def usable(rgb):
    """Chromatic and neither near-white nor near-black: neutrals are page chrome, not brand."""
    h, l, s = colorsys.rgb_to_hls(*(c / 255 for c in rgb))
    return s >= 0.28 and 0.12 <= l <= 0.88


def to_hex(rgb):
    return '#%02x%02x%02x' % rgb


def detect(html, sheets=()):
    """Return {'color', 'source', 'confidence'} or None. `sheets` are extra CSS texts."""
    score, sources = {}, {}  # sources keeps the strongest signal seen for each color

    def add(rgb, weight, source):
        if usable(rgb):
            score[rgb] = score.get(rgb, 0) + weight
            if rgb not in sources or weight > sources[rgb][0]:
                sources[rgb] = (weight, source)

    for tag in META.findall(html) + MASK.findall(html):
        m = CONTENT.search(tag)
        for rgb in parse_colors(m.group(1)) if m else ():
            add(rgb, 4, 'theme-color')
    css = [html] + list(sheets)
    for text in css:
        for m in VAR.finditer(text):
            for rgb in parse_colors(m.group(1))[:1]:
                add(rgb, 5, 'css-var')
    inline = '\n'.join(g for m in STYLE.finditer(html) for g in m.groups() if g) + '\n' + '\n'.join(sheets)
    counts = {}
    for rgb in parse_colors(inline):
        counts[rgb] = counts.get(rgb, 0) + 1
    for rgb, n in counts.items():
        add(rgb, min(n, 6) * 0.5, 'frequency')
    if not score:
        return None
    best = max(score, key=lambda c: (score[c], colorsys.rgb_to_hls(*(x / 255 for x in c))[2]))
    source = sources[best][1]
    confidence = 'alta' if source in ('css-var', 'theme-color') and score[best] >= 4 else 'média' if score[best] >= 1.5 else 'baixa'
    return {'color': to_hex(best), 'source': source, 'confidence': confidence}


def stylesheet_urls(html, base, limit=3):
    urls = []
    for tag in SHEETS.findall(html):
        m = HREF.search(tag)
        if m and not m.group(1).startswith('data:'):
            urls.append(urljoin(base, m.group(1)))
    return urls[:limit]


def fetch_sheets(html, base):
    from site_assets import fetch  # lazy: keeps detect() importable without network code
    sheets = []
    for url in stylesheet_urls(html, base):
        try:
            raw, _, _ = fetch(url, limit=1024 * 1024, timeout=10)
            sheets.append(raw.decode('utf-8', 'ignore'))
        except (ValueError, OSError):
            continue  # a missing stylesheet only lowers confidence
    return sheets


def from_manifest(manifest, with_sheets=True):
    root = Path(manifest).parent
    best = None
    for page in json.loads(Path(manifest).read_text())['pages']:
        saved = json.loads((root / page['file']).read_text())
        data = saved['data']
        html = data.get('rawHtml') or data.get('html') or ''
        found = detect(html, fetch_sheets(html, saved['source_url']) if with_sheets else ())
        rank = {'alta': 3, 'média': 2, 'baixa': 1}
        if found and (not best or rank[found['confidence']] > rank[best['confidence']]):
            best = {**found, 'page': saved['source_url']}
    return best


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('manifest', type=Path, help='scrape-manifest.json written by site_assets.py scrape')
    p.add_argument('--no-stylesheets', action='store_true', help='Use only the cached HTML')
    args = p.parse_args()
    print(json.dumps(from_manifest(args.manifest, not args.no_stylesheets), ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
