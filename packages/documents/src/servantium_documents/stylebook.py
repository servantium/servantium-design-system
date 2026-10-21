"""`sv stylebook <brand> [--company company.yaml] [--docs index.yaml] [-o out.html]`

One self-contained HTML file, laid out like a design-system page in Figma: the brand
(logos, colour roles with measured contrast, type with the real fonts embedded, the
document components) and, given a company profile, how the business is organised (org
chart, departments, people and titles, rate card, offer, stack, how it sells and
delivers) and the documents it produces at each stage.

Everything is embedded (fonts and logos as data URIs), so the file opens anywhere, offline,
and can be dropped into Drive or published as a page. The company profile is rendered
generically: known sections get purpose-built views, anything else becomes a tidy table,
so the profile can grow without touching this file.
"""
import base64
import datetime as dt
import html
import mimetypes
from pathlib import Path

import yaml

from . import brands

E = html.escape


def _uri(path):
    p = Path(path)
    mt = mimetypes.guess_type(p.name)[0] or ('font/ttf' if p.suffix == '.ttf' else 'application/octet-stream')
    return f'data:{mt};base64,{base64.b64encode(p.read_bytes()).decode()}'


def _lum(hx):
    def ch(c):
        c /= 255
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = (int(hx[i:i + 2], 16) for i in (1, 3, 5))
    return 0.2126 * ch(r) + 0.7152 * ch(g) + 0.0722 * ch(b)


def contrast(a, b):
    la, lb = sorted((_lum(a), _lum(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)


def _font_file(b, role):
    f = b.fonts.get(role, {})
    if not f.get('file'):
        return None
    for d in (b.root / 'fonts', Path.home() / 'Library/Fonts', Path('/Library/Fonts')):
        if (d / f['file']).exists():
            return d / f['file']
    return None


ROLE_USE = {
    'primary': 'Actions, accents, chart series 1', 'primary_strong': 'Eyebrows, links, small accent text',
    'primary_soft': 'Light accent fills, highlights', 'dark': 'Dark grounds, headlines',
    'darker': 'Deepest ground', 'tint': 'Panels, table zebra', 'tint_soft': 'Page washes',
    'ink': 'Primary text', 'ink_soft': 'Body text', 'muted': 'Captions, labels', 'line': 'Rules, borders',
    'surface': 'Cards, quiet fills', 'on_dark': 'Text on dark', 'on_dark_muted': 'Secondary text on dark',
    'accent_1': 'Chart series', 'accent_2': 'Chart series', 'accent_3': 'Chart series', 'accent_4': 'Chart series',
    'danger': 'Red status, risks', 'warning': 'Amber status, cautions', 'info': 'Notes, information',
}


# ── generic data rendering ──────────────────────────────────────────────────
def _label(k):
    return str(k).replace('_', ' ').strip().capitalize()


def _scalar(v):
    if isinstance(v, bool):
        return 'Yes' if v else 'No'
    if isinstance(v, float):
        return f'{v:,.2f}'.rstrip('0').rstrip('.') if abs(v) < 1000 else f'{v:,.0f}'
    if isinstance(v, int) and abs(v) >= 10000:
        return f'{v:,}'
    return E(str(v))


def render_value(v, depth=0):
    if isinstance(v, dict):
        if all(not isinstance(x, (dict, list)) for x in v.values()):
            rows = ''.join(f'<tr><th>{E(_label(k))}</th><td>{_scalar(x)}</td></tr>' for k, x in v.items())
            return f'<table class="kv">{rows}</table>'
        parts = []
        for k, x in v.items():
            tag = 'h4' if depth else 'h3'
            parts.append(f'<div class="sub"><{tag}>{E(_label(k))}</{tag}>{render_value(x, depth + 1)}</div>')
        return ''.join(parts)
    if isinstance(v, list):
        if v and all(isinstance(x, dict) for x in v):
            cols = []
            for x in v:
                for k, y in x.items():
                    if k not in cols and not isinstance(y, (dict, list)) or (k not in cols and isinstance(y, list) and all(not isinstance(z, (dict, list)) for z in y)):
                        cols.append(k)
            cols = cols[:9]
            head = ''.join(f'<th>{E(_label(c))}</th>' for c in cols)
            body = ''
            for x in v:
                cells = []
                for c in cols:
                    y = x.get(c, '')
                    if isinstance(y, list):
                        y = ', '.join(str(z) for z in y)
                    num = isinstance(y, (int, float)) and not isinstance(y, bool)
                    cells.append(f'<td class="{"num" if num else ""}">{_scalar(y)}</td>')
                body += '<tr>' + ''.join(cells) + '</tr>'
            nested = [(x, k) for x in v for k, y in x.items() if isinstance(y, (dict, list)) and k not in cols]
            extra = ''
            if nested and len(v) <= 8:
                for x in v:
                    inner = {k: y for k, y in x.items() if k not in cols}
                    if inner:
                        name = next((str(x[c]) for c in ('name', 'title', 'id') if c in x), '')
                        extra += f'<details><summary>{E(name)}</summary>{render_value(inner, depth + 1)}</details>'
            return f'<div class="tw"><table class="grid"><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table></div>{extra}'
        return '<ul>' + ''.join(f'<li>{render_value(x, depth + 1) if isinstance(x, (dict, list)) else _scalar(x)}</li>' for x in v) + '</ul>'
    return f'<p>{_scalar(v)}</p>'


# ── purpose-built views ─────────────────────────────────────────────────────
def _uses(p):
    u = p.get('servantium_user')
    return u is True or (isinstance(u, dict) and (u.get('enabled') or u.get('user')))


def org_chart(people):
    """The chief at the top, the leadership team in a row, and under each leader their whole
       organisation as an indented column. Compact enough for 40+ named people. reports_to may
       hold a person's id or name."""
    by_id = {}
    for p in people:
        if isinstance(p, dict):
            by_id[p.get('id') or p.get('name')] = p
            if p.get('name'):
                by_id.setdefault(p['name'], p)
    key = lambda p: p.get('id') or p.get('name')
    kids = {}
    roots = []
    for p in {key(p): p for p in people if isinstance(p, dict)}.values():
        boss = by_id.get(p.get('reports_to')) if p.get('reports_to') else None
        if boss and key(boss) != key(p):
            kids.setdefault(key(boss), []).append(p)
        else:
            roots.append(p)

    def card(p, cls='card'):
        tag = ' <span class="tag">Servantium</span>' if _uses(p) else ''
        return (f'<div class="{cls}"><b>{E(p["name"])}</b><span>{E(str(p.get("title", "")))}</span>'
                f'<i>{E(str(p.get("department", "")))}{tag}</i></div>')

    def column(p, depth=0):
        out = ''.join(f'<div class="ocrow" style="margin-left:{depth * 14}px">{card(c, "mini")}</div>' + column(c, depth + 1)
                      for c in kids.get(key(p), []))
        return out

    html_ = ''
    for r in roots:
        team = kids.get(key(r), [])
        html_ += f'<div class="ochief">{card(r)}</div><div class="oteam">'
        for lead in team:
            html_ += f'<div class="olead">{card(lead)}{column(lead)}</div>'
        html_ += '</div>'
    return f'<div class="org2">{html_}</div>'


def _names(node, ids):
    """Swap person ids for names wherever a value is exactly an id (heads, owners, reports_to)."""
    if isinstance(node, dict):
        return {k: _names(v, ids) for k, v in node.items()}
    if isinstance(node, list):
        return [_names(v, ids) for v in node]
    if isinstance(node, str) and node in ids:
        return ids[node]
    return node


def _find_people(company):
    org = company.get('org') or {}
    for key in ('people', 'staff', 'named_people', 'team'):
        if isinstance(org.get(key), list):
            return org[key]
    if isinstance(company.get('people'), list):
        return company['people']
    return []


# ── the page ─────────────────────────────────────────────────────────────────
CSS = '''
:root{--bg:#F6F6F7;--panel:#FFFFFF;--line:#E4E4E7;--ink:#18181B;--muted:#71717A;--side:#FFFFFF}
*{box-sizing:border-box}html{scroll-behavior:smooth}
body{margin:0;background:var(--bg);color:var(--ink);font:14px/1.5 var(--body),system-ui,sans-serif}
.side{position:fixed;inset:0 auto 0 0;width:248px;background:var(--side);border-right:1px solid var(--line);
  padding:20px 16px;overflow:auto}
.side img{max-width:150px;max-height:44px;display:block;margin:4px 6px 18px}
.side a{display:block;padding:6px 10px;border-radius:6px;color:var(--ink);text-decoration:none;font-size:13px}
.side a:hover{background:var(--tint)}.side small{display:block;color:var(--muted);font-size:11px;
  text-transform:uppercase;letter-spacing:.08em;margin:16px 10px 6px}
main{margin-left:248px;padding:40px 48px 120px;max-width:1280px}
section{background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:32px 36px;margin:0 0 28px}
section>h2{font:600 26px/1.2 var(--display),serif;margin:0 0 4px;color:var(--dark)}
section>.lede{color:var(--muted);margin:0 0 24px;max-width:760px}
h3{font:600 15px/1.3 var(--body);margin:26px 0 10px;color:var(--dark)}h4{font:600 13px var(--body);margin:16px 0 8px;color:var(--muted);text-transform:uppercase;letter-spacing:.06em}
.hero{background:var(--dark);color:var(--on_dark);border-radius:14px;padding:48px;margin-bottom:28px;position:relative;overflow:hidden}
.hero img{max-height:64px;max-width:320px}.hero h1{font:400 44px/1.1 var(--display),serif;margin:28px 0 10px;max-width:820px}
.hero p{color:var(--on_dark_muted);max-width:720px;margin:0}.hero .meta{margin-top:24px;font-size:12px;letter-spacing:.08em;text-transform:uppercase;color:var(--on_dark_muted)}
.row{display:grid;gap:16px}.c2{grid-template-columns:repeat(2,1fr)}.c3{grid-template-columns:repeat(3,1fr)}.c4{grid-template-columns:repeat(4,1fr)}
.tile{border:1px solid var(--line);border-radius:10px;padding:28px;display:flex;align-items:center;justify-content:center;min-height:150px}
.tile img{max-width:80%;max-height:70px}.cap{font-size:12px;color:var(--muted);margin-top:8px}
.sw{border:1px solid var(--line);border-radius:10px;overflow:hidden}.sw .chip{height:76px}
.sw .t{padding:10px 12px}.sw b{display:block;font-size:13px}.sw code{font:12px ui-monospace,monospace;color:var(--muted)}
.sw .use{font-size:12px;color:var(--muted)}.ratio{font:11px ui-monospace,monospace;margin-top:4px}
.pass{color:#15803D}.fail{color:#B91C1C}
.spec{border:1px solid var(--line);border-radius:10px;padding:24px}.spec .big{font:400 46px/1.1 var(--display),serif;color:var(--dark)}
.spec .body{font:16px/1.6 var(--body)}
table{border-collapse:collapse;width:100%;font-size:13px}.tw{overflow:auto;border:1px solid var(--line);border-radius:10px;margin:6px 0 10px}
.grid th{background:var(--dark);color:var(--on_dark);text-align:left;font-weight:600;padding:8px 10px;white-space:nowrap;font-size:12px}
.grid td{padding:7px 10px;border-top:1px solid var(--line);vertical-align:top}.grid tr:nth-child(even) td{background:var(--tint_soft)}
td.num{text-align:right;font-variant-numeric:tabular-nums;white-space:nowrap}
.kv th{width:240px;text-align:left;color:var(--muted);font-weight:500;padding:6px 10px 6px 0;vertical-align:top}.kv td{padding:6px 0}
.kv tr{border-top:1px solid var(--line)}
details{border:1px solid var(--line);border-radius:8px;padding:8px 12px;margin:6px 0}summary{cursor:pointer;font-weight:600}
.btn{display:inline-block;padding:9px 16px;border-radius:8px;font-weight:600;font-size:13px;margin:0 8px 8px 0}
.b1{background:var(--primary);color:#fff}.b2{background:var(--tint);color:var(--dark)}.b3{border:1px solid var(--line);color:var(--ink)}
.rag{display:inline-block;padding:3px 10px;border-radius:999px;font-size:12px;font-weight:600;margin-right:6px}
.kpi{border:1px solid var(--line);border-radius:10px;padding:18px;border-top:3px solid var(--primary)}
.kpi b{font:600 30px var(--display),serif;color:var(--dark);display:block}.kpi span{font-size:12px;color:var(--muted)}
.call{background:var(--dark);color:var(--on_dark);border-radius:8px;padding:12px 16px;font-size:13px}
.call b{color:var(--primary_soft)}
.org{overflow:auto;padding:10px 0}.org ul{display:flex;gap:10px;padding-left:0;list-style:none;margin:0;justify-content:center}
.org li{display:flex;flex-direction:column;align-items:center;position:relative;padding-top:16px}
.org li::before{content:"";position:absolute;top:0;left:50%;height:16px;border-left:1px solid var(--line)}
.org>ul>li::before{display:none}.org ul ul{padding-top:0;border-top:1px solid var(--line)}
.org .card{border:1px solid var(--line);border-top:3px solid var(--primary);border-radius:8px;background:#fff;padding:8px 10px;
  min-width:150px;max-width:190px;text-align:center;font-size:12px}
.org .card b{display:block;font-size:12.5px}.org .card span{display:block;color:var(--ink)}.org .card i{display:block;color:var(--muted);font-style:normal;font-size:11px}
.org2{padding:6px 0}.ochief{display:flex;justify-content:center;margin-bottom:18px}
.oteam{display:grid;grid-template-columns:repeat(auto-fill,minmax(210px,1fr));gap:14px;border-top:1px solid var(--line);padding-top:18px}
.olead>.card{margin-bottom:8px;max-width:none}.org2 .card{border:1px solid var(--line);border-top:3px solid var(--primary);border-radius:8px;
  background:#fff;padding:9px 11px;font-size:12px;min-width:200px}.org2 .card b{display:block;font-size:13px}.org2 .card span{display:block}
.org2 .card i,.org2 .mini i{display:block;color:var(--muted);font-style:normal;font-size:11px}
.org2 .mini{border-left:2px solid var(--line);padding:4px 8px;margin:4px 0;font-size:11.5px;background:var(--tint_soft);border-radius:0 6px 6px 0}
.org2 .mini b{display:block;font-size:12px}.org2 .mini span{display:block}
.tag{background:var(--tint);color:var(--primary_strong);border-radius:4px;padding:0 5px;font-size:10px;font-weight:700}
.stage{border-left:3px solid var(--primary);padding:6px 0 6px 14px;margin:10px 0}.stage b{display:block}
.docs li{margin:3px 0}.kind{font:11px ui-monospace,monospace;color:var(--muted);margin-left:6px}
.thumbs{display:grid;grid-template-columns:repeat(3,1fr);gap:14px}.thumbs figure{margin:0;border:1px solid var(--line);border-radius:8px;overflow:hidden;background:#fff}
.thumbs img{width:100%;display:block}.thumbs figcaption{font-size:12px;padding:8px 10px;color:var(--muted)}
@media(max-width:900px){.side{display:none}main{margin-left:0;padding:16px}.c3,.c4{grid-template-columns:1fr 1fr}}
'''


def build(brand_id, company_path=None, docs_path=None, out=None, title=None):
    b = brands.load(brand_id)
    company = yaml.safe_load(Path(company_path).read_text()) if company_path else {}
    ids = {p['id']: p['name'] for p in _find_people(company) if isinstance(p, dict) and p.get('id') and p.get('name')}
    docs = yaml.safe_load(Path(docs_path).read_text()) if docs_path else None
    c = dict(primary='#00C26D', primary_strong='#00A95E', primary_soft='#6FE7B0', dark='#023E25', darker='#045F37',
             tint='#E8FBF1', tint_soft='#F3FCF8', ink='#0D0D0D', ink_soft='#34404D', muted='#64748B', line='#E1E3E6',
             surface='#F5F6F7', on_dark='#CBEADA', on_dark_muted='#8FC4AB', accent_1='#4C82A7', accent_2='#26A899',
             accent_3='#FFB02E', accent_4='#FF5C70', danger='#FF5C70', warning='#FFB02E', info='#4C82A7')
    c.update({k: str(v).upper() for k, v in b.colors.items()})
    disp, body = b.fonts.get('display', {}).get('family', 'Georgia'), b.fonts.get('body', {}).get('family', 'system-ui')
    faces = ''
    for role, fam in (('display', disp), ('body', body)):
        f = _font_file(b, role)
        if f:
            faces += f"@font-face{{font-family:'{fam}';src:url({_uri(f)}) format('truetype');font-weight:100 900}}\n"
    root = ':root{' + ''.join(f'--{k}:{v};' for k, v in c.items()) + f"--display:'{disp}';--body:'{body}';--tint:{c['tint']}}}"

    def logo(which):
        """The SVG beside a PNG logo when there is one: crisp at any zoom."""
        p = b.logo(which)
        if p and p.with_suffix('.svg').exists():
            p = p.with_suffix('.svg')
        return _uri(p) if p and p.exists() else ''

    ident = company.get('identity', {}) if isinstance(company.get('identity'), dict) else {}
    name = title or ident.get('legal_name') or b.legal_name
    tagline = ident.get('mission') or ident.get('tagline') or ''
    nav, secs = [], []

    def sec(sid, h2, lede, inner, group=None):
        if group:
            nav.append(f'<small>{E(group)}</small>')
        nav.append(f'<a href="#{sid}">{E(h2)}</a>')
        secs.append(f'<section id="{sid}"><h2>{E(h2)}</h2><p class="lede">{E(lede)}</p>{inner}</section>')

    # Brand ------------------------------------------------------------------
    lo, ld, mk, mkd = logo('on_light'), logo('on_dark'), logo('mark_on_light'), logo('mark_on_dark')
    tiles = f'''<div class="row c2">
      <div><div class="tile" style="background:#fff"><img src="{lo}" alt="{E(b.name)} logo"></div><div class="cap">Primary lockup, light grounds</div></div>
      <div><div class="tile" style="background:var(--dark)"><img src="{ld}" alt=""></div><div class="cap">Reversed lockup, dark grounds</div></div></div>
      <div class="row c4" style="margin-top:16px">
      {''.join(f'<div><div class="tile" style="background:{bg};min-height:110px"><img src="{src}" style="max-height:{px}px" alt=""></div><div class="cap">{cap}</div></div>'
               for bg, src, px, cap in (('#fff', mk or lo, 56, 'Symbol'), ('var(--dark)', mkd or ld, 56, 'Symbol, reversed'),
                                        ('var(--tint)', mk or lo, 28, 'Symbol at small size'), ('var(--primary)', mkd or ld, 40, 'On primary')) if src)}</div>
      <h3>Use</h3><ul><li>Give the logo clear space equal to the height of the symbol on every side.</li>
      <li>Use the reversed lockup on {E(b.short)} dark, never on mid-tones or photographs without a scrim.</li>
      <li>Never recolour, stretch, outline, add effects, or rebuild the wordmark in another font.</li>
      <li>Minimum size: 24 px tall on screen, 0.3 in in print. Below that, use the symbol alone.</li></ul>'''
    sec('logo', 'Logo', f'The {b.name} mark and how to use it.', tiles, group='Brand')

    sw = ''
    for role, hx in c.items():
        if role not in ROLE_USE:
            continue
        on = '#FFFFFF' if _lum(hx) < 0.35 else c['ink']
        r = contrast(hx, '#FFFFFF')
        need = 4.5 if role in ('primary_strong', 'muted', 'ink', 'ink_soft') else None
        ok = '' if need is None else (f' <span class="pass">AA</span>' if r >= need else ' <span class="fail">below AA</span>')
        sw += (f'<div class="sw"><div class="chip" style="background:{hx}"></div><div class="t"><b>{E(_label(role))}</b>'
               f'<code>{hx}</code><div class="use">{E(ROLE_USE[role])}</div><div class="ratio">{r:.2f}:1 on white{ok}</div></div></div>')
    pairs = [('White on primary', '#FFFFFF', c['primary']), ('White on dark', '#FFFFFF', c['dark']),
             ('On dark on dark', c['on_dark'], c['dark']), ('Muted on dark', c['on_dark_muted'], c['dark']),
             ('Ink on white', c['ink'], '#FFFFFF'), ('Strong primary on white', c['primary_strong'], '#FFFFFF')]
    pr = ''.join(f'<div class="sw"><div class="chip" style="background:{bg};color:{fg};display:flex;align-items:center;justify-content:center;font-weight:600">Aa {E(n)}</div>'
                 f'<div class="t"><div class="ratio">{contrast(fg, bg):.2f}:1 {"<span class=pass>AA</span>" if contrast(fg, bg) >= 4.5 else "<span class=fail>large text only</span>" if contrast(fg, bg) >= 3 else "<span class=fail>fails</span>"}</div></div></div>'
                 for n, fg, bg in pairs)
    sec('colour', 'Colour', 'Colour roles. Documents and slides pick these by role, never by hex.',
        f'<div class="row c4">{sw}</div><h3>Text pairings</h3><div class="row c3">{pr}</div>'
        f'<h3>Chart series, in order</h3><div style="display:flex;gap:8px">' +
        ''.join(f'<div style="flex:1;height:44px;border-radius:6px;background:{c[k]}"></div>' for k in ('primary', 'dark', 'accent_1', 'accent_2', 'accent_3', 'accent_4')) + '</div>')

    sec('type', 'Typography', 'Two families. Both are on Google Fonts, so Slides, Docs and Sheets render them natively.',
        f'''<div class="row c2"><div class="spec"><div class="cap">Display · {E(disp)}</div><div class="big">Titles say the conclusion.</div>
        <div class="cap" style="margin-top:14px">Slide titles 28–46 pt, document titles, big numbers</div></div>
        <div class="spec"><div class="cap">Body · {E(body)}</div><div class="body">Body text carries the proof: short sentences, real numbers,
        sources named. <b>Semibold</b> for emphasis, never underline.</div><div class="cap" style="margin-top:14px">Body 13–16 pt, labels 9–11 pt caps at +12% tracking</div></div></div>
        <h3>Scale</h3><table class="kv"><tr><th>Display XL</th><td style="font:400 40px var(--display)">{E(b.short)} 2026</td></tr>
        <tr><th>Heading</th><td style="font:600 22px var(--display)">Section heading</td></tr><tr><th>Subhead</th><td style="font:600 16px var(--body)">A subhead in the body face</td></tr>
        <tr><th>Body</th><td style="font:15px var(--body)">The quick brown fox jumps over the lazy dog. 0123456789</td></tr>
        <tr><th>Eyebrow</th><td style="font:700 11px var(--body);letter-spacing:.14em;color:var(--primary_strong)">EYEBROW · LABEL</td></tr></table>''')

    sec('components', 'Document components', 'The pieces every deck, document and workbook is built from.',
        f'''<h3>Actions</h3><span class="btn b1">Primary</span><span class="btn b2">Secondary</span><span class="btn b3">Tertiary</span>
        <h3>Status</h3><span class="rag" style="background:{c["primary"]};color:#fff">Green · on track</span>
        <span class="rag" style="background:{c["warning"]};color:#fff">Amber · at risk</span><span class="rag" style="background:{c["danger"]};color:#fff">Red · off track</span>
        <h3>Numbers</h3><div class="row c3"><div class="kpi"><b>96%</b><span>Samples analysed in window</span></div>
        <div class="kpi"><b>12</b><span>Days, quote turnaround</span></div><div class="kpi"><b>3 of 8</b><span>Milestones complete</span></div></div>
        <h3>Takeaway</h3><div class="call"><b>The so-what.</b> One line that tells the reader what to do with the page.</div>
        <h3>Table</h3><div class="tw"><table class="grid"><thead><tr><th>Phase</th><th>Owner</th><th>Hours</th><th>Fee</th></tr></thead><tbody>
        <tr><td>Discovery</td><td>Project manager</td><td class="num">48</td><td class="num">$9,600</td></tr>
        <tr><td>Build</td><td>Lead</td><td class="num">220</td><td class="num">$44,000</td></tr><tr><td><b>Total</b></td><td></td><td class="num"><b>268</b></td><td class="num"><b>$53,600</b></td></tr></tbody></table></div>''')

    # Company ----------------------------------------------------------------
    if company:
        first = True
        if ident:
            sec('company', 'Company', 'Who they are.', render_value(ident), group='How the business runs')
            first = False
        people = _find_people(company)
        org = company.get('org') or {}
        if org:
            depts = {k: v for k, v in org.items() if k not in ('people', 'staff', 'named_people', 'team')}
            inner = (org_chart(people) if people else '') + render_value(_names(depts, ids))
            if people:
                inner += '<h3>Named people</h3>' + render_value(_names(people, ids))
            sec('org', 'Organisation', 'How the company is organised: reporting lines, departments, titles, and who uses Servantium.',
                inner, group=None if not first else 'How the business runs')
            first = False
        titles = {'rate_card': ('Rate card', 'What each role costs and bills.'),
                  'service_catalog': ('Offer', 'What they sell, in the shapes they sell it.'),
                  'products': ('Products', 'Product and price list.'),
                  'tech_stack': ('Tech stack', 'The systems the business runs on, and where Servantium connects.'),
                  'sales_process': ('How they sell', 'Lifecycle stages, qualification and approval authority.'),
                  'delivery_process': ('How they deliver', 'Method, governance and the standard documents.'),
                  'client_book': ('Clients and engagements', 'The accounts and the book of work.'),
                  'hero_engagement': ('The main engagement', 'The fully documented engagement, first contact to closeout.'),
                  'demo_story': ('Demo moments', 'What a salesperson shows with this company.')}
        for key, val in company.items():
            if key in ('identity', 'org', 'gaps_hint'):
                continue
            h2, lede = titles.get(key, (_label(key), ''))
            sec(key.replace('_', '-'), h2, lede, render_value(_names(val, ids)))

    # Documents --------------------------------------------------------------
    if docs:
        stages = docs.get('stages') if isinstance(docs, dict) else docs
        inner = ''
        for st in stages or []:
            items = ''.join(f'<li>{E(d.get("title", ""))}<span class="kind">{E(d.get("kind", ""))}</span></li>' for d in st.get('docs', []))
            inner += f'<div class="stage"><b>{E(st.get("name", ""))}</b><ul class="docs">{items}</ul></div>'
        sec('documents', 'Documents', 'Every document the business produces, by stage, from first contact to closeout.', inner, group='Documents')

    hero = (f'<div class="hero"><img src="{ld}" alt="{E(b.name)}"><h1>{E(name)} style guide</h1><p>{E(str(tagline))}</p>'
            f'<div class="meta">Brand, organisation and documents · {dt.date.today():%B %Y}'
            f'{" · Fictional company for demonstration" if not b.is_house and (b.root.parent == brands.BUILTIN) else ""}</div></div>')
    page = (f'<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
            f'<title>{E(b.short)} Style Guide</title><style>{faces}{root}{CSS}</style></head><body>'
            f'<nav class="side"><img src="{lo}" alt="">{"".join(nav)}</nav><main>{hero}{"".join(secs)}</main></body></html>')
    out = Path(out or f'{b.id}-style-guide.html')
    out.write_text(page)
    return out
