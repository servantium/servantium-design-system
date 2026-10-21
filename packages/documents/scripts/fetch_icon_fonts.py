"""Fetch the Material Symbols Rounded font and its codepoints from Google.

They are 15 MB of someone else's font, so they are fetched at setup rather than stored
in this public repository. They are fetched TOGETHER: an icon name resolves to a
codepoint, and a codepoint list from one version against a font from another draws
the wrong glyph without any error.
"""
import sys
import urllib.request
from pathlib import Path

BASE = 'https://github.com/google/material-design-icons/raw/master/variablefont/'
STEM = 'MaterialSymbolsRounded%5BFILL%2CGRAD%2Copsz%2Cwght%5D'
DEST = Path(__file__).resolve().parents[1] / 'src' / 'servantium_documents' / 'assets' / 'icons'
FILES = {f'{STEM}.ttf': 'MaterialSymbolsRounded.ttf', f'{STEM}.codepoints': 'codepoints-rounded.txt'}


def main(force=False):
    if not force and all((DEST / local).exists() for local in FILES.values()):
        print('icon fonts present')
        return
    for remote, local in FILES.items():
        print(f'fetching {local} ...', flush=True)
        with urllib.request.urlopen(BASE + remote, timeout=120) as r:
            (DEST / local).write_bytes(r.read())
    print(f'icon fonts -> {DEST}')


if __name__ == '__main__':
    main(force='--force' in sys.argv)
