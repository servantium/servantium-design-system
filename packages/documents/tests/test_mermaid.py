"""Branded Mermaid: the theme follows the active brand, and a build writes SVG, PNG and PDF."""
import shutil
import textwrap
from pathlib import Path

import pytest

from servantium_documents import kit, mermaid as M
from servantium_documents.brand import hexof
from servantium_documents.spec import SpecError

PKG = Path(__file__).resolve().parents[1]
EX = PKG / 'examples'


def _has_mmdc():
    try:
        M.find_mmdc()
        return shutil.which('node') is not None
    except FileNotFoundError:
        return False


needs_mmdc = pytest.mark.skipif(not _has_mmdc(), reason='mermaid-cli (mmdc) not installed')


def test_theme_values_come_from_kit():
    v = M.theme_variables()
    assert v['primaryColor'] == '#' + hexof(kit.MINT)
    assert v['primaryBorderColor'] == '#' + hexof(kit.GREEN)
    assert v['primaryTextColor'] == '#' + hexof(kit.FOREST)
    assert v['lineColor'] == '#' + hexof(kit.INK_MUTED)
    assert v['secondaryColor'] == '#' + hexof(kit.MINT_TINT)
    assert v['tertiaryColor'] == '#' + hexof(kit.MIST)
    assert v['critBkgColor'] == '#' + hexof(kit.CORAL)
    assert v['fontFamily'].startswith(f'"{kit.UI}"')
    assert v['pie1'] == '#' + hexof(kit.GREEN)
    cfg = M.config()
    assert cfg['theme'] == 'base' and cfg['flowchart']['htmlLabels'] is False


def test_brand_classes_are_added_to_flowcharts_only():
    src = M.with_classes('flowchart LR\n  A --> B:::primary\n')
    assert f'classDef primary fill:#{hexof(kit.FOREST)}' in src
    assert 'classDef warn' in src
    seq = 'sequenceDiagram\n  A->>B: hi\n'
    assert M.with_classes(seq) == seq
    own = M.with_classes('graph TD\n  A-->B\n  classDef primary fill:#000\n')
    assert own.count('classDef primary') == 1                 # the author's own wins


def test_gantt_drops_the_today_line():
    assert 'todayMarker off' in M.with_gantt_defaults('gantt\n  dateFormat YYYY-MM-DD\n')
    assert M.with_gantt_defaults('flowchart LR\n') == 'flowchart LR\n'


def test_font_css_embeds_the_body_font_without_a_path():
    css = M.font_css()
    if not Path(kit._FONT_FILES[kit.UI]).exists():
        pytest.skip('brand font not installed')
    assert f'font-family:"{kit.UI}"' in css and 'base64,' in css and '/Users/' not in css


def test_spec_needs_exactly_one_source(tmp_path):
    p = tmp_path / 'm.yaml'
    p.write_text('mermaid: X\nclient: Acme Labs\n')
    with pytest.raises(SpecError, match='source'):
        M.load(p)
    (tmp_path / 'd.mmd').write_text('flowchart LR\n A-->B\n')
    p.write_text('mermaid: X\nclient: Acme Labs\nfile: d.mmd\n')
    assert M.load(p)['source'].startswith('flowchart')


def test_missing_mmdc_explains_how_to_install(monkeypatch):
    monkeypatch.setenv('SV_MMDC', '/nonexistent/mmdc')
    monkeypatch.setattr(M.shutil, 'which', lambda *_: None)
    monkeypatch.setattr(M.Path, 'home', lambda: Path('/nonexistent'))
    monkeypatch.setattr(M.kit, 'REPO_PACKAGES', Path('/nonexistent/packages'))
    with pytest.raises(FileNotFoundError, match='npm install -g @mermaid-js/mermaid-cli'):
        M.find_mmdc()


@needs_mmdc
@pytest.mark.parametrize('name', ['mermaid-flow', 'mermaid-gantt', 'mermaid-sequence'])
def test_build_writes_svg_png_pdf(tmp_path, name):
    shutil.copy(EX / f'{name}.yaml', tmp_path / f'{name}.yaml')
    r = M.build(tmp_path / f'{name}.yaml')
    for k in ('svg', 'png', 'pdf'):
        assert r[k].exists() and r[k].stat().st_size > 1000, k
        assert r[k].parent == tmp_path / 'out'
    svg = r['svg'].read_text()
    assert 'foreignObject' not in svg                         # opens the same in Office and Inkscape
    assert '@font-face' not in svg                            # lean by default
    assert kit.FOOTER_TEXT in svg                             # the frame
    from PIL import Image
    with Image.open(r['png']) as im:
        assert im.size[0] == 2 * round(r['size'][0])          # 2x


@needs_mmdc
def test_bad_source_is_a_spec_error(tmp_path):
    p = tmp_path / 'm.yaml'
    p.write_text(textwrap.dedent('''
        mermaid: Broken
        client: Acme Labs
        source: |
          flowchart LR
            A -->
    '''))
    with pytest.raises(SpecError, match='could not draw'):
        M.build(p)
