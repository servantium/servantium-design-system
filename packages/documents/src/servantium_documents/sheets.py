"""Excel workbooks from a spec: estimates, plans, invoices, purchase orders, expense reports.

A workbook spec is YAML, loaded strictly (dates stay strings) and validated against a JSON
Schema with no unknown keys, like a deck spec (spec.py). Every colour, font, logo and the
footer come from the active brand through kit; nothing here types a hex value or a face.

    python -m servantium_documents.sheets <spec.yaml>   -> <spec dir>/out/<client> <workbook>.xlsx, .pdf

COMPATIBILITY IS THE DESIGN CONSTRAINT. The file must open in Excel without repair, import
into Google Sheets with its formulas, conditional formats, number formats and frozen panes
intact, and print to a clean PDF from LibreOffice. So:
  * every cell carries direct formatting; no named cell styles are relied on;
  * tables are plain ranges with an autofilter, never Excel Table objects (ListObjects);
  * zebra stripes and Gantt bars are conditional formatting with formula rules and solid
    fills (Sheets keeps those; it drops data bars, gradients and conditional borders);
  * every number is a real formula on real A1 references, so the sheet stays live:
    change an hour, a rate or a start date and every total and bar follows;
  * only functions Excel 2007, Sheets and LibreOffice share (SUM, MIN, MAX, IF, AND,
    IFERROR, N, WORKDAY, NETWORKDAYS, EOMONTH, EDATE, WEEKDAY, TODAY); nothing that
    needs an _xlfn prefix.

The modelling convention from the workbook template holds: blue text is an input a person
may change, black text is a formula.

Spec:

    workbook: Implementation Estimate      # the file name, after the client
    client: Acme Logistics
    date: 2026-10-20                       # optional, defaults to today
    prepared_for: Jordan Lee, Acme         # optional
    prepared_by: Delivery team             # optional, defaults to the brand name
    currency: "$"                          # optional symbol, default "$"
    brand: servantium                      # optional; `sv` switches brand before building
    sheets:
      - name: Estimate                     # the tab name (31 characters, no []:*?/\\)
        kind: table | gantt | form | summary
        title: Optional heading            # defaults to the tab name
        subtitle: Optional one line under it
        landscape: true                    # optional; plans default landscape, forms and summaries
                                           # portrait, tables portrait unless too wide

  table:
        columns:
          - {key: role, header: Role, width: 30}
          - {key: hours, header: Hours, format: hours, total: sum, input: true}
          - {key: rate, header: Rate, format: currency, decimals: 0, input: true}
          - {key: fees, header: Fees, format: currency, formula: "=[@hours]*[@rate]", total: sum}
          - {key: share, header: Share, format: percent, formula: "=[@fees]/[#fees]"}
        groups:                            # or `rows:` for a flat table
          - name: Discovery
            rows: [{role: Engagement lead, hours: 40, rate: 225}]
        total_label: Total                 # optional
        autofilter: true                   # default: on for flat tables, off when grouped
        note: Optional footnote under the table
     format: text | int | number | currency | percent | date | hours | yesno | check
             (decimals overrides; text wraps by default, `wrap: false` turns it off;
             booleans read Yes/No, or a check mark in a `check` column)
     total:  sum | average | count | formula (the column's formula on the total row) | none
     total_row: false keeps group subtotals and drops the grand total.
     Row keys that are not columns are ignored, so rows can come from richer records.
     formula references:
        [@key]          this row's cell in column `key`
        [key]           the column's data cells (for SUM, AVERAGE, ...)
        [#key]          the column's total (its total-row cell, or a SUM when it has none)
        [#metric]       a summary metric on this sheet (its label as a slug, or its `key`)
        [Sheet!#key]    the same, on another sheet ([Plan!#end], [Invoice!#total])
        [Sheet!key]     another sheet's column data, for MAX/MIN/AVERAGE ([Monthly!spend])
     Any function Excel 2007, Sheets and LibreOffice share is fine (INT, MOD, SUMIF(S),
     COUNTIF(S), ROUNDUP, ROUNDDOWN, CEILING, FLOOR, IFERROR...); newer ones that open as
     #NAME? somewhere (XLOOKUP, IFS, TEXTJOIN, MAXIFS...) are refused at build.
        [#key.group]    a group's subtotal (group `id`, or its name as a slug: [#fees.discover])
     A row value that starts with "=" is a formula too and overrides the column's.

  gantt:
        scale: week | day | month          # default week
        today: true                        # optional: mark the current period
        tasks:
          - {id: discover, name: Discovery}                      # a phase: it has children
          - {id: kickoff, name: Kickoff, parent: discover, start: 2026-11-02, milestone: true}
          - {id: interviews, name: Interviews, parent: discover, start: 2026-11-03,
             duration_days: 8, owner: Lead, percent: 0.5}
          - {id: design, name: Design, parent: discover, depends_on: [interviews], duration_days: 5}
     A leaf takes `start` (or `depends_on`, which starts it the next working day after its
     predecessors end) and `end` or `duration_days` (working days). A milestone takes a
     start only. A phase's dates and % done are MIN/MAX/weighted formulas over its children.
     WBS numbers come from the outline. Bars are conditional formats on the date header,
     so they move when a date changes.

  form:
        form: invoice | purchase_order | expense_report
        number: INV-1042
        details: [{label: Invoice date, value: 2026-10-20}, {label: Due, value: 2026-11-19}]
        parties: [{label: Bill to, lines: [Acme Logistics, 100 Example Way]}]   # 1-3 blocks
        items:                             # invoice: description, qty, unit, rate (or amount)
          - {description: Discovery workshop, qty: 2, unit: day, rate: 2400}
                                           # purchase_order: sku, description, qty, unit, rate
                                           # expense_report: date, category, description,
                                           #                 merchant, amount
        blank_rows: 2                      # optional empty, formula-ready lines
        discount_rate: 0.05                # or discount: 250 (an amount)
        tax_rate: 0.0825                   # tax_label: Sales tax
        shipping: 40                       # advance: 300 (expense report: less advance)
        terms: Net 30
        payment: [Remit by ACH to ...]     # lines beside the totals
        notes: Free text under the totals
        signatures: [Approved by, Date]    # lines to sign; defaults per form
     Prints to one portrait page. Party blocks sit up to three a row, wider ones wrap to
     a second row; the Subtotal row is left out when nothing stands between it and the total.

  summary:
        eyebrow: Optional label above the title
        meta: true                         # prepared for / by / date block (default true)
        metrics:                           # 1-8 cards, up to `per_row` (default 4) a row
          - {label: Total fees, value: "=[Estimate!#fees]", format: currency, note: Fixed fee}
          - {label: Expense cap, key: cap, value: 500, format: currency}   # [#cap] / [#expense_cap]
        table: {columns: [...], rows: [...]}     # optional small table, as above
        notes: [Optional lines]
        contents: true                     # optional list of the other tabs, linked
     Each metric is also a reference: [Summary!#total_fees] (its label as a slug).
"""
import datetime as dt
from copy import copy
import hashlib
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import yaml
from jsonschema import Draft202012Validator
from openpyxl import Workbook
from openpyxl.drawing.image import Image as XLImage
from openpyxl.drawing.spreadsheet_drawing import AnchorMarker, OneCellAnchor
from openpyxl.drawing.xdr import XDRPositiveSize2D
from openpyxl.formatting.rule import FormulaRule
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter, quote_sheetname
from openpyxl.utils.units import pixels_to_EMU
from openpyxl.workbook.properties import CalcProperties
from openpyxl.worksheet.datavalidation import DataValidation
from openpyxl.worksheet.hyperlink import Hyperlink
from openpyxl.writer.theme import theme_xml

from . import brand, output
from .brand import K, hexof
from .spec import SpecError, _StrictLoader
from .templates.build_xlsx import set_default_font


# ── palette: brand roles only, resolved once from kit ───────────────────────
def _tok(name, fallback):
    v = K.T.COLORS.get(name)
    return v.lstrip('#').upper() if v else fallback


class C:
    FOREST = hexof(K.FOREST)
    GREEN = hexof(K.GREEN)
    GREEN_600 = hexof(K.GREEN_600)
    JADE = hexof(K.GREEN_300)
    MINT = hexof(K.MINT)
    MINT_TINT = hexof(K.MINT_TINT)
    INK = hexof(K.INK)
    INK_800 = hexof(K.INK_800)
    MUTED = hexof(K.INK_MUTED)
    CLOUD = hexof(K.CLOUD)
    MIST = hexof(K.MIST)
    WHITE = hexof(K.WHITE)
    AMBER = hexof(K.AMBER)
    ON_DARK = hexof(K.ON_FOREST)
    ON_DARK_MUTED = hexof(K.ON_FOREST_MUTED)
    INPUT = _tok('color-model-input', hexof(K.SLATE))       # blue means "you may change this"
    LINK = _tok('color-model-link', hexof(K.GREEN_600))
    TODAY_BG = _tok('color-warning-bg', hexof(K.MIST))


BODY, DISPLAY = K.UI, K.DISPLAY
DIAMOND = '◆'


def font(size=10, bold=False, color=None, italic=False, name=None):
    return Font(name=name or BODY, size=size, bold=bold, italic=italic, color=color or C.INK_800)


def solid(hx):
    return PatternFill(fill_type='solid', start_color=hx, end_color=hx)


def side(color=None, style='thin'):
    return Side(style=style, color=color or C.CLOUD)


# ── schema ───────────────────────────────────────────────────────────────────
S = {'type': 'string', 'minLength': 1}
NUM = {'type': 'number'}
BOOL = {'type': 'boolean'}
DATE = {'type': 'string', 'pattern': r'^\d{4}-\d{2}-\d{2}$'}
KEY = {'type': 'string', 'pattern': r'^[A-Za-z_][A-Za-z0-9_]*$'}
FORMULA = {'type': 'string', 'pattern': r'^='}
SCALAR = {'type': ['string', 'number', 'boolean', 'null']}
FORMATS = ['text', 'int', 'number', 'currency', 'percent', 'date', 'hours', 'yesno', 'check']
CHECK = '\u2713'
SHEET_NAME = {'type': 'string', 'minLength': 1, 'maxLength': 31, 'pattern': r'^[^\[\]:*?/\\]+$'}


def _obj(props, required=()):
    return {'type': 'object', 'properties': props, 'required': list(required), 'additionalProperties': False}


def _arr(item, lo=0, hi=None):
    a = {'type': 'array', 'items': item, 'minItems': lo}
    if hi is not None:
        a['maxItems'] = hi
    return a


COLUMN = _obj({'key': KEY, 'header': S, 'width': {'type': 'number', 'minimum': 2, 'maximum': 80},
               'format': {'enum': FORMATS},
               'decimals': {'type': 'integer', 'minimum': 0, 'maximum': 4},
               'total': {'enum': ['sum', 'average', 'count', 'formula', 'none']},
               'formula': FORMULA, 'input': BOOL, 'wrap': BOOL,
               'align': {'enum': ['left', 'center', 'right']}}, ['key', 'header'])
# Rows may carry richer records than the table shows (bound straight from data); only the
# columns are written, and a list in a column prints as a comma-separated string.
ROW = {'type': 'object', 'propertyNames': KEY}
TABLE_PROPS = {
    'columns': _arr(COLUMN, 1, 26),
    'rows': _arr(ROW),
    'groups': _arr(_obj({'name': S, 'id': KEY, 'rows': _arr(ROW, 1), 'subtotal': BOOL}, ['name', 'rows']), 1),
    'total_label': S, 'totals': BOOL, 'total_row': BOOL, 'autofilter': BOOL, 'zebra': BOOL, 'note': S,
}
COMMON = {'name': SHEET_NAME, 'kind': {'enum': ['table', 'gantt', 'form', 'summary']},
          'title': S, 'subtitle': S, 'landscape': BOOL}

TASK = _obj({'id': {'type': ['string', 'integer']}, 'name': S, 'start': DATE, 'end': DATE,
             'duration_days': {'type': 'integer', 'minimum': 1}, 'owner': S,
             'parent': {'type': ['string', 'integer']}, 'milestone': BOOL,
             'percent': {'type': 'number', 'minimum': 0, 'maximum': 1},
             'depends_on': _arr({'type': ['string', 'integer']}, 1)}, ['id', 'name'])

ITEM = _obj({'sku': S, 'date': DATE, 'category': S, 'description': S, 'merchant': S,
             'qty': NUM, 'unit': S, 'rate': NUM, 'amount': NUM}, [])

KINDS = {
    'table': _obj({**COMMON, **TABLE_PROPS}, ['name', 'kind', 'columns']),
    'gantt': _obj({**COMMON, 'scale': {'enum': ['week', 'day', 'month']}, 'today': BOOL,
                   'tasks': _arr(TASK, 1, 200)}, ['name', 'kind', 'tasks']),
    'form': _obj({**COMMON, 'form': {'enum': ['invoice', 'purchase_order', 'expense_report']},
                  'number': S,
                  'details': _arr(_obj({'label': S, 'value': {'type': ['string', 'number']},
                                        'format': {'enum': FORMATS}}, ['label', 'value']), 0, 8),
                  'parties': _arr(_obj({'label': S, 'lines': _arr(S, 1, 6)}, ['label', 'lines']), 0, 3),
                  'items': _arr(ITEM, 1, 60), 'blank_rows': {'type': 'integer', 'minimum': 0, 'maximum': 30},
                  'discount_rate': {'type': 'number', 'minimum': 0, 'maximum': 1},
                  'discount': {'type': 'number', 'minimum': 0},
                  'tax_rate': {'type': 'number', 'minimum': 0, 'maximum': 1}, 'tax_label': S,
                  'shipping': {'type': 'number', 'minimum': 0}, 'advance': {'type': 'number', 'minimum': 0},
                  'terms': S, 'payment': _arr(S, 1, 6),
                  'notes': {'oneOf': [S, _arr(S, 1, 8)]},
                  'signatures': _arr(S, 0, 4)}, ['name', 'kind', 'form', 'items']),
    'summary': _obj({**COMMON, 'eyebrow': S, 'meta': BOOL,
                     'metrics': _arr(_obj({'label': S, 'key': KEY, 'value': {'type': ['string', 'number', 'boolean']},
                                           'format': {'enum': FORMATS},
                                           'decimals': {'type': 'integer', 'minimum': 0, 'maximum': 4},
                                           'note': S}, ['label', 'value']), 0, 8),
                     'per_row': {'type': 'integer', 'minimum': 1, 'maximum': 4},
                     'table': _obj({k: v for k, v in TABLE_PROPS.items() if k != 'groups'}, ['columns']),
                     'notes': _arr(S, 1, 8), 'contents': BOOL}, ['name', 'kind']),
}

SHEET = {'type': 'object', 'required': ['name', 'kind'],
         'properties': {'kind': {'enum': list(KINDS)}},
         'allOf': [{'if': {'properties': {'kind': {'const': k}}, 'required': ['kind']}, 'then': v}
                   for k, v in KINDS.items()]}

SCHEMA = {
    '$schema': 'https://json-schema.org/draft/2020-12/schema',
    'type': 'object',
    'properties': {'workbook': S, 'client': S, 'date': DATE, 'prepared_for': S, 'prepared_by': S,
                   'currency': {'type': 'string', 'minLength': 1, 'maxLength': 4}, 'brand': S,
                   'drive': {'type': 'object', 'properties': {'root': {'enum': ['customers', 'demo']}, 'folder': S}, 'additionalProperties': False},
                   'sheets': _arr(SHEET, 1, 30)},
    'required': ['workbook', 'client', 'sheets'],
    'additionalProperties': False,
}


def _where(err):
    out = []
    path = list(err.absolute_path)
    for i, p in enumerate(path):
        if isinstance(p, int):
            out[-1] = f'{out[-1]}[{p + 1}]' if out else f'[{p + 1}]'
        else:
            out.append(str(p))
    return '.'.join(out) or '(top)'


def _schema_errors(data):
    errs = sorted(Draft202012Validator(SCHEMA).iter_errors(data), key=lambda e: list(e.absolute_path))
    msgs = []
    for e in errs:
        # if/then failures surface as the inner error; keep the deepest, most specific one.
        leaves = [e] if not e.context else sorted(e.context, key=lambda x: -len(list(x.absolute_path)))[:1]
        for x in leaves:
            m = x.message
            if x.validator == 'additionalProperties':
                m += '. Check the field name against the spec format (sheets.py docstring).'
            if x.validator == 'pattern' and 'Za-z_' in str(x.schema.get('pattern', '')):
                m += ' (keys are letters, digits and underscores)'
            split = isinstance(x.instance, dict) and any(v is None for v in x.instance.values())
            if split or re.search(r"'[^']* [^']*' (was unexpected|does not match)", m):
                m += ('\n    Most often a comma inside {...} split a value in two: put the whole value '
                      'in double quotes.')
            msgs.append(f'  {_where(x)}: {m}')
    return msgs


def load(path):
    """Load and validate a workbook spec. Raises SpecError with readable messages."""
    path = Path(path).expanduser()
    raw = path.read_text()
    try:
        data = yaml.load(raw, Loader=_StrictLoader)
    except yaml.YAMLError as e:
        raise SpecError(f'{path.name}: not valid YAML: {e}\n'
                        '  Most often: a value containing ": " or "#". Put it in double quotes.')
    validate(data, name=path.name)
    data.setdefault('date', dt.date.today().isoformat())
    data['_path'] = str(path.resolve())
    data['_sha'] = hashlib.sha256(raw.encode()).hexdigest()[:12]
    return data


def validate(data, name='spec'):
    """Schema plus the rules a schema cannot say. Raises SpecError."""
    if not isinstance(data, dict):
        raise SpecError(f'{name}: the spec must be a mapping with workbook, client and sheets')
    msgs = _schema_errors(data)
    if msgs:
        raise SpecError(f'{name} does not match the workbook spec format:\n' + '\n'.join(dict.fromkeys(msgs)))
    errs = []
    seen = set()
    for i, sh in enumerate(data['sheets'], 1):
        where = f'sheets[{i}] ({sh["name"]})'
        low = sh['name'].lower()
        if low in seen:
            errs.append(f'  {where}: two sheets are named "{sh["name"]}"')
        seen.add(low)
        if sh['kind'] == 'table':
            errs += _check_table(sh, where, need_rows=True)
        elif sh['kind'] == 'summary' and sh.get('table'):
            errs += _check_table(sh['table'], where + '.table', need_rows=True)
        elif sh['kind'] == 'gantt':
            try:
                Plan(sh['tasks'])
            except SpecError as e:
                errs.append(f'  {where}: {e}')
        elif sh['kind'] == 'form':
            allowed = {k for k, *_ in FORM_COLS[sh['form']]} | ({'qty', 'rate'} if sh['form'] != 'expense_report' else set())
            for j, it in enumerate(sh['items'], 1):
                bad = set(it) - allowed
                if bad:
                    errs.append(f'  {where}.items[{j}]: {", ".join(sorted(bad))} not used on a {sh["form"]} '
                                f'(it takes {", ".join(k for k, *_ in FORM_COLS[sh["form"]])})')
            if sh.get('discount') is not None and sh.get('discount_rate') is not None:
                errs.append(f'  {where}: give discount or discount_rate, not both')
    if errs:
        raise SpecError(f'{name}:\n' + '\n'.join(errs))


def _check_table(t, where, need_rows):
    errs = []
    keys = [c['key'] for c in t['columns']]
    dup = {k for k in keys if keys.count(k) > 1}
    if dup:
        errs.append(f'  {where}: column keys repeat: {", ".join(sorted(dup))}')
    if t.get('rows') and t.get('groups'):
        errs.append(f'  {where}: give rows or groups, not both')
    if need_rows and not (t.get('rows') or t.get('groups')):
        errs.append(f'  {where}: a table needs rows (or groups of rows)')
    # Row keys that are not columns are ignored, so rows can bind straight from richer
    # records. Columns and sheets stay strict (the schema rejects unknown keys there).
    for c in t['columns']:
        for other, sigil, k in _REF.findall(c.get('formula', '')):
            # [#name] may be a same-sheet metric or total, resolved at build time.
            if not other and sigil != '#' and k.split('.')[0] not in keys:
                errs.append(f'  {where}: column {c["key"]} formula refers to [{sigil}{k}], which is not a column')
        if c.get('total') == 'formula' and not c.get('formula'):
            errs.append(f'  {where}: column {c["key"]} has total: formula but no formula')
    return errs


# ── formats ──────────────────────────────────────────────────────────────────
_DEFAULT_DECIMALS = {'number': 2, 'currency': 2, 'percent': 0, 'hours': 1}
_DEFAULT_WIDTH = {'text': 24, 'int': 10, 'number': 12, 'currency': 14, 'percent': 10, 'date': 13, 'hours': 10,
                  'yesno': 9, 'check': 8}


def numfmt(fmt, decimals=None, cur='$'):
    fmt = fmt or 'text'
    d = _DEFAULT_DECIMALS.get(fmt, 0) if decimals is None else decimals
    frac = ('.' + '0' * d) if d else ''
    if fmt == 'int':
        return '#,##0'
    if fmt in ('number', 'hours'):
        return f'#,##0{frac}'
    if fmt == 'currency':
        c = f'"{cur}"'
        return f'{c}#,##0{frac};-{c}#,##0{frac};{c}0{frac}'
    if fmt == 'percent':
        return f'0{frac}%'
    if fmt == 'date':
        return 'mmm d, yyyy'
    return 'General'


def _indent(horizontal):
    # Text gets one indent of breathing room. Right-aligned numbers get none: LibreOffice
    # drops the indent on some formula cells (subtotals in a table's last column) and keeps
    # it on others, so indented columns printed out of line. Flush right is consistent.
    return 0 if horizontal == 'right' else 1


def _is_num(fmt):
    return fmt not in (None, 'text', 'date', 'yesno', 'check')


def cell_value(v, fmt):
    """A spec value as the cell should hold it. Booleans never reach a cell as TRUE/FALSE:
       they read Yes/No (or a check mark in a `check` column), as text a person can retype."""
    if isinstance(v, (list, tuple)):
        return ', '.join(str(x) for x in v)
    if isinstance(v, dict):
        return ', '.join(f'{k}: {x}' for k, x in v.items())
    if isinstance(v, bool):
        if fmt == 'check':
            return CHECK if v else None
        return 'Yes' if v else 'No'
    if fmt == 'date':
        return _as_date(v)
    return v


# ── wrapping: rows are sized from the text, since no app grows a merged row ───
def text_lines(text, width_chars, size=10, *, bold=False, name=None, indent=1):
    """Lines `text` takes in a column `width_chars` wide (conservative: a cut line is worse
       than a spare one)."""
    if text is None or text == '':
        return 1
    w = max(0.25, width_chars * 0.068 - 0.07 * indent - 0.06)
    return max(K.est_lines(line, w, size, font=name or BODY, bold=bold) for line in str(text).split('\n'))


def line_h(lines, size=10, pad=5):
    return round(pad + lines * size * 1.32, 1)


def grow(ws, row, height):
    """Raise a row to `height` points, never lower it."""
    cur = ws.row_dimensions[row].height or 15
    ws.row_dimensions[row].height = max(cur, height)


def _as_date(v):
    if isinstance(v, str) and re.fullmatch(r'\d{4}-\d{2}-\d{2}', v):
        return dt.date.fromisoformat(v)
    return v


def long_date(s):
    d = dt.date.fromisoformat(s)
    return f'{d:%B} {d.day}, {d.year}'


def _inches(width_chars):
    # A column-width unit is one digit of the default font (the body face at 10 pt: ~6 px).
    return width_chars * 0.07


# ── formula references ───────────────────────────────────────────────────────
_REF = re.compile(r'\[(?:([^\[\]!]+)!)?([@#]?)([A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)?)\]')


def slug(name):
    return re.sub(r'[^a-z0-9]+', '_', str(name).lower()).strip('_') or 'group'


# ── the plan model (gantt) ───────────────────────────────────────────────────
def _workday(d, n):
    """Excel's WORKDAY(d, n) with no holiday list (n >= 0)."""
    while n > 0:
        d += dt.timedelta(days=1)
        if d.weekday() < 5:
            n -= 1
    return d


class Plan:
    """Tasks in outline order with WBS numbers and build-time dates (the sheet recomputes
       them; these only size the timeline and catch mistakes before anything renders)."""

    def __init__(self, tasks):
        self.by_id = {}
        for t in tasks:
            tid = str(t['id'])
            if tid in self.by_id:
                raise SpecError(f'task id "{tid}" is used twice')
            self.by_id[tid] = dict(t, id=tid, parent=None if t.get('parent') is None else str(t['parent']),
                                   depends_on=[str(x) for x in t.get('depends_on', [])])
        self.children = {tid: [] for tid in self.by_id}
        roots = []
        for t in self.by_id.values():
            if t['parent'] is None:
                roots.append(t['id'])
            elif t['parent'] not in self.by_id:
                raise SpecError(f'task "{t["id"]}": parent "{t["parent"]}" is not a task id')
            else:
                self.children[t['parent']].append(t['id'])
        self.order, self.wbs, self.depth = [], {}, {}

        def walk(ids, prefix, depth, trail):
            for n, tid in enumerate(ids, 1):
                if tid in trail:
                    raise SpecError(f'task "{tid}" is its own ancestor')
                self.order.append(tid)
                self.wbs[tid] = f'{prefix}{n}'
                self.depth[tid] = depth
                walk(self.children[tid], f'{prefix}{n}.', depth + 1, trail | {tid})
        walk(roots, '', 0, frozenset())
        if len(self.order) != len(self.by_id):
            raise SpecError('some tasks sit in a parent loop')
        for tid, t in self.by_id.items():
            name = f'task "{tid}"'
            for d in t['depends_on']:
                if d not in self.by_id:
                    raise SpecError(f'{name}: depends_on "{d}" is not a task id')
            if self.is_phase(tid):
                for k in ('start', 'end', 'duration_days', 'milestone', 'percent'):
                    if k in t:
                        raise SpecError(f'{name} is a phase (it has children): its {k} comes from them, '
                                        f'remove it')
                continue
            if 'start' not in t and not t['depends_on']:
                raise SpecError(f'{name}: give a start date or depends_on')
            if t.get('milestone'):
                if 'end' in t or 'duration_days' in t:
                    raise SpecError(f'{name}: a milestone has a start only')
            elif ('end' in t) == ('duration_days' in t):
                raise SpecError(f'{name}: give end or duration_days (one of them)')
        self.dates = {}
        for tid in self.order:
            self._dates(tid, set())
        for tid, t in self.by_id.items():
            s, e = self.dates[tid]
            if e < s:
                raise SpecError(f'task "{tid}": ends ({e}) before it starts ({s})')

    def is_phase(self, tid):
        return bool(self.children[tid])

    def _dates(self, tid, trail):
        if tid in self.dates:
            return self.dates[tid]
        if tid in trail:
            raise SpecError(f'task "{tid}": depends_on forms a loop')
        trail = trail | {tid}
        t = self.by_id[tid]
        if self.is_phase(tid):
            kids = [self._dates(k, trail) for k in self.children[tid]]
            r = (min(k[0] for k in kids), max(k[1] for k in kids))
        else:
            if 'start' in t:
                s = dt.date.fromisoformat(t['start'])
            else:
                s = _workday(max(self._dates(d, trail)[1] for d in t['depends_on']), 1)
            if t.get('milestone'):
                e = s
            elif 'end' in t:
                e = dt.date.fromisoformat(t['end'])
            else:
                e = _workday(s, t['duration_days'] - 1)
            r = (s, e)
        self.dates[tid] = r
        return r


# ── form layouts ─────────────────────────────────────────────────────────────
# (key, header, width or None for "the rest", format, optional, role)
FORM_COLS = {
    'invoice': [('description', 'Description', None, 'text', False, 'text'),
                ('qty', 'Qty', 8, 'qty', False, 'input'),
                ('unit', 'Unit', 8, 'text', True, 'text'),
                ('rate', 'Rate', 13, 'currency', False, 'input'),
                ('amount', 'Amount', 15, 'currency', False, 'line')],
    'purchase_order': [('sku', 'Item', 12, 'text', True, 'text'),
                       ('description', 'Description', None, 'text', False, 'text'),
                       ('qty', 'Qty', 8, 'qty', False, 'input'),
                       ('unit', 'Unit', 8, 'text', True, 'text'),
                       ('rate', 'Unit price', 13, 'currency', False, 'input'),
                       ('amount', 'Amount', 15, 'currency', False, 'line')],
    'expense_report': [('date', 'Date', 13, 'date', False, 'input'),
                       ('category', 'Category', 16, 'text', False, 'text'),
                       ('description', 'Description', None, 'text', False, 'text'),
                       ('merchant', 'Merchant', 18, 'text', True, 'text'),
                       ('amount', 'Amount', 15, 'currency', False, 'input')],
}
FORM_TITLE = {'invoice': 'Invoice', 'purchase_order': 'Purchase order', 'expense_report': 'Expense report'}
FORM_NUMBER = {'invoice': 'Invoice no.', 'purchase_order': 'PO number', 'expense_report': 'Report no.'}
FORM_TOTAL = {'invoice': 'Total due', 'purchase_order': 'Total', 'expense_report': 'Amount due'}
FORM_SIGN = {'invoice': [], 'purchase_order': ['Authorized by', 'Date'],
             'expense_report': ['Employee signature', 'Approved by']}
FORM_WIDTH = 92                         # character units across a portrait page, gutters excluded


def _party_rows(n, widths, min_w=26):
    """Lay n party blocks (<= 3) across the item columns: as many to a row as fit with
       every block at least `min_w` characters wide, the rest on the next row. Returns
       rows of [(party index, (first col index, last col index))]."""
    def best_split(k):
        # contiguous spans over the columns, maximising the narrowest
        best = None
        import itertools
        for cuts in itertools.combinations(range(1, len(widths)), k - 1):
            edges = (0,) + cuts + (len(widths),)
            spans = [(edges[i], edges[i + 1] - 1) for i in range(k)]
            narrow = min(sum(widths[a:b + 1]) for a, b in spans)
            if best is None or narrow > best[0]:
                best = (narrow, spans)
        return best
    per = 1
    for k in range(min(n, 3, len(widths)), 0, -1):
        b = best_split(k)
        if b and (b[0] >= min_w or k == 1):
            per = k
            break
    spans = best_split(per)[1]
    rows, i = [], 0
    while i < n:
        rows.append([(i + j, spans[j]) for j in range(min(per, n - i))])
        i += per
    return rows


# Functions that need Excel 2010+ name prefixes or are missing from Google Sheets or
# LibreOffice: a sheet using them opens with #NAME? somewhere. Everything else is allowed,
# including INT, MOD, SUMIF(S), COUNTIF(S), ROUNDUP, ROUNDDOWN, CEILING, FLOOR and IFERROR.
UNSAFE_FUNCTIONS = {'XLOOKUP', 'XMATCH', 'IFS', 'SWITCH', 'MAXIFS', 'MINIFS', 'TEXTJOIN', 'CONCAT', 'LET',
                    'LAMBDA', 'FILTER', 'SORT', 'SORTBY', 'UNIQUE', 'SEQUENCE', 'RANDARRAY', 'XOR',
                    'CEILING.MATH', 'FLOOR.MATH', 'STOCKHISTORY', 'TOCOL', 'TOROW', 'VSTACK', 'HSTACK'}
_FUNC = re.compile(r'([A-Z][A-Z0-9.]*)\s*\(')


def unsafe_functions(formula):
    """Names in `formula` that would not survive Excel, Sheets and LibreOffice alike."""
    body = re.sub(r'"[^"]*"', '', str(formula).upper())
    return sorted({f for f in _FUNC.findall(body) if f in UNSAFE_FUNCTIONS})


# ── the workbook ─────────────────────────────────────────────────────────────
class Book:
    def __init__(self, spec):
        self.spec = spec
        self.cur = spec.get('currency', '$')
        self.wb = Workbook()
        tx = theme_xml.encode() if isinstance(theme_xml, str) else theme_xml
        self.wb.loaded_theme = brand.brand_theme_xml(tx)
        set_default_font(self.wb)
        self.registry = {}               # sheet -> {'#key' | 'key': template with {s} for the sheet prefix}
        self.pending = []                # (cell, template, sheet, row, cols)

    # -- formulas
    def later(self, cell, template, sheet, row=None, cols=None):
        self.pending.append((cell, template, sheet, row, cols))

    def resolve(self, template, sheet, row=None, cols=None, ws=None):
        def sub(m):
            other, sigil, key = m.groups()
            if sigil == '@':
                if other or cols is None or key not in cols:
                    raise SpecError(f'{sheet}: {template!r}: [@{key}] needs a column "{key}" on this table')
                ref = f'{cols[key]}{row}'
                # A boolean lands in its cell as the text Yes/No, so a formula that tests it as a
                # condition (IF([@done], ...)) would see text. Compare it to "Yes" instead, unless
                # the formula already compares it to something.
                rest = template[m.end():].lstrip()
                if ws is not None and ws[ref].value in ('Yes', 'No') and not rest.startswith(('=', '<>')):
                    return f'({ref}="Yes")'
                return ref
            target = other.strip() if other else sheet
            reg = self.registry.get(target)
            if reg is None:
                raise SpecError(f'{sheet}: {template!r}: no sheet named "{target}" '
                                f'(sheets: {", ".join(self.registry)})')
            tok = sigil + key
            if tok not in reg:
                raise SpecError(f'{sheet}: {template!r}: "{target}" has no [{tok}]. '
                                f'It offers: {", ".join("[" + t + "]" for t in reg)}')
            return reg[tok].format(s='' if target == sheet else quote_sheetname(target) + '!')
        return _REF.sub(sub, template)

    def finish_formulas(self):
        for cell, template, sheet, row, cols in self.pending:
            bad = unsafe_functions(template)
            if bad:
                raise SpecError(f'{sheet}: {template!r} uses {", ".join(bad)}, which Excel, Google Sheets and '
                                'LibreOffice do not all support. Rewrite it with SUMIFS, INDEX/MATCH, IF or '
                                'IFERROR.')
            cell.value = self.resolve(template, sheet, row, cols, ws=cell.parent)

    # -- build
    def build(self):
        ws0 = self.wb.active
        for i, sh in enumerate(self.spec['sheets']):
            ws = ws0 if i == 0 else self.wb.create_sheet()
            ws.title = sh['name']
            self.registry.setdefault(sh['name'], {})
            {'table': TableSheet, 'gantt': GanttSheet, 'form': FormSheet, 'summary': SummarySheet}[sh['kind']](
                self, ws, sh).render()
        self.finish_formulas()
        p = self.wb.properties
        p.creator = p.lastModifiedBy = K.BRAND_NAME
        p.title = f'{self.spec["client"]} {self.spec["workbook"]}'
        p.subject = self.spec['workbook']
        p.keywords = self.spec['client']
        p.created = p.modified = dt.datetime.combine(dt.date.fromisoformat(self.spec['date']), dt.time(9))
        # No cached values are written, so Excel must calculate on open.
        self.wb.calculation = CalcProperties(fullCalcOnLoad=True)
        self.wb.active = 0
        return self.wb


class Sheet:
    landscape = True
    band_h = 30

    def __init__(self, book, ws, sh):
        self.book, self.ws, self.sh = book, ws, sh
        self.name = sh['name']
        self.cur = book.cur
        self.last_col = 2                # rightmost content column (1-based)
        self.last_row = 1
        ws.sheet_view.showGridLines = False
        ws.sheet_view.zoomScale = 100

    @property
    def reg(self):
        return self.book.registry[self.name]

    # -- chrome
    def widths(self, widths, start=1):
        for i, w in enumerate(widths, start):
            self.ws.column_dimensions[get_column_letter(i)].width = w

    def band(self, *, thin=False):
        """Row 1: the brand band across the page. A thin rule on forms (their logo sits on
           light in the header block); the logo on dark everywhere else."""
        ws = self.ws
        ws.row_dimensions[1].height = 5 if thin else self.band_h
        for c in range(1, self.last_col + 2):
            ws.cell(row=1, column=c).fill = solid(C.FOREST)
        if thin:
            return
        logo = K.LOGO_ON_DARK
        px_h = int(self.band_h * 96 / 72)
        if logo and Path(logo).exists():
            img = XLImage(str(logo))
            h = 17
            w = int(round(img.width * h / img.height))
            img.width, img.height = w, h
            img.anchor = OneCellAnchor(
                _from=AnchorMarker(col=1, colOff=0, row=0, rowOff=pixels_to_EMU((px_h - h) // 2)),
                ext=XDRPositiveSize2D(pixels_to_EMU(w), pixels_to_EMU(h)))
            ws.add_image(img)
        else:
            c = ws.cell(row=1, column=2, value=K.BRAND_NAME)
            c.font = font(13, color=C.WHITE, name=DISPLAY)
            c.alignment = Alignment(vertical='center')
        right = ws.cell(row=1, column=self.last_col, value=self.book.spec['workbook'])
        right.font = font(9, color=C.ON_DARK)
        right.alignment = Alignment(horizontal='right', vertical='center')

    def span_chars(self, c0, c1):
        """Width of columns c0..c1 (1-based, inclusive) in character units."""
        return sum(self.ws.column_dimensions[get_column_letter(c)].width or 8.43 for c in range(c0, c1 + 1))

    def merge_row(self, row, c0, c1):
        if c1 > c0:
            self.ws.merge_cells(start_row=row, start_column=c0, end_row=row, end_column=c1)

    def heading(self, top=3, *, eyebrow=None):
        """Eyebrow, title, subtitle. Returns the next free row."""
        ws, sp = self.ws, self.book.spec
        eb = eyebrow or f'{sp["client"]}  ·  {long_date(sp["date"])}'
        c = ws.cell(row=top, column=2, value=eb.upper())
        c.font = font(8.5, bold=True, color=C.GREEN_600)
        ws.row_dimensions[top].height = 15
        span = self.span_chars(2, self.last_col)
        title = self.sh.get('title', self.name)
        t = ws.cell(row=top + 1, column=2, value=title)
        t.font = font(20, color=C.FOREST, name=DISPLAY)
        t.alignment = Alignment(vertical='center', wrap_text=True)
        self.merge_row(top + 1, 2, self.last_col)
        n = text_lines(title, span, 20, name=DISPLAY, indent=0)
        ws.row_dimensions[top + 1].height = 32 if n == 1 else line_h(n, 20, 8)
        r = top + 2
        if self.sh.get('subtitle'):
            s = ws.cell(row=r, column=2, value=self.sh['subtitle'])
            s.font = font(10.5, color=C.MUTED)
            s.alignment = Alignment(vertical='top', wrap_text=True)
            self.merge_row(r, 2, self.last_col)
            ws.row_dimensions[r].height = line_h(text_lines(self.sh['subtitle'], span, 10.5, indent=0), 10.5, 3)
            r += 1
        ws.row_dimensions[r].height = 10
        return r + 1

    def page(self, *, landscape=None, fit_height=0, title_rows=None, margins=(0.45, 0.5, 0.6)):
        ws = self.ws
        land = self.sh.get('landscape', self.landscape if landscape is None else landscape)
        ws.page_setup.orientation = 'landscape' if land else 'portrait'
        ws.page_setup.paperSize = ws.PAPERSIZE_LETTER
        ws.page_setup.fitToWidth, ws.page_setup.fitToHeight = 1, fit_height
        ws.sheet_properties.pageSetUpPr.fitToPage = True
        ws.print_options.horizontalCentered = True
        side_m, top_m, bottom_m = margins
        ws.page_margins.left = ws.page_margins.right = side_m
        ws.page_margins.top, ws.page_margins.bottom = top_m, bottom_m
        ws.page_margins.header, ws.page_margins.footer = 0.25, 0.3
        for part, txt in ((ws.oddFooter.left, K.FOOTER_TEXT), (ws.oddFooter.right, 'Page &P of &N')):
            part.text, part.size, part.font, part.color = txt, 8, BODY, C.MUTED
        if title_rows:
            ws.print_title_rows = title_rows
        ws.print_area = f'A1:{get_column_letter(self.last_col + 1)}{self.last_row}'


# ── table ────────────────────────────────────────────────────────────────────
class TableSheet(Sheet):
    def render(self):
        sh, ws = self.sh, self.ws
        cols = sh['columns']
        self.last_col = 1 + len(cols)
        widths = [2.5] + [c.get('width', max(_DEFAULT_WIDTH[c.get('format', 'text')], len(c['header']) + 4))
                          for c in cols] + [2.5]
        self.widths(widths)
        self.band()
        top = self.heading()
        t = Table(self, sh, top, standalone=True)
        t.render()
        self.last_row = t.end_row
        ws.freeze_panes = f'A{t.header_row + 1}'
        ws.sheet_properties.tabColor = C.GREEN
        # Portrait while the table fits a portrait page at a readable scale; wider goes landscape.
        self.page(landscape=sum(widths) > 118, title_rows=f'{t.header_row}:{t.header_row}')


class Table:
    """A table at (top, column B) on a sheet: header, rows or groups, subtotals and a
       total row, all as live formulas. Registers [key] and [#key] for the sheet."""

    def __init__(self, sheet, spec, top, *, standalone):
        self.s, self.t, self.top, self.standalone = sheet, spec, top, standalone
        self.cols = spec['columns']
        self.letters = {c['key']: get_column_letter(2 + i) for i, c in enumerate(self.cols)}
        self.header_row = top
        self.end_row = top
        # The narrow gutter after the last column carries the row's fill and rules, so a
        # flush-right number in the last column does not sit on the table's edge.
        pad_col = 2 + len(self.cols)
        w = sheet.ws.column_dimensions[get_column_letter(pad_col)].width
        self.pad = get_column_letter(pad_col) if w and w <= 3 else None

    def padded(self, r):
        if self.pad:
            src = self.s.ws[f'{self.letters[self.cols[-1]["key"]]}{r}']
            dst = self.s.ws[f'{self.pad}{r}']
            dst._style = copy(src._style)          # fill, rules and font; the cell stays empty

    def fmt(self, c):
        f = c.get('format', 'text')
        return numfmt(f, c.get('decimals'), self.s.cur)

    def align(self, c):
        f = c.get('format', 'text')
        a = c.get('align') or ('right' if _is_num(f) or f == 'date' else 'center' if f in ('yesno', 'check') else 'left')
        return Alignment(horizontal=a, vertical='center', indent=_indent(a), wrap_text=self.wraps(c))

    @staticmethod
    def wraps(c):
        return c.get('wrap', c.get('format', 'text') == 'text')

    def width(self, c):
        return self.s.ws.column_dimensions[self.letters[c['key']]].width or _DEFAULT_WIDTH[c.get('format', 'text')]

    def header(self, r):
        ws = self.s.ws
        ws.row_dimensions[r].height = 22
        for c in self.cols:
            cell = ws[f'{self.letters[c["key"]]}{r}']
            cell.value = c['header'].upper()
            cell.font = font(8.5, bold=True, color=C.WHITE)
            cell.fill = solid(C.FOREST)
            a = self.align(c)
            cell.alignment = Alignment(horizontal=a.horizontal, vertical='center', indent=_indent(a.horizontal),
                                       wrap_text=True)
        n = max(text_lines(c['header'].upper(), self.width(c), 8.5, bold=True) for c in self.cols)
        if n > 1:
            grow(ws, r, line_h(n, 8.5, 8))
        self.padded(r)

    def row_cells(self, r, values, *, style='data'):
        ws, book = self.s.ws, self.s.book
        for c in self.cols:
            k = c['key']
            cell = ws[f'{self.letters[k]}{r}']
            v = values.get(k) if values is not None else None
            tmpl = None
            if isinstance(v, str) and v.startswith('='):
                tmpl = v
            elif v is None and c.get('formula'):
                tmpl = c['formula']
            if tmpl:
                book.later(cell, tmpl, self.s.name, r, self.letters)
                color = C.INK_800
            else:
                cell.value = cell_value(v, c.get('format'))
                color = C.INPUT if c.get('input') and v is not None else C.INK_800
            cell.font = font(10, color=color)
            cell.number_format = self.fmt(c)
            cell.alignment = self.align(c)
            cell.border = Border(bottom=side(C.CLOUD))
        self.padded(r)
        ws.row_dimensions[r].height = self.row_h(values)

    def row_h(self, values):
        lines = 1
        for c in self.cols:
            v = values.get(c['key']) if values else None
            if self.wraps(c) and isinstance(v, str) and not v.startswith('='):
                lines = max(lines, text_lines(v, self.width(c), 10))
        return 18 if lines == 1 else line_h(lines, 10, 6)

    def ranges(self, key, blocks, prefix='{s}'):
        L = self.letters[key]
        return ','.join(f'{prefix}${L}${a}:${L}${b}' for a, b in blocks if b >= a)

    def summary_row(self, r, blocks, label, *, kind):
        """kind: 'subtotal' | 'total'. Sums are over the data blocks only, so a grand total
           never double counts its subtotals."""
        ws, book = self.s.ws, self.s.book
        strong = kind == 'total'
        ws.row_dimensions[r].height = 22 if strong else 19
        for i, c in enumerate(self.cols):
            k = c['key']
            cell = ws[f'{self.letters[k]}{r}']
            how = c.get('total', 'none')
            refs = ','.join(f'{self.letters[k]}{a}:{self.letters[k]}{b}' for a, b in blocks if b >= a)
            if how == 'sum' and refs:
                cell.value = f'=SUM({refs})'
            elif how == 'average' and refs:
                cell.value = f'=IFERROR(AVERAGE({refs}),0)'
            elif how == 'count' and refs:
                f = c.get('format', 'text')
                cell.value = (f'=COUNTIF({refs},"Yes")' if f == 'yesno' and ',' not in refs else
                              f'=COUNTIF({refs},"{CHECK}")' if f == 'check' and ',' not in refs else
                              f'=COUNTA({refs})')
            elif how == 'formula':
                book.later(cell, c['formula'], self.s.name, r, self.letters)
            elif i == 0:
                cell.value = label
            cell.number_format = self.fmt(c)
            al = self.align(c)
            cell.alignment = Alignment(horizontal=al.horizontal, vertical='center', indent=_indent(al.horizontal))
            if strong:
                cell.font = font(10.5, bold=True, color=C.FOREST)
                cell.fill = solid(C.MINT)
                cell.border = Border(top=side(C.FOREST, 'medium'), bottom=side(C.FOREST, 'medium'))
            else:
                cell.font = font(10, bold=True, color=C.INK_800)
                cell.border = Border(top=side(C.MUTED), bottom=side(C.CLOUD))
        self.padded(r)
        # The label spans the leading columns that carry no figure, and wraps if it must.
        lead = 0
        for c in self.cols:
            if c.get('total', 'none') != 'none':
                break
            lead += 1
        lead = max(1, lead)
        first = ws[f'{self.letters[self.cols[0]["key"]]}{r}']
        first.alignment = Alignment(horizontal='left', vertical='center', indent=1, wrap_text=True)
        if lead > 1:
            ws.merge_cells(f'{self.letters[self.cols[0]["key"]]}{r}:{self.letters[self.cols[lead - 1]["key"]]}{r}')
        n = text_lines(label, sum(self.width(c) for c in self.cols[:lead]), 10.5 if strong else 10, bold=True)
        if n > 1:
            grow(ws, r, line_h(n, 10.5 if strong else 10, 8))

    def render(self):
        s, ws, t = self.s, self.s.ws, self.t
        r = self.top
        self.header(r)
        r += 1
        grouped = bool(t.get('groups'))
        groups = t.get('groups') or [{'name': None, 'rows': t.get('rows') or []}]
        blocks, self.group_refs = [], []
        for gi, g in enumerate(groups):
            if g['name']:
                ws.row_dimensions[r].height = 21
                for c in self.cols:
                    cell = ws[f'{self.letters[c["key"]]}{r}']
                    cell.fill = solid(C.MINT_TINT)
                    cell.border = Border(bottom=side(C.MINT))
                self.padded(r)
                first = ws[f'B{r}']
                first.value = g['name']
                first.font = font(10.5, bold=True, color=C.FOREST)
                first.alignment = Alignment(vertical='center', indent=1, wrap_text=True)
                last_l = self.letters[self.cols[-1]['key']]
                if last_l != 'B':
                    ws.merge_cells(f'B{r}:{last_l}{r}')
                n = text_lines(g['name'], sum(self.width(c) for c in self.cols), 10.5, bold=True)
                if n > 1:
                    grow(ws, r, line_h(n, 10.5, 8))
                r += 1
            a = r
            for row in g['rows']:
                self.row_cells(r, row)
                r += 1
            blocks.append((a, r - 1))
            sub_row = None
            if grouped and g.get('subtotal', True) and any(c.get('total', 'none') != 'none' for c in self.cols):
                self.summary_row(r, [(a, r - 1)], 'Subtotal', kind='subtotal')
                sub_row = r
                r += 1
            if grouped:
                self.group_refs.append((g.get('id') or slug(g['name']), (a, r - 1 - (sub_row is not None)), sub_row))
            if grouped and gi < len(groups) - 1:
                ws.row_dimensions[r].height = 8
                r += 1
        # zebra: conditional, so it survives a sort; only over data rows
        if t.get('zebra', True):
            first_l = self.letters[self.cols[0]['key']]
            last_l = self.pad or self.letters[self.cols[-1]['key']]
            for a, b in blocks:
                if b > a:
                    ws.conditional_formatting.add(f'{first_l}{a}:{last_l}{b}', FormulaRule(
                        formula=[f'MOD(ROW()-{a},2)=1'], fill=solid(C.MIST)))
        # total_row: false keeps the group subtotals and drops the grand total.
        has_total = (t.get('total_row', t.get('totals', True))
                     and any(c.get('total', 'none') != 'none' for c in self.cols))
        total_row = None
        if has_total:
            if grouped:
                ws.row_dimensions[r].height = 8
                r += 1
            total_row = r
            self.summary_row(r, blocks, t.get('total_label', 'Total'), kind='total')
            r += 1
        # registry: [key] -> data cells, [#key] -> the total
        reg = s.reg
        for c in self.cols:
            k = c['key']
            reg[k] = self.ranges(k, blocks)
            if total_row and c.get('total', 'none') != 'none':
                reg['#' + k] = f'{{s}}${self.letters[k]}${total_row}'
            elif _is_num(c.get('format')):
                reg['#' + k] = f'SUM({reg[k]})'
        for gid, blk, sub_row in self.group_refs:
            for c in self.cols:
                k = c['key']
                reg[f'{k}.{gid}'] = self.ranges(k, [blk])
                if sub_row and c.get('total', 'none') != 'none':
                    reg[f'#{k}.{gid}'] = f'{{s}}${self.letters[k]}${sub_row}'
                elif _is_num(c.get('format')):
                    reg[f'#{k}.{gid}'] = f'SUM({reg[f"{k}.{gid}"]})'
        if self.standalone and t.get('autofilter', not grouped):
            last_data = blocks[-1][1]
            ws.auto_filter.ref = f'B{self.header_row}:{self.letters[self.cols[-1]["key"]]}{last_data}'
        if t.get('note'):
            n = ws.cell(row=r + 1, column=2, value=t['note'])
            n.font = font(9, italic=True, color=C.MUTED)
            n.alignment = Alignment(vertical='top', wrap_text=True)
            last_l = self.pad or self.letters[self.cols[-1]['key']]
            if last_l != 'B':
                ws.merge_cells(f'B{r + 1}:{last_l}{r + 1}')
            span = sum(self.width(c) for c in self.cols)
            ws.row_dimensions[r + 1].height = line_h(text_lines(t['note'], span, 9, indent=0), 9, 4)
            r += 2
        self.end_row = r - 1


# ── gantt ────────────────────────────────────────────────────────────────────
class GanttSheet(Sheet):
    def render(self):
        sh, ws = self.sh, self.ws
        plan = Plan(sh['tasks'])
        scale = sh.get('scale', 'week')
        tasks = [plan.by_id[t] for t in plan.order]
        has_owner = any(t.get('owner') for t in tasks)
        has_pred = any(t['depends_on'] for t in tasks)

        # table columns, then a gutter, then the timeline
        name_w = min(46, max(30, max(len(t['name']) + 2 * plan.depth[t['id']] for t in tasks) + 4))
        spec_cols = [('wbs', 'WBS', 6), ('name', 'Task', name_w)]
        if has_owner:
            owner_w = min(24, max(12, max(len(t.get('owner') or '') for t in tasks) + 3))
            spec_cols.append(('owner', 'Owner', owner_w))
        spec_cols += [('start', 'Start', 11), ('end', 'End', 11), ('days', 'Days', 7), ('pct', 'Done', 8)]
        if has_pred:
            spec_cols.append(('pred', 'After', 10))
        L = {k: get_column_letter(2 + i) for i, (k, _, _) in enumerate(spec_cols)}
        gutter = 2 + len(spec_cols)
        first_tl = gutter + 1

        lo = min(s for s, _ in plan.dates.values())
        hi = max(e for _, e in plan.dates.values())
        if scale == 'week':
            p0 = lo - dt.timedelta(days=lo.weekday())
            n = (hi - p0).days // 7 + 2
            tl_w = 3.6
        elif scale == 'day':
            p0 = lo
            n, d = 1, lo
            while d < hi:
                d = _workday(d, 1); n += 1
            n += 1
            tl_w = 2.9
        else:
            p0 = lo.replace(day=1)
            n = (hi.year - p0.year) * 12 + hi.month - p0.month + 2
            tl_w = 6
        last_tl = first_tl + n - 1
        self.last_col = last_tl
        self.widths([2.5] + [w for _, _, w in spec_cols] + [1.5] + [tl_w] * n + [2.5])
        self.band()
        top = self.heading()
        month_row, hdr = top, top + 1
        first_row = hdr + 1
        rows = {tid: first_row + i for i, tid in enumerate(plan.order)}
        last_row = first_row + len(tasks) - 1
        self.last_row = last_row + 2

        # header
        ws.row_dimensions[month_row].height = 16
        ws.row_dimensions[hdr].height = 22
        for k, label, _ in spec_cols:
            cell = ws[f'{L[k]}{hdr}']
            cell.value = label.upper()
            cell.font = font(8.5, bold=True, color=C.WHITE)
            cell.fill = solid(C.FOREST)
            right = k in ('days', 'pct')
            mid = k in ('start', 'end', 'wbs', 'pred')
            cell.alignment = Alignment(horizontal='right' if right else ('center' if mid else 'left'),
                                       vertical='center', indent=0 if (mid or right) else 1)
        ws.cell(row=hdr, column=gutter).fill = solid(C.FOREST)

        E, F, G, H = L['start'], L['end'], L['days'], L['pct']
        S_rng = f'${E}${first_row}:${E}${last_row}'
        TL0 = get_column_letter(first_tl)
        for i in range(n):
            col = first_tl + i
            cl, prev = get_column_letter(col), get_column_letter(col - 1)
            d = ws.cell(row=hdr, column=col)
            m = ws.cell(row=month_row, column=col)
            if i == 0:
                if scale == 'week':
                    d.value = f'=MIN({S_rng})-WEEKDAY(MIN({S_rng}),3)'
                elif scale == 'day':
                    d.value = f'=MIN({S_rng})'
                else:
                    d.value = f'=DATE(YEAR(MIN({S_rng})),MONTH(MIN({S_rng})),1)'
                m.value = f'={cl}{hdr}'
            else:
                d.value = {'week': f'={prev}{hdr}+7', 'day': f'=WORKDAY({prev}{hdr},1)',
                           'month': f'=EDATE({prev}{hdr},1)'}[scale]
                if scale == 'month':
                    m.value = f'=IF(YEAR({cl}{hdr})<>YEAR({prev}{hdr}),{cl}{hdr},"")'
                else:
                    m.value = f'=IF(MONTH({cl}{hdr})<>MONTH({prev}{hdr}),{cl}{hdr},"")'
            d.number_format = {'week': 'd', 'day': 'd', 'month': 'mmm'}[scale]
            m.number_format = 'yyyy' if scale == 'month' else 'mmm'
            d.font = font(8, bold=True, color=C.WHITE)
            d.fill = solid(C.FOREST)
            d.alignment = Alignment(horizontal='center', vertical='center')
            m.font = font(7 if scale == 'day' else 8.5, bold=True, color=C.FOREST)   # a date cannot overflow
            m.alignment = Alignment(horizontal='left', vertical='bottom')
            m.border = Border(left=side(C.CLOUD)) if i else Border()

        # rows
        thin_bottom = side(C.CLOUD)
        for tid in plan.order:
            t = plan.by_id[tid]
            r = rows[tid]
            phase = plan.is_phase(tid)
            ws.row_dimensions[r].height = 19 if phase else 17
            base = font(10, bold=phase, color=C.FOREST if phase else C.INK_800)
            for k, _, _ in spec_cols:
                c = ws[f'{L[k]}{r}']
                c.font = base
                c.border = Border(bottom=thin_bottom)
                c.alignment = Alignment(vertical='center', indent=1)
                if phase:
                    c.fill = solid(C.MINT_TINT)
            ws.cell(row=r, column=gutter).border = Border(bottom=thin_bottom)
            if phase:
                ws.cell(row=r, column=gutter).fill = solid(C.MINT_TINT)
            ws[f'{L["wbs"]}{r}'] = plan.wbs[tid]
            ws[f'{L["wbs"]}{r}'].alignment = Alignment(horizontal='center', vertical='center')
            ws[f'{L["wbs"]}{r}'].font = font(9, bold=phase, color=C.FOREST if phase else C.MUTED)
            nm = ws[f'{L["name"]}{r}']
            nm.value = t['name']
            nm.alignment = Alignment(vertical='center', indent=1 + 2 * plan.depth[tid], wrap_text=True)
            nlines = text_lines(t['name'], name_w, 10, bold=phase, indent=1 + 2 * plan.depth[tid])
            if has_owner:
                ws[f'{L["owner"]}{r}'] = t.get('owner')
                ws[f'{L["owner"]}{r}'].font = font(9.5, color=C.MUTED)
                ws[f'{L["owner"]}{r}'].alignment = Alignment(vertical='center', indent=1, wrap_text=True)
                nlines = max(nlines, text_lines(t.get('owner'), owner_w, 9.5))
            if nlines > 1:
                grow(ws, r, line_h(nlines, 10, 5))
            if has_pred and t['depends_on']:
                ws[f'{L["pred"]}{r}'] = ', '.join(plan.wbs[d] for d in t['depends_on'])
                ws[f'{L["pred"]}{r}'].font = font(9, color=C.MUTED)
                ws[f'{L["pred"]}{r}'].alignment = Alignment(horizontal='center', vertical='center')
            sc, ec, gc, hc = (ws[f'{x}{r}'] for x in (E, F, G, H))
            if phase:
                kids = [rows[k] for k in plan.children[tid]]
                sc.value = f'=MIN({",".join(f"{E}{k}" for k in kids)})'
                ec.value = f'=MAX({",".join(f"{F}{k}" for k in kids)})'
                num = '+'.join(f'N({G}{k})*N({H}{k})' for k in kids)
                den = '+'.join(f'N({G}{k})' for k in kids)
                hc.value = f'=IFERROR(({num})/({den}),0)'
                gc.value = f'=NETWORKDAYS({E}{r},{F}{r})'
            else:
                if 'start' in t:
                    sc.value = dt.date.fromisoformat(t['start'])
                    sc.font = font(10, color=C.INPUT)
                else:
                    sc.value = f'=WORKDAY(MAX({",".join(f"{F}{rows[d]}" for d in t["depends_on"])}),1)'
                if t.get('milestone'):
                    ec.value = f'={E}{r}'
                    gc.value = 0
                    gc.font = font(10, color=C.MUTED)
                elif 'end' in t:
                    ec.value = dt.date.fromisoformat(t['end'])
                    ec.font = font(10, color=C.INPUT)
                    gc.value = f'=NETWORKDAYS({E}{r},{F}{r})'
                else:
                    gc.value = t['duration_days']
                    gc.font = font(10, color=C.INPUT)
                    ec.value = f'=WORKDAY({E}{r},{G}{r}-1)'
                if not t.get('milestone'):
                    hc.value = t.get('percent', 0)
                    hc.font = font(10, color=C.INPUT)
            for c in (sc, ec):
                c.number_format = 'mmm d'
                c.alignment = Alignment(horizontal='center', vertical='center')
            gc.number_format = '#,##0;-#,##0;"–"'
            hc.number_format = '0%'
            for c in (gc, hc):
                c.alignment = Alignment(horizontal='right', vertical='center')
            if t.get('milestone'):
                hc.value = None
            # timeline cells: light grid, milestone diamonds
            for i in range(n):
                col = first_tl + i
                cell = ws.cell(row=r, column=col)
                cell.border = Border(bottom=thin_bottom)
                if t.get('milestone'):
                    cl = get_column_letter(col)
                    pe = self._period_end(cl, hdr, scale)
                    cell.value = f'=IF(AND(${E}{r}>={cl}${hdr},${E}{r}<={pe}),"{DIAMOND}","")'
                    cell.font = font(11, bold=True, color=C.FOREST)
                    cell.alignment = Alignment(horizontal='center', vertical='center')

        # bars: conditional formats on the date header, per contiguous block of one row type
        kinds = []
        for tid in plan.order:
            t = plan.by_id[tid]
            kinds.append('phase' if plan.is_phase(tid) else 'milestone' if t.get('milestone') else 'task')
        blocks, start = [], 0
        for i in range(1, len(kinds) + 1):
            if i == len(kinds) or kinds[i] != kinds[start]:
                blocks.append((kinds[start], first_row + start, first_row + i - 1))
                start = i
        last_l = get_column_letter(last_tl)
        today = sh.get('today', False)
        for kind, a, b in blocks:
            ref = f'{TL0}{a}:{last_l}{b}'
            pe = self._period_end(TL0, hdr, scale)
            bar = f'${E}{a}<={pe},${F}{a}>={TL0}${hdr}'
            if kind == 'phase':
                ws.conditional_formatting.add(ref, FormulaRule(formula=[f'AND({bar})'], fill=solid(C.FOREST),
                                                               stopIfTrue=True))
            elif kind == 'task':
                done = f'AND({bar},N(${H}{a})>0,{TL0}${hdr}<=${E}{a}+(${F}{a}-${E}{a}+1)*${H}{a}-1)'
                ws.conditional_formatting.add(ref, FormulaRule(formula=[done], fill=solid(C.GREEN),
                                                               stopIfTrue=True))
                ws.conditional_formatting.add(ref, FormulaRule(formula=[f'AND({bar})'], fill=solid(C.JADE),
                                                               stopIfTrue=True))
            if today:
                ws.conditional_formatting.add(ref, FormulaRule(
                    formula=[f'AND(TODAY()>={TL0}${hdr},TODAY()<={pe})'], fill=solid(C.TODAY_BG)))
        if today:
            pe = self._period_end(TL0, hdr, scale).replace(f'{TL0}${hdr}', f'{TL0}{hdr}')
            ws.conditional_formatting.add(f'{TL0}{hdr}:{last_l}{hdr}', FormulaRule(
                formula=[f'AND(TODAY()>={TL0}{hdr},TODAY()<={pe})'], fill=solid(C.AMBER),
                font=Font(color=C.INK, bold=True)))

        # legend under the plan
        lg = last_row + 2
        ws.row_dimensions[lg].height = 16
        items = [(C.FOREST, 'Phase'), (C.GREEN, 'Done'), (C.JADE, 'Planned')]
        col = first_tl
        for hx, label in items:
            sw = ws.cell(row=lg, column=col)
            sw.fill = solid(hx)
            lab = ws.cell(row=lg, column=col + 1, value=label)
            lab.font = font(8.5, color=C.MUTED)
            col += 3
        dm = ws.cell(row=lg, column=col, value=DIAMOND)
        dm.font = font(10, bold=True, color=C.FOREST)
        dm.alignment = Alignment(horizontal='center')
        ws.cell(row=lg, column=col + 1, value='Milestone').font = font(8.5, color=C.MUTED)
        note = ws.cell(row=lg, column=2, value='Blue cells are inputs. Days are working days; '
                                                 'bars and phase dates follow the inputs.')
        note.font = font(8.5, italic=True, color=C.MUTED)
        self.last_row = lg

        dv = DataValidation(type='decimal', operator='between', formula1='0', formula2='1', allow_blank=True)
        dv.error, dv.errorTitle = 'Enter a share between 0% and 100%.', 'Done'
        ws.add_data_validation(dv)
        dv.add(f'{H}{first_row}:{H}{last_row}')

        self.reg['#start'] = f'MIN({{s}}${E}${first_row}:${E}${last_row})'
        self.reg['#end'] = f'MAX({{s}}${F}${first_row}:${F}${last_row})'
        self.reg['start'] = f'{{s}}${E}${first_row}:${E}${last_row}'
        self.reg['end'] = f'{{s}}${F}${first_row}:${F}${last_row}'
        ws.freeze_panes = f'{L["start"]}{first_row}'
        ws.sheet_properties.tabColor = C.FOREST
        self.page(title_rows=f'{month_row}:{hdr}')

    @staticmethod
    def _period_end(cl, hdr, scale):
        return {'week': f'{cl}${hdr}+6', 'day': f'{cl}${hdr}', 'month': f'EOMONTH({cl}${hdr},0)'}[scale]


# ── form ─────────────────────────────────────────────────────────────────────
class FormSheet(Sheet):
    landscape = False

    def render(self):
        sh, ws, book = self.sh, self.ws, self.book
        kind = sh['form']
        items = sh['items']
        used = {k for it in items for k in it}
        cols = [c for c in FORM_COLS[kind] if not c[4] or c[0] in used]
        fixed = sum(c[2] for c in cols if c[2])
        cols = [(k, h, w or max(24, FORM_WIDTH - fixed), f, o, role) for k, h, w, f, o, role in cols]
        n = len(cols)
        Lk = {c[0]: get_column_letter(2 + i) for i, c in enumerate(cols)}
        last = 1 + n
        self.last_col = last
        LN, LN1, LN2 = (get_column_letter(last - i) for i in range(3))
        self.widths([2.5] + [c[2] for c in cols] + [2.5])
        self.band(thin=True)

        # header block: logo left, document title right
        ws.row_dimensions[2].height = 18
        ws.row_dimensions[3].height = 36
        logo = K.LOGO_ON_LIGHT
        if logo and Path(logo).exists():
            img = XLImage(str(logo))
            h = 30
            w = int(round(img.width * h / img.height))
            img.width, img.height = w, h
            img.anchor = OneCellAnchor(_from=AnchorMarker(col=1, colOff=0, row=2, rowOff=pixels_to_EMU(9)),
                                       ext=XDRPositiveSize2D(pixels_to_EMU(w), pixels_to_EMU(h)))
            ws.add_image(img)
        else:
            c = ws['B3']
            c.value = K.BRAND_NAME
            c.font = font(18, color=C.FOREST, name=DISPLAY)
        title = ws[f'{LN}3']
        title.value = sh.get('title', FORM_TITLE[kind])
        title.font = font(24, color=C.FOREST, name=DISPLAY)
        title.alignment = Alignment(horizontal='right', vertical='center')

        # company (left) and details (right)
        r = 5
        left = [(K.BRAND_NAME, True)] + [(ln, False) for ln in (K.ACTIVE.address or [])]
        if K.ACTIVE.website:
            left.append((K.ACTIVE.website, False))
        details = []
        if sh.get('number'):
            details.append((FORM_NUMBER[kind], sh['number'], 'text'))
        for d in sh.get('details', []):
            v = d['value']
            details.append((d['label'], v, d.get('format') or ('date' if isinstance(_as_date(v), dt.date) else 'text')))
        # details labels get at least 14 characters (merged leftwards from LN2); the issuer
        # block takes every column before them
        lab_start = last - 2
        while lab_start > 3 and sum(c[2] for c in cols[lab_start - 2:last - 3]) < 14:
            lab_start -= 1
        left_end = max(2, lab_start - 1)
        left_w = sum(c[2] for c in cols[:left_end - 1])
        for i in range(max(len(left), len(details))):
            ws.row_dimensions[r + i].height = 15
            if i < len(left):
                txt, strong = left[i]
                c = ws[f'B{r + i}']
                c.value = txt
                c.font = font(10 if strong else 9.5, bold=strong, color=C.INK if strong else C.MUTED)
                c.alignment = Alignment(vertical='top', wrap_text=True)
                self.merge_row(r + i, 2, left_end)
                n = text_lines(txt, left_w, 10 if strong else 9.5, bold=strong, indent=0)
                if n > 1:
                    grow(ws, r + i, line_h(n, 10, 3))
            if i < len(details):
                lab, v, f = details[i]
                a = ws.cell(row=r + i, column=lab_start)
                a.value = lab
                a.font = font(9, bold=True, color=C.MUTED)
                a.alignment = Alignment(horizontal='right', vertical='top', indent=1)
                self.merge_row(r + i, lab_start, last - 2)
                ws.merge_cells(f'{LN1}{r + i}:{LN}{r + i}')
                b = ws[f'{LN1}{r + i}']
                b.value = _as_date(v) if f == 'date' else v
                b.number_format = numfmt(f, cur=self.cur)
                b.font = font(10, bold=(i == 0 and bool(sh.get('number'))), color=C.INK)
                b.alignment = Alignment(horizontal='right', vertical='top', wrap_text=True)
                n = text_lines(v if f != 'date' else 'Mmm 00, 0000', cols[-1][2] + cols[-2][2], 10, indent=0)
                if n > 1:
                    grow(ws, r + i, line_h(n, 10, 3))
        r += max(len(left), len(details))
        ws.row_dimensions[r].height = 12
        for ci in range(2, last + 1):
            ws.cell(row=r, column=ci).border = Border(bottom=side(C.CLOUD))
        r += 1
        ws.row_dimensions[r].height = 12
        r += 1

        # parties, spread across the width
        parties = sh.get('parties', [])
        if parties:
            widths_ = [c[2] for c in cols]
            for group in _party_rows(len(parties), widths_):
                depth = max(len(parties[i]['lines']) for i, _ in group)
                ws.row_dimensions[r].height = 16
                for j in range(depth):
                    ws.row_dimensions[r + 1 + j].height = 15
                for i, (a, b) in group:
                    p = parties[i]
                    span_w = sum(widths_[a:b + 1])
                    lab = ws.cell(row=r, column=2 + a, value=p['label'].upper())
                    lab.font = font(8.5, bold=True, color=C.GREEN_600)
                    self.merge_row(r, 2 + a, 2 + b)
                    for j, ln in enumerate(p['lines']):
                        c = ws.cell(row=r + 1 + j, column=2 + a, value=ln)
                        c.font = font(10, bold=(j == 0), color=C.INK if j == 0 else C.INK_800)
                        c.alignment = Alignment(vertical='top', wrap_text=True)
                        self.merge_row(r + 1 + j, 2 + a, 2 + b)
                        n = text_lines(ln, span_w, 10, bold=(j == 0), indent=0)
                        if n > 1:
                            grow(ws, r + 1 + j, line_h(n, 10, 3))
                r += depth + 1
                ws.row_dimensions[r].height = 14
                r += 1

        # line items
        hdr = r
        ws.row_dimensions[hdr].height = 22
        for k, h, w, f, o, role in cols:
            c = ws[f'{Lk[k]}{hdr}']
            c.value = h.upper()
            c.font = font(8.5, bold=True, color=C.WHITE)
            c.fill = solid(C.FOREST)
            c.alignment = Alignment(horizontal='right' if _is_num(f) else 'left', vertical='center',
                                    indent=0 if _is_num(f) else 1)
        PAD = get_column_letter(last + 1)
        ws[f'{PAD}{hdr}'].fill = solid(C.FOREST)
        r += 1
        first = r
        rows = list(items) + [{}] * sh.get('blank_rows', 0)
        text_cols = [(c[0], _inches(c[2]) - 0.16) for c in cols if c[3] == 'text']
        for it in rows:
            n_lines = max([K.est_lines(it[k], w, 10) for k, w in text_cols if it.get(k)] or [1])
            ws.row_dimensions[r].height = 19 if n_lines == 1 else 6 + 13.5 * n_lines
            for k, h, w, f, o, role in cols:
                c = ws[f'{Lk[k]}{r}']
                v = it.get(k)
                if k == 'amount' and role == 'line' and v is None:
                    q, p = f'{Lk["qty"]}{r}', f'{Lk["rate"]}{r}'
                    c.value = f'=IF(OR({q}="",{p}=""),"",{q}*{p})'
                    color = C.INK_800
                else:
                    c.value = cell_value(v, f)
                    color = C.INPUT if (role == 'input' or k == 'amount') and v is not None else C.INK_800
                c.font = font(10, color=color)
                c.number_format = 'General' if f == 'qty' else numfmt(f, cur=self.cur)
                c.alignment = Alignment(horizontal='right' if _is_num(f) else 'left', vertical='center',
                                        indent=0 if _is_num(f) else 1,
                                        wrap_text=(f == 'text'))
                c.border = Border(bottom=side(C.CLOUD))
            ws[f'{PAD}{r}'].border = Border(bottom=side(C.CLOUD))
            r += 1
        last_item = r - 1
        amount_rng = f'{LN}{first}:{LN}{last_item}'

        # totals (right) beside terms and payment (left)
        r += 1
        tot_top = r
        lines = [('Subtotal', None, f'=SUM({amount_rng})', 'subtotal')]
        sub = f'{LN}{tot_top}'
        if sh.get('discount_rate') is not None:
            lines.append(('Discount', ('rate', sh['discount_rate']), f'=-{sub}*{LN1}{{r}}', 'discount'))
        elif sh.get('discount') is not None:
            lines.append(('Discount', None, ('input', -sh['discount']), 'discount'))
        if sh.get('tax_rate') is not None:
            base = f'({sub}+{LN}{tot_top + 1})' if len(lines) > 1 else sub
            lines.append((sh.get('tax_label', 'Tax'), ('rate', sh['tax_rate']), f'={base}*{LN1}{{r}}', 'tax'))
        if sh.get('shipping') is not None:
            lines.append(('Shipping', None, ('input', sh['shipping']), 'shipping'))
        if sh.get('advance') is not None:
            lines.append(('Less advance', None, ('input', -sh['advance']), 'advance'))
        if len(lines) == 1:                         # nothing between subtotal and total: one row
            lines = []
        for i, (label, rate, val, key) in enumerate(lines):
            rr = tot_top + i
            ws.row_dimensions[rr].height = 18
            a = ws[f'{LN2}{rr}']
            a.value = label
            a.font = font(10, color=C.INK_800)
            a.alignment = Alignment(horizontal='right', vertical='center')
            if rate:
                rc = ws[f'{LN1}{rr}']
                rc.value = rate[1]
                rc.number_format = '0.00%' if round(rate[1] * 100, 2) != round(rate[1] * 100) else '0%'
                rc.font = font(10, color=C.INPUT)
                rc.alignment = Alignment(horizontal='right', vertical='center')
            v = ws[f'{LN}{rr}']
            if isinstance(val, tuple):
                v.value = val[1]
                v.font = font(10, color=C.INPUT)
            else:
                v.value = val.format(r=rr)
                v.font = font(10, color=C.INK_800)
            v.number_format = numfmt('currency', cur=self.cur)
            v.alignment = Alignment(horizontal='right', vertical='center')
            self.reg['#' + key] = f'{{s}}${LN}${rr}'
        tr = tot_top + len(lines)
        ws.row_dimensions[tr].height = 26
        for col in (LN2, LN1, LN, PAD):
            ws[f'{col}{tr}'].border = Border(top=side(C.FOREST, 'medium'))
            ws[f'{col}{tr}'].fill = solid(C.MINT)
        lab = ws[f'{LN2}{tr}']
        lab.value = FORM_TOTAL[kind]
        lab.font = font(11, bold=True, color=C.FOREST)
        lab.alignment = Alignment(horizontal='right', vertical='center')
        tv = ws[f'{LN}{tr}']
        tv.value = f'=SUM({LN}{tot_top}:{LN}{tr - 1})' if lines else f'=SUM({amount_rng})'
        tv.font = font(12, bold=True, color=C.FOREST)
        tv.number_format = numfmt('currency', cur=self.cur)
        tv.alignment = Alignment(horizontal='right', vertical='center')
        self.reg['#total'] = f'{{s}}${LN}${tr}'
        self.reg.setdefault('#subtotal', self.reg['#total'])
        self.reg['amount'] = f'{{s}}${LN}${first}:${LN}${last_item}'

        # terms and payment: beside the totals when there is room, else below them
        def text_block(row, label, lines_, end_col):
            c = ws[f'B{row}']
            c.value = label.upper()
            c.font = font(8.5, bold=True, color=C.GREEN_600)
            ws.row_dimensions[row].height = max(ws.row_dimensions[row].height or 15, 15)
            row += 1
            span_w = sum(cc[2] for cc in cols[:end_col - 1])
            for ln in lines_:
                if end_col > 2:
                    ws.merge_cells(start_row=row, start_column=2, end_row=row, end_column=end_col)
                c = ws[f'B{row}']
                c.value = ln
                c.font = font(9.5, color=C.INK_800)
                c.alignment = Alignment(wrap_text=True, vertical='top')
                need = line_h(text_lines(ln, span_w, 9.5, indent=0), 9.5, 3)
                ws.row_dimensions[row].height = max(ws.row_dimensions[row].height or 0, need)
                row += 1
            return row + 1

        blocks = []
        if sh.get('terms'):
            blocks.append(('Terms', [sh['terms']]))
        if sh.get('payment'):
            blocks.append(('Payment', sh['payment']))
        beside_end = last - 3                       # the column before the totals labels
        room = sum(cc[2] for cc in cols[:max(0, beside_end - 1)])
        rr = tot_top
        one_line = all(text_lines(ln, room, 9.5, indent=0) == 1 for _, ls in blocks for ln in ls)
        if room >= 40 and one_line:
            for label, lines_ in blocks:
                rr = text_block(rr, label, lines_, beside_end)
            r = max(tr + 2, rr)
        else:
            r = tr + 2
            blocks_below = blocks
            for label, lines_ in blocks_below:
                r = text_block(r, label, lines_, last)

        notes = sh.get('notes')
        if notes:
            r = text_block(r, 'Notes', [notes] if isinstance(notes, str) else notes, last)

        # signatures
        sigs = sh.get('signatures', FORM_SIGN[kind])
        if sigs:
            ws.row_dimensions[r].height = 30
            r += 1
            # two signature lines a row, split by width with one column left as the gap
            total_w, acc, mid = sum(cc[2] for cc in cols), 0, 2
            for i, cc in enumerate(cols):
                if acc + cc[2] / 2 >= total_w * 0.5:
                    mid = 2 + i
                    break
                acc += cc[2]
            # Two a row when one narrow column can be the gap between them and the halves
            # balance; otherwise one a row, each line across the left 55% of the page.
            ws_ = [cc[2] for cc in cols]
            best = None
            for k in range(1, len(cols) - 1):
                lw, gw, rw = sum(ws_[:k]), ws_[k], sum(ws_[k + 1:])
                if gw <= 18 and abs(lw - rw) <= 0.4 * total_w and (best is None or abs(lw - rw) < best[0]):
                    best = (abs(lw - rw), k)
            if best and len(sigs) > 1:
                k = best[1]
                half, per_row = [(2, 1 + k), (3 + k, last)], 2
            else:
                acc, end = 0, last
                for i, w_ in enumerate(ws_):
                    acc += w_
                    if acc >= total_w * 0.55:
                        end = 2 + i
                        break
                half, per_row = [(2, end)], 1
            for i in range(0, len(sigs), per_row):
                ws.row_dimensions[r].height = 26
                for j, label in enumerate(sigs[i:i + per_row]):
                    a, b = half[j]
                    for ci in range(a, b + 1):
                        ws.cell(row=r, column=ci).border = Border(bottom=side(C.INK_800))
                    lab = ws.cell(row=r + 1, column=a, value=label)
                    lab.font = font(8.5, color=C.MUTED)
                ws.row_dimensions[r + 1].height = 16
                r += 2 if per_row == 1 else 3
                if per_row == 1:
                    ws.row_dimensions[r].height = 18
        self.last_row = r
        ws.sheet_properties.tabColor = C.GREEN
        self.page(landscape=False, fit_height=1, margins=(0.5, 0.45, 0.6))


# ── summary ──────────────────────────────────────────────────────────────────
class SummarySheet(Sheet):
    landscape = False

    def render(self):
        sh, ws, book, sp = self.sh, self.ws, self.book, self.book.spec
        metrics = sh.get('metrics', [])
        per = sh.get('per_row', min(4, max(1, len(metrics))) if metrics else 4)
        tbl = sh.get('table')
        ncols = max(per, len(tbl['columns']) if tbl else 0, 3)
        widths = [21] * ncols
        if tbl:
            for i, c in enumerate(tbl['columns']):
                widths[i] = max(widths[i], c.get('width', _DEFAULT_WIDTH[c.get('format', 'text')]))
        self.last_col = 1 + ncols
        self.widths([2.5] + widths + [2.5])
        self.band()
        r = self.heading(eyebrow=sh.get('eyebrow'))

        if sh.get('meta', True):
            meta = [('Prepared for', sp.get('prepared_for') or sp['client']),
                    ('Prepared by', sp.get('prepared_by') or K.BRAND_NAME),
                    ('Date', long_date(sp['date']))]
            meta_lines = 1
            for i, (k, v) in enumerate(meta):
                col = 2 + i
                if col > self.last_col:
                    break
                a = ws.cell(row=r, column=col, value=k.upper())
                a.font = font(8, bold=True, color=C.MUTED)
                b = ws.cell(row=r + 1, column=col, value=v)
                b.font = font(10, color=C.INK)
                b.alignment = Alignment(vertical='top', wrap_text=True)
                # the last item may run to the sheet's edge
                end = self.last_col if i == len(meta) - 1 or col + 1 > self.last_col else col
                self.merge_row(r + 1, col, end)
                meta_lines = max(meta_lines if i else 1, text_lines(v, self.span_chars(col, end) - 1, 10, indent=0))
            ws.row_dimensions[r].height = 14
            ws.row_dimensions[r + 1].height = line_h(meta_lines, 10, 3)
            r += 2
            ws.row_dimensions[r].height = 14
            r += 1

        for i, m in enumerate(metrics):
            row0 = r + (i // per) * 4
            col = 2 + i % per
            cells = [ws.cell(row=row0 + j, column=col) for j in range(3)]
            for j, c in enumerate(cells):
                c.fill = solid(C.MINT_TINT)
                c.border = Border(left=side(C.GREEN, 'thick'), right=side(C.WHITE, 'thick'))
            lab, val, note = cells
            lab.value = m['label'].upper()
            lab.font = font(8, bold=True, color=C.MUTED)
            lab.alignment = Alignment(horizontal='left', indent=1, vertical='bottom', wrap_text=True)
            v = m['value']
            if isinstance(v, str) and v.startswith('='):
                book.later(val, v, self.name)
            else:
                val.value = cell_value(v, m.get('format'))
            val.number_format = numfmt(m.get('format', 'number' if not isinstance(v, str) or v.startswith('=') else 'text'),
                                       m.get('decimals'), self.cur)
            val.font = font(18, bold=True, color=C.FOREST)
            val.alignment = Alignment(indent=1, vertical='center', horizontal='left')
            note.value = m.get('note')
            note.font = font(8.5, color=C.MUTED)
            note.alignment = Alignment(horizontal='left', indent=1, vertical='top', wrap_text=True)
            ref = f'{{s}}${get_column_letter(col)}${row0 + 1}'
            self.reg['#' + re.sub(r'\W+', '_', m['label'].lower()).strip('_')] = ref
            if m.get('key'):
                self.reg['#' + m['key']] = ref
        if metrics:
            for k in range((len(metrics) + per - 1) // per):
                base = r + k * 4
                row_m = metrics[k * per:(k + 1) * per]
                cw = [self.span_chars(2 + j, 2 + j) for j in range(len(row_m))]
                nl = max(text_lines(m['label'].upper(), w, 8, bold=True) for m, w in zip(row_m, cw))
                nn = max(text_lines(m.get('note'), w, 8.5) for m, w in zip(row_m, cw))
                ws.row_dimensions[base].height = 20 if nl == 1 else line_h(nl, 8, 8)
                ws.row_dimensions[base + 1].height = 30
                ws.row_dimensions[base + 2].height = 18 if nn == 1 else line_h(nn, 8.5, 6)
                ws.row_dimensions[base + 3].height = 12
            r += ((len(metrics) + per - 1) // per) * 4 + 1

        if tbl:
            t = Table(self, tbl, r, standalone=False)
            t.render()
            r = t.end_row + 2

        if sh.get('notes'):
            width_in = _inches(sum(widths)) - 0.3
            for ln in sh['notes']:
                ws.merge_cells(start_row=r, start_column=2, end_row=r, end_column=self.last_col)
                c = ws.cell(row=r, column=2, value=f'•  {ln}')
                c.font = font(9.5, color=C.INK_800)
                c.alignment = Alignment(wrap_text=True, vertical='top')
                ws.row_dimensions[r].height = line_h(text_lines(f'\u2022  {ln}', self.span_chars(2, self.last_col),
                                                                9.5, indent=0), 9.5, 4)
                r += 1
            r += 1

        if sh.get('contents'):
            c = ws.cell(row=r, column=2, value='CONTENTS')
            c.font = font(8.5, bold=True, color=C.GREEN_600)
            r += 1
            for other in sp['sheets']:
                if other['name'] == self.name:
                    continue
                a = ws.cell(row=r, column=2, value=other['name'])
                a.hyperlink = Hyperlink(ref=a.coordinate, location=f'{quote_sheetname(other["name"])}!A1')
                a.font = font(10, bold=True, color=C.LINK, )
                b = ws.cell(row=r, column=3, value=other.get('title', ''))
                b.font = font(9.5, color=C.MUTED)
                b.alignment = Alignment(vertical='center', wrap_text=True)
                self.merge_row(r, 3, self.last_col)
                ws.row_dimensions[r].height = max(17, line_h(text_lines(other.get('title', ''),
                                                                   self.span_chars(3, self.last_col), 9.5), 9.5, 4))
                r += 1
        self.last_row = r
        ws.sheet_properties.tabColor = C.FOREST
        self.page(landscape=False)


# ── build, PDF, recalculation ────────────────────────────────────────────────
def render(spec):
    """An openpyxl Workbook from a loaded spec."""
    return Book(spec).build()


def build(spec_path, *, pdf=True):
    """Spec -> <spec dir>/out/<client> <workbook>.xlsx (+ .pdf). Returns {'xlsx', 'pdf', 'sheets'}."""
    spec = load(spec_path)
    out = Path(spec['_path']).parent / 'out'
    out.mkdir(exist_ok=True)
    xlsx = out / f'{spec["client"]} {spec["workbook"]}.xlsx'
    render(spec).save(str(xlsx))
    res = {'xlsx': xlsx, 'pdf': None, 'sheets': len(spec['sheets'])}
    if pdf:
        res['pdf'] = output.to_pdf(xlsx)
    return res


def recalculate(xlsx, out_dir=None):
    """Open the workbook in LibreOffice, recalculate every formula and save a copy whose
       cached values openpyxl can read (load_workbook(..., data_only=True)). Returns the copy."""
    xlsx = Path(xlsx)
    out_dir = Path(out_dir or tempfile.mkdtemp(prefix='sv-recalc-'))
    out_dir.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as prof:
        subprocess.run([output.soffice(), f'-env:UserInstallation=file://{prof}', '--headless',
                        '--convert-to', 'xlsx:Calc MS Excel 2007 XML', '--outdir', str(out_dir), str(xlsx)],
                       check=True, capture_output=True, timeout=300)
    copy = out_dir / xlsx.name
    if not copy.exists():
        raise RuntimeError(f'LibreOffice did not recalculate {xlsx.name}')
    return copy


def pages(pdf, out_dir, dpi=110):
    """Every PDF page as a PNG (for looking before calling a workbook done)."""
    import pymupdf
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    doc = pymupdf.open(str(pdf))
    paths = []
    for i in range(len(doc)):
        p = out_dir / f'{Path(pdf).stem}-p{i + 1}.png'
        doc[i].get_pixmap(dpi=dpi).save(str(p))
        paths.append(p)
    return paths


if __name__ == '__main__':
    try:
        r = build(sys.argv[1])
    except SpecError as e:
        sys.exit(f'sv: {e}')
    print(f'  {r["sheets"]} sheets')
    for k in ('xlsx', 'pdf'):
        print(f'  {k:<6}{r[k]}')
