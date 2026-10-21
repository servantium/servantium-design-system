"""Servantium Word template.

THE ONE RULE THAT SHAPES THIS FILE. Google Docs keeps only its fixed style set on
import: Normal text, Title, Subtitle, Heading 1-6. Any custom paragraph style
("Servantium Body", "Callout") is flattened to direct formatting and disappears
from the style menu. So the brand goes INTO the built-in styles, never into custom
ones. Word users get a styles gallery that is the brand; Google users get the same
styles under the names Docs already uses.

Two more Google-driven choices:
  * Fonts are set explicitly on every style (w:rFonts), not only via the theme.
    Docs ignores theme fonts but honours explicit ones.
  * Tables carry direct cell formatting (shading, borders) rather than relying on
    a table style, which Docs does not keep.

Page is US Letter with 1in margins: our customers are American and so is the house
spelling.

Outputs:
    dist/Servantium Document Template.docx  -> Google: open, then File > Make a copy
    dist/Servantium.dotx                    -> Word: File > New from template
"""
import zipfile

from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.style import WD_STYLE_TYPE
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK, WD_LINE_SPACING, WD_TAB_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor, Emu

from .. import brand
from ..brand import K, hexof

DISPLAY, BODY = K.DISPLAY, K.UI
C = lambda rgb: RGBColor(rgb[0], rgb[1], rgb[2])


def set_fonts(style_or_run, face):
    """Explicit on all four slots. Google Docs reads ascii/hAnsi; Word uses the rest
       for East Asian and complex scripts, and a missing slot silently falls back."""
    rpr = style_or_run.element.get_or_add_rPr()
    rf = rpr.find(qn('w:rFonts'))
    if rf is None:
        rf = OxmlElement('w:rFonts')
        rpr.insert(0, rf)
    for slot in ('w:ascii', 'w:hAnsi', 'w:eastAsia', 'w:cs'):
        rf.set(qn(slot), face)
    for slot in ('w:asciiTheme', 'w:hAnsiTheme', 'w:eastAsiaTheme', 'w:cstheme'):
        if rf.get(qn(slot)) is not None:
            del rf.attrib[qn(slot)]


def reset(st):
    """python-docx's default template gives Title a rule underneath and Subtitle
       letter-spacing, both in the stock Office blue. Remove before branding."""
    ppr = st.element.find(qn('w:pPr'))
    if ppr is not None:
        for tag in ('w:pBdr',):
            for el in ppr.findall(qn(tag)):
                ppr.remove(el)
    rpr = st.element.find(qn('w:rPr'))
    if rpr is not None:
        for tag in ('w:spacing', 'w:color', 'w:kern', 'w:i', 'w:iCs'):
            for el in rpr.findall(qn(tag)):
                rpr.remove(el)


def style(doc, name, *, face=BODY, size=11, color=K.INK_800, bold=False, caps=False,
          before=0, after=8, line=1.3, keep_next=False, spacing=0):
    st = doc.styles[name]
    reset(st)
    f = st.font
    f.size, f.bold, f.color.rgb, f.all_caps = Pt(size), bold, C(color), caps
    f.italic = False
    set_fonts(st, face)
    if spacing:
        rpr = st.element.get_or_add_rPr()
        sp = OxmlElement('w:spacing'); sp.set(qn('w:val'), str(int(spacing * 20))); rpr.append(sp)
    pf = st.paragraph_format
    pf.space_before, pf.space_after = Pt(before), Pt(after)
    pf.line_spacing_rule = WD_LINE_SPACING.MULTIPLE
    pf.line_spacing = line
    pf.keep_with_next = keep_next
    return st


def shade(cell, hx):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement('w:shd')
    shd.set(qn('w:val'), 'clear'); shd.set(qn('w:color'), 'auto'); shd.set(qn('w:fill'), hx)
    tcPr.append(shd)


def borders(table, hx, size=4, inside_h=True):
    tbl = table._tbl
    tblPr = tbl.tblPr
    b = OxmlElement('w:tblBorders')
    for edge in ('top', 'left', 'bottom', 'right', 'insideH', 'insideV'):
        el = OxmlElement(f'w:{edge}')
        on = edge in ('top', 'bottom') or (edge == 'insideH' and inside_h)
        el.set(qn('w:val'), 'single' if on else 'nil')
        if on:
            el.set(qn('w:sz'), str(size)); el.set(qn('w:space'), '0'); el.set(qn('w:color'), hx)
        b.append(el)
    tblPr.append(b)


def widths(table, inches):
    """Fix the grid so every renderer honours the column widths."""
    table.autofit = False
    tbl = table._tbl
    grid = tbl.find(qn('w:tblGrid'))
    for gc, w in zip(grid.findall(qn('w:gridCol')), inches):
        gc.set(qn('w:w'), str(int(w * 1440)))
    tblPr = tbl.tblPr
    lay = OxmlElement('w:tblLayout'); lay.set(qn('w:type'), 'fixed'); tblPr.append(lay)
    tw = OxmlElement('w:tblW'); tw.set(qn('w:w'), str(int(sum(inches) * 1440))); tw.set(qn('w:type'), 'dxa')
    old = tblPr.find(qn('w:tblW'))
    if old is not None:
        tblPr.remove(old)
    tblPr.append(tw)
    for row in table.rows:
        for c, w in zip(row.cells, inches):
            c.width = Inches(w)


def cell_margins(table, top=80, bottom=80, left=120, right=120):
    tblPr = table._tbl.tblPr
    m = OxmlElement('w:tblCellMar')
    for side, v in (('top', top), ('left', left), ('bottom', bottom), ('right', right)):
        el = OxmlElement(f'w:{side}'); el.set(qn('w:w'), str(v)); el.set(qn('w:type'), 'dxa'); m.append(el)
    tblPr.append(m)


def run(p, text, *, face=BODY, size=None, color=None, bold=None, caps=False, spacing=0):
    r = p.add_run(text)
    set_fonts(r, face)
    if size: r.font.size = Pt(size)
    if color is not None: r.font.color.rgb = C(color)
    if bold is not None: r.font.bold = bold
    if caps: r.font.all_caps = True
    if spacing:
        rpr = r._r.get_or_add_rPr()
        sp = OxmlElement('w:spacing'); sp.set(qn('w:val'), str(int(spacing * 20))); rpr.append(sp)
    return r


def page_field(p, instr='PAGE'):
    """A real PAGE field. Word and Google both render it as the live page number."""
    for kind, txt in (('begin', None), ('instr', f' {instr} '), ('separate', None), ('text', '1'), ('end', None)):
        r = p.add_run()
        set_fonts(r, BODY); r.font.size = Pt(9); r.font.color.rgb = C(K.INK_MUTED)
        if kind == 'instr':
            it = OxmlElement('w:instrText'); it.set(qn('xml:space'), 'preserve'); it.text = txt; r._r.append(it)
        elif kind == 'text':
            t = OxmlElement('w:t'); t.text = txt; r._r.append(t)
        else:
            fc = OxmlElement('w:fldChar'); fc.set(qn('w:fldCharType'), kind); r._r.append(fc)


def footer(sec, width_in):
    """Company and marking on the left, the page number in the bottom-right corner, where
       Word readers look for it. The right tab sits on the right margin of this section,
       so a landscape section needs its own footer at its own width."""
    fp = sec.footer.paragraphs[0]
    for r in list(fp.runs):
        r._r.getparent().remove(r._r)
    # Word's built-in Footer style carries a centre tab at 3.25in and a right tab at 6.5in.
    # Left alone, the centre tab catches the page number and puts it mid-page.
    tabs = fp.paragraph_format.tab_stops
    for pos in (3.25, 6.5):
        if pos != width_in:
            tabs.add_tab_stop(Inches(pos), WD_TAB_ALIGNMENT.CLEAR)
    tabs.add_tab_stop(Inches(width_in), WD_TAB_ALIGNMENT.RIGHT)
    run(fp, f'{K.FOOTER_TEXT}\t', size=9, color=K.INK_MUTED)
    page_field(fp)
    return fp


def callout(doc, label, body, *, tone=K.GREEN, fill=K.MINT_TINT):
    """A one-cell table: the only 'box' that survives Word -> Google intact.
       Floating text boxes and drawing shapes do not."""
    t = doc.add_table(rows=1, cols=1)
    t.alignment = WD_TABLE_ALIGNMENT.LEFT
    c = t.cell(0, 0)
    shade(c, hexof(fill))
    tcPr = c._tc.get_or_add_tcPr()
    tb = OxmlElement('w:tcBorders')
    left = OxmlElement('w:left')
    left.set(qn('w:val'), 'single'); left.set(qn('w:sz'), '24'); left.set(qn('w:color'), hexof(tone))
    tb.append(left); tcPr.append(tb)
    cell_margins(t, top=140, bottom=140, left=220, right=220)
    widths(t, [6.5])
    p = c.paragraphs[0]
    p.paragraph_format.space_after = Pt(0)
    run(p, label + ' ', bold=True, color=K.FOREST)
    run(p, body, color=K.INK_800)
    doc.add_paragraph()
    return t


def data_table(doc, head, rows, widths_in):
    t = doc.add_table(rows=1 + len(rows), cols=len(head))
    t.alignment = WD_TABLE_ALIGNMENT.LEFT
    t.autofit = False
    borders(t, hexof(K.CLOUD))
    cell_margins(t)
    for j, h in enumerate(head):
        c = t.cell(0, j)
        shade(c, hexof(K.FOREST))
        p = c.paragraphs[0]; p.paragraph_format.space_after = Pt(0)
        run(p, h.upper(), size=8.5, bold=True, color=K.WHITE, spacing=0.6)
    # Repeat the header row on every page a long table spans.
    trPr = t.rows[0]._tr.get_or_add_trPr()
    th = OxmlElement('w:tblHeader'); th.set(qn('w:val'), 'true'); trPr.append(th)
    for i, row in enumerate(rows, start=1):
        for j, v in enumerate(row):
            c = t.cell(i, j)
            if i % 2 == 0:
                shade(c, hexof(K.MIST))
            p = c.paragraphs[0]; p.paragraph_format.space_after = Pt(0)
            run(p, v, size=10, bold=(j == 0), color=K.FOREST if j == 0 else K.INK_800)
    widths(t, widths_in)
    doc.add_paragraph()
    return t


def build():
    doc = Document()
    brand.apply_theme_to_package(doc.part.package)

    # ── page ─────────────────────────────────────────────────────────────────
    sec = doc.sections[0]
    sec.page_width, sec.page_height = Inches(8.5), Inches(11)
    for side in ('left_margin', 'right_margin', 'top_margin', 'bottom_margin'):
        setattr(sec, side, Inches(1))
    sec.header_distance = sec.footer_distance = Inches(0.45)
    sec.different_first_page_header_footer = True   # the cover carries its own logo

    # ── built-in styles, branded ─────────────────────────────────────────────
    style(doc, 'Normal', size=11, after=8, line=1.3)
    style(doc, 'Title', face=DISPLAY, size=32, color=K.FOREST, after=6, line=1.05)
    style(doc, 'Subtitle', size=14, color=K.INK_MUTED, after=24, line=1.3)
    style(doc, 'Heading 1', face=DISPLAY, size=22, color=K.FOREST, before=22, after=8, line=1.1, keep_next=True)
    style(doc, 'Heading 2', size=14, color=K.FOREST, bold=True, before=16, after=6, line=1.2, keep_next=True)
    style(doc, 'Heading 3', size=10, color=K.GREEN_600, bold=True, caps=True, spacing=0.8,
          before=12, after=4, line=1.2, keep_next=True)
    style(doc, 'List Bullet', size=11, after=4, line=1.3)
    style(doc, 'List Number', size=11, after=4, line=1.3)
    style(doc, 'Quote', face=DISPLAY, size=15, color=K.FOREST, before=10, after=10, line=1.3)
    style(doc, 'Caption', size=9, color=K.INK_MUTED, after=10)
    # Heading 1 carries a rule underneath, the one flourish in a quiet document.
    h1 = doc.styles['Heading 1'].element.get_or_add_pPr()
    pb = OxmlElement('w:pBdr'); bot = OxmlElement('w:bottom')
    bot.set(qn('w:val'), 'single'); bot.set(qn('w:sz'), '6'); bot.set(qn('w:space'), '4')
    bot.set(qn('w:color'), hexof(K.GREEN)); pb.append(bot); h1.append(pb)

    # ── header and footer (pages 2+) ─────────────────────────────────────────
    hp = sec.header.paragraphs[0]
    hp.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    hp.add_run().add_picture(str(brand.LOGO_ON_LIGHT), **K.logo_fit(brand.LOGO_ON_LIGHT, 1.15, 0.34))
    footer(sec, 6.5)

    # ── cover ────────────────────────────────────────────────────────────────
    p = doc.add_paragraph()
    p.add_run().add_picture(str(brand.LOGO_ON_LIGHT), **K.logo_fit(brand.LOGO_ON_LIGHT, 1.9, 0.6))
    p.paragraph_format.space_after = Pt(96)
    p = doc.add_paragraph()
    run(p, 'CLIENT  ·  DOCUMENT TYPE', size=9.5, bold=True, color=K.GREEN_600, spacing=1.2)
    p.paragraph_format.space_after = Pt(6)
    doc.add_paragraph('Document title goes here', style='Title')
    doc.add_paragraph('One line on what this document decides, and who it is for.', style='Subtitle')

    meta = doc.add_table(rows=4, cols=2)
    borders(meta, hexof(K.CLOUD))
    cell_margins(meta, top=70, bottom=70, left=0, right=120)
    for i, (k, v) in enumerate([('Prepared for', '[Client name]'), ('Prepared by', K.BRAND_NAME),
                                ('Date', '[Month Day, Year]'), ('Status', 'Draft for review')]):
        a, b = meta.cell(i, 0), meta.cell(i, 1)
        for c_ in (a, b):
            c_.paragraphs[0].paragraph_format.space_after = Pt(0)
        run(a.paragraphs[0], k.upper(), size=8.5, bold=True, color=K.INK_MUTED, spacing=0.6)
        run(b.paragraphs[0], v, size=10.5, color=K.INK_800)
    widths(meta, [1.6, 4.9])
    doc.add_paragraph().add_run().add_break(WD_BREAK.PAGE)

    # ── body: the method, shown in the order a consulting document uses ───────
    doc.add_paragraph('Executive summary', style='Heading 1')
    p = doc.add_paragraph()
    run(p, 'Start with the answer. ', bold=True, color=K.FOREST)
    run(p, 'The first paragraph states the recommendation and why, so a reader who stops here '
           'has what they need. Everything after it is support, in order of importance.')
    for t in ('Three supporting points, each a full sentence that could stand alone.',
              'Each one is proved in its own section below.',
              'If there is a decision, name it, the owner and the date.'):
        doc.add_paragraph(t, style='List Bullet')

    callout(doc, 'Decision needed:', 'What you are asking the reader to agree to, by when.')

    doc.add_paragraph('Situation', style='Heading 1')
    doc.add_paragraph('What is true today, stated plainly. No history the reader already knows.')
    doc.add_paragraph('Complication', style='Heading 2')
    doc.add_paragraph('What changed, or what is at risk, that makes a decision necessary now.')

    doc.add_paragraph('Recommendation', style='Heading 1')
    doc.add_paragraph('Options considered', style='Heading 3')
    data_table(doc, ['Option', 'What it means', 'Trade-off'], [
        ['A. Recommended', 'The option we are proposing, in one line.', 'What it costs or risks.'],
        ['B. Alternative', 'The credible alternative.', 'Why it is second.'],
        ['C. Do nothing', 'What happens if nothing changes.', 'The cost of waiting.'],
    ], [1.6, 2.9, 2.0])
    p = doc.add_paragraph('Table 1. Sources go in the caption. An inferred figure says "probably" and gives its basis.',
                          style='Caption')

    doc.add_paragraph('Next steps', style='Heading 1')
    for t in ('Step, owner, date.', 'Step, owner, date.', 'Step, owner, date.'):
        doc.add_paragraph(t, style='List Number')

    doc.add_paragraph('A line worth pulling out, set in the Quote style.', style='Quote')

    doc.add_paragraph('Style reference', style='Heading 1')
    doc.add_paragraph(
        'Every style here is a built-in Word style, so it survives import to Google Docs with its '
        'name. Title, Subtitle, Heading 1 to 3, Normal, List Bullet, List Number, Quote and Caption '
        'are all branded. Use them from the style menu rather than formatting text by hand.')
    return doc


def save(doc):
    docx_path = K.TEMPLATE_DOCX
    dotx_path = brand.DIST / f'{K.BRAND_SHORT}.dotx'
    doc.save(str(docx_path))
    with zipfile.ZipFile(docx_path) as zin, zipfile.ZipFile(dotx_path, 'w', zipfile.ZIP_DEFLATED) as zout:
        for item in zin.infolist():
            data = zin.read(item.filename)
            if item.filename == '[Content_Types].xml':
                data = data.replace(
                    b'application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml',
                    b'application/vnd.openxmlformats-officedocument.wordprocessingml.template.main+xml')
            zout.writestr(item, data)
    return docx_path, dotx_path


if __name__ == '__main__':
    a, b = save(build())
    print(f'-> {a.name}, {b.name}')
