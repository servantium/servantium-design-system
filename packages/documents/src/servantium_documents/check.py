"""Checks a spec before anything renders.

Every rule here exists because a real deck needed it. When a correction comes up in
review, it becomes a rule in this file, so it never has to be said twice:

  too much text          -> LINE, LEDE, DENSITY  (a client status deck, cut twice)
  no em dashes           -> DASH                 (standing voice rule)
  American spelling      -> SPELL                (a client deck shipped British)
  two, three, four       -> COUNT (schema) + EMPHASIS
  numbers need a source  -> SOURCE               (claim rules: no invented numbers)
  titles are conclusions -> TITLE                (consulting method)
  the talk lives in notes-> NOTES

Levels: error blocks the build; warning is shown and the build continues.
"""
import re
from pathlib import Path
from dataclasses import dataclass

from . import kit
from .spec import slides, EMPHASIS

CONTENT_KINDS = {'content', 'bullets', 'columns', 'comparison', 'numbers', 'picture'}

# ── word lists ────────────────────────────────────────────────────────────────
_STEMS = ('organi reali recogni utili optimi standardi prioriti digitali capitali finali summari '
          'customi minimi maximi emphasi categori characteri speciali authori critici apologi '
          'visuali normali centrali operationali moneti monetari industriali commerciali '
          'personali stabili generali formali memori theori').split()
BRITISH = [
    (re.compile(rf'\b({"|".join(_STEMS)})s(e|es|ed|ing|ation|ations)\b', re.I), 'ize/ization'),
    (re.compile(r'\banalys(e|ed|ing)\b', re.I), 'analyze'),
    (re.compile(r'\b(behavi|col|flav|fav|hon|lab|harb|neighb|rum|vig|endeav)our(s|ed|ing|able|ite|ites)?\b', re.I), '-or'),
    (re.compile(r'\b(cent|met|theat|fib|lit|calib|spect)re(s|d)?\b', re.I), '-er'),
    (re.compile(r'\b(programme|catalogue|licence|defence|offence|judgement|whilst|amongst|artefacts?|'
                r'cheques?|learnt|fulfil|enrol|travell(ed|ing)|cancell(ed|ing)|modell(ed|ing)|'
                r'labell(ed|ing)|grey)\b', re.I), 'American spelling'),
]
DASHES = re.compile(r'[—–]|\s--\s')
FIGURE = re.compile(r'\d+(\.\d+)?\s?%|\$\s?\d|\b\d+(\.\d+)?\s?[x×]\b|\b\d{1,3}(,\d{3})+\b|\b(?!(19|20)\d\d\b)\d{3,}\b')

# Budgets. Slides are light; the talk lives in the notes.
TITLE_MAX_LINES, TITLE_WARN_WORDS = 2, 14
LINE_WARN, LINE_ERROR = 12, 20
LEDE_WARN = 24
DENSITY_WARN, DENSITY_ERROR = 75, 120
DIAGRAM_WARN, DIAGRAM_ERROR = 150, 220     # slides whose body is a labeled diagram
DIAGRAMS = {'swimlane', 'gantt', 'flow', 'staircase', 'approach', 'middleout', 'processmap', 'board'}   # short labels in a structure
CTA_W_IN, CTA_WORDS = 3.9, 6        # the closing button is 4.15 in wide
KICKER_CHARS = 10                   # the card corner tag
VARIETY_MAX = 3                     # slides that may share one composition
BOXES = {'cards', 'tiles', 'stats', 'milestones', 'chevrons', 'panels', 'chain', 'logos', 'timeline', 'shipped'}
BOXES_MAX = 3                       # slides in a deck that may be a row of boxes
NAV_TITLES = {'agenda', 'appendix', 'contents', 'next steps', 'questions', 'questions for you', 'commercials'}
TITLE_TROPES = [
    (re.compile(r"^(then|and|so|also|but)\b", re.I), 'leans on the slide before it. Make it stand alone.'),
    (re.compile(r"\bfirst[.,]\s+then\b", re.I), '"X first, then Y" is a slogan. State what happens and why.'),
    (re.compile(r"\b(isn't|is not|not just|not only)\b[^.]*\b(it's|it is|but)\b", re.I),
     '"not X, it\'s Y" is an AI cadence. Say Y.'),
    (re.compile(r"\b(the next step is|here's|common ground|the real (problem|question|story))\b", re.I),
     'stock phrase. Name the thing instead.'),
    (re.compile(r"^(two|three|four) ways in\b|:\s", re.I), 'colon reveal. Write the claim as one sentence.'),
]
REPEAT_SLIDES = 3                   # a 3-word phrase on this many slides is a catchphrase
REPEAT_TITLES = 3                   # a content word in this many titles is a crutch
REPEAT_WORD_SLIDES = 4              # a word in this many titles/punchlines is leaning on it
REPEAT_OK = {'servantium', 'house', kit.BRAND_SHORT.lower(), kit.ACTIVE.id}
WORD_OK = {'your', 'months', 'month', 'team', 'teams'}
FRAMING = {'title', 'lede', 'subtitle'}   # the voice layer; body content may repeat domain nouns

_BANNED_FILE = Path(__file__).parent / 'banned.txt'


def _load_banned():
    """phrase | hint, one per line. Kept as data so the list grows without code."""
    out = []
    for ln in _BANNED_FILE.read_text().splitlines() if _BANNED_FILE.exists() else []:
        ln = ln.strip()
        if not ln or ln.startswith('#'):
            continue
        phrase, _, hint = ln.partition('|')
        phrase = phrase.strip().lower()
        out.append((re.compile(r'(?<![A-Za-z])' + re.escape(phrase) + r'(?![A-Za-z])', re.I),
                    phrase, hint.strip() or 'Say the plain thing.'))
    return out


BANNED = _load_banned()


# Product names that contain a banned word are names, not voice (a lab's chromatography system).
PRODUCT_NAMES = ('Waters Empower', 'Empower CDS', 'Empower 3')


def _banned_hits(txt):
    txt = txt or ''
    for name in PRODUCT_NAMES:
        txt = txt.replace(name, '')
    return [(p, h) for rx, p, h in BANNED if rx.search(txt)]


@dataclass
class Finding:
    level: str      # 'error' | 'warning'
    code: str
    slide: int
    message: str

    def __str__(self):
        mark = 'ERROR  ' if self.level == 'error' else 'warning'
        where = f'slide {self.slide:>2}' if self.slide else 'deck    '
        return f'  {mark} {where}  {self.code:<8} {self.message}'


def _words(s):
    return len(re.findall(r"[A-Za-z0-9][A-Za-z0-9'’.,%$/-]*", s or ''))


def visible_text(kind, f):
    """(label, text) pairs a reader sees on the slide. Notes excluded."""
    out = []
    for key in ('eyebrow', 'title', 'lede', 'subtitle', 'text', 'attribution', 'cta', 'source'):
        if f.get(key):
            out.append((key, f[key]))
    if kind == 'team':
        for pt in f.get('points', []):
            out += [('points', pt['lead']), ('points', pt['text'])]
        for p in f.get('people', []):
            out += [('people', p['name']), ('people', p['role'])]
        if f.get('credentials'):
            out.append(('credentials', f['credentials']))
        for pr in f.get('proof', []):
            out += [('proof', pr['lead']), ('proof', pr['text'])]
        if f.get('stat'):
            out += [('stat', f['stat']['value']), ('stat', f['stat']['label'])]
        return out
    for key in ('points', 'asks', 'left', 'right'):
        v = f.get(key)
        if isinstance(v, list):
            out += [(key, x) for x in v]
        elif isinstance(v, dict):
            out.append((key + '.heading', v.get('heading', '')))
            out += [(key, x) for x in v.get('points', [])]
    for side in ('left', 'right'):
        v = f.get(side)
        if kind == 'split' and isinstance(v, dict):
            out += [(f'{side}.{k}', v[k]) for k in ('label', 'stat', 'headline', 'line') if v.get(k)]
    for st in f.get('stats', []):
        out += [('stat', st['value']), ('stat', st['label'])]
    for comp in f.get('body', []):
        (name, val), = comp.items()
        out += _component_text(name, val)
    return out


_NOT_TEXT = {'icon', 'logo', 'logos', 'photo', 'replaces', 'tone', 'path'}   # file paths and styles, not words


def _component_text(name, val):
    out = []
    items = val if isinstance(val, list) else [val]
    for it in items:
        if isinstance(it, str):
            out.append((name, it))
            continue
        for k, v in it.items():
            if k in ('icon', 'logo', 'logos', 'photo', 'tone', 'done', 'path', 'height', 'widths', 'mermaid',
                     'type', 'values', 'unit', 'active', 'pills', 'row_h'):
                continue
            if isinstance(v, str):
                out.append((f'{name}.{k}', v))
            elif isinstance(v, list):
                for x in v:
                    if isinstance(x, str):
                        out.append((f'{name}.{k}', x))
                    elif isinstance(x, list):
                        out += [(f'{name}.{k}', c) for c in x if isinstance(c, str)]
                    elif isinstance(x, dict):
                        out += [(f'{name}.{k}', c) for kk, c in x.items() if isinstance(c, str) and kk not in _NOT_TEXT]
                        for kk, c in x.items():
                            if isinstance(c, list) and kk not in _NOT_TEXT:
                                out += [(f'{name}.{k}', y) for y in c if isinstance(y, str)]
            elif isinstance(v, dict):
                out += [(f'{name}.{k}', c) for c in v.values() if isinstance(c, str)]
                for c in v.values():
                    if isinstance(c, list):
                        out += [(f'{name}.{k}', x) for x in c if isinstance(x, str)]
    return out


def _icons(f):
    """Every icon named anywhere in the slide's components, however deeply nested."""
    names = []

    def walk(v):
        if isinstance(v, dict):
            if isinstance(v.get('icon'), str):
                names.append(v['icon'])
            for x in v.values():
                walk(x)
        elif isinstance(v, list):
            for x in v:
                walk(x)
    walk(f.get('body', []))
    return names


def check(spec):
    findings = []
    add = lambda lvl, code, n, msg: findings.append(Finding(lvl, code, n, msg))

    for n, kind, f in slides(spec):
        texts = visible_text(kind, f)

        # Voice: dashes and spelling are errors on the slide, warnings in the notes.
        for label, t in texts:
            if DASHES.search(t):
                add('error', 'DASH', n, f'{label}: no em or en dashes. Use a period, comma or parentheses: "{t[:60]}"')
            for rx, fix in BRITISH:
                m = rx.search(t)
                if m:
                    add('error', 'SPELL', n, f'{label}: "{m.group(0)}" is British. Use {fix}.')
        notes = f.get('notes', '')
        if notes and DASHES.search(notes):
            add('warning', 'DASH', n, 'notes contain an em or en dash')
        for rx, fix in BRITISH:
            m = rx.search(notes or '')
            if m:
                add('warning', 'SPELL', n, f'notes: "{m.group(0)}" is British. Use {fix}.')

        # Titles.
        title = f.get('title', '')
        if title and kind in CONTENT_KINDS:
            lines = kit.est_lines(title, kit.TITLE_W_IN, kit.TITLE_SIZE, font=kit.DISPLAY)
            if lines > TITLE_MAX_LINES:
                add('error', 'TITLE', n, f'title runs to {lines} lines; the limit is {TITLE_MAX_LINES}. Cut words.')
            elif lines > 1:
                add('warning', 'TITLE', n, 'title wraps to two lines. Keep titles to one line.')
            elif _words(title) > TITLE_WARN_WORDS:
                add('warning', 'TITLE', n, f'title is {_words(title)} words; aim for {TITLE_WARN_WORDS} or fewer.')
            if _words(title) < 4 and title.strip(' .').lower() not in NAV_TITLES:
                add('warning', 'TITLE', n, f'"{title}" reads like a topic. State the conclusion.')
        # Titles are short claims in plain words, never an AI cadence (a presented deck:
        # long titles pull eyes off the speaker, so the fix for weak titles is the trope, not length).
        if title and kind in CONTENT_KINDS | {'cover', 'team'}:
            for rx, why in TITLE_TROPES:
                if rx.search(title):
                    add('warning', 'TROPE', n, f'title "{title}": {why}')
                    break

        # Density.
        for label, t in texts:
            if label in ('title', 'eyebrow', 'source'):
                continue
            w = _words(t)
            if label == 'lede':
                if w > LEDE_WARN:
                    add('warning', 'LEDE', n, f'lede is {w} words; keep it to one line (~{LEDE_WARN}).')
            elif w > LINE_ERROR:
                add('error', 'LINE', n, f'{label} is {w} words. Too much text; move the detail to the notes: "{t[:50]}..."')
            elif w > LINE_WARN:
                add('warning', 'LINE', n, f'{label} is {w} words; aim for nine: "{t[:50]}..."')
        total = sum(_words(t) for lbl, t in texts if lbl not in ('eyebrow', 'source'))
        # Diagrams carry labels, not prose: a nine-step workflow legitimately holds 120 words.
        diagram = any(next(iter(c)) in DIAGRAMS for c in f.get('body', []))
        warn_at, error_at = (DIAGRAM_WARN, DIAGRAM_ERROR) if diagram else (DENSITY_WARN, DENSITY_ERROR)
        if kind != 'cover':
            if total > error_at:
                add('error', 'DENSITY', n, f'{total} words on the slide. Too much text; the talk lives in the notes.')
            elif total > warn_at:
                add('warning', 'DENSITY', n, f'{total} words on the slide; aim under {warn_at}.')

        # Emphasis: one takeaway, callout, band or quote per slide.
        emph = [next(iter(c)) for c in f.get('body', []) if next(iter(c)) in EMPHASIS]
        if len(emph) > 1:
            add('error', 'EMPHASIS', n, f'{len(emph)} emphasis blocks ({", ".join(emph)}). One per slide.')

        # Sources live in the notes. A source line on a client slide reads as a
        # footnote nobody asked for; the basis goes in the notes, where the presenter
        # has it if asked.
        if f.get('source'):
            add('warning', 'SOURCE', n, 'source line on the slide. Put the basis in the notes instead.')

        # AI-isms: phrases that mark text as machine-written. Errors on the slide.
        for label, t_ in texts:
            for phrase, hint in _banned_hits(t_):
                add('error', 'AIISM', n, f'{label}: "{phrase}" reads as AI. {hint}')
        for phrase, hint in _banned_hits(notes or ''):
            add('warning', 'AIISM', n, f'notes: "{phrase}" reads as AI. {hint}')

        # The talk lives in the notes.
        if kind in CONTENT_KINDS and not notes.strip():
            add('warning', 'NOTES', n, 'no speaker notes. The slide stays light only if the notes carry the talk.')

        # Icons must exist in the icon system.
        for name in _icons(f):
            if not kit.icon_exists(name):
                add('error', 'ICON', n, f'unknown icon "{name}". Check with `sv icons {name}`.')

        # Tables: every row has one cell per column. A comma in an unquoted cell splits it
        # and every value after it slides one column over.
        for comp in f.get('body', []):
            tb = comp.get('table')
            if tb:
                for i, row in enumerate(tb['rows'], 1):
                    if len(row) != len(tb['head']):
                        add('error', 'TABLE', n, f'table row {i} has {len(row)} cells for {len(tb["head"])} columns '
                                                 f'("{row[0]}"). Quote any cell that contains a comma.')

        # Fixed-size chrome: text that must fit its box on one line.
        cta = f.get('cta')
        if cta and kit.est_lines(cta, CTA_W_IN, 14, bold=True) > 1:
            add('error', 'FIT', n, f'cta wraps out of its button; keep it to about {CTA_WORDS} words: "{cta}"')
        for comp in f.get('body', []):
            for card in comp.get('cards', []):
                k = card.get('kicker')
                if k and len(k) > KICKER_CHARS:
                    add('error', 'FIT', n, f'card kicker "{k[:40]}" is a corner tag (like "01" or "Q1"), '
                                           f'{KICKER_CHARS} characters at most. Put sentences in lines.')

    findings += _variety(spec)
    findings += _repeats(spec)
    return findings


_STOP = set("""a an and are as at be but by can do does for from has have how if in into is it its
of on or our so that the their them then there these they this to up was we were what when where
which who will with you your it's we're you're don't can't won't isn't that's what's here's""".split())


def _phrases(txt, n=3):
    words = re.findall(r"[a-z][a-z'’-]*", (txt or '').lower())
    out = set()
    for i in range(len(words) - n + 1):
        gram = words[i:i + n]
        if sum(w not in _STOP for w in gram) >= 2:
            out.add(' '.join(gram))
    return out


def _repeats(spec):
    """A catchphrase repeated across a deck reads as filler ("on one record" on six slides).
       Warn when a three-word phrase shows on the visible text of three or more slides, or a
       content word leans on too many titles."""
    seen, title_words, words, done = {}, {}, {}, False
    ok = REPEAT_OK | {spec['client'].lower()}
    for n, kind, f in slides(spec):
        if done:
            break          # the appendix after the closing slide is reference, not the story
        done = kind == 'closing'
        # stage bars (flow steps, approach stages, zoom steps) repeat on purpose: they are navigation
        visible = ' '.join(t_ for lbl, t_ in visible_text(kind, f)
                           if lbl not in ('eyebrow', 'source') and not lbl.endswith(('.steps', '.stages')))
        for g in _phrases(visible):
            seen.setdefault(g, set()).add(n)
        # Navigation labels repeat by design: a divider's title is also on the agenda and the
        # tracker, and a "Questions for you" stop can come once per section.
        title = f.get('title') or ''
        nav = kind == 'section' or title.strip(' .').lower() in NAV_TITLES
        if not nav:
            for w in set(re.findall(r"[a-z][a-z'-]{3,}", title.lower())) - _STOP:
                title_words.setdefault(w, set()).add(n)
        framing = ' '.join(t_ for lbl, t_ in visible_text(kind, f)
                           if (lbl in FRAMING and not (nav and lbl == 'title'))
                           or lbl.startswith(('takeaway', 'callout', 'band')))
        for w in set(re.findall(r"[a-z][a-z'-]{3,}", framing.lower())) - _STOP:
            words.setdefault(w, set()).add(n)
    out = []
    for g, ns in sorted(seen.items(), key=lambda kv: -len(kv[1])):
        if len(ns) >= REPEAT_SLIDES:
            out.append(Finding('warning', 'REPEAT', 0, f'"{g}" appears on {len(ns)} slides '
                                                      f'({", ".join(map(str, sorted(ns)))}). Say it once.'))
    for w, ns in sorted(words.items(), key=lambda kv: -len(kv[1])):
        if len(ns) >= REPEAT_WORD_SLIDES and w not in ok and w not in WORD_OK:
            out.append(Finding('warning', 'REPEAT', 0, f'"{w}" is on {len(ns)} slides '
                                                      f'({", ".join(map(str, sorted(ns)))}). Vary it or cut it.'))
    for w, ns in title_words.items():
        if len(ns) >= REPEAT_TITLES and w not in ok:
            out.append(Finding('warning', 'REPEAT', 0, f'"{w}" is in {len(ns)} titles '
                                                      f'({", ".join(map(str, sorted(ns)))}). Find another way in.'))
    return out


def _signature(kind, f):
    if kind != 'content':
        return kind
    return '+'.join(next(iter(c)) for c in f.get('body', []))


def _variety(spec):
    """A deck of the same slide over and over reads as a template, not a story.
       Warn when one composition repeats too often, or back to back."""
    out, seen, prev, done, boxes = [], {}, None, False, []
    for n, kind, f in slides(spec):
        if done:
            break          # the appendix is reference material; tables there are fine
        done = kind == 'closing'
        if kind in ('cover', 'closing', 'section', 'split', 'team'):
            prev = None
            continue
        sig = _signature(kind, f)
        seen.setdefault(sig, []).append(n)
        if sig == prev:
            out.append(Finding('warning', 'VARIETY', n, f'same composition as the slide before ({sig}). '
                                                        'Change the picture, not just the words.'))
        elif sig.split('+')[0] in BOXES and (prev or '').split('+')[0] in BOXES:
            out.append(Finding('warning', 'VARIETY', n, f'a row of boxes ({sig.split("+")[0]}) right after another '
                                                        f'({prev.split("+")[0]}). Break it up: a picture, a table, a chart or a diagram.'))
        if sig.split('+')[0] in BOXES:
            boxes.append(n)
        prev = sig
    if len(boxes) > BOXES_MAX:
        out.append(Finding('warning', 'VARIETY', 0, f'{len(boxes)} slides are rows of boxes ({", ".join(map(str, boxes))}); '
                                                    f'keep it to {BOXES_MAX}. Use other shapes: curve, matrix, zoom, flow, '
                                                    'stack, gantt, table, chart, split.'))
    for sig, ns in seen.items():
        if len(ns) > VARIETY_MAX:
            out.append(Finding('warning', 'VARIETY', 0, f'"{sig}" is used on {len(ns)} slides '
                                                        f'({", ".join(map(str, ns))}); keep any one composition to {VARIETY_MAX}.'))
    return out


def storyboard(spec):
    """The titles alone, in order. If they tell the story, the deck is right."""
    rows = []
    for n, kind, f in slides(spec):
        rows.append(f'{n:>3}. {f.get("title") or f.get("text", "")[:70]}   [{kind}]')
    return '\n'.join(rows)
