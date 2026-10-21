"""Brands and data binding. Brand switching happens per process (SV_BRAND), so the
cross-brand checks run the engine in a subprocess."""
import os
import re
import subprocess
import sys
from pathlib import Path

import pytest

from servantium_documents import bind, brands

PKG = Path(__file__).resolve().parents[1]
SRC = PKG / 'src' / 'servantium_documents'


def _in_brand(brand, code):
    env = dict(os.environ, SV_BRAND=brand)
    r = subprocess.run([sys.executable, '-c', code], env=env, capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    return r.stdout.strip()


def test_servantium_is_pure_verdant():
    b = brands.load('servantium')
    assert b.is_house and b.colors == {}
    assert b.logo('on_light').exists()


@pytest.mark.parametrize('bid', [b for b in brands.available() if b != 'servantium'])
def test_every_builtin_brand_loads_complete(bid):
    b = brands.load(bid)
    assert not b.is_house
    for role in ('primary', 'primary_strong', 'dark', 'ink', 'on_dark'):
        assert role in b.colors, f'{bid} is missing {role}'
    for which in ('on_light', 'on_dark', 'mark_on_dark'):
        assert b.logo(which) and b.logo(which).exists(), f'{bid} logo {which}'
    out = _in_brand(bid, 'from servantium_documents import kit; print(kit.DISPLAY, "|", kit.UI, "|", kit.COPYRIGHT, "|", '
                         'all(p.exists() for p in kit._FONT_FILES.values()))')
    display, body, copy, fonts_ok = [x.strip() for x in out.split('|')]
    assert display == b.fonts['display']['family'] and body == b.fonts['body']['family']
    assert b.legal_name in copy and fonts_ok == 'True'


def test_brand_colours_reach_the_kit():
    hx = _in_brand('lattica', 'from servantium_documents import kit; print("%02X%02X%02X" % tuple(kit.GREEN))')
    assert '#' + hx == brands.load('lattica').colors['primary'].upper()


def test_unknown_role_is_refused(tmp_path):
    b = brands.Brand(id='x', name='X', root=tmp_path, colors={'grren': '#123456'})
    with pytest.raises(brands.BrandError):
        b.token_overrides()


def test_no_servantium_literals_left_in_renderers():
    """Brand-specific words come from the brand. Docstrings and comments may mention it."""
    import ast
    # stylebook names the product its readers use (a 'Servantium' user tag), not a brand
    allowed = {'brands.py', 'tokens.py', 'drive.py', 'brand_import.py', 'stylebook.py'}
    for f in list(SRC.glob('*.py')) + list((SRC / 'templates').glob('*.py')):
        if f.name in allowed:
            continue
        tree = ast.parse(f.read_text())
        docs = {id(n.value) for n in ast.walk(tree) if isinstance(n, ast.Expr) and isinstance(n.value, ast.Constant)}
        for n in ast.walk(tree):
            if isinstance(n, ast.Constant) and isinstance(n.value, str) and id(n) not in docs:
                lit = n.value
                if 'Servantium' in lit and not any(ok in lit for ok in ('servantium-documents', 'Servantium-Work', 'Projects/Servantium')):
                    pytest.fail(f'{f.name}:{n.lineno} hardwires {lit!r}')


def test_bind_fills_strings_and_structures(tmp_path):
    (tmp_path / 'd.yaml').write_text('q: {total: 1234.4, rows: [{a: 1}, {a: 2}]}\nwhen: 2026-11-02\n')
    (tmp_path / 's.yaml').write_text('data: {d: d.yaml}\ndeck: "Fee {{ d.q.total | money }}"\nrows: "{{ d.q.rows }}"\n'
                                     'n: "{{ d.q.rows | sum(a) }}"\nday: "{{ d.when | date }}"\n')
    out, sha = bind.bind(tmp_path / 's.yaml')
    import yaml
    b = yaml.safe_load(out.read_text())
    assert b['deck'] == 'Fee $1,234' and b['rows'] == [{'a': 1}, {'a': 2}] and b['n'] == 3.0
    assert b['day'] == 'November 2, 2026' and sha


def test_bind_keeps_numbers_outside_decks(tmp_path):
    (tmp_path / 'd.yaml').write_text('q: {a: 1100000, b: 1036409.2, l: [x, y]}\n')
    (tmp_path / 's.yaml').write_text('data: {d: d.yaml}\nworkbook: W\nleft: "{{ d.q.a - d.q.b }}"\n'
                                     'txt: "{{ d.q.a - d.q.b | money2 }}"\n' + "j: '{{ d.q.l | join(\" / \") }}'\n")
    import yaml
    b = yaml.safe_load(bind.bind(tmp_path / 's.yaml')[0].read_text())
    assert b['left'] == 63590.8 and b['txt'] == '$63,590.80' and b['j'] == 'x / y'


def test_deck_loader_turns_numbers_into_text_only_where_text_is_wanted(tmp_path):
    from servantium_documents import spec as S
    (tmp_path / 'deck.yaml').write_text(
        'deck: T\nclient: _Sandbox\nslides:\n  - numbers:\n      title: Three.\n      stats:\n'
        '        - {value: 170, label: staff}\n        - {value: 2016, label: founded}\n        - {value: 4.5, label: x}\n')
    d = S.load(tmp_path / 'deck.yaml')
    vals = [s['value'] for s in d['slides'][0]['numbers']['stats']]
    assert vals == ['170', '2016', '4.5']


def test_bind_missing_path_is_an_error(tmp_path):
    (tmp_path / 'd.yaml').write_text('a: 1\n')
    (tmp_path / 's.yaml').write_text('data: {d: d.yaml}\ndeck: "{{ d.b }}"\n')
    with pytest.raises(bind.BindError):
        bind.bind(tmp_path / 's.yaml')
