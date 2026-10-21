"""Servantium document kit: brand primitives and slide chrome.

Colours and fonts are GENERATED from Verdant (see tokens.py and scripts/sync_tokens.py);
nothing here types a hex value. Logos and company facts come from @servantium/brand.

Every slide is built on a real layout of the Servantium template, so titles are titles,
the footer comes from the master, and a person can keep editing the file with
"New slide" in PowerPoint or Google Slides. Blocks (blocks.py) draw on the canvas the
layout leaves free.

Fonts: Playfair Display + Source Sans 3 must be installed for text measurement.
"""
from pathlib import Path
from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE
from pptx.oxml.ns import qn
import copy

from . import tokens as T
from . import brands as _brands

PKG = Path(__file__).resolve().parent
ASSETS = PKG / 'assets'
REPO_PACKAGES = PKG.parents[2]                  # packages/
BRAND = REPO_PACKAGES / 'brand'
BRAND_ASSETS = BRAND / 'assets'

# The active brand (SV_BRAND, default servantium). Its colour roles and fonts are laid
# over Verdant's tokens HERE, once, so every constant below and every module that reads
# T.COLORS sees the same brand. Servantium states no colour roles, so it is pure Verdant.
ACTIVE = _brands.ACTIVE
T.COLORS.setdefault('color-accent-3', T.COLORS['color-amber'])     # Verdant's chart accents 5 and 6
T.COLORS.setdefault('color-accent-4', T.COLORS['color-coral'])
T.COLORS.update(ACTIVE.token_overrides())
for _role, _key in (('display', 'font-display'), ('body', 'font-body')):
    if ACTIVE.fonts.get(_role, {}).get('family'):
        T.FONTS[_key] = ACTIVE.fonts[_role]['family']

# Built templates: Servantium's stay at dist/ (their published names); every other brand
# gets dist/<id>/ so no brand's template is ever overwritten by another's.
if ACTIVE.id == _brands.DEFAULT:
    DIST = PKG.parents[1] / 'dist'
elif ACTIVE.root.parent == _brands.BUILTIN:
    DIST = PKG.parents[1] / 'dist' / ACTIVE.id
else:                                    # an imported company: its templates stay with its brand,
    DIST = ACTIVE.root / 'dist'          # in the workspace, never in this public repo
TEMPLATE_PPTX = DIST / f'{ACTIVE.short} Slides Template.pptx'
TEMPLATE_DOCX = DIST / f'{ACTIVE.short} Document Template.docx'
TEMPLATE_XLSX = DIST / f'{ACTIVE.short} Workbook Template.xlsx'


def _rgb(token):
    h = T.COLORS[token].lstrip('#')
    return RGBColor(int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))


# ---------------------------------------------------------------- brand
# The engine's historical names, each bound to the Verdant token it has always matched.
GREEN       = _rgb('color-green')
GREEN_600   = _rgb('color-green-hover')
GREEN_300   = _rgb('color-jade')
FOREST      = _rgb('color-deep-forest')
FOREST_900  = _rgb('color-forest')
MINT        = _rgb('color-soft-mint')
MINT_TINT   = _rgb('color-mint-tint')
INK         = _rgb('color-ink')
INK_800     = _rgb('color-ink-soft')           # document extension, see sync_tokens.py
ON_FOREST        = _rgb('color-on-forest')         # document extension
ON_FOREST_MUTED  = _rgb('color-on-forest-muted')   # document extension
INK_MUTED   = _rgb('color-slate')
CLOUD       = _rgb('color-cloud-grey')
MIST        = _rgb('color-mist-grey')
WHITE       = _rgb('color-white')
CORAL       = _rgb('color-coral')
SLATE       = _rgb('color-slate-blue')
AMBER       = _rgb('color-amber')
TEAL        = _rgb('color-deep-teal')
SUCCESS     = _rgb('color-success')         # status green (RAG, done); GREEN is the brand primary
ACCENT_3    = _rgb('color-accent-3')        # chart series 5 and 6 (status colours stay AMBER / CORAL)
ACCENT_4    = _rgb('color-accent-4')

DISPLAY = T.FONTS['font-display']
UI      = T.FONTS['font-body']

LOGO_ON_LIGHT = ACTIVE.logo('on_light')
LOGO_ON_DARK  = ACTIVE.logo('on_dark')
MARK_ON_DARK  = ACTIVE.logo('mark_on_dark') or LOGO_ON_DARK
MARK_ON_LIGHT = ACTIVE.logo('mark_on_light') or LOGO_ON_LIGHT

W, H    = Inches(13.333), Inches(7.5)
MARGIN  = Inches(0.62)
BODY_W  = W - 2 * MARGIN
FOOTER_Y = Inches(6.86)

BRAND_NAME = ACTIVE.name                 # running text: "Prepared by", metadata author
BRAND_SHORT = ACTIVE.short               # footers, tight labels
FOOTER_TEXT = ACTIVE.footer              # 'Servantium  ·  Confidential'
COPYRIGHT = f'© 2026 {ACTIVE.legal_name}'
HOUSE = ACTIVE.is_house                  # Servantium's own voice and selling rules apply


# ---------------------------------------------------------------- helpers
def rect(slide, x, y, w, h, fill=None, line=None, line_w=Pt(1), shape=MSO_SHAPE.RECTANGLE):
    s = slide.shapes.add_shape(shape, x, y, w, h)
    if fill is None:
        s.fill.background()
    else:
        s.fill.solid(); s.fill.fore_color.rgb = fill
    if line is None:
        s.line.fill.background()
    else:
        s.line.color.rgb = line; s.line.width = line_w
    s.shadow.inherit = False
    if s.has_text_frame:
        s.text_frame.clear()
    return s


def text(slide, x, y, w, h, runs, *, align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP,
         line_spacing=None, space_after=Pt(0)):
    """runs = [(string, {font kwargs}), ...] or [[(str, kw), (str, kw)], ...] for mixed paragraphs."""
    tb = slide.shapes.add_textbox(x, y, w, h)
    tf = tb.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    tf.vertical_anchor = anchor
    paras = runs if isinstance(runs[0], list) else [[r] for r in runs]
    for i, para in enumerate(paras):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = align
        p.space_after = space_after
        if line_spacing:
            p.line_spacing = line_spacing
        for s_txt, kw in para:
            r = p.add_run(); r.text = s_txt
            f = r.font
            f.name = kw.get('font', UI)
            f.size = Pt(kw.get('size', 14))
            f.bold = kw.get('bold', False)
            f.italic = kw.get('italic', False)
            f.color.rgb = kw.get('color', INK_800)
            if kw.get('spacing'):
                r._r.get_or_add_rPr().set('spc', str(int(kw['spacing'] * 100)))
    return tb


def eyebrow(slide, x, y, label, color=GREEN_600, w=None):
    return text(slide, x, y, w or Inches(6), Inches(0.24),
                [(label.upper(), dict(size=9.5, bold=True, color=color, spacing=1.6))])


def title(slide, x, y, s, *, size=30, color=FOREST, w=None, font=DISPLAY):
    ww = w or BODY_W
    # Measured height: the old fixed 0.9in box clipped any headline that wrapped.
    return text(slide, x, y, ww, block_h(s, ww / 914400, size, spacing=1.08, font=font),
                [(s, dict(font=font, size=size, bold=False, color=color))],
                line_spacing=1.06)


def body(slide, x, y, w, paras, *, size=13.5, color=INK_800, spacing=1.34):
    return text(slide, x, y, w, Inches(2), [(p, dict(size=size, color=color)) for p in paras],
                line_spacing=spacing, space_after=Pt(9))


# Real text metrics. Estimating wrapped-line counts from a chars-per-inch constant
# was wrong in both directions: too low and every heading opened a gap beneath it,
# too high and the heading ran into its own subhead. These measure the actual
# outlines, so block_h() is correct for any string at any size.
def _find_font(filename):
    # macOS user fonts first, then the usual Linux locations (CI runs on Linux).
    for d in (Path.home() / 'Library/Fonts', Path('/Library/Fonts'),
              Path.home() / '.local/share/fonts', Path('/usr/share/fonts/truetype/servantium')):
        if (d / filename).exists():
            return d / filename
    return Path.home() / 'Library/Fonts' / filename      # reported missing by `sv doctor`


def _brand_font_file(role, default):
    f = ACTIVE.fonts.get(role, {}).get('file', default)
    local = ACTIVE.root / 'fonts' / f            # a brand may carry its own font files
    return local if local.exists() else _find_font(f)


_FONT_FILES = {
    DISPLAY: _brand_font_file('display', 'PlayfairDisplay[wght].ttf'),
    UI:      _brand_font_file('body', 'SourceSans3[wght].ttf'),
}
_font_cache = {}


def _font(name, size_pt, bold=False):
    key = (name, round(size_pt, 1), bold)
    if key not in _font_cache:
        from PIL import ImageFont
        path = _FONT_FILES.get(name)
        # 4x oversample, then divide back: PIL rounds to integer pixels.
        f = ImageFont.truetype(str(path), int(round(size_pt * 4)))
        try:
            f.set_variation_by_axes([700 if bold else 400])
        except Exception:
            pass
        _font_cache[key] = f
    return _font_cache[key]


def text_w_in(txt, size_pt, *, font=UI, bold=False):
    """Rendered width of `txt` in inches at `size_pt`."""
    try:
        return _font(font, size_pt, bold).getlength(txt) / 4.0 / 72.0
    except Exception:
        return len(txt) * size_pt * 0.5 / 72.0        # crude, but only if the font is missing


def est_lines(txt, width_in, size, factor=None, *, font=UI, bold=False):
    """Greedy word wrap against real glyph widths."""
    words, lines, cur = str(txt).split(), 1, 0.0
    space = text_w_in(' ', size, font=font, bold=bold)
    for w in words:
        ww = text_w_in(w, size, font=font, bold=bold)
        if cur and cur + space + ww > width_in:
            lines += 1; cur = ww
        else:
            cur = cur + space + ww if cur else ww
    return lines


def block_h(txt, width_in, size, spacing=1.3, factor=None, *, font=UI, bold=False):
    return Inches(est_lines(txt, width_in, size, font=font, bold=bold) * size * spacing / 72.0)


_line_cache = {}


def line_factor(font=UI):
    """A line's height as a multiple of the font size, as Keynote and PowerPoint lay it out:
       the font's own ascender, descender and line gap (1.33 for Playfair, 1.42 for Source
       Sans), not the 1.2 most code assumes. Boxes sized on 1.08 were too short, and Keynote
       shrank every title to fit them."""
    if font not in _line_cache:
        try:
            from fontTools.ttLib import TTFont
            t = TTFont(str(_FONT_FILES[font]), lazy=True)
            hh = t['hhea']
            _line_cache[font] = (hh.ascent - hh.descent + hh.lineGap) / t['head'].unitsPerEm
        except Exception:
            _line_cache[font] = 1.2
    return _line_cache[font]


def text_box_h(txt, width_in, size, *, font=UI, bold=False, line_spacing=1.0):
    """The height a text placeholder needs in Keynote and PowerPoint: lines x size x the
       font's real line factor x the paragraph's line spacing (the layout's lnSpc)."""
    lines = est_lines(txt, width_in, size, font=font, bold=bold)
    return Inches(lines * size * line_factor(font) * line_spacing / 72.0)


def bullets(slide, x, y, w, items, *, size=13, color=INK_800, dot=GREEN, gap=Inches(0.16)):
    """Each item is (bold_lead, rest) or a plain string. Height is measured, not guessed."""
    yy = y
    w_in = w.inches - 0.24
    for it in items:
        txt = (it[0] + '  ' + it[1]) if isinstance(it, tuple) else it
        h = block_h(txt, w_in, size)
        rect(slide, x, yy + Inches(0.075), Inches(0.07), Inches(0.07), fill=dot, shape=MSO_SHAPE.OVAL)
        if isinstance(it, tuple):
            runs = [[(it[0] + '  ', dict(size=size, bold=True, color=FOREST)),
                     (it[1], dict(size=size, color=color))]]
        else:
            runs = [[(it, dict(size=size, color=color))]]
        text(slide, x + Inches(0.24), yy, w - Inches(0.24), h, runs, line_spacing=1.3)
        yy += h + gap
    return yy


def picture(slide, path, x, y, w=None, h=None, *, border=True, shadow=True):
    pic = slide.shapes.add_picture(str(path), x, y, width=w, height=h)
    if border:
        ln = pic.line
        ln.color.rgb = CLOUD
        ln.width = Pt(0.75)
    if shadow:
        _soft_shadow(pic)
    return pic


def _soft_shadow(shape):
    """python-pptx has no shadow API; drop in the DrawingML directly."""
    spPr = shape._element.spPr
    for tag in ('a:effectLst',):
        for e in spPr.findall(qn(tag)):
            spPr.remove(e)
    from lxml import etree
    ns = 'http://schemas.openxmlformats.org/drawingml/2006/main'
    eff = etree.SubElement(spPr, f'{{{ns}}}effectLst')
    sh = etree.SubElement(eff, f'{{{ns}}}outerShdw')
    sh.set('blurRad', '180000'); sh.set('dist', '38000'); sh.set('dir', '5400000')
    sh.set('rotWithShape', '0')
    clr = etree.SubElement(sh, f'{{{ns}}}srgbClr'); clr.set('val', '0D1F17')
    alpha = etree.SubElement(clr, f'{{{ns}}}alpha'); alpha.set('val', '16000')


def slide_number_field(slide, x, y, w, color=INK_MUTED, size=9.5, align=PP_ALIGN.RIGHT):
    """A real <fld type="slidenum"> so numbering survives reordering."""
    tb = slide.shapes.add_textbox(x, y, w, Inches(0.24))
    tf = tb.text_frame; tf.word_wrap = False
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    p = tf.paragraphs[0]; p.alignment = align
    from lxml import etree
    a = 'http://schemas.openxmlformats.org/drawingml/2006/main'
    fld = etree.SubElement(p._p, f'{{{a}}}fld')
    fld.set('id', '{B1D6F1A4-9C1E-4A2F-9F53-7C2A4B8E1D33}'); fld.set('type', 'slidenum')
    rPr = etree.SubElement(fld, f'{{{a}}}rPr')
    rPr.set('lang', 'en-US'); rPr.set('sz', str(int(size * 100)))
    lat = etree.SubElement(rPr, f'{{{a}}}latin'); lat.set('typeface', UI)
    sf = etree.SubElement(rPr, f'{{{a}}}solidFill')
    c = etree.SubElement(sf, f'{{{a}}}srgbClr'); c.set('val', f'{color}')
    t = etree.SubElement(fld, f'{{{a}}}t'); t.text = '2'
    return tb


def footer(slide, *, dark=False):
    """No-op. The footer (logo, copyright, rule) lives on the template master now,
       and the slide number is a real placeholder. Kept so old build scripts run."""
    return None


# ---------------------------------------------------------------- template + layouts
PH_EYEBROW, PH_LEDE, PH_SOURCE, PH_SLIDENUM = 10, 11, 13, 12
PH_BODY, PH_BODY2, PH_PICTURE = 1, 2, 14


def new_deck(template=None) -> Presentation:
    """Open the Servantium template and strip its example slides. The master, the
       layouts and the theme stay, so every slide added is on a real layout."""
    path = Path(template) if template else TEMPLATE_PPTX
    if not path.exists():
        raise FileNotFoundError(
            f'Template not built: {path}. Run `sv templates` (or python -m servantium_documents.templates.build_pptx).')
    prs = Presentation(str(path))
    lst = prs.slides._sldIdLst
    for sld in list(lst):
        prs.part.drop_rel(sld.rId)
        lst.remove(sld)
    return prs


def layout(prs, name):
    for lay in prs.slide_masters[0].slide_layouts:
        if lay.name == name:
            return lay
    names = ', '.join(l.name for l in prs.slide_masters[0].slide_layouts)
    raise KeyError(f'No layout {name!r}. The template has: {names}')


def blank(prs):
    """A slide on the Blank layout: footer and number from the master, nothing else."""
    s = prs.slides.add_slide(layout(prs, 'Blank'))
    fill(s, {})
    add_slide_number(s)
    return s


def _ph_key(shape):
    t = shape.placeholder_format.type
    return 'title' if t in (1, 3) else shape.placeholder_format.idx    # TITLE, CENTER_TITLE


def fill(slide, values):
    """values: {'title' | idx: str | [str, ...] | None}. A None value means "leave it,
       it is already populated" (pictures). Unlisted placeholders are removed so edit
       mode stays clean; the layout still offers them on a new slide."""
    for shape in list(slide.placeholders):
        key = _ph_key(shape)
        if key in values:
            v = values[key]
            if v is None:
                continue
            paras = v if isinstance(v, list) else [v]
            tf = shape.text_frame
            tf.text = paras[0]
            for extra in paras[1:]:
                tf.add_paragraph().text = extra
            _lock_text(shape)
        elif shape.placeholder_format.idx != PH_SLIDENUM:
            shape._element.getparent().remove(shape._element)


def _theme_face(shape):
    """The face a placeholder's text takes from its layout: the display face for
       '+mj-lt' (titles), the body face for '+mn-lt', or a named face."""
    try:
        base = shape._base_placeholder
    except Exception:
        base = None
    els = [base._element] if base is not None else []
    for el in els:
        for latin in el.iter('{http://schemas.openxmlformats.org/drawingml/2006/main}latin'):
            face = latin.get('typeface') or ''
            if face == '+mj-lt':
                return DISPLAY
            if face == '+mn-lt':
                return UI
            if face:
                return face
    ph_type = str(shape.placeholder_format.type)
    return DISPLAY if ('TITLE' in ph_type and 'SUB' not in ph_type) else UI


def _lock_text(shape):
    """Text the engine placed and measured must not be resized by the app that opens it.
       The template's placeholders inherit "shrink text on overflow" (normAutofit), and
       Keynote applies it on import, so titles came out smaller than designed. Turn it off
       on this slide's copy, and name the face on every run so no app has to resolve the
       theme's font references."""
    from pptx.enum.text import MSO_AUTO_SIZE
    shape.text_frame.auto_size = MSO_AUTO_SIZE.NONE
    face = _theme_face(shape)
    for p in shape.text_frame.paragraphs:
        for r in p.runs:
            if not r.font.name:
                r.font.name = face


def placeholder(slide, key):
    for shape in slide.placeholders:
        if _ph_key(shape) == key:
            return shape
    return None


def add_slide_number(slide):
    """Instantiate the layout's slide-number placeholder with a live field."""
    if placeholder(slide, PH_SLIDENUM) is not None:
        return
    src = next((p for p in slide.slide_layout.placeholders if p.placeholder_format.idx == PH_SLIDENUM), None)
    if src is None:
        return
    from lxml import etree
    el = copy.deepcopy(src._element)
    body = el.find(qn('p:txBody'))
    for p_ in body.findall(qn('a:p')):
        body.remove(p_)
    A = 'http://schemas.openxmlformats.org/drawingml/2006/main'
    body.append(etree.fromstring(
        f'<a:p xmlns:a="{A}"><a:fld id="{{B6F15528-21DE-4FAA-801E-634DDDAF4B2B}}" type="slidenum">'
        f'<a:rPr lang="en-US"/><a:t>&#8249;#&#8250;</a:t></a:fld></a:p>'))
    slide.shapes._spTree.append(el)


def _place(shape, y, h):
    """Move a placeholder on THIS slide only (the layout is untouched).

    All four coordinates must be written. A placeholder with no position of its own
    inherits one from the layout; setting only top and height makes python-pptx write
    a transform with ZERO width, and the text vanishes. (Found by the first torture
    test render: every measured title was invisible.)"""
    left, width = shape.left, shape.width          # inherited from the layout
    shape.left, shape.top, shape.width, shape.height = int(left), int(y), int(width), int(h)


def notes(slide, txt):
    """Speaker notes. They carry the talk; the slide stays light."""
    if txt:
        slide.notes_slide.notes_text_frame.text = str(txt).strip()


# ---------------------------------------------------------------- slide types
TITLE_SIZE, LEDE_SIZE = 30, 15
TITLE_W_IN, LEDE_W_IN = 11.9, 11.4
TITLE_TOP = Inches(0.96)


def cover(prs, *, eyebrow_text, headline, subhead, meta=None, prepared_for=None):
    s = prs.slides.add_slide(layout(prs, 'Cover'))
    fill(s, {PH_EYEBROW: eyebrow_text.upper(), 'title': headline, PH_BODY: subhead,
             **({PH_LEDE: meta} if meta else {})})
    if prepared_for:
        cobrand(s, *prepared_for)
    return s


def logo_fit(path, max_w_in, max_h_in):
    """width= or height= kwargs that fit a logo inside a box, for add_picture calls."""
    from PIL import Image
    im = Image.open(path)
    if im.height / im.width * max_w_in > max_h_in:
        return {'height': Inches(max_h_in)}
    return {'width': Inches(max_w_in)}


def cobrand(s, name, logo=None):
    """'Prepared for' lockup, top right of the cover, level with the brand logo. A reader's
       logo is drawn for light grounds, so it sits on a white chip; with no logo, the name."""
    from PIL import Image
    right = W - MARGIN
    chip_h = Inches(0.62)
    y = Inches(0.55) + Inches(0.02)
    if logo:
        im = Image.open(logo)
        box_w, box_h = Inches(1.9), Inches(0.42)
        sc = min(box_w / im.width, box_h / im.height)
        w_, h_ = int(im.width * sc), int(im.height * sc)
        rgba = im.convert('RGBA')
        corners = [rgba.getpixel(p) for p in ((0, 0), (im.width - 1, 0), (0, im.height - 1), (im.width - 1, im.height - 1))]
        tile = all(c[3] > 250 for c in corners)          # the logo brings its own ground: no chip
        if tile:
            sc = min(Inches(1.2) / im.width, chip_h / im.height)
            w_, h_ = int(im.width * sc), int(im.height * sc)
        chip_w = w_ if tile else w_ + Inches(0.4)
        cx = right - chip_w
        if not tile:
            chip = rect(s, cx, y, chip_w, chip_h, fill=WHITE, shape=MSO_SHAPE.ROUNDED_RECTANGLE)
            chip.adjustments[0] = 0.18
        s.shapes.add_picture(str(logo), cx + (chip_w - w_) // 2, y + (chip_h - h_) // 2, width=w_, height=h_)
        left = cx
    else:
        tw = Inches(text_w_in(name, 16, font=DISPLAY) + 0.1)
        left = right - tw
        text(s, left, y + Inches(0.12), tw, Inches(0.4), [(name, dict(font=DISPLAY, size=16, color=WHITE))],
             align=PP_ALIGN.RIGHT)
    lab_w = Inches(1.4)
    text(s, left - lab_w - Inches(0.16), y + chip_h // 2 - Inches(0.1), lab_w, Inches(0.2),
         [('PREPARED FOR', dict(size=8.5, bold=True, color=ON_FOREST_MUTED, spacing=1.4))], align=PP_ALIGN.RIGHT)
    return s


def section(prs, *, number, heading, sub=None, tracker=None, current=None):
    s = prs.slides.add_slide(layout(prs, 'Section'))
    fill(s, {PH_EYEBROW: number, 'title': heading, **({PH_LEDE: sub} if sub else {})})
    # The number in the body face: Playfair's old-style figures turned "01" into "o1".
    num = placeholder(s, PH_EYEBROW)
    if num is not None:
        for p in num.text_frame.paragraphs:
            for r in p.runs:
                r.font.name = UI
                r.font.bold = True
    add_slide_number(s)
    if tracker:
        n = len(tracker)
        x0, w, y = Inches(0.82), Inches(11.9), Inches(5.5)
        gap = Inches(0.12)
        tw = (w - gap * (n - 1)) // n
        for i, name in enumerate(tracker):
            x = x0 + i * (tw + gap)
            on = i == current
            rect(s, x, y + Inches(0.5), tw, Inches(0.05) if on else Emu(19050), fill=GREEN if on else CLOUD)
            text(s, x, y + Inches(0.12), tw, Inches(0.3),
                 [[(f'{i + 1:02d}  ', dict(size=10.5, bold=True, color=GREEN_600 if on else INK_MUTED)),
                   (name, dict(size=13, bold=on, color=FOREST if on else INK_MUTED))]])
    return s


def content(prs, *, eyebrow_text=None, heading, sub=None, source=None, layout_name='Title Only',
            extra=None, measured=True):
    """A content slide on a real layout. Returns (slide, y) where y is where the canvas
       starts. The title and lede boxes are resized to their MEASURED text, like the old
       engine, so a one-line title does not leave a two-line gap. Layouts whose
       decorations are drawn at fixed positions (Comparison, Big Numbers) pass
       measured=False and keep the layout's geometry."""
    s = prs.slides.add_slide(layout(prs, layout_name))
    vals = {'title': heading}
    if eyebrow_text:
        vals[PH_EYEBROW] = eyebrow_text.upper()
    if sub:
        vals[PH_LEDE] = sub
    if source:
        vals[PH_SOURCE] = source if source.lower().startswith('source') else f'Source: {source}'
    vals.update(extra or {})
    fill(s, vals)
    add_slide_number(s)
    if not measured:
        lede = placeholder(s, PH_LEDE)
        bottom = (lede.top + lede.height) if lede is not None else placeholder(s, 'title').top + placeholder(s, 'title').height
        return s, bottom + Inches(0.22)

    # Positions keep the measured rhythm; each box is as tall as its text really sets
    # (the font's own line height x the layout's 104% and 128% line spacing).
    title_h = block_h(heading, TITLE_W_IN, TITLE_SIZE, spacing=1.08, font=DISPLAY)
    t = placeholder(s, 'title')
    _place(t, TITLE_TOP, max(title_h + Inches(0.06),
                             text_box_h(heading, TITLE_W_IN, TITLE_SIZE, font=DISPLAY, line_spacing=1.04)
                             + Inches(0.02)))
    y = TITLE_TOP + title_h + Inches(0.16)
    if sub:
        lede_h = block_h(sub, LEDE_W_IN, LEDE_SIZE, spacing=1.32)
        _place(placeholder(s, PH_LEDE), y, max(lede_h + Inches(0.04),
                                               text_box_h(sub, LEDE_W_IN, LEDE_SIZE, line_spacing=1.28)
                                               + Inches(0.02)))
        y += lede_h + Inches(0.1)
    return s, y + Inches(0.22)


def closing(prs, *, headline, lines, cta=None):
    s = prs.slides.add_slide(layout(prs, 'Closing'))
    fill(s, {'title': headline, PH_BODY: list(lines)})
    # The layout's title box holds one line. A second line grew down into the asks,
    # so grow the box upward instead and keep its bottom edge where the layout put it.
    t = s.shapes.title
    extra = est_lines(headline, t.width / 914400, 40, font=DISPLAY) - 1
    if extra > 0:
        line = Inches(40 * line_factor(DISPLAY) / 72.0)      # the layout sets it at 40 pt, 100%
        _place(t, t.top - line * extra, t.height + line * extra)
    add_slide_number(s)
    if cta:
        asks = placeholder(s, PH_BODY)
        yy = asks.top
        for ln in lines:
            yy += block_h(ln, 8.7, 15, spacing=1.3) + Pt(10)
        box = rect(s, MARGIN, yy + Inches(0.3), Inches(4.15), Inches(0.62), fill=GREEN)
        text(s, MARGIN, yy + Inches(0.46), Inches(4.15), Inches(0.3),
             [(cta, dict(size=14, bold=True, color=FOREST))], align=PP_ALIGN.CENTER)
    return s


def quote(prs, *, text_, attribution):
    s = prs.slides.add_slide(layout(prs, 'Quote'))
    fill(s, {PH_BODY: text_, PH_LEDE: attribution})
    add_slide_number(s)
    return s


# ---------------------------------------------------------------- icons
# ONE icon system out of two families.
#
# The product is built on Lucide (lucide-react), so Lucide is the house set and any
# icon that exists there wins. Material Symbols fills the gaps, because Lucide is
# ~2,000 icons and Material is ~3,700 and the difference is mostly the abstract
# business vocabulary decks need (governance, insights, milestones).
#
# They are reconciled, not just mixed. Two settings do it, both measured rather than
# guessed (see the comparison sheet that produced them):
#   * Material ROUNDED, not Outlined. Rounded terminals are what makes Lucide look
#     like Lucide; Outlined next to Lucide reads as two sets.
#   * Material at wght 600 and 1.09x scale. At the default 400 it is visibly thinner
#     and smaller than Lucide at the same nominal size.
# Per-family scale, never per-icon: normalising each glyph to fill its box would
# throw away the size relationships the icon designers intended.
_ICON_DIR = ASSETS / 'icons'
# Rendered icons are a cache, not source: keep them out of the repository.
_ICON_PNG = Path.home() / '.cache' / 'servantium-documents' / 'icons'
_LUCIDE_TTF = _ICON_DIR / 'lucide.ttf'
_MATERIAL_TTF = _ICON_DIR / 'MaterialSymbolsRounded.ttf'
MATERIAL_WGHT = 600
MATERIAL_SCALE = 1.09

_lucide_map = None
_material_map = None


def _lucide():
    global _lucide_map
    if _lucide_map is None:
        import json, re
        _lucide_map = {k: chr(int(re.sub(r'\D', '', v['unicode'])))
                       for k, v in json.loads((_ICON_DIR / 'lucide-info.json').read_text()).items()}
    return _lucide_map


def _material():
    global _material_map
    if _material_map is None:
        _material_map = {}
        for line in (_ICON_DIR / 'codepoints-rounded.txt').read_text().splitlines():
            if ' ' in line:
                n, c = line.split(' ', 1)
                _material_map[n] = chr(int(c, 16))
    return _material_map


def resolve_icon(name):
    """(family, glyph) for an icon name. Lucide first, Material as fallback.

    Accepts either convention: 'circle-check' and 'circle_check' both work, so a
    caller does not have to remember which family an icon came from.
    """
    kebab, snake = name.replace('_', '-'), name.replace('-', '_')
    lu, mr = _lucide(), _material()
    if kebab in lu: return 'lucide', lu[kebab]
    if snake in mr: return 'material', mr[snake]
    if snake in lu: return 'lucide', lu[snake]
    if kebab in mr: return 'material', mr[kebab]
    raise KeyError(f'icon {name!r} is in neither Lucide nor Material Symbols')


def icon_exists(name):
    try:
        resolve_icon(name); return True
    except KeyError:
        return False


def icon_png(name, color=GREEN_600, px=256):
    """Render an icon to a cached transparent PNG and return the path.

    Rasterising is not a shortcut: python-pptx accepts only BMP/GIF/JPEG/PNG/TIFF/WMF,
    so an icon font or an SVG cannot be placed directly. Vector originals ship
    alongside in assets/icons/svg/ for anyone working in Figma or Slides by hand.
    """
    from PIL import Image, ImageDraw, ImageFont
    fam, ch = resolve_icon(name)
    rgb = ((color >> 16) & 255, (color >> 8) & 255, color & 255) if isinstance(color, int) else (
        color[0], color[1], color[2])
    tag = f'{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}'
    _ICON_PNG.mkdir(parents=True, exist_ok=True)
    out = _ICON_PNG / f'{fam}-{name}-{tag}-{px}.png'
    if out.exists():
        return out
    if fam == 'lucide':
        f = ImageFont.truetype(str(_LUCIDE_TTF), px)
    else:
        size = int(px * MATERIAL_SCALE)
        f = ImageFont.truetype(str(_MATERIAL_TTF), size)
        try:
            f.set_variation_by_axes([0, 0, float(size), float(MATERIAL_WGHT)])
        except Exception:
            pass
    pad = int(px * 0.6)
    img = Image.new('RGBA', (px + pad, px + pad), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    b = d.textbbox((0, 0), ch, font=f)
    d.text((-b[0] + (px + pad - (b[2] - b[0])) // 2,
            -b[1] + (px + pad - (b[3] - b[1])) // 2), ch, font=f, fill=rgb + (255,))
    img.save(out)
    return out


def icon(slide, name, x, y, size, color=GREEN_600):
    """Place an icon. `size` is the square box it occupies."""
    return slide.shapes.add_picture(str(icon_png(name, color)), x, y, width=size, height=size)


# ---------------------------------------------------------------- theme
def apply_brand_theme(prs, *, name=None):
    """Kept for old build scripts. The template already carries the brand theme, written
       from tokens by brand.py; this rewrites it the same way, never from literals."""
    from . import brand
    brand.apply_theme_to_package(prs.part.package)
    return prs
