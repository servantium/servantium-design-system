"""Data binding: a spec reads its numbers and names from data files, so the estimate, the
proposal, the SOW, the plan and the invoices all print the same figure.

    data:                                   # alias -> YAML/JSON file, relative to the spec
      co: ../../company.yaml
      hero: ../../hero.yaml
    deck: "{{ co.identity.short }} proposal"
    slides:
      - numbers:
          stats:
            - {value: "{{ hero.quote_v2.total | money }}", label: Fixed fee}
      - content:
          body:
            - table: "{{ hero.fee_table }}"        # a whole value binds the structure itself

Rules:
  {{ a.b[0].c }}          a path into the data; a missing path is an error, never blank
  {{ a.b - c.d * 2 }}     arithmetic: + - * / with spaces around each, and parentheses
  {{ x | filter | ... }}  filters: money (no cents), money2, int, num, pct, hours, date,
                          short_date, day_month (Oct 6), month, year, str, round(n), count(key=value), join(sep) / join(key, sep), upper, lower, title, len, sum(key), first, last
  A string that is ONLY a placeholder is replaced by the value itself (list, number, map),
  so tables and rows can come straight from the data.

`sv build` binds before it validates. The bound spec is written next to the original
as `.<name>.bound.yaml` (hidden) and built from there, so relative paths still resolve.
"""
import datetime as dt
import hashlib
import json
import re
from pathlib import Path

import yaml

TOKEN = re.compile(r'\{\{\s*(.+?)\s*\}\}')
# Exactly one placeholder and nothing else: "{{ a }}, {{ b }}" is two, and stays a string.
WHOLE = re.compile(r'^\s*\{\{\s*((?:(?!\}\}|\{\{).)+?)\s*\}\}\s*$')
# Path steps: name, [3], ["2026-01"] or a dotted key that starts with a digit (monthly_hours.2026-01).
STEP = re.compile(r'\[(\-?\d+)\]|\[["\']([^"\']+)["\']\]|([^.\[\]\s]+)')


class BindError(Exception):
    pass


def _load(path):
    text = Path(path).read_text()
    return json.loads(text) if str(path).endswith('.json') else yaml.safe_load(text)


def _resolve(expr, ctx):
    cur, seen = ctx, []
    for m in STEP.finditer(expr):
        idx, quoted, key = m.group(1), m.group(2), m.group(3)
        step = quoted if quoted is not None else key
        seen.append(step if idx is None else f'[{idx}]')
        try:
            if idx is not None:
                cur = cur[int(idx)]
            elif isinstance(cur, dict) and step in cur:
                cur = cur[step]
            elif isinstance(cur, dict) and step.lstrip('-').isdigit() and int(step) in cur:
                cur = cur[int(step)]                        # YAML keeps 2026 as an int key
            elif isinstance(cur, list) and step.lstrip('-').isdigit():
                cur = cur[int(step)]
            else:
                raise KeyError(step)
        except (KeyError, IndexError, TypeError):
            raise BindError(f'no value at "{expr}" (stopped at {".".join(seen)})')
    return cur


def _date(v):
    return v if isinstance(v, (dt.date, dt.datetime)) else dt.date.fromisoformat(str(v)[:10])


def _apply(value, f):
    name, _, arg = f.partition('(')
    arg = arg.rstrip(')').strip().strip('"\'')
    name = name.strip()
    if name == 'money':
        return f'${float(value):,.0f}' if float(value) >= 0 else f'-${-float(value):,.0f}'
    if name == 'money2':
        return f'${float(value):,.2f}' if float(value) >= 0 else f'-${-float(value):,.2f}'
    if name == 'int':
        return f'{round(float(value)):,}'
    if name == 'num':
        return f'{float(value):,.{int(arg or 1)}f}'
    if name == 'pct':
        v = float(value)
        return f'{v * 100 if abs(v) <= 1 else v:.{int(arg or 0)}f}%'
    if name == 'hours':
        return f'{round(float(value)):,} hours'
    if name == 'date':
        return _date(value).strftime('%B %-d, %Y')
    if name == 'day_month':
        return _date(value).strftime('%b %-d')
    if name == 'short_date':
        return _date(value).strftime('%b %-d, %Y')
    if name == 'month':
        return _date(value).strftime('%B %Y')
    if name in ('upper', 'lower', 'title'):
        return getattr(str(value), name)()
    if name == 'str':
        return str(int(value)) if isinstance(value, float) and value.is_integer() else str(value)
    if name == 'year':
        return str(_date(value).year) if not str(value).isdigit() else str(value)
    if name == 'round':
        return round(float(value), int(arg or 0))
    if name == 'join':
        # join(", ") or join(" / "): a list as one string; join(key, ", ") takes one field per item
        sep = arg if arg else ', '
        if ',' in arg and not arg.strip().startswith(('"', "'")) and arg.split(',', 1)[0].strip().isidentifier():
            key, _, sep = arg.partition(',')
            value = [x.get(key.strip()) for x in value]
            sep = sep.strip().strip('"\'') or ', '
        return sep.join(str(x) for x in value)
    if name == 'count':
        # count(key=value): items in a list whose key equals value; count alone = len
        if not arg:
            return len(value)
        k, _, want = arg.partition('=')
        return sum(1 for x in value if str(x.get(k.strip())) == want.strip())
    if name == 'len':
        return len(value)
    if name == 'sum':
        return sum(float(x[arg] if arg else x) for x in value)
    if name == 'first':
        return value[0]
    if name == 'last':
        return value[-1]
    raise BindError(f'unknown filter "{name}"')


ARITH = re.compile(r'\s[-+*/]\s')


def _arith(expr, ctx):
    """a.b - c.d * 2: paths and numbers joined by + - * / (spaces around each operator), with
       parentheses. Evaluated with Python's arithmetic only; nothing else runs."""
    import ast
    names = {}

    def path(m):
        tok = m.group(0)
        if re.fullmatch(r'-?\d+(\.\d+)?', tok):
            return tok
        key = f'_v{len(names)}'
        names[key] = float(_resolve(tok, ctx))
        return key
    src = re.sub(r'[^\s()+\-*/][^\s()]*', path, expr)
    tree = ast.parse(src, mode='eval')
    for n in ast.walk(tree):
        if not isinstance(n, (ast.Expression, ast.BinOp, ast.UnaryOp, ast.Constant, ast.Name, ast.Load,
                              ast.Add, ast.Sub, ast.Mult, ast.Div, ast.USub, ast.UAdd)):
            raise BindError(f'"{expr}": only + - * / and parentheses are allowed')
    v = eval(compile(tree, '<bind>', 'eval'), {'__builtins__': {}}, names)
    return round(v, 6)


def _eval(expr, ctx):
    parts = [p.strip() for p in expr.split('|')]
    v = _arith(parts[0], ctx) if ARITH.search(f' {parts[0]} ') else _resolve(parts[0], ctx)
    for f in parts[1:]:
        v = _apply(v, f)
    return v


def _walk(node, ctx):
    if isinstance(node, dict):
        return {k: _walk(v, ctx) for k, v in node.items()}
    if isinstance(node, list):
        return [_walk(v, ctx) for v in node]
    if isinstance(node, str) and '{{' in node:
        m = WHOLE.match(node)
        if m:
            v = _eval(m.group(1), ctx)

            return _walk(v, ctx) if isinstance(v, (dict, list)) else (v if not isinstance(v, (int, float)) else v)
        return TOKEN.sub(lambda mm: str(_eval(mm.group(1), ctx)), node)
    return node


_AS_TEXT = [False]     # set while binding a deck: numbers that come FROM data become text


def _texts(node):
    if isinstance(node, dict):
        return {k: _texts(v) for k, v in node.items()}
    if isinstance(node, list):
        return [_texts(v) for v in node]
    if isinstance(node, bool):
        return node
    if isinstance(node, (int, float)):
        return str(int(node)) if float(node).is_integer() else str(node)
    return node


def bind(spec_path):
    """Returns (path_to_build, sha). Specs with no data: build as they are."""
    spec_path = Path(spec_path).resolve()
    raw = spec_path.read_text()
    d = yaml.safe_load(raw) or {}
    if not isinstance(d, dict) or 'data' not in d:
        return spec_path, None
    sources = d.pop('data')
    if isinstance(sources, str):
        sources = {'data': sources}
    h = hashlib.sha256(raw.encode())
    ctx = {}
    for alias, rel in sources.items():
        p = (spec_path.parent / rel).resolve()
        if not p.exists():
            raise BindError(f'data "{alias}": {p} not found')
        h.update(p.read_bytes())
        ctx[alias] = _load(p)
    try:
        bound = _walk(d, ctx)       # numbers stay numbers; spec.load turns one into text where text is wanted
    except BindError as e:
        raise BindError(f'{spec_path.name}: {e}')
    out = spec_path.parent / f'.{spec_path.stem}.bound.yaml'
    out.write_text('# GENERATED by sv from ' + spec_path.name + '. Edit that file, not this one.\n' +
                   yaml.safe_dump(bound, sort_keys=False, allow_unicode=True, width=1000))
    return out, h.hexdigest()[:12]
