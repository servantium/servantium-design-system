"""Branded Mermaid diagrams: the brand's colours and type on any Mermaid source.

Mermaid is the quick way to draw a flowchart, sequence or Gantt; the draw.io engine in
diagram.py stays for swimlane process maps that must read left to right in order.
Mermaid lays the diagram out; this module dresses it: a theme generated from kit (so it
follows the active brand), the brand body font embedded for headless Chrome, and an
optional frame with title, caption and footer.

    python -m servantium_documents.mermaid <spec.yaml>   -> <spec dir>/out/<client> <name>.svg, .png, .pdf
    build(spec_path) -> {'svg': Path, 'png': Path, 'pdf': Path}

Spec:

    mermaid: Quote to Delivery          # the file name, after the client
    client: Acme Labs
    date: 2026-10-20                    # optional, shown in the frame's eyebrow
    title: How a quote becomes a staffed project.   # optional; defaults to the name
    subtitle: One line under the title. # optional
    source: |                           # Mermaid text, or `file: diagram.mmd` (relative to the spec)
      flowchart LR
        A[Quote] --> B{Approved?}
        B -- yes --> C[Staff the project]:::primary
    caption: Figure 1. What the caption says.   # optional
    frame: true                         # default; false writes the bare diagram
    width: 1100                         # optional: a minimum frame width in px
    embed_font: false                   # true keeps the body font inside the SVG (about 0.9 MB)

Brand classes, ready for flowcharts and state diagrams (`A:::primary` or `class A,B soft`):
    primary  dark fill, light text        accent  the brand's action colour
    soft     pale tint                    muted   grey, dashed: optional or out of scope
    warn     amber outline                danger  coral outline            done  grey fill

Finding mermaid-cli (mmdc), in order: $SV_MMDC; `mmdc` on PATH; node_modules/.bin/mmdc at
the repo root; the legacy decks workspace (~/Projects/Servantium/decks). Install with
`npm install -g @mermaid-js/mermaid-cli`, or set SV_MMDC to the binary.
"""
import base64
import datetime as dt
import html
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

import yaml

from . import kit
from .brand import hexof
from .spec import SpecError, _StrictLoader

HEX = lambda c: '#' + hexof(c)
FONT_STACK = f'"{kit.UI}", Helvetica, Arial, sans-serif'
DISPLAY_STACK = f'"{kit.DISPLAY}", Georgia, serif'
CLASS_DIAGRAMS = ('flowchart', 'graph', 'stateDiagram')


# ── spec ─────────────────────────────────────────────────────────────────────
def load(path):
    path = Path(path).expanduser().resolve()
    spec = yaml.load(path.read_bytes(), Loader=_StrictLoader) or {}
    for key in ('mermaid', 'client'):
        if key not in spec:
            raise SpecError(f'{path.name}: missing "{key}"')
    if bool(spec.get('source')) == bool(spec.get('file')):
        raise SpecError(f'{path.name}: give the diagram as `source: |` or `file: x.mmd`, one of them')
    if spec.get('file'):
        f = path.parent / spec['file']
        if not f.exists():
            raise SpecError(f'{path.name}: file not found: {spec["file"]}')
        spec['source'] = f.read_text()
    spec['source'] = str(spec['source']).strip() + '\n'
    if spec.get('date') is not None:
        spec['date'] = str(spec['date'])
    spec['_path'] = str(path)
    return spec


# ── theme ────────────────────────────────────────────────────────────────────
def _ink_on(fill):
    def lum(rgb):
        def ch(c):
            c /= 255
            return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
        return 0.2126 * ch(rgb[0]) + 0.7152 * ch(rgb[1]) + 0.0722 * ch(rgb[2])
    lf = lum(fill)
    return kit.WHITE if 1.05 / (lf + 0.05) >= (lf + 0.05) / (lum(kit.INK) + 0.05) else kit.INK


def theme_variables():
    """Mermaid's `base` theme, every variable from kit, so the active brand flows through."""
    palette = [kit.GREEN, kit.FOREST, kit.SLATE, kit.TEAL, kit.AMBER, kit.CORAL, kit.GREEN_300, kit.INK_MUTED]
    v = {
        'background': HEX(kit.WHITE),
        'fontFamily': FONT_STACK,
        'fontSize': '15px',
        'primaryColor': HEX(kit.MINT),
        'primaryTextColor': HEX(kit.FOREST),
        'primaryBorderColor': HEX(kit.GREEN),
        'secondaryColor': HEX(kit.MINT_TINT),
        'secondaryTextColor': HEX(kit.INK_800),
        'secondaryBorderColor': HEX(kit.CLOUD),
        'tertiaryColor': HEX(kit.MIST),
        'tertiaryTextColor': HEX(kit.INK_800),
        'tertiaryBorderColor': HEX(kit.CLOUD),
        'lineColor': HEX(kit.INK_MUTED),
        'textColor': HEX(kit.INK_800),
        'titleColor': HEX(kit.FOREST),
        'mainBkg': HEX(kit.MINT),
        'nodeBorder': HEX(kit.GREEN),
        'nodeTextColor': HEX(kit.FOREST),
        'clusterBkg': HEX(kit.MINT_TINT),
        'clusterBorder': HEX(kit.CLOUD),
        'edgeLabelBackground': HEX(kit.WHITE),
        'noteBkgColor': HEX(kit.MIST),
        'noteTextColor': HEX(kit.INK_800),
        'noteBorderColor': HEX(kit.CLOUD),
        # sequence
        # stick-figure actors print their name on the page, so actor text is dark on a pale box
        'actorBkg': HEX(kit.MINT),
        'actorBorder': HEX(kit.GREEN),
        'actorTextColor': HEX(kit.FOREST),
        'actorLineColor': HEX(kit.CLOUD),
        'signalColor': HEX(kit.INK_800),
        'signalTextColor': HEX(kit.INK_800),
        'labelBoxBkgColor': HEX(kit.MINT),
        'labelBoxBorderColor': HEX(kit.GREEN),
        'labelTextColor': HEX(kit.FOREST),
        'loopTextColor': HEX(kit.FOREST),
        'activationBkgColor': HEX(kit.MINT),
        'activationBorderColor': HEX(kit.GREEN),
        'sequenceNumberColor': HEX(_ink_on(kit.INK_800)),   # on the signal-coloured disc
        # gantt
        'sectionBkgColor': HEX(kit.MINT_TINT),
        'altSectionBkgColor': HEX(kit.WHITE),
        'sectionBkgColor2': HEX(kit.MIST),
        'taskBkgColor': HEX(kit.GREEN),
        'taskBorderColor': HEX(kit.GREEN_600),
        'taskTextColor': HEX(_ink_on(kit.GREEN)),
        'taskTextLightColor': HEX(_ink_on(kit.GREEN)),
        'taskTextDarkColor': HEX(kit.INK),
        'taskTextOutsideColor': HEX(kit.INK_800),
        'taskTextClickableColor': HEX(kit.GREEN_600),
        'activeTaskBkgColor': HEX(kit.MINT),
        'activeTaskBorderColor': HEX(kit.GREEN_600),
        'doneTaskBkgColor': HEX(kit.CLOUD),
        'doneTaskBorderColor': HEX(kit.INK_MUTED),
        'critBkgColor': HEX(kit.CORAL),
        'critBorderColor': HEX(kit.CORAL),
        'gridColor': HEX(kit.CLOUD),
        'todayLineColor': HEX(kit.AMBER),
        'excludeBkgColor': HEX(kit.MIST),
        # state
        'labelColor': HEX(kit.FOREST),
        'altBackground': HEX(kit.MIST),
        'errorBkgColor': HEX(kit.CORAL),
        'errorTextColor': HEX(_ink_on(kit.CORAL)),
    }
    for i, c in enumerate(palette):            # pie slices, timelines, journeys, mindmaps
        v[f'pie{i + 1}'] = HEX(c)
        v[f'cScale{i}'] = HEX(c)
        v[f'cScaleLabel{i}'] = HEX(_ink_on(c))
    v.update({'pieStrokeColor': HEX(kit.WHITE), 'pieOuterStrokeColor': HEX(kit.WHITE),
              'pieTitleTextColor': HEX(kit.FOREST), 'pieSectionTextColor': HEX(kit.WHITE),
              'pieLegendTextColor': HEX(kit.INK_800)})
    return v


def config():
    """The mermaid-cli config file. SVG text labels (htmlLabels off) so the SVG opens the same
       in Office, Google and Inkscape, which do not draw HTML inside SVG."""
    return {
        'theme': 'base',
        'themeVariables': theme_variables(),
        'fontFamily': FONT_STACK,
        'htmlLabels': False,
        'flowchart': {'htmlLabels': False, 'curve': 'basis', 'padding': 18, 'nodeSpacing': 46,
                      'rankSpacing': 56, 'diagramPadding': 12, 'useMaxWidth': False},
        'sequence': {'useMaxWidth': False, 'mirrorActors': False, 'actorFontFamily': FONT_STACK,
                     'messageFontFamily': FONT_STACK, 'noteFontFamily': FONT_STACK, 'actorFontSize': 15,
                     'messageFontSize': 14, 'noteFontSize': 13, 'boxMargin': 12, 'messageMargin': 38,
                     'diagramMarginX': 16, 'diagramMarginY': 12},
        'gantt': {'useMaxWidth': False, 'fontSize': 13, 'sectionFontSize': 13, 'barHeight': 26, 'barGap': 8,
                  'topPadding': 36, 'leftPadding': 150, 'rightPadding': 40, 'gridLineStartPadding': 40,
                  'numberSectionStyles': 2, 'axisFormat': '%b %d'},
        'state': {'useMaxWidth': False}, 'class': {'useMaxWidth': False}, 'er': {'useMaxWidth': False},
        'pie': {'useMaxWidth': False}, 'journey': {'useMaxWidth': False}, 'timeline': {'useMaxWidth': False},
    }


def class_defs():
    """Brand classes appended to flowcharts and state diagrams."""
    def d(fill, stroke, color, extra=''):
        return f'fill:{HEX(fill)},stroke:{HEX(stroke)},color:{HEX(color)}{extra}'
    return {
        'primary': d(kit.FOREST, kit.FOREST, _ink_on(kit.FOREST)),
        'accent':  d(kit.GREEN, kit.GREEN_600, _ink_on(kit.GREEN)),
        'soft':    d(kit.MINT_TINT, kit.GREEN, kit.FOREST),
        'muted':   d(kit.MIST, kit.CLOUD, kit.INK_MUTED, ',stroke-dasharray:5 4'),
        'warn':    d(kit.WHITE, kit.AMBER, kit.INK_800, ',stroke-width:2px'),
        'danger':  d(kit.WHITE, kit.CORAL, kit.INK_800, ',stroke-width:2px'),
        'done':    d(kit.CLOUD, kit.INK_MUTED, kit.INK_800),
    }


def with_classes(source):
    first = next((l.strip() for l in source.splitlines() if l.strip() and not l.strip().startswith('%%')), '')
    if not first.startswith(CLASS_DIAGRAMS):
        return source
    defined = set(re.findall(r'^\s*classDef\s+(\w+)', source, re.M))
    extra = [f'    classDef {k} {v}' for k, v in class_defs().items() if k not in defined]
    return source.rstrip('\n') + '\n' + '\n'.join(extra) + '\n'


def font_css():
    """@font-face rules for the brand fonts, as data URIs (no file:// CORS trouble in Chrome).
       Generated at build time from kit._FONT_FILES; never committed."""
    rules = []
    for family in (kit.UI, kit.DISPLAY):
        f = kit._FONT_FILES.get(family)
        if f and Path(f).exists():
            b64 = base64.b64encode(Path(f).read_bytes()).decode()
            rules.append(f'@font-face{{font-family:"{family}";src:url(data:font/ttf;base64,{b64}) format("truetype");'
                         f'font-weight:100 900;font-style:normal;}}')
    return '\n'.join(rules)


def brand_css():
    """Rules the theme variables do not reach, then the fonts."""
    rules = [
        f'.grid .tick line{{stroke:{HEX(kit.CLOUD)} !important;opacity:1}}',
        '.grid path{stroke-width:0}',
        f'.grid .tick text{{fill:{HEX(kit.INK_MUTED)}}}',
        f'.cluster-label text,.cluster-label span{{font-weight:700;fill:{HEX(kit.FOREST)};color:{HEX(kit.FOREST)}}}',
        f'.sectionTitle{{fill:{HEX(kit.FOREST)};font-weight:700}}',
        f'.edgeLabel rect,.labelBkg{{fill:{HEX(kit.WHITE)};opacity:1}}',
    ]
    return '\n'.join(rules) + '\n' + font_css()


def with_gantt_defaults(source):
    """No 'today' line: a plan printed today is read next week."""
    if source.lstrip().startswith('gantt') and 'todayMarker' not in source:
        head, _, rest = source.partition('\n')
        return f'{head}\n    todayMarker off\n{rest}'
    return source


def strip_fonts(svg):
    return re.sub(r'@font-face\s*\{[^}]*\}', '', svg)


# ── tools ────────────────────────────────────────────────────────────────────
INSTALL = ('mermaid-cli (mmdc) not found. Install it with `npm install -g @mermaid-js/mermaid-cli`, '
           'or set SV_MMDC to the mmdc binary.')


def find_mmdc():
    cands = [os.environ.get('SV_MMDC'), shutil.which('mmdc'),
             kit.REPO_PACKAGES.parent / 'node_modules' / '.bin' / 'mmdc',
             Path.home() / 'Projects/Servantium/decks/node_modules/.bin/mmdc']
    for c in cands:
        if c and Path(c).exists():
            return Path(c)
    raise FileNotFoundError(INSTALL)


def _node_modules(mmdc):
    """puppeteer for the frame render: the node_modules mmdc came from, else SV_NODE_PATH."""
    for c in (Path(mmdc).parent.parent, Path(mmdc).resolve().parents[2] if len(Path(mmdc).resolve().parents) > 2 else None,
              os.environ.get('SV_NODE_PATH'), kit.REPO_PACKAGES.parent / 'node_modules'):
        if c and (Path(c) / 'puppeteer').exists():
            return str(c)
    raise FileNotFoundError('puppeteer not found next to mmdc. Set SV_NODE_PATH to a node_modules that has it.')


_PRINT_JS = r"""
const puppeteer = require('puppeteer');
(async () => {
  const [htmlPath, W, H, pdfPath, pngPath] = process.argv.slice(2);
  const b = await puppeteer.launch({ headless: 'new' });
  const p = await b.newPage();
  await p.setViewport({ width: +W, height: +H, deviceScaleFactor: 2 });
  await p.goto('file://' + htmlPath, { waitUntil: 'load' });
  await p.evaluate(() => document.fonts.ready);
  await p.pdf({ path: pdfPath, width: W + 'px', height: H + 'px', printBackground: true, pageRanges: '1' });
  await p.screenshot({ path: pngPath, clip: { x: 0, y: 0, width: +W, height: +H } });
  await b.close();
})();
"""


# ── frame ────────────────────────────────────────────────────────────────────
def _size(svg):
    m = re.search(r'viewBox="\s*([-\d.]+)[ ,]+([-\d.]+)[ ,]+([-\d.]+)[ ,]+([-\d.]+)\s*"', svg)
    if not m:
        raise RuntimeError('mermaid SVG has no viewBox')
    return float(m.group(3)), float(m.group(4))


def _wrap(txt, width_px, size_px, font=None):
    words, lines, cur = str(txt).split(), [], ''
    for w in words:
        t = f'{cur} {w}'.strip()
        if cur and kit.text_w_in(t, size_px * 0.75, font=font or kit.UI) * 96 > width_px:
            lines.append(cur); cur = w
        else:
            cur = t
    return lines + ([cur] if cur else [])


def _fmt_date(d):
    try:
        x = dt.date.fromisoformat(str(d))
        return f'{x:%B} {x.day}, {x.year}'
    except ValueError:
        return str(d)


def frame(spec, raw):
    """Title, subtitle and eyebrow above; caption under; a rule and the footer line with the
       brand logo at the foot. The Mermaid SVG nests inside, untouched."""
    w, h = _size(raw)
    pad = 44
    W = max(w + 2 * pad, spec.get('width') or 0, 760)
    inner = W - 2 * pad
    o, y = [], pad
    eyebrow = '  ·  '.join(x for x in (spec['client'] if not str(spec['client']).startswith('_') else '',
                                       _fmt_date(spec['date']) if spec.get('date') else '') if x)
    if eyebrow:
        y += 12
        o.append(f'<text x="{pad}" y="{y}" font-family=\'{FONT_STACK}\' font-size="12" font-weight="700" '
                 f'letter-spacing="1.4" fill="{HEX(kit.GREEN_600)}">{html.escape(eyebrow.upper())}</text>')
        y += 14
    for line in _wrap(spec.get('title') or spec['mermaid'], inner, 30, kit.DISPLAY):
        y += 36
        o.append(f'<text x="{pad}" y="{y}" font-family=\'{DISPLAY_STACK}\' font-size="30" '
                 f'fill="{HEX(kit.FOREST)}">{html.escape(line)}</text>')
    if spec.get('subtitle'):
        y += 6
        for line in _wrap(spec['subtitle'], inner, 16):
            y += 22
            o.append(f'<text x="{pad}" y="{y}" font-family=\'{FONT_STACK}\' font-size="16" '
                     f'fill="{HEX(kit.INK_MUTED)}">{html.escape(line)}</text>')
    y += 28
    body = re.sub(r'^<\?xml[^>]*>\s*', '', raw.strip())
    body = re.sub(r'<svg\b([^>]*?)\swidth="[^"]*"', r'<svg\1', body, count=1)
    body = re.sub(r'<svg\b([^>]*?)\sheight="[^"]*"', r'<svg\1', body, count=1)
    body = re.sub(r'<svg\b([^>]*?)\sstyle="[^"]*"', r'<svg\1', body, count=1)
    x0 = pad + (inner - w) / 2
    body = body.replace('<svg', f'<svg x="{x0:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}"', 1)
    o.append(body)
    y += h
    if spec.get('caption'):
        y += 10
        for line in _wrap(spec['caption'], inner, 13):
            y += 19
            o.append(f'<text x="{pad}" y="{y}" font-family=\'{FONT_STACK}\' font-size="13" '
                     f'fill="{HEX(kit.INK_MUTED)}">{html.escape(line)}</text>')
    y += 26
    o.append(f'<line x1="{pad}" y1="{y}" x2="{W - pad}" y2="{y}" stroke="{HEX(kit.CLOUD)}" stroke-width="1"/>')
    y += 24
    o.append(f'<text x="{pad}" y="{y}" font-family=\'{FONT_STACK}\' font-size="12" '
             f'fill="{HEX(kit.INK_MUTED)}">{html.escape(kit.FOOTER_TEXT)}</text>')
    if kit.LOGO_ON_LIGHT and Path(kit.LOGO_ON_LIGHT).exists():
        from PIL import Image
        with Image.open(kit.LOGO_ON_LIGHT) as im:
            lw, lh = im.size
        hh = 20
        ww = hh * lw / lh
        uri = 'data:image/png;base64,' + base64.b64encode(Path(kit.LOGO_ON_LIGHT).read_bytes()).decode()
        o.append(f'<image x="{W - pad - ww:.1f}" y="{y - hh + 4:.1f}" width="{ww:.1f}" height="{hh}" href="{uri}"/>')
    H = y + pad - 8
    head = (f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" '
            f'width="{W:.0f}" height="{H:.0f}" viewBox="0 0 {W:.0f} {H:.0f}">'
            f'<rect width="100%" height="100%" fill="{HEX(kit.WHITE)}"/>')
    return head + ''.join(o) + '</svg>', W, H


# ── build ────────────────────────────────────────────────────────────────────
def build(spec_path, out_dir=None):
    spec = load(spec_path)
    out = Path(out_dir or Path(spec['_path']).parent / 'out')
    work = out / '.mermaid'
    work.mkdir(parents=True, exist_ok=True)
    stem = f'{spec["client"]} {spec["mermaid"]}'.strip()
    mmdc = find_mmdc()

    css = work / 'brand-fonts.css'
    css.write_text(brand_css())
    cfg = work / 'config.json'
    cfg.write_text(json.dumps(config(), indent=1))
    src = work / f'{stem}.mmd'
    src.write_text(with_gantt_defaults(with_classes(spec['source'])))
    raw = work / f'{stem}.raw.svg'
    r = subprocess.run([str(mmdc), '-i', str(src), '-o', str(raw), '-c', str(cfg), '-C', str(css),
                        '-b', HEX(kit.WHITE), '-q'], capture_output=True, text=True, timeout=180)
    if r.returncode != 0 or not raw.exists():
        msg = (r.stderr or r.stdout).strip().splitlines()
        raise SpecError(f'{Path(spec["_path"]).name}: mermaid could not draw this source:\n  '
                        + '\n  '.join(msg[-8:]))
    raw_svg = raw.read_text()
    if spec.get('frame', True):
        svg_text, W, H = frame(spec, raw_svg)
    else:
        svg_text = re.sub(r'^<\?xml[^>]*>\s*', '', raw_svg.strip())
        W, H = _size(raw_svg)
        svg_text = re.sub(r'<svg\b([^>]*?)\swidth="[^"]*"', r'<svg\1', svg_text, count=1)
        svg_text = re.sub(r'<svg\b([^>]*?)\sheight="[^"]*"', r'<svg\1', svg_text, count=1)
        svg_text = svg_text.replace('<svg', f'<svg width="{W:.0f}" height="{H:.0f}"', 1)
    lean = svg_text if spec.get('embed_font') else strip_fonts(svg_text)
    svg = out / f'{stem}.svg'
    svg.write_text(lean)

    page = work / f'{stem}.html'
    page.write_text(f'<!doctype html><html><head><meta charset="utf-8"><style>{font_css()}\n'
                    f'html,body{{margin:0;padding:0;background:{HEX(kit.WHITE)}}}</style></head>'
                    f'<body>{lean}</body></html>')
    js = work / 'print.cjs'
    js.write_text(_PRINT_JS)
    pdf, png = out / f'{stem}.pdf', out / f'{stem}.png'
    env = {**os.environ, 'NODE_PATH': _node_modules(mmdc)}
    r = subprocess.run(['node', str(js), str(page), str(int(round(W))), str(int(round(H))), str(pdf), str(png)],
                       capture_output=True, text=True, env=env, timeout=180)
    if r.returncode != 0:
        raise RuntimeError(f'printing {svg.name} failed: {r.stderr.strip()[-600:]}')
    return {'svg': svg, 'png': png, 'pdf': pdf, 'size': (W, H)}


if __name__ == '__main__':
    try:
        res = build(sys.argv[1])
    except (SpecError, FileNotFoundError) as e:
        sys.exit(f'sv: {e}')
    for k in ('svg', 'png', 'pdf'):
        print(f'  {k:<5}{res[k]}')
