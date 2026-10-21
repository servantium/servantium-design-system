"""Brands: whose colours, fonts, logos and name a document wears.

Servantium is one brand among several, not the engine's assumption. A brand is a folder
`brands/<id>/` holding `brand.yaml` plus its logo files. The engine resolves the active
brand ONCE, at import, from the environment variable SV_BRAND (default `servantium`), and
kit.py binds its colour and font constants from it. `sv` reads the spec's `brand:` key
and, when it differs from the loaded brand, re-runs itself with SV_BRAND set, so every
module sees one consistent brand for the whole build.

Where brands live:
  packages/documents/brands/<id>/          Servantium and our fictional demo companies
  <workspace>/<Client>/_brand/<id>/        real companies (imported by `sv brand import`;
                                           never committed: Brandfetch forbids caching)
  $SV_BRANDS (colon-separated)             anything else

brand.yaml (every key except id and name is optional; a missing colour role keeps the
Verdant value, so a brand only states what differs):

  id: avelle
  name: Avelle Biosciences              # how the company is named in running text
  legal_name: Avelle Biosciences, Inc.  # copyright line and contracts
  short: Avelle                         # footers and tight labels
  website: avelle.example
  address: [line, line]
  colors:                               # semantic roles, hex
    primary: '#...'                     # the action / accent colour (Servantium green)
    primary_strong: '#...'              # eyebrows, links; must pass 4.5:1 on white
    primary_soft: '#...'                # light accent fills
    dark: '#...'                        # dark grounds, headline ink (Servantium forest)
    darker: '#...'                      # darkest ground
    tint: '#...'                        # pale panel fill (Servantium mint)
    tint_soft: '#...'                   # palest fill
    ink / ink_soft / muted / line / surface
    on_dark / on_dark_muted             # text on the dark ground
    accent_1 / accent_2 / accent_3 / accent_4   # chart series after primary and dark
    danger / warning / info
  fonts:
    display: {family: DM Serif Display, file: DMSerifDisplay-Regular.ttf,
              panose: '02000000000000000000', pitch: '18'}
    body:    {family: DM Sans, file: 'DMSans[opsz,wght].ttf', pitch: '34'}
  logos:                                # paths relative to the brand folder
    on_light: logo.png                  # full lockup for light grounds
    on_dark: logo-white.png             # full lockup for dark grounds
    mark_on_dark: symbol-white.png      # the symbol alone, for dark grounds
  footer: Avelle Biosciences · Confidential
  voice: house | client                 # house = Servantium's own voice rules apply
"""
import os
from dataclasses import dataclass, field
from pathlib import Path

import yaml

PKG = Path(__file__).resolve().parent
BUILTIN = PKG.parents[1] / 'brands'
DEFAULT = 'servantium'

# Semantic role -> the Verdant token key kit.py has always read for that job.
ROLE_TOKENS = {
    'primary':        ['color-green'],
    'primary_strong': ['color-green-hover', 'color-model-link'],
    'primary_soft':   ['color-jade', 'color-light-jade', 'color-pale-green', 'color-fresh-green'],
    'dark':           ['color-deep-forest'],
    'darker':         ['color-forest', 'color-emerald'],
    'tint':           ['color-soft-mint'],
    'tint_soft':      ['color-mint-tint'],
    'ink':            ['color-ink', 'color-ink-1'],
    'ink_soft':       ['color-ink-soft'],
    'muted':          ['color-slate', 'color-ink-muted', 'color-ink-3'],
    'line':           ['color-cloud-grey', 'color-cloud-2'],
    'surface':        ['color-mist-grey', 'color-mist-2'],
    'on_dark':        ['color-on-forest'],
    'on_dark_muted':  ['color-on-forest-muted'],
    'accent_1':       ['color-slate-blue', 'color-info'],
    'accent_2':       ['color-deep-teal'],
    # Amber and coral are STATUS colours in every renderer (caution, risk; pill and RAG tones),
    # so they follow the brand's warning and danger roles. Accents 3 and 4 feed charts only.
    'accent_3':       ['color-accent-3'],
    'accent_4':       ['color-accent-4'],
    # Status green is its own role: a brand's primary may be indigo or copper, and an indigo
    # 'Green' chip reads as nothing. Unset, it stays Verdant's green.
    'success':        ['color-success'],
    'danger':         ['color-danger', 'color-coral'],
    'warning':        ['color-warning', 'color-amber'],
    'info':           ['color-info'],
}


class BrandError(Exception):
    pass


@dataclass
class Brand:
    id: str
    name: str
    root: Path
    legal_name: str = ''
    short: str = ''
    website: str = ''
    address: list = field(default_factory=list)
    colors: dict = field(default_factory=dict)
    fonts: dict = field(default_factory=dict)
    logos: dict = field(default_factory=dict)
    footer: str = ''
    voice: str = 'client'
    raw: dict = field(default_factory=dict)

    @property
    def is_house(self):
        return self.voice == 'house'

    def logo(self, which):
        p = self.logos.get(which)
        return (self.root / p) if p else None

    def token_overrides(self):
        """Verdant token key -> hex, for every role this brand states."""
        out = {}
        for role, hx in self.colors.items():
            if role not in ROLE_TOKENS:
                raise BrandError(f'{self.id}: unknown colour role "{role}". Roles: {", ".join(ROLE_TOKENS)}')
            hx = str(hx).strip()
            if not (hx.startswith('#') and len(hx) == 7):
                raise BrandError(f'{self.id}: colour {role} must be #RRGGBB, got {hx!r}')
            for key in ROLE_TOKENS[role]:
                out[key] = hx.upper()
        # A role that feeds a later role keeps the later one explicit: danger/warning/info win.
        for role in ('success', 'danger', 'warning', 'info'):
            if role in self.colors:
                for key in ROLE_TOKENS[role]:
                    out[key] = str(self.colors[role]).upper()
        return out


def search_path():
    paths = [BUILTIN]
    env = os.environ.get('SV_BRANDS')
    if env:
        paths += [Path(p) for p in env.split(':') if p]
    work = Path(os.environ.get('SV_WORK', Path.home() / 'Servantium-Work'))
    if work.exists():
        paths += sorted(work.glob('*/_brand'))
    return paths


def find(brand_id):
    for base in search_path():
        p = base / brand_id / 'brand.yaml'
        if p.exists():
            return p
    raise BrandError(f'No brand "{brand_id}". Looked in: ' + ', '.join(str(p) for p in search_path()))


def load(brand_id=None):
    brand_id = (brand_id or os.environ.get('SV_BRAND') or DEFAULT).strip().lower()
    path = find(brand_id)
    d = yaml.safe_load(path.read_text()) or {}
    if d.get('id', brand_id) != brand_id:
        raise BrandError(f'{path}: id "{d.get("id")}" does not match its folder "{brand_id}"')
    name = d.get('name') or brand_id.title()
    facts = d.get('company_json')                 # one source for company facts (Servantium: @servantium/brand)
    if facts:
        import json
        cj = json.loads((path.parent / facts).read_text())
        ad = cj.get('address', {})
        d.setdefault('legal_name', cj.get('legalName'))
        d.setdefault('address', [ad.get('line1', ''), f"{ad.get('city', '')}, {ad.get('region', '')} {ad.get('postalCode', '')}".strip(', ')])
        d.setdefault('website', cj.get('urls', {}).get('website', '').replace('https://', ''))
    return Brand(
        id=brand_id, name=name, root=path.parent,
        legal_name=d.get('legal_name', name), short=d.get('short', name),
        website=d.get('website', ''), address=d.get('address', []) or [],
        colors=d.get('colors', {}) or {}, fonts=d.get('fonts', {}) or {},
        logos=d.get('logos', {}) or {}, footer=d.get('footer', f'{d.get("short", name)}  ·  Confidential'),
        voice=d.get('voice', 'house' if brand_id == DEFAULT else 'client'), raw=d,
    )


def available():
    seen = {}
    for base in search_path():
        for p in sorted(base.glob('*/brand.yaml')):
            seen.setdefault(p.parent.name, p.parent)
    return seen


ACTIVE = load()
