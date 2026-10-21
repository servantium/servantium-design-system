"""sv: the Servantium documents command.

    sv new <client> "<deck>"   start a deck spec in ~/Servantium-Work/<client>/<deck>/
    sv storyboard <spec>       the titles alone, in order
    sv check <spec>            every rule, before anything renders
    sv build <spec>            check, render, PDF, contact sheet
    sv publish <spec>          copy the latest build into the client's Drive folder
    sv pull <client> [match]   copy the latest matching file out of Drive
    sv ls <client>             what is in the client's folder
    sv icons <word>            find icon names
    sv templates [--brand id]  rebuild the three templates (or --all brands)
    sv brand list|show|import  brands: what exists, what one holds, import a company's brand
    sv doctor                  check fonts, LibreOffice, template, Drive, Finder
"""
import argparse
import json
import re
import shutil
import sys
from pathlib import Path

from . import __version__, brands, check as C, drive, kit, output, spec as S


def _out_dir(spec):
    return Path(spec['_path']).parent / 'out'


def _slug(s):
    return re.sub(r'[^a-z0-9]+', '-', s.lower()).strip('-')


def _report(findings):
    errors = [f for f in findings if f.level == 'error']
    warns = [f for f in findings if f.level == 'warning']
    for f in sorted(findings, key=lambda f: (f.slide, f.level != 'error')):
        print(f)
    print(f'\n  {len(errors)} error(s), {len(warns)} warning(s)')
    return errors


STARTERS = Path(__file__).resolve().parents[2] / 'starters'


def _starters():
    return {p.stem: p for p in sorted(STARTERS.glob('*.yaml'))} if STARTERS.exists() else {}


def cmd_new(a):
    if a.list:
        for name, p in _starters().items():
            first = next((l[2:].strip() for l in p.read_text().splitlines() if l.startswith('# ')), '')
            print(f'  {name:<26} {first}')
        return
    if not a.client or not a.deck:
        sys.exit('sv new <client> "<name>" [--type <starter>] [--brand <id>]   (sv new --list for types)')
    d = drive.WORK / a.client / _slug(a.deck)
    d.mkdir(parents=True, exist_ok=True)
    if a.type:
        src = _starters().get(a.type)
        if not src:
            sys.exit(f'No starter "{a.type}". Run `sv new --list`.')
        text = src.read_text().replace('{{NAME}}', a.deck).replace('{{CLIENT}}', a.client)
        text = text.replace('{{BRAND}}', a.brand or 'servantium')
        kind = next((k for k in KINDS if text.lstrip().split('\n', 1)[0].startswith(k) or f'\n{k}:' in text), 'spec')
        p = d / ('deck.yaml' if kind == 'deck' else 'spec.yaml')
    else:
        p = d / 'deck.yaml'
        text = STARTER.format(deck=a.deck, client=a.client)
        if a.brand:
            text = text.replace(f'client: {a.client}', f'client: {a.client}\nbrand: {a.brand}', 1)
    if p.exists():
        sys.exit(f'{p} already exists')
    p.write_text(text)
    print(p)


def cmd_storyboard(a):
    from . import bind
    print(C.storyboard(S.load(bind.bind(a.spec)[0])))


def cmd_check(a):
    ensure_brand(a.spec, a._argv)
    from . import bind
    src, data_sha = bind.bind(a.spec)
    spec = S.load(src)
    if _report(C.check(spec)):
        sys.exit(1)


# ── kinds: one `sv build` for every document type ─────────────────────────────
# The top-level key names the kind. Each builder returns {ext: path}.
KINDS = ('deck', 'document', 'workbook', 'mermaid', 'diagram')


def _peek(path):
    """Top-level keys of a spec, without validating it (the kind's loader does that)."""
    import yaml
    try:
        d = yaml.safe_load(Path(path).read_text()) or {}
    except yaml.YAMLError as e:
        sys.exit(f'sv: {Path(path).name} is not valid YAML: {e}\n  Most often: a value with ": " or a comma '
                 'inside {...} or [...]. Put the value in double quotes.')
    if not isinstance(d, dict):
        sys.exit(f'sv: {path} is not a mapping')
    return d


def kind_of(d):
    for k in KINDS:
        if k in d:
            return k
    if 'lanes' in d and 'steps' in d:
        return 'diagram'
    sys.exit('sv: cannot tell what this spec builds. Start it with deck:, document:, workbook: or mermaid:')


def ensure_brand(path, argv):
    """Builds run in the spec's brand. kit binds colours and fonts at import, so a spec in
       another brand re-runs this command once with SV_BRAND set; every module then sees the
       same brand. Nothing is mutated mid-build."""
    import os
    want = str(_peek(path).get('brand') or '').strip().lower()
    if want and want != kit.ACTIVE.id:          # no brand: key keeps the active one (SV_BRAND or servantium)
        if os.environ.get('SV_BRAND_SWITCHED'):
            sys.exit(f'sv: could not switch to brand "{want}"')
        brands.find(want)                               # fail fast with the search path
        env = dict(os.environ, SV_BRAND=want, SV_BRAND_SWITCHED='1')
        os.execve(sys.executable, [sys.executable, '-m', 'servantium_documents.cli', *argv], env)


def _sha(path):
    """The spec's fingerprint, data files included, so a changed number forces a rebuild."""
    import hashlib
    from . import bind
    _, data_sha = bind.bind(path)
    return data_sha or hashlib.sha256(Path(path).read_bytes()).hexdigest()[:12]


def cmd_build(a):
    ensure_brand(a.spec, a._argv)
    from . import bind
    try:
        src, data_sha = bind.bind(a.spec)            # numbers from data files, if the spec has data:
    except bind.BindError as e:
        sys.exit(f'sv: {e}')
    raw = _peek(src)
    kind = kind_of(raw)
    if kind != 'deck':
        files = build_other(kind, src)
        out = Path(a.spec).resolve().parent / 'out'
        out.mkdir(exist_ok=True)
        rep = {'kind': kind, 'spec': str(Path(a.spec).resolve()), 'sha': _sha(a.spec), 'brand': kit.ACTIVE.id,
               'name': raw[kind], 'client': raw.get('client', '_Sandbox'), 'date': str(raw.get('date', '')),
               'drive': raw.get('drive', {}), 'files': {Path(p).suffix: str(p) for p in files.values() if p},
               'engine': __version__, 'findings': []}
        (out / f'report-{_slug(str(raw[kind]))}.json').write_text(json.dumps(rep, indent=1))
        for k, p in files.items():
            print(f'  {k:<8} {p}')
        for f in _OTHER_FINDINGS:
            print(f'  {f}' if f.lstrip().startswith(('warning', 'error')) else f'  warning  {f}')
        return
    spec = S.load(src)
    spec['_path'] = str(Path(a.spec).resolve())
    spec['_sha'] = data_sha or spec['_sha']
    findings = C.check(spec)
    if [f for f in findings if f.level == 'error'] and not a.force:
        _report(findings)
        sys.exit('\nFix the errors, or pass --force to build anyway.')
    out = _out_dir(spec)
    out.mkdir(exist_ok=True)
    owner = 'Sandbox ' if spec['client'] == drive.SANDBOX else '' if spec['client'].startswith('_') else f'{spec["client"]} '
    pptx = out / f'{owner}{spec["deck"]}.pptx'
    findings += render_(spec, pptx, out)
    errors = _report(findings)
    pdf = output.to_pdf(pptx)
    sheet, pages = output.contact_sheet(pdf, out / 'contact.png')
    rep = {'kind': 'deck', 'spec': spec['_path'], 'sha': spec['_sha'], 'brand': kit.ACTIVE.id,
           'name': spec['deck'], 'client': spec['client'], 'date': spec['date'], 'drive': spec.get('drive', {}),
           'pptx': str(pptx), 'pdf': str(pdf), 'files': {'.pptx': str(pptx), '.pdf': str(pdf)},
           'contact': str(sheet), 'pages': pages, 'engine': __version__,
           'findings': [f.__dict__ for f in findings]}
    (out / 'report.json').write_text(json.dumps(rep, indent=1))
    print(f'\n  {pages} slides')
    print(f'  pptx     {pptx}')
    print(f'  pdf      {pdf}')
    print(f'  contact  {sheet}')
    if errors:
        sys.exit(1)


def build_other(kind, path):
    if kind == 'document':
        from . import docs as M
    elif kind == 'workbook':
        from . import sheets as M
    elif kind == 'mermaid':
        from . import mermaid as M
    else:
        from . import diagram as M
    # Deliverables only: contact sheets are for looking, not for the customer's folder.
    res = M.build(path)
    found = res.get('findings') if res.get('findings') is not None else res.get('banned')
    _OTHER_FINDINGS[:] = [str(x) for x in (found or []) if not isinstance(found, (str, Path))]
    return {k: v for k, v in res.items() if isinstance(v, (str, Path)) and k not in ('contact', 'banned', 'findings')}


_OTHER_FINDINGS = []


def render_(spec, pptx, out):
    from .render import render
    return render(spec, pptx, out)


def _report_for(spec_path):
    from . import bind
    out = Path(spec_path).resolve().parent / 'out'
    raw = _peek(bind.bind(spec_path)[0])
    kind = kind_of(raw)
    rep = out / ('report.json' if kind == 'deck' else f'report-{_slug(str(raw[kind]))}.json')
    if not rep.exists():
        sys.exit('Nothing built yet. Run `sv build` first.')
    return json.loads(rep.read_text())


def cmd_publish(a):
    r = _report_for(a.spec)
    from . import bind
    src, data_sha = bind.bind(a.spec)
    now = data_sha or (S.load(a.spec)['_sha'] if r['kind'] == 'deck' else _sha(a.spec))
    if r['sha'] != now:
        sys.exit('The spec (or its data) changed since the last build. Run `sv build` again before publishing.')
    if [f for f in r['findings'] if f['level'] == 'error'] and not a.force:
        sys.exit('The last build had errors. Fix them, or pass --force.')
    d = r.get('drive') or {}
    if a.replace:
        # A revision replaces the published copy: the old files move to _Archive (same Drive IDs),
        # then the new copy takes the same name. The folder never holds two versions side by side.
        folder, olds, specs = drive.current_files(r['client'], r['name'], d.get('root', 'customers'), d.get('folder'))
        moved = drive.archive(folder, olds)
        if specs:
            moved += [f'_source/{n}' for n in drive.archive(folder / '_source', specs)]
        for n in moved:
            print(f'  archived {n}')
    files = {e: p for e, p in r['files'].items() if e in ('.pptx', '.pdf', '.docx', '.xlsx', '.svg', '.png', '.drawio')}
    folder, names = drive.publish(r['client'], r['name'], r['date'] or __import__('datetime').date.today().isoformat(),
                                  files, spec_path=r['spec'], root=d.get('root', 'customers'),
                                  sub=d.get('folder'), kind=r['kind'])
    print(f'  published to {folder}')
    for n in names:
        print(f'    {n}')


def cmd_pull(a):
    print(drive.pull(a.client, a.match, expect_size=a.expect_size))


def cmd_ls(a):
    folder = drive.client_folder(a.client, create_sandbox=False)
    for f in drive.ls(folder, 'folders'):
        print(f'  {f}/')
    for f in drive.ls(folder):
        print(f'  {f}')


def cmd_icons(a):
    names = sorted(set(kit._lucide()) | set(kit._material()))
    hits = [n for n in names if a.word.replace('_', '-').lower() in n.replace('_', '-')]
    print('\n'.join(hits[:80]) or 'no match')


def _switch(brand_id, argv):
    import os
    if brand_id and brand_id != kit.ACTIVE.id:
        brands.find(brand_id)
        os.execve(sys.executable, [sys.executable, '-m', 'servantium_documents.cli', *argv],
                  dict(os.environ, SV_BRAND=brand_id, SV_BRAND_SWITCHED='1'))


def cmd_templates(a):
    if a.all:
        import os, subprocess
        for b in brands.available():
            print(f'  {b}')
            subprocess.run([sys.executable, '-m', 'servantium_documents.cli', 'templates'],
                           env=dict(os.environ, SV_BRAND=b), check=True)
        return
    _switch(a.brand, ['templates'])
    from .templates import build_pptx, build_docx, build_xlsx
    prs = build_pptx.build(); build_pptx.examples(prs); build_pptx.save(prs)
    build_docx.save(build_docx.build())
    build_xlsx.save(build_xlsx.build())
    print(f'  templates -> {kit.TEMPLATE_PPTX.parent}')


def cmd_fonts(a):
    """Keynote and LibreOffice render with installed fonts only (Google Slides, Docs and Sheets
       fetch Google Fonts themselves). Copy every brand's font files into ~/Library/Fonts."""
    target = Path.home() / 'Library' / 'Fonts'
    target.mkdir(parents=True, exist_ok=True)
    for bid, root in brands.available().items():
        if a.brand and bid != a.brand:
            continue
        for f in sorted((root / 'fonts').glob('*.ttf')) if (root / 'fonts').exists() else []:
            dst = target / f.name
            state = 'have' if dst.exists() else 'installed'
            if not dst.exists():
                dst.write_bytes(f.read_bytes())
            print(f'  {bid:<12} {state:<10} {f.name}')


def cmd_brand(a):
    if a.action == 'list':
        for b, root in brands.available().items():
            print(f'  {b:<14} {root}')
        return
    if a.action == 'show':
        b = brands.load(a.id)
        print(f'  {b.name} ({b.id})  voice={b.voice}\n  root {b.root}')
        print(f'  fonts  {b.fonts.get("display", {}).get("family")} / {b.fonts.get("body", {}).get("family")}')
        for role, hx in b.colors.items():
            print(f'  {role:<15}{hx}')
        for k, v in b.logos.items():
            print(f'  logo {k:<12}{b.root / v}  {"ok" if (b.root / v).exists() else "MISSING"}')
        return
    if a.action == 'import':
        from . import brand_import
        print(brand_import.run(a.id, client=a.client))
        return


def cmd_stylebook(a):
    from . import stylebook
    out = stylebook.build(a.brand, a.company, a.docs, a.out)
    print(f'  {out}  ({out.stat().st_size // 1024} KB)')


def cmd_diagram(a):
    ensure_brand(a.spec, a._argv)
    from . import diagram
    r = diagram.build(a.spec)
    print(f'  {r["size"][0]:.0f} x {r["size"][1]:.0f} px canvas')
    for k in ('pdf', 'png', 'svg', 'drawio'):
        print(f'  {k:<7}{r[k]}')
    print('  Edit the .drawio file in diagrams.net (app.diagrams.net or the desktop app).')
    return 0


def cmd_doctor(a):
    ok = True

    def line(good, what, fix=''):
        nonlocal ok
        ok &= good
        print(f'  {"ok  " if good else "FAIL"} {what}' + (f'\n         {fix}' if not good and fix else ''))

    for face, path in kit._FONT_FILES.items():
        line(path.exists(), f'font {face}', f'Install {face} from Google Fonts into ~/Library/Fonts')
    for bid, root in brands.available().items():
        files = list((root / 'fonts').glob('*.ttf')) if (root / 'fonts').exists() else []
        missing = [f.name for f in files if not (Path.home() / 'Library/Fonts' / f.name).exists()]
        line(not missing, f'brand {bid}: fonts installed for Keynote and LibreOffice', 'Run `sv fonts install`')
    try:
        output.soffice(); line(True, 'LibreOffice')
    except FileNotFoundError as e:
        line(False, 'LibreOffice', str(e))
    icons = kit.ASSETS / 'icons'
    line((icons / 'MaterialSymbolsRounded.ttf').exists() and (icons / 'codepoints-rounded.txt').exists(),
         'icon fonts (Material Symbols)', 'Run `npm run icons` (fetched from Google, not stored in git)')
    line(kit.TEMPLATE_PPTX.exists(), 'slides template built', 'Run `sv templates`')
    line(kit.LOGO_ON_LIGHT.exists(), 'brand logos (@servantium/brand)', f'Missing {kit.LOGO_ON_LIGHT}')
    try:
        root = drive.customers_dir()
        line(drive.exists(root), f'Drive customers folder  {root}')
        line(True, 'Finder and System Events can reach Drive')
    except drive.DriveError as e:
        line(False, 'Google Drive for Desktop', str(e))
    line(drive.WORK.exists(), f'workspace  {drive.WORK}', f'mkdir {drive.WORK}')
    print('\n  ready' if ok else '\n  not ready')
    sys.exit(0 if ok else 1)


STARTER = '''deck: {deck}
client: {client}
slides:
  - cover:
      title: {deck}
      subtitle: One line on what this is and who it is for.

  - content:
      eyebrow: Topic
      title: State the conclusion in one sentence.
      lede: One line of context.
      body:
        - cards:
            - {{icon: target, title: First point, lines: [Why it matters]}}
            - {{icon: layers, title: Second point, lines: [Why it matters]}}
            - {{icon: fact_check, title: Third point, lines: [Why it matters]}}
        - takeaway: {{lead: "The so-what.", text: "One line."}}
      notes: |
        The talk goes here. The slide stays light.

  - closing:
      title: What we need out of today.
      asks: [A decision, with an owner., A date.]
'''


def main(argv=None):
    p = argparse.ArgumentParser(prog='sv', description='decks, documents, workbooks and diagrams in any brand')
    p.add_argument('--version', action='version', version=__version__)
    sub = p.add_subparsers(dest='cmd', required=True)
    x = sub.add_parser('new', help='start a spec: blank deck, or --type <starter> (sv new --list)')
    x.add_argument('client', nargs='?'); x.add_argument('deck', nargs='?')
    x.add_argument('--type'); x.add_argument('--brand'); x.add_argument('--list', action='store_true')
    x.set_defaults(fn=cmd_new)
    x = sub.add_parser('storyboard'); x.add_argument('spec'); x.set_defaults(fn=cmd_storyboard)
    x = sub.add_parser('check'); x.add_argument('spec'); x.set_defaults(fn=cmd_check)
    x = sub.add_parser('build'); x.add_argument('spec'); x.add_argument('--force', action='store_true'); x.set_defaults(fn=cmd_build)
    x = sub.add_parser('publish'); x.add_argument('spec'); x.add_argument('--force', action='store_true')
    x.add_argument('--replace', action='store_true', help='archive the published copy, then publish under the same name')
    x.set_defaults(fn=cmd_publish)
    x = sub.add_parser('pull'); x.add_argument('client'); x.add_argument('match', nargs='?')
    x.add_argument('--expect-size', type=int, help='fileSize Google reports; refuses a stale local copy')
    x.set_defaults(fn=cmd_pull)
    x = sub.add_parser('ls'); x.add_argument('client'); x.set_defaults(fn=cmd_ls)
    x = sub.add_parser('icons'); x.add_argument('word'); x.set_defaults(fn=cmd_icons)
    x = sub.add_parser('templates', help='rebuild the Office templates for a brand (default: the active one)')
    x.add_argument('--brand'); x.add_argument('--all', action='store_true'); x.set_defaults(fn=cmd_templates)
    x = sub.add_parser('stylebook', help='one-file HTML style guide for a brand, optionally with its company profile')
    x.add_argument('brand'); x.add_argument('--company'); x.add_argument('--docs'); x.add_argument('-o', '--out')
    x.set_defaults(fn=cmd_stylebook)
    x = sub.add_parser('fonts', help='install every brand font (needed by Keynote and LibreOffice)')
    x.add_argument('action', choices=['install']); x.add_argument('--brand'); x.set_defaults(fn=cmd_fonts)
    x = sub.add_parser('brand', help='list | show <id> | import <domain> --client <Client>')
    x.add_argument('action', choices=['list', 'show', 'import']); x.add_argument('id', nargs='?')
    x.add_argument('--client', help='workspace client folder for an imported brand'); x.set_defaults(fn=cmd_brand)
    x = sub.add_parser('doctor'); x.set_defaults(fn=cmd_doctor)
    x = sub.add_parser('diagram', help='lay out a workflow diagram: PDF, PNG, SVG and an editable .drawio')
    x.add_argument('spec'); x.set_defaults(fn=cmd_diagram)
    argv = sys.argv[1:] if argv is None else argv
    a = p.parse_args(argv)
    a._argv = argv
    try:
        a.fn(a)
    except (S.SpecError, drive.DriveError, brands.BrandError, FileNotFoundError) as e:
        sys.exit(f'sv: {e}')


if __name__ == '__main__':
    main()
