"""`sv brand import <domain> --client <Client>`: a real company's brand, good enough for a deck.

    logo     Brandfetch Logo Link (needs BRAND_FETCH, the Logo Link client id, in the env)
    colours  read from the company's own website: theme-color, CSS custom properties and
             the hex/rgb values its stylesheets use most, greys set aside
    fonts    the font-family its CSS names first; downloaded from Google Fonts when it is
             one, otherwise the closest Google family stands in (measurement needs a file)

Everything lands in ~/Servantium-Work/<Client>/_brand/<id>/ and NEVER in this repo:
Brandfetch's terms forbid caching their assets, and a customer's brand is not ours to
commit. The result is a starting point. Open brand.yaml, check the roles, and fix what
the heuristics got wrong before a customer sees it.
"""
import colorsys
import io
import os
import re
import urllib.parse
import urllib.request
from collections import Counter
from pathlib import Path

import yaml

from . import drive

UA = ('Mozilla/5.0 (Macintosh; Intel Mac OS X 14_0) AppleWebKit/537.36 (KHTML, like Gecko) '
      'Chrome/126.0 Safari/537.36')
GOOGLE_FONTS_RAW = 'https://raw.githubusercontent.com/google/fonts/main/ofl/{dir}/'
# Families we can always fetch: the stand-ins when a site uses a commercial face.
STAND_INS = {'serif': 'Source Serif 4', 'sans': 'Inter', 'display': 'Fraunces'}


def _get(url, *, referer=None, timeout=20):
    req = urllib.request.Request(url, headers={'User-Agent': UA, **({'Referer': referer} if referer else {})})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read(), r.headers.get('Content-Type', '')


# ── colour maths ─────────────────────────────────────────────────────────────
def _rgb(hx):
    hx = hx.lstrip('#')
    if len(hx) == 3:
        hx = ''.join(c * 2 for c in hx)
    return tuple(int(hx[i:i + 2], 16) for i in (0, 2, 4))


def _hex(rgb):
    return '#' + ''.join(f'{max(0, min(255, round(c))):02X}' for c in rgb)


def _lum(rgb):
    def ch(c):
        c /= 255
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = (ch(c) for c in rgb)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast(a, b):
    la, lb = sorted((_lum(_rgb(a)), _lum(_rgb(b))), reverse=True)
    return (la + 0.05) / (lb + 0.05)


def mix(a, b, t):
    ra, rb = _rgb(a), _rgb(b)
    return _hex(tuple(x + (y - x) * t for x, y in zip(ra, rb)))


def darken_to(hx, against, ratio):
    c = hx
    for _ in range(40):
        if contrast(c, against) >= ratio:
            return c
        c = mix(c, '#000000', 0.06)
    return c


def _sat(hx):
    r, g, b = (c / 255 for c in _rgb(hx))
    h, l, s = colorsys.rgb_to_hls(r, g, b)
    return s, l, h


# ── reading the site ─────────────────────────────────────────────────────────
HEX = re.compile(r'#([0-9a-fA-F]{6}|[0-9a-fA-F]{3})\b')
RGB = re.compile(r'rgba?\(\s*(\d{1,3})[ ,]+(\d{1,3})[ ,]+(\d{1,3})')
FAMILY = re.compile(r'font-family\s*:\s*([^;}{]+)', re.I)


def _site_css(domain):
    base = f'https://{domain}/'
    html, _ = _get(base)
    html = html.decode('utf-8', 'replace')
    css = [m for m in re.findall(r'<style[^>]*>(.*?)</style>', html, re.S | re.I)]
    css += re.findall(r'style="([^"]+)"', html)
    links = re.findall(r'<link[^>]+rel=["\']?stylesheet["\']?[^>]*>', html, re.I)
    hrefs = [re.search(r'href=["\']([^"\']+)', l) for l in links]
    for h in [h.group(1) for h in hrefs if h][:8]:
        try:
            body, _ = _get(urllib.parse.urljoin(base, h), referer=base)
            css.append(body.decode('utf-8', 'replace'))
        except Exception:
            continue
    theme = re.search(r'<meta[^>]+name=["\']theme-color["\'][^>]+content=["\']([^"\']+)', html, re.I)
    return html, '\n'.join(css), (theme.group(1) if theme else None)


def _palette(css, theme):
    count = Counter()
    for m in HEX.finditer(css):
        count[_hex(_rgb(m.group(0)))] += 1
    for m in RGB.finditer(css):
        count[_hex(tuple(int(x) for x in m.groups()))] += 1
    # Custom properties named like a brand colour count double: designers name what matters.
    for name, val in re.findall(r'--([\w-]*(?:primary|brand|accent|main)[\w-]*)\s*:\s*(#[0-9a-fA-F]{3,6})', css, re.I):
        count[_hex(_rgb(val))] += 25
    if theme and HEX.match(theme.strip()):
        count[_hex(_rgb(theme.strip()))] += 50
    chroma = [(c, n) for c, n in count.most_common() if _sat(c)[0] > 0.28 and 0.12 < _sat(c)[1] < 0.88]
    darks = [(c, n) for c, n in count.most_common() if _lum(_rgb(c)) < 0.035]
    return chroma, darks, count


def _fonts(css):
    seen = []
    for m in FAMILY.finditer(css):
        for fam in m.group(1).split(','):
            f = fam.strip().strip('"\'').strip()
            if f and not f.startswith('var(') and f.lower() not in (
                    'inherit', 'initial', 'sans-serif', 'serif', 'monospace', 'system-ui', '-apple-system',
                    'blinkmacsystemfont', 'segoe ui', 'arial', 'helvetica', 'helvetica neue', 'roboto mono',
                    'menlo', 'monaco', 'consolas', 'courier', 'courier new', 'sfmono-regular', 'sf mono',
                    'liberation mono', 'apple color emoji', 'segoe ui emoji', 'noto color emoji') \
                    and f not in seen:
                seen.append(f)
    return seen


def _google_font(family, dest):
    """Download a Google Fonts family's TTF from github.com/google/fonts. Returns filename or None."""
    d = re.sub(r'[^a-z0-9]', '', family.lower())
    api = f'https://api.github.com/repos/google/fonts/contents/ofl/{d}'
    try:
        import json
        listing = json.loads(_get(api)[0])
    except Exception:
        return None
    ttfs = [f['name'] for f in listing if f['name'].endswith('.ttf') and 'Italic' not in f['name']]
    pick = next((t for t in ttfs if '[' in t), None) or next((t for t in ttfs if 'Regular' in t), None) or (ttfs or [None])[0]
    if not pick:
        return None
    dest.mkdir(parents=True, exist_ok=True)
    (dest / pick).write_bytes(_get(GOOGLE_FONTS_RAW.format(dir=d) + urllib.parse.quote(pick))[0])
    lic = next((f['name'] for f in listing if f['name'] == 'OFL.txt'), None)
    if lic:
        (dest / lic).write_bytes(_get(GOOGLE_FONTS_RAW.format(dir=d) + lic)[0])
    return pick


def _family_name(path):
    from fontTools.ttLib import TTFont
    names = TTFont(str(path))['name']
    return str(names.getDebugName(16) or names.getDebugName(1))


def _install(path):
    """LibreOffice and Keynote render with installed fonts only."""
    target = Path.home() / 'Library' / 'Fonts' / path.name
    if not target.exists():
        target.write_bytes(path.read_bytes())


# ── logos ────────────────────────────────────────────────────────────────────
def _logo(domain, dest, *, icon=False):
    cid = os.environ.get('BRAND_FETCH')
    if not cid:
        return None
    url = f'https://cdn.brandfetch.io/{domain}{"/icon" if icon else ""}/w/800/h/400?c={cid}&fallback=404'
    try:
        body, ctype = _get(url, referer='https://servantium.com/')
    except Exception:
        return None
    if not ctype.startswith('image/'):
        return None
    from PIL import Image
    im = Image.open(io.BytesIO(body)).convert('RGBA')        # python-pptx rejects WEBP: store PNG
    out = dest / ('symbol.png' if icon else 'logo.png')
    im.save(out)
    return out


def _white_version(src, dest):
    """A light-ground logo recoloured to white for dark grounds. A logo that brings its
       own opaque tile is left alone: it already reads on any ground."""
    from PIL import Image
    im = Image.open(src).convert('RGBA')
    corners = [im.getpixel(p) for p in ((0, 0), (im.width - 1, 0), (0, im.height - 1), (im.width - 1, im.height - 1))]
    if all(c[3] > 250 for c in corners):
        return src
    white = Image.new('RGBA', im.size, (255, 255, 255, 0))
    white.putalpha(im.getchannel('A'))
    px = white.load()
    for y in range(im.height):
        for x in range(im.width):
            a = px[x, y][3]
            px[x, y] = (255, 255, 255, a)
    white.save(dest)
    return dest


# ── the import ───────────────────────────────────────────────────────────────
def run(domain, *, client=None):
    if not domain:
        raise SystemExit('sv brand import <domain> --client <Client>')
    domain = re.sub(r'^https?://', '', domain).strip('/').lower()
    bid = re.sub(r'[^a-z0-9]+', '-', domain.split('.')[0]).strip('-')
    client = client or bid.title()
    dest = drive.WORK / client / '_brand' / bid
    dest.mkdir(parents=True, exist_ok=True)
    notes = []

    html, css, theme = _site_css(domain)
    chroma, darks, count = _palette(css, theme)
    title = re.search(r'<title[^>]*>([^<|–—-]+)', html, re.I)
    name = (title.group(1).strip() if title else client) or client
    name = client if len(name) > 40 else name

    primary = chroma[0][0] if chroma else '#2F6FEB'
    if not chroma:
        notes.append('No brand colour found on the site: primary is a placeholder blue.')
    dark = darks[0][0] if darks else mix(primary, '#000000', 0.72)
    if contrast('#FFFFFF', dark) < 10:
        dark = darken_to(mix(primary, '#000000', 0.6), '#FFFFFF', 10)
    others = [c for c, _ in chroma[1:] if contrast(c, primary) > 1.6][:4]
    accents = (others + [mix(primary, '#FFFFFF', 0.35), mix(dark, primary, 0.5), '#E8A33D', '#D9534F'])[:4]

    colors = {
        'primary': primary,
        'primary_strong': darken_to(primary, '#FFFFFF', 4.6),
        'primary_soft': mix(primary, '#FFFFFF', 0.55),
        'dark': dark,
        'darker': mix(dark, '#000000', 0.25),
        'tint': mix(primary, '#FFFFFF', 0.9),
        'tint_soft': mix(primary, '#FFFFFF', 0.96),
        'on_dark': mix(primary, '#FFFFFF', 0.82),
        'on_dark_muted': mix(primary, '#FFFFFF', 0.55),
        'accent_1': accents[0], 'accent_2': accents[1], 'accent_3': accents[2], 'accent_4': accents[3],
    }
    if contrast(colors['on_dark_muted'], dark) < 4.5:
        colors['on_dark_muted'] = mix(colors['on_dark_muted'], '#FFFFFF', 0.4)

    fams = _fonts(css)
    fonts, fdir = {}, dest / 'fonts'
    for role, want in (('display', fams[0] if fams else None), ('body', fams[1] if len(fams) > 1 else (fams[0] if fams else None))):
        got = _google_font(want, fdir) if want else None
        if not got:
            stand = STAND_INS['sans' if role == 'body' else 'display']
            if want:
                notes.append(f'{role} font "{want}" is not on Google Fonts; {stand} stands in.')
            got = _google_font(stand, fdir)
        fam = _family_name(fdir / got)
        fonts[role] = {'family': fam, 'file': got, 'pitch': '34' if role == 'body' else '18'}
        _install(fdir / got)
    if fonts['display']['family'] == fonts['body']['family']:
        # kit keys measurement by family; one family for both roles uses the stand-in display face
        got = _google_font(STAND_INS['display'], fdir)
        fonts['display'] = {'family': _family_name(fdir / got), 'file': got, 'pitch': '18'}
        _install(fdir / got)
        notes.append('Site uses one family throughout; display falls back to a stand-in. Swap it if it reads wrong.')

    logo = _logo(domain, dest)
    symbol = _logo(domain, dest, icon=True)
    logos = {}
    if logo:
        logos['on_light'] = logo.name
        logos['on_dark'] = _white_version(logo, dest / 'logo-white.png').name
    else:
        notes.append('No logo: set BRAND_FETCH (the Logo Link client id) or drop logo.png in this folder.')
    if symbol:
        logos['mark_on_light'] = symbol.name
        logos['mark_on_dark'] = _white_version(symbol, dest / 'symbol-white.png').name

    data = {'id': bid, 'name': name, 'legal_name': name, 'short': client, 'website': domain,
            'voice': 'client', 'colors': colors, 'fonts': fonts, 'logos': logos,
            'footer': f'{client}  ·  Confidential', 'source': f'sv brand import {domain} (site CSS + Brandfetch Logo Link)'}
    (dest / 'brand.yaml').write_text('# Imported. Check every role before a customer sees it.\n' +
                                     yaml.safe_dump(data, sort_keys=False, allow_unicode=True))
    lines = [f'  brand "{bid}" -> {dest}', f'  primary {primary}  dark {dark}  fonts {fonts["display"]["family"]} / {fonts["body"]["family"]}',
             f'  top site colours: {", ".join(c for c, _ in chroma[:6]) or "none"}']
    lines += [f'  note: {n}' for n in notes]
    lines.append(f'  use it with  brand: {bid}  in a spec under ~/Servantium-Work/{client}/')
    return '\n'.join(lines)
