"""Workflow diagrams on a canvas, not a slide.

A diagram spec (YAML) is laid out once, then drawn twice from the same geometry:

* SVG, printed to PDF and PNG by headless Chrome, in brand type, colors and icons;
* a .drawio file (diagrams.net), the same shapes at the same coordinates with real
  connectors, so anyone can open it and keep editing like Lucidchart.

Mermaid cannot draw swimlanes, and auto-layout tools reorder steps; a business process
reads left to right in the order it happens, so the layout here is ours: one column per
step, one row per lane, joint steps spanning lanes, optional detours below the main row.

Spec:

    diagram: Quote Workflow          # the file name
    client: Acme Labs
    date: 2026-10-04
    title: From discovery call to the customer in three days.
    subtitle: How an Acme quote becomes an approved proposal.
    clock: 3-day clock               # label on the phase row
    lanes:  [{key, name, note}]
    steps:  [{id, num, lane | lanes: [a, b], title, text, kind, target, icon, branch}]
            kind: task | call | optional | approval | decision | end
            branch: true puts an optional detour below the main row, with a skip line
    loops:  [{from, to, label}]      # dashed amber return paths
    phases: [{label, from, to}]      # bands over the step columns (Day 1, Day 2 ...)
    notes:  [{title, text}]          # panels under the lanes
"""
import base64
import datetime as dt
import html
import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from xml.sax.saxutils import escape as xesc

import yaml

from . import kit
from .spec import _StrictLoader, SpecError

PX = 96                                   # canvas units are CSS pixels
HEX = lambda c: '#' + str(c)
C = dict(forest=HEX(kit.FOREST), forest9=HEX(kit.FOREST_900), green=HEX(kit.GREEN), green6=HEX(kit.GREEN_600),
         jade=HEX(kit.GREEN_300), mint=HEX(kit.MINT), mint_t=HEX(kit.MINT_TINT), mist=HEX(kit.MIST),
         cloud=HEX(kit.CLOUD), ink=HEX(kit.INK), ink8=HEX(kit.INK_800), muted=HEX(kit.INK_MUTED),
         white='#FFFFFF', amber=HEX(kit.AMBER), on_forest=HEX(kit.ON_FOREST), slate=HEX(kit.SLATE))
UI, DISPLAY = kit.UI, kit.DISPLAY


def _aspect(path):
    from PIL import Image
    im = Image.open(path)
    return min(im.height / im.width, 0.6)


def _tint(hx, t):
    """hx mixed toward white by t (0..1): the pale lane and card fills follow the brand."""
    r, g, b = (int(hx[i:i + 2], 16) for i in (1, 3, 5))
    return '#%02X%02X%02X' % tuple(round(c + (255 - c) * t) for c in (r, g, b))


C.update(slate_t1=_tint(C['slate'], 0.93), slate_t2=_tint(C['slate'], 0.88), amber_t=_tint(C['amber'], 0.84),
         shadow=C['ink'])
KIND_ICON = {'call': 'groups', 'approval': 'verified', 'decision': 'help', 'end': 'send', 'system': 'sync'}


# ── measuring ────────────────────────────────────────────────────────────────
def text_w(txt, size, bold=False, display=False):
    return kit.text_w_in(txt, size * 0.75, font=DISPLAY if display else UI, bold=bold) * PX


def wrap(txt, width, size, bold=False, display=False):
    lines, cur = [], ''
    for word in str(txt).split():
        trial = f'{cur} {word}'.strip()
        if cur and text_w(trial, size, bold, display) > width:
            lines.append(cur); cur = word
        else:
            cur = trial
    return lines + ([cur] if cur else [])


# ── primitives shared by both renderers ──────────────────────────────────────
class Box(dict):
    """A shape with optional text runs: [(text, size, bold, color, display)]."""


class Img(dict):
    pass


class Wire(dict):
    pass


def load(path):
    p = Path(path)
    try:
        spec = yaml.load(p.read_text(), Loader=_StrictLoader)
    except yaml.YAMLError as e:
        raise SpecError(f'{p.name}: not valid YAML: {e}') from None
    for key in ('diagram', 'client', 'lanes', 'steps'):
        if key not in spec:
            raise SpecError(f'{p.name}: missing "{key}"')
    keys = [ln['key'] for ln in spec['lanes']]
    ids = set()
    for st in spec['steps']:
        lanes = st.get('lanes') or [st.get('lane')]
        bad = [k for k in lanes if k not in keys]
        if bad:
            raise SpecError(f'step {st.get("id")}: unknown lane {bad}; lanes are {keys}')
        if st['id'] in ids:
            raise SpecError(f'step id {st["id"]} is used twice')
        ids.add(st['id'])
        st['_lanes'] = sorted(keys.index(k) for k in lanes)
    for ref in [*((t['id'] if isinstance(t, dict) else t) for st in spec['steps'] for t in st.get('to', [])),
                *(l for lp in spec.get('loops', []) for l in (lp['from'], lp['to'])),
                *(l for ph in spec.get('phases', []) for l in (ph['from'], ph['to']))]:
        if ref not in ids:
            raise SpecError(f'loop or phase points at step {ref}, which does not exist')
    spec.setdefault('date', dt.date.today().isoformat())
    spec['_path'] = str(p)
    return spec


# ── layout ───────────────────────────────────────────────────────────────────
def layout(spec):
    """Columns left to right, one per step (start markers and parallel steps share a column),
    lanes top to bottom, each lane only as tall as its own steps need. Wire rules: same row =
    straight; another lane = out the right side, turn in the gap, into the left side; an
    optional step sits inline with the main line arcing over it; skip = up through the corridor
    above the lanes; loop = dashed through the gap between lanes; parallel = dashed slate."""
    M, LABEL_W, BOX_W, GAP, START_W = 40, 172, 196, 50, 140
    HEAD, TSZ, BSZ, PAD, OVER = 38, 15, 13, 14, 26
    inner = BOX_W - 26
    lanes, steps = spec['lanes'], spec['steps']

    # Columns: every step gets one, unless it shares the previous column.
    cols = []
    for s in steps:
        if s.get('same_column') and cols:
            cols[-1].append(s)
        else:
            cols.append([s])
    col_of = {s['id']: i for i, c in enumerate(cols) for s in c}
    col_w = [(START_W if all(s.get('kind') == 'start' for s in c) else BOX_W) + GAP for c in cols]
    grid_x = M + LABEL_W
    col_x = [grid_x + sum(col_w[:i]) for i in range(len(cols))]
    W = M * 2 + LABEL_W + sum(col_w)
    out = []
    EV_H = 26

    def need(st):
        if st.get('kind') in ('start', 'end'):
            return 64
        h = HEAD + len(wrap(st['title'], inner, TSZ, True)) * TSZ * 1.22
        if st.get('text'):
            h += 3 + len(wrap(st['text'], inner, BSZ)) * BSZ * 1.3
        if st.get('branch') or st.get('kind') == 'optional':
            h += 22
        if st.get('events'):
            h += 8 + len(st['events']) * EV_H
        return h + 12

    # Row height per lane: the tallest single-lane step in it (joint steps stretch to fit).
    row_h = []
    for i in range(len(lanes)):
        own = [need(s) for s in steps if s['_lanes'] == [i]]
        row_h.append(max([84] + own))
    for s in steps:                             # a joint step must fit across its lanes
        ls = s['_lanes']
        if len(ls) > 1:
            span = sum(row_h[l] + 2 * PAD for l in ls) - 2 * PAD
            if need(s) > span:
                row_h[ls[-1]] += need(s) - span

    # Which flow edges jump over an optional step (they need headroom in their lane).
    flow = [s for s in steps if s.get('kind') != 'start' and not s.get('parallel') and not s.get('branch')]
    over_lanes = set()
    for a, b in zip(flow, flow[1:]):
        between = steps[steps.index(a) + 1:steps.index(b)]
        if any(s.get('branch') and s['_lanes'][0] == a['_lanes'][0] for s in between):
            over_lanes.add(a['_lanes'][0])
    top_pad = [PAD + (OVER if i in over_lanes else 0) for i in range(len(lanes))]

    # Header.
    y = M
    tw_ = W - 2 * M - 220
    title = spec.get('title', spec['diagram'])
    title_lines = wrap(title, tw_, 28, display=True)
    out.append(Box(id='title', x=M, y=y, w=tw_, h=len(title_lines) * 35, fill=None, stroke=None,
                   runs=[(title, 28, False, C['forest'], True)], pad=0, align='left', role='text'))
    y += len(title_lines) * 35 + 4
    if spec.get('subtitle'):
        out.append(Box(id='subtitle', x=M, y=y, w=W - 2 * M, h=20, fill=None, stroke=None,
                       runs=[(spec['subtitle'], 14, False, C['muted'], False)], pad=0, align='left', role='text'))
        y += 26
    out.append(Img(id='logo', x=W - M - 168, y=M + 2, w=168, h=168 * _aspect(kit.LOGO_ON_LIGHT), path=str(kit.LOGO_ON_LIGHT)))
    y += 14

    # Phase band.
    band_h = 40 if (spec.get('phases') or spec.get('clock')) else 0
    if band_h:
        out.append(Box(id='band', x=M, y=y, w=W - 2 * M, h=band_h - 6, fill=C['forest'], stroke=None, r=6))
        if spec.get('clock'):
            out.append(Box(id='clock', x=M + 14, y=y, w=LABEL_W - 20, h=band_h - 6, fill=None, stroke=None,
                           runs=[(spec['clock'], 13, True, C['jade'], False)], pad=0, align='left', valign='middle', role='text'))
        for i, ph in enumerate(spec.get('phases', [])):
            x1 = col_x[col_of[ph['from']]]
            x2 = col_x[col_of[ph['to']]] + col_w[col_of[ph['to']]]
            out.append(Box(id=f'phase{i}', x=x1 + 4, y=y + 5, w=x2 - x1 - 8, h=band_h - 16, fill=C['forest9'],
                           stroke=C['green6'], r=6, runs=[(ph['label'].upper(), 12, True, C['white'], False)],
                           pad=0, align='center', valign='middle', spacing=2))
        y += band_h

    # Corridor for skip paths, between the band and the first lane.
    skips = [(s, t) for s in steps for t in s.get('to', []) if isinstance(t, dict) and t.get('route') == 'top']
    corridor = 36 if skips else 0
    corr_y = y + corridor / 2
    y += corridor

    # Lanes.
    lane_y, lane_h = [], []
    for i, ln in enumerate(lanes):
        h = top_pad[i] + row_h[i] + PAD
        lane_y.append(y); lane_h.append(h)
        sysl = ln.get('system')
        out.append(Box(id=f'lane{i}', x=M, y=y, w=W - 2 * M, h=h,
                       fill=C['slate_t1'] if sysl else (C['mist'] if i % 2 == 0 else C['white']),
                       stroke=C['cloud'], dash=bool(sysl)))
        runs = [(ln['name'], 15.5, True, C['slate'] if sysl else C['forest'], False)]
        if ln.get('note'):
            runs.append((ln['note'], 12.5, False, C['muted'], False))
        out.append(Box(id=f'lanelabel{i}', x=M, y=y, w=LABEL_W - 10, h=h, fill=C['slate_t2'] if sysl else C['mint_t'],
                       stroke=C['cloud'], runs=runs, pad=16, align='left', valign='middle',
                       accent_left=C['slate'] if sysl else C['green']))
        y += h
    lanes_bottom = y

    # Step geometry.
    geo = {}
    for st in steps:
        ls = st['_lanes']
        c = col_of[st['id']]
        w = START_W if st.get('kind') == 'start' else BOX_W
        x = col_x[c] + (col_w[c] - w) / 2
        top = lane_y[ls[0]] + top_pad[ls[0]]
        h = lane_y[ls[-1]] + top_pad[ls[-1]] + row_h[ls[-1]] - top
        if st.get('kind') in ('start', 'end'):
            ph = 64
            top, h = top + (row_h[ls[0]] - ph) / 2, ph
        geo[st['id']] = (x, top, w, h)

    def row_y(st):
        g = geo[st['id']]
        if st.get('kind') in ('start', 'end') or len(st['_lanes']) == 1:
            return g[1] + g[3] / 2
        return g[1] + row_h[st['_lanes'][0]] / 2

    # Edges.
    by_id = {s['id']: s for s in steps}
    edges = []
    for a, b in zip(flow, flow[1:]):
        if a.get('to'):
            continue
        between = steps[steps.index(a) + 1:steps.index(b)]
        opt = [s for s in between if s.get('branch')]
        edges.append((a, b, {'over': any(s['_lanes'][0] == a['_lanes'][0] for s in opt)}))
        for s in opt:
            edges += [(a, s, {'dash': True}), (s, b, {'dash': True})]
    for s in steps:
        for t in s.get('to', []):
            o = t if isinstance(t, dict) else {'id': t}
            edges.append((s, by_id[o['id']], o))
    for st in steps:
        if st.get('parallel'):
            sib = next(s for s in steps if col_of[s['id']] == col_of[st['id']] and not s.get('parallel'))
            edges.append((sib, st, {'sync': True, 'label': st.get('sync_label')}))

    for a, b, o in edges:
        ga, gb = geo[a['id']], geo[b['id']]
        label = o.get('label')
        if o.get('sync'):
            sx = ga[0] + ga[2] / 2
            pts = [(sx, ga[1] + ga[3]), (sx, gb[1])] if gb[1] > ga[1] else [(sx, ga[1]), (sx, gb[1] + gb[3])]
            out.append(Wire(pts=pts, color=C['slate'], dash=True, width=2, src=a['id'], dst=b['id'],
                            label=label, label_color=C['slate']))
            continue
        if o.get('route') == 'top':
            sx, ex = ga[0] + ga[2] / 2, gb[0] + min(gb[2] / 2, 44)
            pts = [(sx, ga[1]), (sx, corr_y), (ex, corr_y), (ex, gb[1])]
            out.append(Wire(pts=pts, color=C['green6'], dash=True, width=2, src=a['id'], dst=b['id'],
                            label=label, label_at=((sx + ex) / 2, corr_y), label_color=C['green6']))
            continue
        if o.get('over'):                      # main line arcs over the optional step
            oy = lane_y[a['_lanes'][0]] + OVER / 2 + 2
            sx, ex = ga[0] + ga[2] * 0.45, gb[0] + gb[2] * 0.45   # clear of the audience tags on the right corners
            pts = [(sx, ga[1]), (sx, oy), (ex, oy), (ex, gb[1])]
            out.append(Wire(pts=pts, color=C['green6'], width=2, src=a['id'], dst=b['id'], label=label))
            continue
        # An optional step in another lane: fork out of the top (or bottom) of the step before it and
        # land on the top (or bottom) of the step after it, so the main line keeps the side doors.
        if (b.get('branch') and b['_lanes'][0] != a['_lanes'][0]) or (a.get('branch') and a['_lanes'][0] != b['_lanes'][0]):
            if b.get('branch'):
                fx = ga[0] + ga[2] * 0.45
                up = gb[1] < ga[1]
                fy = ga[1] if up else ga[1] + ga[3]
                if fx < gb[0] - 12:
                    pts = [(fx, fy), (fx, gb[1] + gb[3] / 2), (gb[0], gb[1] + gb[3] / 2)]
                    out.append(Wire(pts=pts, color=C['green6'], dash=True, width=2, src=a['id'], dst=b['id']))
                    continue
            else:
                tx = gb[0] + gb[2] * 0.45
                down = gb[1] > ga[1]
                ty = gb[1] if down else gb[1] + gb[3]
                if tx > ga[0] + ga[2] + 12:
                    pts = [(ga[0] + ga[2], ga[1] + ga[3] / 2), (tx, ga[1] + ga[3] / 2), (tx, ty)]
                    out.append(Wire(pts=pts, color=C['green6'], dash=True, width=2, src=a['id'], dst=b['id']))
                    continue
        single = lambda s: len(s['_lanes']) == 1 or s.get('kind') in ('start', 'end')
        inside = lambda g, yy: g[1] + 10 <= yy <= g[1] + g[3] - 10
        ya = row_y(a) if single(a) else (row_y(b) if single(b) and inside(ga, row_y(b)) else row_y(a))
        yb = row_y(b) if single(b) else (ya if inside(gb, ya) else row_y(b))
        sx, ex = ga[0] + ga[2], gb[0]
        mx = sx + (ex - sx) / 2
        pts = [(sx, ya), (ex, yb)] if abs(ya - yb) < 1 else [(sx, ya), (mx, ya), (mx, yb), (ex, yb)]
        out.append(Wire(pts=pts, color=C['green6'], dash=bool(o.get('dash')), width=2, src=a['id'], dst=b['id'],
                        label=label))
    for lp in spec.get('loops', []):
        ga, gb = geo[lp['from']], geo[lp['to']]
        fx, tx = ga[0] + ga[2] * 0.45, gb[0] + gb[2] * 0.45
        if gb[1] < ga[1]:
            gy = (gb[1] + gb[3] + ga[1]) / 2
            pts = [(fx, ga[1]), (fx, gy), (tx, gy), (tx, gb[1] + gb[3])]
        else:
            gy = ga[1] + ga[3] + PAD / 2
            pts = [(fx, ga[1] + ga[3]), (fx, gy), (tx, gy), (tx, gb[1])]
        out.append(Wire(pts=pts, color=C['amber'], dash=True, width=2, src=lp['from'], dst=lp['to'],
                        label=lp.get('label'), label_at=((fx + tx) / 2, gy), label_color=C['amber']))

    # Steps.
    for st in steps:
        x, top, w, h = geo[st['id']]
        kind = st.get('kind', 'task')
        if kind in ('end', 'start'):
            dark = kind == 'end'
            runs = [(st['title'], 14.5, True, C['white'] if dark else C['forest'], False)]
            if st.get('text'):
                runs.append((st['text'], 12, False, C['jade'] if dark else C['ink8'], False))
            out.append(Box(id=f's{st["id"]}', x=x, y=top, w=w, h=h, fill=C['forest'] if dark else C['mint'],
                           stroke=None if dark else C['green6'], sw=1.5, r=h / 2, runs=runs, pad=12,
                           align='center', valign='middle', step=st['id']))
            continue
        approval = kind in ('approval', 'decision')
        system = kind == 'system'
        optional = kind == 'optional' or st.get('branch')
        runs = [(st['title'], TSZ, True, C['slate'] if system else C['forest'], False)]
        if st.get('text'):
            runs.append((st['text'], BSZ, False, C['ink8'], False))
        out.append(Box(id=f's{st["id"]}', x=x, y=top, w=w, h=h, fill=C['white'],
                       stroke=C['amber'] if approval else (C['green6'] if optional else (C['slate'] if system else C['cloud'])),
                       sw=1.5, dash=optional or system, r=9, runs=runs, pad=13, pad_top=HEAD, align='left',
                       accent=None if (optional or system) else (C['amber'] if approval else C['green']),
                       shadow=not (optional or system), step=st['id']))
        hx = x + 13
        if st.get('num') is not None:
            nw = max(22, text_w(str(st['num']), 11, True) + 12)
            out.append(Box(id=f'n{st["id"]}', x=hx, y=top + 11, w=nw, h=22, fill=C['forest'], stroke=None, r=11,
                           runs=[(str(st['num']), 11, True, C['white'], False)], pad=0, align='center', valign='middle'))
            hx += nw + 6
        if st.get('target'):
            cw = text_w(st['target'], 10.5, True) + 14
            out.append(Box(id=f't{st["id"]}', x=hx, y=top + 12, w=cw, h=20, fill=C['mint'], stroke=None, r=10,
                           runs=[(st['target'], 10.5, True, C['forest'], False)], pad=0, align='center', valign='middle'))
            hx += cw + 5
        if st.get('audience'):
            ext = st['audience'] == 'external'
            label = 'External' if ext else 'Internal'
            cw = text_w(label, 10.5, True) + 14
            out.append(Box(id=f'a{st["id"]}', x=hx, y=top + 12, w=cw, h=20, fill=C['white'],
                           stroke=C['green6'] if ext else C['cloud'], sw=1.25, r=10,
                           runs=[(label, 10.5, True, C['forest'] if ext else C['muted'], False)], pad=0,
                           align='center', valign='middle'))
        if optional:
            out.append(Box(id=f'o{st["id"]}', x=x + 13, y=top + h - 26, w=90, h=16, fill=None, stroke=None,
                           runs=[('OPTIONAL', 10, True, C['green6'], False)], pad=0, align='left', valign='middle',
                           spacing=1.5, role='text'))
        elif system:
            ic = st.get('icon') or KIND_ICON.get(kind)
            if ic:
                out.append(Img(id=f'i{st["id"]}', x=x + w - 34, y=top + 10, w=23, h=23,
                               path=str(kit.icon_png(ic, color=kit.SLATE, px=128))))

    def text_bottom(st):
        x, top, w, h = geo[st['id']]
        yy = top + HEAD + len(wrap(st['title'], inner, TSZ, True)) * TSZ * 1.22
        if st.get('text'):
            yy += 3 + len(wrap(st['text'], inner, BSZ)) * BSZ * 1.3
        return yy

    # Callouts: a note bubble in the lane above the step (below if it is the top lane).
    for st in steps:
        if not st.get('callout'):
            continue
        x, top, w, h = geo[st['id']]
        li = st['_lanes'][0]
        cw = w + 30
        lines = wrap(st['callout'], cw - 26, 12.5, True)
        ch = 14 + len(lines) * 12.5 * 1.3 + 12
        cx = x + (w - cw) / 2
        lx = x + w * 0.3                       # left of centre: clear of any line arcing over the step
        if li > 0:
            cy = lane_y[li - 1] + (lane_h[li - 1] - ch) / 2
            lead = [(lx, cy + ch), (lx, top)]
        else:
            cy = top + h + 20
            lead = [(lx, top + h), (lx, cy)]
        out.append(Box(id=f'c{st["id"]}', x=cx, y=cy, w=cw, h=ch, fill=C['slate_t2'], stroke=C['slate'], sw=1.25, r=8,
                       runs=[(st['callout'], 12.5, True, C['slate'], False)], pad=13, align='left', valign='middle'))
        out.append(Wire(pts=lead, color=C['slate'], dash=True, width=1.5, src=None, dst=None, plain=True))

    # System events: what the system or the CRM records at this step, as chips.
    for st in steps:
        evs = st.get('events') or []
        if not evs:
            continue
        x, top, w, h = geo[st['id']]
        if st.get('kind') in ('start', 'end'):
            ey = top + h + 8
        else:
            ey = text_bottom(st) + 8
        for j, ev in enumerate(evs):
            ev = ev if isinstance(ev, dict) else {'label': ev}
            crm = ev.get('kind') == 'crm'
            cw = min(w - 20, text_w(ev['label'], 11, True) + 20)
            ex = x + (w - cw) / 2 if st.get('kind') in ('start', 'end') else x + 12
            out.append(Box(id=f'ev{st["id"]}_{j}', x=ex, y=ey + j * EV_H, w=cw, h=EV_H - 6,
                           fill=C['amber_t'] if crm else C['slate_t2'], stroke=C['amber'] if crm else C['slate'], sw=1,
                           r=4, runs=[(ev['label'], 11, True, C['amber'] if crm else C['slate'], False)], pad=0,
                           align='center', valign='middle'))

    _place_labels(out)

    # Notes and footer.
    y = lanes_bottom + 18
    notes = spec.get('notes', [])
    if notes:
        nw = (W - 2 * M - 16 * (len(notes) - 1)) / len(notes)
        nh = max(14 + len(wrap(nt['title'], nw - 32, 14, True)) * 18 + 4 +
                 len(wrap(nt.get('text', ''), nw - 32, 13)) * 13 * 1.35 + 14 for nt in notes)
        for i, nt in enumerate(notes):
            runs = [(nt['title'], 14, True, C['forest'], False)]
            if nt.get('text'):
                runs.append((nt['text'], 13, False, C['ink8'], False))
            out.append(Box(id=f'note{i}', x=M + i * (nw + 16), y=y, w=nw, h=nh, fill=C['mint_t'], stroke=C['mint'],
                           r=8, runs=runs, pad=16, align='left', accent_left=C['green']))
        y += nh + 14
    out.append(Box(id='footer', x=M, y=y, w=W - 2 * M, h=16, fill=None, stroke=None,
                   runs=[(f'{kit.BRAND_SHORT} · {spec["client"]} · {spec["date"]}', 11, False, C['muted'], False)],
                   pad=0, align='left', role='text'))
    H = y + 16 + M
    return W, H, out


def _place_labels(items):
    """Slide each wire label along its own horizontal runs to the first spot that touches no
    other wire and no box, so a label never sits on a crossing line."""
    wires = [w for w in items if isinstance(w, Wire)]
    boxes = [b for b in items if isinstance(b, Box) and b.get('step') is not None]
    segs = lambda w: list(zip(w['pts'], w['pts'][1:]))
    def hits(rect, skip):
        x0, y0, x1, y1 = rect
        for w in wires:
            if w is skip:
                continue
            for (ax, ay), (bx, by) in segs(w):
                if min(ax, bx) - 3 <= x1 and max(ax, bx) + 3 >= x0 and min(ay, by) - 3 <= y1 and max(ay, by) + 3 >= y0:
                    return True
        for b in boxes:
            if b['x'] <= x1 and b['x'] + b['w'] >= x0 and b['y'] <= y1 and b['y'] + b['h'] >= y0:
                return True
        return False
    for w in wires:
        if not w.get('label'):
            continue
        lw = text_w(w['label'], 12.5, True) + 18
        total = sum(abs(bx - ax) + abs(by - ay) for (ax, ay), (bx, by) in segs(w)) or 1
        runs, walked = [], 0
        for (ax, ay), (bx, by) in segs(w):
            ln = abs(bx - ax) + abs(by - ay)
            if abs(ay - by) < 1 and abs(bx - ax) > 1:
                runs.append((ax, bx, ay, walked, ln))
            walked += ln
        runs.sort(key=lambda r: -abs(r[1] - r[0]))
        best = None
        for ax, bx, yy, start, ln in runs:
            lo, hi = min(ax, bx), max(ax, bx)
            cands = [lo + (hi - lo) * f for f in (0.5, 0.35, 0.65, 0.2, 0.8)]
            # flush beside any line that crosses this run, and anchored to either end
            for o in wires:
                if o is w:
                    continue
                for (px, py), (qx, qy) in segs(o):
                    if abs(px - qx) < 1 and lo < px < hi and min(py, qy) <= yy <= max(py, qy):
                        cands += [px + 10 + lw / 2, px - 10 - lw / 2]
            cands += [lo + lw / 2, hi - lw / 2, hi + 6 - lw / 2 + lw / 4]
            for cx in cands:
                rect = (cx - lw / 2, yy - 12, cx + lw / 2, yy + 12)
                if not hits(rect, w):
                    f = min(1, max(0, (cx - ax) / (bx - ax))) if bx != ax else 0.5
                    best = (cx, yy, (start + ln * f) / total)
                    break
            if best:
                break
        if not best and runs:                  # nothing clear: centre of the longest run
            ax, bx, yy, start, ln = runs[0]
            best = ((ax + bx) / 2, yy, (start + ln / 2) / total)
        if best:
            w['label_at'], w['label_t'] = (best[0], best[1]), best[2]

# ── SVG ──────────────────────────────────────────────────────────────────────
def _data_uri(path):
    return 'data:image/png;base64,' + base64.b64encode(Path(path).read_bytes()).decode()


def _text_svg(b):
    """Wrap each run inside the box and stack the lines; top or middle aligned."""
    pad, pt = b.get('pad', 0), b.get('pad_top', b.get('pad', 0))
    width = b['w'] - pad * 2
    blocks = []
    for (txt, size, bold, color, display) in b.get('runs', []):
        ls = wrap(txt, width, size, bold, display) if b.get('role') != 'nowrap' else [txt]
        blocks.append((ls, size, bold, color, display))
    lh = lambda size, display: size * (1.25 if display or size >= 16 else 1.3)
    total = sum(len(ls) * lh(sz, d) for ls, sz, _, _, d in blocks) + 4 * (len(blocks) - 1)
    y = b['y'] + pt if b.get('valign', 'top') == 'top' else b['y'] + (b['h'] - total) / 2
    anchor = {'left': 'start', 'center': 'middle', 'right': 'end'}[b.get('align', 'left')]
    x = {'left': b['x'] + pad, 'center': b['x'] + b['w'] / 2, 'right': b['x'] + b['w'] - pad}[b.get('align', 'left')]
    parts = []
    for ls, size, bold, color, display in blocks:
        fam = f"'{DISPLAY}', Georgia, serif" if display else f"'{UI}', Helvetica, Arial, sans-serif"
        sp = f' letter-spacing="{b["spacing"]}"' if b.get('spacing') else ''
        for line in ls:
            y += lh(size, display)
            parts.append(f'<text x="{x:.1f}" y="{y - size * 0.28:.1f}" font-family="{fam}" font-size="{size}" '
                         f'font-weight="{700 if bold else 400}" fill="{color}" text-anchor="{anchor}"{sp}>'
                         f'{html.escape(line)}</text>')
        y += 4
    return parts


def to_svg(W, H, items):
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W:.0f}" height="{H:.0f}" viewBox="0 0 {W:.0f} {H:.0f}">',
         '<defs>',
         f'<marker id="ag" viewBox="0 0 12 10" refX="11" refY="5" markerUnits="userSpaceOnUse" markerWidth="14" '
         f'markerHeight="12" orient="auto"><path d="M0,0 L12,5 L0,10 z" fill="{C["green6"]}"/></marker>',
         f'<marker id="aa" viewBox="0 0 12 10" refX="11" refY="5" markerUnits="userSpaceOnUse" markerWidth="14" '
         f'markerHeight="12" orient="auto"><path d="M0,0 L12,5 L0,10 z" fill="{C["amber"]}"/></marker>',
         f'<marker id="as" viewBox="0 0 12 10" refX="11" refY="5" markerUnits="userSpaceOnUse" markerWidth="14" '
         f'markerHeight="12" orient="auto"><path d="M0,0 L12,5 L0,10 z" fill="{C["slate"]}"/></marker>',
         '<filter id="sh" x="-10%" y="-10%" width="120%" height="130%"><feDropShadow dx="0" dy="1.5" stdDeviation="2" '
         f'flood-color="{C["shadow"]}" flood-opacity="0.10"/></filter>',
         '</defs>', f'<rect width="{W:.0f}" height="{H:.0f}" fill="#FFFFFF"/>']
    wires = [i for i in items if isinstance(i, Wire)]
    boxes = [i for i in items if not isinstance(i, Wire)]
    # Backgrounds first (lanes, band), then wires, then steps and labels on top.
    back = [b for b in boxes if isinstance(b, Box) and (b['id'].startswith(('lane', 'band')))]
    front = [b for b in boxes if b not in back]
    def draw_box(b):
        if b.get('fill') or b.get('stroke'):
            dash = ' stroke-dasharray="6 4"' if b.get('dash') else ''
            flt = ' filter="url(#sh)"' if b.get('shadow') else ''
            o.append(f'<rect x="{b["x"]:.1f}" y="{b["y"]:.1f}" width="{b["w"]:.1f}" height="{b["h"]:.1f}" '
                     f'rx="{b.get("r", 0):.1f}" fill="{b.get("fill") or "none"}" stroke="{b.get("stroke") or "none"}" '
                     f'stroke-width="{b.get("sw", 1)}"{dash}{flt}/>')
        if b.get('accent'):
            r = b.get('r', 0)
            o.append(f'<rect x="{b["x"] + r * 0.6:.1f}" y="{b["y"]:.1f}" width="{b["w"] - r * 1.2:.1f}" height="5" '
                     f'fill="{b["accent"]}"/>')
        if b.get('accent_left'):
            o.append(f'<rect x="{b["x"]:.1f}" y="{b["y"]:.1f}" width="5" height="{b["h"]:.1f}" fill="{b["accent_left"]}"/>')
        o.extend(_text_svg(b))
    for b in back:
        draw_box(b)
    for b in front:                        # boxes, then wires on top so no arrowhead is ever clipped
        if isinstance(b, Img):
            o.append(f'<image x="{b["x"]:.1f}" y="{b["y"]:.1f}" width="{b["w"]:.1f}" height="{b["h"]:.1f}" '
                     f'href="{_data_uri(b["path"])}" preserveAspectRatio="xMidYMid meet"/>')
        else:
            draw_box(b)
    for w in wires:
        d = 'M' + ' L'.join(f'{x:.1f},{y:.1f}' for x, y in w['pts'])
        dash = ' stroke-dasharray="8 5"' if w.get('dash') else ''
        mk = {C['amber']: 'aa', C['slate']: 'as'}.get(w['color'], 'ag')
        end = '' if w.get('plain') else f' marker-end="url(#{mk})"'
        o.append(f'<path d="{d}" fill="none" stroke="{w["color"]}" stroke-width="{w["width"]}" '
                 f'stroke-linejoin="round" stroke-linecap="round"{dash}{end}/>')
    for w in wires:
        if w.get('label') and w.get('label_at'):
            cx, ly = w['label_at']
            tw_ = text_w(w['label'], 12.5, True) + 18
            col = w.get('label_color', w['color'])
            o.append(f'<rect x="{cx - tw_ / 2:.1f}" y="{ly - 12:.1f}" width="{tw_:.1f}" height="24" rx="12" '
                     f'fill="#FFFFFF" stroke="{col}" stroke-width="1.25"/>')
            o.append(f'<text x="{cx:.1f}" y="{ly + 4.5:.1f}" font-family="\'{UI}\', sans-serif" font-size="12.5" '
                     f'font-weight="700" fill="{col}" text-anchor="middle">{html.escape(w["label"])}</text>')
    o.append('</svg>')
    return '\n'.join(o)


# ── draw.io ──────────────────────────────────────────────────────────────────
def _style(**kw):
    return ';'.join(f'{k}={v}' for k, v in kw.items()) + ';'


def _html_value(b):
    parts = []
    for (txt, size, bold, color, display) in b.get('runs', []):
        fam = DISPLAY if display else UI
        w = 'bold' if bold else 'normal'
        parts.append(f'<span style="font-family:{fam};font-size:{size}px;font-weight:{w};color:{color}">'
                     f'{html.escape(txt)}</span>')
    return '<br>'.join(parts)


def to_drawio(spec, W, H, items):
    cells = ['<mxCell id="0"/>', '<mxCell id="1" parent="0"/>']
    ids = {}

    def add(cid, value, style, x, y, w, h, vertex=True):
        ids[cid] = cid
        cells.append(f'<mxCell id="{xesc(cid)}" value="{xesc(value, {chr(34): "&quot;"})}" style="{xesc(style)}" '
                     f'vertex="1" parent="1"><mxGeometry x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" '
                     f'as="geometry"/></mxCell>')
    ordered = sorted([i for i in items if not isinstance(i, Wire)],
                     key=lambda b: 0 if b['id'].startswith(('lane', 'band')) else 1)
    for b in ordered:
        if isinstance(b, Img):
            data = base64.b64encode(Path(b['path']).read_bytes()).decode()
            add(b['id'], '', _style(shape='image', image=f'data:image/png,{data}', imageAspect=1, aspect='fixed'),
                b['x'], b['y'], b['w'], b['h'])
            continue
        st = dict(html=1, whiteSpace='wrap', rounded=1 if b.get('r') else 0,
                  fillColor=b.get('fill') or 'none', strokeColor=b.get('stroke') or 'none',
                  strokeWidth=b.get('sw', 1), align=b.get('align', 'left'),
                  verticalAlign=b.get('valign', 'top'), spacingLeft=b.get('pad', 0), spacingRight=b.get('pad', 0),
                  spacingTop=b.get('pad_top', b.get('pad', 0)) if b.get('valign', 'top') == 'top' else 0,
                  fontFamily=UI)
        if b.get('r'):
            st['arcSize'] = min(50, round(b['r'] / max(1, min(b['w'], b['h'])) * 100))
            st['absoluteArcSize'] = 1
            st['arcSize'] = round(b['r'] * 2)
        if b.get('dash'):
            st['dashed'] = 1
        if b.get('shadow'):
            st['shadow'] = 1
        if b.get('role') == 'text':
            st.update(text=1, strokeColor='none', fillColor='none')
        add(b['id'], _html_value(b), _style(**st), b['x'], b['y'], b['w'], b['h'])
        if b.get('accent'):
            add(b['id'] + '_bar', '', _style(rounded=0, fillColor=b['accent'], strokeColor='none'),
                b['x'] + b.get('r', 0) * 0.6, b['y'], b['w'] - b.get('r', 0) * 1.2, 5)
        if b.get('accent_left'):
            add(b['id'] + '_bar', '', _style(rounded=0, fillColor=b['accent_left'], strokeColor='none'),
                b['x'], b['y'], 5, b['h'])
    step_box = {b['step']: b for b in items if isinstance(b, Box) and b.get('step') is not None}
    for i, w in enumerate(i for i in items if isinstance(i, Wire)):
        if w.get('src') is None or w.get('dst') is None:      # a leader line: free-standing, no arrow
            (x0, y0), (x1, y1) = w['pts'][0], w['pts'][-1]
            st = _style(endArrow='none', html=1, strokeColor=w['color'], strokeWidth=w['width'],
                        dashed=1 if w.get('dash') else 0)
            cells.append(f'<mxCell id="e{i}" value="" style="{xesc(st)}" edge="1" parent="1">'
                         f'<mxGeometry relative="1" as="geometry"><mxPoint x="{x0:.1f}" y="{y0:.1f}" as="sourcePoint"/>'
                         f'<mxPoint x="{x1:.1f}" y="{y1:.1f}" as="targetPoint"/></mxGeometry></mxCell>')
            continue
        s, t = step_box[w['src']], step_box[w['dst']]
        (x0, y0), (x1, y1) = w['pts'][0], w['pts'][-1]
        rel = lambda b, x, y: (min(1, max(0, (x - b['x']) / b['w'])), min(1, max(0, (y - b['y']) / b['h'])))
        ex, ey = rel(s, x0, y0)
        nx, ny = rel(t, x1, y1)
        st = _style(edgeStyle='orthogonalEdgeStyle', rounded=1, html=1, endArrow='none' if w.get('plain') else 'block',
                    endFill=1, endSize=10,
                    strokeColor=w['color'], strokeWidth=w['width'], dashed=1 if w.get('dash') else 0,
                    exitX=f'{ex:.3f}', exitY=f'{ey:.3f}', exitDx=0, exitDy=0,
                    entryX=f'{nx:.3f}', entryY=f'{ny:.3f}', entryDx=0, entryDy=0,
                    fontFamily=UI, fontSize=12, fontStyle=1, fontColor=w['color'], labelBackgroundColor='#FFFFFF')
        pts = ''.join(f'<mxPoint x="{x:.1f}" y="{y:.1f}"/>' for x, y in w['pts'][1:-1])
        lx = f' x="{2 * w["label_t"] - 1:.3f}"' if w.get('label_t') is not None else ''
        cells.append(f'<mxCell id="e{i}" value="{xesc(w.get("label") or "")}" style="{xesc(st)}" edge="1" parent="1" '
                     f'source="{xesc(s["id"])}" target="{xesc(t["id"])}"><mxGeometry{lx} relative="1" as="geometry">'
                     f'<Array as="points">{pts}</Array></mxGeometry></mxCell>')
    name = xesc(f'{spec["client"]} {spec["diagram"]}')
    return (f'<mxfile host="servantium-documents"><diagram name="{name}" id="d1">'
            f'<mxGraphModel dx="{W:.0f}" dy="{H:.0f}" grid="1" gridSize="10" guides="1" tooltips="1" connect="1" '
            f'arrows="1" fold="1" page="1" pageScale="1" pageWidth="{W:.0f}" pageHeight="{H:.0f}" math="0" shadow="0">'
            f'<root>{"".join(cells)}</root></mxGraphModel></diagram></mxfile>')


# ── export ───────────────────────────────────────────────────────────────────
_RENDER_JS = r"""
const path = require('path');
const puppeteer = require('puppeteer');
(async () => {
  const [svgPath, pdfPath, pngPath] = process.argv.slice(2);
  const fs = require('fs');
  const svg = fs.readFileSync(svgPath, 'utf8');
  const m = svg.match(/width="(\d+)" height="(\d+)"/);
  const W = +m[1], H = +m[2];
  const b = await puppeteer.launch({ headless: 'new' });
  const p = await b.newPage();
  await p.setViewport({ width: W, height: H, deviceScaleFactor: 2 });
  await p.setContent(`<html><body style="margin:0">${svg}</body></html>`, { waitUntil: 'load' });
  await p.evaluate(() => document.fonts.ready);
  await p.pdf({ path: pdfPath, width: W + 'px', height: H + 'px', printBackground: true, pageRanges: '1' });
  await p.screenshot({ path: pngPath, clip: { x: 0, y: 0, width: W, height: H } });
  await b.close();
})();
"""


def _node_path():
    for c in (os.environ.get('SV_NODE_PATH'), str(kit.REPO_PACKAGES.parent / 'node_modules'),
              str(Path.home() / 'Projects/Servantium/decks/node_modules')):
        if c and (Path(c) / 'puppeteer').exists():
            return c
    raise FileNotFoundError('puppeteer not found. Install it, or set SV_NODE_PATH to a node_modules that has it.')


def build(spec_path, out_dir=None):
    spec = load(spec_path)
    W, H, items = layout(spec)
    out = Path(out_dir or Path(spec['_path']).parent / 'out')
    out.mkdir(parents=True, exist_ok=True)
    stem = f'{spec["client"]} {spec["diagram"]}'
    svg = out / f'{stem}.svg'
    svg.write_text(to_svg(W, H, items))
    drawio = out / f'{stem}.drawio'
    drawio.write_text(to_drawio(spec, W, H, items))
    js = Path(tempfile.gettempdir()) / 'sv-diagram-render.cjs'
    js.write_text(_RENDER_JS)
    env = {**os.environ, 'NODE_PATH': _node_path()}
    subprocess.run(['node', str(js), str(svg), str(out / f'{stem}.pdf'), str(out / f'{stem}.png')],
                   check=True, env=env, capture_output=True)
    return {'svg': svg, 'drawio': drawio, 'pdf': out / f'{stem}.pdf', 'png': out / f'{stem}.png', 'size': (W, H)}
