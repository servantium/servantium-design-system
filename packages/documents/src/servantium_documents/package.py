"""Make every .pptx open in strict readers, and prove it before it ships.

PowerPoint and LibreOffice quietly repair malformed files; Keynote and Google Slides refuse
them with "the file couldn't be opened". Two defects reached customers before this existed
(2026-10-09):

* a coordinate written as a decimal ("0.0"): DrawingML positions and sizes are whole EMUs;
* a notes master that the presentation never lists: python-pptx relates the notes master
  but does not add <p:notesMasterIdLst>, which the format requires whenever there are notes.

`finalize(prs)` fixes both on the way out. `audit(path)` re-reads the saved file and reports
anything a strict reader would reject; `sv build` turns those into errors.
"""
import re
import zipfile
from lxml import etree

A = 'http://schemas.openxmlformats.org/drawingml/2006/main'
P = 'http://schemas.openxmlformats.org/presentationml/2006/main'
R = 'http://schemas.openxmlformats.org/officeDocument/2006/relationships'
RT_NOTES_MASTER = 'http://schemas.openxmlformats.org/officeDocument/2006/relationships/notesMaster'

# Attributes that must be whole numbers wherever they appear in DrawingML/PresentationML.
INT_ATTRS = {'x', 'y', 'cx', 'cy', 'w', 'h', 'sz', 'spc', 'rot', 'dist', 'dir', 'blurRad'}
_FLOAT = re.compile(r'-?\d+\.\d+')
_GEOM = {f'{{{A}}}off', f'{{{A}}}ext', f'{{{A}}}chOff', f'{{{A}}}chExt', f'{{{P}}}ext'}


def _round_floats(root):
    fixed = 0
    for el in root.iter():
        if not isinstance(el.tag, str):
            continue
        for k, v in el.attrib.items():
            if k in INT_ATTRS and _FLOAT.fullmatch(v or ''):
                el.set(k, str(int(round(float(v)))))
                fixed += 1
    return fixed


def _list_notes_master(prs):
    """Add <p:notesMasterIdLst> right after <p:sldMasterIdLst> when a notes master exists."""
    part = prs.part
    rid = next((r.rId for r in part.rels.values() if r.reltype == RT_NOTES_MASTER), None)
    if rid is None:
        return False
    root = part._element
    if root.find(f'{{{P}}}notesMasterIdLst') is not None:
        return False
    lst = etree.Element(f'{{{P}}}notesMasterIdLst')
    nm = etree.SubElement(lst, f'{{{P}}}notesMasterId')
    nm.set(f'{{{R}}}id', rid)
    root.find(f'{{{P}}}sldMasterIdLst').addnext(lst)
    return True


def finalize(prs):
    """Call right before prs.save(): returns what it fixed, for the build log."""
    fixed = {'decimal coordinates': 0, 'notes master listed': 0}
    for slide in prs.slides:
        fixed['decimal coordinates'] += _round_floats(slide._element)
        if slide.has_notes_slide:
            fixed['decimal coordinates'] += _round_floats(slide.notes_slide._element)
    if _list_notes_master(prs):
        fixed['notes master listed'] = 1
    return fixed


# ── audit: what a strict reader would reject ─────────────────────────────────
_SEQ = {
    'spPr': ['xfrm', 'custGeom', 'prstGeom', 'noFill', 'solidFill', 'gradFill', 'blipFill', 'pattFill', 'grpFill',
             'ln', 'effectLst', 'effectDag', 'scene3d', 'sp3d', 'extLst'],
    'ln': ['noFill', 'solidFill', 'gradFill', 'pattFill', 'prstDash', 'custDash', 'round', 'bevel', 'miter',
           'headEnd', 'tailEnd', 'extLst'],
    'rPr': ['ln', 'noFill', 'solidFill', 'gradFill', 'blipFill', 'pattFill', 'grpFill', 'effectLst', 'effectDag',
            'highlight', 'uLnTx', 'uLn', 'uFillTx', 'uFill', 'latin', 'ea', 'cs', 'sym', 'hlinkClick',
            'hlinkMouseOver', 'rtl', 'extLst'],
    'sp': ['nvSpPr', 'spPr', 'style', 'txBody', 'extLst'],
    'pic': ['nvPicPr', 'blipFill', 'spPr', 'style', 'extLst'],
}
_PRES_SEQ = ['sldMasterIdLst', 'notesMasterIdLst', 'handoutMasterIdLst', 'sldIdLst', 'sldSz', 'notesSz']


_A = '{http://schemas.openxmlformats.org/drawingml/2006/main}'
_P = '{http://schemas.openxmlformats.org/presentationml/2006/main}'


def _shrinkable(sp):
    """A placeholder holding text, with no autofit of its own, inherits the template's
       "shrink text on overflow". Keynote applies it on import and shrank every title."""
    if sp.find(f'{_P}nvSpPr/{_P}nvPr/{_P}ph') is None:
        return None
    body = sp.find(f'{_P}txBody')
    if body is None or not ''.join(t.text or '' for t in body.iter(f'{_A}t')).strip():
        return None
    bp = body.find(f'{_A}bodyPr')
    if bp is not None and (bp.find(f'{_A}noAutofit') is not None or bp.find(f'{_A}spAutoFit') is not None):
        return None
    name = sp.find(f'{_P}nvSpPr/{_P}cNvPr').get('name')
    return f'placeholder "{name}" can be shrunk by Keynote (inherits shrink-on-overflow; set noAutofit)'


def audit(path):
    """[(part, problem)] for anything Keynote or Google Slides would refuse. Empty is good."""
    out = []
    with zipfile.ZipFile(path) as z:
        bad = z.testzip()
        if bad:
            return [(bad, 'corrupt zip entry')]
        names = set(z.namelist())
        pres = etree.fromstring(z.read('ppt/presentation.xml'))
        kids = [etree.QName(c).localname for c in pres]
        order = [k for k in kids if k in _PRES_SEQ]
        if order != sorted(order, key=_PRES_SEQ.index):
            out.append(('ppt/presentation.xml', f'children out of order: {order}'))
        has_notes = any(n.startswith('ppt/notesSlides/') for n in names)
        if has_notes and 'notesMasterIdLst' not in kids:
            out.append(('ppt/presentation.xml', 'notes master exists but is not listed (<p:notesMasterIdLst>)'))
        for n in sorted(names):
            if not re.match(r'ppt/(slides|slideLayouts|slideMasters|notesSlides|notesMasters)/[^/]+\.xml$', n):
                continue
            root = etree.fromstring(z.read(n))
            for el in root.iter():
                if not isinstance(el.tag, str):
                    continue
                ln = etree.QName(el).localname
                for k, v in el.attrib.items():
                    if k in INT_ATTRS and _FLOAT.fullmatch(v or ''):
                        out.append((n, f'<{ln} {k}="{v}">: positions and sizes must be whole numbers'))
                if el.tag in _GEOM and el.get('cx') is not None:
                    try:
                        if int(el.get('cx')) < 0 or int(el.get('cy')) < 0:
                            out.append((n, f'<{ln}> negative size cx={el.get("cx")} cy={el.get("cy")}'))
                    except ValueError:
                        pass
                if ln == 'sp' and n.startswith('ppt/slides/'):
                    problem = _shrinkable(el)
                    if problem:
                        out.append((n, problem))
                seq = _SEQ.get(ln)
                if seq:
                    last = -1
                    for c in el:
                        if not isinstance(c.tag, str):
                            continue
                        cn = etree.QName(c).localname
                        if cn in seq:
                            i = seq.index(cn)
                            if i < last:
                                out.append((n, f'<{ln}> has <{cn}> after <{seq[last]}>'))
                            last = max(last, i)
    return out
