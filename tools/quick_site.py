#!/usr/bin/env python3
"""Create a website from a prepared industry template, without installing or building per business."""
import argparse
import hashlib
import html
import json
import math
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import time
import unicodedata
import uuid

ROOT = Path(__file__).resolve().parents[1]
TEMPLATES = {'electrician': {'name': 'Eletricista · design base', 'path': ROOT / 'templates/electrician'}}
SERVICE_CATALOG = json.loads((TEMPLATES['electrician']['path'] / 'service-catalog.json').read_text())
SEGMENT = json.loads((TEMPLATES['electrician']['path'] / 'segment.json').read_text())
DEFAULT_THEME_COLOR = SEGMENT['default_theme_color']
UF = set('AC AL AP AM BA CE DF ES GO MA MT MS MG PA PB PR PE PI RJ RN RS RO RR SC SP SE TO'.split())


def whatsapp_number(raw):
    """Return 55+DDD+number for Brazilian phones (or the digits of an explicit +international number), else ''."""
    value = str(raw or '').strip()
    digits = re.sub(r'\D', '', value)
    if value.startswith('+'):
        return digits if 10 <= len(digits) <= 15 else ''
    digits = digits.lstrip('0')
    if digits.startswith('55') and len(digits) in (12, 13):
        return digits
    return '55' + digits if len(digits) in (10, 11) else ''


def valid_cnpj(value):
    d = [int(c) for c in re.sub(r'\D', '', value)]
    if len(d) != 14 or len(set(d)) == 1:
        return False
    for size in (12, 13):
        weights = list(range(size - 7, 1, -1)) + list(range(9, 1, -1))
        check = sum(a * b for a, b in zip(d[:size], weights)) % 11
        if d[size] != (0 if check < 2 else 11 - check):
            return False
    return True


def _text(data, key, limit):
    value = data.get(key, '')
    if not isinstance(value, str) or len(value) > limit or any(ord(c) < 32 for c in value):
        raise ValueError(f'Invalid {key}')
    return value.strip()


def _https(value, key):
    if not isinstance(value, str) or not re.fullmatch(r'https://[^\s<>"]{4,300}', value):
        raise ValueError(f'{key} must be an https URL')
    return value


def fingerprint(template):
    digest = hashlib.sha256()
    for p in sorted(template.rglob('*')):
        if not p.is_file() or any(x in p.relative_to(template).parts for x in ('node_modules', 'dist', '.vercel')):
            continue
        digest.update(str(p.relative_to(template)).encode())
        digest.update(p.read_bytes())
    return digest.hexdigest()


def prepare(template='electrician'):
    source = TEMPLATES[template]['path']
    if not (source / 'node_modules').exists():
        subprocess.run(['npm', 'ci', '--no-audit', '--no-fund'], cwd=source, check=True)
    subprocess.run(['npm', 'run', 'lint'], cwd=source, check=True)
    subprocess.run(['npm', 'run', 'build'], cwd=source, check=True)
    (source / 'dist/.prepared.json').write_text(json.dumps({'fingerprint': fingerprint(source)}))


def validate(data):
    if not isinstance(data, dict):
        raise ValueError('Business details must be an object')
    template = data.get('template', 'electrician')
    if template not in TEMPLATES:
        raise ValueError('Choose an available template: electrician')
    color = data.get('theme_color', DEFAULT_THEME_COLOR)
    if color == '':  # not detected: the segment default applies
        color = DEFAULT_THEME_COLOR
    if not isinstance(color, str) or not re.fullmatch(r'#[0-9a-fA-F]{6}', color):
        raise ValueError('Theme color must be a six-digit hex color, e.g. #2563eb')
    # Key absent: the segment's basic services apply. An explicit list (even empty) is honored as given.
    services = data['enabled_services'] if data.get('enabled_services') is not None else list(SEGMENT['default_services'])
    if not isinstance(services, list) or any(not isinstance(item, str) or item not in SERVICE_CATALOG for item in services) or len(services) != len(set(services)):
        raise ValueError('enabled_services must be a list of unique service IDs from service-catalog.json')
    result = {'theme_color': color.lower(), 'enabled_services': services}
    for key in ('name', 'phone', 'email', 'street', 'city', 'zip', 'service_area', 'hours', 'instagram'):
        result[key] = _text(data, key, 180)
    result['about'] = _text(data, 'about', 1200)
    if not result['name']:
        raise ValueError('Business name is required')
    if result['phone'] and not re.fullmatch(r'\+?[0-9 () .-]{5,40}', result['phone']):
        raise ValueError('Use a phone number with digits, spaces, +, brackets or dashes')
    if result['email'] and not re.fullmatch(r'[^\s@<>"\\]+@[^\s@<>"\\]+\.[^\s@<>"\\]+', result['email']):
        raise ValueError('Enter a valid email address')
    state = _text(data, 'state', 2).upper()
    if state and state not in UF:
        raise ValueError('state must be a Brazilian UF, e.g. SP')
    result['state'] = state
    if result['zip'] and not re.fullmatch(r'\d{5}-?\d{3}', result['zip']):
        raise ValueError('zip must be a CEP like 17010-000')
    cnpj = _text(data, 'cnpj', 18)
    if cnpj and not valid_cnpj(cnpj):
        raise ValueError('Invalid CNPJ')
    result['cnpj'] = cnpj
    # The public phone is presumed to be WhatsApp (owner decision); `whatsapp: false` opts out.
    whatsapp = data.get('whatsapp')
    if whatsapp is False:
        result['whatsapp'] = False
    elif whatsapp not in (None, ''):
        if not isinstance(whatsapp, str) or not whatsapp_number(whatsapp):
            raise ValueError('Invalid whatsapp number')
        result['whatsapp'] = whatsapp_number(whatsapp)
    else:
        result['whatsapp'] = whatsapp_number(result['phone'])
    if not result['phone'] and not result['email'] and not result['whatsapp']:
        raise ValueError('Provide a phone number, WhatsApp or email address')
    methods = data.get('payment_methods', [])
    if not isinstance(methods, list) or len(methods) > 8 or any(not isinstance(m, str) or not 0 < len(m.strip()) <= 40 for m in methods):
        raise ValueError('payment_methods must be a list of up to 8 short labels')
    result['payment_methods'] = [m.strip() for m in methods]
    year = data.get('founded_year')
    if year is not None and (not isinstance(year, int) or isinstance(year, bool) or not 1900 <= year <= time.localtime().tm_year):
        raise ValueError('Invalid founded_year')
    result['founded_year'] = year
    rating = data.get('google_rating')
    if rating is not None:
        if isinstance(rating, bool) or not isinstance(rating, (int, float)) or not 1 <= rating <= 5:
            raise ValueError('google_rating must be between 1 and 5')
        count = data.get('google_reviews_count', 0)
        if isinstance(count, bool) or not isinstance(count, int) or count < 0:
            raise ValueError('Invalid google_reviews_count')
        result.update(google_rating=rating, google_reviews_count=count, google_reviews_url=_https(data.get('google_reviews_url'), 'google_reviews_url'))
    reviews = data.get('reviews', [])
    if not isinstance(reviews, list) or len(reviews) > 6:
        raise ValueError('reviews must be a list of up to 6 items')
    clean = []
    for review in reviews:
        if not isinstance(review, dict):
            raise ValueError('Invalid review')
        item = {'author': _text(review, 'author', 80), 'text': _text(review, 'text', 600), 'source_url': _https(review.get('source_url'), 'review source_url')}
        if not item['author'] or not item['text']:
            raise ValueError('Reviews need author and text')
        if review.get('rating') is not None:
            if isinstance(review['rating'], bool) or not isinstance(review['rating'], (int, float)) or not 1 <= review['rating'] <= 5:
                raise ValueError('Invalid review rating')
            item['rating'] = review['rating']
        clean.append(item)
    result['reviews'] = clean
    preview = data.get('preview', True)
    if not isinstance(preview, bool):
        raise ValueError('preview must be true or false')
    result['preview'] = preview
    return template, {k: v for k, v in result.items() if v or k in ('enabled_services', 'preview') or v is False}


def _luminance(rgb):
    lin = [(c / 255 / 12.92) if c / 255 <= 0.04045 else ((c / 255 + 0.055) / 1.055) ** 2.4 for c in rgb]
    return 0.2126 * lin[0] + 0.7152 * lin[1] + 0.0722 * lin[2]


def _mix(rgb, target, amount):
    return [math.floor(c + (t - c) * amount + 0.5) for c, t in zip(rgb, target)]


def render_favicon(theme_color):
    """Same mark as components/Logo.jsx (tile gradient, white house, light bolt), colored like the page theme.
    Mirrors deriveTheme() in src/themeMath.js so the favicon, the logo and the theme never disagree."""
    rgb = [int(theme_color[i:i + 2], 16) for i in (1, 3, 5)]
    dark = rgb
    while _luminance(dark) > 0.16:
        dark = _mix(dark, [0, 0, 0], 0.1)
    light = rgb
    while _luminance(light) < 0.55:
        light = _mix(light, [255, 255, 255], 0.12)
    hexa = lambda c: '#%02x%02x%02x' % tuple(c)
    return ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 48 48">'
            f'<defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{hexa(rgb)}"/><stop offset="1" stop-color="{hexa(dark)}"/></linearGradient></defs>'
            '<rect width="48" height="48" rx="13" fill="url(#g)"/>'
            '<path d="M11 23.5 24 12l13 11.5M14 21.5V37h20V21.5" fill="none" stroke="#fff" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round"/>'
            f'<path d="M25.6 19.5 20 28.5h5l-1.6 8L30 26.5h-5.2z" fill="{hexa(light)}"/></svg>\n')


def render_head(page, business):
    """Static <title>/description/OG per business: link previews (WhatsApp, e-mail) never run JavaScript."""
    city = business.get('city', '')
    suffix = '' if city else '_no_city'
    values = {'noun': SEGMENT['noun'], 'activity': SEGMENT['activity'], 'city': city, 'name': business['name']}
    title = SEGMENT['seo_title' + suffix].format(**values)
    description = SEGMENT['seo_description' + suffix].format(**values)
    esc = lambda value: html.escape(value, quote=True)
    page = re.sub(r'<title>.*?</title>', lambda _: f'<title>{esc(title)}</title>', page, count=1, flags=re.S)
    for pattern, value in ((r'name="description"', description), (r'property="og:title"', title), (r'property="og:description"', description), (r'property="og:site_name"', business['name'])):
        page = re.sub(r'(<meta ' + pattern + r' content=")[^"]*(")', lambda m: m.group(1) + esc(value) + m.group(2), page, count=1)
    page = re.sub(r'(<meta name="theme-color" content=")[^"]*(")', lambda m: m.group(1) + business.get('theme_color', DEFAULT_THEME_COLOR) + m.group(2), page, count=1)
    return page.replace('Your Company', esc(business['name']))


def create(data, output_root=None):
    started = time.perf_counter()
    template, business = validate(data)
    source = TEMPLATES[template]['path']
    cache = source / 'dist'
    stamp = cache / '.prepared.json'
    if not stamp.exists() or json.loads(stamp.read_text())['fingerprint'] != fingerprint(source):
        raise ValueError('Template needs preparation. Run: python3 tools/quick_site.py prepare')
    parent = Path(output_root) if output_root else ROOT / 'runs/quick'
    parent.mkdir(parents=True, exist_ok=True)
    ascii_name = unicodedata.normalize('NFKD', business['name']).encode('ascii', 'ignore').decode().lower()
    slug = re.sub(r'[^a-z0-9]+', '-', ascii_name).strip('-')[:48] or 'business'
    identifier = slug + '-' + uuid.uuid4().hex[:8]
    destination = parent / identifier
    staging = Path(tempfile.mkdtemp(prefix='.creating-', dir=parent))
    try:
        site = staging / 'site'
        shutil.copytree(cache, site, ignore=shutil.ignore_patterns('.prepared.json'))
        # Data lives in its own JavaScript file. JSON escaping prevents source injection.
        (site / 'business.js').write_text('window.WEBSITE_BUSINESS = ' + json.dumps(business, ensure_ascii=True) + ';\n')
        (site / 'favicon.svg').write_text(render_favicon(business.get('theme_color', DEFAULT_THEME_COLOR)))
        (site / 'index.html').write_text(render_head((site / 'index.html').read_text(), business))
        shutil.copyfile(source / 'vercel.json', site / 'vercel.json')
        shutil.copyfile(source / 'stock-images.json', staging / 'stock-images.json')
        result = {'id': identifier, 'template': template, 'business': business, 'site': str(destination / 'site'), 'seconds': round(time.perf_counter()-started, 3)}
        (staging / 'website.json').write_text(json.dumps(result, indent=2))
        staging.rename(destination)
        return result
    except Exception:
        shutil.rmtree(staging, ignore_errors=True)
        raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    p = commands.add_parser('prepare', help='Build the reusable template once after template edits')
    p.add_argument('--template', choices=TEMPLATES, default='electrician')
    commands.add_parser('templates')
    p = commands.add_parser('create', help='Generate a ready-to-host website')
    p.add_argument('--template', choices=TEMPLATES, default='electrician')
    p.add_argument('--name', required=True)
    p.add_argument('--theme-color', dest='theme_color', default=DEFAULT_THEME_COLOR, help='Brand color as #RRGGBB (default: segment default; see tools/brand_color.py)')
    p.add_argument('--enabled-service', dest='enabled_services', action='append', default=None, choices=SERVICE_CATALOG, help='Repeat for each verified service; omit to use the segment basic services')
    p.add_argument('--no-services', dest='no_services', action='store_true', help='Announce no specific services')
    for field in ('phone', 'email', 'street', 'city', 'state', 'zip', 'cnpj', 'hours', 'service_area', 'instagram', 'about', 'whatsapp'):
        p.add_argument('--' + field.replace('_', '-'), dest=field, default='')
    p.add_argument('--no-whatsapp', dest='whatsapp', action='store_false', help='The public phone does not use WhatsApp')
    p.add_argument('--payment-method', dest='payment_methods', action='append', default=[])
    p = commands.add_parser('batch', help='Generate websites from a JSON array of business details')
    p.add_argument('file', type=Path)
    args = vars(parser.parse_args())
    command = args.pop('command')
    try:
        if command == 'prepare': prepare(**args)
        elif command == 'templates': print(json.dumps({k: v['name'] for k, v in TEMPLATES.items()}, indent=2))
        elif command == 'create':
            if args.pop('no_services'): args['enabled_services'] = []
            print(json.dumps(create(args), indent=2))
        else:
            records = json.loads(args['file'].read_text())
            if not isinstance(records, list): raise ValueError('Batch file must contain a JSON array')
            for record in records: validate(record)
            print(json.dumps([create(record) for record in records], indent=2))
    except (ValueError, OSError, subprocess.CalledProcessError) as error:
        parser.exit(1, str(error) + '\n')

if __name__ == '__main__':
    main()
