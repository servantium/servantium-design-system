"""PDF and contact sheets. The PDF is what customers receive; the contact sheet is
what Claude looks at before calling a deck done. Both come from the same render."""
import shutil
import subprocess
import tempfile
from pathlib import Path


def soffice():
    exe = shutil.which('soffice') or '/Applications/LibreOffice.app/Contents/MacOS/soffice'
    if not Path(exe).exists():
        raise FileNotFoundError('LibreOffice (soffice) not found. Install it: brew install --cask libreoffice')
    return exe


def to_pdf(src):
    """Render .pptx/.docx/.xlsx to PDF next to the source. Returns the PDF path."""
    src = Path(src)
    # A private profile avoids clashing with a LibreOffice window the user has open.
    with tempfile.TemporaryDirectory() as prof:
        subprocess.run([soffice(), f'-env:UserInstallation=file://{prof}', '--headless',
                        '--convert-to', 'pdf', '--outdir', str(src.parent), str(src)],
                       check=True, capture_output=True, timeout=300)
    pdf = src.with_suffix('.pdf')
    if not pdf.exists():
        raise RuntimeError(f'LibreOffice did not produce {pdf.name}')
    return pdf


def contact_sheet(pdf, out_png, *, cols=3, dpi=55, pages=None):
    """Every page on one image, numbered, so a whole deck can be checked at a glance."""
    import pymupdf
    from PIL import Image, ImageDraw
    doc = pymupdf.open(str(pdf))
    idx = list(range(len(doc))) if pages is None else [p - 1 for p in pages]
    tiles = []
    for i in idx:
        pix = doc[i].get_pixmap(dpi=dpi)
        im = Image.frombytes('RGB', (pix.width, pix.height), pix.samples)
        d = ImageDraw.Draw(im)
        d.rectangle((0, 0, 34, 22), fill=(2, 62, 37))
        d.text((8, 5), str(i + 1), fill=(255, 255, 255))
        tiles.append(im)
    w, h = tiles[0].size
    rows = (len(tiles) + cols - 1) // cols
    g = 10
    sheet = Image.new('RGB', (cols * w + (cols + 1) * g, rows * h + (rows + 1) * g), (154, 163, 173))
    for j, im in enumerate(tiles):
        sheet.paste(im, (g + (j % cols) * (w + g), g + (j // cols) * (h + g)))
    sheet.save(out_png)
    return out_png, len(doc)


def page_png(pdf, page, out_png, dpi=110):
    """One page at reading size, for a close look."""
    import pymupdf
    pymupdf.open(str(pdf))[page - 1].get_pixmap(dpi=dpi).save(str(out_png))
    return out_png
